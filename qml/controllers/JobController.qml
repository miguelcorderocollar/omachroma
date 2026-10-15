import QtQuick
import Quickshell.Io

Item {
  id: root
  property string backend: ""
  property string state: "idle"
  property string status: "Choose source images, a theme and at least one reference."
  property string error: ""
  property string resultPath: ""
  property string jobId: ""
  property string resultJobId: ""
  property string installedPath: ""
  property string installedTheme: ""
  property string runTheme: ""
  property var cost: null
  property string actionMessage: ""
  property string actionError: ""
  property var queue: []
  property var activeCommand: null
  property string activeResultPath: ""
  signal outputReceived(var record)
  property int batchIndex: 0
  property int batchTotal: 0
  property int warningCount: 0
  readonly property bool busy: runProc.running || queue.length > 0
  readonly property bool actionBusy: exportProc.running || setProc.running || clearProc.running
  readonly property string displayStatus: actionBusy ? (exportProc.running ? "Choose where to save the image…" : clearProc.running ? "Clearing preview…" : "Saving to theme…") : actionMessage || (busy && batchTotal > 1 ? "Output " + batchIndex + "/" + batchTotal + " · " + (activeCommand && activeCommand.label ? activeCommand.label + " · " : "") : "") + status
  property bool cancelled: false
  property bool timedOut: false
  signal finished()
  function restore(value) {
    if (busy || actionBusy || !value) return
    jobId = value.id || ""
    resultPath = value.resultExists ? value.resultPath : value.previousResultPath || ""
    resultJobId = value.resultExists ? value.id : value.previousResultId || ""
    installedPath = value.installedPath || value.previousInstalledPath || ""
    installedTheme = installedPath ? (value.installedPath ? value.installedTheme || value.theme : value.previousInstalledTheme) || "" : ""
    cost = value.cost || null
    state = value.status || "done"
    status = value.message === "done" ? "Saved wallpaper." : value.message || "Saved wallpaper."
    error = value.error || ""
    if (state === "running") { state = "error"; status = "Job interrupted."; error = "The previous job stopped. Any saved preview remains available in History." }
    if (value.resultPath && !value.resultExists) error = error || "The saved image is missing. Choose another history entry."
    actionMessage = ""; actionError = ""; batchIndex = 0; batchTotal = 0
  }
  function clear() {
    if (busy || actionBusy) return
    resultPath = ""; jobId = ""; resultJobId = ""; installedPath = ""; installedTheme = ""; cost = null; state = "idle"; error = ""; status = ""
    actionMessage = ""; actionError = ""; batchIndex = 0; batchTotal = 0
    clearProc.command = ["python3", backend, "--clear-preview"]
    clearProc.running = true
  }
  function start(argv, theme) { startBatch([argv], theme) }
  function startBatch(commands, theme) {
    if (busy || actionBusy || !commands.length) return
    cancelled = false; timedOut = false; error = ""; actionMessage = ""; actionError = ""
    batchIndex = 0; batchTotal = commands.length; warningCount = 0; runTheme = theme || ""; cost = null
    queue = commands.slice(); beginNext()
  }
  function beginNext() {
    if (!queue.length || cancelled || timedOut) return
    var command = queue[0]; queue = queue.slice(1); batchIndex++
    activeCommand = command.argv ? command : {argv: command, theme: runTheme}
    var argv = activeCommand.argv
    runTheme = activeCommand.theme || runTheme; activeResultPath = ""
    state = "working"; status = "Preparing images…"; jobId = ""; cost = null
    runProc.command = ["python3", backend].concat(argv, ["--run"])
    runProc.running = true
  }
  function finishOutput() {
    if (!activeCommand || !activeCommand.key) return
    root.outputReceived({key: activeCommand.key, id: jobId, name: activeCommand.name,
      sourcePath: activeCommand.sourcePath, theme: activeCommand.theme,
      resultPath: activeResultPath, resultExists: activeResultPath !== "",
      status: state === "done" ? "done" : cancelled ? "cancelled" : "failed",
      installedPath: activeResultPath ? installedPath : "", installedTheme: activeResultPath ? installedTheme : "",
      cost: cost, error: error, message: status})
  }
  function cancel() {
    if (!busy || cancelled) return
    cancelled = true; queue = []
    status = "Stopping; keeping saved images…"
    if (runProc.running) runProc.signal(15)
    else { state = "cancelled"; status = "Batch stopped."; finished() }
  }
  function saveToTheme(theme) {
    if (busy || actionBusy || !resultPath || !theme) return
    actionError = ""; actionMessage = ""
    setProc.command = ["python3", backend, "--save-to-theme", resultPath, "--theme", theme].concat(resultJobId ? ["--job-id", resultJobId] : [])
    setProc.running = true
  }
  function openFolder() {
    if (folderProc.running || !resultPath) return
    var path = installedPath || resultPath
    folderProc.command = ["xdg-open", path.slice(0, path.lastIndexOf("/"))]
    folderProc.running = true
  }
  function saveAs() {
    if (busy || actionBusy || !resultPath) return
    actionError = ""; actionMessage = ""
    exportProc.command = ["/usr/bin/python3", backend, "--export-image", resultPath]
    exportProc.running = true
  }
  Process {
    id: runProc
    stdout: SplitParser {
      onRead: {
        try {
          var event = JSON.parse(data)
          if (event.jobId) root.jobId = event.jobId
          if (event.message) root.status = event.message
          if (event.path) { root.activeResultPath = event.path; root.resultPath = event.path; root.resultJobId = event.jobId || root.jobId; root.installedPath = ""; root.installedTheme = "" }
          if (event.cost) root.cost = event.cost
          if (event.state === "failed") { root.state = "error"; root.error = event.error || event.message }
          if (event.state === "done") {
            root.state = "done"
            if (event.warning) root.warningCount++
            root.installedPath = event.installedPath || ""
            root.installedTheme = root.installedPath ? event.theme || root.runTheme : ""
            root.status = event.warning || (root.installedTheme ? "Saved to " + root.installedTheme + "." : "Image generated. Choose a theme to save it.")
          }
        } catch (e) { root.error = "Invalid response from the wallpaper backend." }
      }
    }
    stderr: StdioCollector { id: runError; waitForEnd: true }
    onExited: {
      if (root.cancelled || root.timedOut) {
        root.queue = []; root.state = root.timedOut ? "error" : "cancelled"
        root.status = root.timedOut ? "Job timed out. Remaining sources were not submitted." : "Stopped locally. Remaining sources were not submitted."
        root.error = "Completed provider work may still be billed. Any saved preview remains available in History."
      } else if (exitCode !== 0 || root.state !== "done") {
        root.queue = []; root.state = "error"
        root.status = root.batchTotal > 1 ? "Batch stopped at output " + root.batchIndex + "/" + root.batchTotal + "." : "Job failed."
        if (!root.error) {
          try { root.error = JSON.parse(runError.text).message }
          catch (e) { root.error = "Backend failed. Check the selected model, API key and connection." }
        }
      } else if (root.queue.length) {
        root.finishOutput(); Qt.callLater(root.beginNext); return
      } else if (root.batchTotal > 1) {
        root.status = "Saved " + root.batchTotal + " wallpapers. Latest preview shown." + (root.warningCount ? " " + root.warningCount + " had upscale warnings; see History." : "")
      }
      root.finishOutput(); Qt.callLater(root.finished)
    }
  }
  Timer {
    interval: 920000; running: runProc.running
    onTriggered: { root.timedOut = true; root.queue = []; runProc.signal(15) }
  }
  Process {
    id: clearProc
    onExited: { if (exitCode !== 0) root.actionError = "Could not remember the cleared preview. Saved images remain in History." }
  }
  Process {
    id: folderProc
    onExited: { if (exitCode !== 0) root.actionError = "Could not open the saved folder." }
  }
  Process {
    id: setProc
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var saved = JSON.parse(text)
          root.installedPath = saved.installedPath; root.installedTheme = saved.installedTheme
          root.actionMessage = "Saved to " + saved.installedTheme + "."
        } catch (e) { root.actionError = "Could not read the theme save result." }
      }
    }
    stderr: StdioCollector {
      waitForEnd: true
      onStreamFinished: { if (text.trim()) { try { root.actionError = JSON.parse(text).message } catch (e) { root.actionError = "Could not save to the theme." } } }
    }
    onExited: { if (exitCode !== 0 && !root.actionError) root.actionError = "Could not save to the selected theme. The result remains available." }
  }
  Process {
    id: exportProc
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var result = JSON.parse(text)
          if (result.path) root.actionMessage = "Saved copy to " + result.path
        } catch (e) { if (text.trim()) root.actionError = "Could not read the saved image location." }
      }
    }
    stderr: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        if (!text.trim()) return
        try { root.actionError = JSON.parse(text).message }
        catch (e) { root.actionError = "Could not save the image. Try another destination." }
      }
    }
    onExited: { if (exitCode !== 0 && !root.actionError) root.actionError = "Could not save the image. Try another destination." }
  }
}
