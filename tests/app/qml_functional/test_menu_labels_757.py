"""A bal hasáb öt kontextusmenüjének FELIRATAI — #757/2.

A 2026-08-15-i mérő kör kilenc olyan feliratot talált, ami eltér az
eredetitől, és megállapította, hogy az öt menüfájlban **egyetlen**
`&`-mnemonik sincs — vagyis Alt-navigáció nincs, holott a
`docs/specs/ui-audit-context-menus.md` A.3 pontja ezt kifejezetten elvárja
(„A `&` gyorsjelölések átvehetők, így az Alt-navigáció is egyezik").

A várt szövegek forrása a `Picasa3i18n.dll` string-táblája
(`<menüosztály>::<ID_PARANCS>` kulcsok) — a privát kutatási repó
`referencia/stringres-en-hu.tsv` fájlja. A táblázat ITT, a tesztben él, mert
a kutatási repó nem része a nyilvános projektnek; az azonosító minden
sorban ott van, hogy visszakereshető legyen.

Miért nem elég a `test_context_menu_parity_422.py`: az a tétel LÉTÉT
állítja (objectName), a feliratáról csak annyit, hogy nem üres. Kilenc
eltérő szöveg és 54 hiányzó mnemonik így fért el zöld CI mellett.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE: list[object] = []

#: menüfájl -> objectName -> (várt angol felirat, a string-tábla azonosítója)
#:
#: A felirat SZÓ SZERINT az eredeti, a `&` mnemonik-jelölővel együtt. Ahol a
#: sor gyorsbillentyűt is mutat, az a `\t` utáni rész — az nem az eredeti
#: string-táblából jön, hanem a saját megjelenítésünk (a Picasa a
#: gyorsbillentyűt külön oszlopban rajzolta).
FELIRATOK: dict[str, dict[str, tuple[str, str]]] = {
    "FolderContextMenu": {
        "folderMenuEditDescription": (
            "&Edit Folder Description...", "Folder::ID_ALBUM_EDITCAPTIONS"
        ),
        "folderMenuSelectAll": (
            "Select &All Pictures\tCtrl+A", "Album::ID_ALBUM_SELECTALLPICTURES"
        ),
        "folderMenuClearSelection": (
            "&Clear Selection\tCtrl+D", "Folder::ID_CLEAR_SELECTION"
        ),
        "folderMenuInvertSelection": (
            "&Invert Selection\tCtrl+I", "Album::ID_SELECT_INVERT"
        ),
        "folderContextMenuMoveToCollection": (
            "Mo&ve to Collection", "Folder::ID_ALBUM_MOVETOCOLLECTION"
        ),
        # a Picasa saját, nem menüosztályhoz kötött szövege — nincs benne `&`
        "folderContextMenuNewCollection": ("New Collection...", "IDS_NEW_COLLECTION"),
        "folderMenuRefreshThumbnails": (
            "Refresh &Thumbnails", "Folder::ID_REFRESH_THUMB"
        ),
        "folderMenuSortBy": ("S&ort Folder By", "Folder::SortFolderBy"),
        "folderMenuSortByDate": ("&Date", "Sort::ID_DATESORT"),
        "folderMenuSortByName": ("&Name", "Sort::ID_NAMESORT"),
        "folderMenuSortBySize": ("&Size", "Sort::ID_SIZESORT"),
        "folderMenuSortReverse": ("&Reverse order", "Sort::ID_REVERSESORT"),
        "folderMenuHideFolder": ("&Hide Folder", "Folder::ID_HIDEENTIREALBUM"),
        "folderMenuLocate": (
            "&Locate on Disk\tCtrl+Enter", "FolderWin::ID_ALBUM_LOCATEONDISK"
        ),
        "folderMenuRemoveFromPicasa": (
            "&Remove from Picasa...", "Folder::ID_MANAGE_ALBUM"
        ),
        "folderMenuMoveFolder": ("&Move Folder...", "Folder::ID_MOVEFOLDER"),
        "folderMenuDeleteFolder": ("&Delete Folder...", "Folder::ID_ALBUM_DELETE"),
        "folderMenuUploadToGooglePhotos": (
            "Upload to Google &Photos...",
            "Album::ID_UPLOAD_ALBUM_TO_GOOGLE_PLUS_PHOTOS",
        ),
        "folderMenuExportAsHtml": (
            "E&xport as HTML Page...", "Album::ID_ALBUM_MAKE_WEB"
        ),
        "folderMenuAddNameTags": ("&Add name tags", "Album::ID_ALBUM_FILTERFACES"),
    },
    "AlbumContextMenu": {
        "albumMenuDelete": ("&Delete Album", "Album::ID_ALBUM_DELETE"),
        "albumMenuEditDescription": (
            "&Edit Album Description...", "Album::ID_ALBUM_EDITCAPTIONS"
        ),
        "albumMenuAddNameTags": ("&Add name tags", "Album::ID_ALBUM_FILTERFACES"),
        "albumMenuSelectAll": (
            "Select &All Pictures", "Album::ID_ALBUM_SELECTALLPICTURES"
        ),
        "albumMenuClearSelection": ("&Clear Selection", "Album::ID_CLEAR_SELECTION"),
        "albumMenuInvertSelection": ("&Invert Selection", "Album::ID_SELECT_INVERT"),
        "albumMenuRefreshThumbnails": (
            "&Refresh Thumbnails", "Album::ID_REFRESH_THUMB"
        ),
        # #757/2: a string-táblában megvolt, a menüből hiányzott
        "albumMenuSortAlbumBy": ("Sort &Album By", "Album::SortAlbumBy"),
        "albumMenuOnlineActions": ("Online Actions", "Album::ID_ONLINE_ACTIONS"),
        "albumMenuUploadToGooglePhotos": (
            "Upload to Google &Photos...",
            "Album::ID_UPLOAD_ALBUM_TO_GOOGLE_PLUS_PHOTOS",
        ),
        "albumMenuUploadToWebAlbums": (
            "Upload to &Picasa Web Albums...", "Album::ID_UPLOAD_TO_LIGHTHOUSE"
        ),
        "albumMenuExportAsHtml": (
            "E&xport as HTML Page...", "Album::ID_ALBUM_MAKE_WEB"
        ),
    },
    "FolderListContextMenu": {
        "folderListMenuSortByDate": ("Sort by &Date", "AlbumList::ID_VIEWBYDATE"),
        "folderListMenuSortByName": ("Sort by &Name", "AlbumList::ID_VIEWBYNAME"),
        "folderListMenuSortBySize": ("Sort by &Size", "AlbumList::ID_VIEWBYSIZE"),
        "folderListMenuSortByChanged": (
            "Sort by &Recent Changes", "AlbumList::ID_VIEWBYRECENT"
        ),
        "folderListMenuSortReverse": ("Re&verse sort", "AlbumList::ID_VIEWREVERSE"),
        "folderListMenuSortPeopleByName": (
            "Sort &People by Name", "AlbumList::ID_PEOPLEBYNAME"
        ),
        "folderListMenuSortPeopleByCount": (
            "Sort People by &Amount", "AlbumList::ID_PEOPLEBYAMOUNT"
        ),
        "folderListMenuSortPeopleByTopList": (
            "Sort People by Top &10", "AlbumList::ID_PEOPLEBYAMOUNTTOP10"
        ),
        "folderListMenuFlatView": (
            "&Simplified Tree View", "AlbumList::ID_VIEW_WATCHED"
        ),
        "folderListMenuShowThumbnails": (
            "Show &Thumbnails in Library", "AlbumList::ID_VIEW_THUMBNAILS"
        ),
        # #757/2: a spec kétszer is „11 tétel"-t írt, a string-táblában
        # viszont 12 `AlbumList::` sor van — ez a tizenkettedik
        "folderListMenuShortcuts": ("&Shortcuts", "AlbumList::Shortcuts"),
        "folderListMenuDesktop": ("&Desktop", "AlbumList::ID_VIEW_DESKTOP"),
    },
    "CollectionContextMenu": {
        "collectionMenuRename": (
            "Rename &Collection...", "Collection::ID_RENAMECOLLECTION"
        ),
        "collectionMenuRemove": (
            "&Remove Collection", "Collection::ID_REMOVECOLLECTION"
        ),
        "collectionMenuPassword": (
            "&Add/Change a password...", "Collection::ID_COL_PASSWORD"
        ),
    },
    "PeopleAlbumContextMenu": {
        "peopleAlbumMenuDelete": (
            "&Delete People Album", "PplAlbum::ID_ALBUM_DELETE"
        ),
        "peopleAlbumMenuEdit": (
            "&Edit People Album...", "PplAlbum::ID_ALBUM_EDITCAPTIONS"
        ),
        "peopleAlbumMenuSelectAll": (
            "Select &All", "PplAlbum::ID_ALBUM_SELECTALLPICTURES"
        ),
        "peopleAlbumMenuClearSelection": (
            "&Clear Selection", "PplAlbum::ID_CLEAR_SELECTION"
        ),
    },
}

MIND = tuple(
    (komponens, nev)
    for komponens, tetelek in FELIRATOK.items()
    for nev in tetelek
)

#: Az eredetiben SEM volt mnemonikja — az egyetlen két kivétel.
MNEMONIK_NELKUL = {"albumMenuOnlineActions", "folderContextMenuNewCollection"}


@pytest.fixture
def qml_engine(qt_app):
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


def _felirat(tetel) -> str:
    """Az almenü felirata a `title`, a tételeké a `text`."""
    return tetel.property("text") or tetel.property("title") or ""


class TestAFeliratokAzEredetiek:
    @pytest.mark.parametrize(("komponens", "nev"), MIND, ids=[n for _, n in MIND])
    def test_a_felirat_szo_szerint_egyezik(self, qml_engine, komponens, nev):
        vart, azonosito = FELIRATOK[komponens][nev]
        menu = _menu(qml_engine, komponens)

        tetel = menu.findChild(QObject, nev)
        assert tetel is not None, f"{komponens}: hiányzik a(z) {nev} tétel"

        assert _felirat(tetel) == vart, (
            f"{komponens}.{nev}: a felirat eltér az eredetitől "
            f"({azonosito})"
        )


class TestMindenTetelnekVanMnemonikja:
    """`ui-audit-context-menus.md` A.3: „A `&` gyorsjelölések átvehetők,
    így az Alt-navigáció is egyezik."""

    @pytest.mark.parametrize(("komponens", "nev"), MIND, ids=[n for _, n in MIND])
    def test_a_tetelben_ott_a_mnemonik(self, qml_engine, komponens, nev):
        if nev in MNEMONIK_NELKUL:
            pytest.skip("az eredetiben sincs mnemonikja")
        menu = _menu(qml_engine, komponens)

        tetel = menu.findChild(QObject, nev)
        assert tetel is not None

        assert "&" in _felirat(tetel), (
            f"{komponens}.{nev}: nincs `&`-mnemonik, tehát nincs "
            "Alt-navigáció (#757/2)"
        )


class TestAMnemonikNemLatszikNyersen:
    """A helyfoglaló tételek (`PicasaMenuItem`) saját `contentItem`-et
    kaptak (#416) — ha az sima `Text`, a felirat NYERSEN mutatná az
    ampersandot („&Hide Folder"). A Qt mnemonik-tudatos címkéje a
    `QQuickMnemonicLabel`; azt a `QtQuick.Controls.impl` `IconLabel`-je
    hozza magával, ugyanúgy, ahogy a sima `MenuItem` alapértelmezése."""

    def _mnemonik_cimke(self, item) -> bool:
        cimke = item.property("contentItem")
        if cimke is None:
            return False
        maradek = [cimke]
        while maradek:
            aktualis = maradek.pop()
            if aktualis.metaObject().className() == "QQuickMnemonicLabel":
                return True
            maradek.extend(aktualis.childItems())
        return False

    @pytest.mark.parametrize(
        ("komponens", "nev"),
        [
            ("FolderContextMenu", "folderMenuHideFolder"),
            ("FolderContextMenu", "folderMenuDeleteFolder"),
            ("AlbumContextMenu", "albumMenuDelete"),
            ("CollectionContextMenu", "collectionMenuPassword"),
            ("PeopleAlbumContextMenu", "peopleAlbumMenuDelete"),
        ],
    )
    def test_a_helyfoglalo_felirata_mnemonik_tudatos(
        self, qml_engine, komponens, nev
    ):
        menu = _menu(qml_engine, komponens)
        tetel = menu.findChild(QObject, nev)
        assert tetel is not None

        assert self._mnemonik_cimke(tetel), (
            f"{komponens}.{nev}: a felirat sima `Text`-ben rajzolódik, ezért "
            "az ampersand NYERSEN látszik a menüben (#757/2)"
        )
