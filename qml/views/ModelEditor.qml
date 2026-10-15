import QtQuick
import QtQuick.Layouts
import qs.Commons

ModalFrame {
  id: root
  required property var store
  title: "Model configuration"
  function edit() { editor.text = JSON.stringify(store.modelConfig, null, 2); store.error = ""; open() }
  Connections { target: root.store; function onModelsSaved() { if (root.opened) root.close() } }
  ColumnLayout {
    anchors.fill: parent; spacing: Style.spacing.md
    PromptInput { id: editor; Layout.fillWidth: true; Layout.fillHeight: true; label: "Model configuration JSON"; placeholder: "Model configuration JSON" }
    Text {
      visible: root.store.error !== ""
      Layout.fillWidth: true; textFormat: Text.PlainText; wrapMode: Text.WordWrap
      text: root.store.error; color: Color.urgent
      font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
    }
    RowLayout {
      Layout.fillWidth: true; spacing: Style.spacing.sm
      ActionButton { text: "Cancel"; onClicked: root.close() }
      Item { Layout.fillWidth: true }
      ActionButton { text: "Validate and save"; enabled: !root.store.busy; onClicked: root.store.saveModels(editor.text) }
    }
  }
}
