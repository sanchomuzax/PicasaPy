import QtQuick

// Vágó-overlay a kép fölé: húzható/átméretezhető kijelölés 8 fogantyúval,
// a kijelölésen kívüli terület sötétítve. UX-alapelv 1 (docs/specs/
// ux-principles.md): Enter elfogadja a vágást ÉS a hívó lépteti a
// következő képre — a sorozat-vágás így megszakítás nélkül folyik; Esc
// szerkesztés nélkül zár.
Item {
    id: overlay
    objectName: "cropOverlay"

    // relatív koordináták (0..1) a befoglaló kép dobozához képest
    property rect cropRect: Qt.rect(0.1, 0.1, 0.8, 0.8)
    // 0 = szabad arány; egyébként szélesség/magasság rögzített hányados
    property real aspectRatio: 0
    readonly property int handleSize: 10
    readonly property int minSelectionPx: 24

    signal accepted(rect r)
    signal cancelled()

    focus: true
    Keys.onReturnPressed: overlay.acceptCrop()
    Keys.onEnterPressed: overlay.acceptCrop()
    Keys.onEscapePressed: overlay.cancelCrop()

    function acceptCrop() { overlay.accepted(overlay.cropRect) }
    function cancelCrop() { overlay.cancelled() }
    function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)) }

    // pixel-koordináták a belső elrendezéshez (a cropRect relatív értékeiből)
    readonly property real selX: overlay.width > 0 ? cropRect.x * overlay.width : 0
    readonly property real selY: overlay.height > 0 ? cropRect.y * overlay.height : 0
    readonly property real selW: overlay.width > 0 ? cropRect.width * overlay.width : 0
    readonly property real selH: overlay.height > 0 ? cropRect.height * overlay.height : 0

    // a kijelölésen kívüli terület sötétítése — négy csík a kijelölés körül
    Rectangle {
        color: "#000000a0"
        x: 0; y: 0
        width: overlay.width; height: overlay.selY
    }
    Rectangle {
        color: "#000000a0"
        x: 0; y: overlay.selY + overlay.selH
        width: overlay.width
        height: Math.max(0, overlay.height - overlay.selY - overlay.selH)
    }
    Rectangle {
        color: "#000000a0"
        x: 0; y: overlay.selY
        width: overlay.selX; height: overlay.selH
    }
    Rectangle {
        color: "#000000a0"
        x: overlay.selX + overlay.selW; y: overlay.selY
        width: Math.max(0, overlay.width - overlay.selX - overlay.selW)
        height: overlay.selH
    }

    // maga a kijelölés — húzáskor az egész téglalapot mozgatja
    Rectangle {
        id: selection
        objectName: "cropSelection"
        x: overlay.selX; y: overlay.selY
        width: overlay.selW; height: overlay.selH
        color: "transparent"
        border.width: 2
        border.color: "#ffffff"

        MouseArea {
            id: moveArea
            anchors.fill: parent
            drag.target: selection
            drag.axis: Drag.XAndYAxis
            drag.minimumX: 0
            drag.minimumY: 0
            drag.maximumX: Math.max(0, overlay.width - selection.width)
            drag.maximumY: Math.max(0, overlay.height - selection.height)
            onPositionChanged: if (drag.active)
                overlay.commitFromPixels(selection.x, selection.y,
                                          selection.width, selection.height)
        }
    }

    // pixelben számolt kijelölésből visszaírja a relatív cropRect-et
    function commitFromPixels(px, py, pw, ph) {
        if (overlay.width <= 0 || overlay.height <= 0) return
        overlay.cropRect = Qt.rect(px / overlay.width, py / overlay.height,
                                    pw / overlay.width, ph / overlay.height)
    }

    // 8 átméretező fogantyú a kijelölés sarkain/élein
    Repeater {
        model: ["nw", "n", "ne", "w", "e", "sw", "s", "se"]
        delegate: Rectangle {
            id: handle
            required property string modelData
            objectName: "cropHandle_" + modelData
            width: overlay.handleSize; height: overlay.handleSize
            radius: overlay.handleSize / 2
            color: "#ffffff"
            border.width: 1; border.color: "#333333"
            x: overlay.handlePixelX(modelData) - width / 2
            y: overlay.handlePixelY(modelData) - height / 2

            MouseArea {
                anchors.fill: parent
                drag.target: handle
                onPositionChanged: if (drag.active)
                    overlay.resizeFromHandle(handle.modelData,
                                              handle.x + handle.width / 2,
                                              handle.y + handle.height / 2)
            }
        }
    }

    function handlePixelX(pos) {
        if (pos.indexOf("w") >= 0) return overlay.selX
        if (pos.indexOf("e") >= 0) return overlay.selX + overlay.selW
        return overlay.selX + overlay.selW / 2
    }
    function handlePixelY(pos) {
        if (pos.indexOf("n") >= 0) return overlay.selY
        if (pos.indexOf("s") >= 0) return overlay.selY + overlay.selH
        return overlay.selY + overlay.selH / 2
    }

    // egy fogantyú mozgatásából új kijelölés-téglalapot számol; rögzített
    // aspectRatio esetén a magasságot a szélességből származtatja
    function resizeFromHandle(pos, mouseX, mouseY) {
        var left = overlay.selX, top = overlay.selY
        var right = overlay.selX + overlay.selW, bottom = overlay.selY + overlay.selH

        if (pos.indexOf("w") >= 0)
            left = overlay.clamp(mouseX, 0, right - overlay.minSelectionPx)
        if (pos.indexOf("e") >= 0)
            right = overlay.clamp(mouseX, left + overlay.minSelectionPx, overlay.width)
        if (pos.indexOf("n") >= 0)
            top = overlay.clamp(mouseY, 0, bottom - overlay.minSelectionPx)
        if (pos.indexOf("s") >= 0)
            bottom = overlay.clamp(mouseY, top + overlay.minSelectionPx, overlay.height)

        var w = right - left
        var h = bottom - top
        if (overlay.aspectRatio > 0) {
            h = w / overlay.aspectRatio
            bottom = top + h
        }
        overlay.commitFromPixels(left, top, w, h)
    }
}
