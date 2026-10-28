import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy

Rectangle {
    required property var hostWindow
    required property var hostController
    required property var hostToolbar
    required property var hostSearchSuggestionsBox
    required property var hostBackupHost
    required property var hostRightDrawerHandle
    required property var hostPeoplePanel

    property alias grid: grid
    property alias unnamedFacesView: unnamedFacesView

    color: Theme.lightboxBg
    SplitView.fillWidth: true

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // zöld eredménysáv aktív szűrőnél (Picasa-minta)
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 26
            // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
            // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
            visible: hostWindow.personAlbumName === ""
                && ((hostController && hostController.filterActive !== undefined)
                    ? hostController.filterActive : false)
            color: "#5aa865"
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                spacing: 10
                Rectangle {
                    // #4531: a keresés után is látszik (az eredetiben
                    // a keresősáv `viewallbutton`-ja)
                    objectName: "searchBackToViewAll"
                    Layout.preferredHeight: 18
                    Layout.preferredWidth: viewAllText.width + 20
                    radius: 9
                    color: "#ffffff"
                    Text {
                        id: viewAllText
                        anchors.centerIn: parent
                        //: #1398: MÉRVE a `viewallbutton` feliratának
                        //: („Back to View All"); az eredeti súgója
                        //: „Exit Search Mode". Nálunk a zöld sávnak
                        //: nincs súgó-rétege, ezért csak a felirat.
                        text: qsTr("Back to View All")
                        font.pixelSize: Theme.fontSize - 1
                        font.bold: true
                        color: "#3b8f00"
                    }
                    TapHandler {
                        // #4531: keresésből a mező is ürüljön, és a bal
                        // hasáb is álljon vissza a teljes mappalistára —
                        // ugyanaz az út, mint a keresőmező ✕ gombja
                        onTapped: {
                            if (hostToolbar.searchText.trim().length > 0) {
                                hostToolbar.clearSearch()
                                hostWindow.clearSelection()
                                hostController.search("")
                                hostSearchSuggestionsBox.suggestions = []
                            } else {
                                hostController.clearFilter()
                            }
                        }
                    }
                }
                Text {
                    // #305: null-őr
                    //: #1830: a kor-szűrő mondata a találati sáv
                    //: szövege UTÁN jön („Legfeljebb N napos
                    //: képek."), ahogy az eredeti a találati
                    //: fejlécben írja ki. Szűrés nélkül üres, tehát
                    //: a sáv változatlan.
                    text: hostController
                          ? (hostController.ageFilterText
                             ? hostController.filterStatusText + " "
                               + hostController.ageFilterText
                             : hostController.filterStatusText)
                          : ""
                    color: "white"
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                }
                // #1833: a MINTA jelzése és törlése (`similarthumb`
                // + `clearsim`). Az eredetiben a keresés második
                // rétegében ül; nálunk a zöld eredménysávban, mert a
                // hasonlóság-keresés is szűrt nézetet ad, és a
                // „Mindet" gomb amúgy is itt vezet ki belőle.
                Text {
                    objectName: "similaritySampleLabel"
                    visible: (hostController
                              && hostController.similaritySample !== undefined)
                             ? hostController.similaritySample.length > 0
                             : false
                    text: qsTr("Similarity Search Results")
                    color: "white"
                    font.pixelSize: Theme.fontSize
                }
                Rectangle {
                    objectName: "similarityClearButton"
                    visible: (hostController
                              && hostController.similaritySample !== undefined)
                             ? hostController.similaritySample.length > 0
                             : false
                    Layout.preferredHeight: 18
                    Layout.preferredWidth: clearSimText.width + 20
                    radius: 9
                    color: "#ffffff"
                    Text {
                        id: clearSimText
                        anchors.centerIn: parent
                        //: `clearsim` — a minta törlése.
                        text: qsTr("Clear Sample")
                        font.pixelSize: Theme.fontSize - 1
                        font.bold: true
                        color: "#3b8f00"
                    }
                    TapHandler {
                        onTapped: hostController.clearSimilarity()
                    }
                }
                // #1398: a másodpéldány-mód jelzése a sávon (az
                // eredetiben a keresési sáv rejtett `dupesearch`
                // eleme jelzi). ⚠️ A felirat NEM mért — a rejtett
                // elemhez a szövegtár nem ad szöveget.
                Text {
                    objectName: "dupeSearchLabel"
                    visible: (hostController
                              && hostController.viewModeName !== undefined)
                             ? hostController.viewModeName === "dupes"
                             : false
                    text: qsTr("Duplicate Files")
                    color: "white"
                    font.pixelSize: Theme.fontSize
                }
                Item { Layout.fillWidth: true }
            }
        }

        // #1398: a keresés ideje alatt is legyen látható jelzés —
        // üres várakozás TILOS (#1798). A nagy könyvtár átvizsgálása
        // másodpercekig tart, és a rács addig a régi nézetet mutatja.
        Rectangle {
            objectName: "dupeSearchScanningBar"
            Layout.fillWidth: true
            Layout.preferredHeight: 26
            visible: (hostController
                      && hostController.dupeSearchScanning !== undefined)
                     ? hostController.dupeSearchScanning : false
            color: "#f0e3b0"
            Text {
                objectName: "dupeSearchScanningText"
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 8
                text: qsTr("Looking for duplicate files...")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
        }

        // #1833: „Updating similarity database (will be fast next
        // time)" — az ELSŐ keresés végigszámolja a hiányzó
        // ujjlenyomatokat. ⚠️ Üres várakozás TILOS (#1798): a
        // felhasználónak látnia kell, hogy dolgozunk, ÉS azt is,
        // hogy ez egyszeri.
        Rectangle {
            objectName: "similarityUpdatingBar"
            Layout.fillWidth: true
            Layout.preferredHeight: 26
            visible: (hostController
                      && hostController.similarityUpdating !== undefined)
                     ? hostController.similarityUpdating : false
            color: "#f0e3b0"
            Text {
                objectName: "similarityUpdatingText"
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 8
                //: `CSimSearch::updating` — az eredeti szövege (#3573)
                text: qsTr(
                    "Updating similarity database "
                    + "(will be fast next time)")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
        }

        // indexkép-csoport: fehér kártya a vásznon (kézikönyv 08)
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            // A személyalbum saját, szűkebb keretet kap. A Név
            // nélküliek ugyanitt jelenik meg, de nem örökölheti az
            // előző személyalbum nulla margóját (#5363).
            readonly property bool personAlbumLayout:
                hostWindow.personAlbumName !== ""
                && !hostWindow.unnamedFacesOpen
            // A Picasa személylapja közvetlenül a bal oldali
            // elválasztó után indul; a kártya általános kerete itt
            // külön vízszintes/felső behúzással állítja be a fejlécet.
            Layout.leftMargin: personAlbumLayout ? 0 : 12
            Layout.topMargin: personAlbumLayout ? 0 : 12
            Layout.bottomMargin: 12
            //: #3604: a JOBB oldalon nincs kártya-rés — az eredetiben
            //: (`albumsback`) a rácsterület flush az ablak/fiók
            //: széléhez (`XConstraint 1, 1, 0`). A másik három oldal
            //: 12 px-es kerete a mi kártya-stílusunk, azt ez a jegy
            //: nem kérdőjelezi meg.
            Layout.rightMargin: 0
            // #5352: a Név nélküliek (és a mellőzött) nézetben a
            // kártya kerete is az eredeti szürke (job-208: #e2e2e2);
            // sötét témában a mai szín marad.
            color: hostWindow.unnamedFacesOpen && !Theme.dark
                   ? Theme.chromeBg : Theme.contentPanel
            border.color: Theme.chromeBorder

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: parent.personAlbumLayout ? 0 : 14
                anchors.topMargin: parent.personAlbumLayout ? 6 : 14
                anchors.bottomMargin: 14
                //: #3604: a jobb belső margó a fiók-fogó sávjának
                //: szélessége — így a rács görgetősávja pont odáig ér
                //: (`feedScrollBar` jobb éle == `jobbFiokFogo` bal
                //: éle), csukott fióknál tehát az ablak széléig.
                anchors.rightMargin: hostRightDrawerHandle.width
                spacing: 4

                // Könyvtár-feed (#64) — a komponens a PicasaPy
                // modulban él (LightboxFeed.qml, #150)
                LightboxFeed {
                    id: grid
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    // kereséskor a #7-es csoportosított nézet fut,
                    // a „Névtelenek" nézetnél (#26) az UnnamedFacesView
                    // #305: null-őr
                    visible: hostController
                        ? (!hostController.searchActive && !hostWindow.unnamedFacesOpen)
                        : true
                    appWindow: hostWindow
                    // #3751: a mentés-panel állapota a rács
                    // feliratához — ugyanazok a bemenetek, mint a
                    // `FolderPane`-é (ld. ott a #3681-es jegyzetet);
                    // a tartalmat a vezérlő szűri (`BackupHost`).
                    mentesSzuroAktiv: hostBackupHost.visible
                    mentesToltodnek: hostBackupHost.mappakToltodnek
                    mentesVanKeszlet: hostBackupHost.kivalasztott >= 0
                    onOpenRequested: function(row) {
                        hostWindow.openPhotoViewer(row)
                    }
                    onSlideshowRequested: function(startRow) {
                        hostWindow.startSlideshow(startRow)
                    }
                }

                // #7: keresési találatok mappánként csoportosítva
                // (Picasa-minta) — a GridView nem támogat szekció-
                // fejlécet, ezért csoportonként egy fejléc + egy
                // nem-interaktív al-rács.
                ListView {
                    id: groupedResults
                    objectName: "groupedSearchResults"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    // #305/#1572: null-őr
                    visible: (hostController && hostController.searchActive !== undefined)
                        ? (hostController.searchActive && !hostWindow.unnamedFacesOpen) : false
                    model: hostController ? hostController.searchGroups : []
                    spacing: 0

                    delegate: ColumnLayout {
                        id: groupDelegate
                        required property var modelData
                        width: groupedResults.width
                        spacing: 0

                        SearchGroupHeader {
                            Layout.fillWidth: true
                            section: groupDelegate.modelData.folderName
                        }

                        GridView {
                            id: subgrid
                            Layout.fillWidth: true
                            interactive: false
                            // #85: itt is kiegyenlített sor — az
                            // oszlopszám névleges méretből, a tényleges
                            // cellaWidth a szélességet tölti ki.
                            readonly property int nominalCellWidth:
                                hostWindow.thumbSize + 18
                            readonly property int columns: Math.max(
                                1, Math.floor(width / nominalCellWidth))
                            cellWidth: columns > 0
                                ? Math.floor(width / columns)
                                : nominalCellWidth
                            // #305: null-őr
                            cellHeight: hostWindow.thumbSize + 18
                                + ((hostController ? hostController.thumbCaptionMode : "none") !== "none"
                                   ? 16 : 0)
                            height: Math.ceil(
                                groupDelegate.modelData.photos.length
                                / columns) * cellHeight
                            model: groupDelegate.modelData.photos

                            delegate: ThumbDelegate {
                                id: groupedThumb
                                required property var modelData
                                width: subgrid.cellWidth
                                height: subgrid.cellHeight
                                // #85/#83: a kép a névleges méretre
                                // plafonozott
                                maxContentWidth: subgrid.nominalCellWidth
                                maxContentHeight: subgrid.cellHeight
                                name: modelData.name
                                thumbUrl: modelData.thumbUrl
                                star: modelData.star
                                caption: modelData.caption
                                isVideo: modelData.isVideo
                                hasEdits: modelData.hasEdits
                                hasGeo: modelData.hasGeo === true
                                // #463: arc-jelvények
                                hasFaces: modelData.hasFaces === true
                                hasFaceSuggestion:
                                    modelData.hasFaceSuggestion === true
                                // #455: a tálcán tartott kép
                                // jelvénye — a `heldCount` a
                                // reaktív trigger (a `photos.
                                // revision` mintája, ld. TrayBar).
                                held: hostController
                                      ? (hostController.heldCount,
                                         hostController.isHeldAt(modelData.row))
                                      : false
                                isHidden: modelData.hidden === true
                                index: modelData.row
                                dragRows: hostWindow.selectedIndexes
                                    && hostWindow.selectedIndexes.length
                                    ? hostWindow.selectedIndexes.slice()
                                    : [modelData.row]
                                keywords: modelData.keywords
                                resolution: modelData.resolution
                                // #305: null-őr
                                captionMode: hostController ? hostController.thumbCaptionMode : "none"
                                // #142: set-alapú lookup
                                selected: hostWindow.selectedSet[
                                    modelData.row] === true
                                onChosen: function(i, mods) {
                                    hostWindow.handleThumbClick(i, mods)
                                }
                                onOpened: function(i) {
                                    hostWindow.openPhotoViewer(i)
                                }
                                onContextMenuRequested: function(i, cx, cy) {
                                    hostWindow.openPhotoContextMenu(
                                        i, groupedThumb, cx, cy)
                                }
                            }
                        }
                    }
                    ScrollBar.vertical: PicasaScrollBar {}
                }

                // #26 (3. lépcső): a „Névtelenek" album — a bal
                // hasáb új sorára kattintva jelenik meg, a fő rács
                // helyén (ld. UnnamedFacesView.qml docstring)
                UnnamedFacesView {
                    id: unnamedFacesView
                    objectName: "unnamedFacesView"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: hostWindow.unnamedFacesOpen
                    mode: hostWindow.facesAlbumMode
                    faceScanController: hostWindow._faceScanController
                    onShowIgnoredRequested:
                        hostWindow.facesAlbumMode = "ignored"
                    onShowUnnamedRequested:
                        hostWindow.facesAlbumMode = "unnamed"
                    onNameSubmitted: function(faceId, name) {
                        hostPeoplePanel.nameFaceFromPanel(faceId, name, true)
                    }
                    onNamedSuggestionAccepted: Qt.callLater(
                        function() {
                            hostPeoplePanel.refreshHeaderPeopleSnapshot(true)
                        }
                    )
                }
            }
        }
    }
}
