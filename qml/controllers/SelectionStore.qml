import QtQuick
import Quickshell.Io
Item {
  id: root
  property string backend: ""
  property string wanted: ""
  function remember(ident) { if (ident) { wanted = ident; debounce.restart() } }
  function cancel() { wanted = ""; debounce.stop(); if (process.running) process.running = false }
  Timer {
    id: debounce; interval: 120
    onTriggered: {
      if (process.running || !root.wanted) return
      process.command = ["python3", root.backend, "--remember-output", root.wanted]
      root.wanted = ""; process.running = true
    }
  }
  Process {
    id: process
    onExited: { if (root.wanted) debounce.restart() }
  }
}
