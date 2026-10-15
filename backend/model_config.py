"""Validate user-owned model choices. No arbitrary URLs, headers or shell code."""
import copy
import json
import math
import re
import stat
from pathlib import Path

MAX_BYTES = 256 * 1024
EMPTY = {'schemaVersion': 1, 'models': {'fal': [], 'openrouter': []},
         'upscalers': [], 'hidden': {'fal': [], 'openrouter': [], 'upscalers': []}, 'defaults': {}}
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)+$')
KINDS = ('seedvr', 'precision', 'aura', 'clarity', 'creative')


def read_json(path):
    path = Path(path)
    info = path.stat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
        raise ValueError('Configuration must be a regular file smaller than 256 KB.')
    def invalid(value):
        raise ValueError('Non-finite JSON numbers are not supported.')
    return json.loads(path.read_text(), parse_constant=invalid)


def identifier(value):
    if not isinstance(value, str) or len(value) > 180 or not ID.fullmatch(value) or '..' in value:
        raise ValueError('Model IDs must be provider paths such as author/model, without URLs.')
    return value


def text(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 180 or any(ord(c) < 32 for c in value):
        raise ValueError(name + ' must be a short, non-empty string.')
    return value


def number(value):
    try:
        valid = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError('Prices must be finite, non-negative numbers.')
    return value


def strings(value, choices=None):
    if not isinstance(value, list) or len(value) > 100 or any(not isinstance(v, str) for v in value):
        raise ValueError('Expected a list of strings.')
    if len(set(value)) != len(value) or choices is not None and any(v not in choices for v in value):
        raise ValueError('Duplicate or unsupported choices.')
    return value


def model(value, provider):
    allowed = {'value', 'label', 'adapter', 'resolutions', 'qualityOptions', 'maxImages', 'price', 'dimensions'}
    if not isinstance(value, dict) or set(value) - allowed:
        raise ValueError('Unknown model field. See docs/models.md.')
    result = copy.deepcopy(value)
    identifier(result.get('value')); text(result.get('label'), 'Model label')
    adapters = ('aspect', 'landscape', 'auto') if provider == 'fal' else ('openrouter',)
    if result.get('adapter') not in adapters:
        raise ValueError('Choose a documented adapter supported by the provider.')
    resolutions = strings(result.get('resolutions', []), ('1K', '2K', '4K'))
    qualities = strings(result.get('qualityOptions', []), ('auto', 'low', 'medium', 'high', 'xhigh', 'max'))
    if provider == 'fal' and result['adapter'] != 'auto' and not resolutions:
        raise ValueError('This fal adapter requires at least one resolution.')
    if result['adapter'] == 'auto' and not qualities:
        raise ValueError('The auto adapter requires qualityOptions.')
    result['resolutions'] = resolutions
    count = result.get('maxImages', 5)
    if isinstance(count, bool) or not isinstance(count, int) or not 2 <= count <= 32:
        raise ValueError('maxImages must be between 2 and 32.')
    result['maxImages'] = count
    price = result.get('price', {})
    if not isinstance(price, dict) or set(price) - {'1K', '2K', '4K', 'image', 'outputToken', 'inputImage'}:
        raise ValueError('Unsupported price fields.')
    for amount in price.values():
        number(amount)
    dimensions = result.get('dimensions', {})
    if not isinstance(dimensions, dict) or set(dimensions) - set(resolutions):
        raise ValueError('Dimensions must refer to supported resolutions.')
    for size in dimensions.values():
        if not isinstance(size, list) or len(size) != 2 or any(isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 16384 for n in size):
            raise ValueError('Dimensions must contain two positive pixel sizes, at most 16384.')
    if result['adapter'] == 'landscape' and set(dimensions) != set(resolutions):
        raise ValueError('The landscape adapter needs dimensions for every resolution.')
    return result


def validate(value, bundled, upscale_catalog):
    if not isinstance(value, dict) or set(value) - set(EMPTY) or (type(value.get('schemaVersion', 1)) is not int or value.get('schemaVersion', 1) != 1):
        raise ValueError('Unsupported model configuration schema.')
    result = copy.deepcopy(EMPTY)
    result.update(copy.deepcopy(value))
    if not isinstance(result['models'], dict) or set(result['models']) - {'fal', 'openrouter'}:
        raise ValueError('models must contain fal and/or openrouter lists.')
    merged = {}
    for provider in ('fal', 'openrouter'):
        rows = result['models'].get(provider, [])
        if not isinstance(rows, list) or len(rows) > 40:
            raise ValueError('At most 40 configured models per provider are supported.')
        rows = [model(row, provider) for row in rows]
        if len({row['value'] for row in rows}) != len(rows):
            raise ValueError('Duplicate configured model IDs.')
        result['models'][provider] = rows
        merged[provider] = {row['value']: row for row in bundled[provider]}
        merged[provider].update({row['value']: row for row in rows})
    rows = result['upscalers']
    if not isinstance(rows, list) or len(rows) > 20:
        raise ValueError('At most 20 configured upscalers are supported.')
    kinds = dict(upscale_catalog)
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) - {'id', 'label', 'endpoint', 'adapter', 'models', 'factors', 'description'}:
            raise ValueError('Unknown upscaler field.')
        ident = text(row.get('id'), 'Upscaler ID')
        if not re.fullmatch(r'[a-z][a-z0-9_-]{0,50}', ident) or ident in seen or ident == 'none':
            raise ValueError('Invalid or duplicate upscaler ID.')
        seen.add(ident); text(row.get('label'), 'Upscaler label'); identifier(row.get('endpoint'))
        if row.get('adapter') not in KINDS:
            raise ValueError('Unsupported upscaler adapter.')
        models = strings(row.get('models', []))
        if not models or any(not m.strip() or len(m) > 100 for m in models):
            raise ValueError('Upscaler models must be non-empty short names.')
        factors = row.get('factors', [])
        if not isinstance(factors, list) or not factors or any(isinstance(n, bool) or n not in (2, 4) for n in factors) or len(set(factors)) != len(factors):
            raise ValueError('Upscaler factors must be 2 and/or 4.')
        if row['adapter'] == 'aura' and factors != [4]:
            raise ValueError('Aura requires fixed 4× output.')
        if not isinstance(row.get('description', ''), str) or len(row.get('description', '')) > 1000:
            raise ValueError('Upscaler description is too long.')
        kinds[ident] = row
    hidden = result['hidden']
    if not isinstance(hidden, dict) or set(hidden) - {'fal', 'openrouter', 'upscalers'}:
        raise ValueError('Unsupported hidden-model group.')
    for provider in ('fal', 'openrouter', 'upscalers'):
        known = merged[provider] if provider != 'upscalers' else kinds
        values = strings(hidden.get(provider, []))
        if any(v not in known or v == 'none' for v in values):
            raise ValueError('Hidden entries must refer to configured choices; None cannot be hidden.')
        if provider != 'upscalers' and not set(known) - set(values):
            raise ValueError('Keep at least one editing model visible for each provider.')
        hidden[provider] = values
    defaults = result['defaults']
    if not isinstance(defaults, dict) or set(defaults) - {'fal', 'openrouter', 'upscaler', 'upscaleModel', 'upscaleFactor'}:
        raise ValueError('Unsupported default field.')
    for provider in ('fal', 'openrouter'):
        if provider in defaults and (not isinstance(defaults[provider], str) or defaults[provider] not in merged[provider] or defaults[provider] in hidden[provider]):
            raise ValueError('Default models must exist and remain visible.')
    kind = defaults.get('upscaler', 'seedvr')
    if not isinstance(kind, str) or kind not in kinds or kind in hidden['upscalers']:
        raise ValueError('Default upscaler must exist and remain visible.')
    spec = kinds[kind]
    if 'upscaleModel' in defaults and defaults['upscaleModel'] not in spec['models']:
        raise ValueError('Default upscale model does not belong to the chosen upscaler.')
    if 'upscaleFactor' in defaults and (isinstance(defaults['upscaleFactor'], bool) or defaults['upscaleFactor'] not in spec['factors']):
        raise ValueError('Unsupported default upscale factor.')
    return result
