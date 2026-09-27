import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "Beállítások" (options.fen) — a Picasa legnagyobb preferencia-
// dialógusa, a docs/specs/picasa-fen-dialogs.md 3.11. szakaszában
// dokumentált 8 fül szerint (a forrás-doksi fejléce "9 fül"-et említ, de
// a widget-fa csak 8 fület ír le részletesen — ld. az issue jelentését).
//
// A dialógus a MoveDatabaseDialog.qml (#368) mintáját követi: önálló,
// mozgatható/átméretezhető Window, a Main.qml-be illesztés (Eszközök →
// Beállítások... menüpont bekötése) az integrátoré.
//
// MA csak az "General" fülön van élő vezérlő (nyelv, törlés-megerősítés
// elnyomása) — a többi fül a FEN-struktúra kedvéért épül fel, de tiltott,
// mert a mögöttes funkció nincs meg a PicasaPy-ban (ld. az egyes
// OptionsTab*.qml fájlok fejléc-kommentjeit).
Window {
    id: optionsWindow
    objectName: "optionsDialog"
    title: qsTr("Options")
    modality: Qt.ApplicationModal

    //: #3544: a Shift+F1 fejezete. Külön ablakos, modális párbeszéd: a
    //: főablak súgója mögé kerülne, ezért a `WindowHelp` a párbeszéd FÖLÖTT,
    //: külön ablakban nyitja.
    property string helpTopic: "features/beallitasok.md"
    WindowHelp { tema: optionsWindow.helpTopic }
    // #3661 (2. lelet): az eredeti 560 px-es alapszélesség belső
    // tartalomterülete (536 px) kisebb, mint a 8 magyar fülcím összesen
    // igényelt szélessége (mérve, a csomagolt Open Sans-szal/`PicasaStyle`-
    // lal: ~646 px) — a fülsor emiatt a MEGNYITÁSKOR is levágta a jobb
    // szélső füleket, a korábbi „mindegyik látszik, csak összeszűkítve"
    // viselkedés helyett (regresszió a main-hez képest). A 680 px innen
    // számolt, ~10 px tartalékkal (646 + 2×12 margó + tartalék) — ennyin a
    // fülsor a MEGNYITÁSKOR görgetés nélkül mutatja mind a 8 fület.
    //
    // ⚠️ SZÁNDÉKOSAN NEM futásidőben, `tabBar.implicitWidth`-ből számolt
    // érték: a `Component.onCompleted`-ben mért `implicitWidth` a lenti
    // `leftPadding`/`rightPadding`-et is tartalmazza, ami az EREDETI (ekkor
    // még 560 px-es, túlcsorduló) szélességen már felvette a nyilak 44 px-es
    // tartalékát — ez a mérést önmagát felfújva 714 px-es eredményt adott.
    // A `tabBar.contentItem.contentWidth` (a paddingtől független, tényleges
    // tartalomszélesség) `Component.onCompleted`-kori értéke pedig a belső
    // `ListView` még be nem fejeződött kezdeti elrendezése miatt volt
    // megbízhatatlan (641 px-es, MÉG TÚLCSORDULÓ eredményt adott). A fix
    // szám ezt a két buktatót kerüli el.
    width: 680
    height: 460
    minimumWidth: 480
    minimumHeight: 360
    color: Theme.canvasBg

    function open() {
        optionsWindow.visible = true
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        // #3661 (2. lelet): 480 px-en a 8 magyar fülcím nem fér ki a
        // fülsoron — a fülsor GÖRGETHETŐ (a `TabBar` belső `ListView`-ja
        // húzással/egérkerékkel amúgy is mozgatható), de érintő/kerék
        // nélkül ez láthatatlan maradna. A két nyíl LÁTHATÓVÁ teszi a
        // görgetést, és kattintással is elérhetővé.
        //
        // ⚠️ A nyilak RÁFEDVE ülnek a fülsor két szélére (nem egy
        // RowLayout külön oszlopaiban) — egy `RowLayout`-beli gomb
        // LÁTHATATLANUL IS helyet foglalna (a QtQuick.Layouts nem hagyja ki
        // az invisible elemet a méretezésből, csak a `Layout.
        // alwaysStayInLayout` ELLENKEZŐJÉVEL lehetne kihagyatni), ami
        // önmagát beteljesítő túlcsordulást okozott: a gombok helyfoglalása
        // összeszűkítette a fülsort ÉPP ANNYIRA, hogy az így már valóban
        // túlcsordult, tehát a gombok LÁTHATÓVÁ váltak AKKOR IS, amikor a
        // teljes fülsor görgetés nélkül elfért volna (mérve: az akkori
        // próba-alapméreten, ahol enélkül semmi nem lógott volna ki, a
        // gombok mégis megjelentek). A ráfedés elkerüli ezt: a
        // `TabBar` `anchors.fill`-lel mindig a teljes rendelkezésre álló
        // szélességet kapja (a `tulcsordul` számítása is EZT — a padding
        // nélküli `tabBar.width`-et — hasonlítja a tartalom szélességéhez,
        // tehát a nyilak megjelenése MAGA nem befolyásolja a saját
        // feltételét). A `tabBar.leftPadding`/`rightPadding` csak a BELSŐ
        // látható sávot szűkíti a nyilak szélességével, amikor kell — ez
        // biztosítja, hogy a kiválasztott fül a nyilak ALÁ sose fusson be.
        Item {
            id: tabBarRow
            Layout.fillWidth: true
            implicitHeight: tabBar.implicitHeight
            Layout.preferredHeight: tabBar.implicitHeight

            TabBar {
                id: tabBar
                objectName: "optionsTabBar"
                anchors.fill: parent
                // #3661: a Fusion-stílus a fülgombok szélességét egyenlő
                // részekre osztaná (`bar.width / count`), és a fülcím-Text nem
                // tördelődik/nem "elide"-olódik — a magyar feliratok ezért
                // szomszédos fülekre folynának át, a legkijjebbi pedig a fülsor
                // szélén túl. A `width: implicitWidth` kikapcsolja az egyenlő
                // osztást (minden fül a saját feliratának megfelelő szélességet
                // kapja), a `clip: true` pedig a fülsoron túli részt levágja —
                // így 480 px-en a fülsor GÖRGETHETŐ (a ListView már flickelhető)
                // lesz, nem kilógó vagy egymást átfedő. A lenti
                // `leftPadding`/`rightPadding` a nyilak SZÉLESSÉGÉVEL szűkíti
                // a belső látható sávot túlcsordulás esetén, hogy a nyilak
                // SOSE takarják a kiválasztott fül feliratát.
                //
                // ⚠️ A Fusion `TabBar` SAJÁT (a `highlightRangeMode`-ból
                // adódó) görgetése MÉRVE margót hagy a kiválasztott fül elé
                // MÉG A LEGELSŐ fülnél is (0. index esetén ~36 px-et — az
                // „Általános" felirat ezért „ános"-ra vágva jelent meg 480
                // px-en, tehát ez volt a 2. lelet EGYIK gyökéroka). A lenti
                // `mutasdALathatoFulet()` ezt FELÜLÍRJA: a kiválasztott fül
                // pontosan a látható sáv elejére/végére igazodik, margó
                // nélkül — a 0. fülnél `contentX` mindig 0.
                clip: true
                leftPadding: tabBarRow.tulcsordul ? 22 : 0
                rightPadding: tabBarRow.tulcsordul ? 22 : 0
                onCurrentIndexChanged: Qt.callLater(tabBarRow.mutasdALathatoFulet)

                TabButton { objectName: "optionsTabGeneral"; text: qsTr("General"); width: implicitWidth }
                TabButton { objectName: "optionsTabEmail"; text: qsTr("E-Mail"); width: implicitWidth }
                TabButton { objectName: "optionsTabFileTypes"; text: qsTr("File Types"); width: implicitWidth }
                TabButton { objectName: "optionsTabSlideshow"; text: qsTr("Slideshow"); width: implicitWidth }
                TabButton { objectName: "optionsTabPrinting"; text: qsTr("Printing"); width: implicitWidth }
                TabButton { objectName: "optionsTabNetwork"; text: qsTr("Network"); width: implicitWidth }
                TabButton { objectName: "optionsTabWebAlbums"; text: qsTr("Web Albums"); width: implicitWidth }
                TabButton { objectName: "optionsTabNameTags"; text: qsTr("Name Tags"); width: implicitWidth }
            }

            // ⚠️ SZÁNDÉKOSAN a `tabBar.contentChildren` (a nyolc TABBUTTON
            // SAJÁT `implicitWidth`-jeinek összege), NEM
            // `tabBar.contentItem.contentWidth`: az utóbbi KÖRKÖRÖS
            // bindinghurkot okozott (mérve: „Binding loop detected for
            // property tulcsordul") — a `contentItem.contentWidth` a belső
            // `ListView` mérete, ami a lenti `leftPadding`/`rightPadding`
            // hatására maga is újraszámolódik, ami visszahat a `tulcsordul`-
            // ra, ami megint padingot vált. A `contentChildren[i].
            // implicitWidth` a TabButtonok SAJÁT, a tabBar méretezésétől
            // FÜGGETLEN szöveg-metrikája — nem hurkolhat vissza.
            readonly property real fulokSzukseglete: {
                var osszeg = 0
                for (var i = 0; i < tabBar.contentChildren.length; ++i)
                    osszeg += tabBar.contentChildren[i].implicitWidth
                return osszeg
            }
            // ⚠️ Qt „Binding loop detected for property tulcsordul"
            // figyelmeztetést ír ki emiatt a kötés miatt (a `leftPadding`
            // változása újraszámoltatja a Fusion `TabBar` saját
            // `implicitWidth`-jét, ami visszahat erre a kiértékelésre) —
            // MÉRVE stabil, véges értéken áll meg (nem valódi végtelen
            // ciklus), és a projekt szűrője (`qml_warning_filter.py`,
            // #1599/#1748) SZÁNDÉKOSAN nem bukik el rajta: 38 másik
            // párbeszéd is hordozza ugyanezt a mintát, a kikapcsolása külön,
            // tucatnyi fájlt érintő javítás tárgya, nem ennek a jegynek.
            readonly property bool tulcsordul:
                tabBarRow.fulokSzukseglete > tabBar.width + 1
            onTulcsordulChanged: Qt.callLater(tabBarRow.mutasdALathatoFulet)

            /** A kiválasztott fül MARGÓ NÉLKÜL, teljesen látható legyen a
                fülsor görgethető sávján belül — a 0. fülnél `contentX`
                pontosan 0 (ld. a `tabBar` fejléc-kommentjét). `Qt.callLater`-
                rel hívva: a Fusion `TabBar` saját görgetése UTÁN fut le,
                tehát felülírja azt, nem verseng vele. */
            function mutasdALathatoFulet() {
                var ci = tabBar.contentItem
                if (!ci)
                    return
                var elem = tabBar.itemAt(tabBar.currentIndex)
                if (!elem)
                    return
                if (elem.x < ci.contentX)
                    ci.contentX = elem.x
                else if (elem.x + elem.width > ci.contentX + ci.width)
                    ci.contentX = elem.x + elem.width - ci.width
            }
            Component.onCompleted: Qt.callLater(mutasdALathatoFulet)

            Button {
                objectName: "optionsTabScrollLeftButton"
                text: "‹"
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: 22
                z: 1
                visible: tabBarRow.tulcsordul
                enabled: tabBar.contentItem && tabBar.contentItem.contentX > 0
                onClicked: tabBar.contentItem.contentX = Math.max(
                    0, tabBar.contentItem.contentX - tabBar.width / 2)
            }

            Button {
                objectName: "optionsTabScrollRightButton"
                text: "›"
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: 22
                z: 1
                visible: tabBarRow.tulcsordul
                enabled: tabBar.contentItem
                    && tabBar.contentItem.contentX
                        < tabBar.contentItem.contentWidth - tabBar.width - 1
                onClicked: tabBar.contentItem.contentX = Math.min(
                    tabBar.contentItem.contentWidth - tabBar.width,
                    tabBar.contentItem.contentX + tabBar.width / 2)
            }
        }

        StackLayout {
            id: tabStack
            objectName: "optionsTabStack"
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex
            clip: true

            OptionsTabGeneral { Layout.fillWidth: true }
            OptionsTabEmail { Layout.fillWidth: true }
            OptionsTabFileTypes { Layout.fillWidth: true }
            OptionsTabSlideshow { Layout.fillWidth: true }
            OptionsTabPrinting { Layout.fillWidth: true }
            OptionsTabNetwork { Layout.fillWidth: true }
            OptionsTabWebAlbums { Layout.fillWidth: true }
            OptionsTabNameTags { Layout.fillWidth: true }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Item { Layout.fillWidth: true }
            // a mostani élő beállítások (nyelv, törlés-megerősítés) azonnal
            // hatnak, ahogy a menüből is — nincs külön OK/Alkalmaz szükséges
            PicasaButton {
                objectName: "optionsCloseButton"
                text: qsTr("Close")
                accent: Theme.picasaGreen
                onClicked: optionsWindow.visible = false
            }
        }
    }
}
