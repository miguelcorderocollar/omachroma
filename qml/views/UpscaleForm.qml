import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Ui

// Upscale mode: existing image + optional theme install + factor.
// Data in via properties, actions out via signals; Panel.qml owns state.
Column {
  id: root
  spacing: Style.spacing.md

  property string upscalePath: ""
  property string upscaleTheme: ""
  property var themes: []
  property int upscaleFactor: 2
  property var factorOptions: [2, 4]
  property color foreground: Color.menu.text

  signal pathEdited(string path)
  signal browseRequested()
  signal themeSelected(string theme)
  signal factorSelected(int factor)

  RowLayout {
    width: parent.width
    PanelSectionHeader { Layout.fillWidth: true; text: "Image to upscale"; foreground: root.foreground }

  }
  Item {
    width: parent.width
    height: upscaleField.implicitHeight
    TextField {
      id: upscaleField
      anchors.left: parent.left
      anchors.right: upscaleBrowseButton.left
      anchors.rightMargin: Style.spacing.controlGap
      anchors.verticalCenter: parent.verticalCenter
      foreground: root.foreground
      placeholderText: "Type an image path, like ~/Pictures/photo.jpg"
      text: root.upscalePath
      onTextEdited: root.pathEdited(text)
    }
    ActionButton {
      id: upscaleBrowseButton
      anchors.right: parent.right
      anchors.verticalCenter: parent.verticalCenter
      height: upscaleField.implicitHeight
      iconText: "󰉋"
      Accessible.name: "Choose image to upscale"
      tooltipText: "Choose an image"
      focusable: true
      bordered: true
      foreground: root.foreground
      onClicked: root.browseRequested()
    }
  }
  BorderSurface {
    visible: root.upscalePath !== ""
    width: Style.space(88)
    height: Style.space(56)
    radius: Style.cornerRadius
    color: "transparent"
    borderSpec: Border.controlSpec("normal", root.foreground, Color.accent)
    Image {
      anchors.fill: parent
      anchors.margins: 2
      source: root.upscalePath !== "" ? "file://" + root.upscalePath : ""
      asynchronous: true
      sourceSize.width: 176
      fillMode: Image.PreserveAspectCrop
      Accessible.name: "Image to upscale preview"
    }
  }

  Dropdown {
    label: "Install into theme (optional)"
    options: ["(just save)"].concat(root.themes)
    value: root.upscaleTheme === "" ? "(just save)" : root.upscaleTheme
    width: parent.width
    onChanged: { root.themeSelected(value === "(just save)" ? "" : value) }
  }
  Dropdown {
    label: "Factor"
    options: root.factorOptions.map(function(n) { return {value: String(n), label: n + "×"} })
    value: String(root.upscaleFactor)
    width: parent.width
    onChanged: { root.factorSelected(parseInt(value)) }
  }
}
