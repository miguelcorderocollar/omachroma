import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Commons as Commons
import qs.Ui

Column {
  id: root
  property var paths: []
  signal added(string path)
  signal removed(string path)
  signal browseRequested()
  spacing: Commons.Style.spacing.sm
  function addPath() {
    if (!pathField.text.trim()) return
    root.added(pathField.text.trim()); pathField.clear()
  }
  RowLayout {
    width: parent.width
    PanelSectionHeader { Layout.fillWidth: true; text: "SOURCE IMAGES" }

  }
  RowLayout {
    width: parent.width; spacing: Commons.Style.spacing.controlGap
    TextField {
      id: pathField; Layout.fillWidth: true; foreground: Commons.Color.menu.text
      placeholderText: "Paste an image path, then press Enter"
      Accessible.name: "Add source image path"
      onAccepted: root.addPath()
    }
    ActionButton {
      iconText: "󰐕"; focusable: true; bordered: true
      Layout.preferredHeight: pathField.implicitHeight
      enabled: pathField.text.trim() !== ""
      Accessible.name: "Add source image path"; tooltipText: "Add image path"
      onClicked: root.addPath()
    }
    ActionButton {
      iconText: "󰉋"; focusable: true; bordered: true
      Layout.preferredHeight: pathField.implicitHeight
      Accessible.name: "Choose source images"; tooltipText: "Choose one or more source images"
      onClicked: root.browseRequested()
    }
  }
  Flow {
    width: parent.width; spacing: Commons.Style.spacing.sm
    Repeater {
      model: root.paths
      BorderSurface {
        id: thumbnail
        required property string modelData
        required property int index
        width: Commons.Style.space(88); height: Commons.Style.space(56)
        color: "transparent"; radius: Commons.Style.cornerRadius
        borderSpec: Commons.Border.controlSpec("normal", Commons.Color.menu.text, Commons.Color.accent)
        Image {
          anchors.fill: parent; anchors.margins: Commons.Style.space(2)
          source: "file://" + thumbnail.modelData
          asynchronous: true; sourceSize.width: 176
          fillMode: Image.PreserveAspectCrop
          Accessible.name: "Source " + thumbnail.modelData.split("/").pop()
        }
        BorderSurface {
          anchors.right: parent.right; anchors.top: parent.top
          width: removeButton.width; height: removeButton.height
          color: Commons.Color.menu.background; radius: Commons.Style.cornerRadius
          PanelActionButton {
            id: removeButton; focusable: true; iconText: "×"
            tooltipText: "Remove " + thumbnail.modelData.split("/").pop()
            Accessible.name: tooltipText
            onClicked: root.removed(thumbnail.modelData)
          }
        }
        Rectangle {
          visible: root.paths.length > 1
          anchors.left: parent.left; anchors.bottom: parent.bottom
          width: Commons.Style.space(16); height: width; color: Commons.Color.menu.background
          Text { anchors.centerIn: parent; text: thumbnail.index + 1; color: Commons.Color.menu.text; font.family: Commons.Style.font.family; font.pixelSize: Commons.Style.font.caption }
        }
        HoverHandler { id: hover }
        PanelToolTip { visible: hover.hovered; text: thumbnail.modelData }
      }
    }
  }
}
