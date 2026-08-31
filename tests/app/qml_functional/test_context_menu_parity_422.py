"""#422 — az eredeti tételsor hiánytalansága menünként.

A jegy elfogadási feltétele: „menünként a `ui-audit-context-menus.md`
tételsora hiánytalanul megvan". A képernyőképek viszont csak azt mutatják,
ami épp látszott — a **hiteles** tételsor a `Picasa3i18n.dll`
string-táblájából jön (`<menüosztály>::<ID_PARANCS>` kulcsok, hivatalos
magyar felirattal). Ez a teszt az így kiegészített tételsort őrzi.

A végigvezetés három tételt talált, amit sem a képernyőképek, sem a spec
szöveges felsorolása nem hozott elő:

* `AlbumPhoto::ID_FILE_LOCATEINPICASA` — „Keresés a Picasában". A „Keresés
  a lemezen" párja BEFELÉ: album-nézetből a kép saját mappájára ugrik a
  könyvtárban. A képernyőkép mappa-nézetben készült, ahol nincs értelme,
  ezért maradt ki.
* `PplAlbumPhoto::ID_PEOPLEALBUMS` — „Hozzáadás az Emberek albumhoz". A
  spec A.2 négy `PplAlbumPhoto`-parancsot említ, de a felsorolásban ez
  összemosódott az „Áthelyezés új személyhez…"-zel.
* `Album::ID_UPLOAD_TO_LIGHTHOUSE` — „Feltöltés a Picasa Webalbumokba…".
  Ez oldja fel a spec „13 tétel, de csak 11 nevesítve" ellentmondását: a
  13-ból NÉGY feltöltés-azonosító, amik mindössze KÉT különböző feliratot
  adnak (Google Fotók / Picasa Webalbumok) — nálunk eddig csak az első
  szerepelt.

Negyedikként a `Folder::ID_UNHIDEENTIREALBUM` „Mappa megjelenítése" is
hiányzott: a spec A.2 kimondja, hogy ez **nem külön tétel**, hanem az
„Mappa elrejtése" állapotfüggő felirat-váltása — pontosan úgy, ahogy a
kép-szintű Elrejtés ↔ Megjelenítés már működik.

Tesztelési buktatók (a projekt szabálya): a `Repeater` delegáltjai
`findChild`-dal nem találhatók meg, és a `visible` ÖRÖKLŐDIK — egy zárt
menü minden gyereke láthatatlan. Ezért a jelenlétet a fában való
megtalálás bizonyítja, a láthatóság-kötést pedig csak ott vizsgáljuk, ahol
a menüt tényleg fel is nyitjuk (`qml_app` + `openPhotoContextMenu`).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from picasapy.index import open_index, sync_tree

_KEEPALIVE: list[object] = []

_QML_DIR = Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml"

_TOKEN = "604c294a68b0de9cc9222c4714f289d5"

#: Menünként a HIÁNYTALAN tételsor: objectName -> a hivatalos magyar
#: felirat, amiért a tétel bekerült. A magyar szöveg NEM a forráskódból
#: jön, hanem a `Picasa3i18n.dll` string-táblájából — így a teszt egyben
#: azt is dokumentálja, mire hivatkozik minden egyes sor.
TETELSOR: dict[str, dict[str, str]] = {
    "PhotoContextMenu": {
        "contextMenuOpen": "Megjelenítés és szerkesztés",
        "contextMenuAddToAlbum": "Hozzáadás az albumhoz",
        "contextMenuRemoveFromAlbum": "Eltávolítás az albumból",
        "contextMenuRemoveFromPeopleAlbum": "Eltávolítás az Emberek albumból",
        "contextMenuAddToPeopleAlbum": "Hozzáadás az Emberek albumhoz",
        "contextMenuMoveToNewPerson": "Áthelyezés új személyhez...",
        "contextMenuSetAsPeopleAlbumThumbnail": (
            "Beállítás az Emberek album indexképeként"
        ),
        "contextMenuRotateRight": "Forgatás jobbra",
        "contextMenuRotateLeft": "Forgatás balra",
        "contextMenuUndoAllEdits": "Összes szerkesztés visszavonása",
        "contextMenuHide": "Elrejtés",
        "contextMenuMove": "Áthelyezés új mappába...",
        "contextMenuSplitFolder": "Mappa felosztása itt...",
        "contextMenuOpenFile": "Fájl megnyitása",
        "contextMenuOpenWith": "Társítás",
        "contextMenuSave": "Mentés",
        "contextMenuRevert": "Visszaállítás",
        "contextMenuLocateInPicasa": "Keresés a Picasában",
        "contextMenuLocate": "Keresés a lemezen",
        "contextMenuDelete": "Törlés a lemezről",
        "contextMenuCopyFullPath": "Teljes elérési út másolása",
        "contextMenuUploadToWebAlbums": "Feltöltés a Picasa Webalbumokba...",
        "contextMenuBlockUpload": "Feltöltés tiltása",
        "contextMenuResetFaces": "Arcok alaphelyzetbe állítása",
        "contextMenuProperties": "Tulajdonságok",
    },
    "AlbumContextMenu": {
        "albumMenuDelete": "Album törlése",
        "albumMenuEditDescription": "Albumleírás szerkesztése...",
        "albumMenuAddNameTags": "Névcímkék hozzáadása",
        "albumMenuSelectAll": "Az összes kép kijelölése",
        "albumMenuClearSelection": "Kijelölés törlése",
        "albumMenuInvertSelection": "Kiválasztás megfordítása",
        "albumMenuRefreshThumbnails": "Indexképek frissítése",
        # #757: az `Album::SortAlbumBy` — a #422-es végigvezetés az `ID_`
        # előtag hiánya miatt hagyta ki a sorból
        "albumMenuSortAlbumBy": "Album rendezésének alapja...",
        "albumMenuOnlineActions": "Online műveletek",
        "albumMenuUploadToGooglePhotos": "Feltöltés a Google Fotókba...",
        "albumMenuUploadToWebAlbums": "Feltöltés a Picasa Webalbumokba...",
        "albumMenuExportAsHtml": "Exportálás HTML-oldalként...",
    },
}

MIND = tuple(
    (komponens, nev)
    for komponens, tetelek in TETELSOR.items()
    for nev in tetelek
)


@pytest.fixture
def qml_engine(qt_app):
    """Menü-komponens önálló betöltéséhez — nem kell hozzá a teljes app."""
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _menu(engine, komponens: str):
    component = QQmlComponent(engine)
    component.setData(
        (
            "import QtQuick\nimport PicasaPy 1.0\n"
            f'{komponens} {{ objectName: "menu" }}\n'
        ).encode("utf-8"),
        QUrl(),
    )
    root = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert root is not None
    QQmlEngine.setObjectOwnership(root, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, root))
    return root


class TestATetelsorHianytalan:
    """Menünként minden dokumentált parancsnak megvan a HELYE."""

    @pytest.mark.parametrize(("komponens", "nev"), MIND, ids=[n for _, n in MIND])
    def test_a_tetel_ott_van_a_menuben(self, qml_engine, komponens, nev) -> None:
        menu = _menu(qml_engine, komponens)

        tetel = menu.findChild(QObject, nev)

        assert tetel is not None, (
            f"{komponens}: hiányzik a(z) {TETELSOR[komponens][nev]!r}"
            f" tétel ({nev})"
        )

    @pytest.mark.parametrize(("komponens", "nev"), MIND, ids=[n for _, n in MIND])
    def test_a_tetelnek_van_felirata(self, qml_engine, komponens, nev) -> None:
        """Üres feliratú sor nem tétel: a menü magassága és a tételek helye
        csak akkor egyezik az eredetivel, ha tényleg ki is van írva.

        Az almenük (`Menu`) felirata a `title`, a tételeké (`MenuItem`) a
        `text` — mindkettő elfogadható."""
        menu = _menu(qml_engine, komponens)
        tetel = menu.findChild(QObject, nev)
        assert tetel is not None

        felirat = tetel.property("text") or tetel.property("title")
        assert felirat, f"{nev}: nincs felirat"


class TestAMappaRejtesFeliratotValt:
    """`Folder::ID_HIDEENTIREALBUM` ↔ `ID_UNHIDEENTIREALBUM` — a spec A.2
    szerint NEM külön tétel, hanem ugyanazon a helyen váltó felirat.

    #757 óta a felirat az eredeti `&`-mnemonikot is hordozza; a
    mnemonik-betű a két állapotban KÜLÖNBÖZŐ (`&Hide` / `&Unhide`), tehát
    az sem hagyható el az összevetésből."""

    def test_alaphelyzetben_elrejtes(self, qml_engine) -> None:
        menu = _menu(qml_engine, "FolderContextMenu")
        tetel = menu.findChild(QObject, "folderMenuHideFolder")
        assert tetel is not None

        assert tetel.property("text") == "&Hide Folder"

    def test_rejtett_mappan_megjelenites(self, qml_engine) -> None:
        menu = _menu(qml_engine, "FolderContextMenu")
        menu.setProperty("folderHidden", True)
        tetel = menu.findChild(QObject, "folderMenuHideFolder")
        assert tetel is not None

        assert tetel.property("text") == "&Unhide Folder", (
            "rejtett mappán a felirat a Mappa megjelenítése alakra vált"
        )

    def test_nem_jott_letre_kulon_tetel(self, qml_engine) -> None:
        """Ellenpróba: a váltás egy tételen történik, nem kettőn."""
        menu = _menu(qml_engine, "FolderContextMenu")

        assert menu.findChild(QObject, "folderMenuUnhideFolder") is None


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _open_context_menu(window, qt_app, row):
    """A menüt TÉNYLEGESEN felnyitja — zárt popupban a `visible` minden
    gyereken hamis, függetlenül a kötéstől (ld. a modul docstringjét)."""
    grid = _child(window, "photoGrid")
    QMetaObject.invokeMethod(
        window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", row), Q_ARG("QVariant", grid),
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()


def _close_context_menu(window, qt_app):
    menu = _child(window, "photoContextMenu")
    QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _add_album_membership(lib, tmp_path, controller, qt_app):
    (lib / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\n"
        f"name=Nyaralás\n"
        f"token={_TOKEN}\n"
        f"[a.jpg]\n"
        f"albums={_TOKEN}\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    qt_app.processEvents()


class TestKeresesAPicasabanCsakAlbumNezetben:
    """`AlbumPhoto::ID_FILE_LOCATEINPICASA` — a kép SAJÁT mappájára ugrás.
    Mappa-nézetben nincs értelme (már ott vagyunk), ezért ugyanaz a kapu,
    mint az „Eltávolítás az albumból"-nál."""

    # #1613: a tétel azóta a „Keresés" ALMENÜBEN ül. Csukott almenüben a
    # Qt minden tételt `visible: false`-nak mutat — a saját kötésünket
    # tehát csak NYITOTT almenüben lehet megmérni. (Ugyanaz a csapda, mint
    # a #1720 szövegmező-menüjénél: a `visible` a felbukkanó ablak
    # állapotát tükrözi, nem a mi feltételünket.)
    @staticmethod
    def _nyisd_ki_a_kereses_almenut(window, qt_app):
        almenu = _child(window, "contextMenuLocateMenu")
        almenu.setProperty("visible", True)
        qt_app.processEvents()
        return almenu

    def test_mappa_nezetben_rejtve(self, qml_app, qt_app) -> None:
        window, controller, _engine = qml_app
        assert controller.currentAlbumToken == ""

        _open_context_menu(window, qt_app, 0)
        self._nyisd_ki_a_kereses_almenut(window, qt_app)
        tetel = _child(window, "contextMenuLocateInPicasa")

        assert tetel.property("visible") is False
        _close_context_menu(window, qt_app)

    def test_album_nezetben_latszik(self, qml_app, qt_app, tmp_path) -> None:
        window, controller, _engine = qml_app
        _add_album_membership(tmp_path / "kepek", tmp_path, controller, qt_app)
        controller.showAlbum(_TOKEN)
        qt_app.processEvents()

        _open_context_menu(window, qt_app, 0)
        self._nyisd_ki_a_kereses_almenut(window, qt_app)
        tetel = _child(window, "contextMenuLocateInPicasa")

        assert tetel.property("visible") is True
        _close_context_menu(window, qt_app)
