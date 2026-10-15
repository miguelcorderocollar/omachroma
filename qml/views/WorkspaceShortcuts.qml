import QtQuick

Item {
  id: root
  required property var app
  required property var settings
  property bool modalOpen: false
  readonly property bool active: app.opened && !modalOpen && !app.pickingImage && !app.job.actionBusy
  readonly property bool workspace: active && !app.settingsOpen && !app.historyOpen
  signal backRequested()
  Shortcut { sequence: "Ctrl+,"; enabled: root.active; onActivated: { root.app.settingsOpen = !root.app.settingsOpen; root.app.historyOpen = false } }
  Shortcut { sequence: "Ctrl+H"; enabled: root.active; onActivated: root.app.toggleHistory() }
  Shortcut { sequence: "Alt+Left"; enabled: root.active && (root.app.settingsOpen || root.app.historyOpen); onActivated: root.backRequested() }
  Shortcut { sequence: "Ctrl+Tab"; enabled: root.active && root.app.settingsOpen; onActivated: root.settings.nextTab(1) }
  Shortcut { sequence: "Ctrl+Shift+Tab"; enabled: root.active && root.app.settingsOpen; onActivated: root.settings.nextTab(-1) }
  Shortcut { sequence: "Ctrl+1"; enabled: root.workspace && !root.app.editingLocked; onActivated: root.app.mode = "generate" }
  Shortcut { sequence: "Ctrl+2"; enabled: root.workspace && !root.app.editingLocked && root.app.store.upscalingEnabled; onActivated: root.app.mode = "upscale" }
  Shortcut { sequence: "Alt+G"; enabled: root.workspace; onActivated: root.app.primaryAction() }
  Shortcut { sequence: "Ctrl+O"; enabled: root.workspace && !root.app.busy; onActivated: root.app.browse(root.app.mode === "upscale" ? "upscale" : "source", "Choose images") }
  Shortcut { sequence: "Ctrl+Shift+O"; enabled: root.workspace && !root.app.busy && root.app.theme !== "" && root.app.mode === "generate"; onActivated: root.app.browse("reference", "Add style reference") }
  Shortcut { sequence: "Ctrl+S"; enabled: root.workspace && !root.app.busy && root.app.previewPath !== ""; onActivated: root.app.exportOutput() }
  Shortcut { sequence: "Ctrl+Delete"; enabled: root.workspace && !root.app.busy; onActivated: root.app.clearPreview() }
  Shortcut { sequence: "Ctrl+."; enabled: root.active && root.app.job.busy; onActivated: root.app.job.cancel() }
}
