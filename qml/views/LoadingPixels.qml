import QtQuick
import qs.Commons
import qs.Commons as Commons

Item {
  id: root
  property bool running: false
  property int frame: 0
  readonly property var positions: [0, 1, 2, 5, 8, 7, 6, 3]
  implicitWidth: Commons.Style.space(24)
  implicitHeight: implicitWidth
  Accessible.name: "Working"
  Accessible.role: Accessible.Indicator
  Repeater {
    model: 8
    Rectangle {
      required property int index
      width: Commons.Style.space(5); height: width
      x: (root.positions[index] % 3) * Commons.Style.space(8)
      y: Math.floor(root.positions[index] / 3) * Commons.Style.space(8)
      color: Commons.Color.accent
      opacity: ((index - root.frame + 8) % 8) < 3 ? 1 : 0.18
    }
  }
  Timer { interval: 110; repeat: true; running: root.running && root.visible; onTriggered: root.frame = (root.frame + 1) % 8 }
}
