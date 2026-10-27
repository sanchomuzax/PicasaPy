import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

PicasaMenu {
    id: menuHelp
    property var bar: null
    property var controllerRef: null
    title: qsTr("&Help")
    //: #2054: BEKÖTVE — a súgó a csomagban van, net nélkül is megnyílik.
    MenuItem {
        objectName: "menuHelpContents"
        text: qsTr("&Help Contents and Index") + "\tF1"
        onTriggered: bar.helpRequested("")
    }
    MenuItem {
        objectName: "menuHelpKeyboardShortcuts"
        text: qsTr("&Keyboard Shortcuts")
        onTriggered: bar.keyboardShortcutsRequested()
    }
    MenuSeparator {}
    // hiányzott (#324 audit): web-linkek
    PicasaMenuItem { text: qsTr("Picasa &Forums"); placeholder: false; retired: true }  // #638
    PicasaMenuItem { text: qsTr("Online Information"); placeholder: false; retired: true }  // #638
    PicasaMenuItem { text: qsTr("Product Release Notes"); placeholder: false; retired: true }  // #638
    // #1774 (mérve): az eredetiben itt NINCS csoporthatár.
    PicasaMenuItem { text: qsTr("Privacy Policy"); placeholder: false; retired: true }  // #638
    PicasaMenuItem { text: qsTr("Terms of Service"); placeholder: false; retired: true }  // #638
    MenuSeparator {}
    // #4640: a PicasaPy saját frissítéskeresése nem paritás-feladat. Az
    // eredeti az egykori Google-szolgáltatásra épült, amelyet a Picasa
    // Wine alatt maga letiltott, ezért nyugdíjazott (szürke, pont nélkül),
    // nem helyfoglaló.
    PicasaMenuItem { text: qsTr("&Check for Updates"); placeholder: false; retired: true }
    MenuSeparator {}
    // SAJÁT FUNKCIÓ (#1364): a Teljesítmény-monitor az eredeti Picasa
    // 3.9 Súgó menüjében NEM létezik (`docs/specs/ui-audit-menus.md`) —
    // a mi fejlesztői eszközünk, tehát a bináris-egyezés ide nem
    // vonatkozik. (Az eredetinek volt `/uidebug` lapja a beépített
    // kiszolgálón, de azt szándékosan nem építjük meg: ADR-011.)
    PicasaMenuItem {
        objectName: "menuHelpPerfMonitor"
        placeholder: false
        sajat: true
        text: qsTr("Performance Monitor")
        checkable: true
        checked: (controllerRef && controllerRef.perfMonitorEnabled !== undefined)
            ? controllerRef.perfMonitorEnabled : false
        onTriggered: {
            controller.togglePerfMonitor()
            // #2377: a `checkable` MenuItem kattintáskor MAGA billenti a
            // `checked`-et, és ez eldobja a fenti kötést. Ma azért nem
            // látszik, mert a művelet mindig átbillenti az állapotot —
            // ez szerencse, nem szerkezet (ld. #1471).
            checked = Qt.binding(function () {
                return (controllerRef && controllerRef.perfMonitorEnabled !== undefined)
                    ? controllerRef.perfMonitorEnabled : false
            })
        }
    }
    // #1654: TARTÓS tesztüzem. A Teljesítmény-monitorral szemben ez
    // TÚLÉLI a kilépést, és a KÖVETKEZŐ indulást naplózza az első
    // ezredmásodperctől — az indulás az egyetlen szakasz, amit
    // menetközbeni kapcsolóval elvből nem lehet megmérni (#1653).
    PicasaMenuItem {
        objectName: "menuHelpTesztuzem"
        // #1701: a tesztüzem a PicasaPy saját eszköze — az eredeti
        // Picasában nincs megfelelője
        placeholder: false
        sajat: true
        text: qsTr("Test Mode (logs the next startup)")
        checkable: true
        checked: (controllerRef && controllerRef.tesztuzemEnabled !== undefined)
            ? controllerRef.tesztuzemEnabled : false
        onTriggered: {
            controllerRef.toggleTesztuzem()
            // #2377: a `checkable` MenuItem kattintáskor MAGA billenti a
            // `checked`-et, és ez eldobja a fenti kötést. Ma azért nem
            // látszik, mert a művelet mindig átbillenti az állapotot —
            // ez szerencse, nem szerkezet (ld. #1471).
            checked = Qt.binding(function () {
                return (controllerRef && controllerRef.tesztuzemEnabled !== undefined)
                    ? controllerRef.tesztuzemEnabled : false
            })
        }
    }
    // Egykattintásos átadás — CSAK tesztüzemben látszik. A `height`
    // nullázása azért kell, mert a rejtett MenuItem különben üres
    // sávot hagyna a Súgó menüben.
    PicasaMenuItem {
        objectName: "menuHelpSendLog"
        // #1701: a naplóátadás is a miénk — a tesztüzem párja
        placeholder: false
        sajat: true
        // ⚠️ A láthatóság feltétele SAJÁT tulajdonságban él, nem
        // közvetlenül a `visible`-ben: a QQuickItem `visible`-je az
        // EFFEKTÍV láthatóságot adja vissza, ami csukott menünél
        // mindig hamis — a kötés helyessége azon nem mérhető.
        readonly property bool tesztuzemAktiv:
            (controllerRef && controllerRef.tesztuzemEnabled !== undefined)
            ? controllerRef.tesztuzemEnabled : false
        text: qsTr("Send Log...")
        visible: tesztuzemAktiv
        height: tesztuzemAktiv ? implicitHeight : 0
        onTriggered: controllerRef.tesztuzemNaploAtadasa()
    }
    MenuItem {
        text: qsTr("About PicasaPy")
        onTriggered: bar.aboutRequested()
    }
}
