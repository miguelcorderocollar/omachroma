import QtQuick
import QtQuick.Controls as QQC
import qs.Commons
import qs.Ui
import "../logic/Omachroma.js" as Omachroma

Column {
  id: root
  required property var store
  signal usePromptRequested()
  signal falKeyRequested()
  spacing: Style.spacing.md
  PanelSectionHeader { text: "API KEYS" }
  KeySection {
    id: falKey
    width: parent.width; provider: "fal"; label: "fal.ai"
    hasKey: root.store.keys.fal
    environmentKey: !!root.store.environmentKeys.fal; locked: root.store.busy
    onSaveRequested: { root.store.saveKey(provider, key) }
    onRemoveRequested: root.store.removeKey(provider)
  }
  KeySection {
    width: parent.width; provider: "openrouter"; label: "OpenRouter"
    hasKey: root.store.keys.openrouter
    environmentKey: !!root.store.environmentKeys.openrouter; locked: root.store.busy
    onSaveRequested: { root.store.saveKey(provider, key) }
    onRemoveRequested: root.store.removeKey(provider)
  }
  PanelSeparator { width: parent.width }
  ModelSettings { width: parent.width; store: root.store }
  PanelSeparator { width: parent.width }
  PanelSectionHeader { text: "GENERATION DEFAULTS" }
  Button {
    text: "Restore model defaults"
    focusable: true; bordered: true
    enabled: root.store.loaded && !root.store.busy
    tooltipText: "Apply your configured model defaults, resolution, quality and upscaling. Keep provider, API keys and prompt."
    onClicked: root.store.restoreModelDefaults()
  }
  Dropdown {
    width: parent.width; label: "Provider"
    options: [{value: "fal", label: "fal.ai"}, {value: "openrouter", label: "OpenRouter"}]
    value: root.store.config.provider || "fal"
    onChanged: { root.store.update("provider", value) }
  }
  Dropdown {
    width: parent.width; label: "Editing model"
    options: Omachroma.editingOptions(root.store.editModels[root.store.config.provider || "fal"], root.store.config.res || "1K")
    value: root.store.config.model || ""
    onChanged: { root.store.update("model", value) }
  }
  Dropdown {
    width: parent.width; label: "Edit resolution"
    visible: (root.store.modelSpec.resolutions || []).length > 0
    options: root.store.modelSpec.resolutions || []
    value: root.store.config.res || "1K"
    onChanged: { root.store.update("res", value) }
  }
  Dropdown {
    visible: (root.store.modelSpec.qualityOptions || []).length > 0
    width: parent.width; label: "Image quality · higher can cost more"
    options: root.store.modelSpec.qualityOptions || []
    value: root.store.config.quality || "high"
    onChanged: { root.store.update("quality", value) }
  }
  Dropdown {
    width: parent.width; label: "Upscaler · fal.ai"
    enabled: !!root.store.keys.fal
    opacity: enabled ? 1 : 0.45
    options: Omachroma.upscalerOptions(root.store.upscaleOptions, root.store.prices)
    value: root.store.keys.fal ? root.store.config.upscaler || "seedvr" : "none"
    onChanged: { root.store.update("upscaler", value) }
  }
  Row {
    visible: !root.store.keys.fal
    spacing: Style.spacing.sm
    Text {
      text: "Upscaling off · fal.ai key required"
      color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
      anchors.verticalCenter: parent.verticalCenter
    }
    Button {
      text: "Add key"; focusable: true; bordered: true
      onClicked: { root.falKeyRequested(); falKey.focusField() }
    }
  }
  Text {
    visible: !!root.store.keys.fal && root.store.config.provider === "openrouter"
    text: "Editing: OpenRouter · Upscaling: fal.ai"
    color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
  }
  Dropdown {
    visible: !!root.store.keys.fal && (root.store.upscaleSpec.models || []).length > 1
    width: parent.width; label: "Upscale model"
    options: Omachroma.upscaleModelOptions(root.store.upscaleModels[root.store.config.upscaler || "seedvr"], root.store.config.upscaler || "seedvr", root.store.prices)
    value: root.store.config.upscaleModel || ""
    onChanged: { root.store.update("upscaleModel", value) }
  }
  Text {
    visible: !!root.store.keys.fal
    width: parent.width; wrapMode: Text.WordWrap
    text: root.store.upscaleSpec.description || ""
    color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
  }
  Dropdown {
    visible: !!root.store.keys.fal && root.store.config.upscaler !== "none"
    width: parent.width; label: "Upscale factor"
    options: (root.store.upscaleSpec.factors || []).map(function(n) { return {value: String(n), label: n + "×"} })
    value: String(root.store.config.upscaleFactor || 2)
    onChanged: { root.store.update("upscaleFactor", parseInt(value)) }
  }
  Dropdown {
    visible: !!root.store.keys.fal && root.store.config.upscaler === "creative" && root.store.config.upscaleModel === "Bloom 2"
    width: parent.width; label: "Creativity · 1 preserves more, 9 invents more"
    options: ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    value: String(root.store.config.creativity || 5)
    onChanged: { root.store.update("creativity", parseInt(value)) }
  }
  PanelSeparator { width: parent.width }
  PanelSectionHeader { text: "DEFAULT PROMPT" }
  PromptInput {
    id: prompt
    width: parent.width; value: root.store.config.prompt || ""
    label: "Default generation prompt"
  }
  Row {
    spacing: Style.spacing.sm
    Button { iconText: "󰆓"; focusable: true; bordered: true; tooltipText: "Save default prompt"; Accessible.name: "Save default prompt"; onClicked: root.store.update("prompt", prompt.text) }
    Button { text: "Use default in Generate"; focusable: true; bordered: true; onClicked: root.usePromptRequested() }
  }
}
