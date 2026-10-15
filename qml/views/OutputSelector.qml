import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Ui
Column {
  id: root
  required property var plan
  property bool busy: false
  property var external: null
  signal selected(string key)
  signal saveRemaining()
  signal regenerate()
  spacing: Style.spacing.sm
  Dropdown {
    width: parent.width; label: "Output"
    options: root.plan.options.concat(root.external ? [{value: "history:" + root.external.id, label: (root.external.name || "Wallpaper") + " · " + root.external.theme + " · History"}] : [])
    value: root.external ? "history:" + root.external.id : root.plan.selectedKey
    onChanged: { root.selected(value) }
  }
  RowLayout {
    width: parent.width
    Text {
      Layout.fillWidth: true
      text: root.plan.savedCount + " saved · " + root.plan.unsaved.length + " ready to save · " + root.plan.pending.length + " remaining"
      wrapMode: Text.WordWrap; color: Color.muted
      font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
    }
    Button {
      visible: root.plan.unsaved.length > 0
      text: "Save remaining (" + root.plan.unsaved.length + ")"
      enabled: !root.busy; focusable: true; bordered: true
      tooltipText: "Copy only completed, unsaved outputs to their own target themes"
      onClicked: root.saveRemaining()
    }
    Button {
      visible: !!(!root.external && root.plan.selected && (root.plan.selected.status === "done" || root.plan.selected.accepted))
      text: "New variation"; enabled: !root.busy; focusable: true; bordered: true
      tooltipText: "Generate this source/theme again. Billed as a new output; keep the old result in History."
      onClicked: root.regenerate()
    }
  }
  Text {
    visible: root.plan.selected && !root.plan.selected.resultPath
    width: parent.width; wrapMode: Text.WordWrap
    text: root.plan.selected && root.plan.selected.error || "This output has not been generated yet."
    color: root.plan.selected && root.plan.selected.error ? Color.urgent : Color.muted
    font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
  }
}
