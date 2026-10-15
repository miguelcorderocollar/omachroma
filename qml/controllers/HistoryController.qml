import QtQuick
import Quickshell.Io

Item {
  id: root
  property string backend: ""
  property var records: []
  property string error: ""
  readonly property bool busy: process.running
  signal selected(var result)
  function load() { call("--history", "") }
  function select(ident) { call("--load-history", ident) }
  function call(action, ident) {
    if (busy) return
    error = ""; process.action = action
    process.command = ["python3", backend, action].concat(ident ? [ident] : [])
    process.running = true
  }
  Process {
    id: process
    property string action: ""
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var value = JSON.parse(text)
          if (!value || value.error) { root.error = value && value.error || "History entry is missing."; return }
          if (process.action === "--history") root.records = value.records || []
          else root.selected(value)
        } catch (e) { root.error = "Could not read saved history." }
      }
    }
    onExited: { if (exitCode !== 0 && !root.error) root.error = "History could not load. Saved images remain on disk." }
  }
}
