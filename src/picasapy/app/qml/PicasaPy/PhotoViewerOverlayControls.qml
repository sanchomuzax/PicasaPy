import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: viewerOverlayControls
    anchors.fill: parent
    property var hostViewer: null
    property var hostPhotoArea: null
    readonly property var viewer: hostViewer
    readonly property var photoArea: hostPhotoArea
    readonly property var editorPanel: viewer.editorPanel
    readonly property var cropOverlay: viewer.cropOverlay
    readonly property var editorToolBar: viewer.editorToolBar
    readonly property var photo: viewer.photo
    readonly property var photoElotte: viewer.photoElotte
    readonly property var photoElotteKeret: viewer.photoElotteKeret
    readonly property var photoKeret: viewer.photoKeret
    readonly property var facesOverlay: viewer.facesOverlay
    readonly property var paintMaskArea: viewer.paintMaskArea
    readonly property var neutralPickArea: viewer.neutralPickArea
    readonly property var effectColorPickArea: viewer.effectColorPickArea
    readonly property var retouchClickArea: viewer.retouchClickArea
    readonly property var redeyeDragArea: viewer.redeyeDragArea
    readonly property var textClickArea: viewer.textClickArea
    property alias nextPreloadImage: elotoltoKovetkezo
    property alias previousPreloadImage: elotoltoElozo
    property alias hostViewerPanArea: viewerPanArea

        //: #3663: a „Kijelölve” jelvény - a KÉPEN KÍVÜL, a szürke
        //: margóban, a fókuszban lévő fél mellett, az osztó felőli
        //: oldalon (mérve: `docs/specs/ui-audit-editor.md` 3/b.3,
        //: élőben újramérve a `Colab EN 33`-`35` referenciákon).
        //: A #3013 a `photoArea` GYEREKEként, a `photo` ELÉ tette -
        //: ezért időnként a kép ALÁ került (a `photo` később
        //: rajzolódott rá), és a `photoArea` `clip: true`-ja levágta
        //: volna, ha a margóba lógna. Itt, a `photoArea` UTÁN,
        //: TESTVÉRKÉNT áll: garantáltan a kép fölött rajzolódik, és
        //: nem vágja le semmi.
        Rectangle {
            objectName: "viewerFocusBadge"
            visible: viewer.layoutMode !== "1up"
            //: #3663: MÉRT méret (`Colab EN 33`, 1280×1024): 86×26,
            //: enyhén lekerekített - NEM kapszula (a #3013 `height/2`
            //: sugara azt adott).
            width: viewer.jelvenySzel
            height: viewer.jelvenyMag
            radius: 4
            color: Theme.viewerFocusBadgeBg

            //: #3663: a helyet a KIRAJZOLT kép téglalapjából
            //: számoljuk (`paintedWidth`/`paintedHeight`), NEM a
            //: befoglaló `photoElotte`/`photo` dobozból - az utóbbi
            //: a `photoArea` felét kapja, de a kép azon belül
            //: KÖZÉPRE igazítva, letterboxolva jelenik meg
            //: (`PreserveAspectFit`), tehát a doboz éle és a kép
            //: éle jellemzően NEM esik egybe.
            readonly property var fokuszKep:
                viewer.aktivOldal === "bal" ? photoElotte : photo
            readonly property var fokuszKeret:
                viewer.aktivOldal === "bal" ? photoElotteKeret : photoKeret
            //: ⚠️ a `fokuszKep.x`/`.y` a SAJÁT felének keretéhez
            //: (`fokuszKeret`), az pedig a `photoArea`-hoz KÉPEST
            //: helyi (a `photo`/`photoElotte` a `photoArea` GYEREKE),
            //: a jelvény viszont a `photoArea` TESTVÉRE - tehát a
            //: KÖZÖS szülőhöz képesti koordinátához a `photoArea`
            //: saját eltolását is hozzá kell adni. Enélkül a jelvény
            //: pontosan a `photoArea` margójával (itt 14 px) tér el
            //: a várt helytől - ez okozta az első verzió 14 px-es
            //: eltérését minden mért esetben.
            //: #3741: a KÉPERNYŐN látszó méret - 90°/270°-os
            //: forgatásnál (`iniSteps` páratlan) a kirajzolt
            //: szélesség és magasság helyet cserél.
            readonly property bool forgatott: fokuszKep.iniSteps % 2 !== 0
            readonly property real kepSzel: forgatott
                ? fokuszKep.paintedHeight : fokuszKep.paintedWidth
            readonly property real kepMag: forgatott
                ? fokuszKep.paintedWidth : fokuszKep.paintedHeight
            readonly property real kepBal: photoArea.x + fokuszKeret.x
                + fokuszKep.x + (fokuszKep.width - kepSzel) / 2
            readonly property real kepJobb: kepBal + kepSzel
            readonly property real kepFent: photoArea.y + fokuszKeret.y
                + fokuszKep.y + (fokuszKep.height - kepMag) / 2
            readonly property real kepLent: kepFent + kepMag

            //: #3663: a `Colab EN 33`/`34` (vízszintes) és `35`
            //: (függőleges) referenciákon mért rés - mindkét
            //: elrendezésben ugyanaz a két állandó adja vissza a
            //: mért 60/62/27/61/26 px-es réseket: a KÉPEK SÍKJÁVAL
            //: PÁRHUZAMOS tengelyen (vízszintesben az osztó felé,
            //: függőlegesben a bal margó felé) ~61 px, a MERŐLEGES
            //: tengelyen (vízszintesben fölfelé a margóba,
            //: függőlegesben az osztó felé) ~27 px.
            readonly property int parhuzamosRes: viewer.jelvenyParhuzamosRes
            readonly property int merolegesRes: viewer.jelvenyMerolegesRes

            x: viewer.fuggolegesElrendezes
                ? kepBal - width - parhuzamosRes
                : (viewer.aktivOldal === "bal"
                   ? kepJobb - parhuzamosRes - width
                   : kepBal + parhuzamosRes)
            //: #3756: a helyét a két fél illesztése tartja fenn
            //: (`viewer.illesztesiDoboz`) - álló képnél felül, széles
            //: képnél függőlegesen balra -, így a jelvény a kép arányától
            //: függetlenül a mért résen áll, és nem takarja sem a felső
            //: sávot, sem a bal panelt, sem a képet.
            y: viewer.fuggolegesElrendezes
                ? (viewer.aktivOldal === "bal"
                   ? kepLent - merolegesRes - height
                   : kepFent + merolegesRes)
                : kepFent - height - merolegesRes

            Text {
                id: jelvenySzoveg
                anchors.centerIn: parent
                text: qsTr("Selected")
                font.pixelSize: Theme.fontSize - 2
                font.bold: true
                color: "#ffffff"
            }
        }

        // #6: nagyított képen húzással pásztázás; dupla katt = fit.
        // #4499: a bekapcsolt egykattintásos kilépés csak egyképes,
        // nem Kiegyenesítéses illesztett nézetben kapja meg a szabad
        // előnézeti területet; a nagyított pásztázás minden nézetben él.
        MouseArea {
            id: viewerPanArea
            objectName: "viewerPanArea"
            // #4078: a `photoArea` belső rétegében a pásztázó a
            // képek fölött, a Kiegyenesítés sávja (z=20) alatt áll.
            // Így a képen húzás - kettős nézetben a képi TapHandler
            // fölött is - továbbra is pásztáz, a sáv pedig megkapja
            // a saját kattintásait és csúszkahúzását.
            parent: photoArea
            anchors.fill: parent
            z: 10
            enabled: (viewer.zoomFactor > 1.01
                      || (viewer.singleClickExitEnabled
                          && viewer.layoutMode === "1up"
                          && !editorPanel.tiltActive))
                     && !editorPanel.cropActive
                     && !viewer.isCurrentVideo
            cursorShape: viewer.zoomFactor > 1.01
                         ? Qt.OpenHandCursor : Qt.ArrowCursor
            property real lastX: 0
            property real lastY: 0
            property real pendingSingleClickX: 0
            property real pendingSingleClickY: 0
            property bool dragged: false
            property bool exitAfterDoubleClick: false
            // Tesztből olvasható diagnosztika: a platformfüggő
            // egéresemény-út vizsgálatához a próba a kezelő ágát és
            // a lenyomás előtti időzítő-állapotot olvassa ki.
            property int pressEventCount: 0
            property bool timerRunningOnLastPress: false
            property string lastPressBranch: "not-pressed"

            // #4499: a beállított egykattintásos kilépés a Qt
            // dupla-kattintási időablakának lejártakor zár. Így a
            // dupla kattintás második eseménye még a nézőé marad.
            Timer {
                id: singleClickExitTimer
                objectName: "singleClickExitTimer"
                interval: Qt.styleHints.mouseDoubleClickInterval
                onTriggered: {
                    if (viewer.singleClickExitEnabled
                            && viewer.layoutMode === "1up"
                            && !editorPanel.tiltActive)
                        viewer.kerBezaras()
                }
            }

            // #4083: a nagyított nézet pásztázója fölé került, így
            // az aktív képi MouseArea-k lenyomását is elkapta. A
            // lenyomást csak akkor engedjük tovább, ha a ténylegesen
            // látható/aktív képi átfedő területére esik; a többi
            // képpont és a képen kívüli sáv továbbra is pásztázható.
            function benneVan(item, x, y) {
                if (!item || !item.visible || !item.enabled) return false
                var pont = item.mapFromItem(viewerPanArea, x, y)
                return pont.x >= 0 && pont.y >= 0
                       && pont.x < item.width && pont.y < item.height
            }
            function aktivAtfedoAlatt(x, y) {
                return benneVan(paintMaskArea, x, y)
                    || benneVan(neutralPickArea, x, y)
                    || benneVan(effectColorPickArea, x, y)
                    || benneVan(retouchClickArea, x, y)
                    || benneVan(redeyeDragArea, x, y)
                    || benneVan(textClickArea, x, y)
                    || (facesOverlay.editMode
                        && benneVan(facesOverlay, x, y))
            }
            function lathatoKepAlatt(item, frame, x, y) {
                if (!benneVan(item, x, y)) return false
                var pont = frame.mapFromItem(viewerPanArea, x, y)
                return pont.x >= 0 && pont.y >= 0
                       && pont.x < frame.width
                       && pont.y < frame.height
            }
            function fokuszKattintas(x, y) {
                if (viewer.layoutMode === "1up") return
                // Nagyításkor a kép Image-doboza átlóghat a saját
                // felén, miközben a keret levágja a túlnyúló részt.
                // A fókuszt csak a ténylegesen látható képrész váltsa.
                if (lathatoKepAlatt(
                            photoElotte, photoElotteKeret, x, y)) {
                    viewer.fokuszValt("bal")
                    return
                }
                if (lathatoKepAlatt(photo, photoKeret, x, y))
                    viewer.fokuszValt("jobb")
            }
            onPressed: function(event) {
                pressEventCount += 1
                timerRunningOnLastPress = singleClickExitTimer.running
                dragged = false
                if (aktivAtfedoAlatt(event.x, event.y)) {
                    lastPressBranch = "active-overlay"
                    event.accepted = false
                    return
                }
                // Windows-on a MouseButtonDblClick eljuthat az
                // ablakig úgy is, hogy a MouseArea doubleClicked
                // jelzése kimarad. Az első kattintás időzítője még
                // fut a második lenyomáskor; ezt a másik eseményutat
                // is dupla kattintásként zárjuk le.
                if (singleClickExitTimer.running
                        && Math.abs(event.x - pendingSingleClickX)
                           <= Qt.styleHints.mouseDoubleClickDistance
                        && Math.abs(event.y - pendingSingleClickY)
                           <= Qt.styleHints.mouseDoubleClickDistance
                        && viewer.singleClickExitEnabled
                        && viewer.layoutMode === "1up"
                        && !editorPanel.tiltActive) {
                    lastPressBranch = "second-press-exit"
                    singleClickExitTimer.stop()
                    exitAfterDoubleClick = true
                } else {
                    lastPressBranch = "accepted"
                }
                lastX = event.x; lastY = event.y
            }
            onPositionChanged: function(event) {
                if (!pressed) return
                if (Math.abs(event.x - lastX) + Math.abs(event.y - lastY) > 4)
                    dragged = true
                if (viewer.zoomFactor > 1.01) {
                    viewer.panX += event.x - lastX
                    viewer.panY += event.y - lastY
                    viewer.clampPan()
                }
                lastX = event.x; lastY = event.y
            }
            onClicked: function(event) {
                if (exitAfterDoubleClick) return
                if (dragged) return
                if (viewer.singleClickExitEnabled
                        && viewer.layoutMode === "1up"
                        && !editorPanel.tiltActive) {
                    pendingSingleClickX = event.x
                    pendingSingleClickY = event.y
                    singleClickExitTimer.restart()
                    return
                }
                fokuszKattintas(event.x, event.y)
            }
            onDoubleClicked: function(event) {
                if (viewer.singleClickExitEnabled
                        && viewer.layoutMode === "1up"
                        && !editorPanel.tiltActive) {
                    singleClickExitTimer.stop()
                    // A MouseArea a második lenyomáskor jelzi a dupla
                    // kattintást. Elfogadott jelzésnél elnyomja a második
                    // kattintás released/clicked jelzéseit is, ezért a
                    // kiengedésre időzített bezárás nem futna le.
                    exitAfterDoubleClick = true
                    // Engedjük kiadni a második kattintás jelzéseit:
                    // az onClicked a fenti jelzővel őrzi a nézőt, az
                    // onReleased pedig a kiengedés UTÁN zárja be.
                    event.accepted = false
                } else {
                    viewer.zoomFit()
                }
            }
            onReleased: {
                if (!exitAfterDoubleClick) return
                exitAfterDoubleClick = false
                Qt.callLater(function() { viewer.kerBezaras() })
            }
        }

        BusyIndicator {
            anchors.centerIn: parent
            running: photo.status === Image.Loading
        }

        ZoomNavigator {
            objectName: "zoomNavigator"
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.rightMargin: 8
            anchors.bottomMargin: captionBar.visible
                ? captionBar.height + 8 : 8
            visible: !viewer.quickViewerMode
                     && viewer.zoomFactor > 1.01
                     && !viewer.isCurrentVideo
                     && !viewer.zoomNavigatorDismissed
            imageSource: photoArea.fokuszKep.source
            imageAspect: photoArea.fokuszKep.paintedHeight > 0
                ? photoArea.fokuszKep.paintedWidth
                  / photoArea.fokuszKep.paintedHeight : 1
            imageRotation: photoArea.fokuszKep.rotation
            zoomFactor: viewer.zoomFactor
            zoomPercent: viewer.zoomFactor
                / Math.max(0.01, viewer.actualZoomFactor()) * 100
            viewRect: viewer.zoomNavigatorViewRect
            onPanRequested: function(deltaX, deltaY) {
                viewer.panFromZoomNavigator(deltaX, deltaY)
            }
            onCloseRequested: viewer.zoomNavigatorDismissed = true
        }

        // #1072 - `editpanel/render_now` („Létrehozás"): a PISZKOZAT
        // külön befejező lépése. A `projectutils::draft_collage`
        // szövege erre a gombra hivatkozik: a megosztás és a
        // nyomtatás feltétele, hogy a felhasználó megnyomja.
        //
        // A HELYE mért, nem választott (spec 4.3, `editpanel.tre`):
        // az `overlay_group` gyereke, tehát a kép FÖLÖTTI réteg -
        // a bélyegképen nincs rajta, csak a JPEG-be égetett
        // „PISZKOZAT" felirat. Vízszintesen középen (`m_centerX`),
        // függőlegesen a saját közepe a szülő 87,5%-án
        // (`YConstraint 0.5, 0.875, 0`).
        //
        // ⚠️ Renderelés közben az eredeti ugyanide teszi a
        // „Folyamatban..." feliratot (`editpanel/in_progress_label`)
        // - a kettő EGYMÁS HELYÉRE lép, ezért egyetlen elem
        // felirata változik, nem két külön gomb.
        PicasaButton {
            id: piszkozatLetrehozas
            objectName: "viewerCreateNowButton"
            //: `editpanel/render_now` / `editpanel/in_progress_label`
            text: viewer.controllerReady && controller.collageRendering
                  ? qsTr("In Progress...") : qsTr("Create Now")
            enabled: !(viewer.controllerReady
                       && controller.collageRendering)
            font.pixelSize: Theme.fontSize
            visible: !viewer.quickViewerMode
                     && viewer.currentIsCollageDraft
            x: (parent.width - width) / 2
            y: parent.height * 0.875 - height / 2
            ToolTip.text: qsTr("Render the final collage from this draft")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: controller.finishCollageDraft(
                viewer.currentFilePath)
        }

        // #2564: a nagyítás-hármas (illesztés · 1:1 · csúszka) ELKERÜLT
        // innen az ALSÓ ESZKÖZSÁVBA (`TrayBar.qml`,
        // `trayViewerZoomRow`) - mérve az `editpanel.tre:1288-1324`
        // horgonyai és a `respack.yt` x-tartományai szerint az
        // eredetiben a könyvtár nagyító + bélyegkép-csúszka
        // párjának a HELYÉN ül, nem a fotó fölött lebegve.
        //
        // Ez a doboz a MI KÉT arc-gombunké maradt (`☺` és `✎`):
        // ezek nincsenek az eredetiben (saját döntés, #147/#26), és
        // a #2564 kifejezetten hatókörön kívül hagyta őket. A
        // lebegő forma nekik marad, mert a fotón értelmezett
        // állapotot kapcsolnak.
        Rectangle {
            id: facesBar
            objectName: "viewerFacesBar"
            //: VÁLTOZATLAN feltétel: ugyanaz, ami a korábbi
            //: `zoomBar`-t vezérelte - videón nincs arc-keret,
            //: vágás közben pedig a fotó fölötti réteg tiszta.
            visible: !viewer.quickViewerMode
                     && viewer.photoOverlaysUsable
            anchors.right: parent.right
            anchors.rightMargin: 4
            //: #2565: a felirat-sáv FÖLÉ, nem rá. A sáv a fotó
            //: alján végigfut (mérve), és a lebegő doboz eddig
            //: eltakarta a sáv jobb szélén ülő kukát - a kirajzolt
            //: képen látszott, számolásból nem derült volna ki.
            anchors.bottom: captionBar.visible
                            ? captionBar.top : parent.bottom
            anchors.bottomMargin: 4
            width: facesRow.width + 12
            height: 26
            radius: 4
            color: "#00000059"
            Row {
                id: facesRow
                anchors.centerIn: parent
                spacing: 4
                // #147: arc-keretek be/ki (F billentyűvel egyenértékű)
                PicasaButton {
                    objectName: "facesToggleButton"
                    text: "☺"
                    checkable: true
                    checked: viewer.facesVisible
                    width: 26; height: 20
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Show Faces")
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: viewer.toggleFaces()
                }
                // #26 (2. kör): arc-SZERKESZTŐ mód be/ki
                // (Shift+F billentyűvel egyenértékű) - videónál
                // nincs értelme, ott letiltjuk.
                PicasaButton {
                    objectName: "facesEditToggleButton"
                    text: "✎"
                    checkable: true
                    checked: viewer.facesEditMode
                    enabled: !viewer.isCurrentVideo
                    width: 26; height: 20
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Edit Faces")
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: viewer.toggleFacesEdit()
                }
            }
        }
        // szerkeszthető felirat-sor - a model.revision referencia
        // miatt a kötés modell-frissítésnél (pl. mentés után)
        // újraértékelődik, ahogy a forgatás-kötés is (lásd fent).
        // Gépeléskor a Qt eltávolítja a deklaratív kötést a text
        // property-ről (közvetlen C++ írás), ezért elfogadás és
        // Esc után Qt.binding()-gel újra be kell kötni, különben a
        // mező a következő navigáláskor nem frissülne.
        // #1816: a felirat-sáv KÉT vezérlője. Az eredetiben a
        // `captionbutton` („Show/Hide Caption") és a `captiontrash`
        // („Delete this caption") - a `0x0057bb50` kezelő a
        // `captionbutton` · `caption` · `captiontrash` hármast
        // EGYÜTT kezeli.
        //
        // ⚠️ A jegy KÉT belépési pontot ír elő (`editpanel/` és
        // `editoneup/captionbutton`). Nálunk a szerkesztő panel a
        // NÉZŐN BELÜL él (`EditorPanel` ugyanebben a fájlban), tehát
        // ez az EGY sáv mindkét állapotot kiszolgálja - mérve, nem
        // feltételezve: a sáv `visible`-je csak a vágásra és a
        // videóra érzékeny, a szerkesztő nyitottságára nem.
        // #2565 + #2587: a KÉPALÁÍRÁS-SÁV. A mérce a tulajdonos NÉGY
        // felvétele (`research/felirat-ki-bekapcsolva/`, 1920 × 1080,
        // Picasa 3 és PicasaPy, felirat BE és KI állapotban).
        //
        // A `.tre` kényszerei (`editpanel.tre:1238-1266`):
        //   `captionbutton`  `XConstraint 0, 0, 3`   `Y 1, 1, -3`
        //   `caption`        `X 0, 0, 25` … `1, 1, -24`
        //   `captiontrash`   `XConstraint 1, 1, -3`  `Y 1, 1, -3`
        //   `captionbase` / `captionbasetop`: a sáv HÁTTERE
        //     (`predraw 1`), teljes szélességben.
        //
        // ⚠️ A `captionbutton` `hidetarget`-je a `caption` és a
        // `captiontrash` - **magát a gombot nem**. A felvételen ez
        // pontosan így látszik: kikapcsolt feliratnál a SÁV eltűnik,
        // a kapcsoló viszont OTT MARAD a kép bal alsó sarkában.
        // Ezért ül a gomb a fotó-terület rétegén, nem a sávban.
        Item {
            id: captionBar
            objectName: "captionBar"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            //: MÉRT magasság: a felvételen a csík y 906…926 (21 px).
            height: 21
            visible: viewer.captionVisible && !viewer.quickViewerMode

            //: `captionbase` + `captionbasetop` - a sáv saját
            //: háttere. MÉRVE: a felvételen `#c6c6c6`, vagyis a
            //: KRÓM világosszürkéje, nem a fotó-terület szürkéje és
            //: nem sötét. Sötét témában a króm sötét párja.
            Rectangle {
                id: captionBarBackground
                objectName: "captionBarBackground"
                anchors.fill: parent
                color: Theme.captionBar
            }

            TextInput {
                id: captionField
                objectName: "captionField"
                //: `caption`: a két gomb KÖZÖTT, a sáv teljes
                //: maradékán - az eredetin a felirat a sáv
                //: közepén áll, FÉLKÖVÉREN és sötéten.
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.leftMargin: 25
                anchors.rightMargin: 24
                anchors.verticalCenter: parent.verticalCenter
                horizontalAlignment: TextInput.AlignHCenter
                color: Theme.captionBarText
                font.pixelSize: Theme.fontSize
                font.bold: true
                selectByMouse: true
                text: viewer.photosModel
                    ? (viewer.photosModel.revision,
                       viewer.photosModel.captionAt(viewer._kijeloltSort()))
                    : ""

                function rebind() {
                    text = Qt.binding(function () {
                        return viewer.photosModel
                            ? (viewer.photosModel.revision,
                               viewer.photosModel.captionAt(viewer._kijeloltSort()))
                            : ""
                    })
                }

                onAccepted: {
                    controller.setCaption(viewer._kijeloltSort(), text)
                    rebind()
                    viewer.forceActiveFocus()
                }
                Keys.onEscapePressed: (event) => {
                    rebind()
                    viewer.forceActiveFocus()
                    event.accepted = true
                }
            }

            //: A felszólítás a SÁVBAN áll, a felirat helyén - az
            //: eredetin („Készítsen képaláírást!") ugyanott, ahol a
            //: kész felirat lenne (a `235707.jpg` felvételen
            //: közvetlenül összevethető).
            Text {
                objectName: "captionPlaceholder"
                anchors.centerIn: parent
                text: qsTr("Make a caption!")
                color: Theme.captionBarText
                opacity: 0.7
                font.pixelSize: Theme.fontSize
                visible: captionField.text.length === 0
                         && !captionField.activeFocus
            }

            ToolButton {
                objectName: "captionTrashButton"
                anchors.right: parent.right
                anchors.rightMargin: 3
                anchors.verticalCenter: parent.verticalCenter
                flat: true
                implicitWidth: 17
                implicitHeight: 13
                text: "✕"
                //: `captiontrash` - az eredeti buboréksúgója
                ToolTip.text: qsTr("Delete this caption")
                ToolTip.visible: hovered
                ToolTip.delay: Theme.tooltipDelay
                // üres feliratot nincs mit törölni
                enabled: captionField.text.length > 0
                contentItem: Text {
                    text: parent.text
                    color: Theme.captionBarText
                    opacity: parent.enabled ? (parent.hovered ? 1 : 0.7) : 0.3
                    font.pixelSize: Theme.fontSize - 2
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Item {}
                // #1816 DÖNTÉS: NINCS megerősítés. Az eredetiben ez
                // szemetes-ikon közvetlen hatással, és a művelet nem
                // lemezromboló: a felirat egyetlen mező,
                // újragépelhető. A projekt #459-es elve a
                // megerősítést a lemezt érintő, visszafordíthatatlan
                // műveletekre tartja fenn. (Az eredetiről ez NINCS
                // mérve - saját döntés.)
                onClicked: {
                    controller.setCaption(viewer._kijeloltSort(), "")
                    captionField.rebind()
                }
            }
        }

        // #2587: a felirat-KAPCSOLÓ a fotó-terület BAL ALSÓ sarkában,
        // a sáv állapotától FÜGGETLENÜL. A `.tre` szerint a
        // `captionbutton` `hidetarget`-je csak a `caption` és a
        // `captiontrash`; a felvételen kikapcsolt feliratnál is ott
        // áll a kis világos négyzet - ez az EGYETLEN út vissza.
        //
        // MÉRT geometria (`picasa3-felirat-*.jpg`, mindkét állapotban
        // AZONOS): a fehér doboz x 287…303, y 910…922 - vagyis
        // **17 × 13**, a fotó-terület bal szélétől 1 képponttal, a
        // sáv függőleges közepén.
        //
        // KÉT ÁLLAPOT (`editoneup/caption_icon` és
        // `caption_yesicon`, `oneup.tre:112-124`): bekapcsolt
        // feliratnál a dobozban két vízszintes vonal, kikapcsoltnál
        // ÜRES a doboz. A felvételen pontosan ez látszik.
        Rectangle {
            id: captionToggle
            objectName: "captionToggleButton"
            anchors.left: parent.left
            anchors.leftMargin: 1
            anchors.bottom: parent.bottom
            anchors.bottomMargin: viewer.captionVisible
                                  ? (captionBar.height - height) / 2 : 4
            width: 17
            height: 13
            radius: 2
            visible: viewer.photoOverlaysUsable
                     && !viewer.quickViewerMode
            color: Theme.captionToggleBg
            border.width: 1
            border.color: viewer.captionVisible
                          ? Theme.captionToggleBorder : "transparent"

            //: `caption_icon`: két vízszintes vonal - CSAK bekapcsolt
            //: feliratnál (a kikapcsolt állapot doboza üres).
            Column {
                anchors.centerIn: parent
                spacing: 3
                visible: viewer.captionVisible
                Repeater {
                    model: 2
                    Rectangle {
                        width: 9
                        height: 1
                        color: Theme.captionToggleBorder
                    }
                }
            }

            ToolTip.text: qsTr("Show/Hide Caption")
            ToolTip.visible: egerTerulet.containsMouse
            ToolTip.delay: Theme.tooltipDelay
            MouseArea {
                id: egerTerulet
                anchors.fill: parent
                //: a MÉRT doboz 17 × 13 - kicsi a kényelmes
                //: találathoz, ezért az érzékeny terület nagyobb, a
                //: RAJZ viszont a mért méretű marad
                anchors.margins: -5
                hoverEnabled: true
                onClicked: viewer.billentsdAFeliratot()
            }
        }


        // elő-betöltés: a szomszédok már dekódolva, mire lépsz -
        // a #84 óta a mappán belüli szomszéd (folderNeighbor), nem
        // a nyers currentIndex±1, hogy ne a szomszéd mappa képét
        // töltsük elő feleslegesen a mappahatárnál
        Image {
            id: elotoltoKovetkezo
            objectName: "viewerPreloadNext"
            visible: false
            //: #3877: forrás és forrásméret EGYÜTT (`viewer._betolt`);
            //: a `fillMode` a `photo`/`photoElotte`-é, különben a Qt
            //: gyorstára nem találna (#3832).
            readonly property var betoltes: viewer._elotoltoPar(1)
            onBetoltesChanged: Qt.callLater(viewer._betoltesekIrasa)
            Component.onCompleted: viewer._betolt(elotoltoKovetkezo, betoltes)
            fillMode: Image.PreserveAspectFit
            asynchronous: Qt.platform.pluginName !== "offscreen"; autoTransform: true
        }
        Image {
            id: elotoltoElozo
            objectName: "viewerPreloadPrev"
            visible: false
            readonly property var betoltes: viewer._elotoltoPar(-1)
            onBetoltesChanged: Qt.callLater(viewer._betoltesekIrasa)
            Component.onCompleted: viewer._betolt(elotoltoElozo, betoltes)
            fillMode: Image.PreserveAspectFit
            asynchronous: Qt.platform.pluginName !== "offscreen"; autoTransform: true
        }

        // #4183: a bal fiók függőleges peremén marad, és becsukás
        // után is visszanyitható. A méretet az eredeti mérés adja.
        ToolButton {
            objectName: "toggle_left_drawer"
            visible: !viewer.quickViewerMode
            x: 1
            anchors.verticalCenter: parent.verticalCenter
            width: 15
            height: 16
            z: 20
            flat: true
            text: viewer.editorDrawerOffset === 0 ? "‹" : "›"
            ToolTip.text: qsTr("Show/Hide Edit Controls")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            contentItem: Text {
                text: parent.text
                color: Theme.panelHeaderText
                font.pixelSize: 17
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Item {}
            onClicked: viewer.toggleEditorDrawer()
        }
}
