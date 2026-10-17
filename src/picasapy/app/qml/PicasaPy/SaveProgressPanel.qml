import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #1527/#5268: lebegő mentési/visszaállítási folyamatjelző — a
// `BatchEditProgressPanel` mintájára. A műveletek a `SaveMixin`-ben
// háttérszálon futnak (`_start_background`).
//
// A szöveg az eredeti KÉT hivatalos alakja, egyes és többes számra külön
// erőforrásként (`CThumbUI::FileSave::progfile` / `progfiles`):
//
//   „Fájl mentése: %.1f%%"        — EGY fájl
//   „%1$d fájl mentése %2$.1f%%"  — több fájl
//   „Fájlok visszaállítása"        — a fájlok Revert művelete
//
// ⚠️ A százalék EGY tizedesjegyre megy: a hivatalos formátum `%.1f`. A
// #1527 jegy szövege „századpontos"-t ír, de a formátumsztring az
// erősebb bizonyíték, és az tizedet mond.
Rectangle {
    id: panel

    property int fileCount: 0
    property real percent: 0
    property bool isReverting: false

    width: 250
    height: content.implicitHeight + 20
    radius: 4
    color: Theme.trayBg
    border.color: Theme.chromeBorder
    border.width: 1

    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 10
        spacing: 6

        Text {
            objectName: "saveProgressPanelText"
            Layout.fillWidth: true
            //: CThumbUI::FileSave::progfile — EGY fájl mentése, %1 a
            //: százalék egy tizedesjeggyel
            text: panel.isReverting
                  //: CThumbUI::FileRevert::progress
                  ? qsTr("Reverting Files.")
                  : panel.fileCount === 1
                    ? qsTr("Saving file %1%").arg(panel.percent.toFixed(1))
                    //: CThumbUI::FileSave::progfiles — %1 a fájlok száma,
                    //: %2 a százalék egy tizedesjeggyel
                    : qsTr("Saving %1 files %2%").arg(panel.fileCount)
                                                 .arg(panel.percent.toFixed(1))
            color: Theme.ink
            font.pixelSize: Theme.fontSize
            elide: Text.ElideRight
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            radius: 4
            color: Theme.trackBg
            border.color: Theme.chromeBorder

            Rectangle {
                objectName: "saveProgressPanelBarFill"
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                radius: parent.radius
                color: Theme.picasaGreen
                width: parent.width * Math.max(0, Math.min(1, panel.percent / 100))
            }
        }
    }
}
