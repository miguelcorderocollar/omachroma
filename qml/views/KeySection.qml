import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Commons as Commons
import qs.Ui

Column {
  id: root
  property string provider: "fal"
  property string label: "fal.ai"
  property bool hasKey: false
  property bool locked: false
  property bool environmentKey: false
  signal saveRequested(string provider, string key)
  signal removeRequested(string provider)
  spacing: Commons.Style.spacing.sm
  function focusField() { keyField.forceActiveFocus() }
  Row {
    spacing: Commons.Style.spacing.sm
    Text {
      text: root.label
      color: Commons.Color.menu.text
      font.family: Commons.Style.font.family; font.pixelSize: Commons.Style.font.bodySmall
    }
    Text {
      visible: root.hasKey
      text: "✓"
      color: Commons.Color.pick("omatinta.success", "mediumseagreen")
      font.family: Commons.Style.font.family; font.pixelSize: Commons.Style.font.bodySmall
      Accessible.name: root.label + " API key saved"
    }
  }
  RowLayout {
    width: parent.width; spacing: Commons.Style.spacing.sm
    TextField {
      id: keyField
      Layout.fillWidth: true
      password: true
      enabled: !root.locked
      foreground: Commons.Color.menu.text
      placeholderText: root.hasKey ? "••••••••••••" : "Paste " + root.label + " key"
      Accessible.name: root.hasKey ? root.label + " saved API key, masked. Type to replace." : root.label + " API key"
      onAccepted: { root.saveRequested(root.provider, text); clear() }
    }
    IconAction {
      id: saveButton
      iconText: "󰆓"; focusable: true; bordered: true
      Layout.alignment: Qt.AlignVCenter
      Layout.preferredHeight: keyField.implicitHeight
      Layout.preferredWidth: keyField.implicitHeight
      Accessible.name: "Save " + root.label + " API key"
      enabled: !root.locked && keyField.text.trim() !== ""
      tooltipText: "Save " + root.label + " API key"
      onClicked: { root.saveRequested(root.provider, keyField.text); keyField.clear() }
    }
    IconAction {
      iconText: "󰆴"; tooltipText: "Remove saved " + root.label + " key"
      hoverColor: Commons.Color.urgent
      Layout.preferredHeight: keyField.implicitHeight; Layout.preferredWidth: keyField.implicitHeight
      enabled: root.hasKey && !root.locked
      onClicked: root.removeRequested(root.provider)
    }
  }
  Text {
    visible: root.environmentKey
    width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
    text: "An environment key is active. Removing the saved key does not remove it."
    color: Commons.Color.muted; font.family: Commons.Style.font.family; font.pixelSize: Commons.Style.font.bodySmall
  }
}
