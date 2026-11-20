import QtQuick

// #7316: a poszter elkészülte után az eredeti szerkesztőnézetre vált, és az
// UTOLSÓ létrejött lapot mutatja (`0x00530c10`, a lapciklus után
// `0x0053de70`); a forráskép a kijelölésben marad. Ez a siker visszajelzése,
// külön eredmény-párbeszéd nélkül.
//
// A lapok a háttérben íródnak, és a célzott újraolvasás veszi fel őket a
// rácsmodellbe, ezért a megnyitás a modell frissülésére vár. A kijelölést NEM
// érinti: a néző csak a saját sorát állítja, a modell kijelölés-megőrzése a
// beszúrás után a forrásképen tartja. Ha az utolsó lap a várakozási időn belül
// sem kerül a rácsba (másik nézet, hálózati mappa), a `notOpened` jelzés a
// hívót a régi eredmény-párbeszédre bízza, hogy a siker ne maradjon
// visszajelzés nélkül.
Item {
    id: opener
    objectName: "posterResultOpener"

    // a főablak (nézőnyitás) és az alkalmazásvezérlő (rácsmodell)
    property var hostWindow: null
    property var hostController: null
    // ennyi ideig várunk a lap rácsmodellbe kerülésére
    property int waitMs: 20000
    // a megnyitásra váró lapok útvonalai, létrehozási sorrendben
    property var pendingPaths: []

    signal notOpened(var paths)

    function open(paths) {
        if (!paths || paths.length === 0) {
            opener.notOpened(paths || [])
            return
        }
        opener.pendingPaths = paths
        if (!opener.tryOpen())
            giveUpTimer.restart()
    }

    function tryOpen() {
        if (opener.pendingPaths.length === 0 || !opener.hostWindow
                || !opener.hostController)
            return false
        var last = String(opener.pendingPaths[opener.pendingPaths.length - 1])
        var row = opener.hostController.photos.rowOfPath(last)
        if (row < 0) return false
        giveUpTimer.stop()
        opener.pendingPaths = []
        opener.hostWindow.openPhotoViewer(row)
        return true
    }

    // A `revisionChanged` a beszúrások és a reset UTÁN jön, egyszer, tehát
    // a sorindex már a kész modellre vonatkozik.
    Connections {
        target: opener.hostController ? opener.hostController.photos : null
        function onRevisionChanged() { opener.tryOpen() }
    }

    Timer {
        id: giveUpTimer
        interval: opener.waitMs
        repeat: false
        onTriggered: {
            var paths = opener.pendingPaths
            opener.pendingPaths = []
            if (paths.length > 0) opener.notOpened(paths)
        }
    }
}
