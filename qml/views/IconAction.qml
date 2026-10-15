import QtQuick
import qs.Commons
import qs.Ui

PanelActionButton {
  focusable: true
  bordered: true
  size: Math.max(Style.spacing.controlHeight, Style.font.body + Style.spacing.controlPaddingY * 2 + 2)
  Accessible.name: tooltipText
  opacity: enabled ? 1 : 0.4
}
