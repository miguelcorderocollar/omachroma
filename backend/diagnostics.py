"""Credential-free local dependency checks."""
import shutil
import subprocess
import sys
from pathlib import Path


def check():
    commands = {name: bool(shutil.which(name)) for name in ('omarchy', 'omarchy-shell', 'magick', 'xdg-open', 'wl-copy')}
    gio = subprocess.run(['/usr/bin/python3', '-c', 'import gi; gi.require_version("Gio", "2.0"); from gi.repository import Gio'],
                         capture_output=True, timeout=10).returncode == 0
    portal = False
    try:
        result = subprocess.run(['gdbus', 'introspect', '--session', '--dest', 'org.freedesktop.portal.Desktop',
                                 '--object-path', '/org/freedesktop/portal/desktop'], capture_output=True, timeout=10)
        portal = result.returncode == 0 and b'org.freedesktop.portal.FileChooser' in result.stdout
    except (OSError, subprocess.TimeoutExpired):
        pass
    return {'pythonSupported': sys.version_info >= (3, 11), 'commands': commands,
            'systemPyGObject': gio, 'fileChooserPortal': portal,
            'ready': all(commands.values()) and gio and portal}


def storage_usage():
    """Bounded metadata-only scan. Never read contents or follow directory links."""
    import os
    import stat
    from . import storage
    total = count = 0
    complete = True
    if storage.DATA.is_symlink():
        raise ValueError('Data directory is a symlink; storage scan skipped.')
    stack = [storage.DATA]
    visited = 0
    while stack:
        directory = stack.pop()
        if directory.is_symlink():
            continue
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if visited >= 5000:
                        return {'bytes': total, 'files': count, 'complete': False}
                    visited += 1
                    info = entry.stat(follow_symlinks=False)
                    if stat.S_ISDIR(info.st_mode):
                        stack.append(Path(entry.path))
                    elif stat.S_ISREG(info.st_mode):
                        total += info.st_size
                        count += 1
        except FileNotFoundError:
            continue
        except OSError:
            complete = False
    return {'bytes': total, 'files': count, 'complete': complete}


def open_data_folder():
    from . import storage
    if storage.DATA.is_symlink():
        raise ValueError('Data directory is a symlink; left unchanged.')
    storage.DATA.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(['xdg-open', str(storage.DATA)], capture_output=True, timeout=10)
    if result.returncode:
        raise ValueError('The app data folder could not open.')
