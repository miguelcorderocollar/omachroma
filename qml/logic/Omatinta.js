// Provider rates are dated snapshots. Output size, quality and input images can change the bill.
function dollars(value) {
  var amount = Number(value)
  if (amount > 0 && amount < 0.0001) return "$" + amount.toPrecision(4)
  return "$" + amount.toFixed(4).replace(/0+$/, "").replace(/\.$/, "")
}

function reportedCost(report) {
  if (!report) return "Final cost not reported"
  function amount(value) { return "$" + Number(value).toFixed(6).replace(/0+$/, "").replace(/\.$/, "") }
  if (report.complete && report.total !== null && report.total !== undefined)
    return "Final cost " + amount(report.total)
  var parts = []
  if (report.edit !== null && report.edit !== undefined) parts.push("Reported edit " + amount(report.edit))
  if (report.upscale !== null && report.upscale !== undefined) parts.push("Reported upscale " + amount(report.upscale))
  if (!parts.length) return "Final cost not reported"
  if (report.upscaleRequested && (report.upscale === null || report.upscale === undefined)) parts.push("upscale not reported")
  return parts.join(" · ")
}

function providerRate(rates) {
  var groups = {}
  ;(rates || []).forEach(function(rate) {
    var tokens = rate.unit === "token" || rate.unit === "tokens"
    var name = rate.billable + "/" + (tokens ? "M tokens" : rate.unit) + (rate.conditional ? " (conditional)" : "")
    if (!groups[name]) groups[name] = []
    groups[name].push(Number(rate.usd) * (tokens ? 1000000 : 1))
  })
  return Object.keys(groups).map(function(name) {
    var values = groups[name], low = Math.min.apply(null, values), high = Math.max.apply(null, values)
    return dollars(low) + (high !== low ? "–" + dollars(high) : "") + "/" + name
  }).join(" + ") || "price unavailable"
}

function editingRate(spec, resolution) {
  if (spec.rates && spec.rates.length) return providerRate(spec.rates)
  var price = spec.price || {}, sizes = spec.resolutions || []
  if (price.outputToken) return dollars(price.outputToken * 1000000) + "/M output image tokens"
  var size = sizes.indexOf(resolution) >= 0 ? resolution : sizes[0]
  var rate = price[size] !== undefined ? price[size] : price.image
  if (rate === undefined) return "price unavailable"
  var text = "~" + dollars(rate) + "/image" + (price[size] !== undefined ? " at " + size : "")
  if (price.inputImage) text += " + " + dollars(price.inputImage) + "/extra reference"
  return text
}

function pricedLabel(label, rate) { return label.split(" · ")[0] + " · " + rate }
function editingOptions(models, resolution) {
  return (models || []).map(function(spec) {
    return {value: spec.value, label: pricedLabel(spec.label, editingRate(spec, resolution)) + (spec.available === false ? " · unavailable" : "")}
  })
}
function upscaleRate(kind, prices) {
  if (kind === "none") return "$0 extra"
  var rate = (prices.upscale || {})[kind] || {}
  if (rate.rates) return providerRate(rate.rates)
  if (rate.unitMP && rate.usd !== undefined) return dollars(rate.usd) + "/" + rate.unitMP + " MP block"
  return rate.rateText || "price unavailable"
}
function upscalerOptions(options, prices) {
  return (options || []).map(function(option) { return {value: option.value, label: pricedLabel(option.label, upscaleRate(option.value, prices))} })
}
function upscaleModelOptions(models, kind, prices) {
  return (models || []).map(function(model) { return {value: model, label: pricedLabel(model, upscaleRate(kind, prices))} })
}

function priceText(config, mode, prices, w, h, factor, modelSpec, count) {
  if (!prices.checked || !modelSpec) return "Loading price estimate…"
  var text = "", total = 0, known = true, price = modelSpec.price || {}
  count = mode === "upscale" ? 1 : count || 0
  if (mode === "generate") {
    text = "Edit " + editingRate(modelSpec, config.res)
    // Provider unit rates can have resolution/quality adjustments. Do not turn them into a promised bill.
    var edit = !modelSpec.rates && !price.inputImage && !price.outputToken ? (price[config.res] !== undefined ? price[config.res] : price.image) : undefined
    if (edit !== undefined) total += edit
    else known = false
    var dimensions = (modelSpec.dimensions || {})[config.res]
    w = dimensions ? dimensions[0] : 0; h = dimensions ? dimensions[1] : 0
    factor = config.upscaleFactor || 2
  }
  if (config.upscaler !== "none") {
    var unit = (prices.upscale || {})[config.upscaler] || {}
    var mp = w && h ? w * h * factor * factor / 1000000 : 0
    var cost = !unit.rates && mp ? unit.unitMP ? Math.ceil(mp / unit.unitMP) * unit.usd : unit.usdPerMP !== undefined ? mp * unit.usdPerMP : null : null
    text += (text ? " + " : "") + (cost !== null ? "upscale ~ " + dollars(cost) : "upscale " + upscaleRate(config.upscaler, prices))
    if (cost === null) known = false
    else total += cost
  }
  var checked = modelSpec.priceChecked || prices.checked
  var up = (prices.upscale || {})[config.upscaler] || {}
  text += (text ? "\n" : "") + (count > 0 && known ? (count > 1 ? "Remaining batch ~ " : "Estimate ~ ") + dollars(total * count) : count > 1 ? "Batch total varies with usage; " + count + " outputs remain" : "Total varies with usage")
  text += "\nEdit rates: " + checked + (config.upscaler !== "none" ? " · Upscale rates: " + (up.checkedAt || prices.checked) : "")
  return text + " · quality, dimensions and references may add cost"
}
