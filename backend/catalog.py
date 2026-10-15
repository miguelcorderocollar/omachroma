"""Curated adapters, user choices and last-good provider metadata."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from urllib.parse import quote, urlencode

from . import model_config

BUNDLE = model_config.read_json(Path(__file__).with_name('models.json'))
MODELS = BUNDLE['models']


class RefreshTimeout(Exception):
    """Hard CLI deadline, distinct from recoverable per-request failures."""


def user_config(strict=False):
    from . import storage, upscalers
    path = storage.DATA / 'models.json'
    try:
        value = model_config.read_json(path) if path.exists() else {}
        return model_config.validate(value, MODELS, upscalers.CATALOG), ''
    except (OSError, ValueError, TypeError, KeyError):
        if strict:
            raise ValueError('Invalid model configuration. See docs/models.md.') from None
        return copy.deepcopy(model_config.EMPTY), 'Model configuration could not load. Bundled choices are active; repair models.json in Settings.'


def save(value):
    from . import storage, upscalers
    checked = model_config.validate(value, MODELS, upscalers.CATALOG)
    encoded = json.dumps(checked, indent=2) + '\n'
    if len(encoded.encode()) > model_config.MAX_BYTES:
        raise ValueError('Model configuration exceeds the 256 KB limit.')
    storage.atomic_write(storage.DATA / 'models.json', encoded)
    return checked


def cache():
    from . import storage
    path = storage.DATA / 'catalog-cache.json'
    try:
        result = model_config.read_json(path) if path.exists() else {}
        if not isinstance(result, dict) or result.get('schemaVersion', 1) != 1:
            raise ValueError('Invalid cache schema.')
        for group in ('fal', 'openrouter', 'upscalers'):
            rows = result.get(group, {})
            if not isinstance(rows, dict) or len(rows) > 100:
                raise ValueError('Invalid cache group.')
            for entry in rows.values():
                if not isinstance(entry, dict) or not isinstance(entry.get('available', True), bool):
                    raise ValueError('Invalid cache entry.')
                if not isinstance(entry.get('checkedAt'), str) or not entry['checkedAt']:
                    raise ValueError('Invalid cache timestamp.')
                rates = entry.get('rates', [])
                if not isinstance(rates, list) or len(rates) > 50:
                    raise ValueError('Invalid cache rates.')
                for rate in rates:
                    if not isinstance(rate, dict) or not isinstance(rate.get('unit'), str) or not isinstance(rate.get('billable'), str):
                        raise ValueError('Invalid price unit.')
                    model_config.number(rate.get('usd'))
                    if not isinstance(rate.get('conditional', False), bool):
                        raise ValueError('Invalid price condition flag.')
        return result, ''
    except (ValueError, OSError, TypeError):
        return {}, 'Price cache could not load. Bundled rates are active; Refresh prices to rebuild it.'


def models(provider, include_hidden=False):
    config, _ = user_config()
    by_id = {item['value']: copy.deepcopy(item) for item in MODELS.get(provider, [])}
    manual = set()
    for item in config['models'].get(provider, []):
        by_id[item['value']] = copy.deepcopy(item)
        if item.get('price'):
            manual.add(item['value'])
    metadata, _ = cache()
    for ident, item in by_id.items():
        entry = metadata.get(provider, {}).get(ident, {})
        item['available'] = entry.get('available', True)
        item['hidden'] = ident in config['hidden'].get(provider, [])
        item['priceChecked'] = BUNDLE['checkedAt']
        item['priceSource'] = 'manual' if ident in manual else 'bundled'
        if ident in manual:
            item['priceChecked'] = 'user configuration'
        elif entry.get('rates'):
            item['rates'] = entry['rates']
            item['priceChecked'] = entry['checkedAt']
            item['priceSource'] = 'provider'
        if 'checkedAt' in entry:
            item['availabilityChecked'] = entry.get('availabilityChecked', entry['checkedAt'])
    return [item for item in by_id.values() if include_hidden or not item['hidden']]


def default_model(provider):
    config, _ = user_config()
    visible = models(provider)
    wanted = config['defaults'].get(provider, {'fal': 'google/nano-banana-2.1/edit', 'openrouter': 'google/gemini-nano-banana-2.1'}[provider])
    return wanted if any(m['value'] == wanted for m in visible) else visible[0]['value']


def metadata_request(url, key, provider, timeout=8):
    from . import providers
    return json.loads(providers.request(url, key=key, provider=provider, timeout=timeout, limit=2 * 1024 * 1024))


def rates(value):
    result = []
    if not isinstance(value, list) or len(value) > 50:
        raise ValueError('Provider returned invalid pricing metadata.')
    for item in value:
        if not isinstance(item, dict):
            raise ValueError('Provider returned an invalid price.')
        amount = model_config.number(item.get('cost_usd', item.get('unit_price')))
        unit = model_config.text(item.get('unit'), 'Price unit')
        billable = model_config.text(item.get('billable', 'output'), 'Billing target')
        row = {'usd': amount, 'unit': unit, 'billable': billable}
        # Preserve uncertainty rather than interpreting unknown provider conditions.
        row['conditional'] = any(k not in ('cost_usd', 'unit_price', 'unit', 'billable', 'currency', 'endpoint_id') for k in item)
        if row not in result:
            result.append(row)
    return result


def refresh():
    from . import storage, upscalers
    custom, _ = user_config(strict=True)
    manual = {p: {m['value'] for m in custom['models'][p] if m.get('price')} for p in ('fal', 'openrouter')}
    keys = storage.credentials()
    previous, _ = cache()
    result = copy.deepcopy(previous)
    result['schemaVersion'] = 1
    warnings = []
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    started = time.monotonic()
    updated = availability_updated = 0
    changed = False
    def fetch(url, key, provider):
        remaining = 75 - (time.monotonic() - started)
        if remaining <= 0:
            raise ValueError('Metadata refresh reached its 75-second deadline.')
        return metadata_request(url, key, provider, min(8, remaining))
    def remember(group, ident, data, rate=True):
        nonlocal updated, availability_updated, changed
        result.setdefault(group, {})[ident] = {'checkedAt': stamp, **data}
        changed = True
        updated += int(rate)
        availability_updated += int(group == 'openrouter')
    if keys.get('FAL_KEY'):
        try:
            editing = models('fal', include_hidden=True)
            engines = upscalers.catalog(include_hidden=True)
            ids = list(dict.fromkeys([m['value'] for m in editing] + [m['endpoint'] for k, m in engines.items() if k != 'none']))
            pricing = {}
            for offset in range(0, len(ids), 50):
                data = fetch('https://api.fal.ai/v1/models/pricing?' + urlencode({'endpoint_id': ','.join(ids[offset:offset + 50])}), keys['FAL_KEY'], 'fal')
                if not isinstance(data.get('prices'), list) or data.get('has_more'):
                    raise ValueError('Incomplete fal price response; keeping the previous cache.')
                for row in data['prices']:
                    if not isinstance(row, dict) or not isinstance(row.get('endpoint_id'), str):
                        warnings.append('fal returned a malformed rate row; it was ignored.')
                        continue
                    if row.get('currency', 'USD') != 'USD':
                        continue
                    try:
                        pricing[row['endpoint_id']] = rates([row])
                    except ValueError:
                        warnings.append('fal returned an invalid rate; the previous value was retained.')
            for m in editing:
                if m['value'] in pricing and m['value'] not in manual['fal']:
                    remember('fal', m['value'], {'rates': pricing[m['value']]})
            for kind, m in engines.items():
                if kind != 'none' and m['endpoint'] in pricing:
                    remember('upscalers', kind, {'rates': pricing[m['endpoint']]})
            if any(ident not in pricing for ident in ids):
                warnings.append('fal omitted some rates; their previous or bundled values remain active.')
        except (ValueError, OSError, KeyError, TypeError):
            warnings.append('fal prices could not refresh. Previous or bundled rates remain active.')
    else:
        warnings.append('fal key missing; fal rates were not refreshed.')
    if keys.get('OPENROUTER_API_KEY'):
        try:
            data = fetch('https://openrouter.ai/api/v1/images/models', keys['OPENROUTER_API_KEY'], 'openrouter')
            if not isinstance(data.get('data'), list):
                raise ValueError('Invalid OpenRouter catalog.')
            available = {m['id'] for m in data['data'] if isinstance(m, dict) and isinstance(m.get('id'), str)}
            complete = len(available) == len(data['data'])
            if not complete:
                warnings.append('OpenRouter returned malformed catalog rows; only confirmed availability was updated.')
            for m in models('openrouter', include_hidden=True):
                ident = m['value']
                if ident not in available:
                    if not complete:
                        continue
                    old = previous.get('openrouter', {}).get(ident, {})
                    remember('openrouter', ident, {**old, 'available': False, 'availabilityChecked': stamp}, rate=False)
                    continue
                if ident in manual['openrouter']:
                    old = previous.get('openrouter', {}).get(ident, {})
                    remember('openrouter', ident, {**old, 'available': True, 'availabilityChecked': stamp}, rate=False)
                    continue
                try:
                    info = fetch('https://openrouter.ai/api/v1/images/models/' + quote(ident, safe='/') + '/endpoints', keys['OPENROUTER_API_KEY'], 'openrouter')
                    endpoints = info.get('endpoints')
                    if not isinstance(endpoints, list) or not endpoints:
                        raise ValueError('No pricing endpoints returned.')
                    combined = []
                    for endpoint in endpoints:
                        combined.extend(rates(endpoint['pricing']))
                    remember('openrouter', ident, {'available': True, 'rates': combined[:50]})
                except (ValueError, OSError, KeyError, TypeError):
                    warnings.append(m['label'] + ': previous rates retained after refresh failure.')
        except (ValueError, OSError, KeyError, TypeError):
            warnings.append('OpenRouter catalog could not refresh. Previous metadata remains active.')
    else:
        warnings.append('OpenRouter key missing; its rates were not refreshed.')
    if changed:
        storage.atomic_write(storage.DATA / 'catalog-cache.json', json.dumps(result, indent=2) + '\n')
    return {'updated': updated, 'availabilityUpdated': availability_updated, 'warnings': warnings}
