import QtQuick
import Quickshell.Io
Item {
  id: root
  property string backend: ""
  property var targets: []
  property var data: ({})
  property var queue: []
  property int limit: 13
  property string error: ""
  readonly property bool busy: process.running || queue.length > 0
  function load(themes) {
    targets = themes.slice()
    queue = themes.filter(function(theme) { return !(data[theme] && data[theme].loaded) && (!process.running || process.theme !== theme) })
    next()
  }
  function next() {
    if (process.running || !queue.length) return
    process.theme = queue[0]; queue = queue.slice(1)
    process.command = ["python3", backend, "--theme-bundle", process.theme]
    process.running = true
  }
  function update(theme, patch) {
    var nextData = Object.assign({}, data)
    nextData[theme] = Object.assign({}, data[theme] || {}, patch)
    data = nextData
  }
  function clearSelections() {
    var nextData = Object.assign({}, data)
    targets.concat(queue, process.running ? [process.theme] : []).forEach(function(theme) { if (!nextData[theme]) nextData[theme] = {} })
    Object.keys(nextData).forEach(function(theme) { nextData[theme] = Object.assign({}, nextData[theme], {refs: []}) })
    data = nextData; error = ""
  }
  function toggle(theme, path) {
    var refs = ((data[theme] || {}).refs || []).slice(), index = refs.indexOf(path)
    if (index >= 0) refs.splice(index, 1)
    else if (refs.length < limit) refs.push(path)
    else { error = "This model supports up to " + limit + " references per theme."; return }
    update(theme, {refs: refs}); error = ""
  }
  function custom(theme, path) {
    var item = data[theme] || {}, images = (item.backgrounds || []).slice()
    if (!images.some(function(image) { return image.path === path })) images.push({name: path.split("/").pop(), path: path})
    update(theme, {backgrounds: images})
    if ((item.refs || []).indexOf(path) < 0) toggle(theme, path)
  }
  Process {
    id: process
    property string theme: ""
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var value = JSON.parse(text), old = root.data[process.theme] || {}
          root.update(process.theme, {loaded: true, backgrounds: value.backgrounds || [], swatches: value.swatches || [], refs: old.refs || (value.backgrounds || []).slice(0, Math.min(3, root.limit)).map(function(image) { return image.path })})
          root.error = ""
        } catch (e) { root.error = "Could not load references for " + process.theme + ". Reselect it to retry." }
      }
    }
    onExited: { if (exitCode !== 0) root.error = "Could not load references for " + theme + ". Reselect it to retry."; Qt.callLater(root.next) }
  }
}
