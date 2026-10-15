import QtQuick
import qs.Commons
import qs.Ui

Column {
  id: root
  required property var store
  spacing: Style.spacing.sm
  PanelSectionHeader { text: "LOCAL DATA" }
  Text {
    width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
    text: "Images and History stay until you remove them. Clear only resets the current selection."
    color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
  }
  Flow {
    width: parent.width; spacing: Style.spacing.sm
    Button {
      text: "Check storage usage"; focusable: true; bordered: true
      enabled: !root.store.busy && !root.store.dataBusy
      onClicked: root.store.dataAction(false)
    }
    Button {
      text: "Open app data folder"; focusable: true; bordered: true
      enabled: !root.store.busy && !root.store.dataBusy
      onClicked: root.store.dataAction(true)
    }
  }
  Text {
    visible: !!root.store.storageInfo
    width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
    text: root.store.storageInfo ? (root.store.storageInfo.complete ? "" : "At least ") + (root.store.storageInfo.bytes / 1048576).toFixed(1) + " MiB across " + root.store.storageInfo.files + " files. Removing files through the file manager does not remove copies already saved to themes." : ""
    color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
  }
}
