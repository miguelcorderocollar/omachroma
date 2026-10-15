import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Ui

RowLayout {
  id: root
  property bool canSet: false
  property string theme: ""
  property string installedTheme: ""
  property string costText: ""
  signal saveRequested()
  signal themeRequested()
  signal costRequested()
  spacing: Style.spacing.controlGap
  ActionButton {
    text: "Save as…"; enabled: root.canSet
    tooltipText: "Export a copy · Ctrl+S"
    onClicked: root.saveRequested()
  }
  ActionButton {
    text: root.installedTheme && root.installedTheme === root.theme ? "Saved to " + root.theme : "Save to " + root.theme
    iconText: root.installedTheme && root.installedTheme === root.theme ? "✓" : ""
    visible: root.theme !== ""
    enabled: root.canSet && root.installedTheme !== root.theme
    onClicked: root.themeRequested()
  }
  Item { Layout.fillWidth: true }
  IconAction {
    iconText: "󰋽"; tooltipText: root.costText
    Accessible.name: "Reported cost"; Accessible.description: root.costText
    onClicked: root.costRequested()
  }
}
