"""Durable, bounded Omatinta job metadata (never prompts or credentials)."""
from datetime import datetime, timezone
import hashlib
import heapq
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid

from . import costs, storage

MAX_LISTING = 100
MAX_HISTORY_READS = 500
MAX_LEGACY_FOLDERS = 500
MAX_RECORD_BYTES = 128 * 1024
_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
_FIELDS = ('date', 'name', 'provider', 'model', 'theme', 'resultPath', 'error',
           'message', 'status', 'sourcePath', 'installedPath', 'installedTheme', 'cost')
_PATH_FIELDS = {'resultPath', 'sourcePath', 'installedPath'}


def _root(create=False):
    data = Path(storage.DATA)
    if data.is_symlink():
        raise ValueError('History data directory is a symlink.')
    if create:
        data.mkdir(parents=True, exist_ok=True)
    root = data / 'history'
    if root.is_symlink():
        raise ValueError('History directory is a symlink.')
    if create:
        root.mkdir(mode=0o700, exist_ok=True)
        os.chmod(root, 0o700)
    return root


def _entry_path(job_id, create=False):
    if not isinstance(job_id, str) or not _ID.fullmatch(job_id) or job_id in ('.', '..'):
        raise ValueError('Invalid history ID.')
    root = _root(create)
    directory = root / job_id
    if directory.is_symlink():
        raise ValueError('History entry is a symlink.')
    if create:
        directory.mkdir(mode=0o700, exist_ok=True)
        os.chmod(directory, 0o700)
    return directory / 'job.json'


def _safe_record(record):
    """Return only bounded string metadata, rejecting malformed field types."""
    result = {}
    for key in _FIELDS:
        if key not in record or record[key] is None:
            continue
        value = record[key]
        if key == 'cost':
            result[key] = costs.normalize_summary(value)
            continue
        if not isinstance(value, str):
            raise ValueError('Invalid history field type.')
        result[key] = value[:4096 if key in _PATH_FIELDS else 500]
    return result


def _write(job_id, record):
    safe = _safe_record(record)
    if not isinstance(safe.get('status'), str):
        raise ValueError('History status is required.')
    path = _entry_path(job_id, create=True)
    if path.is_symlink():
        raise ValueError('History metadata is a symlink.')
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.job-')
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(safe, stream, ensure_ascii=False, separators=(',', ':'))
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def create(*, name='', provider='', model='', theme='', source_path=''):
    job_id = uuid.uuid4().hex
    record = {'date': datetime.now(timezone.utc).isoformat(timespec='microseconds'),
              'name': name or 'Wallpaper', 'provider': provider, 'model': model,
              'theme': theme or '', 'resultPath': '', 'error': '',
              'message': 'Starting…', 'status': 'running'}
    if source_path:
        record['sourcePath'] = str(source_path)
    _write(job_id, record)
    return job_id


def update(job_id, **changes):
    current = read(job_id)
    if current is None:
        raise ValueError('History entry does not exist.')
    current.update({key: value for key, value in changes.items() if key in _FIELDS})
    _write(job_id, current)
    return current


def read(job_id):
    path = _entry_path(job_id)
    try:
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, 'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                return None
            data = stream.read(MAX_RECORD_BYTES + 1)
        if len(data) > MAX_RECORD_BYTES:
            return None
        value = json.loads(data.decode('utf-8'))
        if not isinstance(value, dict) or not isinstance(value.get('status'), str):
            return None
        record = _safe_record(value)
        record['id'] = job_id
        from . import themes
        installed_theme = record.get('installedTheme') or record.get('theme', '')
        installed = themes.installed_path(record.get('resultPath', ''), installed_theme, record.get('installedPath', ''))
        record['installedPath'] = installed
        record['installedTheme'] = installed_theme if installed else ''
        result_path = record.get('resultPath', '')
        try:
            record['resultExists'] = bool(result_path and Path(result_path).is_file())
        except (OSError, ValueError):
            record['resultExists'] = False
        return record
    except (OSError, TypeError, ValueError, UnicodeError):
        return None


