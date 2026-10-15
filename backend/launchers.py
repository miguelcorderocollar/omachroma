"""Register and remove only plugin-managed launcher entries."""
import os
from pathlib import Path
from . import storage


def install():
    plugin = Path(__file__).resolve().parent.parent
    dest = Path(os.environ.get('XDG_DATA_HOME', storage.HOME / '.local/share')) / 'applications/omachroma.desktop'
    template = (plugin / 'omachroma.desktop').read_text()
    if dest.is_symlink():
        raise ValueError('Launcher entry is a symlink; left unchanged.')
    if dest.exists() and 'X-Omachroma-Managed=true' not in dest.read_text() and dest.read_text() != template:
        # Recognize the original repository-owned template during migration.
        if dest.read_text().replace('Icon=image-wallpaper', 'Icon=@ICON@') != template.replace('X-Omachroma-Managed=true\n', ''):
            raise ValueError('Custom launcher entry left unchanged.')
    text = template.replace('@ICON@', str(plugin / 'assets/omachroma.svg'))
    if not dest.exists() or dest.read_text() != text:
        storage.atomic_write(dest, text, 0o644)


def remove(legacy=False):
    name = 'omapaper' if legacy else 'omachroma'
    path = Path(os.environ.get('XDG_DATA_HOME', storage.HOME / '.local/share')) / ('applications/' + name + '.desktop')
    if path.is_symlink():
        raise ValueError('Launcher entry is a symlink; left unchanged.')
    if not path.exists():
        return
    text = path.read_text()
    marker = 'X-OmaPaper-Managed=true' if legacy else 'X-Omachroma-Managed=true'
    if marker not in text.splitlines() or 'Exec=omarchy-shell shell summon mikelon797.' + name not in text.splitlines():
        raise ValueError('Custom launcher entry left unchanged.')
    path.unlink()
