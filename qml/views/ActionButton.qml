import QtQuick
import qs.Commons
import qs.Commons as Commons
import qs.Ui

Button {
  focusable: true
  bordered: true
  iconSize: fontSize
  implicitHeight: Math.max(Commons.Style.spacing.controlHeight, Commons.Style.font.body + Commons.Style.spacing.controlPaddingY * 2 + 2)
  height: implicitHeight
  opacity: enabled ? 1 : 0.4
}
