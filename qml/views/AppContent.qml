import QtQuick
import QtQuick.Window
import QtQuick.Controls as QQC
import QtQuick.Layouts
import qs.Commons
import qs.Ui
import "../logic/Omachroma.js" as Omachroma
import "../logic/Focus.js" as Focus

FocusScope {
  id: root
  required property var app
  focus: true
  readonly property bool modalOpen: lightbox.opened || modelEditor.opened || costDetails.opened
  function goBack() { app.settingsOpen = false; app.historyOpen = false; Qt.callLater(workspaceGenerate.forceActiveFocus) }
  function focusNavigation() { if (app.settingsOpen || app.historyOpen) header.focusBack(); else workspaceGenerate.forceActiveFocus() }
  function revealFocus() {
    var item = Window.window ? Window.window.activeFocusItem : null
    var parent = item
    while (parent && parent !== contentColumn) parent = parent.parent
    if (!parent || !scroll.contentItem || scroll.contentItem.contentY === undefined) return
    var position = item.mapToItem(contentColumn, 0, 0), viewport = scroll.contentItem
    if (position.y < viewport.contentY) viewport.contentY = position.y
    else if (position.y + item.height > viewport.contentY + scroll.height) viewport.contentY = position.y + item.height - scroll.height
  }
  Connections { target: root.Window.window; function onActiveFocusItemChanged() { Qt.callLater(root.revealFocus) } }
  Keys.onEscapePressed: {
    if (root.modalOpen || app.pickingImage) return
    if (app.settingsOpen || app.historyOpen) root.goBack()
    else app.requestClose()
    event.accepted = true
  }
  Connections {
    target: root.app
    function onSettingsOpenChanged() { Focus.closePopups(root) }
    function onHistoryOpenChanged() { Focus.closePopups(root) }
    function onModeChanged() { Focus.closePopups(root) }
  }
  Connections { target: root.app.store; function onIoBusyChanged() { if (root.app.store.ioBusy) Focus.closePopups(root) } }
  WorkspaceShortcuts { app: root.app; settings: settings; modalOpen: root.modalOpen; onBackRequested: root.goBack() }
  Rectangle { anchors.fill: parent; color: Qt.rgba(Color.menu.background.r, Color.menu.background.g, Color.menu.background.b, 1) }
  ColumnLayout {
    id: mainColumn
    enabled: !root.modalOpen
    anchors.fill: parent
    anchors.margins: Style.spacing.panelPadding
    spacing: Style.spacing.md
    AppHeader {
      id: header
      Layout.fillWidth: true
      settingsOpen: app.settingsOpen
      historyOpen: app.historyOpen
      onSettingsRequested: { app.settingsOpen = !app.settingsOpen; app.historyOpen = false }
      onHistoryRequested: app.toggleHistory()
      onBackRequested: root.goBack()
    }
    RowLayout {
      visible: !app.settingsOpen && !app.historyOpen
      Layout.fillWidth: true
      ActionButton {
        id: workspaceGenerate
        enabled: !app.editingLocked
        text: "Generate"; focusable: true; bordered: true; selected: app.mode === "generate"
        onClicked: { app.mode = "generate"; app.settingsOpen = false; app.historyOpen = false }
      }
      ActionButton {
        text: "Upscale"; focusable: true; bordered: true; selected: app.mode === "upscale"
        enabled: app.store.loaded && app.store.upscalingEnabled && !app.editingLocked
        opacity: enabled ? 1 : 0.45
        tooltipText: enabled ? "Upscale · Ctrl+2" : "Enable upscaling in Settings"
        onClicked: { app.mode = "upscale"; app.settingsOpen = false; app.historyOpen = false }
      }
      Item { Layout.fillWidth: true }
    }
    PanelSeparator { Layout.fillWidth: true; foreground: Color.menu.text }
    QQC.ScrollView {
      id: scroll
      Layout.fillWidth: true
      Layout.fillHeight: true
      contentWidth: availableWidth
      clip: true
      Column {
        id: contentColumn
        width: scroll.availableWidth
        spacing: Style.spacing.lg
        GenerateForm {
          visible: app.mode === "generate" && !app.settingsOpen && !app.historyOpen
          width: parent.width
          enabled: !app.busy
          sourcePaths: app.sourcePaths
          theme: app.theme
          themes: app.store.themes
          targetThemes: app.targetThemes
          outputCount: app.plan.totalCount
          referenceData: app.references.data
          backgrounds: app.backgrounds
          pickedRefs: app.pickedRefs
          referenceLimit: app.referenceLimit
          swatches: app.swatches
          copiedSwatchIndex: app.copiedSwatchIndex
          promptText: app.prompt
          onSourceAdded: { app.addSource(path) }
          onSourceRemoved: { app.removeSource(path) }
          onPromptEdited: { app.prompt = value }
          onBrowseRequested: app.browse("source", "Choose source images")
          onCustomRefRequested: app.browse("reference", "Add style reference")
          onThemeSelected: { app.selectTheme(theme) }
          onTargetsChanged: { app.setTargets(themes) }
          onRefToggled: { app.toggleRef(path) }
          onColorCopied: { app.copyColor(value, index) }
        }
        UpscaleForm {
          visible: app.mode === "upscale" && !app.settingsOpen && !app.historyOpen
          width: parent.width; enabled: !app.busy
          upscalePath: app.upscalePath; upscaleTheme: app.upscaleTheme
          themes: app.store.themes; upscaleFactor: app.upscaleFactor
          factorOptions: app.store.upscaleSpec.factors || [2, 4]
          onPathEdited: { app.upscalePath = app.localPath(path) }
          onBrowseRequested: app.browse("upscale", "Choose image to upscale")
          onThemeSelected: { app.upscaleTheme = theme }
          onFactorSelected: { app.store.update("upscaleFactor", factor) }
        }
        SettingsView {
          id: settings
          visible: app.settingsOpen
          width: parent.width
          store: app.store
          onUsePromptRequested: { app.prompt = app.config.prompt; root.goBack() }
          onConfigureRequested: modelEditor.edit()
        }
        HistoryView {
          visible: app.historyOpen
          width: parent.width; history: app.history; jobBusy: app.busy
        }
        OutputSelector {
          visible: app.mode === "generate" && !app.settingsOpen && !app.historyOpen && app.plan.outputs.length > 0
          width: parent.width; plan: app.plan; busy: app.busy; external: app.externalOutput
          onSelected: { app.selectOutput(key) }
          onSaveRemaining: app.saveRemaining()
          onRegenerate: app.newVariation()
        }
        ResultView {
          visible: !app.settingsOpen && !app.historyOpen && app.previewPath !== ""
          width: parent.width
          resultPath: app.previewPath; busy: app.busy
          installedPath: app.previewInstalledPath
          onFolderRequested: app.openOutputFolder()
          onPreviewRequested: { lightbox.showImage(path) }
        }
        ResultActions {
          visible: !app.settingsOpen && !app.historyOpen && app.previewPath !== ""
          width: parent.width; canSet: !app.busy
          theme: app.previewTheme; installedTheme: app.previewInstalledTheme
          costText: Omachroma.reportedCost(app.previewCost)
          onSaveRequested: app.exportOutput()
          onThemeRequested: app.saveOutput()
          onCostRequested: { costDetails.details = Omachroma.reportedCost(app.previewCost); costDetails.open() }
        }
      }
    }
    PanelSeparator { Layout.fillWidth: true; foreground: Color.menu.text }
    FooterBar {
      visible: !app.settingsOpen && !app.historyOpen
      Layout.fillWidth: true
      primaryLabel: app.mode === "upscale" ? "Upscale" : app.plan.totalCount > 200 ? "Reduce selection" : !app.plan.totalCount ? "Generate" : !app.plan.pending.length ? "All generated" : "Generate " + app.plan.pending.length + (app.plan.pending.length === 1 ? " output" : " outputs")
      footText: app.saver.busy ? "Saving…" : app.pickingImage ? "Choosing images…" : app.job.busy || app.job.actionBusy ? app.job.displayStatus : ""
      lastError: app.saver.error || app.references.error || app.job.actionError || app.job.error || app.notice
      costText: app.preview && app.preview.resultPath && !app.job.busy ? "Selected output · " + Omachroma.reportedCost(app.previewCost) : app.job.state !== "idle" && !app.job.busy && !app.preview ? Omachroma.reportedCost(app.job.cost) : (app.mode === "upscale" ? "Estimate\n" : (app.job.busy ? app.job.batchTotal + " queued outputs" : app.plan.pending.length + " remaining outputs") + " · estimate per output\n") + Omachroma.priceText(app.config, app.mode, app.store.prices, app.upscaleWidth, app.upscaleHeight, app.upscaleFactor, app.store.modelSpec, app.plan.pending.length)
      canPrimary: app.canPrimary
      busy: app.job.busy
      actionBusy: app.job.actionBusy || app.pickingImage || app.saver.busy || app.references.busy || app.store.ioBusy
      onPrimaryClicked: app.primaryAction()
      onClearClicked: app.clearPreview()
      onCancelClicked: app.job.cancel()
    }

  }
  ModelEditor { id: modelEditor; store: app.store; anchors.fill: parent; z: 11; onClosed: { if (!restoredFocus) Qt.callLater(root.focusNavigation) } }
  ModalFrame {
    id: costDetails; title: "Reported cost"; anchors.fill: parent; z: 11
    onClosed: { if (!restoredFocus) Qt.callLater(root.focusNavigation) }
    property string details: ""
    Text { anchors.fill: parent; textFormat: Text.PlainText; text: costDetails.details; wrapMode: Text.WordWrap; color: Color.menu.text; font.family: Style.font.family; font.pixelSize: Style.font.body }
  }
  ImageLightbox {
    id: lightbox
    anchors.fill: parent; z: 10
    onClosed: { if (!restoredFocus) Qt.callLater(root.focusNavigation) }
  }
}
