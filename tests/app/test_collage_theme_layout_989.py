"""#989: a téma-választó HAT a vászonra — a panel a téma pakolóját futtatja.

A 0.8.0 kiadás legsúlyosabb hiánya: a Kollázs-panel téma-választója
látszott és kattintható volt, a vászon mégis mindig ugyanazt mutatta. A
`collage_layout.laid_out` téma nélküli szignatúrával a Képkupac szórását
hívta, a `_relayout` pedig csak a keretet adta át.

Amit ez a fájl állít:

1. a hat téma a vásznon HAT KÜLÖNBÖZŐ elrendezést ad,
2. a determinisztikus témák a rájuk jellemző szabályos alakot adják,
3. a téma-váltás UTÁN a **mentett** kimenet is az új elrendezést mutatja
   (a `.cxf` a vászon csomópontjait írja, a JPEG pedig azokból készül).

⚠️ Beégetett SHA/MD5 sehol: a képpont-azonosság a platformot is
szerződésbe foglalná, és a Windows-lábon némán bukna (#942 tanulsága). Az
állítások szerkezetiek, illetve két kimenet ÖSSZEHASONLÍTÁSÁN alapulnak.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.collage.cxf import loads
from picasapy.collage.themes import (
    COLLAGE_THEMES,
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    PICTUREGRID,
    PICTUREPILE,
    REGULARGRID,
)

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
    for name, meret in (
        ("a.jpg", (80, 60)),
        ("b.jpg", (60, 80)),
        ("c.jpg", (70, 70)),
        ("d.jpg", (96, 54)),
        ("e.jpg", (54, 96)),
    ):
        make_jpeg(root / name, size=meret)
    return root


@pytest.fixture
def kimenet(tmp_path):
    return tmp_path / "Kollázsok"


@pytest.fixture
def host(qt_app, tmp_path, library, kimenet):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin

    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(kimenet))

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos(
                [
                    _Photo(str(library), "a.jpg", "Alma", 400, 300),
                    _Photo(str(library), "b.jpg", None, 300, 400),
                    _Photo(str(library), "c.jpg", "Cica", 200, 200),
                    _Photo(str(library), "d.jpg", None, 480, 270),
                    _Photo(str(library), "e.jpg", None, 270, 480),
                ]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

        def _collage_output_width(self):
            # az éles 5120 képpont tesztben másodperceket és tíz-megabájtos
            # tömböket jelentene; ezek az állítások az ELRENDEZÉSRŐL szólnak
            return 320

    instance = _Host()
    yield instance
    assert instance.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


@pytest.fixture
def nyitott(host):
    host.openCollage([0, 1, 2, 3, 4])
    return host


def _wait(signal, action, timeout_ms=20000):
    """A műveletet a jelzésre FELIRATKOZVA indítja, majd bevárja azt.

    #988: ugyanaz a GC-szünetes közös segéd, mint a testvér kollázs-
    tesztekben — ez a fájl a #949-cel AZONOS mintát használt és ugyanazt
    a háttérszálas kollázs-mentést hajtja, tehát ugyanaz a
    versenyhelyzet érte volna el, amint a #949 elhallgat."""
    return varj_kollazs_jelzesre(signal, action, timeout_ms)


def _geometria(vezerlo) -> tuple:
    """A vászon elrendezésének ujjlenyomata — rendezve, mert az állítás az
    elrendezésről szól, nem a rétegsorrendről."""
    return tuple(
        sorted(
            (
                round(node.center_x, 1),
                round(node.center_y, 1),
                round(node.width, 1),
                round(node.height, 1),
                round(node.theta, 4),
            )
            for node in vezerlo.collageNodes.nodes
        )
    )


