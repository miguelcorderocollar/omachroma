"""Reviewed dedicated upscalers. All hosted by fal; engine schemas are distinct."""
CATALOG = {
    'seedvr': {
        'label': 'SeedVR2 · recommended',
        'endpoint': 'fal-ai/seedvr/upscale/image',
        'models': ['SeedVR2'], 'factors': [2, 4],
        'description': 'Recommended quality/cost balance. Restores fine detail without a text prompt; small details can change.'
    },
    'precision': {
        'label': 'Topaz Precision · preserve detail',
        'endpoint': 'topaz/upscale/image/precision',
        'models': ['Standard V2', 'High Fidelity V3', 'High Fidelity V2', 'Low Resolution V2', 'CGI', 'Text Refine', 'Faces'],
        'factors': [2, 4],
        'description': 'Use when preserving the edited composition, colors and existing detail matters most.'
    },
    'aura': {
        'label': 'AuraSR v2 · fast 4×',
        'endpoint': 'fal-ai/aura-sr',
        'models': ['AuraSR v2'], 'factors': [4],
        'description': 'A fast GAN upscaler with overlapping tiles to reduce seams. Always produces 4× dimensions.'
    },
    'clarity': {
        'label': 'Clarity · creative detail',
        'endpoint': 'fal-ai/clarity-upscaler',
        'models': ['Clarity'], 'factors': [2, 4],
        'description': 'Adds texture and detail. Conservative creativity and strong resemblance help retain the source.'
    },
    'creative': {
        'label': 'Topaz Creative · add detail',
        'endpoint': 'topaz/upscale/image/creative',
        'models': ['Bloom 2', 'Bloom', 'Bloom Realism'], 'factors': [2, 4],
        'description': 'Bloom can invent new texture. Choose Precision for faithful enlargement.'
    },
    'none': {
        'label': 'None · save the edit', 'endpoint': '', 'models': [], 'factors': [],
        'description': 'Keep the editing model’s original output without another provider request.'
    },
}
MODELS = {name: spec['models'] for name, spec in CATALOG.items()}
OPTIONS = [{'value': name, 'label': spec['label']} for name, spec in CATALOG.items()]
DEFAULT = 'seedvr'


def validate(kind, model, factor):
    spec = catalog().get(kind)
    if not spec or kind == 'none':
        raise ValueError('Select a supported upscaler.')
    if model not in spec['models']:
        raise ValueError('Select a model supported by this upscaler.')
    if factor not in spec['factors']:
        allowed = ', '.join(str(n) + '×' for n in spec['factors'])
        raise ValueError(f"{spec['label']} supports {allowed} upscaling.")
    return spec


def catalog(include_hidden=False):
    from . import catalog as metadata
    custom, _ = metadata.user_config()
    result = {k: dict(v, adapter=k) for k, v in CATALOG.items()}
    for item in custom['upscalers']:
        result[item['id']] = item
    return {k: v for k, v in result.items() if include_hidden or k not in custom['hidden']['upscalers']}


def default_kind():
    from . import catalog as metadata
    custom, _ = metadata.user_config()
    choices = catalog()
    wanted = custom['defaults'].get('upscaler', DEFAULT)
    return wanted if wanted in choices else next(iter(choices))


def prices():
    from . import catalog as metadata
    from pathlib import Path
    result = metadata.model_config.read_json(Path(__file__).with_name('prices.json'))
    cached, _ = metadata.cache()
    for kind, entry in cached.get('upscalers', {}).items():
        if entry.get('rates'):
            result['upscale'][kind] = {'rates': entry['rates'], 'checkedAt': entry['checkedAt']}
    return result
