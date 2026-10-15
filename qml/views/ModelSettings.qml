import QtQuick
import qs.Commons
import qs.Ui

Column {
  id: root
  required property var store
  property bool editing: false
  spacing: Style.spacing.sm
  function changeModel(action) {
    var next = JSON.parse(JSON.stringify(store.modelConfig))
    var provider = store.config.provider || "fal"
    var model = store.config.model
    if (action === "default") next.defaults[provider] = model
    if (action === "hide") {
      var choices = store.editModels[provider].filter(function(item) { return item.value !== model })
      if (!choices.length) return
      next.hidden[provider].push(model)
      if (next.defaults[provider] === model || store.providerDefaults[provider] === model)
        next.defaults[provider] = choices[0].value
    }
    if (action === "show") next.hidden = {fal: [], openrouter: [], upscalers: []}
    store.saveModels(JSON.stringify(next))
  }
  PanelSectionHeader { text: "MODELS & PRICES" }
  Text {
    width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
    text: "Keep your preferred models, hide others, or add compatible models in the configuration editor. New models must use a supported request adapter."
    color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
  }
  Flow {
    width: parent.width; spacing: Style.spacing.sm
    Button {
      text: "Refresh prices"; focusable: true; bordered: true
      enabled: !root.store.busy
      tooltipText: "Refresh known model availability and provider rates; keep cached rates if offline"
      onClicked: root.store.refreshPrices()
    }
    Button {
      text: "Use selected model by default"; focusable: true; bordered: true
      enabled: root.store.loaded && !root.store.busy
      onClicked: root.changeModel("default")
    }
    Button {
      text: "Hide selected model"; focusable: true; bordered: true
      enabled: !root.store.busy && (root.store.editModels[root.store.config.provider || "fal"] || []).length > 1
      onClicked: root.changeModel("hide")
    }
    Button {
      text: "Show hidden models"; focusable: true; bordered: true
      enabled: !root.store.busy
      onClicked: root.changeModel("show")
    }
  }
  Text {
    visible: root.store.catalogWarning !== ""
    width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
    text: root.store.catalogWarning
    color: Color.urgent; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
  }
  Button {
    text: root.editing ? "Close model configuration" : "Edit model configuration"
    focusable: true; bordered: true; enabled: !root.store.busy
    onClicked: {
      if (!root.editing) editor.text = JSON.stringify(root.store.modelConfig, null, 2)
      root.editing = !root.editing
    }
  }
  Column {
    visible: root.editing; width: parent.width; spacing: Style.spacing.sm
    Text {
      width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.PlainText
      text: "JSON configuration · saved to " + root.store.dataPath + "/models.json. See docs/models.md for adapters and examples. Saving validates the entire file before replacing it. Manual price overrides take precedence over refreshed rates."
      color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
    }
    PromptInput {
      id: editor; width: parent.width; height: Style.space(240)
      label: "Model configuration JSON"; placeholder: "Paste model configuration JSON"
    }
    Button {
      text: "Validate and save model configuration"; focusable: true; bordered: true
      enabled: !root.store.busy
      onClicked: root.store.saveModels(editor.text)
    }
  }
}
