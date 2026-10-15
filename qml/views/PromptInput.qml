import QtQuick
import QtQuick.Controls as QQC
import qs.Commons
import qs.Ui
QQC.ScrollView {
  id: root
  property string value: ""
  property string label: "Generation prompt"
  property string placeholder: "Describe the recolor…"
  property alias text: area.text
  signal edited(string value)
  contentWidth: availableWidth
  height: Math.ceil(metrics.lineSpacing * 4) + Style.spacing.inputPaddingY * 2
  clip: true
  FontMetrics { id: metrics; font.family: Style.font.family; font.pixelSize: Style.font.body }
  QQC.TextArea {
    id: area
    width: root.availableWidth
    text: root.value; wrapMode: Text.Wrap
    onTextChanged: { if (activeFocus) root.edited(text) }
    color: Color.menu.text; selectionColor: Color.accent; selectedTextColor: Color.menu.background
    font.family: Style.font.family; font.pixelSize: Style.font.body
    placeholderText: root.placeholder
    Accessible.name: root.label
    topPadding: Style.spacing.inputPaddingY; bottomPadding: Style.spacing.inputPaddingY
    leftPadding: Style.spacing.controlPaddingX; rightPadding: Style.spacing.controlPaddingX
    background: null
  }
  background: BorderSurface {
    color: Style.controlFill(area.activeFocus, area.hovered, Color.menu.text, Color.accent)
    borderSpec: Border.controlSpec(area.activeFocus ? "focus" : "normal", Color.menu.text, Color.accent)
    radius: Style.cornerRadius
  }
}
