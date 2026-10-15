"""Validate before billing, isolate intermediate files, and retain useful results."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import tempfile
import uuid
from . import costs, history, providers, storage, upscalers


class Cancelled(Exception):
    """Raised by the CLI's SIGTERM handler to persist a cancelled job."""


_active_job_id = None
_active_result_path = ''
_active_cost = None


def emit(**values):
    global _active_cost
    if _active_job_id:
        values.setdefault('jobId', _active_job_id)
        summary = values.get('cost')
        if summary is not None:
            summary = costs.normalize_summary(summary)
            values['cost'] = summary
            _active_cost = summary
        state = values.get('state', '')
        path = values.get('path', '')
        message = values.get('warning') or values.get('message') or ('Wallpaper saved.' if state == 'done' else state)
        changes = {'message': str(message)[:500]}
        if summary is not None:
            changes['cost'] = summary
        if isinstance(values.get('installedPath'), str):
            changes['installedPath'] = values['installedPath']
        if isinstance(values.get('installedTheme'), str):
            changes['installedTheme'] = values['installedTheme']
        if isinstance(values.get('theme'), str):
            changes['theme'] = values['theme']
        if path:
            _remember_result(path)
            changes['resultPath'] = _active_result_path
        if state == 'done':
            changes['status'] = 'done'
        try:
            history.update(_active_job_id, **changes)
        except (OSError, ValueError):
            pass
    print(json.dumps(values), flush=True)


def _remember_result(path):
    global _active_result_path
    try:
        candidate = Path(path).expanduser()
        if candidate.is_file() and not candidate.is_symlink():
            _active_result_path = str(candidate.resolve())
    except (OSError, ValueError):
        pass


def magick(*args):
    try:
        r = subprocess.run(['magick', *map(str, args)], capture_output=True, timeout=60)
    except FileNotFoundError:
        raise ValueError('ImageMagick is required. Install it before generating.') from None
    if r.returncode:
        raise ValueError('Cannot read or convert the image. Choose a supported local image.')
    return r.stdout.decode().strip()


def image(path):
    p = Path(path).expanduser().resolve()
    if not p.is_file() or p.suffix.lower() not in storage.EXTENSIONS:
        raise ValueError('Choose a local JPG, PNG, WebP, BMP or GIF image.')
    magick('identify', '-ping', '-format', '%w %h', str(p) + '[0]')
    return p


def validate(args):
    if args.theme:
        storage.theme_name(args.theme)
        if args.theme not in storage.themes():
            raise ValueError('Choose an installed theme.')
    if args.install and not args.theme:
        raise ValueError('Installing a wallpaper requires a theme.')
    if not 1 <= args.upscale_factor <= 4:
        raise ValueError('Upscale factor must be between 1 and 4.')
    if args.upscaler == 'none' and args.upscale_only:
        raise ValueError('Select an upscaler in Settings first.')
    if args.upscaler != 'none':
        upscalers.validate(args.upscaler, args.upscale_model, args.upscale_factor)
    if args.upscale_only:
        return [image(args.upscale_only)], ''
    if not args.theme or not args.source:
        raise ValueError('Choose a source image and theme.')
    if not args.style_refs:
        raise ValueError('Select at least one style reference.')
    spec = storage.model_spec(args.provider, args.model)
    if not spec:
        raise ValueError('Select a model available from the selected provider.')
    if spec.get('available') is False:
        raise ValueError('This model is unavailable. Refresh prices or choose another model in Settings.')
    if len(args.style_refs) + 1 > spec['maxImages']:
        raise ValueError(f"This model accepts up to {spec['maxImages'] - 1} style references.")
    if spec['resolutions'] and args.res not in spec['resolutions']:
        raise ValueError('Select a resolution supported by this model.')
    if spec.get('qualityOptions') and args.quality not in spec['qualityOptions']:
        raise ValueError('Select an image quality supported by this model.')
    prompt = Path(args.prompt_file).expanduser().read_text().strip() if args.prompt_file else args.prompt
    if not prompt or not prompt.strip():
        raise ValueError('Enter a prompt.')
    return [image(p) for p in [args.source, *args.style_refs]], prompt.strip()


