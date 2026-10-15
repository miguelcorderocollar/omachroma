"""Local settings, credentials and theme discovery. No API calls here."""
import json
import os
from pathlib import Path
import tempfile
import tomllib
from . import upscalers

HOME = Path.home()
_base = Path(os.environ.get('XDG_DATA_HOME', HOME / '.local/share'))
# Keep legacy paths intact so saved result/history references remain valid.
DATA = _base / ('omapaper' if (_base / 'omapaper').is_dir() and not (_base / 'omachroma').exists() else 'omachroma')
STOCK = Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy')) / 'themes'
USER = HOME / '.config/omarchy/themes'
BACKGROUNDS = HOME / '.config/omarchy/backgrounds'
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
DEFAULT_PROMPT = ('Recreate the FIRST image using the colors, light, mood and texture of the OTHER '
                  'reference images. Preserve the subjects and composition. Do not add or remove '
                  'elements. Wide 16:9 desktop wallpaper, no added text or watermark.')
from . import catalog
EDIT_MODELS = catalog.MODELS
DEFAULT_PROVIDER_MODELS = {'fal': 'google/nano-banana-2.1/edit', 'openrouter': 'google/gemini-nano-banana-2.1'}


def model_spec(provider, model):
    return next((item for item in catalog.models(provider) if item['value'] == model), None)


def default_model(provider):
    return catalog.default_model(provider)

UPSCALE_MODELS = upscalers.MODELS

DEFAULTS = {'provider': 'fal', 'model': DEFAULT_PROVIDER_MODELS['fal'], 'res': '1K', 'quality': 'high',
            'upscaler': upscalers.DEFAULT, 'upscaleModel': 'SeedVR2', 'upscaleFactor': 2, 'creativity': 5,
            'prompt': DEFAULT_PROMPT}


def atomic_write(path, text, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError('Refusing to replace a symlink: ' + str(path))
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'w') as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def credentials(explicit=''):
    result = {}
    path = Path(explicit).expanduser() if explicit else DATA / '.env'
    if path.is_file():
        for line in path.read_text().splitlines():
            key, sep, value = line.partition('=')
            if sep and key.strip() in ('FAL_KEY', 'OPENROUTER_API_KEY'):
                result[key.strip()] = value.strip().strip('\"\'')
    for key in ('FAL_KEY', 'OPENROUTER_API_KEY'):
        if os.environ.get(key):
            result[key] = os.environ[key]
    return result


def save_key(provider, key):
    name = {'fal': 'FAL_KEY', 'openrouter': 'OPENROUTER_API_KEY'}[provider]
    if not key.strip() or any(c in key for c in '\r\n\x00'):
        raise ValueError('Enter a valid API key on a single line.')
    # Preserve the other saved credential, without persisting environment secrets.
    env = credentials(str(DATA / '.env'))
    for k in tuple(env):
        if k in os.environ:
            env.pop(k)
    path = DATA / '.env'
    if path.is_file():
        for line in path.read_text().splitlines():
            k, sep, v = line.partition('=')
            if sep and k in ('FAL_KEY', 'OPENROUTER_API_KEY'):
                env[k] = v.strip()
    env[name] = key.strip()
    atomic_write(path, ''.join(k + '=' + v + '\n' for k, v in env.items()))


def normalize_config(value):
    if not isinstance(value, dict):
        raise ValueError('Settings must be a JSON object.')
    custom, _ = catalog.user_config()
    defaults = DEFAULTS | {k: v for k, v in custom['defaults'].items() if k in DEFAULTS}
    provider = value.get('provider', defaults['provider'])
    if provider not in ('fal', 'openrouter'):
        provider = 'fal'
    defaults['model'] = default_model(provider)
    defaults['upscaler'] = upscalers.default_kind()
    defaults['upscaleModel'] = custom['defaults'].get('upscaleModel', next(iter(upscalers.catalog()[defaults['upscaler']]['models']), ''))
    c = defaults | {k: v for k, v in value.items() if k in DEFAULTS}
    if not isinstance(c['provider'], str) or c['provider'] not in EDIT_MODELS:
        c['provider'] = 'fal'
    if c['model'] not in [m['value'] for m in catalog.models(c['provider'])]:
        c['model'] = default_model(c['provider'])
    spec = model_spec(c['provider'], c['model'])
    if c['res'] not in spec['resolutions']:
        c['res'] = spec['resolutions'][0] if spec['resolutions'] else '1K'
    quality_options = spec.get('qualityOptions', [])
    if quality_options and c['quality'] not in quality_options:
        c['quality'] = 'high' if 'high' in quality_options else quality_options[0]
    engines = upscalers.catalog()
    if not isinstance(c['upscaler'], str) or c['upscaler'] not in engines:
        c['upscaler'] = upscalers.default_kind()
    if c['upscaleModel'] not in engines[c['upscaler']]['models']:
        c['upscaleModel'] = next(iter(engines[c['upscaler']]['models']), '')
    factors = engines[c['upscaler']]['factors']
    if factors and c['upscaleFactor'] not in factors:
        c['upscaleFactor'] = factors[0]
    try:
        c['creativity'] = max(1, min(9, int(c['creativity'])))
    except (ValueError, TypeError, OverflowError):
        c['creativity'] = DEFAULTS['creativity']
    if not isinstance(c['prompt'], str) or not c['prompt'].strip():
        c['prompt'] = DEFAULT_PROMPT
    return c


def config():
    path = DATA / 'config.json'
    try:
        return normalize_config(catalog.model_config.read_json(path) if path.exists() else {})
    except (ValueError, TypeError, OSError):
        return normalize_config({})


