import QtQuick
import qs.Commons
import qs.Ui

Button {
  focusable: true
  bordered: true
  iconSize: fontSize
  implicitHeight: Math.max(Style.spacing.controlHeight, Style.font.body + Style.spacing.controlPaddingY * 2 + 2)
  height: implicitHeight
  opacity: enabled ? 1 : 0.4
}
