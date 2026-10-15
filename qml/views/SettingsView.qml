import QtQuick
import qs.Commons
import qs.Ui
import "../logic/Focus.js" as Focus

Column {
  id: root
  required property var store
  property int tabIndex: 0
  property var tabs: ["Generation", "Models", "Keys", "Data", "Keyboard"]
  signal usePromptRequested()
  signal configureRequested()
  spacing: Style.spacing.lg
  onTabIndexChanged: Focus.closePopups(root)
  function nextTab(direction) { tabIndex = (tabIndex + direction + tabs.length) % tabs.length }
  Flow {
    width: parent.width; spacing: Style.spacing.sm
    Repeater {
      model: root.tabs
      ActionButton { text: modelData; selected: index === root.tabIndex; Accessible.role: Accessible.PageTab; Accessible.name: modelData; onClicked: root.tabIndex = index }
    }
  }
  Column {
    width: parent.width; spacing: Style.spacing.lg
    enabled: !root.store.busy
    opacity: enabled ? 1 : 0.45
    GenerationSettings { visible: root.tabIndex === 0; width: parent.width; store: root.store; onUsePromptRequested: root.usePromptRequested() }
    ModelSettings { visible: root.tabIndex === 1; width: parent.width; store: root.store; onConfigureRequested: root.configureRequested() }
    Column {
      visible: root.tabIndex === 2; width: parent.width; spacing: Style.spacing.lg
      KeySection {
        width: parent.width; provider: "fal"; label: "fal.ai"
        hasKey: root.store.keys.fal; environmentKey: !!root.store.environmentKeys.fal; locked: root.store.busy
        onSaveRequested: root.store.saveKey(provider, key)
        onRemoveRequested: root.store.removeKey(provider)
      }
      KeySection {
        width: parent.width; provider: "openrouter"; label: "OpenRouter"
        hasKey: root.store.keys.openrouter; environmentKey: !!root.store.environmentKeys.openrouter; locked: root.store.busy
        onSaveRequested: root.store.saveKey(provider, key)
        onRemoveRequested: root.store.removeKey(provider)
      }
    }
    DataSettings { visible: root.tabIndex === 3; width: parent.width; store: root.store }
    KeyboardSettings { visible: root.tabIndex === 4; width: parent.width }
  }
  Text {
    visible: root.store.refreshing || root.store.error !== ""
    width: parent.width; textFormat: Text.PlainText; wrapMode: Text.WordWrap
    text: root.store.error || "Refreshing prices…"
    color: root.store.error ? Color.urgent : Color.muted
    font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
  }
}
