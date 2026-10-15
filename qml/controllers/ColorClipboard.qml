import QtQuick
import Quickshell.Io
Item {
  id: root
  signal copied(int index, string theme)
  signal failed()
  function copy(value, index, theme) {
    if (process.running) return
    process.value = value; process.index = index; process.theme = theme
    process.running = true
  }
  Process {
    id: process
    property string value: ""
    property int index: -1
    property string theme: ""
    command: ["wl-copy"]; stdinEnabled: true
    onRunningChanged: { if (running) stdinEnabled = true }
    onStarted: { write(value); stdinEnabled = false }
    onExited: { if (exitCode === 0) root.copied(index, theme); else root.failed() }
  }
}
