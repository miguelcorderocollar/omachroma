import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Ui
import "../logic/Omachroma.js" as Omachroma

Column {
  id: root
  required property var store
  signal usePromptRequested()
  spacing: Style.spacing.md
  Dropdown {
    width: parent.width; label: "Provider"
    options: [{value:"fal",label:"fal.ai"},{value:"openrouter",label:"OpenRouter"}]
    value: root.store.config.provider || "fal"
    onChanged: root.store.update("provider", value)
  }
  Dropdown {
    width: parent.width; label: "Editing model"
    options: Omachroma.editingOptions(root.store.editModels[root.store.config.provider || "fal"], root.store.config.res || "1K")
    value: root.store.config.model || ""
    onChanged: root.store.update("model", value)
  }
  Dropdown {
    width: parent.width; label: "Resolution"; visible: (root.store.modelSpec.resolutions || []).length > 0
    options: root.store.modelSpec.resolutions || []; value: root.store.config.res || "1K"
    onChanged: root.store.update("res", value)
  }
  Dropdown {
    width: parent.width; label: "Quality"; visible: (root.store.modelSpec.qualityOptions || []).length > 0
    options: root.store.modelSpec.qualityOptions || []; value: root.store.config.quality || "high"
    onChanged: root.store.update("quality", value)
  }
  PanelSeparator { width: parent.width }
  Toggle {
    width: parent.width; label: "Enable upscaling"
    checked: root.store.upscalingEnabled
    enabled: !!root.store.keys.fal && root.store.upscaleOptions.some(function(option) { return option.value !== "none" })
    description: root.store.keys.fal ? "" : "fal.ai key required"
    Accessible.role: Accessible.CheckBox; Accessible.name: label; Accessible.checked: checked
    Accessible.onPressAction: root.store.update("upscaleEnabled", !checked)
    onClicked: root.store.update("upscaleEnabled", !checked)
  }
  Column {
    width: parent.width; visible: root.store.upscalingEnabled
    spacing: Style.spacing.md
    Dropdown {
      width: parent.width; label: "Upscaler"
      options: Omachroma.upscalerOptions(root.store.upscaleOptions.filter(function(option) { return option.value !== "none" }), root.store.prices)
      value: root.store.config.upscaler || "seedvr"
      onChanged: root.store.update("upscaler", value)
    }
    Dropdown {
      width: parent.width; label: "Upscale model"; visible: (root.store.upscaleSpec.models || []).length > 1
      options: Omachroma.upscaleModelOptions(root.store.upscaleModels[root.store.config.upscaler], root.store.config.upscaler, root.store.prices)
      value: root.store.config.upscaleModel || ""
      onChanged: root.store.update("upscaleModel", value)
    }
    Dropdown {
      width: parent.width; label: "Factor"
      options: (root.store.upscaleSpec.factors || []).map(function(n) { return {value:String(n),label:n+"×"} })
      value: String(root.store.config.upscaleFactor || 2)
      onChanged: root.store.update("upscaleFactor", parseInt(value))
    }
    Dropdown {
      width: parent.width; label: "Creativity"
      visible: root.store.config.upscaler === "creative" && root.store.config.upscaleModel === "Bloom 2"
      options: ["1","2","3","4","5","6","7","8","9"]; value: String(root.store.config.creativity || 5)
      onChanged: root.store.update("creativity", parseInt(value))
    }
  }
  PanelSeparator { width: parent.width }
  PanelSectionHeader { text: "Default prompt" }
  PromptInput { id: prompt; width: parent.width; value: root.store.config.prompt || ""; label: "Default generation prompt" }
  RowLayout {
    width: parent.width; spacing: Style.spacing.sm
    ActionButton { iconText: "󰆓"; text: "Save prompt"; onClicked: root.store.update("prompt", prompt.text) }
    ActionButton { text: "Use in Generate"; onClicked: root.usePromptRequested() }
    Item { Layout.fillWidth: true }
  }
  ActionButton { text: "Restore defaults"; tooltipText: "Apply configured model defaults; preserve provider, keys and prompt"; onClicked: root.store.restoreModelDefaults() }
}
