import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Bal oldali gyűjtemény-hasáb — Picasa "Folder List" gyökere (#320): öt
// önálló, csukható gyűjtemény (Albumok/Emberek/Projektek/Mappák/Egyéb),
// mindegyik saját fejléccel; csak a Mappák gyűjtemény tagolt évszám-
// szakaszokra (ld. docs/specs/ui-audit-mainwindow.md, mappafa szakasz).
Rectangle {
    id: pane
    color: Theme.panelBg

    property alias foldersModel: folderList.model
    property string selectedPath: ""
    property bool starredActive: false
    property bool searchActive: false
    property string searchQuery: ""
    property int searchResultCount: 0
    signal folderChosen(string path)
    signal starredChosen()

    // Gyűjtemény-csukottság — kezdőérték a collections.py
    // DEFAULT_COLLAPSED-jét tükrözi (controller hiányában is ésszerű).
    property bool albumsCollapsed: false
    property bool peopleCollapsed: true
    property bool projectsCollapsed: true
    property bool foldersCollapsed: false
    property bool otherCollapsed: true

    Component.onCompleted: {
        // #305: null-őr — a controller a QML-engine leépítésekor
        // átmenetileg null lehet (itt: induláskor még nem biztos, hogy
        // kötve van, ha a teszt csak magát a komponenst tölti be).
        if (!controller) return
        pane.albumsCollapsed = controller.isCollectionCollapsed("albums")
        pane.peopleCollapsed = controller.isCollectionCollapsed("people")
        pane.projectsCollapsed = controller.isCollectionCollapsed("projects")
        pane.foldersCollapsed = controller.isCollectionCollapsed("folders")
        pane.otherCollapsed = controller.isCollectionCollapsed("other")
    }

    // Egy gyűjtemény nyitása/csukása: a helyi állapotot azonnal frissíti
    // (a fejléc-nyíl és a tartalom eltűnése ne várjon a controllerre), a
    // perzisztálás a controlleren át fut (#305: null-őrrel).
    function toggleCollection(name) {
        var next
        if (name === "albums") { pane.albumsCollapsed = !pane.albumsCollapsed; next = pane.albumsCollapsed }
        else if (name === "people") { pane.peopleCollapsed = !pane.peopleCollapsed; next = pane.peopleCollapsed }
        else if (name === "projects") { pane.projectsCollapsed = !pane.projectsCollapsed; next = pane.projectsCollapsed }
        else if (name === "folders") { pane.foldersCollapsed = !pane.foldersCollapsed; next = pane.foldersCollapsed }
        else if (name === "other") { pane.otherCollapsed = !pane.otherCollapsed; next = pane.otherCollapsed }
        else return
        if (controller) controller.setCollectionCollapsed(name, next)
    }

    // Kurzor/görgő léptetés a könyvtárelemek között (#77): a szomszéd
    // mappát a modell adja (az évszám-sorokat átugorva), a kiválasztás a
    // szokásos folderChosen-úton fut. A görgő itt nem görget, hanem a
    // kijelölt mappát lépteti (Picasa-viselkedés); a touchpad kis deltáit
    // egy teljes fokozatig (120) gyűjtjük.
    function stepFolder(delta) {
        if (!folderList.model) return
        var target = folderList.model.neighborFolder(pane.selectedPath, delta)
        if (target !== "" && target !== pane.selectedPath)
            pane.folderChosen(target)
    }
    property real wheelAccum: 0
    function wheelStep(delta) {
        wheelAccum += delta
        while (wheelAccum <= -120) { wheelAccum += 120; stepFolder(1) }
        while (wheelAccum >= 120) { wheelAccum -= 120; stepFolder(-1) }
    }
    // a kijelölt mappa maradjon látótérben (kívülről is változhat:
    // kereső-javaslat, feed-görgetés)
    onSelectedPathChanged: {
        if (!folderList.model) return
        var row = folderList.model.rowOfPath(pane.selectedPath)
        if (row >= 0) folderList.positionViewAtIndex(row, ListView.Contain)
    }

    // A görgő-kezelő a pane gyökerén él: Flickable-be (ListView) ágyazott
    // pointer-handler nem támogatott, és itt a fejléc-sávok fölött is működik.
    WheelHandler {
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onWheel: function(event) { pane.wheelStep(event.angleDelta.y) }
    }

    // Egy gyűjtemény-fejléc: zöld ▼ (nyitva) / piros ▶ (csukva) háromszög +
    // felirat, a meglévő fejléc-gradienssel. A `headerText` felülírhatja a
    // "label (itemCount)" alapértelmezést (pl. kereső-eredmény szövege).
    component CollectionHeader: Rectangle {
        id: header
        property string label: ""
        property int itemCount: 0
        property string headerText: ""
        property string labelObjectName: ""
        property bool collapsed: false
        signal toggled()

        // a sor saját objectName-je a fejlécéből képezve (teszthez: a
        // "toggled" jel innen közvetlenül kiváltható, ahogy a projektben
        // szokásos egyedi gombok "clicked" jelének közvetlen hívása)
        objectName: header.labelObjectName !== "" ? header.labelObjectName + "Row" : ""
        height: 22
        gradient: Gradient {
            GradientStop { position: 0.0; color: Theme.panelHeaderTop }
            GradientStop { position: 1.0; color: Theme.panelHeaderBg }
        }
        border.color: Theme.chromeBorder
        Row {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left; anchors.leftMargin: 4
            spacing: 4
            Text {
                text: header.collapsed ? "▶" : "▼"
                font.pixelSize: 8
                // Audit: az eredeti Picasában a nyitott gyűjtemény zöld, a
                // csukott piros — ez itt ÁLLAPOT-jelzés, nem márka-szerep;
                // külön "collapsed" jelzőszín híján a brandRed tokent
                // kölcsönözzük erre a célra.
                color: header.collapsed ? Theme.brandRed : Theme.picasaGreen
            }
            Text {
                objectName: header.labelObjectName
                text: header.headerText !== "" ? header.headerText
                      : header.label + " (" + header.itemCount + ")"
                font.pixelSize: Theme.fontSize; font.bold: true
                color: Theme.panelHeaderText
            }
        }
        MouseArea {
            anchors.fill: parent
            onClicked: header.toggled()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        CollectionHeader {
            Layout.fillWidth: true
            label: qsTr("Albums")
            itemCount: 1
            labelObjectName: "albumsHeader"
            collapsed: pane.albumsCollapsed
            onToggled: pane.toggleCollection("albums")
        }

        Rectangle {
            id: starredItem
            objectName: "starredItem"
            visible: !pane.albumsCollapsed
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            color: pane.starredActive
                   ? Theme.panelSelection : "transparent"
            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 16
                spacing: 5
                Text { text: "★"; color: Theme.starYellow; font.pixelSize: Theme.fontSize }
                Text {
                    text: qsTr("Starred photos")
                    font.pixelSize: Theme.fontSize
                    color: pane.starredActive
                           ? Theme.panelSelectionText : Theme.textDark
                }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: pane.starredChosen()
            }
        }

        CollectionHeader {
            Layout.fillWidth: true
            label: qsTr("People")
            // #320: a tartalom (arc-csoportok) a 3. fázisban / a #320
            // további lépéseiben érkezik — most csak a fejléc létezik.
            itemCount: 0
            labelObjectName: "peopleHeader"
            collapsed: pane.peopleCollapsed
            onToggled: pane.toggleCollection("people")
        }

        CollectionHeader {
            Layout.fillWidth: true
            label: qsTr("Projects")
            // #320: a tartalom forrása még kutatás alatt — egyelőre üres.
            itemCount: 0
            labelObjectName: "projectsHeader"
            collapsed: pane.projectsCollapsed
            onToggled: pane.toggleCollection("projects")
        }

        CollectionHeader {
            Layout.fillWidth: true
            label: qsTr("Folders")
            itemCount: folderList.model ? folderList.model.folderCount : 0
            headerText: pane.searchActive
                        ? qsTr("Search results for \"%1\" (%2)")
                          .arg(pane.searchQuery).arg(pane.searchResultCount)
                        : ""
            labelObjectName: "folderPaneHeader"
            collapsed: pane.foldersCollapsed
            onToggled: pane.toggleCollection("folders")
        }

        ListView {
            id: folderList
            objectName: "folderListView"
            visible: !pane.foldersCollapsed
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            // kurzorgombok, amikor a lista fókuszban van (#77)
            activeFocusOnTab: true
            Keys.onUpPressed: pane.stepFolder(-1)
            Keys.onDownPressed: pane.stepFolder(1)

            // A háttér-szinkron utáni modell-frissítés ne nullázza a
            // görgetési pozíciót — enélkül a lista folyton visszaugrik,
            // és nem lehet görgetni. A reset 0-ra ugrása nem írhatja
            // felül a mentett pozíciót (#10, a fotórács mintájára).
            property real savedY: 0
            property bool restoring: false
            onContentYChanged: {
                if (!restoring && (contentY > 0 || moving))
                    savedY = contentY
            }
            onMovementEnded: savedY = contentY
            Connections {
                target: folderList.model
                function onFolderCountChanged() {
                    folderList.restoring = true
                    folderList.contentY = Math.min(
                        folderList.savedY,
                        Math.max(0, folderList.contentHeight
                                    - folderList.height))
                    folderList.restoring = false
                }
            }
            delegate: Rectangle {
                required property string kind
                required property string name
                required property string path
                required property int count
                width: folderList.width; height: 22
                color: kind === "folder" && pane.selectedPath === path
                       ? Theme.panelSelection : "transparent"

                // évszám-elválasztó: arányos betűs címke + vékony
                // vízszintes elválasztó vonal a panel széléig (audit:
                // docs/specs/ui-audit-mainwindow.md, mappafa szakasz)
                Text {
                    id: yearLabel
                    visible: kind === "year"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left; anchors.leftMargin: 6
                    text: name
                    font.pixelSize: Theme.fontSize
                    color: Theme.panelYearText
                }
                Rectangle {
                    visible: kind === "year"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: yearLabel.right; anchors.leftMargin: 6
                    anchors.right: parent.right; anchors.rightMargin: 6
                    height: 1
                    color: Theme.chromeBorder
                }

                Row {
                    visible: kind === "folder"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left; anchors.leftMargin: 12
                    spacing: 5
                    Text {
                        text: "▸"
                        font.pixelSize: Theme.fontSize - 2
                        color: pane.selectedPath === path
                               ? Theme.panelSelectionText : Theme.folderArrow
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    FolderIcon { size: 13; anchors.verticalCenter: parent.verticalCenter }
                    Text {
                        text: name + " (" + count + ")"
                        font.pixelSize: Theme.fontSize
                        color: pane.selectedPath === path
                               ? Theme.panelSelectionText : Theme.ink
                    }
                }
                MouseArea {
                    enabled: kind === "folder"
                    anchors.fill: parent
                    onClicked: {
                        folderList.forceActiveFocus()   // kurzorgombokhoz (#77)
                        pane.folderChosen(path)
                    }
                }
            }
            ScrollBar.vertical: PicasaScrollBar {}
        }

        CollectionHeader {
            Layout.fillWidth: true
            label: qsTr("Other")
            // #320: még nincs kijelölt tartalom-forrás ehhez a
            // gyűjteményhez — a fejléc addig is látszik, üresen.
            itemCount: 0
            labelObjectName: "otherHeader"
            collapsed: pane.otherCollapsed
            onToggled: pane.toggleCollection("other")
        }
    }
}
