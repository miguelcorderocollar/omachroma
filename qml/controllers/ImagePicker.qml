import QtQuick
import Quickshell.Io

Item {
  id: root
  property string backend: ""
  readonly property bool busy: process.running
  signal selected(string target, var paths)
  signal failed(string message)
  function open(target, title, multiple) {
    if (busy) return
    process.target = target
    process.command = ["/usr/bin/python3", backend, "--pick-images", "--picker-title", title].concat(multiple ? ["--multiple"] : [])
    process.running = true
  }
  Process {
    id: process
    property string target: ""
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var paths = JSON.parse(text).paths || []
          if (paths.length) root.selected(process.target, paths)
        } catch (e) { if (text.trim()) root.failed("Could not read the selected images.") }
      }
    }
    onExited: { if (exitCode !== 0 && exitCode !== 1) root.failed("The image picker could not open. Paste a path instead.") }
  }
}
