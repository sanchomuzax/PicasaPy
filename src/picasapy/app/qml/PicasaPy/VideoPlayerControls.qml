import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

// A videólejátszó két módvezérlője. A kép méretét a hívó komponens kezeli;
// a teljes képernyős állapotot ez a komponens kapcsolja az őt befogadó ablakon.
Item {
    id: controls

    property bool actualSizeEnabled: false
    signal actualSizeToggled(bool enabled)

    implicitWidth: 64
    implicitHeight: 26

    property int _visibilityBeforeFullscreen: Window.Windowed
    property bool _ownsFullscreen: false

    function toggleFullscreen() {
        var hostWindow = controls.Window.window
        if (!hostWindow) return

        if (controls._ownsFullscreen
                && hostWindow.visibility === Window.FullScreen) {
            hostWindow.visibility = controls._visibilityBeforeFullscreen
            controls._ownsFullscreen = false
        } else if (hostWindow.visibility !== Window.FullScreen) {
            controls._visibilityBeforeFullscreen = hostWindow.visibility
            hostWindow.visibility = Window.FullScreen
            controls._ownsFullscreen = true
        }
    }

    Component.onDestruction: {
        var hostWindow = controls.Window.window
        if (controls._ownsFullscreen && hostWindow
                && hostWindow.visibility === Window.FullScreen) {
            hostWindow.visibility = controls._visibilityBeforeFullscreen
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 4

        PicasaButton {
            objectName: "videoActualSizeButton"
            Layout.fillHeight: true
            Layout.preferredWidth: 30
            text: "1:1"
            checkable: true
            checked: controls.actualSizeEnabled
            ToolTip.text: qsTr("Show actual movie size (don't stretch)")
            ToolTip.delay: Theme.tooltipDelay
            ToolTip.visible: hovered
            onClicked: controls.actualSizeToggled(
                           !controls.actualSizeEnabled)
        }

        PicasaButton {
            objectName: "videoFullscreenButton"
            Layout.fillHeight: true
            Layout.preferredWidth: 30
            text: "⛶"
            ToolTip.text: qsTr("Play full screen")
            ToolTip.delay: Theme.tooltipDelay
            ToolTip.visible: hovered
            onClicked: controls.toggleFullscreen()
        }
    }
}
