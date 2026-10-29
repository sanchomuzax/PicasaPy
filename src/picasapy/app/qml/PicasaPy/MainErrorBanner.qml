import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A főablak hibasávja és az azt frissítő vezérlőjelzések (#6136).
// A főablak a szükséges vezérlő-, párbeszéd- és időzítőobjektumokat adja át.
// #459: globális, látható hibasáv. AUDIT-lelet: a `syncFailed`
// (photoOpFailed IDE fut be, ld. photo_ops_controller.py
// `_on_photo_write_failed`), `albumWriteFailed`, `geoWriteFailed` és
// `faceWriteFailed` jelzések korábban SEHOVA nem voltak bekötve a
// QML-oldalon — a felhasználó néma bukást látott, a hiba csak a
// naplóba (`_log.exception`/hallgatólagos emit) került. Ez az
// egyetlen, közös felület mind a négy csatornának.
Rectangle {
    id: errorBanner
    required property var hostController
    required property var hostTestLogDialog
    required property var hostBrokenPhotoDialog
    required property var hostBrokenPhotoBatchTimer
    property alias messageText: errorBannerText
    objectName: "errorBanner"
    z: 1000
    anchors.top: parent.top
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.topMargin: 8
    radius: 4
    // #459/5: az „offline mappa" NEM hiba, hanem tájékoztatás — ugyanaz
    // a sáv, de borostyán tónussal, hogy ne keveredjen az írás- és
    // szinkron-hibákkal.
    property bool notice: false
    // #1500: épp a színkeresés feltöltéséről szól-e a sáv (csak ekkor
    // frissítik a haladásjelzések a szövegét)
    property bool colorNoticeActive: false
    color: errorBanner.notice ? "#b7791f" : "#c0392b"
    visible: errorBannerText.text.length > 0
    implicitWidth: errorBannerRow.implicitWidth + 16
    implicitHeight: errorBannerRow.implicitHeight + 12

    RowLayout {
        id: errorBannerRow
        anchors.centerIn: parent
        spacing: 12
        Text {
            id: errorBannerText
            objectName: "errorBannerText"
            text: ""
            color: Theme.infoBarText
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            Layout.maximumWidth: 480
        }
        // #1500/#1476: a színkeresés előkészítése akár egy órányi
        // processzoridő — MUSZÁJ tudni leállítani. A gomb csak a
        // színkeresés tájékoztatóján jelenik meg; a többi üzenetnek
        // nincs mit leállítania.
        PicasaButton {
            objectName: "errorBannerStopButton"
            visible: errorBanner.colorNoticeActive
            text: qsTr("Stop")
            onClicked: {
                errorBanner.hostController.cancelColorIndex()
                errorBanner.colorNoticeActive = false
                errorBannerText.text = ""
            }
        }
        PicasaButton {
            objectName: "errorBannerCloseButton"
            text: qsTr("Close")
            onClicked: errorBannerText.text = ""
        }
    }

    Timer {
        interval: 8000
        running: errorBannerText.text.length > 0
        onTriggered: errorBannerText.text = ""
    }

    Connections {
        target: errorBanner.hostController
        function onSyncFailed(message) {
            errorBanner.notice = false
            errorBannerText.text = message
        }
        function onAlbumWriteFailed(message) {
            errorBanner.notice = false
            errorBannerText.text = message
        }
        function onGeoWriteFailed(message) {
            errorBanner.notice = false
            errorBannerText.text = message
        }
        // #1500: a színkeresés (`color:`/`szín:`) gyorsítótára még hiányos.
        // TÁJÉKOZTATÁS (borostyán), nem hiba: az üres találati lista
        // ilyenkor nem azt jelenti, hogy nincs ilyen színű kép, hanem hogy
        // még nem számoltuk ki. A szöveget a vezérlő adja (számok vannak
        // benne), a sáv csak megjeleníti.
        function onColorIndexIncomplete(done, total) {
            errorBanner.notice = true
            errorBanner.colorNoticeActive = true
            errorBannerText.text = errorBanner.hostController.colorIndexNoticeText(done, total)
        }
        // A sáv számai ÉLŐBEN követik a háttérmunkát, amíg látszik. A
        // `text.length > 0` őr azért kell, mert a sávot a saját időzítője
        // (és a Bezárás gomb) kiüríti — egy későbbi haladásjelzés nem
        // támaszthatja fel a felhasználó által eltüntetett üzenetet.
        function onColorIndexProgress(done, total) {
            if (errorBanner.colorNoticeActive && errorBannerText.text.length > 0)
                errorBannerText.text = errorBanner.hostController.colorIndexNoticeText(done, total)
        }
        function onColorIndexFinished(done, total) {
            errorBanner.colorNoticeActive = false
        }
        // #459/5: nem elérhető mappa — tájékoztató üzenet néma bukás helyett
        // #1654: a tesztüzem visszajelzései. TÁJÉKOZTATÁS (borostyán),
        // nem hiba: a bekapcsolás („a naplózás a következő indításnál
        // kezdődik"), a napló átadása és a mentés eredménye jár erre.
        function onTesztuzemUzenet(uzenet) {
            errorBanner.notice = true
            errorBannerText.text = uzenet
        }
        // #2553: a napló átadása MINDIG a felhasználó választásával megy.
        // A vezérlő adja a kiinduló mappát és a javasolt fájlnevet.
        function onTesztuzemMentesKert(uzenet, mappaUrl, javasoltNev) {
            errorBanner.notice = true
            errorBannerText.text = uzenet
            hostTestLogDialog.nyisdMeg(mappaUrl, javasoltNev)
        }
        function onFolderUnavailable(path) {
            errorBanner.notice = true
            errorBannerText.text = qsTr("This folder is currently unavailable (for example a disconnected drive or network share). Its photos stay in the database and thumbnails come from the cache, but the original files cannot be opened or edited right now.")
        }
        // #4597: a mappa rejtése/megjelenítése/áthelyezése nem ment át
        function onFolderHideFailed(path, reason) {
            // az ini-írás kudarca nem hiba, hanem tájékoztatás — kivéve, ha a
            // megjelenítés maradt el és a mappa rejtett maradt
            errorBanner.notice = reason !== "write-failed-unhide"
            if (reason === "offline-unhide") {
                //: #4597: elérhetetlen (offline) mappa megjelenítése nem engedett
                errorBannerText.text = qsTr("The folder cannot be shown again while it is unavailable (for example a disconnected drive). It stays hidden.")
            } else if (reason === "write-failed-hide") {
                //: #4597: a mappa rejtve van, de a .picasa.ini nem írható
                errorBannerText.text = qsTr("The folder is hidden, but it could not be marked for Picasa (the .picasa.ini file cannot be written).")
            } else if (reason === "hidden-move") {
                //: #4597: rejtett mappa gyűjteménybe mozgatása nem engedett
                errorBannerText.text = qsTr("A hidden folder cannot be moved into a collection. Unhide it first.")
            } else {
                //: #4597: a megjelenítés ini-írása elbukott, a mappa rejtett marad
                errorBannerText.text = qsTr("The folder could not be shown again because its .picasa.ini file cannot be written. The folder stays hidden.")
            }
        }
        //: #1403: az XMP-arcírás EGY összegzést ad a köteg végén (kiírt ·
        //: kihagyott · első hiba). A csak olvasható fájl az eredetiben is
        //: megnevezett hibaeset, ezért az okot kiírjuk.
        //: #1403: `FaceTagJob::cancelled` — az eredetinek KÜLÖN
        //: állapotszövege van a megszakításra, tehát nem a befejezés
        //: üzenetét adjuk vissza.
        //: #1005: a háttérkép TÉNYLEGESEN beállítva — megnevezzük, mi
        //: végezte el (a felhasználó így tudja, melyik asztali környezet
        //: fogadta el), mert Linuxon több út van.
        function onDesktopBackgroundApplied(tool) {
            errorBanner.notice = true
            errorBannerText.text = qsTr("The desktop background is set (%1).").arg(tool)
        }
        //: #1005: a BMP kiírva, de az asztalt nem sikerült beállítani. A néma
        //: sikertelenség a legrosszabb kimenet: megmondjuk, HOVA került a
        //: kép, hogy kézzel beállíthassa.
        function onDesktopBackgroundFailed(bmpPath) {
            errorBanner.notice = false
            errorBannerText.text = qsTr("The picture is ready at %1, but the desktop background could not be set automatically.").arg(bmpPath)
        }
        function onXmpFacesCancelled(written) {
            errorBanner.notice = true
            errorBannerText.text = qsTr("Cancelled writing face tags (%1 file(s) written).").arg(written)
        }
        function onXmpFacesFinished(written, skipped, reason) {
            errorBanner.notice = reason === ""
            if (reason !== "")
                errorBannerText.text = qsTr("Face data written to %1 file(s); %2 skipped. First problem: %3")
                    .arg(written).arg(skipped).arg(reason)
            else
                errorBannerText.text = qsTr("Face data written to %1 file(s); %2 skipped.")
                    .arg(written).arg(skipped)
        }
        function onBrokenPhotosDetected(items) {
            var ids = hostBrokenPhotoDialog.ensure().pendingIds.slice()
            var names = hostBrokenPhotoDialog.ensure().pendingNames.slice()
            for (var i = 0; i < items.length; i++) {
                ids.push(items[i].id)
                names.push(items[i].name)
            }
            hostBrokenPhotoDialog.ensure().pendingIds = ids
            hostBrokenPhotoDialog.ensure().pendingNames = names
            // #459: rövid összegyűjtés — több törött kép is felbukkanhat
            // egymás után görgetés közben, ezeket EGY dialógusba fűzzük
            // ("this file(s)"), nem fotónként külön felugró ablakot.
            hostBrokenPhotoBatchTimer.restart()
        }
    }
}
