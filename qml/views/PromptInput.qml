import QtQuick
import QtQuick.Controls as QQC
import qs.Commons
import qs.Commons as Commons
import qs.Ui
QQC.ScrollView {
  id: root
  property string value: ""
  property string label: "Generation prompt"
  property string placeholder: "Describe the recolor…"
  property alias text: area.text
  signal edited(string value)
  contentWidth: availableWidth
  height: Math.ceil(metrics.lineSpacing * 4) + Commons.Style.spacing.inputPaddingY * 2
  clip: true
  FontMetrics { id: metrics; font.family: Commons.Style.font.family; font.pixelSize: Commons.Style.font.body }
  QQC.TextArea {
    id: area
    width: root.availableWidth
    text: root.value; wrapMode: Text.Wrap
    onTextChanged: { if (activeFocus) root.edited(text) }
    color: Commons.Color.menu.text; selectionColor: Commons.Color.accent; selectedTextColor: Commons.Color.menu.background
    font.family: Commons.Style.font.family; font.pixelSize: Commons.Style.font.body
    placeholderText: root.placeholder
    Accessible.name: root.label
    topPadding: Commons.Style.spacing.inputPaddingY; bottomPadding: Commons.Style.spacing.inputPaddingY
    leftPadding: Commons.Style.spacing.controlPaddingX; rightPadding: Commons.Style.spacing.controlPaddingX
    background: null
  }
  background: BorderSurface {
    color: Commons.Style.controlFill(area.activeFocus, area.hovered, Commons.Color.menu.text, Commons.Color.accent)
    borderSpec: Commons.Border.controlSpec(area.activeFocus ? "focus" : "normal", Commons.Color.menu.text, Commons.Color.accent)
    radius: Commons.Style.cornerRadius
  }
}
