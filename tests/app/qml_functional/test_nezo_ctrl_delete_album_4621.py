"""#4621 — a NÉZŐ `Ctrl+Delete`-je és „Törlés” tétele albumból eltávolít.

Spec: `docs/specs/ui-audit-context-menus.md` D.7. Az eredetiben a
`0x9c9a` parancs a néző helyi menüjéből, a billentyűről és a menüsávból
ugyanazt a `0x005c9b00`-t hívja, és az dönt: album (nem `]search`) →
albumtagság le, a fájl marad; mappa és Keresési eredmények → lemezről
törlés. A felirat ugyanezen a feltételen ágazik („Eltávolítás az
albumból” / „Törlés a lemezről”).

Nálunk a néző három belépője (a `Main.qml` ablak-szintű `Ctrl+Delete`-je,
a `PhotoViewer.qml` saját billentyűkezelője és a helyi menü tétele) eddig
mindig lemezről törölt. Most mind a menüsáv KÖZÖS elágazásán megy át.

Mérce: valódi billentyűesemény ÉS a menüpont valódi kattintása, a
megerősítő végigvive; a fájl megmaradását `Path.exists()`, az
albumtagság levételét az ini mutatja. Kétirányú: a mappa-ág KÖVETELI a
törlést. A várt feliratok kiírt literálok (a fixture nem telepít
fordítót, ezért az angol forrásszöveg látszik).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from support.qml_halasztott import epitsd_fel_ha_fileops

_TOKEN = "604c294a68b0de9cc9222c4714f289d5"
_ROY_ID = "b8e4117cf1d6615b"
_ROY = "Roy Avery"
_RECT = "3f840000c3509f84"


def _gyerek(window, nev):
    epitsd_fel_ha_fileops(window, nev)
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a(z) {nev} nem található"
    return elem


def _varj(controller, qt_app, korok=100):
    for _ in range(korok):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _katt(window, elem) -> None:
    kp = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window, Qt.LeftButton, Qt.NoModifier, QPoint(int(kp.x()), int(kp.y()))
    )


def _album_nezet(lib, tmp_path, controller, qt_app):
    (lib / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\nname=Nyaralás\ntoken={_TOKEN}\n"
        f"[a.jpg]\nalbums={_TOKEN}\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    controller.showAlbum(_TOKEN)
    qt_app.processEvents()


def _szemely_nezet(lib, tmp_path, controller, qt_app):
    (lib / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY_ID}={_ROY};;\n"
        f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY_ID};\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    controller.showPerson(_ROY)
    qt_app.processEvents()


def _nezo_nyit(window, qt_app):
    window.setProperty("viewerOpen", True)
    viewer = _gyerek(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    viewer.setProperty("focus", True)
    QMetaObject.invokeMethod(
        viewer, "forceActiveFocus", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    return viewer


def _ctrl_delete(window, qt_app):
    """Valódi (spontán) `Ctrl+Delete` — a `sendEvent` egy szintetikus
    eseményt a Shortcut-nak ÉS a néző Keys-kezelőjének is átadna, így a
    dialógus kétszer nyílna, és a teszt rossz Shortcut mellett is zöld
    maradna (#4621 átnézése)."""
    QTest.keyClick(
        window, Qt.Key.Key_Delete, Qt.KeyboardModifier.ControlModifier
    )
    qt_app.processEvents()


def _ablak_szintu_kotes_ki(window, qt_app):
    """A `Main.qml` ablak-szintű `Ctrl+Delete`-jét kikapcsolja, hogy a
    billentyű a `PhotoViewer.qml` SAJÁT kezelőjéhez jusson (a másik
    belépő külön mérendő)."""
    sc = _gyerek(window, "shortcutDeleteFromDiskViewer")
    sc.setProperty("enabled", False)
    qt_app.processEvents()


def _menu_nyit(window, qt_app):
    viewer = _gyerek(window, "photoViewer")
    QMetaObject.invokeMethod(
        viewer, "openContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()
    return _gyerek(window, "viewerContextMenu")


def _menu_zar(window, qt_app):
    menu = window.findChild(QObject, "viewerContextMenu")
    if menu is not None:
        QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _menupont_katt(window, qt_app):
    """A néző helyi menüjének törlés-tételére VALÓDI kattintás."""
    _menu_nyit(window, qt_app)
    tetel = _gyerek(window, "viewerMenuDelete")
    _katt(window, tetel)
    qt_app.processEvents()


def _lemezes_megerosit(window, controller, qt_app):
    confirm = _gyerek(window, "deleteConfirmDialog")
    assert confirm.property("visible") is True
    assert confirm.property("trashAvailable"), "nincs lomtár a környezetben"
    QMetaObject.invokeMethod(
        confirm, "confirmed", Qt.ConnectionType.DirectConnection
    )
    _varj(controller, qt_app)


def _album_megerosit(window, qt_app):
    """Az „Elemek eltávolítása” megerősítő végigvitele valódi kattintással."""
    confirm = window.findChild(QObject, "removeFromAlbumDialog")
    assert confirm is not None and confirm.property("visible") is True, (
        "az albumból eltávolítás megerősítője nem nyílt meg"
    )
    gomb = window.findChild(QObject, "removeFromAlbumYesButton")
    assert gomb is not None
    _katt(window, gomb)
    qt_app.processEvents()


def _belepok():
    return ["billentyu_ablak", "billentyu_nezo", "helyi_menu"]


def _inditsd(belepo, window, qt_app):
    if belepo == "helyi_menu":
        _menupont_katt(window, qt_app)
        return
    if belepo == "billentyu_nezo":
        _ablak_szintu_kotes_ki(window, qt_app)
    _ctrl_delete(window, qt_app)


class TestAlbumbolMegnyitottKepEltavolit:
    def _egy(self, belepo, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        _nezo_nyit(window, qt_app)
        confirm = _gyerek(window, "deleteConfirmDialog")

        _inditsd(belepo, window, qt_app)

        assert confirm.property("visible") is False, (
            f"{belepo}: albumból megnyitott képen lemezről törlést kérdezett"
        )
        _album_megerosit(window, qt_app)
        _varj(controller, qt_app)
        assert (lib / "a.jpg").exists(), f"{belepo}: a fájl törlődött"
        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert f"albums={_TOKEN}" not in ini, f"{belepo}: tagság maradt"

    def test_ablak_szintu_ctrl_delete(self, qml_app, qt_app, tmp_path):
        self._egy("billentyu_ablak", qml_app, qt_app, tmp_path)

    def test_nezo_sajat_ctrl_delete_kezeloje(self, qml_app, qt_app, tmp_path):
        self._egy("billentyu_nezo", qml_app, qt_app, tmp_path)

    def test_helyi_menu_tetele(self, qml_app, qt_app, tmp_path):
        self._egy("helyi_menu", qml_app, qt_app, tmp_path)

    def test_a_megerosito_hivatalos_szoveget_hasznalja(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        _album_nezet(tmp_path / "kepek", tmp_path, controller, qt_app)
        _nezo_nyit(window, qt_app)

        _ctrl_delete(window, qt_app)

        confirm = window.findChild(QObject, "removeFromAlbumDialog")
        assert confirm is not None
        assert confirm.property("title") == "Remove Items"
        assert confirm.property("yesText") == "Remove Image"
        assert confirm.property("message") == (
            "Are you sure you want to remove the selected image from the "
            "current album?"
        )


class TestEmberekAlbumbolMegnyitottKep:
    def _egy(self, belepo, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _szemely_nezet(lib, tmp_path, controller, qt_app)
        _nezo_nyit(window, qt_app)

        _inditsd(belepo, window, qt_app)

        assert _gyerek(window, "deleteConfirmDialog").property(
            "visible"
        ) is False, f"{belepo}: lemezről törlést kérdezett"
        dlg = window.findChild(QObject, "removePeopleFacesDialog")
        assert dlg is not None and dlg.property("visible") is True, (
            f"{belepo}: az arc-eltávolítás megerősítője nem nyílt"
        )
        gomb = window.findChild(QObject, "removePeopleFacesYesButton")
        assert gomb is not None
        _katt(window, gomb)
        _varj(controller, qt_app)
        assert (lib / "a.jpg").exists()
        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert f"rect64({_RECT}),{_ROY_ID}" not in ini, (
            f"{belepo}: az arc-címke nem esett le"
        )

    def test_ablak_szintu_ctrl_delete(self, qml_app, qt_app, tmp_path):
        self._egy("billentyu_ablak", qml_app, qt_app, tmp_path)

    def test_nezo_sajat_ctrl_delete_kezeloje(self, qml_app, qt_app, tmp_path):
        self._egy("billentyu_nezo", qml_app, qt_app, tmp_path)

    def test_helyi_menu_tetele(self, qml_app, qt_app, tmp_path):
        self._egy("helyi_menu", qml_app, qt_app, tmp_path)


class TestMappabolMegnyitottKepTovabbraIsTorol:
    """Ellenkező irányú őr: a mappa-ág KÖVETELI a lemezről törlést."""

    def _egy(self, belepo, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        kep = tmp_path / "kepek" / "a.jpg"
        assert kep.exists()
        _nezo_nyit(window, qt_app)

        _inditsd(belepo, window, qt_app)

        _lemezes_megerosit(window, controller, qt_app)
        assert not kep.exists(), f"{belepo}: mappában nem törölt"

    def test_ablak_szintu_ctrl_delete(self, qml_app, qt_app, tmp_path):
        self._egy("billentyu_ablak", qml_app, qt_app, tmp_path)

    def test_nezo_sajat_ctrl_delete_kezeloje(self, qml_app, qt_app, tmp_path):
        self._egy("billentyu_nezo", qml_app, qt_app, tmp_path)

    def test_helyi_menu_tetele(self, qml_app, qt_app, tmp_path):
        self._egy("helyi_menu", qml_app, qt_app, tmp_path)

    def test_a_mappa_nezet_a_nezett_fajlt_celozza(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _nezo_nyit(window, qt_app)
        _ctrl_delete(window, qt_app)
        utak = _gyerek(window, "deleteConfirmDialog").property("paths")
        if hasattr(utak, "toVariant"):
            utak = utak.toVariant()
        assert [Path(p) for p in utak] == [
            Path(controller.watchedFolders[0]) / "a.jpg"
        ]


class TestAFeliratAMuvelettelEgyezik:
    def test_mappaban_torles_a_lemezrol(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezo_nyit(window, qt_app)
        _menu_nyit(window, qt_app)
        try:
            assert _gyerek(window, "viewerMenuDelete").property("text") == (
                "Delete from Disk\tCtrl+Delete"
            )
        finally:
            _menu_zar(window, qt_app)

    def test_albumban_eltavolitas_az_albumbol(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        _album_nezet(tmp_path / "kepek", tmp_path, controller, qt_app)
        _nezo_nyit(window, qt_app)
        _menu_nyit(window, qt_app)
        try:
            assert _gyerek(window, "viewerMenuDelete").property("text") == (
                "Remove from Album\tCtrl+Delete"
            )
        finally:
            _menu_zar(window, qt_app)

    def test_emberek_albumban_eltavolitas_az_albumbol(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        _szemely_nezet(tmp_path / "kepek", tmp_path, controller, qt_app)
        _nezo_nyit(window, qt_app)
        _menu_nyit(window, qt_app)
        try:
            assert _gyerek(window, "viewerMenuDelete").property("text") == (
                "Remove from Album\tCtrl+Delete"
            )
        finally:
            _menu_zar(window, qt_app)

    def test_keresesi_eredmenyekben_torles_a_lemezrol(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        mezo = window.findChild(QObject, "searchField")
        mezo.setProperty("text", "a")
        QMetaObject.invokeMethod(
            mezo, "textEdited", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert controller.searchActive
        _nezo_nyit(window, qt_app)
        _menu_nyit(window, qt_app)
        try:
            assert _gyerek(window, "viewerMenuDelete").property("text") == (
                "Delete from Disk\tCtrl+Delete"
            )
        finally:
            _menu_zar(window, qt_app)


def _ket_kepes_album(lib, tmp_path, controller, qt_app):
    (lib / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\nname=Nyaralás\ntoken={_TOKEN}\n"
        f"[a.jpg]\nalbums={_TOKEN}\n[b.jpg]\nalbums={_TOKEN}\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    controller.showAlbum(_TOKEN)
    qt_app.processEvents()


class TestMegerositesNelkuliBeallitas:
    """J2: a „megerősítés nélkül” beállítás elnyomja a kérdést — a
    művelet ilyenkor azonnal lefut, ezért a dupla futás (két belépő egy
    leütésre) itt látszana: a másik kép tagsága is leesne."""

    def test_nincs_parbeszed_es_csak_a_nezett_kep_esik_ki(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, engine = qml_app
        lib = tmp_path / "kepek"
        _ket_kepes_album(lib, tmp_path, controller, qt_app)
        beallitasok = engine.rootContext().contextProperty("confirmSettings")
        beallitasok.setSuppressed("removeFromAlbum", True)
        try:
            _nezo_nyit(window, qt_app)
            _gyerek(window, "removeFromAlbumDialogLoader")  # felépítés

            _ctrl_delete(window, qt_app)
            _varj(controller, qt_app)

            dlg = window.findChild(QObject, "removeFromAlbumDialog")
            assert dlg is None or dlg.property("visible") is not True
            assert _gyerek(window, "deleteConfirmDialog").property(
                "visible"
            ) is False
            assert (lib / "a.jpg").exists() and (lib / "b.jpg").exists()
            ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
            a = ini.split("[a.jpg]", 1)[1].split("[", 1)[0] if "[a.jpg]" in ini else ""
            b = ini.split("[b.jpg]", 1)[1].split("[", 1)[0] if "[b.jpg]" in ini else ""
            assert f"albums={_TOKEN}" not in a, "a.jpg tagsága nem esett le"
            assert f"albums={_TOKEN}" in b, "a b.jpg tagsága is leesett"
        finally:
            beallitasok.setSuppressed("removeFromAlbum", False)


class TestABModbanAJobbOldaliKepreVonatkozikAMenu:
    """J4: A|B módban, jobb oldali fókusszal a helyi menü EGY képre
    vonatkozik — a törlés és a többi tétel (itt a teljes útvonal másolása)
    ugyanarra az aktív képre."""

    def test_a_menu_utja_es_az_eltavolitott_kep_ugyanaz(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _ket_kepes_album(lib, tmp_path, controller, qt_app)
        nezo = _nezo_nyit(window, qt_app)
        kozep = _gyerek(window, "viewerLayoutAb")
        _katt(window, kozep)
        assert nezo.property("layoutMode") == "ab"
        nezo.setProperty("aktivOldal", "jobb")
        qt_app.processEvents()
        assert nezo.property("currentIndex") == 0

        _menu_nyit(window, qt_app)
        QGuiApplication.clipboard().setText("")
        QMetaObject.invokeMethod(
            _gyerek(window, "viewerContextMenu"), "copyFullPathRequested",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        masolt = Path(QGuiApplication.clipboard().text())
        assert masolt == lib / "b.jpg", "a menü a BAL képre vonatkozik"

        _gyerek(window, "viewerMenuDelete")
        _katt(window, _gyerek(window, "viewerMenuDelete"))
        _album_megerosit(window, qt_app)
        _varj(controller, qt_app)

        assert (lib / "a.jpg").exists() and (lib / "b.jpg").exists()
        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert "[b.jpg]" not in ini or (
            f"albums={_TOKEN}" not in ini.split("[b.jpg]", 1)[1].split("[", 1)[0]
        ), "a másolt útvonal képe nem esett ki az albumból"
        assert f"albums={_TOKEN}" in ini.split("[a.jpg]", 1)[1].split("[", 1)[0]
