import QtQuick
import Quickshell
import Quickshell.Io
import "app/qml" as App

Scope {
  id: demo
  property bool prepared: false
  property bool ready: false
  property bool startupCaptureDone: false
  App.Panel { id: app }

  function windowForApp() {
    for (var i = 0; i < app.data.length; i++) {
      var child = app.data[i]
      if (child.title === "Omatinta") return child
    }
    return null
  }

  function contentForApp() {
    var window = windowForApp()
    return window && window.contentItem && window.contentItem.children.length
      ? window.contentItem.children[0] : null
  }

  function findSettings(node) {
    if (!node) return null
    if (node.tabIndex !== undefined && node.tabs !== undefined) return node
    var children = node.children || []
    for (var i = 0; i < children.length; i++) {
      var found = findSettings(children[i])
      if (found) return found
    }
    return null
  }

  function findPreview(node) {
    if (!node) return null
    if (node.imagePath !== undefined && typeof node.showImage === "function" &&
        typeof node.close === "function") return node
    var children = node.children || []
    for (var i = 0; i < children.length; i++) {
      var found = findPreview(children[i])
      if (found) return found
    }
    return null
  }

  function capture(path) {
    var content = contentForApp()
    if (!content) { console.error("DEMO_CAPTURE_FAILED: AppContent is unavailable"); return }
    content.grabToImage(function(result) {
      if (!result.saveToFile(path)) console.error("DEMO_CAPTURE_FAILED", path)
      else {
        console.log("DEMO_CAPTURED", path)
        if (Quickshell.env("DEMO_EXIT_AFTER_CAPTURE") === "1") Qt.quit()
      }
    })
  }

  function showSettings(tab) {
    app.settingsOpen = true
    app.historyOpen = false
    Qt.callLater(function() {
      var page = demo.findSettings(demo.contentForApp())
      if (!page) { console.error("DEMO_SETTINGS_UNAVAILABLE"); return }
      var index = page.tabs.indexOf(tab)
      if (index < 0) { console.error("DEMO_UNKNOWN_SETTINGS_TAB", tab); return }
      page.tabIndex = index
    })
  }

  Component.onCompleted: {
    var window = windowForApp()
    if (window) {
      window.implicitWidth = Number(Quickshell.env("DEMO_WIDTH")) || 940
      window.implicitHeight = Number(Quickshell.env("DEMO_HEIGHT")) || 900
    }
    app.open("{}")
  }

  IpcHandler {
    target: "omatinta-demo"
    function workspace(): void {
      app.settingsOpen = false
      app.historyOpen = false
      app.mode = "generate"
    }
    function upscale(): void {
      app.settingsOpen = false
      app.historyOpen = false
      app.mode = "upscale"
    }
    function settings(tab: string): void {
      demo.showSettings(tab)
    }
    function history(): void {
      app.settingsOpen = false
      app.historyOpen = true
      app.history.load()
    }
    function selectHistory(id: string): void { app.history.select(id) }
    function preview(): void {
      var lightbox = demo.findPreview(demo.contentForApp())
      if (!lightbox) { console.error("DEMO_PREVIEW_UNAVAILABLE"); return }
      lightbox.showImage(app.previewPath)
    }
    function dismissPreview(): void {
      var lightbox = demo.findPreview(demo.contentForApp())
      if (lightbox) lightbox.close()
    }
    function captureTo(path: string): void { demo.capture(path) }
    function close(): void { app.close() }
  }

  Timer {
    interval: 200
    repeat: true
    running: true
    onTriggered: {
      if (!demo.prepared && app.store.loaded && !app.store.busy) {
        demo.prepared = true
        app.sourcePaths = [Quickshell.env("DEMO_SOURCE")]
        app.setTargets([Quickshell.env("DEMO_THEME")])
        app.prompt = Quickshell.env("DEMO_PROMPT")
        app.settingsOpen = false
        app.historyOpen = false
        app.mode = "generate"
        console.log("DEMO_READY", JSON.stringify({
          theme: app.theme,
          keyReady: app.keysReady,
          source: app.sourcePath,
          result: app.externalOutput ? app.externalOutput.resultPath : ""
        }))
      }
      if (demo.prepared && !demo.ready && !app.references.busy &&
          app.references.data[Quickshell.env("DEMO_THEME")] &&
          app.references.data[Quickshell.env("DEMO_THEME")].loaded) {
        demo.ready = true
        console.log("DEMO_INTERACTIVE")
        var startView = Quickshell.env("DEMO_START_VIEW")
        if (startView === "settings") demo.showSettings(Quickshell.env("DEMO_SETTINGS_TAB") || "Generation")
        else if (startView === "history") app.toggleHistory()
      }
      if (demo.ready && !demo.startupCaptureDone && Quickshell.env("DEMO_CAPTURE_PATH")) {
        demo.startupCaptureDone = true
        var path = Quickshell.env("DEMO_CAPTURE_PATH")
        Qt.callLater(function() { Qt.callLater(function() { demo.capture(path) }) })
      }
    }
  }
}