def _run(args):
    images, prompt = validate(args)
    keys = storage.credentials(args.env_file)
    required = set()
    if not args.upscale_only:
        required.add('FAL_KEY' if args.provider == 'fal' else 'OPENROUTER_API_KEY')
    if args.upscaler != 'none':
        required.add('FAL_KEY')
    if not args.run:
        emit(state='dry-run', provider=args.provider, model=args.model, references=len(images)-1,
             requiredKeys=sorted(required))
        return
    for key in required:
        if not keys.get(key):
            raise ValueError(key + ' is missing. Add it in Settings.')
    tag = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8]
    out = Path(args.repo_dir).expanduser().resolve() / (args.theme or 'upscaled') / tag
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='omachroma-') as scratch:
        compressed = []
        for i, p in enumerate(images):
            dest = Path(scratch) / f'{i}.jpg'
            magick(str(p) + '[0]', '-auto-orient', '-resize', '2048x2048>', '-background', '#000000', '-alpha', 'remove', '-strip', '-quality', '90', dest)
            compressed.append(dest)
        edited = out / 'edited.png'
        cost = None
        upscale_cost = None
        edit_requested = not bool(args.upscale_only)
        upscale_requested = args.upscaler != 'none'
        if args.upscale_only:
            source = images[0]
        else:
            emit(state='editing', message='Editing with ' + args.provider + '…')
            cost = providers.edit(args.provider, args.model, prompt, compressed, args.res, args.quality, keys, edited)
            emit(state='edited', path=str(edited), message='Edit saved. Preparing final image…',
                 cost=costs.summary(cost, None, edit_requested=True,
                                    upscale_requested=upscale_requested))
            magick('identify', '-ping', edited)
            source = edited
            storage.atomic_write(out / 'prompt.txt', prompt + '\n')
        final = out / 'wallpaper.jpg'
        warning = ''
        if args.upscaler == 'none':
            magick(source, '-quality', '95', final)
        else:
            emit(state='upscaling', message='Upscaling with ' + args.upscale_model + '…',
                 cost=costs.summary(cost, None, edit_requested=edit_requested,
                                    upscale_requested=True))
            try:
                # Convert to JPEG without shrinking before upscale; data URL MIME stays correct.
                upload = Path(scratch) / 'upscale.jpg'
                magick(str(source) + '[0]', '-auto-orient', '-strip', '-quality', '95', upload)
                restored = Path(scratch) / 'restored-image'
                upscale_cost = providers.upscale(upload, args.upscaler, args.upscale_model, args.upscale_factor,
                                                 args.creativity, keys, restored)
                emit(state='upscaled', message='Upscaling complete.',
                     cost=costs.summary(cost, upscale_cost, edit_requested=edit_requested,
                                        upscale_requested=True))
                magick(restored, '-quality', '95', final)
            except (Cancelled, TimeoutError):
                raise
            except Exception:
                if args.upscale_only:
                    raise
                magick(edited, '-quality', '95', final)
                warning = 'Edit saved, but upscaling failed. You can retry it in Upscale.'
        installed = ''
        if args.install:
            try:
                from . import themes
                installed = themes.save_image(final, args.theme)['installedPath']
            except (OSError, ValueError):
                warning = (warning + ' Wallpaper saved, but theme installation failed.').strip()
        emit(state='done', path=str(final), installedPath=installed, theme=args.theme or '',
             warning=warning, editCost=cost,
             cost=costs.summary(cost, upscale_cost, edit_requested=edit_requested,
                                upscale_requested=upscale_requested))


def _safe_error(error):
    """Keep useful bounded failure text while filtering credential-shaped values."""
    value = str(error).replace('\x00', '')
    # Provider adapters intentionally avoid response bodies, but do not persist
    # any credential-looking assignment should a lower layer include one.
    import re
    value = re.sub(r'(?i)(api[_ -]?key|authorization|token)(\s*[:=]\s*)\S+', r'\1\2[redacted]', value)
    return value[:500]


def run(args):
    """Record each real attempt around the existing single-run implementation."""
    global _active_job_id, _active_result_path, _active_cost
    if not args.run:
        return _run(args)
    source = args.upscale_only or args.source or ''
    try:
        source_name = Path(source).expanduser().name
        name = Path(source_name).stem if source_name else 'Wallpaper'
    except (TypeError, ValueError):
        name = 'Wallpaper'
    job_id = history.create(name=name or 'Wallpaper', provider=args.provider,
                            model=args.model, theme=args.theme or '',
                            source_path=source)
    storage.remember_job(job_id)
    _active_job_id = job_id
    _active_result_path = ''
    edit_requested = not bool(args.upscale_only)
    upscale_requested = args.upscaler != 'none'
    _active_cost = costs.summary(edit_requested=edit_requested,
                                 upscale_requested=upscale_requested)
    if args.upscale_only:
        _remember_result(args.upscale_only)
    emit(state='starting', message='Job started.', cost=_active_cost)
    try:
        result = _run(args)
        # A completed upscale-only operation already emitted done. Keep the
        # status complete even if a future runner returns without a final event.
        try:
            history.update(job_id, status='done', resultPath=_active_result_path,
                           cost=_active_cost)
        except (OSError, ValueError):
            pass
        return result
    except Cancelled as error:
        try:
            history.update(job_id, status='cancelled', error=_safe_error(error),
                           message='Cancelled.', resultPath=_active_result_path,
                           cost=_active_cost)
        except (OSError, ValueError):
            pass
        emit(state='cancelled', message='Cancelled.', cost=_active_cost)
        raise
    except Exception as error:
        safe = _safe_error(error)
        try:
            history.update(job_id, status='failed', error=safe, message=safe,
                           resultPath=_active_result_path, cost=_active_cost)
        except (OSError, ValueError):
            pass
        emit(state='failed', error=safe, message=safe, cost=_active_cost)
        raise
    finally:
        _active_job_id = None
        _active_result_path = ''
        _active_cost = None
