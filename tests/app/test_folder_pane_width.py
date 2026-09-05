"""#322: a bal oldali mappapanel szélessége állítható és megjegyződik.

A szélesség a QSettings `view/folderPaneWidth` kulcsában él (mint a
`view/folderSort` és társai), és ésszerű határok közé szorul — így egy
elrontott (0 vagy képernyőnél szélesebb) érték sem tudja használhatatlanná
tenni a felületet a következő induláskor.
"""

import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg

from picasapy.app.controller import (
    FOLDER_PANE_WIDTH_DEFAULT,
    FOLDER_PANE_WIDTH_MAX,
    FOLDER_PANE_WIDTH_MIN,
)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    # elszigetelt QSettings — a valós PicasaPy-beállításokat ne írja a teszt
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    yield ctl
    ctl.shutdown() if hasattr(ctl, "shutdown") else None


class TestFolderPaneWidth:
    def test_default_when_unset(self, controller):
        assert controller.folderPaneWidth == FOLDER_PANE_WIDTH_DEFAULT

    def test_set_and_read_back(self, controller):
        controller.setFolderPaneWidth(310)
        assert controller.folderPaneWidth == 310

    def test_persisted_to_settings(self, controller):
        controller.setFolderPaneWidth(275)
        assert int(controller._get_settings().value("view/folderPaneWidth")) == 275

    def test_too_narrow_is_clamped(self, controller):
        controller.setFolderPaneWidth(10)
        assert controller.folderPaneWidth == FOLDER_PANE_WIDTH_MIN

    def test_too_wide_is_clamped(self, controller):
        controller.setFolderPaneWidth(5000)
        assert controller.folderPaneWidth == FOLDER_PANE_WIDTH_MAX

    def test_garbage_in_settings_falls_back_to_default(self, controller):
        controller._get_settings().setValue("view/folderPaneWidth", "nem-szám")
        assert controller.folderPaneWidth == FOLDER_PANE_WIDTH_DEFAULT

    def test_survives_a_new_controller_on_the_same_settings(
        self, controller, tmp_path, library
    ):
        controller.setFolderPaneWidth(288)

        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache

        second = AppController(
            tmp_path / "index.db",
            (str(library),),
            ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs2", size=32)),
            settings=controller._get_settings(),
            watched_file=tmp_path / "WatchedFolders.txt",
        )
        assert second.folderPaneWidth == 288


class TestMertKorlatok2329:
    """#2329: az eredeti osztósáv legkisebb szélessége **240**, a
    legnagyobb pedig **ablakfüggő** (a főpanel szélessége − 240).

    Mérve: a kezelő osztálya `ytSplitterOffsetHandler` (RTTI `0x00d4734c`);
    a gyártó a `+0x18` mezőbe **240.0**-t tölt (`0x009da130`, a konstans a
    `0x00cf48b0`-on); az alsó korlát a `0x009d9df4`–`0x009d9e0e`, a felső a
    `0x009d9e21`–`0x009d9e50` (`sub`, `fsub`, `fcomp`).

    A felső korlát ablakfüggő, tehát a Python-oldali vágás nem tudja
    egyedül eldönteni — ott csak biztonsági határ marad. Az ablakhoz kötést
    a QML végzi, azt a `test_fo_ablak_elrendezes_587.py` méri.
    """

    def test_a_legkisebb_szelesseg_240(self) -> None:
        """A foga: 160-nal a hasáb 80 képponttal keskenyebbre húzható
        volt, mint amit az eredeti valaha megenged."""
        assert FOLDER_PANE_WIDTH_MIN == 240

    def test_a_legkisebb_egyezik_az_alapertelmezessel(self) -> None:
        """Az eredetiben ugyanaz a szám — a sáv nem húzható az
        alapértelmezés alá."""
        assert FOLDER_PANE_WIDTH_MIN == FOLDER_PANE_WIDTH_DEFAULT

    def test_a_240_nel_keskenyebb_mentett_ertek_felemelkedik(
        self, controller
    ) -> None:
        """Aki korábban 160-ra húzta, induláskor 240-et kap — a getter
        vágása ezt magától megteszi, de kimondva is állítjuk."""
        controller._get_settings().setValue("view/folderPaneWidth", 170)
        assert controller.folderPaneWidth == 240

    def test_szeles_ablakhoz_valo_ertek_is_atmegy(self, controller) -> None:
        """A 600-as fix felső korlát széles ablakon TÚL SZŰK volt: az
        eredeti ott a szélesség − 240-ig enged. A Python-oldali határ ezért
        följebb kerül; a valódi, ablakfüggő korlátot a QML adja."""
        controller.setFolderPaneWidth(900)
        assert controller.folderPaneWidth == 900


def test_a_QML_felso_korlatja_ABLAKFUGGO() -> None:
    """#2329: a `SplitView.maximumWidth` nem lehet fix szám.

    Az eredetié a főpanel szélessége − 240. A fix 600 széles ablakon
    SZŰKEBB volt az eredetinél, keskeny ablakon viszont tágabb — ezért a
    kötésnek a tárolóra kell hivatkoznia. Ez a próba a forrást nézi: a
    kirajzolt szélességet a `test_fo_ablak_elrendezes_587.py` méri.
    """
    from pathlib import Path as _P

    qml = (
        _P(__file__).resolve().parents[2]
        / "src" / "picasapy" / "app" / "qml" / "Main.qml"
    ).read_text(encoding="utf-8")
    import re

    m = re.search(r"^\s*SplitView\.maximumWidth:(.*)$", qml, re.MULTILINE)
    assert m, "nem találom a SplitView.maximumWidth kötést"
    kifejezes = m.group(1).strip()
    assert not re.fullmatch(r"\d+", kifejezes), (
        "a felső korlát FIX szám — az eredetié ablakfüggő: " + kifejezes
    )
    assert "mainSplit.width" in kifejezes, (
        "a felső korlát nem a tároló szélességéhez kötött: " + kifejezes
    )
    assert "240" in kifejezes, (
        "a mért levonás (− 240) hiányzik a kötésből: " + kifejezes
    )