def _history_children(root, maximum):
    """Yield the newest bounded set of history dirs with bounded memory."""
    newest = []
    try:
        with os.scandir(root) as children:
            for child in children:
                try:
                    if not child.is_dir(follow_symlinks=False) or not _ID.fullmatch(child.name):
                        continue
                    modified = child.stat(follow_symlinks=False).st_mtime_ns
                    row = (modified, child.name, Path(child.path))
                    if len(newest) < maximum:
                        heapq.heappush(newest, row)
                    elif row[:2] > newest[0][:2]:
                        heapq.heapreplace(newest, row)
                except OSError:
                    continue
    except OSError:
        return
    for _, _, path in sorted(newest, reverse=True):
        yield path


def _indexed_result_folders():
    """Find output folders already represented in history, with bounded reads."""
    root = _root()
    folders = set()
    if not root.is_dir():
        return folders
    for child in _history_children(root, MAX_HISTORY_READS):
        item = read(child.name)
        result_path = item.get('resultPath', '') if item else ''
        if result_path:
            try:
                folders.add(Path(result_path).resolve(strict=False).parent)
            except (OSError, ValueError):
                pass
    return folders


def _legacy_jobs(result_root):
    """Yield direct theme/job folders only, examining at most 500 entries."""
    examined = 0
    try:
        themes = os.scandir(result_root)
    except OSError:
        return
    with themes:
        for theme_entry in themes:
            if examined >= MAX_LEGACY_FOLDERS:
                return
            examined += 1
            try:
                if not theme_entry.is_dir(follow_symlinks=False):
                    continue
                jobs_dir = os.scandir(theme_entry.path)
            except OSError:
                continue
            with jobs_dir:
                for job_entry in jobs_dir:
                    if examined >= MAX_LEGACY_FOLDERS:
                        return
                    examined += 1
                    try:
                        if job_entry.is_dir(follow_symlinks=False):
                            yield Path(job_entry.path), theme_entry.name
                    except OSError:
                        continue


def _import_legacy():
    """Import one preferred result per prior theme/job directory on demand."""
    result_root = Path(storage.DATA) / 'results'
    if result_root.is_symlink() or not result_root.is_dir():
        return
    try:
        resolved_root = result_root.resolve(strict=True)
    except OSError:
        return
    represented = _indexed_result_folders()
    for folder, theme in _legacy_jobs(result_root):
        if folder.is_symlink():
            continue
        try:
            resolved_folder = folder.resolve(strict=True)
            resolved_folder.relative_to(resolved_root)
        except (OSError, ValueError):
            continue
        if resolved_folder in represented:
            continue
        # Select a final result once; edited.png is a fallback for interrupted jobs.
        for filename in ('wallpaper.jpg', 'edited.png'):
            candidate = folder / filename
            try:
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                resolved = candidate.resolve(strict=True)
                resolved.relative_to(resolved_folder)
                file_stat = candidate.stat()
            except (OSError, ValueError):
                continue
            job_id = 'legacy-' + hashlib.sha256(str(resolved_folder).encode()).hexdigest()[:32]
            if read(job_id) is None:
                stamp = datetime.fromtimestamp(file_stat.st_mtime, timezone.utc).isoformat(timespec='seconds')
                try:
                    _write(job_id, {'date': stamp, 'name': 'Previous wallpaper',
                                    'provider': '', 'model': '', 'theme': theme,
                                    'resultPath': str(resolved), 'error': '',
                                    'message': 'Imported from previous results', 'status': 'done'})
                except (OSError, ValueError):
                    pass
            represented.add(resolved_folder)
            break


def listing(limit=50):
    _import_legacy()
    root = _root()
    if not root.is_dir():
        return []
    entries = []
    for child in _history_children(root, MAX_HISTORY_READS):
        item = read(child.name)
        if item is not None:
            entries.append((item.get('date', ''), child.name, item))
    entries.sort(key=lambda row: (row[0], row[1]), reverse=True)
    try:
        count = max(0, min(int(limit), MAX_LISTING))
    except (TypeError, ValueError):
        count = 50
    return [item for _, _, item in entries[:count]]


def latest():
    items = listing(1)
    return items[0] if items else None