class TestATemavaltasHatAVasznara:
    def test_a_hat_tema_hat_kulonbozo_elrendezest_ad(self, nyitott):
        """A jegy MÉRCÉJE. A Képkockamozaikhoz rögzített kép kell —
        anélkül az eredeti is az alap pakolóra esik vissza."""
        ujjlenyomatok: dict[str, tuple] = {}
        for tema in COLLAGE_THEMES:
            nyitott.setCollageTheme(tema)
            if tema == FRAMEGRID:
                nyitott.setCollageSelection([1])
                nyitott.setFrameCenterFromSelection()
            ujjlenyomatok[tema] = _geometria(nyitott)

        for egyik in COLLAGE_THEMES:
            for masik in COLLAGE_THEMES:
                if egyik >= masik:
                    continue
                assert ujjlenyomatok[egyik] != ujjlenyomatok[masik], (
                    f"{egyik} és {masik} UGYANAZT az elrendezést mutatja"
                )

    @pytest.mark.parametrize(
        "tema", [PICTUREGRID, REGULARGRID, CONTACTSHEET, MULTIEXP]
    )
    def test_a_kepkupachoz_kepest_mind_maskepp_all(self, nyitott, tema):
        kupac = _geometria(nyitott)
        nyitott.setCollageTheme(tema)
        assert _geometria(nyitott) != kupac

    def test_a_temavaltas_utan_is_ugyanazok_a_kepek(self, nyitott):
        elotte = sorted(Path(n.path).name for n in nyitott.collageNodes.nodes)
        for tema in COLLAGE_THEMES:
            nyitott.setCollageTheme(tema)
            assert (
                sorted(Path(n.path).name for n in nyitott.collageNodes.nodes)
                == elotte
            ), tema

    def test_a_visszavaltas_ujra_a_racsot_adja(self, nyitott):
        """A téma-váltás oda-vissza is működik: nem egyszeri „beragadás"."""
        nyitott.setCollageTheme(REGULARGRID)
        racs = _geometria(nyitott)
        nyitott.setCollageTheme(PICTUREPILE)
        assert _geometria(nyitott) != racs
        nyitott.setCollageTheme(REGULARGRID)
        assert _geometria(nyitott) == racs


class TestSzabalyosTemak:
    def test_a_racs_cellai_egyformak_es_racsban_allnak(self, nyitott):
        """Egyformák — EGY lapegység tűréssel: a cellahatárok egész
        képpontra kerekednek (`picasa_round`), tehát 1024 / 3 osztásnál a
        341 és a 342 váltakozik. Ez az eredeti viselkedése, nem hiba."""
        nyitott.setCollageTheme(REGULARGRID)
        nodes = nyitott.collageNodes.nodes
        szelessegek = [n.width for n in nodes]
        magassagok = [n.height for n in nodes]
        assert max(szelessegek) - min(szelessegek) <= 1.5
        assert max(magassagok) - min(magassagok) <= 1.5
        oszlopok = sorted({round(n.center_x, 1) for n in nodes})
        sorok = sorted({round(n.center_y, 1) for n in nodes})
        assert len(oszlopok) * len(sorok) >= len(nodes)

    def test_az_indexkep_a_fejlec_alatt_kezdodik(self, nyitott):
        nyitott.setCollageTheme(CONTACTSHEET)
        nodes = nyitott.collageNodes.nodes
        sav = round(1024 * nyitott.collagePageRatio * 0.08)
        assert min(n.center_y - n.height / 2 for n in nodes) >= sav - 1.0

    def test_a_tobbszoros_exponalas_mindent_kozepre_tesz(self, nyitott):
        nyitott.setCollageTheme(MULTIEXP)
        nodes = nyitott.collageNodes.nodes
        kozep_y = 1024 * nyitott.collagePageRatio / 2
        assert {(round(n.center_x, 0), round(n.center_y, 0)) for n in nodes} == {
            (512.0, round(kozep_y, 0))
        }

    def test_a_kepkockamozaik_a_rogzitett_kepet_kozepre_emeli(self, nyitott):
        nyitott.setCollageTheme(FRAMEGRID)
        nyitott.setCollageSelection([1])
        nyitott.setFrameCenterFromSelection()
        nodes = nyitott.collageNodes.nodes
        hangsulyos = nodes[nyitott.collageFrameCenter]
        assert Path(hangsulyos.path).name == "b.jpg"
        assert hangsulyos.center_x == pytest.approx(512.0, abs=3.0)
        assert hangsulyos.width == pytest.approx(512.0, abs=3.0)


