import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Ui

RowLayout {
  id: root
  property bool settingsOpen: false
  property bool historyOpen: false
  signal settingsRequested()
  signal historyRequested()
  spacing: Style.spacing.md
  Column {
    Layout.fillWidth: true
    spacing: Style.space(2)
    Text {
      text: "Omachroma"
      color: Color.menu.text
      font.family: Style.font.family; font.pixelSize: Style.font.title; font.bold: true
    }

  }
  Button {
    text: root.historyOpen ? "Back" : "History"
    selected: root.historyOpen; focusable: true; bordered: true
    tooltipText: "Saved wallpapers and job status · Ctrl+H"
    onClicked: root.historyRequested()
  }
  Button {
    iconText: "󰒓"
    selected: root.settingsOpen; focusable: true; bordered: true
    foreground: Color.menu.text
    tooltipText: "Settings · Ctrl+,"
    Accessible.name: "Settings"
    onClicked: root.settingsRequested()
  }
}
