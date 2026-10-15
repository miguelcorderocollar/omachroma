import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import qs.Commons
import qs.Ui

FocusScope {
  id: root
  property bool opened: false
  property string imagePath: ""
  property var previousFocus: null
  signal closed()
  visible: opened
  focus: opened
  function open(path) {
    if (!path) return
    previousFocus = Window.window ? Window.window.activeFocusItem : null
    imagePath = path; opened = true
    Qt.callLater(root.forceActiveFocus)
  }
  function close() {
    opened = false
    var target = previousFocus; previousFocus = null
    if (target && target.visible) Qt.callLater(function() { target.forceActiveFocus() })
    else closed()
  }
  Keys.priority: Keys.BeforeItem
  Keys.onEscapePressed: { root.close(); event.accepted = true }
  Rectangle {
    anchors.fill: parent
    color: Qt.rgba(Color.menu.background.r, Color.menu.background.g, Color.menu.background.b, 0.88)
    MouseArea { anchors.fill: parent; onClicked: root.close() }
  }
  BorderSurface {
    id: card
    anchors.centerIn: parent
    width: Math.max(1, Math.min(Style.space(960), root.width - Style.spacing.panelPadding * 2))
    height: Math.max(1, Math.min(Style.space(640), root.height - Style.spacing.panelPadding * 2))
    color: Color.menu.background; radius: Style.cornerRadius
    borderSpec: Border.controlSpec("normal", Color.menu.text, Color.accent)
    Accessible.role: Accessible.Dialog
    Accessible.name: "Result image preview"
    MouseArea { anchors.fill: parent; onClicked: {} }
    ColumnLayout {
      anchors.fill: parent; anchors.margins: Style.spacing.panelPadding
      spacing: Style.spacing.md
      RowLayout {
        Layout.fillWidth: true
        PanelSectionHeader { Layout.fillWidth: true; text: "RESULT PREVIEW" }
        PanelActionButton {
          focusable: true; iconText: "×"; tooltipText: "Close preview"
          Accessible.name: tooltipText
          onClicked: root.close()
        }
      }
      Image {
        Layout.fillWidth: true; Layout.fillHeight: true
        source: root.opened && root.imagePath ? "file://" + root.imagePath : ""
        asynchronous: true; sourceSize.width: 2048
        fillMode: Image.PreserveAspectFit
        Accessible.name: "Enlarged result image"
      }
    }
  }
}
