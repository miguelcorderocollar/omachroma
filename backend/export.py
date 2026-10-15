"""Export a result through the native Save File portal, without moving it."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
from . import storage

FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}


def choose_destination(source):
    # The caller uses /usr/bin/python3 for the system PyGObject bindings.
    import gi
    gi.require_version('Gio', '2.0')
    from gi.repository import Gio, GLib

    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    loop = GLib.MainLoop()
    picked = []
    answered = []
    token = 'omachroma' + str(os.getpid())
    sender = bus.get_unique_name()[1:].replace('.', '_')
    predicted = '/org/freedesktop/portal/desktop/request/' + sender + '/' + token

    def response(connection, sender_name, path, interface, signal, params):
        code, values = params.unpack()
        answered.append(code)
        if code == 0:
            picked.extend(values.get('uris', []))
        loop.quit()

    def subscribe(path):
        return bus.signal_subscribe('org.freedesktop.portal.Desktop',
            'org.freedesktop.portal.Request', 'Response', path, None,
            Gio.DBusSignalFlags.NONE, response)

    subscriptions = [subscribe(predicted)]
    filters = [('Images', [(0, '*.jpg'), (0, '*.jpeg'), (0, '*.png'), (0, '*.webp')])]
    options = {'handle_token': GLib.Variant('s', token),
               'current_name': GLib.Variant('s', 'omachroma-' + source.parent.name + source.suffix),
               'filters': GLib.Variant('a(sa(us))', filters)}
    handle = bus.call_sync('org.freedesktop.portal.Desktop',
        '/org/freedesktop/portal/desktop', 'org.freedesktop.portal.FileChooser',
        'SaveFile', GLib.Variant('(ssa{sv})', ('', 'Save wallpaper as', options)),
        None, Gio.DBusCallFlags.NONE, -1, None).unpack()[0]
    if handle != predicted:
        subscriptions.append(subscribe(handle))
    timer = GLib.timeout_add_seconds(600, loop.quit)
    loop.run()
    if answered:
        GLib.source_remove(timer)
    for subscription in subscriptions:
        bus.signal_unsubscribe(subscription)
    if not answered:
        raise ValueError('Save dialog timed out. Try Save as again.')
    if answered[0] == 1:
        return None
    if answered[0] != 0 or not picked:
        raise ValueError('The desktop save dialog could not choose a destination.')
    return Path(GLib.filename_from_uri(picked[0])[0])


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
    with tempfile.TemporaryDirectory(prefix='.omachroma-export-', dir=destination.parent) as temp:
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
