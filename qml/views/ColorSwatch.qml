import QtQuick
import qs.Commons
import qs.Commons as Commons
import qs.Ui

Button {
  id: root
  property color swatchColor: "transparent"
  property bool copied: false
  implicitWidth: Commons.Style.space(24)
  implicitHeight: Commons.Style.space(24)
  focusable: true
  bordered: true
  foreground: Commons.Color.menu.text
  tooltipText: copied ? "Copied" : "Copy color"
  Accessible.name: "Copy theme color " + String(swatchColor)
  Rectangle {
    anchors.fill: parent
    anchors.margins: Commons.Style.space(2)
    radius: Math.max(0, Commons.Style.cornerRadius - Commons.Style.space(2))
    color: root.swatchColor
    Text {
      anchors.centerIn: parent
      visible: root.copied
      text: "󰄬"
      color: root.swatchColor.r * 0.299 + root.swatchColor.g * 0.587 + root.swatchColor.b * 0.114 > 0.5 ? Qt.rgba(0, 0, 0, 1) : Qt.rgba(1, 1, 1, 1)
      font.family: Commons.Style.font.family
      font.pixelSize: Commons.Style.font.caption
      font.bold: true
    }
  }
}
