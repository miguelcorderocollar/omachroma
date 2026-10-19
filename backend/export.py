"""Export a result through the native Save File portal, without moving it."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
from . import storage

FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}


def choose_destination(source):
    from . import picker
    paths = picker.choose('SaveFile', 'Save wallpaper as', source=source)
    return paths[0] if paths else None


def copy_image(source, destination):
    source = Path(source).expanduser().resolve()
    destination = Path(destination).expanduser()
    if not source.is_file() or source.suffix.lower() not in storage.EXTENSIONS:
        raise ValueError('The saved image is missing or unsupported. Choose another history entry.')
    if destination.is_symlink():
        raise ValueError('Choose a destination file that is not a symlink.')
    if not destination.suffix:
        destination = destination.with_suffix(source.suffix)
    if destination.suffix.lower() not in FORMATS:
        raise ValueError('Save with a .jpg, .jpeg, .png or .webp extension.')
    if source == destination.resolve():
        return str(source)
    # Atomic export keeps the original and any existing destination intact
    # if copying or format conversion fails.
    with tempfile.TemporaryDirectory(prefix='.omatinta-export-', dir=destination.parent) as temp:
        staged = Path(temp) / ('image' + destination.suffix.lower())
        same_format = source.suffix.lower() == destination.suffix.lower() or (
            source.suffix.lower() in {'.jpg', '.jpeg'} and destination.suffix.lower() in {'.jpg', '.jpeg'})
        if same_format:
            shutil.copyfile(source, staged)
        else:
            result = subprocess.run(['magick', str(source), str(staged)], capture_output=True, timeout=60)
            if result.returncode:
                raise ValueError('Could not convert the image. Try saving with its original extension.')
        if destination.is_symlink():
            raise ValueError('The destination became a symlink. Choose another file.')
        staged.replace(destination)
    return str(destination.resolve())


def save_image(source):
    source = Path(source).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() not in storage.EXTENSIONS:
        raise ValueError('The saved image is missing. Choose another history entry.')
    try:
        destination = choose_destination(source)
    except ValueError:
        raise
    except Exception:
        raise ValueError('The desktop save dialog could not open. Try Save as again.') from None
    if destination is None:
        return {'cancelled': True}
    return {'path': copy_image(source, destination), 'cancelled': False}
