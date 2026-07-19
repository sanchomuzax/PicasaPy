import QtQuick

// Vágó-overlay a kép fölé (#51, Picasa-hű): NINCS előre kijelölt terület —
// a kijelölést a felhasználó egérrel húzva hozza létre, utána mozgatható
// és 8 fogantyúval átméretezhető; a kijelölésen kívüli rész sötétített.
// UX-alapelv 1 (docs/specs/ux-principles.md): Enter elfogadja a vágást ÉS
// a hívó lépteti a következő képre (sorozat-vágás); Esc szerkesztés nélkül
// zár. Az Előnézet tartása alatt a külső terület a néző hátterével fedett.
Item {
    id: overlay
    objectName: "cropOverlay"

    // relatív koordináták (0..1) a befoglaló kép dobozához képest
    property rect cropRect: Qt.rect(0, 0, 0, 0)
    property bool hasSelection: false
    // 0 = szabad arány; egyébként szélesség/magasság rögzített hányados
    property real aspectRatio: 0
    // Előnézet-gomb tartása: a külső terület teljesen takart
    property bool previewHold: false
    readonly property int handleSize: 10
    readonly property int minSelectionPx: 24

    signal accepted(rect r)
    signal cancelled()

    focus: true
    Keys.onReturnPressed: overlay.acceptCrop()
    Keys.onEnterPressed: overlay.acceptCrop()
    Keys.onEscapePressed: overlay.cancelCrop()

    function acceptCrop() {
        if (overlay.hasSelection)
            overlay.accepted(overlay.cropRect)
    }
    function cancelCrop() { overlay.cancelled() }
    function resetSelection() {
        overlay.hasSelection = false
        overlay.cropRect = Qt.rect(0, 0, 0, 0)
    }

    // meglévő (mentett) kijelölés betöltése a Vágás eszköz megnyitásakor
    // (#71) — `selection` egy {x,y,width,height} objektum vagy null/undefined
    function loadSelection(selection) {
        if (selection) {
            overlay.cropRect = Qt.rect(selection.x, selection.y,
                                        selection.width, selection.height)
            overlay.hasSelection = true
        } else {
            overlay.resetSelection()
        }
    }
    function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)) }

    // A meglévő kijelölés átformálása új arányra (#59): a középpont és a
    // terület megmarad, az oldalarány az új értéket veszi fel.
    function applyAspect(ratio) {
        if (!overlay.hasSelection || ratio <= 0) return
        var cx = overlay.selX + overlay.selW / 2
        var cy = overlay.selY + overlay.selH / 2
        var area = Math.max(overlay.selW * overlay.selH,
                            overlay.minSelectionPx * overlay.minSelectionPx)
        var w = Math.sqrt(area * ratio)
        var h = w / ratio
        if (w > overlay.width) { w = overlay.width; h = w / ratio }
        if (h > overlay.height) { h = overlay.height; w = h * ratio }
        var x = overlay.clamp(cx - w / 2, 0, overlay.width - w)
        var y = overlay.clamp(cy - h / 2, 0, overlay.height - h)
        overlay.commitFromPixels(x, y, w, h)
    }

    // Forgatás kézi (szabad) aránynál: a kijelölés fekvő↔álló váltása.
    function swapSelectionOrientation() {
        if (!overlay.hasSelection || overlay.selW <= 0) return
        overlay.applyAspect(overlay.selH / overlay.selW)
    }

    // Gyorsvágás (Picasa három bélyegképe): bal-felső / fekvő / álló.
    // Rögzített aránynál azt tartja; szabad aránynál 4:3-at (ill. 3:4-et).
    function selectPreset(kind) {
        var boxAspect = overlay.width / Math.max(1, overlay.height)
        var ratio = overlay.aspectRatio
        if (kind === "landscape")
            ratio = (ratio > 0 && ratio >= 1) ? ratio
                  : (ratio > 0 ? 1 / ratio : 4 / 3)
        else if (kind === "portrait")
            ratio = (ratio > 0 && ratio < 1) ? ratio
                  : (ratio > 0 ? 1 / ratio : 3 / 4)
        else if (ratio <= 0)
            ratio = boxAspect   // bal-felső, szabad arány: a teljes kép

        // a legnagyobb, arányos téglalap a dobozban (relatív egységben)
        var w, h
        if (ratio >= boxAspect) { w = 1; h = boxAspect / ratio }
        else { h = 1; w = ratio / boxAspect }
        // Picasa: a gyorsvágás kicsit beljebb kezd, hogy látszódjon a keret
        w *= 0.85; h *= 0.85
        var x = kind === "topleft" ? 0 : (1 - w) / 2
        var y = kind === "topleft" ? 0 : (1 - h) / 2
        overlay.cropRect = Qt.rect(x, y, w, h)
        overlay.hasSelection = true
    }

    // pixel-koordináták a belső elrendezéshez (a cropRect relatív értékeiből)
    readonly property real selX: overlay.width > 0 ? cropRect.x * overlay.width : 0
    readonly property real selY: overlay.height > 0 ? cropRect.y * overlay.height : 0
    readonly property real selW: overlay.width > 0 ? cropRect.width * overlay.width : 0
    readonly property real selH: overlay.height > 0 ? cropRect.height * overlay.height : 0

    // -- kijelölés létrehozása húzással (Picasa: nincs elő-kijelölés) -----
    MouseArea {
        id: createArea
        anchors.fill: parent
        property real startX: 0
        property real startY: 0
        property bool creating: false
        onPressed: function(event) {
            startX = event.x; startY = event.y
            creating = true
        }
        onPositionChanged: function(event) {
            if (!creating) return
            overlay.updateCreation(startX, startY, event.x, event.y)
        }
        onReleased: function(event) {
            if (!creating) return
            creating = false
            // túl kicsi (kattintásnyi) kijelölés: nem jön létre
            if (overlay.selW < overlay.minSelectionPx
                || overlay.selH < overlay.minSelectionPx)
                overlay.resetSelection()
        }
    }

    // húzás közbeni téglalap-számítás, rögzített aránnyal is
    function updateCreation(x1, y1, x2, y2) {
        var left = Math.min(x1, x2), top = Math.min(y1, y2)
        var w = Math.abs(x2 - x1), h = Math.abs(y2 - y1)
        if (overlay.aspectRatio > 0) {
            h = w / overlay.aspectRatio
            if (y2 < y1) top = y1 - h
        }
        left = overlay.clamp(left, 0, overlay.width)
        top = overlay.clamp(top, 0, overlay.height)
        w = Math.min(w, overlay.width - left)
        h = Math.min(h, overlay.height - top)
        if (overlay.aspectRatio > 0) {
            // a levágott oldal után az arányt újra érvényesítjük
            w = Math.min(w, h * overlay.aspectRatio)
            h = w / overlay.aspectRatio
        }
        overlay.hasSelection = true
        overlay.commitFromPixels(left, top, w, h)
    }

    // a kijelölésen kívüli terület: normál módban sötétítés, Előnézet
    // tartásakor a néző hátterével teljesen fedett (vágás-előnézet)
    readonly property color dimColor: overlay.previewHold ? "#808080"
                                                          : "#000000a0"
    Rectangle {
        visible: overlay.hasSelection
        color: overlay.dimColor
        x: 0; y: 0
        width: overlay.width; height: overlay.selY
    }
    Rectangle {
        visible: overlay.hasSelection
        color: overlay.dimColor
        x: 0; y: overlay.selY + overlay.selH
        width: overlay.width
        height: Math.max(0, overlay.height - overlay.selY - overlay.selH)
    }
    Rectangle {
        visible: overlay.hasSelection
        color: overlay.dimColor
        x: 0; y: overlay.selY
        width: overlay.selX; height: overlay.selH
    }
    Rectangle {
        visible: overlay.hasSelection
        color: overlay.dimColor
        x: overlay.selX + overlay.selW; y: overlay.selY
        width: Math.max(0, overlay.width - overlay.selX - overlay.selW)
        height: overlay.selH
    }

    // maga a kijelölés — húzáskor az egész téglalapot mozgatja
    Rectangle {
        id: selection
        objectName: "cropSelection"
        visible: overlay.hasSelection && !overlay.previewHold
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
            visible: overlay.hasSelection && !overlay.previewHold
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
