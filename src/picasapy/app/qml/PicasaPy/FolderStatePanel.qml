import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Jobb oldali állapot-panel a Mappakezelőben (#231): a fában kijelölt
// mappához tartozó háromállapotú választó, alatta a figyelt mappák
// Picasa-kompatibilis összegző listája (a korábbi lapos Mappakezelő
// öröksége — így a régről megszokott áttekintés is megmarad).
//
// A választó sorokat SZÁNDÉKOSAN nem QtQuick.Controls RadioButonnal
// rajzoljuk: a RadioButton (AbstractButton) kattintáskor IMPERATÍVAN
// írja a saját `checked` tulajdonságát, ami véglegesen eltörné a
// backendhez kötött deklaratív bindingot (a következő mappa-kijelölésnél
// a kör már nem követné a valós állapotot). Itt a kör-ikon `visible`
// binding-je sosem kap imperatív írást — a kattintás-kezelő KIZÁRÓLAG a
// controllert hívja —, így mindig frissen tükrözi a kijelölt mappa
// tényleges állapotát.
ColumnLayout {
    id: panel
    property var manager
    property string selectedPath: ""
    spacing: 4

    readonly property var stateOptions: [
        { state: "once", label: qsTr("Scan Once") },
        { state: "none", label: qsTr("Remove from Picasa") },
        { state: "always", label: qsTr("Scan Always") }
    ]

    // #449: a Picasa 3 Mappakezelőjében NÉGY vezérlő volt, nem három — az
    // arcfelismerés be/ki kapcsolója a fenti hármastól (Scan Always/Once/
    // Remove) TELJESEN FÜGGETLEN (pl. egy mappa lehet egyszerre figyelt ÉS
    // arcfelismerésből kizárt), ezért szándékosan NEM negyedik rádiógomb,
    // hanem önálló jelölőnégyzet — vizuálisan is elkülönítve (lásd lent).
    //
    // A kizárt-e eldöntés (ős-mappákra is kiterjedő egyezéssel) itt, JS-ben
    // fut a `controller.faceExcludedFolders` NOTIFY-property alapján — a
    // `stateFor` (FolderManagerDialog.qml) mintáját követve, hogy a
    // binding automatikusan újraértékelődjön a lista változásakor (a
    // Python `faceDetectionEnabledFor` a tényleges, ős-mappát is kezelő
    // igazságforrás, ezt tükrözi vissza itt egyszerű előtag-egyezéssel).
    // #543: a kizártság-eldöntés a FolderManagerDialogba került (a fa
    // jelvénye is ugyanezt használja) — itt csak továbbhívunk rá.
    function facesExcludedFor(path) {
        return panel.manager ? panel.manager.facesExcludedFor(path) : false
    }

    Text {
        Layout.fillWidth: true
        text: panel.selectedPath.length > 0
              ? panel.selectedPath
              : qsTr("Select a folder on the left.")
        wrapMode: Text.WrapAnywhere
        elide: Text.ElideRight
        maximumLineCount: 3
        font.pixelSize: Theme.fontSize
        font.bold: true
        color: Theme.ink
    }

    // #543: az eredeti `foldermgr.tre` SÜLLYESZTETT keretbe
    // (`decrect softbevel/flatbevel`) zárja az állapot-választót, a
    // „For the current folder:" felirattal.
    Text {
        text: qsTr("For the current folder:")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }

    Rectangle {
        id: statusFrame
        Layout.preferredWidth: 231
        Layout.preferredHeight: 172
        color: Theme.contentPanel
        border.width: 1
        border.color: Theme.chromeBorder
        radius: 2

        ColumnLayout {
            id: statusColumn
            anchors.fill: parent
            anchors.margins: 8
            spacing: 0

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 0
        enabled: panel.selectedPath.length > 0

        Repeater {
            model: panel.stateOptions
            // #305: a MouseArea korábban a RowLayout KÖZVETLEN (tehát
            // layout-kezelt) gyermekeként `anchors.fill: parent`-et
            // használt — ez a Qt Quick Layouts szerint definiálatlan
            // viselkedés ("Detected anchors on an item that is managed
            // by a layout") és figyelmeztetést dobott minden sorra. A
            // delegate gyökere ezért egyszerű Item: a RowLayout csak a
            // sor tartalmát rendezi, a MouseArea pedig ezen KÍVÜL, a
            // gyökér-Item testvéreként fedi le a teljes sort.
            delegate: Item {
                id: optionRow
                required property var modelData
                objectName: "folderStateOption:" + optionRow.modelData.state
                Layout.fillWidth: true
                implicitHeight: 33

                RowLayout {
                    id: rowLayout
                    anchors.fill: parent
                    spacing: 5

                    Rectangle {
                        width: 24; height: 24; radius: 12
                        border.width: 1
                        border.color: Theme.chromeBorder
                        color: Theme.contentPanel
                        Rectangle {
                            anchors.centerIn: parent
                            width: 12; height: 12; radius: 6
                            color: Theme.selectionBlue
                            visible: panel.manager !== undefined
                                     && panel.manager !== null
                                     && panel.manager.stateFor(panel.selectedPath)
                                        === optionRow.modelData.state
                        }
                    }
                    Text {
                        text: optionRow.modelData.label
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: if (panel.manager)
                                   panel.manager.setState(
                                       panel.selectedPath, optionRow.modelData.state)
                }
            }
        }
    }

    // #449: vékony elválasztó — vizuálisan is jelezze, hogy a lenti
    // kapcsoló NEM tartozik a fenti hármashoz.
    Rectangle {
        Layout.fillWidth: true
        Layout.topMargin: 4
        Layout.bottomMargin: 4
        height: 1
        color: Theme.chromeBorder
    }

    Item {
        id: faceDetectionRow
        objectName: "faceDetectionToggle"
        Layout.fillWidth: true
        implicitHeight: faceDetectionLayout.implicitHeight
        // #543: az arcfelismerés-kapcsoló csak BEOLVASOTT mappán él — ha a
        // mappa „Remove from Picasa" állapotban van, az eredetiben is
        // szürke (nincs mihez arcadatot rendelni).
        enabled: panel.selectedPath.length > 0
                 && panel.manager
                 && panel.manager.stateFor(panel.selectedPath) !== "none"
                 && !panel.manager.parentFacesExcludedFor(panel.selectedPath)
        opacity: faceDetectionRow.enabled ? 1.0 : 0.4

        readonly property bool enabledForSelection:
            !panel.facesExcludedFor(panel.selectedPath)

        // a jelölőnégyzet kattintás-logikája külön, nevesített
        // függvényben (a MouseArea `clicked(mouse)` szignálja kötelező
        // paramétert visz, ami közvetlen tesztbeli meghívást nehezítene) —
        // ki: megerősítést kér (faceDetectionConfirm); be: azonnali
        function toggle() {
            if (!panel.manager) return
            panel.manager.setFaceDetectionEnabled(
                panel.selectedPath, !faceDetectionRow.enabledForSelection)
        }

        RowLayout {
            id: faceDetectionLayout
            anchors.fill: parent
            spacing: 6

            Rectangle {
                width: 14; height: 14
                border.width: 1
                border.color: Theme.chromeBorder
                color: Theme.contentPanel
                Text {
                    anchors.centerIn: parent
                    text: "✓"
                    font.pixelSize: 11
                    color: Theme.selectionBlue
                    visible: faceDetectionRow.enabledForSelection
                }
            }
            // #543: a `stringres` szerint a FELIRAT IS vált
            // (`CFolderMgrDialog::hasfr` / `::nofr`), nem csak a pipa
            Text {
                objectName: "faceDetectionToggleLabel"
                text: faceDetectionRow.enabledForSelection
                      ? qsTr("Face Detection On")
                      : qsTr("Face Detection Off")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
        }
        MouseArea {
            objectName: "faceDetectionToggleArea"
            anchors.fill: parent
            onClicked: faceDetectionRow.toggle()
        }
    }

        }
    }

    Text {
        text: qsTr("Watched folders")
        font.pixelSize: Theme.fontSize
        font.bold: true
        color: Theme.ink
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.fillHeight: true
        color: Theme.contentPanel
        border.color: Theme.chromeBorder

        ListView {
            id: watchedList
            objectName: "folderManagerWatchedList"
            anchors.fill: parent
            anchors.margins: 1
            clip: true
            // #305: null-őr — a controller a QML-engine leépítésekor
            // átmenetileg null lehet
            model: panel.manager ? panel.manager.visibleWatched : []
            delegate: Rectangle {
                required property string modelData
                width: watchedList.width
                height: 22
                color: panel.selectedPath === modelData
                       ? Theme.selectionBlue : "transparent"
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: 6
                    width: parent.width - 12
                    elide: Text.ElideMiddle
                    text: modelData
                    font.pixelSize: Theme.fontSize
                    color: panel.selectedPath === modelData
                           ? "#ffffff" : Theme.ink
                }
                TapHandler {
                    onTapped: if (panel.manager)
                                  panel.manager.selectedPath = modelData
                }
            }
            ScrollBar.vertical: PicasaScrollBar {}
        }
    }
}
