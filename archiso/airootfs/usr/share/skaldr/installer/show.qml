import QtQuick 2.15

Rectangle {
    // The Calamares slideshow viewport is about 880x340 at CI resolution.
    // The previous 1100x650 image was clipped, showing oversized abstract
    // wallpaper fragments instead of a recognizable Skaldr illustration.
    id: root
    width: 880
    height: 340
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#101b31" }
        GradientStop { position: 1.0; color: "#172743" }
    }

    Image {
        id: skaldrLogo
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -8
        width: 228
        height: 228
        source: "file:///usr/share/pixmaps/skaldr-logo.svg"
        sourceSize.width: 512
        sourceSize.height: 512
        fillMode: Image.PreserveAspectFit
        smooth: true
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 18
        text: "PERFORMANCE BY INTENTION"
        font.family: "DejaVu Sans"
        font.pixelSize: 15
        font.letterSpacing: 2
        color: "#ccd9ed"
    }
}
