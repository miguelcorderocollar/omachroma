import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Ui
import "../logic/Omachroma.js" as Omachroma

Column {
  id: root
  required property var history
  property bool jobBusy: false
  property int cursorIndex: -1
  spacing: Style.spacing.sm
  function focusRow(index) {
    var row = rows.itemAt(Math.max(0, Math.min(index, rows.count - 1)))
    if (row) row.forceActiveFocus()
  }
  RowLayout {
    width: parent.width
    PanelSectionHeader { Layout.fillWidth: true; text: "WALLPAPER HISTORY" }
    PanelActionButton {
      focusable: true; iconText: "󰑐"; tooltipText: "Refresh history"; Accessible.name: tooltipText
      enabled: !root.history.busy; onClicked: root.history.load()
    }
  }
  RowLayout {
    width: parent.width
    visible: root.history.busy || root.history.error !== "" || !root.history.records.length
    LoadingPixels { visible: root.history.busy; running: visible }
    Text {
      Layout.fillWidth: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText
      text: root.history.error || (root.history.busy ? "Loading history…" : "No saved jobs yet.")
      color: root.history.error ? Color.urgent : Color.muted
      font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
    }
  }
  Repeater {
    id: rows
    model: root.history.records
    delegate: CursorSurface {
      id: entry
      required property var modelData
      required property int index
      width: root.width
      height: Math.max(Style.space(56), details.implicitHeight) + Style.spacing.sm * 2
      foreground: Color.menu.text; hasCursor: root.cursorIndex === index
      activeFocusOnTab: true; enabled: !root.history.busy && !root.jobBusy
      Accessible.role: Accessible.ListItem
      Accessible.name: modelData.name || "Wallpaper"
      Accessible.description: (modelData.theme || "") + ", " + modelData.status
      Accessible.onPressAction: entry.activate()
      function activate() { forceActiveFocus(); root.history.select(modelData.id) }
      onActiveFocusChanged: { if (activeFocus) root.cursorIndex = index }
      Keys.onReturnPressed: activate()
      Keys.onEnterPressed: activate()
      Keys.onSpacePressed: activate()
      Keys.onDownPressed: root.focusRow(index + 1)
      Keys.onUpPressed: root.focusRow(index - 1)
      HoverHandler { onHoveredChanged: { if (hovered) root.cursorIndex = entry.index } }
      TapHandler { onTapped: entry.activate() }
      RowLayout {
        anchors.fill: parent
        anchors.margins: Style.spacing.sm; spacing: Style.spacing.md
        Image {
          Layout.preferredWidth: Style.space(88); Layout.preferredHeight: Style.space(56)
          source: entry.modelData.resultExists ? "file://" + entry.modelData.resultPath : ""
          asynchronous: true; sourceSize.width: 176; fillMode: Image.PreserveAspectCrop
          Accessible.name: "Saved wallpaper preview"
        }
        Column {
          id: details
          Layout.fillWidth: true; spacing: Style.spacing.labelGap
          Text {
            width: parent.width; textFormat: Text.PlainText; elide: Text.ElideRight
            text: entry.modelData.name || "Wallpaper"
            color: Color.menu.text; font.family: Style.font.family; font.pixelSize: Style.font.body; font.bold: true
          }
          Text {
            width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
            text: (entry.modelData.date || "").slice(0,16).replace("T", " ") + " UTC · " + entry.modelData.status + (entry.modelData.theme ? " · " + entry.modelData.theme : "")
            color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.caption
          }
          Text {
            width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
            text: entry.modelData.error || entry.modelData.message || (entry.modelData.resultExists ? "Saved wallpaper" : "No saved image")
            color: entry.modelData.error ? Color.urgent : Color.muted
            font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
          }
          Text {
            visible: !!entry.modelData.cost
            width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
            text: Omachroma.reportedCost(entry.modelData.cost)
            color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.caption
          }
        }
      }
    }
  }
}
