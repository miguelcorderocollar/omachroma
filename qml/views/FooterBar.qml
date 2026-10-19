import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Commons as Commons
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
  spacing: Commons.Style.spacing.sm
  RowLayout {
    visible: root.lastError !== "" || root.busy || root.actionBusy && root.footText !== ""
    Layout.fillWidth: true
    LoadingPixels { visible: root.busy || root.actionBusy; running: visible }
    Text {
      Layout.fillWidth: true; textFormat: Text.PlainText; wrapMode: Text.WordWrap
      text: root.lastError || root.footText
      color: root.lastError ? Commons.Color.urgent : Commons.Color.menu.text
      font.family: Commons.Style.font.family; font.pixelSize: Commons.Style.font.bodySmall
      Accessible.role: Accessible.StaticText
    }
  }
  RowLayout {
    Layout.fillWidth: true; spacing: Commons.Style.spacing.controlGap
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
