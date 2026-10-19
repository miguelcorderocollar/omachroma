import QtQuick
import qs.Commons
import qs.Commons as Commons
import qs.Ui

PanelActionButton {
  focusable: true
  bordered: true
  size: Math.max(Commons.Style.spacing.controlHeight, Commons.Style.font.body + Commons.Style.spacing.controlPaddingY * 2 + 2)
  Accessible.name: tooltipText
  opacity: enabled ? 1 : 0.4
}
