"""#7385: a Hangolás pipettája a finetune2 réteg ELŐTTI lánc képéből mintáz.

Az eredeti Picasában (J5a, `job-852`) a pipetta p4-e a KÉP FORRÁSÁNAK színe:
a beige folt (`c89779`) az `ffc89779`-et írja akkor is, ha a Színhőmérséklet a
jobb szélen áll (a folt előnézete ilyenkor `cf9c54`), és akkor is, ha a folt
az előző mintavétel óta már szürke (`a1a1a1`). A PicasaPy a MEGJELENÍTETT
(szerkesztett) előnézetből mintázott, így ilyenkor `ffcf9c54`-et, illetve a
már semlegesített szürkét írta.

A mintavétel 5x5 képpontos területátlag (a #7345 E23 mérése; a méret a B14
felvételig kimondott feltevés, ld. `test_pipetta_mintavetel_gyorsitotar_7385`),
a vágás kezelése a mai. A tesztképen a foltok 40 képpontosak, az ablak végig a
foltban marad.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

_N = 4  # 4x4 folt, mint a `color_patches.jpg`
_FOLT_PX = 40
#: a J5-ös mintakép foltjai (`job-855` 13. kocka: módosítatlan kép), sor-oszlop
#: sorrendben; a képernyőkép 1-2 szintes ingadozását a telített foltoknál
#: kerekítettük (a mintakép tiszta primerei).
_FOLTOK = (
    ((255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)),
    ((0, 255, 255), (255, 0, 255), (255, 255, 255), (0, 0, 0)),
    ((128, 128, 128), (0xC8, 0x97, 0x79), (0x3C, 0x5A, 0x96), (0x5B, 0x8C, 0x3B)),
    ((0xE5, 0xC8, 0x3C), (0x77, 0x3C, 0x8C), (0xF0, 0xF0, 0xF0), (0x1E, 0x1E, 0x1E)),
)
#: a beige folt a 3. sor 2. oszlopában (0-tól: 2. sor, 1. oszlop); a közepe
#: normált koordinátában
_BEIGE_NX = (1 * _FOLT_PX + _FOLT_PX / 2) / (_N * _FOLT_PX - 1)
_BEIGE_NY = (2 * _FOLT_PX + _FOLT_PX / 2) / (_N * _FOLT_PX - 1)
_BEIGE = "ffc89779"
_BETOLTOTT = "finetune2=1,0,0,0,ffccc6b2,0;"


def _foltos_kep(ut: Path) -> Path:
    kep = Image.new("RGB", (_N * _FOLT_PX, _N * _FOLT_PX))
    for sor in range(_N):
        for oszlop in range(_N):
            kep.paste(
                _FOLTOK[sor][oszlop],
                (oszlop * _FOLT_PX, sor * _FOLT_PX, (oszlop + 1) * _FOLT_PX, (sor + 1) * _FOLT_PX),
            )
    kep.save(ut, "PNG")
    return ut


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def controller(qt_app, provider):
    from picasapy.app.edit_controller import EditController

    return EditController(provider)


@pytest.fixture
def foltok(tmp_path):
    return _foltos_kep(tmp_path / "foltok.png")


def _megnyit(controller, kep: Path, lanc: str | None = None) -> None:
    if lanc is not None:
        (kep.parent / ".picasa.ini").write_text(f"[{kep.name}]\nfilters={lanc}\n", encoding="utf-8")
    controller.beginEdit("1", str(kep))
    assert controller.waitForBackgroundWorkers(10.0)


def _varj_a_rajzra(controller) -> None:
    assert controller.waitForBackgroundWorkers(10.0), "az előnézeti worker nem állt le"


def _p4_utolso_reteg(controller) -> str:
    """A lánc UTOLSÓ `finetune2` rétegének p4-e (a látogatás rétege)."""
    sorok = [
        elem.split("=", 1)[1].split(",")
        for elem in str(controller.chainValue).split(";")
        if elem.startswith("finetune2=")
    ]
    assert sorok, controller.chainValue
    return sorok[-1][4]


def _megjelenitett(provider, x: float, y: float) -> tuple[int, int, int]:
    """A MEGJELENÍTETT előnézet színe a normált ponton (a mérő nézete)."""
    szin = provider.sample_color("1", x, y)
    assert szin is not None
    return szin


def _hex(szin: tuple[int, int, int]) -> str:
    return "ff%02x%02x%02x" % szin


class TestForrasbolMintaz:
    def test_ujabb_mintavetel_nem_nulla_homerseklet_mellett_a_forras_szinet_irja(
        self, controller, provider, foltok
    ):
        """J5a 23-25. kocka: a Színhőmérséklet a jobb szélen, a folt előnézete
        `cf9c54`; az újabb mintavétel p4-e ennek ELLENÉRE a forrás `c89779`."""
        _megnyit(controller, foltok)
        assert controller.pickNeutralColor(_BEIGE_NX, _BEIGE_NY) is True
        assert _p4_utolso_reteg(controller) == _BEIGE

        controller.setFinetune(0.0, 0.0, 0.0, 1.0)
        _varj_a_rajzra(controller)
        # a próba feltétele: az előnézet tényleg más, mint a forrás
        assert _hex(_megjelenitett(provider, _BEIGE_NX, _BEIGE_NY)) != _BEIGE

        assert controller.pickNeutralColor(_BEIGE_NX, _BEIGE_NY) is True

        assert _p4_utolso_reteg(controller) == _BEIGE

    def test_elobb_a_homerseklet_utana_a_mintavetel_is_a_forras_szinet_irja(
        self, controller, provider, foltok
    ):
        """J5a eredeti sorrendje: a Színhőmérséklet a jobb szélre, aztán a
        mintavétel. A p4 a forrás, a Színhőmérséklet megmarad (a látogatás
        ugyanazt a réteget írja, egy visszavonási lépés)."""
        _megnyit(controller, foltok)
        controller.setFinetune(0.0, 0.0, 0.0, 1.0)
        _varj_a_rajzra(controller)
        assert _hex(_megjelenitett(provider, _BEIGE_NX, _BEIGE_NY)) != _BEIGE

        assert controller.pickNeutralColor(_BEIGE_NX, _BEIGE_NY) is True

        assert _p4_utolso_reteg(controller) == _BEIGE
        assert controller.colorTemp == 1.0
        assert str(controller.chainValue).count("finetune2=") == 1

    def test_a_mar_semlegesitett_folton_az_ujabb_mintavetel_is_a_forras_szine(
        self, controller, provider, foltok
    ):
        """J5a 15. kocka: az első mintavétel után a folt szürke (`a1a1a1`),
        a következő mintavétel p4-e mégis a forrás `c89779`."""
        _megnyit(controller, foltok)
        controller.pickNeutralColor(_BEIGE_NX, _BEIGE_NY)
        _varj_a_rajzra(controller)
        felengedve = _megjelenitett(provider, _BEIGE_NX, _BEIGE_NY)
        assert _hex(felengedve) != _BEIGE, "a próba feltétele: a folt már nem beige"

        controller.pickNeutralColor(_BEIGE_NX, _BEIGE_NY)

        assert _p4_utolso_reteg(controller) == _BEIGE

    def test_a_teljes_lanc_minden_mintaja_a_reteg_elotti_kep(self, controller, provider, foltok):
        """A minta a látogatás rétege ELŐTTI lánc képe: egy korábbi effekt
        (itt fekete-fehér) látszik benne, a réteg saját hatása nem."""
        _megnyit(controller, foltok)
        controller.applyEffect("bw")
        _varj_a_rajzra(controller)
        elvart = _hex(_megjelenitett(provider, _BEIGE_NX, _BEIGE_NY))
        assert elvart != _BEIGE, "a próba feltétele: a bw megváltoztatta a foltot"

        controller.pickNeutralColor(_BEIGE_NX, _BEIGE_NY)
        controller.setFinetune(0.0, 0.0, 0.0, 1.0)
        _varj_a_rajzra(controller)
        controller.pickNeutralColor(_BEIGE_NX, _BEIGE_NY)

        assert _p4_utolso_reteg(controller) == elvart

    def test_a_betoltott_reteg_hatasa_benne_van_az_uj_latogatas_mintajaban(
        self, controller, provider, foltok
    ):
        """J3d/J4a/J6c: a betöltött `finetune2` mellé új réteg kerül, tehát a
        betöltött réteg a RÉTEG ELŐTTI lánc része."""
        _megnyit(controller, foltok, _BETOLTOTT)
        # a betöltött réteg (p4 = ffccc6b2) átszínezi a beige foltot
        elvart = _hex(_megjelenitett(provider, _BEIGE_NX, _BEIGE_NY))
        assert elvart != _BEIGE, "a próba feltétele: a betöltött réteg hat a foltra"

        controller.pickNeutralColor(_BEIGE_NX, _BEIGE_NY)
        controller.setFinetune(0.0, 0.0, 0.0, 1.0)
        _varj_a_rajzra(controller)
        controller.pickNeutralColor(_BEIGE_NX, _BEIGE_NY)

        assert _p4_utolso_reteg(controller) == elvart

    def test_vagasnal_a_pont_a_kirajzolt_kepre_vonatkozik(self, controller, provider, foltok):
        """A mai vágás-kezelés marad: a normált pont a VÁGOTT kép pontja
        (a forrás 25-75%-os sávjának 25%-a a forrás 37,5%-a: a beige oszlop)."""
        _megnyit(controller, foltok)
        controller.applyCrop(0.25, 0.0, 0.5, 1.0)
        _varj_a_rajzra(controller)

        controller.pickNeutralColor(0.25, _BEIGE_NY)
        controller.setFinetune(0.0, 0.0, 0.0, 1.0)
        _varj_a_rajzra(controller)
        controller.pickNeutralColor(0.25, _BEIGE_NY)

        assert _p4_utolso_reteg(controller) == _BEIGE

    def test_a_kepen_kivuli_pont_tovabbra_is_elutasitott(self, controller, foltok):
        _megnyit(controller, foltok)

        assert controller.pickNeutralColor(5.0, 5.0) is False
        assert controller.canUndo is False

    def test_az_effekt_szin_pipetta_a_megjelenitett_kepbol_mintaz(
        self, controller, provider, foltok
    ):
        """A másik pipetta (#5674, effekt-szín paraméter) nem tartozik ide:
        az továbbra is azt a színt adja, amit a felhasználó lát."""
        _megnyit(controller, foltok)
        controller.pickNeutralColor(_BEIGE_NX, _BEIGE_NY)
        _varj_a_rajzra(controller)
        latott = _megjelenitett(provider, _BEIGE_NX, _BEIGE_NY)

        szin = controller.pickEffectColor(_BEIGE_NX, _BEIGE_NY)

        assert szin == "#%02x%02x%02x" % latott
