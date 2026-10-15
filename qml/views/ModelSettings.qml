import QtQuick
import qs.Commons
import qs.Ui
import "../logic/Omachroma.js" as Omachroma

Column {
  id: root
  required property var store
  signal configureRequested()
  spacing: Style.spacing.md
  function changeModel(action) {
    var next = JSON.parse(JSON.stringify(store.modelConfig))
    var provider = store.config.provider || "fal", model = store.config.model
    if (action === "default") next.defaults[provider] = model
    if (action === "hide") {
      var choices = store.editModels[provider].filter(function(item) { return item.value !== model })
      if (!choices.length) return
      next.hidden[provider].push(model)
      if (next.defaults[provider] === model || store.providerDefaults[provider] === model) next.defaults[provider] = choices[0].value
    }
    if (action === "show") next.hidden = {fal: [], openrouter: [], upscalers: []}
    store.saveModels(JSON.stringify(next))
  }
  Dropdown {
    width: parent.width; label: "Provider"
    options: [{value:"fal",label:"fal.ai"},{value:"openrouter",label:"OpenRouter"}]
    value: root.store.config.provider || "fal"; onChanged: root.store.update("provider", value)
  }
  Dropdown {
    width: parent.width; label: "Editing model"
    options: Omachroma.editingOptions(root.store.editModels[root.store.config.provider || "fal"], root.store.config.res || "1K")
    value: root.store.config.model || ""; onChanged: root.store.update("model", value)
  }
  Flow {
    width: parent.width; spacing: Style.spacing.sm
    ActionButton { text: "Set default"; onClicked: root.changeModel("default") }
    ActionButton { text: "Hide model"; enabled: (root.store.editModels[root.store.config.provider || "fal"] || []).length > 1; onClicked: root.changeModel("hide") }
    ActionButton { text: "Show hidden"; onClicked: root.changeModel("show") }
  }
  PanelSeparator { width: parent.width }
  Flow {
    width: parent.width; spacing: Style.spacing.sm
    ActionButton {
      text: "Refresh prices"; iconText: "󰑐"
      tooltipText: root.store.message || "Refresh known models; keep cached rates if offline"
      onClicked: root.store.refreshPrices()
    }
    ActionButton { text: "Configure models…"; onClicked: root.configureRequested() }
  }
  Text {
    width: parent.width; textFormat: Text.PlainText; wrapMode: Text.WordWrap
    text: "Rates: " + (root.store.modelSpec.priceChecked || root.store.prices.checked || "not checked")
    color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.caption
  }
  Text {
    visible: root.store.catalogWarning !== "" || root.store.refreshWarning !== ""
    width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
    text: root.store.catalogWarning || root.store.refreshWarning
    color: Color.urgent; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
  }
}
