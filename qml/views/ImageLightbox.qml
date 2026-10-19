import QtQuick
import qs.Commons
import qs.Commons as Commons

ModalFrame {
  id: root
  property string imagePath: ""
  title: "Result preview"
  function showImage(path) { if (path) { imagePath = path; open() } }
  Image {
    anchors.fill: parent
    source: root.opened && root.imagePath ? "file://" + root.imagePath : ""
    asynchronous: true; sourceSize.width: 2048; fillMode: Image.PreserveAspectFit
    Accessible.name: "Enlarged result image"
  }
}
