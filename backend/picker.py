"""Native file portals with plugin-owned last-folder memory."""
import os
from pathlib import Path
from . import model_config, storage


def folder(kind):
    try:
        value = model_config.read_json(storage.DATA / 'picker.json')
        if not isinstance(value, dict) or not isinstance(value.get(kind, ''), str):
            raise ValueError('Invalid picker state.')
        path = Path(value.get(kind, '')).expanduser()
        if path.is_absolute() and path.is_dir():
            return path
    except (OSError, ValueError, TypeError):
        pass
    pictures = storage.HOME / 'Pictures'
    return pictures if pictures.is_dir() else storage.HOME


def remember(path, kind):
    path = Path(path).expanduser().resolve().parent
    try:
        value = model_config.read_json(storage.DATA / 'picker.json')
        if not isinstance(value, dict): value = {}
    except (OSError, ValueError, TypeError):
        value = {}
    value = {k: v for k, v in value.items() if k in ('images', 'export') and isinstance(v, str)}
    value[kind] = str(path)
    import json
    storage.atomic_write(storage.DATA / 'picker.json', json.dumps(value) + '\n')


def choose(method, title, *, multiple=False, source=None):
    import gi
    gi.require_version('Gio', '2.0')
    from gi.repository import Gio, GLib
    kind = 'export' if method == 'SaveFile' else 'images'
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    loop = GLib.MainLoop(); picked = []; answered = []
    token = 'omachroma' + str(os.getpid())
    sender = bus.get_unique_name()[1:].replace('.', '_')
    predicted = '/org/freedesktop/portal/desktop/request/' + sender + '/' + token
    def response(connection, sender_name, path, interface, signal, params):
        code, values = params.unpack()
        answered.append(code)
        if code == 0: picked.extend(values.get('uris', []))
        loop.quit()
    def subscribe(path):
        return bus.signal_subscribe('org.freedesktop.portal.Desktop', 'org.freedesktop.portal.Request',
            'Response', path, None, Gio.DBusSignalFlags.NONE, response)
    subscriptions = [subscribe(predicted)]
    formats = ('jpg','jpeg','png','webp','bmp','gif') if method == 'OpenFile' else ('jpg','jpeg','png','webp')
    patterns = [(0, '*.' + ext) for ext in (*formats, *(ext.upper() for ext in formats))]
    options = {'handle_token': GLib.Variant('s', token),
               'current_folder': GLib.Variant('ay', os.fsencode(folder(kind)) + b'\x00'),
               'filters': GLib.Variant('a(sa(us))', [('Images', patterns)])}
    if method == 'OpenFile': options['multiple'] = GLib.Variant('b', multiple)
    else: options['current_name'] = GLib.Variant('s', 'omachroma-' + source.parent.name + source.suffix)
    handle = bus.call_sync('org.freedesktop.portal.Desktop', '/org/freedesktop/portal/desktop',
        'org.freedesktop.portal.FileChooser', method, GLib.Variant('(ssa{sv})', ('', title, options)),
        None, Gio.DBusCallFlags.NONE, 15000, None).unpack()[0]
    if handle != predicted: subscriptions.append(subscribe(handle))
    timer = GLib.timeout_add_seconds(600, loop.quit)
    loop.run()
    if answered: GLib.source_remove(timer)
    for subscription in subscriptions: bus.signal_unsubscribe(subscription)
    if not answered: raise ValueError('File dialog timed out. Try again.')
    if answered[0] == 1: return []
    if answered[0] != 0 or not picked: raise ValueError('The desktop file dialog could not choose a file.')
    paths = [Path(GLib.filename_from_uri(uri)[0]) for uri in picked[:200]]
    try:
        remember(paths[0], kind)
    except (OSError, ValueError):
        pass
    return paths
