#!/usr/bin/env python3
"""Omachroma backend. Local queries are free; API jobs require --run."""
import argparse
import json
from pathlib import Path
import signal
import sys
from backend import catalog, diagnostics, export, history, jobs, picker, storage, themes, upscalers


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--snapshot', action='store_true')
    ap.add_argument('--history', action='store_true')
    ap.add_argument('--load-history')
    ap.add_argument('--remember-output')
    ap.add_argument('--clear-preview', action='store_true')
    ap.add_argument('--export-image')
    ap.add_argument('--save-to-theme')
    ap.add_argument('--job-id')
    ap.add_argument('--save-config', action='store_true')
    ap.add_argument('--restore-model-defaults', action='store_true')
    ap.add_argument('--save-key', choices=['fal', 'openrouter'])
    ap.add_argument('--install-launcher', action='store_true')
    ap.add_argument('--remove-launcher', action='store_true')
    ap.add_argument('--remove-key', choices=['fal', 'openrouter'])
    ap.add_argument('--save-models', action='store_true')
    ap.add_argument('--refresh-prices', action='store_true')
    ap.add_argument('--doctor', action='store_true')
    ap.add_argument('--pick-images', action='store_true')
    ap.add_argument('--multiple', action='store_true')
    ap.add_argument('--picker-title', default='Choose images')
    ap.add_argument('--storage-info', action='store_true')
    ap.add_argument('--open-data-folder', action='store_true')
    ap.add_argument('--init-env', action='store_true')
    ap.add_argument('--list-themes', action='store_true')
    ap.add_argument('--list-backgrounds')
    ap.add_argument('--theme-colors')
    ap.add_argument('--theme-bundle')
    ap.add_argument('--theme')
    ap.add_argument('--source')
    ap.add_argument('--style-refs', nargs='*', default=[])
    ap.add_argument('--prompt', default=storage.DEFAULT_PROMPT)
    ap.add_argument('--prompt-file')
    ap.add_argument('--provider', choices=['fal', 'openrouter'], default='fal')
    ap.add_argument('--model')
    ap.add_argument('--quality', choices=['auto', 'low', 'medium', 'high', 'xhigh', 'max'], default='high')
    ap.add_argument('--res', choices=['1K', '2K', '4K'], default='1K')
    ap.add_argument('--upscaler', choices=list(upscalers.catalog()), default=upscalers.default_kind())
    ap.add_argument('--upscale-model')
    ap.add_argument('--upscale-factor', type=float)
    ap.add_argument('--upscale-only')
    ap.add_argument('--creativity', type=int, choices=range(1, 10), default=5)
    ap.add_argument('--env-file', default='')
    ap.add_argument('--repo-dir', default=str(storage.DATA / 'results'))
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--skip-upscale', action='store_true')
    ap.add_argument('--tag')  # retained for older callers; jobs always use unique IDs
    ap.add_argument('--seed', type=int)
    args = ap.parse_args()
    if args.pick_images:
        try:
            paths = picker.choose('OpenFile', args.picker_title, multiple=args.multiple)
        except Exception:
            raise ValueError('The desktop image picker could not open. Check the FileChooser portal.') from None
        print(json.dumps({'paths': [str(path) for path in paths]}))
    elif args.storage_info:
        print(json.dumps(diagnostics.storage_usage()))
    elif args.open_data_folder:
        diagnostics.open_data_folder()
    elif args.doctor:
        print(json.dumps(diagnostics.check()))
    elif args.history:
        print(json.dumps({'records': history.listing()}))
    elif args.remember_output:
        storage.remember_job(args.remember_output)
        print(json.dumps({'remembered': True}))
    elif args.load_history:
        value = history.read(args.load_history)
        if value is None:
            raise ValueError('History entry is missing.')
        storage.remember_job(args.load_history)
        print(json.dumps(value))
    elif args.clear_preview:
        storage.remember_job(None)
        print(json.dumps({'cleared': True}))
    elif args.export_image:
        print(json.dumps(export.save_image(args.export_image)))
    elif args.save_to_theme:
        if not args.theme:
            raise ValueError('Choose a theme before saving the wallpaper.')
        record = history.read(args.job_id) if args.job_id else None
        if args.job_id and (record is None or record.get('resultPath') != str(Path(args.save_to_theme).expanduser().resolve())):
            raise ValueError('The history entry does not match this image.')
        saved = themes.save_image(args.save_to_theme, args.theme)
        if record:
            history.update(args.job_id, **saved)
        print(json.dumps(saved))
    elif args.snapshot or args.init_env:
        print(json.dumps(storage.snapshot()))
    elif args.save_config:
        value = storage.normalize_config(json.loads(sys.stdin.readline()))
        storage.atomic_write(storage.DATA / 'config.json', json.dumps(value, indent=2) + '\n')
        print(json.dumps(storage.snapshot()))
    elif args.restore_model_defaults:
        storage.restore_model_defaults()
        print(json.dumps(storage.snapshot()))
    elif args.save_key:
        storage.save_key(args.save_key, sys.stdin.readline().rstrip('\n'))
        print(json.dumps(storage.snapshot()))
    elif args.save_models:
        catalog.save(json.loads(sys.stdin.read(256 * 1024 + 1)))
        print(json.dumps(storage.snapshot()))
    elif args.refresh_prices:
        def refresh_deadline(signum, frame):
            raise catalog.RefreshTimeout('Metadata refresh timed out. Saved data remains available.')
        previous_handler = signal.signal(signal.SIGALRM, refresh_deadline)
        signal.alarm(80)
        try:
            refreshed = catalog.refresh()
            print(json.dumps(storage.snapshot() | {'refresh': refreshed}))
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous_handler)
    elif args.remove_key:
        storage.remove_key(args.remove_key)
        print(json.dumps(storage.snapshot()))
    elif args.remove_launcher:
        storage.remove_launcher()
    elif args.install_launcher:
        storage.install_launcher()
        try:
            storage.remove_launcher(legacy=True)
        except ValueError:
            pass
    elif args.list_themes:
        print(json.dumps(storage.themes()))
    elif args.list_backgrounds:
        print(json.dumps(storage.backgrounds(args.list_backgrounds)))
    elif args.theme_colors:
        print(json.dumps(storage.colors(args.theme_colors)))
    elif args.theme_bundle:
        print(json.dumps({'backgrounds': storage.backgrounds(args.theme_bundle), 'swatches': storage.colors(args.theme_bundle)}))
    else:
        if args.skip_upscale:
            args.upscaler = 'none'
        args.model = args.model or storage.default_model(args.provider)
        args.upscale_model = args.upscale_model or next(iter(upscalers.catalog()[args.upscaler]['models']), '')
        if args.upscale_factor is None:
            args.upscale_factor = next(iter(upscalers.catalog()[args.upscaler]['factors']), 2)
        def timeout(signum, frame):
            raise TimeoutError('Job timed out after 15 minutes. The provider may have billed completed work.')
        signal.signal(signal.SIGALRM, timeout)
        def cancel(signum, frame):
            raise jobs.Cancelled('Stopped locally. Completed provider work may still be billed.')
        signal.signal(signal.SIGTERM, cancel)
        signal.alarm(900)
        jobs.run(args)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, IndexError, TypeError, TimeoutError, jobs.Cancelled, catalog.RefreshTimeout) as e:
        print(json.dumps({'state': 'error', 'message': str(e)[:350]}), file=sys.stderr)
        sys.exit(1)
