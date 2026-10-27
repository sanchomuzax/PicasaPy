import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: leftDrawer
    property var hostViewer: null
    readonly property var hostEditCtl:
        (typeof editController !== "undefined") ? editController : null
    property var hostPhotoArea: null
    property var hostCropOverlay: null
    property var hostCopyCaptionConfirmLoader: null
    property var hostUndoDataLossDialogLoader: null
    property var hostMovieResetConfirmLoader: null
    property var hostKepkockaJelzes: null
    property var hostVideoLoader: null
    property alias hostEditorPanel: editorPanel
    objectName: "viewerLeftDrawer"
    visible: !leftDrawer.hostViewer.quickViewerMode
    // #411: az EditorPanel.qml implicitWidth-ével összhangban —
    // FIX 280px, nem ablakarányos (ld. az ottani kommentet)
    clip: true
    // #641: itt NINCS `Layout.minimumHeight`. A #628 azt tette ide,
    // de az visszafelé sült el: a doboz nem zsugorodott a cellára,
    // hanem TÚLNYÚLT rajta, és a panel aljához igazodó
    // Visszavonás/Újra sor kicsúszott a képernyőről. A „mindig
    // elfér" garanciát az ABLAK minimális magassága adja
    // (`Main.qml`, a `viewer.requiredHeight`-ből) — ha az mégsem
    // tartható, a doboz zsugorodik, és a fül TARTALMA veszít, nem
    // a gombsor.
    color: Theme.chromeBg

    // #4566: videónál a fülsáv helyén a videó-panel áll (a spec
    // `movietab` szakasza). A fülsáv ilyenkor el van rejtve, nem
    // csak szürkítve.
    VideoEditPanel {
        id: videoEditPanel
        objectName: "videoEditPanel"
        visible: leftDrawer.hostViewer.isCurrentVideo
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 280
        x: leftDrawer.hostViewer.editorDrawerOffset
        // a vágás állapota a modellből jön; a `revision` SZÁNDÉKOS
        // függőség, ld. a lejátszó trimStartMs kötését
        trimmed: leftDrawer.hostViewer.photosModel
            ? (leftDrawer.hostViewer.photosModel.revision,
               leftDrawer.hostViewer.photosModel.movieTrimAt(leftDrawer.hostViewer.currentIndex).start >= 0
               || leftDrawer.hostViewer.photosModel.movieTrimAt(leftDrawer.hostViewer.currentIndex).end >= 0)
            : false
        // a képkockát a LEJÁTSZÓ pozíciójából mentjük, ezért élő
        // lejátszó kell hozzá
        captureAvailable: leftDrawer.hostVideoLoader.status === Loader.Ready
        //: az eredeti (`CThumbUI::UndomovieEdits`) előbb rákérdez
        onResetTrimRequested: leftDrawer.hostMovieResetConfirmLoader.ensure().askFor(
            leftDrawer.hostViewer.currentIndex)
        onCaptureFrameRequested: {
            if (leftDrawer.hostVideoLoader.item)
                leftDrawer.hostVideoLoader.item.captureFrame()
        }
        //: `movieeditpanel/export_movie` → `LinuxNomovie`.
        onExportClipRequested: {
            if (controller && !controller.movieClipExportSupported)
                leftDrawer.hostKepkockaJelzes.mutasd(
                    qsTr("This feature is not supported for Linux"))
            else if (controller && controller.exportMovieClip !== undefined)
                controller.exportMovieClip(leftDrawer.hostViewer.currentIndex)
        }
    }

    PhotoViewerEditorPanel {
        id: editorPanel
        hostViewer: leftDrawer.hostViewer
        hostPhotoArea: leftDrawer.hostPhotoArea
        hostCropOverlay: leftDrawer.hostCropOverlay
        hostCopyCaptionConfirmLoader: leftDrawer.hostCopyCaptionConfirmLoader
        hostUndoDataLossDialogLoader: leftDrawer.hostUndoDataLossDialogLoader
    }

    // #3234: a döntés-csúszka a KÉP FÖLÖTTI sávba költözött
    // (`EditorToolBar`, `toolslider`) — az `editpanel.tre`
    // `#---Straighen Overlay---` szakasza szerint ott a helye,
    // nem a bal panel alatt. A viselkedése VÁLTOZATLAN: húzás
    // közben élő előnézet (#72), elengedéskor ír.
    // élő RGB-hisztogram + fényképezőgép-adat sor (#25): a
    // korábbi placeholder-doboz élesítve — HistogramBox.qml
    // #1323: a panel a bal fiókON BELÜL dokkolt, nem a
    // képterület fölött lebeg. Az `editpanel.tre` szerint
    // (`nerdview_container`, XConstraint 0, 0, LEFTDRAWEROFFSET,
    // 20) a bal éle a fiók bal szélétől 20 px — a
    // `LEFTDRAWEROFFSET` a fiók BE-/KICSÚSZTATÁSÁT vezérlő
    // változó (0 ↔ −279, `editpanel.tre:1413`), nem a fiók
    // szélessége; a képterület `LEFTDRAWEROFFSET + 279`-nél
    // kezdődik (`insetleft`, 1421). A 238 × 144-es doboz így a
    // 280 px-es fiók sávján belülre esik.
    HistogramBox {
        objectName: "viewerHistogramBox"
        anchors.bottom: parent.bottom
        // #1905/3: MÉRVE a tulajdonos egymás mellé tett
        // felvételén — a doboz alsó szegélye 4 px-re van a bal
        // panel aljától (Picasa 3: y=921, a panel alja y=925;
        // nálunk y=830 volt, azaz 95 px lebegés).
        //
        // A 95 az `editpanel.tre` `nerdview_container`
        // `YConstraint 1, 1, -95` sorából jött — CSAKHOGY annak
        // a szülője `root`, nem a bal fiók. A fiók aljára
        // ugyanazt a −95-öt alkalmazva nagy üres sáv marad
        // alatta. A felvétel dönt.
        anchors.bottomMargin: 4
        anchors.left: parent.left
        anchors.leftMargin: 20
        width: 238
        height: 144
        // #305: null-őr
        histogramData: leftDrawer.hostEditCtl
            ? leftDrawer.hostEditCtl.histogram : ({ r: [], g: [], b: [] })
        cameraSummary: leftDrawer.hostEditCtl ? leftDrawer.hostEditCtl.cameraSummary : ""
    }
}
