"""Save retained images into a selected theme, without changing the desktop."""
import hashlib
from pathlib import Path
import re
from . import export, storage


def destination(source, theme):
    storage.theme_name(theme)
    source = Path(source).expanduser().resolve()
    tag = source.parent.name
    if not re.fullmatch(r'\d{8}-\d{6}-[a-f0-9]{8}', tag):
        tag = hashlib.sha256(str(source).encode()).hexdigest()[:16]
    return storage.BACKGROUNDS / theme / ('01-omatinta-' + tag + '.jpg')


def installed_path(source, theme, hint=''):
    if not source or not theme:
        return ''
    try:
        expected = destination(source, theme)
        if hint:
            hinted = Path(hint)
            if hinted.parent.resolve() == expected.parent.resolve() and hinted.name.startswith(('01-omatinta-', '01-omachroma-', '01-omapaper-')):
                expected = hinted
        candidates = [expected]
        for legacy_prefix in ('01-omachroma-', '01-omapaper-'):
            candidates.append(expected.with_name(expected.name.replace('01-omatinta-', legacy_prefix, 1)))
        for candidate in candidates:
            if candidate.is_file() and not candidate.is_symlink():
                return str(candidate.resolve())
    except (ValueError, OSError):
        pass
    return ''


def save_image(source, theme):
    from .jobs import image
    source = image(source)
    if theme not in storage.themes():
        raise ValueError('Choose an installed theme before saving the wallpaper.')
    target = destination(source, theme)
    if storage.BACKGROUNDS.is_symlink() or target.parent.is_symlink():
        raise ValueError('The theme wallpaper directory must not be a symlink.')
    target.parent.mkdir(parents=True, exist_ok=True)
    saved = export.copy_image(source, target)
    return {'installedPath': saved, 'installedTheme': theme}