def restore_model_defaults():
    """Reset generation controls, preserving provider, prompt and credential files."""
    current = config()
    provider = current['provider']
    reset_fields = ('res', 'quality', 'upscaler', 'upscaleModel', 'upscaleFactor', 'creativity')
    current.update({key: DEFAULTS[key] for key in reset_fields})
    current['model'] = default_model(provider)
    custom, _ = catalog.user_config()
    current.update({k: v for k, v in custom['defaults'].items() if k in reset_fields})
    if 'upscaler' not in custom['defaults']:
        current['upscaler'] = upscalers.default_kind()
    if 'upscaleModel' not in custom['defaults']:
        current['upscaleModel'] = next(iter(upscalers.catalog()[current['upscaler']]['models']), '')
    restored = normalize_config(current)
    atomic_write(DATA / 'config.json', json.dumps(restored, indent=2) + '\n')
    return restored


def theme_name(name):
    if not name or name.startswith('.') or Path(name).name != name or '\\' in name:
        raise ValueError('Invalid theme name.')
    return name


def themes():
    return sorted({p.name for base in (STOCK, USER) if base.is_dir()
                   for p in base.iterdir() if p.is_dir()})


def backgrounds(name):
    name = theme_name(name)
    found = {}
    for base in (STOCK / name / 'backgrounds', USER / name / 'backgrounds', BACKGROUNDS / name):
        if base.is_dir():
            for p in sorted(base.iterdir()):
                if p.is_file() and p.suffix.lower() in EXTENSIONS:
                    found[p.name] = str(p)
    return [{'name': k, 'path': v} for k, v in sorted(found.items())]


def colors(name):
    name = theme_name(name)
    values = {}
    for base in (STOCK / name, USER / name):
        p = base / 'colors.toml'
        if p.is_file():
            values.update(tomllib.loads(p.read_text()))
    return [values[k] for k in ('background', 'foreground', 'accent', 'blue', 'red') if values.get(k)]


def remember_job(ident):
    from . import history
    if ident is not None and history.read(ident) is None:
        raise ValueError('History entry is missing.')
    atomic_write(DATA / 'current-job.json', json.dumps({'id': ident}) + '\n')


def snapshot():
    from . import history
    keys = credentials()
    current_file = HOME / '.local/state/omarchy/current/theme.name'
    current = current_file.read_text().strip() if current_file.is_file() else ''
    records = history.listing(limit=100)
    last_job = dict(records[0]) if records else None
    selection_file = DATA / 'current-job.json'
    if selection_file.is_file() and not selection_file.is_symlink():
        try:
            if selection_file.stat().st_size > 65536:
                raise ValueError('Current job selection is too large.')
            selection = json.loads(selection_file.read_text())
            if not isinstance(selection, dict) or 'id' not in selection:
                raise ValueError('Current job selection is invalid.')
            last_job = history.read(selection['id']) if selection.get('id') else None
        except (OSError, ValueError, TypeError, KeyError):
            pass
    if last_job and not last_job.get('resultExists'):
        previous = next((record for record in records if record.get('resultExists')), {})
        last_job.update(previousResult=previous, previousResultPath=previous.get('resultPath', ''),
                        previousResultId=previous.get('id', ''), previousInstalledPath=previous.get('installedPath', ''),
                        previousInstalledTheme=previous.get('installedTheme', ''))
    return {'currentTheme': current, 'lastJob': last_job, 'prices': upscalers.prices(),
            'config': config(), 'themes': themes(), 'editModels': {p: catalog.models(p) for p in EDIT_MODELS},
            'modelConfig': catalog.user_config()[0], 'catalogWarning': config_warning() or catalog.user_config()[1] or catalog.cache()[1],
            'dataPath': str(DATA), 'modelConfigPath': str(DATA / 'models.json'),
            'providerDefaults': {p: default_model(p) for p in EDIT_MODELS},
            'environmentKeys': {p: bool(os.environ.get(k)) for p, k in (('fal', 'FAL_KEY'), ('openrouter', 'OPENROUTER_API_KEY'))},
            'upscaleModels': {k: v['models'] for k, v in upscalers.catalog().items()},
            'upscaleOptions': [{'value': k, 'label': v['label']} for k, v in upscalers.catalog().items()],
            'upscaleSpecs': upscalers.catalog(), 'keys': {'fal': bool(keys.get('FAL_KEY')),
            'openrouter': bool(keys.get('OPENROUTER_API_KEY'))}}


def install_launcher():
    from . import launchers
    launchers.install()


def remove_key(provider):
    """Remove only the selected saved key; environment credentials are untouched."""
    name = {'fal': 'FAL_KEY', 'openrouter': 'OPENROUTER_API_KEY'}[provider]
    path = DATA / '.env'
    if path.is_symlink():
        raise ValueError('Credential file is a symlink; left unchanged.')
    if path.exists():
        if path.stat().st_size > 16384:
            raise ValueError('Credential file is too large; left unchanged.')
        lines = [line for line in path.read_text().splitlines() if line.partition('=')[0].strip() != name]
        atomic_write(path, '\n'.join(lines) + ('\n' if lines else ''))


def remove_launcher(legacy=False):
    from . import launchers
    launchers.remove(legacy)


def config_warning():
    path = DATA / 'config.json'
    try:
        if path.exists():
            normalize_config(catalog.model_config.read_json(path))
    except (OSError, ValueError, TypeError):
        return 'Settings file could not load. Defaults are active; saving a setting repairs config.json. Saved images and keys are unchanged.'
    return ''
