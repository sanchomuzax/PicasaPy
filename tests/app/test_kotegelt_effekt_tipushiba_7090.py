"""A kötegelt effekt jelzi, ha videó (nem támogatott típus) kimaradt (#7090).

Az eredeti Picasa kötegelt effektmotorja (`0x005fe370`) a kijelölés
bejárásakor megszámolja a nem támogatott típusú (mozgókép) fájlokat, a
támogatottakat módosítja, és a köteg végén az `IDS_SOME_EDITS_FAILED_TYPE`
figyelmeztetést adja. Nálunk a videót eddig EGYÁLTALÁN nem hagytuk ki (a
`filters=` lánc a videó szakaszába is bekerült), és semmit nem mondtunk.

A vezérlő csak a TÉNYT jelenti (`batchEditTypeFailed(int)` a kihagyottak
számával), a szöveg a felületen él (`PicasaNotifier.qml`), a forgatás
`rotationTypeFailed` jelzésének (#1755) mintája szerint.

A forgatás oldala a #1755 óta kész (`test_forgatas_jelzes_1755.py`); az
itteni utolsó osztály csak azt rögzíti, hogy a KÉT jelzés ugyanazt a
szöveg-családot használja, és a kötegelt effekt szövege hivatalos.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre, wait_for_photo_op

from picasapy.ini import load_document
from tests.support.qml_blokk import blokk_horgony_utan

_APP = Path(picasapy.app.__file__).parent
_NOTIFIER = (_APP / "qml" / "PicasaPy" / "PicasaNotifier.qml").read_text(
    encoding="utf-8"
)
_TS = (_APP / "i18n" / "picasapy_hu.ts").read_text(encoding="utf-8")

#: Az eredeti `IDS_SOME_EDITS_FAILED_TYPE` angol forrása (`enUS/stringres.xml`,
#: a két szóköz a mondatok között az eredetié) és hivatalos magyar fordítása
#: (`i18n-hu/stringres.xml`).
ANGOL = (
    "Some images were not modified because of the file type.  "
    "Note that effects cannot be applied to movies."
)
MAGYAR = (
    "Néhány képet nem sikerült módosítani a fájltípusa miatt. "
    "Megjegyzendő, hogy mozgóképekre nem lehet effektusokat alkalmazni."
)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    folder = root / "nyaralas"
    folder.mkdir(parents=True)
    make_jpeg(folder / "IMG_0001.jpg", size=(200, 100))
    make_jpeg(folder / "IMG_0002.jpg", size=(200, 100))
    (folder / "film.mp4").write_bytes(b"\x00" * 32)
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library / "nyaralas"))
    assert varj_feltetelre(
        qt_app, lambda: not ctl.backgroundWorkersRunning(), 10.0
    ), "az indulási háttérmunka nem fejeződött be"
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _sorok(controller, *, video: bool) -> list[int]:
    return [
        i
        for i, photo in enumerate(controller.photos.photos)
        if (photo.kind == "video") is video
    ]


def _filters(library, name: str) -> str | None:
    ini = library / "nyaralas" / ".picasa.ini"
    if not ini.exists():
        return None
    section = load_document(ini).section(name)
    return section.get("filters") if section is not None else None


class TestAJelzes:
    def test_vegyes_kijeloles_JELZI_a_kihagyott_videot(
        self, controller, library
    ):
        """A jegy magja: kép + videó együtt: a képek módosulnak, a videó
        kimarad, és ezt MEGMONDJUK."""
        kaptunk: list[int] = []
        controller.batchEditTypeFailed.connect(kaptunk.append)
        sorok = [*_sorok(controller, video=False), *_sorok(controller, video=True)]

        wait_for_photo_op(
            controller, lambda: controller.applyEffectMany(sorok, "sepia")
        )

        assert kaptunk == [1], "a kihagyott videóról nem jött jelzés"
        for name in ("IMG_0001.jpg", "IMG_0002.jpg"):
            assert "sepia" in (_filters(library, name) or ""), (
                f"a kép ({name}) nem kapta meg az effektet"
            )

    def test_a_videora_NEM_kerul_lanc(self, controller, library):
        """Az eredeti átugorja a nem támogatott típust: a videó szakaszába
        nem kerülhet `filters=`."""
        sorok = [*_sorok(controller, video=False), *_sorok(controller, video=True)]

        wait_for_photo_op(
            controller, lambda: controller.applyEffectMany(sorok, "sepia")
        )

        assert _filters(library, "film.mp4") is None

    def test_a_jelzes_a_KOTEG_VEGEN_jon(self, controller):
        """„A köteg lefutása után”: a jelzés pillanatában a haladás-panel
        már nem látszik."""
        allapot: list[bool] = []
        controller.batchEditTypeFailed.connect(
            lambda _n: allapot.append(controller.batchEditActive)
        )
        sorok = [*_sorok(controller, video=False), *_sorok(controller, video=True)]

        wait_for_photo_op(
            controller, lambda: controller.applyEffectMany(sorok, "sepia")
        )

        assert allapot == [False], "a jelzés a köteg futása KÖZBEN érkezett"

    def test_csak_kepek_eseten_NINCS_jelzes(self, controller):
        """A jelzés nem lehet zajos: ha nincs kihagyott elem, hallgat."""
        kaptunk: list[int] = []
        controller.batchEditTypeFailed.connect(kaptunk.append)

        wait_for_photo_op(
            controller,
            lambda: controller.applyEffectMany(
                _sorok(controller, video=False), "sepia"
            ),
        )

        assert kaptunk == []

    def test_csak_videot_tartalmazo_kijeloles_is_JELEZ(
        self, controller, library
    ):
        """Nem üres kijelölés, de egyik elem sem szerkeszthető: a jelzés
        megjön, ini-írás és haladás-panel nélkül."""
        kaptunk: list[int] = []
        controller.batchEditTypeFailed.connect(kaptunk.append)

        controller.applyEffectMany(_sorok(controller, video=True), "sepia")

        assert kaptunk == [1]
        assert controller.batchEditActive is False
        assert _filters(library, "film.mp4") is None
        assert controller.canUndoBatchEdit is False

    def test_a_kihagyottak_SZAMAT_viszi(self, controller, library):
        """Két videó → 2. (A számot a felület `skipped <= 0` őre használja.)"""
        (library / "nyaralas" / "film2.mp4").write_bytes(b"\x00" * 32)
        from picasapy.index import open_index, sync_tree

        with open_index(controller._db_path) as conn:
            sync_tree(conn, library)
        controller.selectFolder(str(library / "nyaralas"))
        kaptunk: list[int] = []
        controller.batchEditTypeFailed.connect(kaptunk.append)

        controller.applyEffectMany(_sorok(controller, video=True), "bw")

        assert kaptunk == [2]

    def test_ismeretlen_effektre_nincs_jelzes(self, controller):
        """Az ismeretlen effekt egyáltalán nem fut: a típushiba sem szólhat."""
        kaptunk: list[int] = []
        controller.batchEditTypeFailed.connect(kaptunk.append)

        controller.applyEffectMany(_sorok(controller, video=True), "nemletezo")

        assert kaptunk == []

    def test_az_Undo_All_Edits_nem_ad_tipushiba_jelzest(self, controller):
        """Más parancs (`clearAllEffectsMany`) nem hozza elő a régi számlálót."""
        kaptunk: list[int] = []
        controller.batchEditTypeFailed.connect(kaptunk.append)
        sorok = [*_sorok(controller, video=False), *_sorok(controller, video=True)]
        wait_for_photo_op(
            controller, lambda: controller.applyEffectMany(sorok, "sepia")
        )
        kaptunk.clear()

        wait_for_photo_op(
            controller,
            lambda: controller.clearAllEffectsMany(
                _sorok(controller, video=False)
            ),
        )

        assert kaptunk == []

    def test_a_masodik_koteg_nem_orokli_az_elso_szamlalojat(self, controller):
        """A kihagyottak száma kötegenként számolódik, nem halmozódik."""
        kaptunk: list[int] = []
        controller.batchEditTypeFailed.connect(kaptunk.append)
        vegyes = [*_sorok(controller, video=False), *_sorok(controller, video=True)]
        wait_for_photo_op(
            controller, lambda: controller.applyEffectMany(vegyes, "sepia")
        )

        wait_for_photo_op(
            controller,
            lambda: controller.applyEffectMany(
                _sorok(controller, video=False), "bw"
            ),
        )

        assert kaptunk == [1]


class TestAFelulet:
    def test_a_notifier_felveszi_a_jelzest(self):
        assert "function onBatchEditTypeFailed(" in _NOTIFIER

    def test_nulla_kihagyottra_a_notifier_HALLGAT(self):
        assert "if (skipped <= 0)" in blokk_horgony_utan(
            _NOTIFIER, "function onBatchEditTypeFailed("
        )

    def test_a_felirat_a_HIVATALOS_angol_forras(self):
        assert f'qsTr("{ANGOL}")' in _NOTIFIER

    def test_a_magyar_a_SZOVEGTARBOL_valo(self):
        assert f"<source>{ANGOL}</source>" in _TS
        assert f"<translation>{MAGYAR}</translation>" in _TS
