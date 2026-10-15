import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import qs.Commons
import qs.Ui

// Generate mode: source picker + preview, theme + swatches, style-ref grid,
// editable prompt. Data flows down via properties; user actions emit signals
// handled by Panel.qml. Theme tokens come straight from the singletons.
Column {
  id: root
  spacing: Style.spacing.md

  property var sourcePaths: []
  property string theme: ""
  property var themes: []
  property var targetThemes: []
  property int outputCount: 0
  property var referenceData: ({})
  property var backgrounds: []
  property var pickedRefs: []
  property int referenceLimit: 4
  property var swatches: []
  property int copiedSwatchIndex: -1
  property color foreground: Color.menu.text
  property string promptText: ""
  signal sourceAdded(string path)
  signal sourceRemoved(string path)
  signal promptEdited(string value)
  signal customRefRequested()
  signal colorCopied(string value, int index)

  signal browseRequested()
  signal themeSelected(string theme)
  signal targetsChanged(var themes)
  signal refToggled(string path)
  onEnabledChanged: { if (!enabled) { targetSelector.close(); referenceSelector.close() } }


  SourceImages {
    width: parent.width
    paths: root.sourcePaths
    onAdded: { root.sourceAdded(path) }
    onRemoved: { root.sourceRemoved(path) }
    onBrowseRequested: root.browseRequested()
  }

  MultiSelect {
    id: targetSelector
    label: "Target themes"
    width: parent.width
    options: root.themes.map(function(theme) {
      var data = root.referenceData[theme]
      return {value: theme, label: theme, description: root.targetThemes.indexOf(theme) < 0 ? "" : data && data.loaded ? (data.refs.length ? data.refs.length + " references" : "Add a reference") : "Loading references"}
    })
    noSelectionText: "Choose target themes"
    onChanged: { root.targetsChanged(values); targetSelector.values = root.targetThemes }
  }
  Binding { target: targetSelector; property: "values"; value: root.targetThemes }
  Text {
    visible: root.sourcePaths.length > 0 && root.targetThemes.length > 0
    width: parent.width; wrapMode: Text.WordWrap
    text: root.sourcePaths.length + " source" + (root.sourcePaths.length === 1 ? "" : "s") + " × " + root.targetThemes.length + " theme" + (root.targetThemes.length === 1 ? "" : "s") + " = " + root.outputCount + " outputs"
    color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
  }
  Dropdown {
    id: referenceSelector
    visible: root.targetThemes.length > 1
    label: "References for"
    options: root.targetThemes; value: root.theme; width: parent.width
    onChanged: { root.themeSelected(value) }
  }
  RowLayout {
    width: parent.width
    visible: root.swatches.length > 0
    spacing: Style.spacing.sm
    Flow {
      Layout.fillWidth: true
      spacing: Style.spacing.sm
      Repeater {
        model: root.swatches
        ColorSwatch {
          swatchColor: modelData || "transparent"
          copied: root.copiedSwatchIndex === index
          onClicked: root.colorCopied(modelData, index)
        }
      }
    }
    Text {
      text: "Copied"
      opacity: root.copiedSwatchIndex >= 0 ? 1 : 0
      color: Color.menu.text
      font.family: Style.font.family; font.pixelSize: Style.font.caption
      Accessible.name: root.copiedSwatchIndex >= 0 ? "Color copied to clipboard" : ""
    }
  }
  Text {
    visible: root.targetThemes.length > 0
    text: "Style references · " + root.pickedRefs.length + "/" + root.referenceLimit
    color: Qt.darker(root.foreground, 1.4)
    font.family: Style.font.family
    font.pixelSize: Style.font.caption
    font.bold: true
  }
  Button { visible: root.targetThemes.length > 0; text: "Add custom reference…"; focusable: true; bordered: true; onClicked: root.customRefRequested() }
  Flow {
    visible: root.targetThemes.length > 0
    width: parent.width
    spacing: Style.spacing.sm
    Repeater {
      model: root.backgrounds
      Item {
        width: Style.space(88)
        height: Style.space(56)
        activeFocusOnTab: true
        Accessible.role: Accessible.CheckBox
        Accessible.name: modelData.name
        Accessible.checked: picked
        property bool picked: root.pickedRefs.indexOf(modelData.path) >= 0
        BorderSurface {
          anchors.fill: parent
          radius: Style.cornerRadius
          color: "transparent"
          borderSpec: Border.controlSpec(parent.activeFocus ? "focus" : parent.picked ? "selected" : "normal", root.foreground, Color.accent)
          Image {
            anchors.fill: parent
            anchors.margins: 2
            source: "file://" + modelData.path
            asynchronous: true
            sourceSize.width: 176
            fillMode: Image.PreserveAspectCrop
            Accessible.name: modelData.name
          }
        }
        Rectangle {
          visible: parent.picked
          width: Style.space(18)
          height: Style.space(18)
          radius: width / 2
          anchors.top: parent.top
          anchors.right: parent.right
          anchors.margins: Style.space(3)
          color: Color.accent
          Text {
            anchors.centerIn: parent
            text: "✓"
            color: Color.menu.background
            font.bold: true
            font.pixelSize: Style.font.caption
          }
        }
        MouseArea {
          anchors.fill: parent
          cursorShape: Qt.PointingHandCursor
          onClicked: { parent.forceActiveFocus(); root.refToggled(modelData.path) }
        }
        Keys.onSpacePressed: root.refToggled(modelData.path)
        Keys.onReturnPressed: root.refToggled(modelData.path)
      }
    }
  }

  PanelSectionHeader { text: "Shared prompt"; foreground: root.foreground }
  PromptInput {
    width: parent.width; value: root.promptText
    onEdited: { root.promptEdited(value) }
  }
}
