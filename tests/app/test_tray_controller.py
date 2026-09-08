"""`TrayMixin` — a képtálca (Picture Tray, #455) állapot-magja.

A `test_photo_ops_controller.py` fixtúra-mintáját követi: valódi
`AppController` két mappával (a mappákon-átnyúló gyűjtés bizonyításához).
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def two_folder_library(tmp_path):
    root = tmp_path / "kepek"
    folder_a = root / "a"
    folder_b = root / "b"
    folder_a.mkdir(parents=True)
    folder_b.mkdir(parents=True)
    make_jpeg(folder_a / "x.jpg", size=(800, 600))
    make_jpeg(folder_a / "y.jpg", size=(800, 600))
    make_jpeg(folder_b / "z.jpg", size=(800, 600))
    return root, folder_a, folder_b


@pytest.fixture
def controller(qt_app, tmp_path, two_folder_library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    root, _folder_a, _folder_b = two_folder_library
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(root),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    return ctl


def _rows_by_name(controller, *names) -> list:
    photos = controller.photos.photos
    by_name = {p.name: i for i, p in enumerate(photos)}
    return [by_name[name] for name in names]


class TestHoldRows:
    def test_empty_tray_initially(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        assert controller.heldCount == 0

    def test_hold_row_adds_to_tray(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        rows = _rows_by_name(controller, "x.jpg")
        controller.holdRows(rows)
        assert controller.heldCount == 1
        assert controller.isHeldAt(rows[0]) is True

    def test_hold_is_idempotent(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        rows = _rows_by_name(controller, "x.jpg")
        controller.holdRows(rows)
        controller.holdRows(rows)
        assert controller.heldCount == 1

    def test_hold_survives_folder_change(self, controller, two_folder_library):
        """A tálca lényege: mappaváltás után is megmarad a megtartott kép,
        holott a `selectedIndexes`/sor-index elveszne (a #150-es
        row-alapú kijelölés csak az aktuális mappára érvényes)."""
        _root, folder_a, folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        rows = _rows_by_name(controller, "x.jpg")
        controller.holdRows(rows)

        controller.selectFolder(str(folder_b))
        assert controller.heldCount == 1
        # a b mappa "z.jpg" sora NEM tartott
        z_row = _rows_by_name(controller, "z.jpg")[0]
        assert controller.isHeldAt(z_row) is False

    def test_hold_across_two_folders_accumulates(
        self, controller, two_folder_library
    ):
        _root, folder_a, folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))
        controller.selectFolder(str(folder_b))
        controller.holdRows(_rows_by_name(controller, "z.jpg"))
        assert controller.heldCount == 2


class TestClearHeld:
    def test_clears_all(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        controller.holdRows(_rows_by_name(controller, "x.jpg", "y.jpg"))
        assert controller.heldCount == 2
        controller.clearHeld()
        assert controller.heldCount == 0

    def test_clear_empty_tray_is_noop(self, controller):
        controller.clearHeld()
        assert controller.heldCount == 0


class TestHeldThumbUrl:
    def test_returns_url_even_from_other_folder(self, controller, two_folder_library):
        _root, folder_a, folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))
        controller.selectFolder(str(folder_b))
        # jelenleg a b mappa van megnyitva, a tartott kép mégis az a-ból
        url = controller.heldThumbUrlAt(0)
        assert url.startswith("image://thumbs/")

    def test_out_of_range_is_empty(self, controller):
        assert controller.heldThumbUrlAt(0) == ""


class TestHeldChangedSignal:
    def test_emitted_on_hold(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        seen = []
        controller.heldChanged.connect(lambda: seen.append(True))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))
        assert seen == [True]

    def test_not_emitted_when_nothing_changes(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))
        seen = []
        controller.heldChanged.connect(lambda: seen.append(True))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))  # már bent van
        assert seen == []


class TestOsszecsukottMappaToken:
    """#1919 — egy egész mappa a tálcán, EGYETLEN tokenként.

    A vezérlő itt csak fordít: mappa-útvonalból darabszám és borítókép, a
    nézetnek pedig `trayAlbumTokens`. Hogy MELYIK gesztus indítja ezt, az
    a jegy nyitott kérdése — menüpont ezért nem tartozik hozzá.
    """

    def test_a_mappa_osszecsukva_egy_tokent_ad(
        self, controller, two_folder_library
    ):
        _root, folder_a, _folder_b = two_folder_library
        assert controller.collapseFolderIntoTray(str(folder_a)) is True
        tokenek = controller.trayAlbumTokens
        assert len(tokenek) == 1
        assert tokenek[0]["key"] == str(folder_a)
        assert tokenek[0]["photoCount"] == 2
        assert tokenek[0]["isAlbum"] is False

    def test_a_token_BORITOKEPET_is_kap(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.collapseFolderIntoTray(str(folder_a))
        assert controller.trayAlbumTokens[0]["coverThumbUrl"], (
            "a token borítókép nélkül üres dobozként jelenne meg"
        )

    def test_a_token_NEM_szamit_bele_a_belyegkep_sorba(
        self, controller, two_folder_library
    ):
        """A `heldCount`-ból számol a bélyegkép-sor; a tokennek saját
        rajza van, tehát nem növelheti a rács elemszámát."""
        _root, folder_a, _folder_b = two_folder_library
        controller.collapseFolderIntoTray(str(folder_a))
        assert controller.heldCount == 0

    def test_a_talca_VEGYESEN_is_tarthat_kepet_es_tokent(
        self, controller, two_folder_library
    ):
        _root, folder_a, folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))
        controller.collapseFolderIntoTray(str(folder_b))
        assert controller.heldCount == 1
        assert len(controller.trayAlbumTokens) == 1

    def test_a_MEGTARTOTT_tokent_a_kovetkezo_kijeloles_nem_sopri_el(
        self, controller, two_folder_library
    ):
        """Egy egész mappa összecsukása szándékos gyűjtés — a token ezért
        `held`, ugyanúgy, mint a „Kijelölés megtartása" képei."""
        _root, folder_a, folder_b = two_folder_library
        controller.collapseFolderIntoTray(str(folder_b))
        controller.selectFolder(str(folder_a))
        controller.syncSelection(_rows_by_name(controller, "y.jpg"))
        assert len(controller.trayAlbumTokens) == 1

    def test_az_ismetelt_osszecsukas_nem_duplaz(
        self, controller, two_folder_library
    ):
        _root, folder_a, _folder_b = two_folder_library
        controller.collapseFolderIntoTray(str(folder_a))
        controller.collapseFolderIntoTray(str(folder_a))
        assert len(controller.trayAlbumTokens) == 1

    def test_az_ismeretlen_mappa_nem_ad_tokent(self, controller, tmp_path):
        assert controller.collapseFolderIntoTray(str(tmp_path / "nincs")) is False
        assert controller.trayAlbumTokens == []

    # -- a token mellett a KÉP-oldali lekérdezések is működnek -------------
    #
    # A `trayItems` a Klipek lap (`CollageClipsTab.qml`) bemenete, és a
    # tálca MINDEN elemén végigmegy. A #1919 óta a listában TOKEN is lehet,
    # aminek nincs `photo_id`-ja — a szótár-építés ezen elhasalt, és a
    # QML-kötés futásidőben `AttributeError`-t dobott. A fenti „vegyesen is
    # tarthat" próba ezt NEM fogta meg, mert csak a `heldCount`-ot és a
    # `trayAlbumTokens`-t olvasta, a `trayItems`-t nem.

    def test_a_trayItems_TOKEN_mellett_is_olvashato(
        self, controller, two_folder_library
    ):
        """A token nem törheti el a KÉP-elemeket ígérő lekérdezést."""
        _root, folder_a, folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))
        controller.collapseFolderIntoTray(str(folder_b))
        elemek = controller.trayItems
        assert [elem["name"] for elem in elemek] == ["x.jpg"], (
            "a `trayItems` nem a tálca EGYETLEN képét adja vissza "
            f"({elemek!r}) — vagy elhasalt a tokenen"
        )

    def test_a_trayItems_a_kep_HELD_jelzojet_megtartja(
        self, controller, two_folder_library
    ):
        """A token jelenléte nem mosdathatja el a kép saját jelzőit."""
        _root, folder_a, folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))
        controller.collapseFolderIntoTray(str(folder_b))
        (elem,) = controller.trayItems
        assert elem["held"] is True
        assert elem["used"] is False

    def test_a_heldPaths_TOKEN_mellett_is_csak_kepeket_ad(
        self, controller, two_folder_library
    ):
        """A tálca alatti műveletsor (nyomtatás, e-mail, kollázs) ezen
        dolgozik — a tokennek nincs fájl-útvonala, nem kerülhet bele."""
        _root, folder_a, folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))
        controller.collapseFolderIntoTray(str(folder_b))
        utvonalak = controller.heldPaths
        assert len(utvonalak) == 1
        assert utvonalak[0].endswith("x.jpg")

    def test_az_ures_utvonal_nem_ad_tokent(self, controller):
        assert controller.collapseFolderIntoTray("") is False

    def test_a_token_kibontasa_eltavolitja(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.collapseFolderIntoTray(str(folder_a))
        assert controller.expandFolderInTray(str(folder_a)) is True
        assert controller.trayAlbumTokens == []

    def test_a_nem_letezo_token_kibontasa_FALSE(self, controller):
        assert controller.expandFolderInTray("/nincs/ilyen") is False

    def test_az_urites_a_tokent_is_elviszi(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.collapseFolderIntoTray(str(folder_a))
        controller.clearHeld()
        assert controller.trayAlbumTokens == []
