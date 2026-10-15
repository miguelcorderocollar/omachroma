import QtQuick
import Quickshell.Io

// Register the launcher on enable, even before the panel is first summoned.
Item {
  readonly property string backend: decodeURIComponent(String(Qt.resolvedUrl("../generate-theme-wallpaper.py")).replace(/^file:\/\//, ""))
  Process { id: install; command: ["python3", backend, "--install-launcher"] }
  Component.onCompleted: install.running = true
}
