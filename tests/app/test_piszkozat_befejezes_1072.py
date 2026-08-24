"""A piszkozat KÜLÖN BEFEJEZŐ LÉPÉSE és a hozzá vezető visszaút (#1072).

A jegy harmadik hiánya: *„a mentés egyben véglegesít"* — nálunk nem volt
olyan lépés, amivel a felhasználó egy MÁR mentett piszkozatot befejez.

Az eredetiben ez az `editpanel/render_now` = **„Létrehozás"** gomb, ami a
piszkozat képe FÖLÖTT ül (spec 4.1/4.3), és a `projectutils::draft_collage`
szövege is erre a gombra hivatkozik.

Két dolog kell hozzá, és mindkettő hiányzott:

1. **a piszkozat felismerése** egy megnyitott képről (`isCollageDraft`),
2. **a piszkozat projektjének betöltése**: a `openCollageProject` (#1002)
   a kép melletti `<név>.cxf`-et keresi, ami a piszkozat mellett épp
   NINCS — a piszkozat projektje az `autosave.cxf`. Emiatt a „Kollázs
   szerkesztése" gomb hatástalan lett volna a piszkozaton, pedig a spec
   6. szakasza szerint ott is működik.

A befejezés a MEGLÉVŐ mentő kódútra megy (`createCollage`,
`replaceExisting=True`) — a spec 5.1 mért igazolása szerint az eredeti is
ugyanazt a fájlnevet írja felül (`AI10.jpg` 46 KB → 2440 KB), nem
sorszámoz mellé.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.collage.autosave import AUTOSAVE_NAME
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_kollazs_jelzesre


class _Photo:
    def __init__(self, folder_path, name, caption=None, width=400, height=300):
        self.folder_path = folder_path
        self.name = name
        self.caption = caption
        self.width = width
        self.height = height


class _Photos:
    def __init__(self, photos):
        self.photos = list(photos)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "Nyaralás 2026"
    root.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / name, size=(80, 60))
    return root


@pytest.fixture
def kollazsok_mappa(tmp_path):
    return tmp_path / "Kollázsok"


@pytest.fixture
def settings(tmp_path, kollazsok_mappa):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY

    beallitasok = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    beallitasok.setValue(COLLAGE_OUTPUT_DIR_KEY, str(kollazsok_mappa))
    return beallitasok


@pytest.fixture
def host(qt_app, settings, library, tmp_path):
    from picasapy.app.collage_controller import CollageMixin

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            # az indexelő ág (`_index_saved_collage`) a mentés után ezt
            # kéri; enélkül csak zajos naplót írna
            self._db_path = tmp_path / "index.db"
            self._photos = _Photos(
                [
                    _Photo(str(library), "a.jpg", "Alma"),
                    _Photo(str(library), "b.jpg", None, 300, 400),
                    _Photo(str(library), "c.jpg", "Cica", 200, 200),
                ]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

        def _collage_output_width(self):
            # az éles 5120 (spec 9.1) egy tesztben 60 MB-os vászon —
            # ezek az állítások a fájlokról és az állapotról szólnak
            return 240

    példány = _Host()
    yield példány
    assert példány.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


@pytest.fixture
def piszkozat(host, kollazsok_mappa) -> Path:
    """Mentett, majd bezárt piszkozat — pontosan az, amit a felhasználó
    a Kollázsok albumban talál."""
    host.openCollage([0, 1, 2])
    host.saveCollageDraft()
    host.closeCollage()
    kepek = sorted(kollazsok_mappa.glob("*.jpg"))
    assert len(kepek) == 1, f"a piszkozatnak egy képe van, nem {kepek}"
    assert (kollazsok_mappa / AUTOSAVE_NAME).exists()
    return kepek[0]


class TestAPiszkozatFelismerese:
    def test_a_mentett_piszkozat_PISZKOZATNAK_latszik(self, host, piszkozat):
        """Enélkül a felületnek nincs mihez kötnie sem a tiltást, sem a
        „Létrehozás" gombot."""
        assert host.isCollageDraft(str(piszkozat)) is True

    def test_sima_fenykep_NEM_piszkozat(self, host, library):
        assert host.isCollageDraft(str(library / "a.jpg")) is False

    def test_ures_utvonal_NEM_piszkozat(self, host):
        assert host.isCollageDraft("") is False


class TestAPiszkozatUjranyitasa:
    def test_a_piszkozat_visszanyilik_szerkesztesre(self, host, piszkozat):
        """Spec 6.: a „Kollázs szerkesztése" a PISZKOZATON is működik.

        A #1002 kódútja a kép melletti `<név>.cxf`-et kereste, ami itt
        nincs — a piszkozat projektje az `autosave.cxf`."""
        host.closeCollage()

        host.openCollageProject(str(piszkozat))

        assert host.collageOpen is True
        assert host.collageClipCount == 3
        assert host.collageSavedPath == str(piszkozat)


class TestABefejezes:
    def test_a_befejezes_KESZ_kollazst_hagy(self, host, piszkozat, kollazsok_mappa):
        """A „Létrehozás" után: ugyanaz a fájlnév, `.cxf` párral, és a
        piszkozat automentése eltűnik — a kép többé nem piszkozat."""
        host.closeCollage()

        megjott, _args = varj_kollazs_jelzesre(
            host.collageDone, lambda: host.finishCollageDraft(str(piszkozat))
        )

        assert megjott, "a befejezés nem futott le"
        assert sorted(p.name for p in kollazsok_mappa.glob("*.jpg")) == [
            piszkozat.name
        ], "a befejezés új nevet adott a kollázsnak"
        assert piszkozat.with_suffix(".cxf").exists(), "nincs projektfájl-pár"
        assert not (kollazsok_mappa / AUTOSAVE_NAME).exists()
        assert host.isCollageDraft(str(piszkozat)) is False

    def test_sima_fenykepre_a_befejezes_NEM_csinal_semmit(self, host, library):
        """Egy tetszőleges képre kattintva nem indulhat renderelés."""
        host.finishCollageDraft(str(library / "a.jpg"))

        assert host.collageRendering is False
