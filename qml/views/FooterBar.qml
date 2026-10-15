import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Ui

ColumnLayout {
  id: root
  property string primaryLabel: "Generate"
  property string footText: ""
  property string lastError: ""
  property string costText: ""
  property string themeName: ""
  property string installedTheme: ""
  property bool canPrimary: false
  property bool canSet: false
  property bool busy: false
  property bool actionBusy: false
  property bool resultAvailable: false
  signal primaryClicked()
  signal setClicked()
  signal saveClicked()
  signal clearClicked()
  signal cancelClicked()
  spacing: Style.spacing.sm
  RowLayout {
    Layout.fillWidth: true; spacing: Style.spacing.md
    LoadingPixels { visible: root.busy || root.actionBusy; running: visible }
    Text {
      Layout.fillWidth: true
      text: root.lastError || root.footText
      textFormat: Text.PlainText; wrapMode: Text.WordWrap
      color: root.lastError ? Color.urgent : Color.menu.text
      font.family: Style.font.family; font.pixelSize: Style.font.bodySmall
      Accessible.role: Accessible.StaticText
    }
  }
  RowLayout {
    Layout.fillWidth: true; spacing: Style.spacing.controlGap
    Item { Layout.fillWidth: true }
    Button {
      tooltipText: "Clear source images, selected references, result and status; keep saved files and History"
      text: "Clear"; focusable: true; bordered: true
      enabled: !root.busy && !root.actionBusy; onClicked: root.clearClicked()
    }
    Button {
      visible: root.resultAvailable; text: "Save as…"; focusable: true; bordered: true
      enabled: root.canSet; tooltipText: "Save a copy to a filename and location you choose"
      onClicked: root.saveClicked()
    }
    Button {
      visible: root.resultAvailable
      iconText: root.themeName && root.installedTheme === root.themeName ? "✓" : ""
      foreground: root.themeName && root.installedTheme === root.themeName ? Color.pick("omachroma.success", "mediumseagreen") : Color.menu.text
      opacity: enabled || root.themeName && root.installedTheme === root.themeName ? 1 : 0.4
      text: root.themeName ? (root.installedTheme === root.themeName ? "Saved to " : "Save to ") + root.themeName : "Choose a theme"
      focusable: true; bordered: true
      enabled: root.canSet && root.themeName !== "" && root.installedTheme !== root.themeName
      tooltipText: "Save into the selected theme's wallpaper folder"
      onClicked: root.setClicked()
    }
  }
  RowLayout {
    Layout.fillWidth: true; spacing: Style.spacing.controlGap
    Text {
      Layout.fillWidth: true; text: root.costText; wrapMode: Text.WordWrap
      color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.caption
    }
    Button {
      visible: root.busy; text: "Stop"; focusable: true; bordered: true
      onClicked: root.cancelClicked()
    }
    Button {
      visible: !root.busy; text: root.primaryLabel; focusable: true; bordered: true; selected: root.canPrimary
      enabled: root.canPrimary; opacity: enabled ? 1 : 0.4
      tooltipText: "Sends images to your provider · Alt+G"
      onClicked: root.primaryClicked()
    }
  }
}
