"""Register and remove only plugin-managed launcher entries."""
import os
from pathlib import Path
from . import storage


def install():
    plugin = Path(__file__).resolve().parent.parent
    dest = Path(os.environ.get('XDG_DATA_HOME', storage.HOME / '.local/share')) / 'applications/omatinta.desktop'
    template = (plugin / 'omatinta.desktop').read_text()
    if dest.is_symlink():
        raise ValueError('Launcher entry is a symlink; left unchanged.')
    if dest.exists() and 'X-Omatinta-Managed=true' not in dest.read_text() and dest.read_text() != template:
        # Recognize the original repository-owned template during migration.
        if dest.read_text().replace('Icon=image-wallpaper', 'Icon=@ICON@') != template.replace('X-Omatinta-Managed=true\n', ''):
            raise ValueError('Custom launcher entry left unchanged.')
    text = template.replace('@ICON@', str(plugin / 'assets/omatinta.svg'))
    if not dest.exists() or dest.read_text() != text:
        storage.atomic_write(dest, text, 0o644)
    # Clean previous managed names after a successful install.
    for legacy_name, marker in (('omachroma', 'X-Omachroma-Managed=true'),
                                ('omapaper', 'X-OmaPaper-Managed=true')):
        legacy_path = dest.parent / (legacy_name + '.desktop')
        try:
            if legacy_path.is_file() and not legacy_path.is_symlink():
                legacy_text = legacy_path.read_text().splitlines()
                if marker in legacy_text and 'Exec=omarchy-shell shell summon mikelon797.' + legacy_name in legacy_text:
                    legacy_path.unlink()
        except OSError:
            pass


def _remove_name(name, marker):
    path = Path(os.environ.get('XDG_DATA_HOME', storage.HOME / '.local/share')) / ('applications/' + name + '.desktop')
    if path.is_symlink():
        raise ValueError('Launcher entry is a symlink; left unchanged.')
    if not path.exists():
        return
    text = path.read_text()
    if marker not in text.splitlines() or 'Exec=omarchy-shell shell summon mikelon797.' + name not in text.splitlines():
        raise ValueError('Custom launcher entry left unchanged.')
    path.unlink()


def remove(legacy=False):
    if legacy:
        _remove_name('omapaper', 'X-OmaPaper-Managed=true')
        return
    _remove_name('omatinta', 'X-Omatinta-Managed=true')
