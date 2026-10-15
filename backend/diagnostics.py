"""Credential-free local dependency checks."""
import shutil
import subprocess
import sys


def check():
    commands = {name: bool(shutil.which(name)) for name in ('omarchy', 'omarchy-shell', 'magick', 'xdg-open', 'wl-copy')}
    gio = subprocess.run(['/usr/bin/python3', '-c', 'import gi; gi.require_version("Gio", "2.0"); from gi.repository import Gio'],
                         capture_output=True, timeout=10).returncode == 0
    portal = False
    try:
        result = subprocess.run(['gdbus', 'introspect', '--session', '--dest', 'org.freedesktop.portal.Desktop',
                                 '--object-path', '/org/freedesktop/portal/desktop'], capture_output=True, timeout=10)
        portal = result.returncode == 0 and b'org.freedesktop.portal.FileChooser' in result.stdout
    except (OSError, subprocess.TimeoutExpired):
        pass
    return {'pythonSupported': sys.version_info >= (3, 11), 'commands': commands,
            'systemPyGObject': gio, 'fileChooserPortal': portal,
            'ready': all(commands.values()) and gio and portal}
