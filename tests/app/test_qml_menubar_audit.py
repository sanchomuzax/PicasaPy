"""A menürendszer teljessége és gyorsbillentyűi az eredeti Picasa 3.9-hez
képest (#324/#327, ld. `docs/specs/ui-audit-menus.md`).

Két réteg:

1. Élő QML-fa (a `qml_app` fixture teljes ablakot tölt be offscreen) —
   az `objectName`-mel ellátott, ténylegesen bekötött tételek engedélyezettségét
   és a hozzájuk tartozó élő `Shortcut`-okat ellenőrzi.
2. A `PicasaMenuBar.qml` forrásszövegére épülő ellenőrzés — az auditban
   „nem" (teljesen hiányzó) jelölt angol feliratok mindegyike szerepeljen
   a fájlban, és a hozzájuk tartozó gyorsbillentyű-felirat (ha az auditban
   van gyorsbillentyű) is látszódjon. Azért szövegalapú, mert az inaktív
   (`enabled: false`) tételeknek jellemzően nincs `objectName`-jük — az
   élő QML-fából való kiolvasásuk nem adna érdemben többet, mint hamis
   biztonságérzetet.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt

_MENU_QML = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "picasapy"
    / "app"
    / "qml"
    / "PicasaPy"
    / "PicasaMenuBar.qml"
)


def _source() -> str:
    return _MENU_QML.read_text(encoding="utf-8")


# -- 1. réteg: a korábban teljesen hiányzó feliratok mindegyike bekerült ---

# (angol felirat, van-e hozzá az auditban gyorsbillentyű-felirat a menüben)
HIANYZOTT_TETELEK = [
    # Fájl
    ("Import From Google Photos...", None),
    # ⚠️ #1616: a gyorsbillentyű KIKERÜLT a feliratból. A funkciónak nyoma
    # sincs a kódban, a tétel helyfoglaló — és a #1616 szabálya szerint
    # nem hirdetünk olyat, ami nincs bekötve. Amint a funkció elkészül,
    # a felirat és az élő `Shortcut` EGYSZERRE kerül vissza.
    ("Open File(s) in Editor", None),
    ("Move to New Folder...", None),
    ("Save As...", None),
    ("Save a Copy", None),
    ("Order Prints...", None),
    # Szerkesztés
    ("Cut", "Ctrl+X"),
    ("Copy", "Ctrl+C"),
    ("Paste", "Ctrl+V"),
    ("Copy Text", None),
    ("Paste Text", None),
    # Nézet
    ("Show Editing Controls", None),
    ("Search Options", None),
    ("Thumbnails Only", None),
    ("Use Color Management", None),
    ("Display Mode", None),
    # Mappa
    ("Hide", None),
    ("Show", None),
    ("Print Thumbnails...", "Ctrl+Shift+P"),
    ("Export as HTML Page...", None),
    ("Move...", None),
    ("Delete...", None),
    # Kép
    ("Reset Face Positions", None),
    # Létrehozás
    ("Set as Desktop Background...", None),
    ("Add to Screensaver...", None),
    ("Make a Gift CD...", None),
    ("Publish to Blogger...", None),
    # Eszközök
    ("Upload Manager...", None),
    ("Configure Photo Viewer...", None),
    ("Configure Screensaver...", None),
    ("Batch Upload...", None),
    ("Upload", None),
    ("Geotag", None),
    ("Experimental", None),
    ("Configure Buttons...", None),
    # Súgó
    ("Picasa Forums", None),
    ("Online Information", None),
    ("Product Release Notes", None),
    ("Privacy Policy", None),
    ("Terms of Service", None),
]


def test_hianyzott_menupontok_bekerultek():
    src = _source()
    for label, _shortcut in HIANYZOTT_TETELEK:
        assert f'qsTr("{label}")' in src, f"hiányzik a menüpont: {label!r}"


def test_hianyzott_gyorsbillentyuk_lathatok_a_feliratban():
    src = _source()
    for label, shortcut in HIANYZOTT_TETELEK:
        if shortcut is None:
            continue
        assert f'qsTr("{label}") + "\\t{shortcut}"' in src, (
            f"a(z) {label!r} menüpontnak látszania kellene a "
            f"{shortcut!r} gyorsbillentyűnek a feliratban"
        )


# -- 2. réteg: az eltérő szerkezetű tételek valódi almenük lettek ---------


def test_rendezes_valodi_almenu_a_mappa_menuben():
    src = _source()
    assert 'objectName: "menuFolderSortBy"' in src
    assert 'title: qsTr("Sort By")' in src


def test_csoportos_szerkesztes_almenu_a_kep_menuben():
    src = _source()
    assert 'title: qsTr("Batch Edit")' in src


def test_mozgofilm_almenu_es_a_mukodo_muvelet_megmaradt():
    src = _source()
    assert 'title: qsTr("Movie")' in src
    # a korábban is működő "Movie" tétel az almenü gyermekeként él tovább,
    # ugyanazzal a jelzéssel
    assert 'objectName: "menuCreateMovie"' in src
    assert "bar.movieRequested()" in src


# -- 3. réteg: élő QML-fa — a meglévő, MŰKÖDŐ tételek nem romlottak el ----


class TestMeglevoTetelekMukodnekTovabbra:
    """A már élesen működő menüpontok viselkedése nem változhatott."""

    def test_file_menu_active_items_unchanged(self, qml_app):
        window, controller, lib, engine = qml_app
        for name in (
            "menuFileRename",
            "menuFileExport",
            "menuFileLocate",
            "menuFileDelete",
        ):
            item = window.findChild(QObject, name)
            assert item is not None, name
            # kijelölés nélkül (a fixture nem jelöl ki semmit) inaktívak
            assert item.property("enabled") is False

    def test_edit_effects_items_present(self, qml_app):
        window, controller, lib, engine = qml_app
        copy_item = window.findChild(QObject, "menuEditCopyEffects")
        paste_item = window.findChild(QObject, "menuEditPasteEffects")
        assert copy_item is not None
        assert paste_item is not None

    def test_dark_theme_and_perf_monitor_untouched(self, qml_app):
        window, controller, lib, engine = qml_app
        dark = window.findChild(QObject, "menuViewDarkTheme")
        perf = window.findChild(QObject, "menuHelpPerfMonitor")
        assert dark is not None and dark.property("checkable") is True
        assert perf is not None and perf.property("checkable") is True

    def test_a_mappanezet_tetelei_ELOK_ebben_a_fixtureben_is(
        self, qml_app, qt_app
    ):
        """#1454: a `folderHierarchyController` bekötése ELŐSZÖR csak a
        `tests/app/qml_functional/conftest.py`-ba került be — itt a
        `bar.folderViewCtl` null maradt volna, a három új menütétel néma, a
        pipa örökre az „Egyszerű mappanézet"-en. Ma nem bukna tőle semmi, de
        egy jövőbeli, EBBEN a fixture-ben mérő teszt zölden mérne egy halott
        menüt. Ez az őr azt méri, hogy a tétel tényleg hat."""
        window, _controller, _lib, engine = qml_app
        hier = engine.rootContext().contextProperty("folderHierarchyController")
        assert hier is not None, (
            "a folderHierarchyController nincs regisztrálva ebben a "
            "fixture-ben — a Mappanézet menü néma"
        )
        assert hier.treeView is False

        tetel = window.findChild(QObject, "menuViewTreeView")
        assert tetel is not None
        QMetaObject.invokeMethod(tetel, "toggle", Qt.ConnectionType.DirectConnection)
        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert hier.treeView is True
        assert window.findChild(
            QObject, "folderHierarchyList"
        ).property("visible") is True

    def test_folder_sort_by_submenu_exists(self, qml_app):
        """A Mappa ▸ Rendezés almenü megvan — csak a jelenlétét nézzük, nem
        UI-kattintást (a Menu popup-nyitás offscreen módban törékeny).

        #1454: a korábbi név („mirrors folder view") azt állította, hogy ez
        az almenü a Nézet ▸ Mappanézettel AZONOS — épp ez volt a hiba. A
        mappák rendezése azóta EGYEDÜL itt (és a helyi menükben) él; a
        tényleges kattintást a
        `tests/app/qml_functional/test_mappanezet_menu_1454.py` méri."""
        window, controller, lib, engine = qml_app
        sort_by = window.findChild(QObject, "menuFolderSortBy")
        assert sort_by is not None


# -- 4. réteg: élő gyorsbillentyűk (#327) ----------------------------------


class TestGyorsbillentyuk:
    def test_uj_elo_shortcutok_jelen_vannak(self, qml_app):
        window, controller, lib, engine = qml_app
        for name, sequence in (
            ("shortcutSmallThumbnails", "Ctrl+1"),
            ("shortcutNormalThumbnails", "Ctrl+2"),
            ("shortcutLocateOnDisk", "Ctrl+Return"),
            ("shortcutDeleteFromDisk", "Delete"),
            # #1472: a Ctrl+P eddig csak FELIRAT volt a Nyomtatás… tételen
            ("shortcutPrint", "Ctrl+P"),
            # #1590: ugyanez az Indexképek nyomtatása… Ctrl+Shift+P-jével
            ("shortcutPrintContactSheet", "Ctrl+Shift+P"),
        ):
            shortcut = window.findChild(QObject, name)
            assert shortcut is not None, name
            assert str(shortcut.property("sequence")) == sequence

    def test_kijelolestol_fuggo_shortcutok_alapbol_tiltottak(self, qml_app):
        """Kijelölés nélkül a Ctrl+Enter / Delete gyorsbillentyűk nem
        élesek — ugyanaz a feltétel, mint a menüpontoké (photoActionsEnabled)."""
        window, controller, lib, engine = qml_app
        locate = window.findChild(QObject, "shortcutLocateOnDisk")
        delete = window.findChild(QObject, "shortcutDeleteFromDisk")
        # #1472: a nyomtatás ugyanezen a feltételen áll
        printing = window.findChild(QObject, "shortcutPrint")
        assert locate.property("enabled") is False
        assert delete.property("enabled") is False
        assert printing.property("enabled") is False

    def test_thumbnail_shortcutok_mindig_elesek(self, qml_app):
        window, controller, lib, engine = qml_app
        small = window.findChild(QObject, "shortcutSmallThumbnails")
        normal = window.findChild(QObject, "shortcutNormalThumbnails")
        assert small.property("enabled") is True
        assert normal.property("enabled") is True

    def test_inaktiv_tetelekhez_nincs_uj_elo_shortcut_objektum(self):
        """Az inaktív pontok (pl. Ctrl+N, Ctrl+X, F1...) csak a feliratban
        jelennek meg — nem szabad hozzájuk élő `Shortcut {}` elemet kötni.
        Az egyetlen forrás-elhelyezésű `Shortcut` blokk a fájl elején van,
        pontosan 8 elemmel (a fenti nyolc aktív tételhez). A szám #1472-ben
        nőtt négyről ötre (a `Nyomtatás…` tétel élővé vált, tehát a
        Ctrl+P-nek is élő billentyűt kellett kapnia), a #1590-ben ötről
        hatra (`Indexképek nyomtatása…`, Ctrl+Shift+P), a #1615-ben hatról
        hétre (`Importálás forrása…`, Ctrl+M), a #1633-ban pedig hétről
        nyolcra (`Fájl felvétele a Picasába…`, Ctrl+O)."""
        src = _source()
        # #1616: a `Ctrl+N` (Új album…) bekötésével nyolcról KILENCRE nőtt.
        # A darabszám önmagában gyenge mérce — nem mondja meg, MELYIK
        # hiányzik —, de olcsó jelzés arra, ha valaki némán kivesz egyet.
        # A tartalmi ellenőrzést a `test_gyorsbillentyuk_1616.py` söprő őre
        # végzi: az minden ÉLŐ menütételre megköveteli az élő `Shortcut`-ot.
        assert src.count("Shortcut {") == 9


class TestMukodoTetelekBillentyui:
    """#327: aminek a felirata billentyűt ígér ÉS a menüpont működik, ahhoz
    tartozzon élő `Shortcut` — akár itt, akár a Main.qml globálisai közt.

    A Qt a `Return` és az `Enter` billentyűt szinonimaként kezeli, a Picasa
    viszont „Enter"-t ír a menüben; a normalizálás ezt a kettőt vonja össze,
    hogy a felirat és a bekötés eltérése ne látsszon hiánynak.
    """

    @staticmethod
    def _normalise(sequence: str) -> str:
        return sequence.replace("Enter", "Return")

    def _live_sequences(self) -> set[str]:
        import re

        main_qml = _MENU_QML.parent.parent / "Main.qml"
        combined = _source() + main_qml.read_text(encoding="utf-8")
        return {
            self._normalise(seq)
            for seq in re.findall(r'sequence:\s*"([^"]+)"', combined)
        }

    def test_minden_mukodo_tetel_billentyuje_elo(self):
        import re

        live = self._live_sequences()
        missing = []
        for item in re.findall(r"MenuItem\s*\{[^}]*?\}", _source(), re.S):
            promised = re.search(r"\\t([A-Za-z0-9+]+)", item)
            if not promised:
                continue
            works = "onTriggered" in item and "enabled: false" not in item
            if works and self._normalise(promised.group(1)) not in live:
                title = re.search(r'qsTr\("([^"]+)"\)', item)
                missing.append(
                    (promised.group(1), title.group(1) if title else "?")
                )
        assert not missing, f"működő menüpont élő billentyű nélkül: {missing}"

    def test_a_szinonima_normalizalas_nem_nyel_el_valodi_hianyt(self):
        # ellenpróba: egy kitalált billentyű NEM lehet a bekötöttek közt
        assert "Ctrl+Shift+Alt+Q" not in self._live_sequences()
