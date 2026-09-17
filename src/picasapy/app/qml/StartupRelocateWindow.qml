import QtQuick
import QtQuick.Layouts
import PicasaPy

// A `moving_database.fen` megfelelője: a KÖVETKEZŐ induláskor elvégzett
// adatbázis-költözés haladásjelzője (#3214).
//
// Miért külön, önálló ablak, és nem a fő ablak párbeszéde: a költözésnek a
// tárhely-előkészítés (zár + útvonalak) ELŐTT kell lefutnia, különben a
// program a régi helyet nyitná meg. Ilyenkor a fő ablak még nem létezik —
// a mért eredetiben is külön, korai ablak jelenik meg.
//
// Megszakítás gomb SZÁNDÉKOSAN nincs: a másolás ezen a ponton az indulás
// része, és a fél úton abbahagyott költözés után nem volna eldöntve,
// melyik helyről induljon a program. A forrás minden hibaágon érintetlen
// marad (`picasapy.index.relocate` invariánsa), tehát a művelet
// megszakítás nélkül is biztonságos.
Window {
    id: koltozesAblak
    objectName: "startupRelocateWindow"
    visible: true
    title: qsTr("Moving the database")
    width: 460
    height: 150
    minimumWidth: 360
    minimumHeight: 130
    color: Theme.canvasBg

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 10

        Text {
            objectName: "startupRelocateTitle"
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("PicasaPy is moving the database.")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        Text {
            objectName: "startupRelocatePhaseText"
            Layout.fillWidth: true
            //: a mag fázisnevei (`database`/`cache`/`done`) emberi nyelven —
            //: a fordítás a felület dolga, ld. `RelocationProgress`
            text: {
                var fazis = (typeof koltozes !== "undefined" && koltozes
                             && koltozes.fazis !== undefined)
                            ? koltozes.fazis : ""
                if (fazis === "database") return qsTr("Photo index…")
                if (fazis === "cache") return qsTr("Thumbnail cache…")
                if (fazis === "done") return qsTr("Finishing…")
                return ""
            }
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        Text {
            objectName: "startupRelocateTargetText"
            Layout.fillWidth: true
            elide: Text.ElideMiddle
            //: #1956: `typeof` a NÉVRE, `&&` az ÉRTÉKRE — a híd az ablak
            //: ELDOBÁSAKOR is nullra válthat, és a kötés még újraértékelődik
            text: (typeof koltozes !== "undefined" && koltozes)
                  ? koltozes.cel : ""
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            radius: 4
            color: Theme.trackBg
            border.color: Theme.chromeBorder

            Rectangle {
                objectName: "startupRelocateProgressFill"
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                radius: parent.radius
                color: Theme.picasaGreen
                width: parent.width * (
                    (typeof koltozes !== "undefined" && koltozes
                     && koltozes.arany !== undefined)
                        ? koltozes.arany : 0)
            }
        }

        Item { Layout.fillHeight: true }
    }
}
