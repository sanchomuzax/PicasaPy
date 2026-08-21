"""A Mappakezelő fája VALÓDI EGÉRKATTINTÁSRA nyíljon ki (#1200).

## Miért külön fájl, és miért kattintással

A meglévő készlet (`test_qml_folder_manager.py`) a `toggleExpand()`
FÜGGVÉNYT hívja közvetlenül:

```python
_invoke(row_item, "toggleExpand")     # KÖZVETLEN függvényhívás
```

A függvény hibátlan — **csak épp senki nem tudja elsütni**. A nyíl
`MouseArea`-ja a sor `MouseArea`-ja ALATT volt (korábban deklarálva),
ezért a sor elnyelte a kattintást: a felhasználónál a fa egyáltalán nem
nyílt ki, a teszt viszont zöld maradt.

Ez a „fog nélküli őr" mintája: zöld készlet egy használhatatlan funkció
fölött. Ezért ez a fájl **kizárólag valódi `QMouseEvent`-tel** dolgozik.
"""

from PySide6.QtCore import QEvent, QPointF, Qt, QTimer, QEventLoop, QMetaObject
from PySide6.QtGui import QMouseEvent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtCore import QObject


def _dialog_window(window):
    dialog = window.findChild(QQuickWindow, "folderManagerDialog")
    assert dialog is not None, "folderManagerDialog nem található Window-ként"
    return dialog


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _by_name(window, name):
    dialog = _dialog_window(window)
    for item in _walk(dialog.contentItem()):
        if item.objectName() == name:
            return item
    return None


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


def _tree_controller(engine):
    return engine.rootContext().contextProperty("folderTreeController")


def _open_with_root(window, qt_app, engine, root_path):
    dialog = window.findChild(QObject, "folderManagerDialog")
    loop = _quit_on(_tree_controller(engine).childrenLoaded)
    dialog.setProperty("rootPath", str(root_path))
    QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
    loop.exec()
    qt_app.processEvents()
    return dialog


def _kattints(qt_app, ablak, elem, dx=None, dy=None):
    """VALÓDI egéresemény az elem közepére (vagy a megadott eltolásra).

    ⚠️ Nem `clicked()`-hívás és nem `toggleExpand()`: a lényeg éppen az,
    hogy a találati sorrend (z-rend) helyes-e."""
    pont = elem.mapToScene(
        QPointF(
            elem.width() / 2 if dx is None else dx,
            elem.height() / 2 if dy is None else dy,
        )
    )
    for tipus in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
        ablak.sendEvent(
            ablak.contentItem(),
            QMouseEvent(
                tipus,
                pont,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            ),
        ) if hasattr(ablak, "sendEvent") else None
    qt_app.processEvents()
    return pont


