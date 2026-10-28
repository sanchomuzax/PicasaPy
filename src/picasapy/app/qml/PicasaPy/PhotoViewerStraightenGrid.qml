import QtQuick
import QtQuick.Window

//: #3924, „⛳ A Kiegyenesítés négyzethálója”:
//: a csempézett rács a kép fölött áll, a kép forgása alatt.
//: A becsomagolt 44×44-es mintát az Image.Tile
//: változatlan logikai képpontméretben ismétli a képre.
Item {
    required property var photoArea
    required property var editorToolBar
    id: straightenGridOverlay
    objectName: "straightenGridOverlay"
    // A közös, forgatatlan szülőben a Qt clip mind a négy
    // egész képernyőszélt azonosan raszterezi; a rács
    // így a 90°-os képeknél sem veszít el perempixelt.
    parent: photoArea
    z: 1
    scale: 1
    rotation: 0
    clip: true
    visible: photoArea.hostEditorPanel.tiltActive
             && photoArea.hostEditorPanel.activeTab === 0
             && !photoArea.hostViewer.isCurrentVideo

    property int racsKezdoX: 0
    property int racsKezdoY: 0
    property int vagasJelenetX: 0
    property int vagasJelenetY: 0
    property real gombparBal: 0
    property real gombparFelso: 0
    property real gombparJobb: 0
    property real gombparAlso: 0
    property bool gombparMaszkAktiv: false
    property bool elsoKirajzolasUtaniMaszkFrissult: false

    function frissitGombparMaszk() {
        if (!editorToolBar.visible)
        {
            gombparMaszkAktiv = false
            return
        }

        var gombok = [
            editorToolBar.cancelButtonItem,
            editorToolBar.applyButtonItem,
        ]
        var xek = []
        var yek = []
        for (var i = 0; i < gombok.length; ++i) {
            var gomb = gombok[i]
            var sarkok = [
                gomb.mapToItem(straightenGridOverlay, 0, 0),
                gomb.mapToItem(straightenGridOverlay,
                               gomb.width, 0),
                gomb.mapToItem(straightenGridOverlay,
                               0, gomb.height),
                gomb.mapToItem(straightenGridOverlay,
                               gomb.width, gomb.height),
            ]
            for (var j = 0; j < sarkok.length; ++j) {
                xek.push(sarkok[j].x)
                yek.push(sarkok[j].y)
            }
        }

        var bal = Math.min.apply(null, xek)
        var fent = Math.min.apply(null, yek)
        var jobb = Math.max.apply(null, xek)
        var lent = Math.max.apply(null, yek)
        gombparBal = Math.max(0, Math.min(width, bal))
        gombparFelso = Math.max(0, Math.min(height, fent))
        gombparJobb = Math.max(0, Math.min(width, jobb))
        gombparAlso = Math.max(0, Math.min(height, lent))
        gombparMaszkAktiv = gombparJobb > gombparBal
            && gombparAlso > gombparFelso
    }

    function racsSzeletX(szeletX) {
        var jelenetX = vagasJelenetX + szeletX
        return racsKezdoX
            + Math.floor((jelenetX - racsKezdoX) / 44) * 44
            - jelenetX
    }

    function racsSzeletY(szeletY) {
        var jelenetY = vagasJelenetY + szeletY
        return racsKezdoY
            + Math.floor((jelenetY - racsKezdoY) / 44) * 44
            - jelenetY
    }

    function frissitGeometria() {
        var kep = photoArea.fokuszKep
        if (kep.paintedWidth <= 0 || kep.paintedHeight <= 0)
            return

        var kozep = kep.mapToItem(
            null, kep.width / 2, kep.height / 2)
        var nagyitas = Math.abs(kep.scale)
        var fordult = kep.iniSteps % 2 !== 0
        var kepSzel = (fordult
            ? kep.paintedHeight : kep.paintedWidth) * nagyitas
        var kepMag = (fordult
            ? kep.paintedWidth : kep.paintedHeight) * nagyitas
        var bal = Math.floor(kozep.x - kepSzel / 2)
        var jobb = Math.floor(kozep.x + kepSzel / 2)
        var fent = Math.floor(kozep.y - kepMag / 2)
        var lent = Math.floor(kozep.y + kepMag / 2)
        var helyiKezdo = parent.mapFromItem(
            null, bal, fent)

        width = jobb - bal
        height = lent - fent
        x = helyiKezdo.x
        y = helyiKezdo.y
        vagasJelenetX = bal
        vagasJelenetY = fent

        var teruletKozep = photoArea.mapToItem(
            null, photoArea.width / 2, photoArea.height / 2)
        racsKezdoX = Math.trunc(teruletKozep.x - 249)
        racsKezdoY = Math.trunc(teruletKozep.y - 153)
        Qt.callLater(frissitGombparMaszk)
    }

    onVisibleChanged: {
        if (visible) {
            elsoKirajzolasUtaniMaszkFrissult = false
            Qt.callLater(frissitGeometria)
        }
    }
    Component.onCompleted: Qt.callLater(frissitGeometria)

    //: Négy, egymást nem fedő csempézett rész alkotja a
    //: rácsot. A középső bal/jobb résszel a teljes gombpár
    //: téglalapja marad üres; a csúszkasáv fölött továbbra
    //: is látszik a rács. A QtQuick.Effects nem fut minden
    //: célgépen, ezért a kivágás egyszerű QtQuick-clip.
    // Felső sáv: a gombpár fölötti teljes képterület.
    Item {
        x: 0
        y: 0
        width: straightenGridOverlay.width
        height: straightenGridOverlay.gombparMaszkAktiv
                ? straightenGridOverlay.gombparFelso
                : straightenGridOverlay.height
        clip: true
        visible: width > 0 && height > 0
        Image {
            objectName: "straightenGridImage"
            x: straightenGridOverlay.racsSzeletX(parent.x)
            y: straightenGridOverlay.racsSzeletY(parent.y)
            width: parent.width + 88
            height: parent.height + 88
            source: "../../assets/tools/straighten_grid.png"
            sourceSize: Qt.size(44, 44)
            fillMode: Image.Tile
            horizontalAlignment: Image.AlignLeft
            verticalAlignment: Image.AlignTop
            smooth: false
            cache: false
            asynchronous: false
        }
    }
    // A gombok bal oldalán megmarad a háló, a résen nem.
    Item {
        x: 0
        y: straightenGridOverlay.gombparFelso
        width: straightenGridOverlay.gombparBal
        height: straightenGridOverlay.gombparAlso
                - straightenGridOverlay.gombparFelso
        clip: true
        visible: straightenGridOverlay.gombparMaszkAktiv
                 && width > 0 && height > 0
        Image {
            x: straightenGridOverlay.racsSzeletX(parent.x)
            y: straightenGridOverlay.racsSzeletY(parent.y)
            width: parent.width + 88
            height: parent.height + 88
            source: "../../assets/tools/straighten_grid.png"
            sourceSize: Qt.size(44, 44)
            fillMode: Image.Tile
            horizontalAlignment: Image.AlignLeft
            verticalAlignment: Image.AlignTop
            smooth: false
            cache: false
            asynchronous: false
        }
    }
    // A gombok jobb oldalán megmarad a háló.
    Item {
        x: straightenGridOverlay.gombparJobb
        y: straightenGridOverlay.gombparFelso
        width: straightenGridOverlay.width
                - straightenGridOverlay.gombparJobb
        height: straightenGridOverlay.gombparAlso
                - straightenGridOverlay.gombparFelso
        clip: true
        visible: straightenGridOverlay.gombparMaszkAktiv
                 && width > 0 && height > 0
        Image {
            x: straightenGridOverlay.racsSzeletX(parent.x)
            y: straightenGridOverlay.racsSzeletY(parent.y)
            width: parent.width + 88
            height: parent.height + 88
            source: "../../assets/tools/straighten_grid.png"
            sourceSize: Qt.size(44, 44)
            fillMode: Image.Tile
            horizontalAlignment: Image.AlignLeft
            verticalAlignment: Image.AlignTop
            smooth: false
            cache: false
            asynchronous: false
        }
    }
    // Alsó sáv: a gombpár alatti teljes képterület.
    Item {
        x: 0
        y: straightenGridOverlay.gombparMaszkAktiv
           ? straightenGridOverlay.gombparAlso : 0
        width: straightenGridOverlay.width
        height: straightenGridOverlay.gombparMaszkAktiv
                ? straightenGridOverlay.height
                  - straightenGridOverlay.gombparAlso
                : 0
        clip: true
        visible: width > 0 && height > 0
        Image {
            x: straightenGridOverlay.racsSzeletX(parent.x)
            y: straightenGridOverlay.racsSzeletY(parent.y)
            width: parent.width + 88
            height: parent.height + 88
            source: "../../assets/tools/straighten_grid.png"
            sourceSize: Qt.size(44, 44)
            fillMode: Image.Tile
            horizontalAlignment: Image.AlignLeft
            verticalAlignment: Image.AlignTop
            smooth: false
            cache: false
            asynchronous: false
        }
    }
    Connections {
        target: photoArea.fokuszKep
        function frissit() {
            Qt.callLater(straightenGridOverlay.frissitGeometria)
        }
        function onXChanged() { frissit() }
        function onYChanged() { frissit() }
        function onWidthChanged() { frissit() }
        function onHeightChanged() { frissit() }
        function onPaintedWidthChanged() { frissit() }
        function onPaintedHeightChanged() { frissit() }
        function onScaleChanged() { frissit() }
        function onRotationChanged() { frissit() }
        function onIniStepsChanged() { frissit() }
    }
    Connections {
        target: photoArea
        function frissit() {
            Qt.callLater(straightenGridOverlay.frissitGeometria)
        }
        function onXChanged() { frissit() }
        function onYChanged() { frissit() }
        function onWidthChanged() { frissit() }
        function onHeightChanged() { frissit() }
    }
    Connections {
        target: photoArea.parent
        function frissit() {
            Qt.callLater(straightenGridOverlay.frissitGeometria)
        }
        function onXChanged() { frissit() }
        function onYChanged() { frissit() }
        function onWidthChanged() { frissit() }
        function onHeightChanged() { frissit() }
    }
    Connections {
        target: photoArea.hostViewer
        function frissit() {
            Qt.callLater(straightenGridOverlay.frissitGeometria)
        }
        function onXChanged() { frissit() }
        function onYChanged() { frissit() }
        function onWidthChanged() { frissit() }
        function onHeightChanged() { frissit() }
    }
    Connections {
        target: editorToolBar
        function frissit() {
            Qt.callLater(
                straightenGridOverlay.frissitGombparMaszk)
        }
        function onXChanged() { frissit() }
        function onYChanged() { frissit() }
        function onWidthChanged() { frissit() }
        function onHeightChanged() { frissit() }
        function onScaleChanged() { frissit() }
        function onRotationChanged() { frissit() }
        function onVisibleChanged() { frissit() }
    }
    // A Row gyermekei az első megnyitás elrendezési
    // körében kapják meg a végleges x/y-t. Az első
    // animációs/layout kör után olvassuk ki a gombpár
    // tényleges helyét, így a háló első kirajzolása sem
    // régi koordinátával indul.
    Connections {
        target: straightenGridOverlay.Window.window
        function onAfterAnimating() {
            if (straightenGridOverlay.visible
                    && editorToolBar.visible
                    && !straightenGridOverlay
                         .elsoKirajzolasUtaniMaszkFrissult) {
                straightenGridOverlay
                    .elsoKirajzolasUtaniMaszkFrissult = true
                straightenGridOverlay.frissitGombparMaszk()
            }
        }
    }
    Connections {
        target: editorToolBar.applyButtonItem
        function frissit() {
            Qt.callLater(
                straightenGridOverlay.frissitGombparMaszk)
        }
        function onXChanged() { frissit() }
        function onYChanged() { frissit() }
        function onWidthChanged() { frissit() }
        function onHeightChanged() { frissit() }
    }
    Connections {
        target: editorToolBar.cancelButtonItem
        function frissit() {
            Qt.callLater(
                straightenGridOverlay.frissitGombparMaszk)
        }
        function onXChanged() { frissit() }
        function onYChanged() { frissit() }
        function onWidthChanged() { frissit() }
        function onHeightChanged() { frissit() }
    }
}
