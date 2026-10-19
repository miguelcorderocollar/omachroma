import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Commons as Commons
import qs.Ui
Column {
  id: root
  required property var plan
  property bool busy: false
  property var external: null
  signal selected(string key)
  signal saveRemaining()
  signal regenerate()
  spacing: Commons.Style.spacing.sm
  Dropdown {
    width: parent.width; label: "Output"
    options: root.plan.options.concat(root.external ? [{value: "history:" + root.external.id, label: (root.external.name || "Wallpaper") + " · " + root.external.theme + " · History"}] : [])
    value: root.external ? "history:" + root.external.id : root.plan.selectedKey
    onChanged: { root.selected(value) }
  }
  RowLayout {
    width: parent.width
    ActionButton {
      visible: root.plan.unsaved.length > 0
      text: "Save remaining (" + root.plan.unsaved.length + ")"
      enabled: !root.busy; focusable: true; bordered: true
      tooltipText: "Copy only completed, unsaved outputs to their own target themes"
      onClicked: root.saveRemaining()
    }
    ActionButton {
      visible: !!(!root.external && root.plan.selected && (root.plan.selected.status === "done" || root.plan.selected.accepted))
      text: "New variation"; enabled: !root.busy; focusable: true; bordered: true
      tooltipText: "Generate this source/theme again. Billed as a new output; keep the old result in History."
      onClicked: root.regenerate()
    }
  }
  Text {
    visible: !root.external && !!(root.plan.selected && root.plan.selected.error)
    width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
    text: root.plan.selected && root.plan.selected.error || ""
    color: Commons.Color.urgent; font.family: Commons.Style.font.family; font.pixelSize: Commons.Style.font.bodySmall
  }
}
