import QtQuick
import QtQuick.Controls

// A videó be- és kimeneti pontjai. A lejátszási pozíció külön csúszkán van.
RangeSlider {
    id: control
    objectName: "video_control_bar/trimslider"
    property int durationMs: 0
    property int startMs: -1
    property int endMs: -1
    signal trimRequested(int startMs, int endMs)

    from: 0
    to: Math.max(1, Math.max(durationMs, endMs))
    first.value: Math.max(0, startMs)
    second.value: endMs >= 0 ? endMs : to

    first.onMoved: trimRequested(
        first.value <= 0 ? -1 : Math.round(first.value), endMs)
    second.onMoved: trimRequested(
        startMs,
        durationMs > 0 && second.value >= durationMs
            ? -1 : Math.round(second.value))

    first.handle: Rectangle {
        // Egyedi fogantyúnál a stílus nem pozícionál: a helyét mi kötjük
        // az értékhez, különben mindkét fogantyú a sáv bal szélén áll.
        x: control.leftPadding + control.first.visualPosition
            * (control.availableWidth - width)
        y: control.topPadding + (control.availableHeight - height) / 2
        objectName: "videoTrimStartThumb"
        implicitWidth: 14
        implicitHeight: 12
        radius: 2
        color: "#d5d5d5"
        border.width: 1
        border.color: "#202020"
    }
    second.handle: Rectangle {
        // Egyedi fogantyúnál a stílus nem pozícionál: a helyét mi kötjük
        // az értékhez, különben mindkét fogantyú a sáv bal szélén áll.
        x: control.leftPadding + control.second.visualPosition
            * (control.availableWidth - width)
        y: control.topPadding + (control.availableHeight - height) / 2
        objectName: "videoTrimEndThumb"
        implicitWidth: 14
        implicitHeight: 12
        radius: 2
        color: "#d5d5d5"
        border.width: 1
        border.color: "#202020"
    }
}
