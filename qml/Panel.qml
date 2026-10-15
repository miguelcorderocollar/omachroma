import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import "controllers"
import "views"
import "logic/BatchPlan.js" as Planning

Item {
  id: root
  property var shell: null
  property var manifest: null
  property bool opened: false
  property bool closingFromHost: false
  property string mode: "generate"
  property bool settingsOpen: false
  property bool historyOpen: false
  property var sourcePaths: []
  readonly property string sourcePath: sourcePaths.length ? sourcePaths[0] : ""
  property string theme: ""
  property var targetThemes: []
  readonly property var backgrounds: (references.data[theme] || {}).backgrounds || []
  readonly property var pickedRefs: (references.data[theme] || {}).refs || []
  readonly property var swatches: (references.data[theme] || {}).swatches || []
  property var externalOutput: null
  property alias plan: plan
  property alias references: references
  property alias saver: saver
  readonly property var preview: mode === "generate" ? externalOutput || (plan.outputs.length ? plan.selected : null) : null
  readonly property string previewPath: preview ? preview.resultPath || "" : job.resultPath
  readonly property string previewInstalledPath: preview ? preview.installedPath || "" : job.installedPath
  readonly property string previewTheme: preview ? preview.theme || "" : selectedTheme
  readonly property string previewInstalledTheme: preview ? preview.installedTheme || "" : job.installedTheme
  readonly property var previewCost: preview ? preview.cost || null : job.cost
  property int copiedSwatchIndex: -1
  property string upscalePath: ""
  property string upscaleTheme: ""
  readonly property int upscaleFactor: config.upscaleFactor || 2
  property int upscaleWidth: 0
  property int upscaleHeight: 0
  property string prompt: ""
  property string notice: ""
  property alias store: store
  property alias job: job
  property alias history: history
  readonly property string backend: decodeURIComponent(String(Qt.resolvedUrl("../generate-theme-wallpaper.py")).replace(/^file:\/\//, ""))
  readonly property var config: store.effectiveConfig
  readonly property int referenceLimit: Math.max(1, (store.modelSpec.maxImages || 5) - 1)
  readonly property bool busy: job.busy || job.actionBusy || picker.busy || saver.busy
  readonly property bool editingLocked: job.busy || job.actionBusy || saver.busy
  readonly property bool pickingImage: picker.busy
  readonly property bool keysReady: store.loaded && (mode === "upscale" ? !!store.keys.fal : !!store.keys[config.provider])
  readonly property string referenceReadiness: Planning.ready(targetThemes, references.data, referenceLimit)
  readonly property string readiness: !store.loaded ? "Loading Settings…" : mode === "generate" && store.modelSpec.available === false ? "The selected model is unavailable. Refresh prices or choose another model." : !keysReady ? "Add the " + (mode === "upscale" || config.provider === "fal" ? "fal.ai" : "OpenRouter") + " key in Settings." : mode === "upscale" ? (config.upscaler === "none" ? "Select an upscaler in Settings." : upscalePath ? "Ready to upscale." : "Choose an image to upscale.") : !sourcePath ? "Choose source images." : !targetThemes.length ? "Choose target themes." : referenceReadiness || (plan.totalCount > 200 ? "Choose at most 200 source/theme combinations." : !prompt.trim() ? "Enter a prompt." : !plan.pending.length ? "All requested outputs are generated." : "Ready to generate " + plan.pending.length + " remaining outputs.")
  readonly property string selectedTheme: mode === "upscale" ? upscaleTheme : theme
  readonly property bool canPrimary: !busy && !store.busy && keysReady && (mode !== "generate" || store.modelSpec.available !== false) && (mode === "upscale" ? upscalePath !== "" && config.upscaler !== "none" : sourcePaths.length > 0 && targetThemes.length > 0 && !referenceReadiness && plan.pending.length > 0 && plan.totalCount <= 200 && prompt.trim() !== "")

  function open(payloadJson) {
    opened = true; window.visible = true
    store.load()
    try {
      var payload = JSON.parse(payloadJson || "{}")
      if (payload.view === "history") { historyOpen = true; settingsOpen = false; history.load() }
      else if (payload.view === "settings") { settingsOpen = true; historyOpen = false }
    } catch (e) {}
  }
  function close() {
    closingFromHost = true; opened = false; window.visible = false; closingFromHost = false
  }
  function requestClose() {
    if (shell && typeof shell.hide === "function") shell.hide("mikelon797.omachroma")
    else close()
  }
  function localPath(path) {
    return path.startsWith("~/") ? Quickshell.env("HOME") + path.slice(1) : path
  }
  function setTargets(values) {
    if (editingLocked) return
    targetThemes = values.filter(function(value, index) { return store.themes.indexOf(value) >= 0 && values.indexOf(value) === index })
    if (targetThemes.indexOf(theme) < 0) theme = targetThemes[0] || ""
    copiedSwatchIndex = -1; references.load(targetThemes)
  }
  function selectTheme(value) {
    if (editingLocked) return
    if (targetThemes.indexOf(value) < 0) setTargets([value])
    theme = value; copiedSwatchIndex = -1
  }
  function toggleRef(path) { if (!editingLocked) references.toggle(theme, path) }
  function selectOutput(key) {
    if (key.startsWith("history:")) return
    selection.cancel()
    externalOutput = null; plan.selectedKey = key; saver.message = ""; saver.error = ""
    if (!busy && plan.selected && plan.selected.resultPath) { job.restore(plan.selected); selection.remember(plan.selected.id) }
  }
  function saveOutput() {
    if (busy || !previewPath) return
    job.actionMessage = ""; job.actionError = ""
    if (preview) saver.save([preview])
    else job.saveToTheme(selectedTheme)
  }
  function saveRemaining() { if (!busy) { job.actionMessage = ""; job.actionError = ""; saver.save(plan.unsaved) } }
  function clearPreview() {
    if (busy) return
    selection.cancel(); saver.error = ""; saver.message = ""; references.error = ""
    sourcePaths = []; upscalePath = ""; references.clearSelections(); copiedSwatchIndex = -1
    externalOutput = null; plan.selectedKey = ""; job.clear(); notice = ""
  }
  function openOutputFolder() {
    if (outputFolder.running || !previewPath) return
    var path = previewInstalledPath || previewPath
    outputFolder.command = ["xdg-open", path.slice(0, path.lastIndexOf("/"))]; outputFolder.running = true
  }
  Process { id: outputFolder }
  function exportOutput() {
    if (busy || !previewPath) return
    if (preview) job.restore(preview)
    job.saveAs()
  }
  function newVariation() {
    if (busy) return
    selection.cancel()
    var previous = plan.selected
    var command = plan.variation()
    if (command) { externalOutput = previous; job.startBatch([command]) }
  }
  function addSource(path) {
    if (editingLocked) return
    path = localPath(path.trim())
    if (!path || sourcePaths.indexOf(path) >= 0) return
    sourcePaths = sourcePaths.concat([path])
  }
  function removeSource(path) { if (!editingLocked) sourcePaths = sourcePaths.filter(function(p) { return p !== path }) }
  function toggleHistory() {
    historyOpen = !historyOpen; settingsOpen = false
    if (historyOpen) history.load()
  }
  function browse(target, title) {
    if (busy) return
    picker.open(target, title, target === "source")
  }
  function copyColor(value, index) { clipboard.copy(value, index, theme) }
  function primaryAction() {
    if (!canPrimary) return
    selection.cancel()
    notice = ""
    saver.message = ""; saver.error = ""
    var argv = ["--quality", config.quality || "high", "--upscaler", config.upscaler, "--upscale-factor", String(root.upscaleFactor), "--upscale-model", config.upscaleModel || "", "--creativity", String(config.creativity)]
    if (mode === "upscale") {
      argv.push("--upscale-only", localPath(upscalePath))
      if (upscaleTheme) argv.push("--theme", upscaleTheme, "--install")
      job.start(argv, upscaleTheme)
    } else {
      job.startBatch(plan.pending)
    }
  }

  Image {
    visible: false
    source: root.upscalePath ? "file://" + root.upscalePath : ""
    onStatusChanged: {
      root.upscaleWidth = status === Image.Ready ? sourceSize.width : 0
      root.upscaleHeight = status === Image.Ready ? sourceSize.height : 0
    }
  }
  BackendState {
    id: store
    backend: root.backend
    locked: root.editingLocked
    onLoadedChanged: {
      if (loaded && job.state === "idle" && store.lastJob) {
        job.restore(store.lastJob)
        root.externalOutput = store.lastJob.resultExists ? store.lastJob : store.lastJob.previousResult || null
      }
      if (loaded && !root.prompt) root.prompt = config.prompt
      if (loaded && !root.theme) {
        var restoredTheme = store.lastJob && (store.lastJob.installedTheme || store.lastJob.theme) || currentTheme
        if (themes.indexOf(restoredTheme) >= 0) root.selectTheme(restoredTheme)
      }
    }
  }
  JobController {
    id: job; backend: root.backend
    onOutputReceived: { plan.accept(record); if (root.externalOutput && record.status === "done") { root.externalOutput = null; plan.selectedKey = record.key } }
    onFinished: { if (root.historyOpen) history.load(); if (job.state === "done" && plan.selected && plan.selected.id) selection.remember(plan.selected.id) }
  }
  ThemeReferences { id: references; backend: root.backend; limit: root.referenceLimit }
  OutputPlan {
    id: plan; sources: root.sourcePaths; themes: root.targetThemes
    references: root.references.data; config: root.config; prompt: root.prompt
    onSelectionInvalidated: { root.externalOutput = record; saver.message = ""; job.actionMessage = "" }
  }
  ThemeSaver {
    id: saver; backend: root.backend
    onSaved: { plan.saved(record); if (root.externalOutput && root.externalOutput.id === record.id) root.externalOutput = record }
  }
  HistoryController {
    id: history; backend: root.backend
    onSelected: {
      if (root.busy) return
      job.restore(result); root.historyOpen = false
      root.externalOutput = Object.assign({}, result, {theme: result.installedTheme || result.theme})
      root.notice = "Showing history for " + (result.name || "wallpaper")
    }
  }
  ImagePicker {
    id: picker
    onSelected: {
      if (target === "upscale") root.upscalePath = paths[0]
      else if (target === "reference") {
        references.custom(root.theme, paths[0])
      } else paths.forEach(function(path) { root.addSource(path) })
    }
    onFailed: { root.notice = message }
  }
  SelectionStore { id: selection; backend: root.backend }
  ColorClipboard {
    id: clipboard
    onCopied: { if (theme === root.theme) { root.copiedSwatchIndex = index; copyFeedback.restart() }; if (root.notice === "Could not copy the color.") root.notice = "" }
    onFailed: root.notice = "Could not copy the color."
  }
  Timer {
    id: copyFeedback
    interval: 2000
    onTriggered: root.copiedSwatchIndex = -1
  }
  FloatingWindow {
    id: window
    visible: false
    title: "Omachroma"
    implicitWidth: 760
    implicitHeight: 850
    minimumSize: Qt.size(580, 520)
    // Clear the complete native buffer with the theme color on every frame.
    color: Qt.rgba(Color.menu.background.r, Color.menu.background.g, Color.menu.background.b, 1)
    surfaceFormat.opaque: true
    onVisibleChanged: {
      root.opened = visible
      if (!visible && !root.closingFromHost) root.requestClose()
    }
    AppContent {
      anchors.fill: parent
      app: root
    }
  }
}
