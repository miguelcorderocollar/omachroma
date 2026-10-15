import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Ui

ColumnLayout {
  id: root
  property string primaryLabel: "Generate"
  property string footText: ""
  property string lastError: ""
  property string costText: ""
  property bool canPrimary: false
  property bool busy: false
  property bool actionBusy: false
  signal primaryClicked()
  signal clearClicked()
  signal cancelClicked()
  spacing: Style.spacing.sm
  RowLayout {
    visible: root.lastError !== "" || root.busy || root.actionBusy && root.footText !== ""
    Layout.fillWidth: true
    LoadingPixels { visible: root.busy || root.actionBusy; running: visible }
    Text {
      Layout.fillWidth: true; textFormat: Text.PlainText; wrapMode: Text.WordWrap
      text: root.lastError || root.footText
      color: root.lastError ? Color.urgent : Color.menu.text
      font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
      Accessible.role: Accessible.StaticText
    }
  }
  RowLayout {
    Layout.fillWidth: true; spacing: Style.spacing.controlGap
    ActionButton {
      text: "Clear"; enabled: !root.busy && !root.actionBusy
      tooltipText: "Clear selection · Ctrl+Delete"
      onClicked: root.clearClicked()
    }
    Item { Layout.fillWidth: true }
    ActionButton {
      visible: root.busy; text: "Stop"
      tooltipText: "Stop local work · Ctrl+."
      onClicked: root.cancelClicked()
    }
    ActionButton {
      visible: !root.busy; text: root.primaryLabel
      selected: root.canPrimary; enabled: root.canPrimary
      tooltipText: "Send to provider · Alt+G" + (root.costText ? "\n" + root.costText : "")
      Accessible.description: root.costText
      onClicked: root.primaryClicked()
    }
  }
}
