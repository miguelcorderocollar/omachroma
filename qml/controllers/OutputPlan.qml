import QtQuick
import "../logic/BatchPlan.js" as Plan
Item {
  id: root
  property var sources: []
  property var themes: []
  property var references: ({})
  property var config: ({})
  property string prompt: ""
  property var completed: ({})
  property string selectedKey: ""
  signal selectionInvalidated(var record)
  readonly property int totalCount: sources.length * themes.length
  readonly property var jobs: totalCount <= 200 ? Plan.jobs(sources, themes, references, config, prompt) : []
  readonly property var pending: jobs.filter(function(job) { return !completed[job.key] || completed[job.key].status !== "done" && !completed[job.key].accepted })
  readonly property var outputs: jobs.map(function(job) { return Object.assign({}, job, completed[job.key] || {}, {key: job.key, label: job.label, theme: job.theme}) })
  readonly property var selected: {
    for (var i = 0; i < outputs.length; i++) if (outputs[i].key === selectedKey) return outputs[i]
    return null
  }
  readonly property var unsaved: outputs.filter(function(output) { return output.status === "done" && output.resultPath && (!output.installedPath || output.installedTheme !== output.theme) })
  readonly property int savedCount: outputs.length - pending.length - unsaved.length
  readonly property var options: outputs.map(function(output) { return {value: output.key, label: output.label + " · " + Plan.status(completed[output.key])} })
  onJobsChanged: {
    if (!jobs.some(function(job) { return job.key === selectedKey })) {
      if (completed[selectedKey]) selectionInvalidated(completed[selectedKey])
      selectedKey = jobs.length ? jobs[0].key : ""
    }
  }
  function accept(record) {
    if (!record.key) return
    var next = Object.assign({}, completed); next[record.key] = record; completed = next
  }
  function saved(record) {
    var next = Object.assign({}, completed)
    if (next[record.key]) next[record.key] = Object.assign({}, next[record.key], record, {accepted: true})
    completed = next
  }
  function variation() {
    if (!selected) return null
    var key = selectedKey, next = Object.assign({}, completed)
    delete next[key]; completed = next
    return jobs.filter(function(job) { return job.key === key })[0]
  }
}