class TestNyilKattintas:
    def _fa(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, engine = qml_app
        gyoker = tmp_path / "tallozo"
        (gyoker / "alfa" / "beta").mkdir(parents=True)
        _open_with_root(window, qt_app, engine, gyoker)
        return window, engine, gyoker

    def test_a_nyilra_kattintva_KINYILIK_a_sor(self, qml_app, qt_app, tmp_path):
        """⚠️ Ez a jegy magja: a felhasználónál a fa nem nyílt ki."""
        from PySide6.QtTest import QTest

        window, engine, gyoker = self._fa(qml_app, qt_app, tmp_path)
        sor = _by_name(window, f"folderTreeItem:{gyoker / 'alfa'}")
        assert sor is not None, "az alfa sor nem található"
        assert sor.property("hasChildren") is True
        assert sor.property("expanded") is False

        nyil = _by_name(window, f"folderTreeArrow:{gyoker / 'alfa'}")
        assert nyil is not None, (
            "a kinyitó nyílnak azonosítható elemnek kell lennie "
            "(objectName), különben kattintással nem célozható"
        )
        pont = nyil.mapToScene(QPointF(nyil.width() / 2, nyil.height() / 2))
        loop = _quit_on(_tree_controller(engine).childrenLoaded)
        QTest.mouseClick(
            _dialog_window(window),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            pont.toPoint(),
        )
        loop.exec()
        qt_app.processEvents()

        assert sor.property("expanded") is True, (
            "a nyílra kattintás NEM nyitotta ki a sort — a sor MouseArea-ja "
            "elnyeli a kattintást"
        )

    def test_a_nyilra_kattintas_NEM_jelol_ki(self, qml_app, qt_app, tmp_path):
        """Az eredetiben a két találati terület elkülönül."""
        from PySide6.QtTest import QTest

        window, engine, gyoker = self._fa(qml_app, qt_app, tmp_path)
        dialog = window.findChild(QObject, "folderManagerDialog")
        dialog.setProperty("selectedPath", "")
        nyil = _by_name(window, f"folderTreeArrow:{gyoker / 'alfa'}")
        assert nyil is not None
        pont = nyil.mapToScene(QPointF(nyil.width() / 2, nyil.height() / 2))

        QTest.mouseClick(
            _dialog_window(window),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            pont.toPoint(),
        )
        qt_app.processEvents()

        assert dialog.property("selectedPath") == "", (
            "a nyílra kattintás kijelölte a sort is"
        )

    def test_a_SORRA_kattintas_tovabbra_is_kijelol(self, qml_app, qt_app, tmp_path):
        from PySide6.QtTest import QTest

        window, engine, gyoker = self._fa(qml_app, qt_app, tmp_path)
        dialog = window.findChild(QObject, "folderManagerDialog")
        dialog.setProperty("selectedPath", "")
        sor = _by_name(window, f"folderTreeRow:{gyoker / 'alfa'}")
        assert sor is not None
        # a név tájékán, jóval a nyíl UTÁN
        pont = sor.mapToScene(QPointF(sor.width() - 20, sor.height() / 2))

        QTest.mouseClick(
            _dialog_window(window),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            pont.toPoint(),
        )
        qt_app.processEvents()

        assert dialog.property("selectedPath") == str(gyoker / "alfa")


class TestGombsor:
    """A párbeszédnek PONTOSAN három gombja van (#1200).

    Bizonyíték az eredeti oldalról: a `tre:foldermgr` „# BUTTONS"
    szakasza `ok`, `cancel`, `help` — más nincs; a `respack.yt` is pontosan
    három `superbutton` réteget tartalmaz, mindhárom 98 × 28.

    ⚠️ A két extra gomb nem csak felesleges volt: MAGYAR feliratokkal a sor
    617,7 px-et igényelt egy 550 px-es ablakban, és ezért a Súgó gomb
    kilógott a képernyőről. A tulajdonos képernyőképén emiatt nem látszott.
    """

    def _nyisd(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, _controller, _lib, _engine = qml_app
        dialog = window.findChild(QObject, "folderManagerDialog")
        QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        return window, dialog

    def test_a_ket_extra_gomb_NINCS_a_parbeszedben(self, qml_app, qt_app):
        window, _dialog = self._nyisd(qml_app, qt_app)

        assert _by_name(window, "adoptPicasaFoldersButton") is None, (
            "a Picasa-mappak atvetele gomb az eredetiben NEM letezik"
        )

    def test_a_harom_gomb_megvan(self, qml_app, qt_app):
        window, _dialog = self._nyisd(qml_app, qt_app)

        for nev in (
            "folderManagerOkButton",
            "folderManagerCancelButton",
            "folderManagerHelpButton",
        ):
            assert _by_name(window, nev) is not None, f"hiányzik: {nev}"

    def test_a_gombsor_MAGYAR_feliratokkal_is_befer(self, qml_app, qt_app):
        """⚠️ MÉRŐ teszt, nem szemre.

        Az ablak 550 px; a jegy mércéje 550 − 2×4 margó = 542 px."""
        window, _dialog = self._nyisd(qml_app, qt_app)
        sor = _by_name(window, "folderManagerButtonRow")
        assert sor is not None, (
            "a gombsornak azonosíthatónak kell lennie, hogy MÉRNI lehessen"
        )

        assert sor.property("implicitWidth") <= 542, (
            f"a gombsor {sor.property('implicitWidth')} px-et igényel, "
            "az ablak 550 px — a Súgó kilóg a képernyőről"
        )


class TestFajlMenuBekotes:
    """A „Mappa hozzáadása a Picasához…" a FÁJL MENÜBŐL nyitja a
    Mappakezelőt (#1200/6).

    Bizonyíték az eredetiből: `eMenuFile::ID_TOOLS_INCLUDEEXCLUDEFOLDERS`
    (`stringres` 2648. sor) → parancs `0x9caa` → `0x005cb990` szétosztó →
    `0x005ce590` — **ez a párbeszéd nyílik meg**. Nem külön funkció, és
    nem mappaválasztó.

    ⚠️ Nálunk ez a menüpont `placeholder: true` volt (inaktív), a
    funkciót pedig egy gomb végezte a párbeszédben — pont fordítva.
    """

    def test_a_menupont_NEM_placeholder(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, _controller, _lib, _engine = qml_app
        tetel = window.findChild(QObject, "menuFileAddFolder")
        assert tetel is not None, (
            "a Fajl menu Mappa-hozzaadas tetelenek azonosithatonak kell lennie"
        )
        assert tetel.property("placeholder") is not True, (
            "a menüpont inaktív (placeholder) — az eredetiben ez nyitja a "
            "Mappakezelot"
        )

    def test_a_menupont_MEGNYITJA_a_mappakezelot(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, _controller, _lib, _engine = qml_app
        dialog = window.findChild(QObject, "folderManagerDialog")
        assert dialog.property("visible") is not True

        tetel = window.findChild(QObject, "menuFileAddFolder")
        assert tetel is not None
        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert dialog.property("visible") is True, (
            "a Fájl menü tétele nem nyitotta meg a Mappakezelot"
        )


class TestAllapotIkon:
    """MINDEN soron pontosan egy állapot-ikon látszik (#1200/2).

    Bizonyíték az eredetiből: `0x007c6700` (a `CFolderMgrDialog::
    TreeListDraw` vtable rajzoló metódusa), `0x007c68ec`–`0x007c691d`:
    **if / else-if / else** — nincs kihagyó ág. A harmadik (alapértelmezett,
    „nincs állapot") esetben is rajzol, a `folder_manager_exclude` piros
    ikonjával.

    ⚠️ Nálunk a jelvény `visible`-je csak `always`/`once` esetén volt igaz,
    tehát a fa legtöbb során SEMMI nem látszott.
    """

    def test_a_harmadik_allapotban_is_van_ikon(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, engine = qml_app
        gyoker = tmp_path / "ikonfa"
        (gyoker / "alfa").mkdir(parents=True)
        _open_with_root(window, qt_app, engine, gyoker)

        jelveny = _by_name(window, f"folderTreeGlyph:{gyoker / 'alfa'}")
        assert jelveny is not None, "az allapot-jelveny nem talalhato"
        assert jelveny.property("folderState") == "none", (
            "ez a teszt a HARMADIK allapotra szol"
        )

        allapot = None
        for elem in _walk(jelveny):
            if elem.objectName() == "folderStateIcon":
                allapot = elem
                break
        assert allapot is not None, (
            "az allapot-ikonnak azonosithatonak kell lennie"
        )
        assert allapot.property("visible") is True, (
            "a harmadik allapotban NEM latszik ikon — az eredeti minden "
            "soron rajzol (0x007c6700 else aga)"
        )


class TestRadiosorIkonok:
    """A három rádiósor mindegyike mellett ott a SAJÁT ikonja (#1200/4).

    Bizonyíték az eredetiből: a `tre:foldermgr`-ben az `icon_once`,
    `icon_exclude`, `icon_always` a `status_group` GYERMEKEI; a rectek
    szerint a rádió 24×24 az `x=310`-en, az IKON az `x≈340`-en, a felirat
    az `x=363`-on, 33 px sorosztással.

    ⚠️ Nálunk a soroknak nem volt ikonjuk — a felhasználó csak a szövegből
    tudta, melyik állapot melyik, a fában viszont ikonok állnak.
    """

    def _nyisd(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, engine = qml_app
        gyoker = tmp_path / "radiofa"
        (gyoker / "alfa").mkdir(parents=True)
        _open_with_root(window, qt_app, engine, gyoker)
        dialog = window.findChild(QObject, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(gyoker / "alfa"))
        qt_app.processEvents()
        return window

    def test_mindharom_sor_kap_ikont(self, qml_app, qt_app, tmp_path):
        window = self._nyisd(qml_app, qt_app, tmp_path)

        for allapot in ("once", "exclude", "always"):
            sor = _by_name(window, f"folderStateOption:{allapot}")
            if sor is None:
                continue
            ikon = None
            for elem in _walk(sor):
                if elem.objectName() == f"folderStateOptionIcon:{allapot}":
                    ikon = elem
                    break
            assert ikon is not None, (
                f"a(z) {allapot} radiosor mellol hianyzik az ikon"
            )
