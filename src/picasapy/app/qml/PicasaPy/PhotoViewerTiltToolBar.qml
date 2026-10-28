import QtQuick

// vágó-overlay a kép TÉNYLEGESEN kirajzolt (letterbox
// nélküli) területén. Enter: elfogad + következő kép a
// vágó-mód megtartásával (sorozat-vágás, UX-alapelv 1);
// Esc: kilép a vágásból. MVP-korlát: ini-forgatott
// (rotate=) képnél a koordináták a megjelenített térben
// értendők — a forgatás+vágás kombináció a #21-ben pontosodik.
// #3123: az eszköz-sáv a KÉP FÖLÖTT lebeg — az
// eredetiben az Alkalmaz/Mégse pár nem a bal panelben ül
// (`editpanel/tool_container: editpanel/preview`,
// `m_centerX`, `YConstraint 1, 1, -10`). A gombok a
// korábbi panel-gombok OBJEKTUMNEVÉT viszik tovább, hogy
// a rájuk épülő működés (és annak ellenőrzése) ne
// szakadjon meg.
//: #3741: a `photo` helyett a `photoArea.fokuszKep` a
//: szülő — a sáv a TÉNYLEGESEN szerkesztett félre kerül,
//: bal fókusznál a `photoElotte`-ra (ld. a `fokuszKep`
//: docsztringjét a `photo` alatt).
EditorToolBar {
    required property var photoArea
    id: editorToolBar
    objectName: "editorToolBar"
    textEntryHasFocus: photoArea.hostViewer.textEntryHasFocus
    parent: photoArea
    z: 20
    //: #3320: a sáv KIZÁRÓLAG a kiegyenesítésé. A
    //: `.tre` a `tool_container`-t a
    //: `#---Straighen Overlay---` szakaszfejléc alá
    //: teszi (`:1038`–`:1052`); a másik négy eszköz
    //: párja a SAJÁT paneljében ül (`crop_well`,
    //: `retouch_well`, `redeye_well`).
    tool: (photoArea.hostEditorPanel.tiltActive
           && photoArea.hostEditorPanel.activeTab === 0) ? "tilt" : ""
    //: a kiegyenesítés Alkalmaz gombja mindig aktív —
    //: a döntés értéke már ki van írva (#72)
    applyEnabled: true
    //: #3234: a döntés-csúszka tartománya — −1…1
    //: Picasa-egység (±11,5°)
    csuszkaMin: -1
    csuszkaMax: 1
    //: húzás közben ÉLŐ előnézet, ini-mentés nélkül
    //: (#72); a programozott szinkron (nyitás, lapozás)
    //: nem vált ki előnézetet (#131)
    onCsuszkaMozgott: (ertek) => {
        if (typeof editController !== "undefined" && editController
                && photoArea.hostEditorPanel.tiltActive && !photoArea.hostViewer.tiltSzinkronFut)
            editController.previewTilt(ertek)
    }
    //: #4058: az elengedés csak az előnézetet frissíti;
    //: menteni az Alkalmaz gomb fog.
    onCsuszkaElengedve: (ertek) => {
        if (typeof editController !== "undefined" && editController
                && photoArea.hostEditorPanel.tiltActive)
            editController.previewTilt(ertek)
    }
    //: A sáv a kép forgatása fölötti, forgatatlan rétegen
    //: marad. A képernyőn látható képrész négy sarkát
    //: leképezzük a forgatás utáni befoglaló téglalaphoz;
    //: a sáv közepe ehhez igazodik, az alsó rés 10×képskála.
    readonly property point kepernyoKozep:
    {
        var kep = photoArea.fokuszKep
        var kepBal = (kep.width - kep.paintedWidth) / 2
        var kepFelso = (kep.height - kep.paintedHeight) / 2
        var kepJobb = kepBal + kep.paintedWidth
        var kepAlso = kepFelso + kep.paintedHeight
        var sarkok = [
            kep.mapToItem(null, kepBal, kepFelso),
            kep.mapToItem(null, kepJobb, kepFelso),
            kep.mapToItem(null, kepBal, kepAlso),
            kep.mapToItem(null, kepJobb, kepAlso),
        ]
        var minX = Math.min(sarkok[0].x, sarkok[1].x,
                            sarkok[2].x, sarkok[3].x)
        var maxX = Math.max(sarkok[0].x, sarkok[1].x,
                            sarkok[2].x, sarkok[3].x)
        var maxY = Math.max(sarkok[0].y, sarkok[1].y,
                            sarkok[2].y, sarkok[3].y)
        var kepSkala = kep.scale
        //: A mapToItem() a transzformált sarkokat
        //: visszaadja, de a QML-kötés nem iratkozik fel
        //: a belső x/y/méret/scale/rotation olvasásokra.
        //: A nullával szorzott függőség frissíti a sávot
        //: lapozáskor, nagyításkor és átméretezéskor is.
        var fuggoseg = (kep.x + kep.y + kep.width
            + kep.height + kep.paintedWidth
            + kep.paintedHeight + kep.scale + kep.rotation) * 0
        return Qt.point(
            (minX + maxX) / 2 + fuggoseg,
            maxY - kepSkala * (height / 2 + 10)
                + fuggoseg)
    }
    readonly property point szuloKozep:
        parent.mapFromItem(
            null, kepernyoKozep.x, kepernyoKozep.y)
    x: Math.round(szuloKozep.x - width / 2)
    y: Math.round(szuloKozep.y - height / 2)
    rotation: 0
    scale: photoArea.fokuszKep.scale
    transformOrigin: Item.Center
    onApplyClicked: {
        //: #4058: a Kiegyenesítés egyetlen mentése az
        //: Alkalmazás. Változatlan értéknél ne keletkezzen
        //: fölösleges réteg vagy Visszavonás-lépés.
        if (tool === "tilt") {
            if (typeof editController !== "undefined" && editController
                    && editorToolBar.csuszkaErtek
                    !== photoArea.hostViewer.tiltErtekNyitaskor)
                editController.setTilt(
                    editorToolBar.csuszkaErtek)
            photoArea.hostViewer.tiltAlkalmazasFut = true
            photoArea.hostEditorPanel.tiltActive = false
            photoArea.hostViewer.tiltAlkalmazasFut = false
        }
    }
    onCancelClicked: {
        //: #4058: a Mégse a nyitáskori mentett láncot
        //: rendereli újra; a mentett lánc és az előzmény
        //: addig változatlan maradt.
        if (tool === "tilt")
            photoArea.hostEditorPanel.tiltActive = false
    }
}
