import QtQuick
import Quickshell.Io

// All persistence crosses stdin. API keys never appear in argv or shell settings.
Item {
  id: root
  property string backend: ""
  property var config: ({})
  property var themes: []
  property string currentTheme: ""
  property var editModels: ({fal: [], openrouter: []})
  property var upscaleOptions: []
  property var upscaleSpecs: ({})
  readonly property var upscaleSpec: upscaleSpecs[config.upscaler || "seedvr"] || ({factors: [2, 4], models: [], description: ""})
  property var upscaleModels: ({none: [], precision: [], creative: []})
  property var prices: ({})
  property var modelConfig: ({})
  property var providerDefaults: ({})
  property var environmentKeys: ({})
  property string catalogWarning: ""
  property string dataPath: ""
  property var storageInfo: null
  readonly property bool dataBusy: dataProc.running
  property var keys: ({fal: false, openrouter: false})
  readonly property var effectiveConfig: Object.assign({}, config, {upscaler: keys.fal ? config.upscaler : "none"})
  property var lastJob: null
  property string error: ""
  property string message: ""
  property bool loaded: false
  property bool locked: false
  readonly property var modelSpec: {
    var models = editModels[config.provider || "fal"] || []
    for (var i = 0; i < models.length; i++)
      if (models[i].value === config.model) return models[i]
    return models.length ? models[0] : ({resolutions: [], qualityOptions: [], maxImages: 5})
  }
  readonly property bool busy: locked || loadProc.running || saveProc.running
  function accept(text) {
    try {
      var data = JSON.parse(text)
      config = data.config; themes = data.themes; currentTheme = data.currentTheme || ""
      editModels = data.editModels; upscaleModels = data.upscaleModels
      upscaleOptions = data.upscaleOptions; upscaleSpecs = data.upscaleSpecs; keys = data.keys
      prices = data.prices; lastJob = data.lastJob || null; loaded = true; error = ""
      modelConfig = data.modelConfig; providerDefaults = data.providerDefaults
      environmentKeys = data.environmentKeys; catalogWarning = data.catalogWarning || ""
      dataPath = data.dataPath || ""
      if (data.refresh) message = data.refresh.updated + " rates refreshed; " + (data.refresh.availabilityUpdated || 0) + " availability entries checked." + (data.refresh.warnings.length ? " " + data.refresh.warnings.join(" ") : "")
    } catch (e) { error = "Could not read Settings. Check the local config file." }
  }
  function load() {
    if (busy) return
    loadProc.command = ["python3", backend, "--snapshot"]
    loadProc.running = true
  }
  function update(key, value) {
    if (!loaded || busy) return
    var next = Object.assign({}, config)
    next[key] = value
    if (key === "provider") next.model = providerDefaults[value]
    if (key === "upscaler") next.upscaleModel = (upscaleModels[value] || [""])[0] || ""
    saveProc.successMessage = "Settings saved."
    saveProc.payload = JSON.stringify(next) + "\n"
    saveProc.command = ["python3", backend, "--save-config"]
    saveProc.running = true
  }
  function restoreModelDefaults() {
    if (!loaded || busy) return
    saveProc.successMessage = "Recommended model defaults restored."
    saveProc.payload = ""
    saveProc.command = ["python3", backend, "--restore-model-defaults"]
    saveProc.running = true
  }
  function saveKey(provider, key) {
    if (busy || !key.trim()) return
    saveProc.successMessage = "API key saved."
    saveProc.payload = key.trim() + "\n"
    saveProc.command = ["python3", backend, "--save-key", provider]
    saveProc.running = true
  }
  function saveModels(value) {
    if (!loaded || busy) return
    saveProc.successMessage = "Model choices saved. Restore model defaults to apply your preferred generation defaults."
    saveProc.payload = value + "\n"
    saveProc.command = ["python3", backend, "--save-models"]
    saveProc.running = true
  }
  function removeKey(provider) {
    if (!loaded || busy) return
    saveProc.successMessage = environmentKeys[provider] ? "Saved key removed. An environment key is still active." : "Saved key removed."
    saveProc.payload = ""
    saveProc.command = ["python3", backend, "--remove-key", provider]
    saveProc.running = true
  }
  function refreshPrices() {
    if (!loaded || busy) return
    saveProc.successMessage = ""
    saveProc.payload = ""
    saveProc.command = ["python3", backend, "--refresh-prices"]
    message = "Refreshing provider metadata. Images and prompts are not sent."
    saveProc.running = true
  }
  function dataAction(open) {
    if (dataProc.running || busy) return
    dataProc.opening = open
    dataProc.command = ["python3", backend, open ? "--open-data-folder" : "--storage-info"]
    dataProc.running = true
  }
  Process {
    id: dataProc
    property bool opening: false
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        if (!dataProc.opening && text.trim()) {
          try { root.storageInfo = JSON.parse(text) }
          catch (e) { root.error = "Could not read storage usage." }
        }
      }
    }
    onExited: { if (exitCode !== 0) root.error = "Could not inspect or open the app data folder." }
  }
  Process {
    id: loadProc
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: root.accept(text) }
    onExited: { if (exitCode !== 0) root.error = "Settings could not load. Check config.json in the Omachroma data folder." }
  }
  Process {
    id: saveProc
    property string payload: ""
    property string successMessage: "Settings saved."
    stdinEnabled: true
    onStarted: { write(payload); payload = ""; stdinEnabled = false }
    onRunningChanged: { if (running) stdinEnabled = true }
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: root.accept(text) }
    stderr: StdioCollector { id: saveError; waitForEnd: true }
    onExited: {
      payload = ""
      if (successMessage || exitCode !== 0) root.message = exitCode === 0 ? successMessage : ""
      if (exitCode !== 0) {
        try { root.error = JSON.parse(saveError.text).message }
        catch (e) { root.error = "Could not save. Check the key or settings and try again." }
      }
    }
  }
}
