import QtQuick
import QtQuick.Layouts
import qs.Commons

Column {
  spacing: Style.spacing.md
  Repeater {
    model: [
      ["Tab / Shift+Tab", "Move between controls"], ["Enter / Space", "Activate a focused button or reference"],
      ["Arrow keys", "Choose dropdown options or History entries"], ["Escape", "Close dialog, go back, then close app"],
      ["Alt+Left", "Back"], ["Ctrl+,", "Settings"], ["Ctrl+H", "History"],
      ["Ctrl+1 / Ctrl+2", "Generate / Upscale"], ["Ctrl+Tab / Ctrl+Shift+Tab", "Next / previous Settings tab"],
      ["Ctrl+O", "Choose source or upscale images"], ["Ctrl+Shift+O", "Add a style reference"],
      ["Alt+G", "Generate or upscale from the workspace"], ["Ctrl+S", "Save result as"],
      ["Ctrl+Delete", "Clear selection"], ["Ctrl+.", "Stop local work"]
    ]
    RowLayout {
      width: parent.width; spacing: Style.spacing.md
      Text { Layout.preferredWidth: Style.space(230); textFormat: Text.PlainText; text: modelData[0]; color: Color.menu.text; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall }
      Text { Layout.fillWidth: true; wrapMode: Text.WordWrap; textFormat: Text.PlainText; text: modelData[1]; color: Color.muted; font.family: Style.font.family; font.pixelSize: Style.font.bodySmall }
    }
  }
}
