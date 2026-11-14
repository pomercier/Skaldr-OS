import QtQuick 2.15

Rectangle {
    // Render the same 880x340 vector banner in the QML slideshow and
    // the static Calamares productWelcome fallback. Never crop a 4K wallpaper.
    id: root
    width: 880
    height: 340
    color: "#0b162a"

    Image {
        anchors.fill: parent
        source: "file:///usr/share/calamares/branding/skaldr/welcome.svg"
        sourceSize.width: 880
        sourceSize.height: 340
        fillMode: Image.PreserveAspectFit
        smooth: true
        cache: true
    }
}
