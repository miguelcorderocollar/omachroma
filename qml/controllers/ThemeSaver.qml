import QtQuick
import Quickshell.Io
Item {
  id: root
  property string backend: ""
  property var queue: []
  property var current: null
  property string error: ""
  property string message: ""
  property int total: 0
  property int count: 0
  readonly property bool busy: process.running || queue.length > 0
  signal saved(var record)
  function save(records) {
    if (busy || !records.length) return
    error = ""; message = ""; count = 0; total = records.length; queue = records.slice(); next()
  }
  function next() {
    if (process.running || !queue.length) return
    current = queue[0]; queue = queue.slice(1)
    process.command = ["python3", backend, "--save-to-theme", current.resultPath, "--theme", current.theme].concat(current.id ? ["--job-id", current.id] : [])
    process.running = true
  }
  Process {
    id: process
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try { root.saved(Object.assign({}, root.current, JSON.parse(text))) }
        catch (e) { root.error = "Could not read the theme save result."; root.queue = [] }
      }
    }
    stderr: StdioCollector {
      waitForEnd: true
      onStreamFinished: { if (text.trim()) { try { root.error = JSON.parse(text).message } catch(e) { root.error = "Could not save " + root.current.theme + "." }; root.queue = [] } }
    }
    onExited: {
      if (exitCode !== 0) { root.queue = []; root.error = root.error || "Could not save the selected output." }
      else if (!root.error) { root.count++; root.message = "Saved " + root.count + "/" + root.total + " outputs." }
      Qt.callLater(root.next)
    }
  }
}
