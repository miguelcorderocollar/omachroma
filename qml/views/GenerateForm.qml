import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import qs.Commons
import qs.Commons as Commons
import qs.Ui

// Generate mode: source picker + preview, theme + swatches, style-ref grid,
// editable prompt. Data flows down via properties; user actions emit signals
// handled by Panel.qml. Theme tokens come straight from the singletons.
Column {
  id: root
  spacing: Commons.Style.spacing.md

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
  property color foreground: Commons.Color.menu.text
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
    spacing: Commons.Style.spacing.sm
    Flow {
      Layout.fillWidth: true
      spacing: Commons.Style.spacing.sm
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
      color: Commons.Color.menu.text
      font.family: Commons.Style.font.family; font.pixelSize: Commons.Style.font.caption
      Accessible.name: root.copiedSwatchIndex >= 0 ? "Color copied to clipboard" : ""
    }
  }
  Text {
    visible: root.targetThemes.length > 0
    text: "Style references · " + root.pickedRefs.length + "/" + root.referenceLimit
    color: Qt.darker(root.foreground, 1.4)
    font.family: Commons.Style.font.family
    font.pixelSize: Commons.Style.font.caption
    font.bold: true
  }
  ActionButton { visible: root.targetThemes.length > 0; text: "Add custom reference…"; focusable: true; bordered: true; onClicked: root.customRefRequested() }
  Flow {
    visible: root.targetThemes.length > 0
    width: parent.width
    spacing: Commons.Style.spacing.sm
    Repeater {
      model: root.backgrounds
      Item {
        width: Commons.Style.space(88)
        height: Commons.Style.space(56)
        activeFocusOnTab: true
        Accessible.role: Accessible.CheckBox
        Accessible.name: modelData.name
        Accessible.checked: picked
        Accessible.onPressAction: root.refToggled(modelData.path)
        property bool picked: root.pickedRefs.indexOf(modelData.path) >= 0
        BorderSurface {
          anchors.fill: parent
          radius: Commons.Style.cornerRadius
          color: "transparent"
          borderSpec: Commons.Border.controlSpec(parent.activeFocus ? "focus" : parent.picked ? "selected" : "normal", root.foreground, Commons.Color.accent)
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
          width: Commons.Style.space(18)
          height: Commons.Style.space(18)
          radius: width / 2
          anchors.top: parent.top
          anchors.right: parent.right
          anchors.margins: Commons.Style.space(3)
          color: Commons.Color.accent
          Text {
            anchors.centerIn: parent
            text: "✓"
            color: Commons.Color.menu.background
            font.bold: true
            font.pixelSize: Commons.Style.font.caption
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
