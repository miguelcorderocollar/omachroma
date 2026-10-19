import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Commons as Commons
import qs.Ui

RowLayout {
  id: root
  property bool settingsOpen: false
  property bool historyOpen: false
  signal settingsRequested()
  signal historyRequested()
  signal backRequested()
  function focusBack() { back.forceActiveFocus() }
  spacing: Commons.Style.spacing.sm
  IconAction {
    id: back
    visible: root.settingsOpen || root.historyOpen
    iconText: "󰁍"; tooltipText: "Back · Alt+Left"
    onClicked: root.backRequested()
  }
  Text {
    Layout.fillWidth: true; textFormat: Text.PlainText
    text: root.settingsOpen ? "Omatinta / Settings" : root.historyOpen ? "Omatinta / History" : "Omatinta"
    color: Commons.Color.menu.text; font.family: Commons.Style.font.family
    font.pixelSize: Commons.Style.font.title; font.bold: true
  }
  IconAction {
    visible: !root.settingsOpen && !root.historyOpen
    iconText: "󰋚"; tooltipText: "History · Ctrl+H"
    onClicked: root.historyRequested()
  }
  IconAction {
    visible: !root.settingsOpen && !root.historyOpen
    iconText: "󰒓"; tooltipText: "Settings · Ctrl+,"
    onClicked: root.settingsRequested()
  }
}
