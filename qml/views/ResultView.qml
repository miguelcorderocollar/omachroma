import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.Commons
import qs.Commons as Commons
import qs.Ui

// Status lives in the footer; this view owns the retained preview only.
Column {
  id: root
  spacing: Commons.Style.spacing.md

  property string resultPath: ""
  property bool busy: false
  property string installedPath: ""
  property color foreground: Commons.Color.menu.text
  signal previewRequested(string path)
  signal folderRequested()

  RowLayout {
    width: parent.width
    PanelSectionHeader { Layout.fillWidth: true; text: root.busy ? "Saved preview" : "Result"; foreground: root.foreground }

  }
  CursorSurface {
    id: thumbnail
    width: Commons.Style.space(256); height: Commons.Style.space(144)
    foreground: root.foreground; hasCursor: hover.hovered || activeFocus
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: "Enlarge result preview"
    Accessible.onPressAction: thumbnail.activate()
    function activate() { forceActiveFocus(); root.previewRequested(root.resultPath) }
    Image {
      anchors.fill: parent; anchors.margins: Commons.Style.space(2)
      source: root.resultPath !== "" ? "file://" + root.resultPath : ""
      asynchronous: true; sourceSize.width: 768; fillMode: Image.PreserveAspectFit
      Accessible.name: "Result thumbnail"
    }
    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
    TapHandler { onTapped: thumbnail.activate() }
    Keys.onReturnPressed: activate()
    Keys.onEnterPressed: activate()
    Keys.onSpacePressed: activate()
    PanelToolTip { visible: hover.hovered; text: "Click to enlarge" }
  }
  RowLayout {
    width: parent.width
    Text {
      Layout.fillWidth: true; wrapMode: Text.WrapAnywhere; textFormat: Text.PlainText
      text: (root.installedPath || root.resultPath).replace(Quickshell.env("HOME"), "~")
      color: Commons.Color.muted; font.family: Commons.Style.font.family; font.pixelSize: Commons.Style.font.caption
    }
    IconAction {
      focusable: true; iconText: "󰉋"; tooltipText: "Open saved folder"
      Accessible.name: tooltipText
      onClicked: root.folderRequested()
    }
  }
}
