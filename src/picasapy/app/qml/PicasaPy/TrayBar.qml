import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Alsó sáv (#150-ben kiemelve a Main.qml-ből): kék infó-sáv (busy-
// animációval, #70) + kijelölés-tálca a művelet-gombokkal (Picasa).
// A kijelölés-állapot a főablaké (appWindow); a néző aktuális sorát a
// viewerIndex tulajdonság hozza.
Column {
    id: tray

    // a főablak (kijelölés-állapot + rotateTargetsAllVideo őr gazdája)
    required property var appWindow
    // a néző aktuális sora (a Main köti a photoViewer.currentIndex-re)
    property int viewerIndex: -1
    // az Exportálás gomb (a dialógus a Main.qml-ben él)
    signal exportRequested()
    // #361: Kollázs/Film a tálcáról (a dialógusok a Main.qml-ben élnek)
    signal collageRequested()
    signal movieRequested()

    // a forgatás/csillag célsora — a Main rotateTargetRow()-ja is ezt kéri
    readonly property int starTargetRow: trayStar.targetRow

    // #305: null-őr — a controller a QML-engine leépítésekor átmenetileg
    // null lehet, miközben ezek a kötések utoljára kiértékelődnek.
    readonly property var ctl: controller

    // tömör acélkék infó-sáv; kijelöléskor a kép adatai
    Rectangle {
        id: infoBar
        width: parent.width; height: 20
        color: Theme.infoBar
        clip: true

        // #70: lassan végigvonuló fény-hullám, amíg a PicasaPy a
        // háttérben dolgozik (indexelés, thumbnail-batch). XAnimator:
        // a render-szálon fut (a főszálat/GIL-t nem érinti, ld. #53),
        // idle-ben running=false → 0 CPU/GPU. Nem polloz: a
        // controller.isWorking jelzés-alapú (busyChanged).
        Rectangle {
            id: busySweep
            objectName: "busySweep"
            visible: tray.ctl ? tray.ctl.isWorking : false
            width: Math.max(80, infoBar.width / 5)
            height: infoBar.height
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "transparent" }
                GradientStop { position: 0.5; color: "#59ffffff" }
                GradientStop { position: 1.0; color: "transparent" }
            }
            XAnimator on x {
                running: busySweep.visible
                loops: Animation.Infinite
                from: -busySweep.width
                to: infoBar.width
                duration: 1800
            }
        }
        Text {
            anchors.centerIn: parent
            text: !tray.ctl ? "" : (tray.appWindow.viewerOpen
                  ? tray.ctl.viewerInfo(tray.viewerIndex)
                  : (tray.appWindow.selectedIndexes.length === 1
                     ? tray.ctl.photoInfo(tray.appWindow.selectedIndex)
                     : tray.ctl.statusText))
            color: Theme.infoBarText
            font.pixelSize: Theme.fontSize
            font.bold: true
        }
    }

    Rectangle {
        width: parent.width; height: 52
        color: Theme.trayBg
        Rectangle {
            width: parent.width; height: 1
            color: Theme.trayBorder
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10; anchors.rightMargin: 10
            spacing: 8

            // kijelölés-tálca: a kijelölt képek miniatűrjei (Picasa)
            Item {
                Layout.preferredWidth: 200
                Layout.preferredHeight: 46
                Flow {
                    anchors.fill: parent
                    spacing: 2
                    clip: true
                    Repeater {
                        model: tray.appWindow.selectedIndexes
                        delegate: Image {
                            required property var modelData
                            width: 20; height: 20
                            source: tray.ctl
                                ? tray.ctl.photos.thumbUrlAt(Number(modelData))
                                : ""
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                        }
                    }
                }
                Text {
                    visible: tray.appWindow.selectedIndexes.length === 0
                    anchors.centerIn: parent
                    text: qsTr("Selection")
                    color: Theme.placeholderText
                    font.pixelSize: Theme.fontSize
                }
            }

            PicasaButton {
                id: trayStar
                readonly property int targetRow: tray.appWindow.viewerOpen
                    ? tray.viewerIndex : tray.appWindow.selectedIndex
                readonly property bool multi:
                    !tray.appWindow.viewerOpen
                    && tray.appWindow.selectedIndexes.length > 1
                enabled: tray.appWindow.viewerOpen
                         || tray.appWindow.selectedIndex >= 0
                Layout.preferredWidth: 34
                onClicked: multi
                           ? controller.toggleStarMany(
                                 tray.appWindow.selectedIndexes)
                           : controller.toggleStar(targetRow)
                contentItem: Text {
                    objectName: "trayStarLabel"
                    text: "★"
                    font.pixelSize: 15
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    // arany, ha a kiválasztott kép csillagos; egyébként
                    // világos kontúr-csillag (Picasa-minta, nem fekete!)
                    color: (tray.ctl
                            ? (tray.ctl.photos.revision,
                               tray.ctl.photos.starAt(trayStar.targetRow))
                            : false)
                           ? Theme.starYellow : "#ffffff"
                    style: Text.Outline
                    styleColor: "#9a9a9a"
                }
            }
            PicasaButton {
                id: trayRotateLeftBtn
                objectName: "trayRotateLeft"
                text: "↺"
                // #103: csak-videó kijelölésnél tiltva (photos.revision:
                // modell-frissüléskor újraértékelt kötés)
                enabled: (tray.ctl ? tray.ctl.photos.revision : 0,
                          (tray.appWindow.viewerOpen
                           || tray.appWindow.selectedIndex >= 0)
                          && !tray.appWindow.rotateTargetsAllVideo())
                Layout.preferredWidth: 34
                onClicked: trayStar.multi
                           ? controller.rotateLeftMany(
                                 tray.appWindow.selectedIndexes)
                           : controller.rotateLeft(trayStar.targetRow)
                // #314: a PicasaButton alap-krómja (PicasaButton.qml) nem
                // témavezérelt — mindig világos bevel-gomb. Az alapértelmezett
                // contentItem az `ink`-et használná, ami sötét témán
                // kivilágosodik és eltűnne a világos gombháttéren; itt a
                // fix `Theme.iconInk`-kel felülírjuk (letiltva marad a
                // PicasaButton eredeti, szintén rögzített szürkéje).
                contentItem: Text {
                    objectName: "trayRotateLeftLabel"
                    text: trayRotateLeftBtn.text
                    font: trayRotateLeftBtn.font
                    color: trayRotateLeftBtn.enabled ? Theme.iconInk : "#9a9a9a"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
            PicasaButton {
                id: trayRotateRightBtn
                objectName: "trayRotateRight"
                text: "↻"
                enabled: (tray.ctl ? tray.ctl.photos.revision : 0,
                          (tray.appWindow.viewerOpen
                           || tray.appWindow.selectedIndex >= 0)
                          && !tray.appWindow.rotateTargetsAllVideo())
                Layout.preferredWidth: 34
                onClicked: trayStar.multi
                           ? controller.rotateRightMany(
                                 tray.appWindow.selectedIndexes)
                           : controller.rotateRight(trayStar.targetRow)
                // #314: ld. trayRotateLeftBtn indoklása fentebb.
                contentItem: Text {
                    objectName: "trayRotateRightLabel"
                    text: trayRotateRightBtn.text
                    font: trayRotateRightBtn.font
                    color: trayRotateRightBtn.enabled ? Theme.iconInk : "#9a9a9a"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
            Item { Layout.fillWidth: true }
            // nagyítás-csúszka − / + jelekkel (kézikönyv 06)
            Text { text: "−"; color: Theme.textGray; font.pixelSize: 13 }
            PicasaSlider {
                id: sizeSlider
                from: 72; to: 256; value: tray.appWindow.thumbSize
                Layout.preferredWidth: 140
                onMoved: tray.appWindow.thumbSize = value
            }
            Text { text: "+"; color: Theme.textGray; font.pixelSize: 13 }
            Item { width: 10 }
            // #361: a kimeneti sáv gombjai saját SVG-ikonnal (PBZ-leltár:
            // outputlayout/ebutton, /pbutton) — a felirat objectName-jei
            // (label szöveg, iconInk-szín) VÁLTOZATLANOK, csak egy Image
            // került a Text mellé (icons/PicasaButtonWithIcon mintája
            // lentebb, trayExportBtn-nél).
            PicasaButton {
                id: trayEmailBtn
                text: qsTr("E-Mail")
                enabled: false
                contentItem: Row {
                    spacing: 5
                    Image {
                        anchors.verticalCenter: parent.verticalCenter
                        source: "icons/email.svg"
                        sourceSize: Qt.size(14, 14)
                        opacity: trayEmailBtn.enabled ? 1.0 : 0.5
                    }
                    Text {
                        objectName: "trayEmailLabel"
                        anchors.verticalCenter: parent.verticalCenter
                        text: trayEmailBtn.text
                        font: trayEmailBtn.font
                        color: trayEmailBtn.enabled ? Theme.iconInk : "#9a9a9a"
                    }
                }
            }
            PicasaButton {
                id: trayPrintBtn
                text: qsTr("Print")
                enabled: false
                contentItem: Row {
                    spacing: 5
                    Image {
                        anchors.verticalCenter: parent.verticalCenter
                        source: "icons/print.svg"
                        sourceSize: Qt.size(14, 14)
                        opacity: trayPrintBtn.enabled ? 1.0 : 0.5
                    }
                    Text {
                        objectName: "trayPrintLabel"
                        anchors.verticalCenter: parent.verticalCenter
                        text: trayPrintBtn.text
                        font: trayPrintBtn.font
                        color: trayPrintBtn.enabled ? Theme.iconInk : "#9a9a9a"
                    }
                }
            }
            PicasaButton {
                id: trayExportBtn
                objectName: "trayExportButton"
                text: qsTr("Export")
                enabled: !tray.appWindow.viewerOpen
                         && tray.appWindow.selectedIndexes.length > 0
                onClicked: tray.exportRequested()
                // #314: a PicasaButton alap-krómja nem témavezérelt (ld.
                // trayRotateLeftBtn indoklása fentebb) — az ikon+felirat
                // tintája itt is a fix Theme.iconInk.
                contentItem: Row {
                    spacing: 5
                    Image {
                        anchors.verticalCenter: parent.verticalCenter
                        source: "icons/folder-export.svg"
                        sourceSize: Qt.size(14, 14)
                        opacity: trayExportBtn.enabled ? 1.0 : 0.5
                    }
                    Text {
                        objectName: "trayExportLabel"
                        anchors.verticalCenter: parent.verticalCenter
                        text: trayExportBtn.text
                        font: trayExportBtn.font
                        color: trayExportBtn.enabled ? Theme.iconInk : "#9a9a9a"
                    }
                }
            }
            Item { width: 6 }
            // #361: Kollázs / Film / Megosztás — a PBZ-leltár szerint
            // (outputlayout/collage, /makemovie, /sharewith) az eredeti
            // kimeneti sávnak is részei; a tényleges Létrehozás-funkció
            // a Create-menü mellett innen is indítható (collage/movie
            // signal → Main.qml → CreateDialogs); a Megosztás backend
            // híján tiltott helyőrző marad. Nincs
            // qsTr-tooltip: a "Picture Collage..."/"Movie"/"Share" szöveg
            // MÁR fordított a CreateDialogs/PicasaMenuBar/Main kontextusban
            // — új kontextusban újra felvéve a lupdate "unfinished"-nek
            // látná (test_i18n_completeness.py), az integrátor a menü-
            // pontokkal egy körben veheti fel ide is a fordítást.
            PicasaButton {
                id: trayCollageBtn
                objectName: "trayCollageButton"
                enabled: !tray.appWindow.viewerOpen
                         && tray.appWindow.selectedIndexes.length > 0
                onClicked: tray.collageRequested()
                Layout.preferredWidth: 30
                contentItem: Image {
                    objectName: "trayCollageIcon"
                    anchors.centerIn: parent
                    source: "icons/collage.svg"
                    sourceSize: Qt.size(16, 16)
                    opacity: trayCollageBtn.enabled ? 1.0 : 0.5
                }
            }
            PicasaButton {
                id: trayMovieBtn
                objectName: "trayMovieButton"
                enabled: !tray.appWindow.viewerOpen
                         && tray.appWindow.selectedIndexes.length > 0
                onClicked: tray.movieRequested()
                Layout.preferredWidth: 30
                contentItem: Image {
                    objectName: "trayMovieIcon"
                    anchors.centerIn: parent
                    source: "icons/movie.svg"
                    sourceSize: Qt.size(16, 16)
                    opacity: trayMovieBtn.enabled ? 1.0 : 0.5
                }
            }
            PicasaButton {
                id: trayShareBtn
                objectName: "trayShareButton"
                enabled: false
                Layout.preferredWidth: 30
                contentItem: Image {
                    objectName: "trayShareIcon"
                    anchors.centerIn: parent
                    source: "icons/share.svg"
                    sourceSize: Qt.size(16, 16)
                    opacity: 0.5
                }
            }
            Item { width: 6 }
            // az egyetlen zöld elsődleges tett — jobbra igazítva,
            // a képernyő vizuális súlypontja (kézikönyv 01/08)
            PicasaButton {
                id: trayUploadBtn
                text: qsTr("Upload to Google Photos")
                enabled: false
                accent: Theme.picasaGreen
                contentItem: Row {
                    spacing: 5
                    Image {
                        anchors.verticalCenter: parent.verticalCenter
                        source: "icons/upload.svg"
                        sourceSize: Qt.size(14, 14)
                    }
                    Text {
                        objectName: "trayUploadLabel"
                        anchors.verticalCenter: parent.verticalCenter
                        text: trayUploadBtn.text
                        font: trayUploadBtn.font
                        color: "white"
                    }
                }
            }
        }
    }
}
