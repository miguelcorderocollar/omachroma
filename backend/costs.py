"""Parse provider-reported costs and build safe job cost summaries."""
import math


def amount(value):
    """Accept finite, non-negative provider amounts (including numeric strings)."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            value = float(value)
        except ValueError:
            return None
    if not isinstance(value, (int, float)):
        return None
    try:
        value = float(value)
    except OverflowError:
        return None
    return value if math.isfinite(value) and value >= 0 else None


def from_response(result):
    """Return only an explicit usage.cost field; never infer from catalog prices."""
    usage = result.get('usage') if isinstance(result, dict) else None
    return amount(usage.get('cost')) if isinstance(usage, dict) else None


def summary(edit=None, upscale=None, *, edit_requested=True, upscale_requested=False):
    edit = amount(edit)
    upscale = amount(upscale)
    edit_requested = bool(edit_requested)
    upscale_requested = bool(upscale_requested)
    complete = (not edit_requested or edit is not None) and (not upscale_requested or upscale is not None)
    total = None
    if complete:
        total = (edit if edit_requested else 0.0) + (upscale if upscale_requested else 0.0)
    return {'edit': edit, 'upscale': upscale, 'total': total, 'complete': complete,
            'upscaleRequested': upscale_requested}


def normalize_summary(value):
    """Validate the public persisted/event summary shape."""
    if not isinstance(value, dict):
        raise ValueError('Invalid cost summary.')
    if not isinstance(value.get('complete'), bool) or not isinstance(value.get('upscaleRequested'), bool):
        raise ValueError('Invalid cost summary flags.')
    edit = amount(value.get('edit'))
    upscale = amount(value.get('upscale'))
    total = amount(value.get('total'))
    if value.get('edit') is not None and edit is None:
        raise ValueError('Invalid edit cost.')
    if value.get('upscale') is not None and upscale is None:
        raise ValueError('Invalid upscale cost.')
    if value.get('total') is not None and total is None:
        raise ValueError('Invalid total cost.')
    if value['complete']:
        if value['upscaleRequested'] and upscale is None:
            raise ValueError('Incomplete upscale cost summary.')
        expected = (edit or 0.0) + (upscale or 0.0)
        if total is None or not math.isclose(total, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError('Inconsistent total cost.')
    elif total is not None:
        raise ValueError('Incomplete summaries cannot have a total.')
    return {'edit': edit, 'upscale': upscale, 'total': total,
            'complete': value['complete'], 'upscaleRequested': value['upscaleRequested']}
