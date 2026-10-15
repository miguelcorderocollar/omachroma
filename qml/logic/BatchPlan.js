function jobs(sources, themes, references, config, prompt) {
  var result = []
  ;(sources || []).forEach(function(source, sourceIndex) {
    ;(themes || []).forEach(function(theme) {
      var refs = (references[theme] || {}).refs || []
      var palette = (references[theme] || {}).swatches || []
      var themedPrompt = prompt + "\nTarget theme: " + theme + (palette.length ? "\nTheme palette: " + palette.join(", ") : "")
      var argv = ["--quality", config.quality || "high", "--upscaler", config.upscaler,
        "--upscale-factor", String(config.upscaleFactor || 2), "--upscale-model", config.upscaleModel || "",
        "--creativity", String(config.creativity || 5), "--theme", theme, "--source", source,
        "--provider", config.provider, "--model", config.model, "--res", config.res,
        "--prompt", themedPrompt, "--install", "--style-refs"].concat(refs)
      // A changed prompt/model/reference selection is a new recipe, not a saved output.
      var key = JSON.stringify(argv)
      result.push({key: key, argv: argv, theme: theme, sourcePath: source,
        name: source.split("/").pop(), label: (sources.length > 1 ? (sourceIndex + 1) + ". " : "") + source.split("/").pop() + " · " + theme})
    })
  })
  return result
}
function ready(themes, references, limit) {
  for (var i = 0; i < themes.length; i++) {
    var data = references[themes[i]]
    if (!data || !data.loaded) return "Loading references for " + themes[i] + "…"
    if (!data.refs.length) return "Choose a style reference for " + themes[i] + "."
    if (data.refs.length > limit) return "Reduce style references for " + themes[i] + "."
  }
  return ""
}
function status(record) {
  if (!record) return "Pending"
  if (record.status === "done") return record.installedPath && record.installedTheme === record.theme ? "Saved" : "Ready to save"
  return record.resultPath ? (record.installedPath && record.installedTheme === record.theme ? "Partial · Saved" : "Partial") : record.status === "cancelled" ? "Stopped" : "Failed"
}