class TestAMentettKimenet:
    """A #920 elfogadási feltétele: a mentett kép azt mutatja, amit a
    vásznon látsz — tehát a téma-váltás a MENTÉSEN is átüt."""

    def _ment(self, vezerlo, kimenet: Path) -> Path:
        elotte = set(kimenet.glob("*.jpg")) if kimenet.exists() else set()
        megjott, _ = _wait(
            vezerlo.collageDone, lambda: vezerlo.createCollage(False)
        )
        assert megjott, "nem érkezett collageDone"
        assert vezerlo.waitForBackgroundWorkers(30.0)
        # a következő mentés NE a mostanit írja felül (spec 9.2)
        vezerlo.dropSavedCollagePath()
        uj = set(kimenet.glob("*.jpg")) - elotte
        assert len(uj) == 1, f"nem pontosan egy új kollázs született: {uj}"
        return uj.pop()

    def test_a_mentett_cxf_a_VASZON_csomopontjait_irja(self, nyitott, kimenet):
        nyitott.setCollageTheme(REGULARGRID)
        vasznon = [
            (round(n.width, 3), round(n.height, 3))
            for n in nyitott.collageNodes.nodes
        ]
        jpeg = self._ment(nyitott, kimenet)
        projekt = loads(jpeg.with_suffix(".cxf").read_bytes())
        assert projekt.theme == REGULARGRID
        assert len(projekt.nodes) == len(vasznon)
        # a `.cxf` a vászon ARÁNYAIBAN tárol; a rács egyforma cellái ott is
        # egyformák maradnak — ez köti össze a mentést a látvánnyal
        szelessegek = [n.w for n in projekt.nodes]
        magassagok = [n.h for n in projekt.nodes]
        assert max(szelessegek) - min(szelessegek) <= 0.005
        assert max(magassagok) - min(magassagok) <= 0.005

    def test_a_temavaltas_utan_MAS_kep_mentodik(self, nyitott, kimenet):
        """Mozaik és Rács: a két téma minden EGYÉB beállítása azonos (nincs
        keret, az árnyék alapból ki), tehát ha a mentett képek eltérnek, az
        KIZÁRÓLAG az elrendezés különbsége lehet — a Képkupaccal szemben,
        ahol az árnyék alapértéke önmagában is más képet adna."""
        # ⚠️ NEM `cv2.imread`: a mentés útvonala ékezetes
        # (`Képek/Picasa/Kollázsok`), és az OpenCV Windowson az ilyen utat
        # NEM tudja megnyitni — `None`-t ad vissza, némán. A projektnek
        # pontosan erre van bájt-alapú olvasója (#190), a mag is azt
        # használja (`collage/render.py`). A CI windows-lába ezen bukott el.
        import cv2

        from picasapy.cvimage import read_image_bytes

        def _beolvas(ut):
            """A mag `_decode`-jának mintája: bájtok + `imdecode`."""
            payload = read_image_bytes(ut)
            assert payload is not None, f"nem olvasható: {ut}"
            return cv2.imdecode(payload, cv2.IMREAD_COLOR)

        nyitott.setCollageTheme(PICTUREGRID)
        mozaik = _beolvas(self._ment(nyitott, kimenet))
        nyitott.setCollageTheme(REGULARGRID)
        racs = _beolvas(self._ment(nyitott, kimenet))
        assert mozaik is not None and racs is not None
        assert mozaik.shape == racs.shape
        assert not (mozaik == racs).all(), "a mentett kép nem követte a témát"
