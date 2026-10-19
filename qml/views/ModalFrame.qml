import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import qs.Commons
import qs.Commons as Commons
import qs.Ui

FocusScope {
  id: root
  property bool opened: false
  property string title: ""
  property var previousFocus: null
  default property alias contents: holder.data
  signal closed(bool restoredFocus)
  visible: opened; focus: opened
  function open() {
    previousFocus = Window.window ? Window.window.activeFocusItem : null
    opened = true
    Qt.callLater(function() { closeButton.forceActiveFocus() })
  }
  function close() {
    opened = false
    var target = previousFocus; previousFocus = null
    var restored = !!(target && target.visible && target.enabled)
    if (restored) Qt.callLater(function() { target.forceActiveFocus() })
    closed(restored)
  }
  function owns(item) { while (item) { if (item === root) return true; item = item.parent }; return false }
  function cycle(forward) {
    var current = Window.window ? Window.window.activeFocusItem : closeButton
    for (var i = 0; current && i < 512; i++) {
      current = current.nextItemInFocusChain(forward)
      if (owns(current) && current.visible && current.enabled && current.activeFocusOnTab) { current.forceActiveFocus(); return }
    }
    closeButton.forceActiveFocus()
  }
  Shortcut { sequence: "Tab"; enabled: root.opened; onActivated: root.cycle(true) }
  Shortcut { sequence: "Shift+Tab"; enabled: root.opened; onActivated: root.cycle(false) }
  Shortcut { sequence: "Escape"; enabled: root.opened; onActivated: root.close() }
  Rectangle {
    anchors.fill: parent
    color: Qt.rgba(Commons.Color.menu.background.r, Commons.Color.menu.background.g, Commons.Color.menu.background.b, 0.9)
    MouseArea { anchors.fill: parent; onClicked: root.close() }
  }
  BorderSurface {
    anchors.centerIn: parent
    width: Math.max(1, Math.min(Commons.Style.space(960), root.width - Commons.Style.spacing.panelPadding * 2))
    height: Math.max(1, Math.min(Commons.Style.space(640), root.height - Commons.Style.spacing.panelPadding * 2))
    color: Commons.Color.menu.background; radius: Commons.Style.cornerRadius
    borderSpec: Commons.Border.controlSpec("normal", Commons.Color.menu.text, Commons.Color.accent)
    Accessible.role: Accessible.Dialog; Accessible.name: root.title
    MouseArea { anchors.fill: parent; onClicked: {} }
    ColumnLayout {
      anchors.fill: parent; anchors.margins: Commons.Style.spacing.panelPadding
      spacing: Commons.Style.spacing.md
      RowLayout {
        Layout.fillWidth: true
        PanelSectionHeader { Layout.fillWidth: true; text: root.title }
        IconAction { id: closeButton; iconText: "×"; tooltipText: "Close · Escape"; onClicked: root.close() }
      }
      Item { id: holder; Layout.fillWidth: true; Layout.fillHeight: true }
    }
  }
}
