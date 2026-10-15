import QtQuick
import Quickshell.Io

Item {
  id: root
  readonly property bool busy: process.running
  signal selected(string target, var paths)
  signal failed(string message)
  function open(target, title, multiple) {
    if (busy) return
    process.target = target
    process.command = ["omarchy", "file", "select", "--title", title, "--extensions", "jpg jpeg png webp bmp gif"].concat(multiple ? ["--multiple"] : [])
    process.running = true
  }
  Process {
    id: process
    property string target: ""
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        var paths = String(text || "").trim().split("\n").filter(function(path) { return path !== "" })
        if (paths.length) root.selected(process.target, paths)
      }
    }
    onExited: { if (exitCode !== 0 && exitCode !== 1) root.failed("The image picker could not open. Paste a path instead.") }
  }
}
