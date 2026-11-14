import QtQuick 2.15

Rectangle {
    id: root
    width: 1100
    height: 650
    color: "#0d1527"
    Image {
        anchors.fill: parent
        source: "file:///usr/share/wallpapers/Skaldr/contents/images/3840x2160.svg"
        fillMode: Image.PreserveAspectCrop
        smooth: true
        asynchronous: true
    }
}
