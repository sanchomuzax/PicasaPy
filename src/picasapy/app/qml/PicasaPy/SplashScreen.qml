import QtQuick
import PicasaPy

// Indítóképernyő (#189): kártyaszerű overlay a betöltés idejére — logó,
// verzió, animált állapotüzenet-sor és alul a kék „foglalt"-sáv fénycsíkkal.
//
// Az objektum property-vezérelt: a Python-oldali StartupStatus híd tölti a
// `statusText`-et, és `ready = true`-ra állítja, amikor az indulás kész — a
// splash erre magától kifakul (opacity-animáció), majd láthatatlanná válik.
// A bekötést az integrátor végzi; itt a komponens és a viselkedés áll
// készen, önállóan tesztelhetően. Bekötési lépések (forró fájlok):
//
//   application.py — korán (a controller előtt):
//     startup_status = StartupStatus("Indulás…")   # helyi változóban (GC!)
//     engine.rootContext().setContextProperty("startupStatus", startup_status)
//     ...az induló lépéseknél startup_status.report("Mappák beolvasása…"),
//     a kész nézetnél egyszer startup_status.finish() (vagy
//     controller.syncFinished.connect(startup_status.finish))
//
//   Main.qml — a gyökér legfelső rétegén:
//     SplashScreen { anchors.fill: parent; z: 10000; version: appVersion
//                    statusText: startupStatus.statusText
//                    ready: startupStatus.ready }
Item {
    id: root
    objectName: "splashScreen"

    // -- kívülről kötött property-k (StartupStatus tükre) --------------------
    property string version: ""       // pl. "v0.4.31 (…)" — a verzió-címkéhez
    property string statusText: ""     // aktuális állapotüzenet
    property bool ready: false          // true → a splash kifakul és eltűnik

    // az indulás alatt vagyunk-e: a foglalt-sáv és a pont-animáció ehhez köt,
    // hogy készre álláskor magától megálljon
    readonly property bool busy: !root.ready

    anchors.fill: parent
    // kifakulás készre álláskor; a láthatóság az opacity-t követi, így a
    // funkcionális teszt a `ready` átbillentésével szimulálhatja az eltűnést
    visible: opacity > 0.01
    opacity: root.ready ? 0.0 : 1.0
    Behavior on opacity {
        NumberAnimation { duration: 260; easing.type: Easing.InOutQuad }
    }

    // halvány elsötétítő háttér a mögöttes (még üres) felület elé
    Rectangle {
        anchors.fill: parent
        color: Theme.canvasBg
    }

    // -- a középre igazított kártya ------------------------------------------
    Rectangle {
        id: card
        objectName: "splashCard"
        anchors.centerIn: parent
        width: 420
        // #240: explicit összeg — a title-sor is számít, és a logó fix
        // magassága miatt a kártya SVG-hiba esetén sem eshet össze
        height: titleBar.height + 28 + column.implicitHeight + 24 + bar.height
        radius: 6
        color: Theme.contentPanel
        border.color: Theme.chromeBorder
        border.width: 1
        clip: true

        // felső title-sor
        Rectangle {
            id: titleBar
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 34
            color: Theme.chromeBg
            Text {
                anchors.centerIn: parent
                text: "PicasaPy"
                color: Theme.ink
                font.pixelSize: Theme.fontSize + 1
                font.bold: true
            }
        }

        // középső tartalom: logó + verzió + állapotsor
        Column {
            id: column
            anchors.top: titleBar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: 28
            spacing: 16

            Image {
                id: logo
                objectName: "splashLogo"
                anchors.horizontalCenter: parent.horizontalCenter
                // a qml/PicasaPy/ mappából az app/assets két szinttel feljebb.
                // #240: explicit magasság — az elrendezés akkor sem esik
                // össze, ha a kép (még) nem töltődött be; SVG-hibánál (pl.
                // hiányzó Qt-SVG plugin Debianon) raszteres fallback.
                source: Qt.resolvedUrl("../../assets/logo.svg")
                height: 72
                sourceSize.height: 144
                fillMode: Image.PreserveAspectFit
                onStatusChanged: {
                    if (status === Image.Error
                            && source !== Qt.resolvedUrl("../../assets/icon.png"))
                        source = Qt.resolvedUrl("../../assets/icon.png")
                }
            }

            Text {
                objectName: "splashVersionLabel"
                // #242: szélesség-korlát + sortörés — a hosszú (commit-
                // hash-es) build-sztring is a kártyán belül marad, sosem
                // érhet a foglalt-sáv alá (a kártya-magasság az
                // implicitHeight-ből követi a többsoros feliratot)
                width: parent.width
                wrapMode: Text.WordWrap
                text: root.version.length > 0
                      ? qsTr("PicasaPy · version %1").arg(root.version)
                      : "PicasaPy"
                color: Theme.folderDate
                font.pixelSize: Theme.fontSize
                horizontalAlignment: Text.AlignHCenter
            }

            // állapotüzenet-sor + három animált pont
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 4

                Text {
                    objectName: "splashStatusText"
                    text: root.statusText
                    color: Theme.textGray
                    font.pixelSize: Theme.fontSize
                    verticalAlignment: Text.AlignVCenter
                }

                // 1,4 s ciklusú, folyamatosan futó fázis; a pontok ebből
                // számolják az opacitásukat, egymáshoz képest 0,2 s
                // eltolással (0,2 / 1,4 ≈ 0,143 fázis)
                Item {
                    id: dots
                    width: 22
                    height: Theme.fontSize
                    // csak akkor látszanak, ha van mit tölteni és van szöveg
                    visible: root.busy && root.statusText.length > 0
                    property real phase: 0.0
                    NumberAnimation on phase {
                        from: 0.0; to: 1.0; duration: 1400
                        loops: Animation.Infinite
                        running: dots.visible
                    }
                    Row {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 3
                        Repeater {
                            model: 3
                            Rectangle {
                                width: 4
                                height: 4
                                radius: 2
                                color: Theme.textGray
                                // saját fázis a dot indexe szerint eltolva,
                                // 0..1-re visszacsomagolva; a szinusz adja a
                                // lágy fel-le pulzálást
                                property real local: {
                                    var p = dots.phase - index * (0.2 / 1.4)
                                    return p - Math.floor(p)
                                }
                                opacity: 0.3 + 0.7 * (0.5 + 0.5
                                         * Math.sin(local * 2 * Math.PI))
                            }
                        }
                    }
                }
            }
        }

        // -- alsó „foglalt"-sáv fénycsíkkal ----------------------------------
        Rectangle {
            id: bar
            objectName: "splashBusyBar"
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 13                 // 12–14 px
            color: Theme.infoBar        // #568FB7 steel-blue
            clip: true

            // balról jobbra futó fénycsík lágy gradiens-szélekkel; a mozgás
            // 1,8 s-os lineáris végtelen ciklus, csak busy állapotban fut
            Rectangle {
                id: sweep
                objectName: "splashSweep"
                width: parent.width * 0.32
                height: parent.height
                visible: root.busy
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "#00FFFFFF" }
                    GradientStop { position: 0.5; color: "#59FFFFFF" }
                    GradientStop { position: 1.0; color: "#00FFFFFF" }
                }
                NumberAnimation on x {
                    from: -sweep.width
                    to: bar.width
                    duration: 1800
                    loops: Animation.Infinite
                    running: sweep.visible
                }
            }
        }
    }
}
