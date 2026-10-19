import QtQuick
import qs.Commons
import qs.Commons as Commons
import qs.Ui

Column {
  id: root
  required property var store
  spacing: Commons.Style.spacing.sm
  PanelSectionHeader { text: "LOCAL DATA" }
  Text {
    width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
    text: "Clear keeps saved files."
    color: Commons.Color.muted; font.family: Commons.Style.font.family; font.pixelSize: Commons.Style.font.bodySmall
  }
  Flow {
    width: parent.width; spacing: Commons.Style.spacing.sm
    ActionButton {
      text: "Check usage"; focusable: true; bordered: true
      enabled: !root.store.busy && !root.store.dataBusy
      onClicked: root.store.dataAction(false)
    }
    ActionButton {
      text: "Open data folder"; focusable: true; bordered: true
      enabled: !root.store.busy && !root.store.dataBusy
      onClicked: root.store.dataAction(true)
    }
  }
  Text {
    visible: !!root.store.storageInfo
    width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
    text: root.store.storageInfo ? (root.store.storageInfo.complete ? "" : "At least ") + (root.store.storageInfo.bytes / 1048576).toFixed(1) + " MiB across " + root.store.storageInfo.files + " files." : ""
    color: Commons.Color.muted; font.family: Commons.Style.font.family; font.pixelSize: Commons.Style.font.bodySmall
  }
}
