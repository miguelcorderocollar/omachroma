import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import qs.Commons
import qs.Ui
import "../logic/Omachroma.js" as Omachroma

FocusScope {
  id: root
  required property var app
  focus: true
  Keys.onEscapePressed: { if (lightbox.opened) lightbox.close(); else if (app.settingsOpen) app.settingsOpen = false; else if (app.historyOpen) app.historyOpen = false; else app.requestClose() }
  Shortcut { sequence: "Alt+G"; enabled: app.opened && !lightbox.opened; onActivated: app.primaryAction() }
  Shortcut { sequence: "Ctrl+,"; enabled: app.opened && !lightbox.opened; onActivated: { app.settingsOpen = !app.settingsOpen; app.historyOpen = false } }
  Shortcut { sequence: "Ctrl+H"; enabled: app.opened && !lightbox.opened; onActivated: app.toggleHistory() }
  Rectangle { anchors.fill: parent; color: Qt.rgba(Color.menu.background.r, Color.menu.background.g, Color.menu.background.b, 1) }
  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Style.spacing.panelPadding
    spacing: Style.spacing.md
    AppHeader {
      Layout.fillWidth: true
      settingsOpen: app.settingsOpen
      historyOpen: app.historyOpen
      onSettingsRequested: { app.settingsOpen = !app.settingsOpen; app.historyOpen = false }
      onHistoryRequested: app.toggleHistory()
    }
    RowLayout {
      Layout.fillWidth: true
      Button {
        text: "Generate"; focusable: true; bordered: true; selected: app.mode === "generate"
        onClicked: { app.mode = "generate"; app.settingsOpen = false; app.historyOpen = false }
      }
      Button {
        text: "Upscale"; focusable: true; bordered: true; selected: app.mode === "upscale"
        enabled: app.store.loaded && !!app.store.keys.fal
        opacity: enabled ? 1 : 0.45
        tooltipText: enabled ? "Upscale using fal.ai" : "Requires a fal.ai API key"
        onClicked: { app.mode = "upscale"; app.settingsOpen = false; app.historyOpen = false }
      }
      Text {
        visible: app.store.loaded && !app.store.keys.fal
        text: "fal.ai key required"; color: Color.muted
        font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
      }
      Item { Layout.fillWidth: true }
    }
    RowLayout {
      visible: !app.settingsOpen && !app.historyOpen && !app.keysReady && app.store.loaded
      Layout.fillWidth: true
      Text {
        Layout.fillWidth: true; text: app.readiness; wrapMode: Text.WordWrap
        color: Color.urgent; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
      }
      Button { text: "Add API key"; focusable: true; bordered: true; onClicked: app.settingsOpen = true }
    }
    PanelSeparator { Layout.fillWidth: true; foreground: Color.menu.text }
    QQC.ScrollView {
      id: scroll
      Layout.fillWidth: true
      Layout.fillHeight: true
      contentWidth: availableWidth
      clip: true
      Column {
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
          visible: app.settingsOpen
          width: parent.width
          store: app.store
          enabled: !app.busy && !app.store.busy
          onUsePromptRequested: { app.prompt = app.config.prompt; app.notice = "Default prompt loaded into Generate." }
          onFalKeyRequested: scroll.contentItem.contentY = 0
        }
        HistoryView {
          visible: app.historyOpen
          width: parent.width; history: app.history; jobBusy: app.busy
        }
        Text {
          visible: app.notice !== ""
          width: parent.width; text: app.notice; textFormat: Text.PlainText; wrapMode: Text.WordWrap
          color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
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
          onPreviewRequested: { lightbox.open(path) }
        }
      }
    }
    PanelSeparator { Layout.fillWidth: true; foreground: Color.menu.text }
    FooterBar {
      visible: !app.settingsOpen && !app.historyOpen
      Layout.fillWidth: true
      primaryLabel: app.mode === "upscale" ? "Upscale" : app.plan.totalCount > 200 ? "Reduce selection" : !app.plan.totalCount ? "Generate" : !app.plan.pending.length ? "All generated" : app.plan.pending.length === app.plan.jobs.length ? (app.plan.pending.length === 1 ? "Generate" : "Generate " + app.plan.pending.length + " outputs") : "Generate remaining (" + app.plan.pending.length + ")"
      footText: app.saver.busy ? "Saving remaining outputs…" : app.references.busy ? "Loading theme references…" : app.pickingImage ? "Choosing images…" : app.busy || !app.preview ? app.job.state !== "idle" ? app.job.displayStatus : app.readiness : app.saver.message || app.job.actionMessage || (app.preview.status === "done" ? (app.preview.installedPath ? "Saved to " + app.preview.theme + "." : "Ready to save " + app.preview.theme + ".") : app.readiness)
      lastError: app.saver.error || app.references.error || app.job.actionError || app.job.error
      costText: app.preview && app.preview.resultPath && !app.job.busy ? "Selected output · " + Omachroma.reportedCost(app.previewCost) : app.job.state !== "idle" && !app.job.busy && !app.preview ? Omachroma.reportedCost(app.job.cost) : (app.mode === "upscale" ? "Estimate\n" : (app.job.busy ? app.job.batchTotal + " queued outputs" : app.plan.pending.length + " remaining outputs") + " · estimate per output\n") + Omachroma.priceText(app.config, app.mode, app.store.prices, app.upscaleWidth, app.upscaleHeight, app.upscaleFactor, app.store.modelSpec, app.plan.pending.length)
      canPrimary: app.canPrimary
      canSet: !app.busy && app.previewPath !== ""
      resultAvailable: app.previewPath !== ""
      themeName: app.previewTheme
      installedTheme: app.previewInstalledTheme
      busy: app.job.busy
      actionBusy: app.job.actionBusy || app.pickingImage || app.saver.busy || app.references.busy
      onPrimaryClicked: app.primaryAction()
      onSetClicked: app.saveOutput()
      onSaveClicked: app.exportOutput()
      onClearClicked: app.clearPreview()
      onCancelClicked: app.job.cancel()
    }
    Text {
      visible: app.settingsOpen
      Layout.fillWidth: true; wrapMode: Text.WordWrap
      text: app.busy ? "A job is running. Settings unlock when it finishes." : app.store.error || app.store.message || "Changes save on this machine. Keys are never displayed again."
      textFormat: Text.PlainText
      color: app.store.error ? Color.urgent : Color.muted
      font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
    }
  }
  ImageLightbox {
    id: lightbox
    anchors.fill: parent; z: 10
    onClosed: root.forceActiveFocus()
  }
}
