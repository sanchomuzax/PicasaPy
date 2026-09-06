"""#2492: a nagyítás-csúszka MÉRT leképezése.

## A tulajdonos jelentése (v0.8.293)

> „az »1:1« nem akkorára nagyít, mint az igazi picasa… a zoom csúszkát
> teljesen balra húzva »fit«-tel"

Nálunk a csúszka a SZORZÓT tárolta lineárisan (`from: 0.25, to: 8`), ezért
az „1:1" nem a felezőpontra esett, és a bal szélső állás nem az illesztés
volt, hanem annak a negyede.

## A MÉRT szerződés

Forrás: `docs/specs/ui-audit-editor.md`, „A szerkesztő NAGYÍTÁS-HÁRMASA".
A csúszka **normalizált** értéket tárol, `[0, 1]`-re vágva
(`0x005d13a9` `fldz`, `0x005d13c6` `fld1`), és a szorzót két folytonos ág
adja (`0x00a601cf`–`0x00a60221`):

    0 ≤ v < 0,5 :  1 + (2^(2v) − 1) · (r − 1)
    0,5 ≤ v ≤ 1 :  r · 2^(4·(v − 0,5))

ahol `r` = a valódi és az illesztett méret aránya. Rögzített pontok:
**v=0 → 1** (illesztés), **v=0,5 → r** (100 %), **v=1 → 4r** (400 %).

A gombok ugyanezt állítják (`FUN_005d59f0`): `fit` → 0.0f, `1to1` → 0.5f;
a visszafelé irány (`FUN_005d1c70`) az ÉRTÉKBŐL választja ki, melyik gomb
az aktív.
"""

from __future__ import annotations

import math

import pytest
from PySide6.QtCore import QMetaObject, QObject, Q_ARG, Qt


def _hivd(qt_app, obj, nev, *args):
    QMetaObject.invokeMethod(
        obj, nev, Qt.ConnectionType.DirectConnection,
        *[Q_ARG("QVariant", a) for a in args],
    )
    qt_app.processEvents()


@pytest.fixture
def nezo(qml_app, qt_app):
    window, _controller, _engine = qml_app
    qt_app.processEvents()
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    return viewer


def _r(qt_app, nezo) -> float:
    """A MÉRT `r`: a szorzó a v = 0,5-ös rögzített pontban."""
    _hivd(qt_app, nezo, "setZoomValue", 0.5)
    return nezo.property("zoomFactor")


class TestARogzitettPontok:
    def test_a_bal_szelso_allas_az_ILLESZTES(self, nezo, qt_app):
        """A tulajdonos jelentésének első fele: „a csúszkát teljesen balra
        húzva »fit«". Korábban a bal vég 0,25 volt — az illesztett méret
        NEGYEDE."""
        _hivd(qt_app, nezo, "setZoomValue", 0)
        assert nezo.property("zoomFactor") == 1.0
        assert nezo.property("zoomMode") == "fit"

    def test_a_FELEZOPONT_a_valodi_meret(self, nezo, qt_app):
        """A jelentés másik fele: az „1:1" a csúszka KÖZEPE."""
        _hivd(qt_app, nezo, "setZoomValue", 0.5)
        assert nezo.property("zoomMode") == "actual"

    def test_a_jobb_szelso_allas_400_szazalek(self, nezo, qt_app):
        r = _r(qt_app, nezo)
        _hivd(qt_app, nezo, "setZoomValue", 1)
        assert abs(nezo.property("zoomFactor") - 4 * r) < 1e-9

    def test_az_1to1_gomb_a_FELEZOPONTRA_all(self, nezo, qt_app):
        """`FUN_005d59f0`: a `1to1` a 0.5f-et adja át."""
        _hivd(qt_app, nezo, "setZoomValue", 0.9)
        _hivd(qt_app, nezo, "zoomActual")
        assert nezo.property("zoomValue") == 0.5

    def test_a_fit_gomb_a_NULLARA_all(self, nezo, qt_app):
        _hivd(qt_app, nezo, "setZoomValue", 0.9)
        _hivd(qt_app, nezo, "zoomFit")
        assert nezo.property("zoomValue") == 0.0


class TestAGorbe:
    @pytest.mark.parametrize(
        "v,szorzo_r_hez",
        [(0.5, 1.0), (0.625, math.sqrt(2)), (0.75, 2.0), (0.875, 2 * math.sqrt(2)), (1.0, 4.0)],
    )
    def test_a_felso_fel_negyedenkent_DUPLAZODIK(self, nezo, qt_app, v, szorzo_r_hez):
        """`2^(4·0,25) = 2` — a mért tábla: 100 · 141 · 200 · 283 · 400 %."""
        r = _r(qt_app, nezo)
        _hivd(qt_app, nezo, "setZoomValue", v)
        assert abs(nezo.property("zoomFactor") - r * szorzo_r_hez) < 1e-6

    def test_az_also_fel_a_ket_rogzitett_pontot_koti_ossze(self, nezo, qt_app):
        """`1 + (2^(2v) − 1)·(r − 1)` — a v=0,25-ös pont a képletből."""
        r = _r(qt_app, nezo)
        _hivd(qt_app, nezo, "setZoomValue", 0.25)
        vart = 1 + (math.pow(2, 0.5) - 1) * (r - 1)
        assert abs(nezo.property("zoomFactor") - vart) < 1e-6

    def test_a_ket_ag_FOLYTONOS(self, nezo, qt_app):
        """A töréspontnál (0,5) a két ág ugyanazt adja — a képlet enélkül
        ugrana a valódi méretnél, épp ott, ahol a felhasználó a legtöbbet
        jár."""
        r = _r(qt_app, nezo)
        _hivd(qt_app, nezo, "setZoomValue", 0.5 - 1e-7)
        also = nezo.property("zoomFactor")
        _hivd(qt_app, nezo, "setZoomValue", 0.5 + 1e-7)
        felso = nezo.property("zoomFactor")
        assert abs(also - r) < 1e-5 and abs(felso - r) < 1e-5

    def test_a_gorbe_SEHOL_NEM_CSOKKEN(self, nezo, qt_app):
        """⚠️ Szigorú növekedést itt NEM lehet állítani, és ez a KÉPLETBŐL
        következik: ha a kép belefér a nézetbe, `r = 1`, és az alsó ág
        `1 + (2^(2v) − 1)·(r − 1)` azonosan 1 — vagyis LAPOS. A próba
        fixtúrájának képe pont ilyen. A monotonitás viszont mindkét ágon
        elvárás: egy csökkenő szakasz azt jelentené, hogy a csúszka
        jobbra húzása KISEBBÍT."""
        elozo = -1.0
        for i in range(21):
            _hivd(qt_app, nezo, "setZoomValue", i / 20)
            most = nezo.property("zoomFactor")
            assert most >= elozo - 1e-9, (
                f"v={i / 20}: {most} kisebb, mint az előző {elozo}"
            )
            elozo = most

    def test_a_FELSO_fel_szigoruan_no(self, nezo, qt_app):
        """A felső ág (`r · 2^(4(v−0,5))`) `r`-től függetlenül nő."""
        elozo = -1.0
        for i in range(10, 21):
            _hivd(qt_app, nezo, "setZoomValue", i / 20)
            most = nezo.property("zoomFactor")
            assert most > elozo, f"v={i / 20}: {most} nem nagyobb, mint {elozo}"
            elozo = most


class TestAVagasEsABeakadas:
    def test_a_tartomanyon_kivulit_VAGJA(self, nezo, qt_app):
        """MÉRVE (`0x005d13a9` `fldz`, `0x005d13c6` `fld1`): az érték soha
        nem megy 0 alá vagy 1 fölé — az illesztettnél kisebbre és a 400 %
        fölé nem lehet állítani."""
        _hivd(qt_app, nezo, "setZoomValue", -3)
        assert nezo.property("zoomValue") == 0.0
        _hivd(qt_app, nezo, "setZoomValue", 42)
        assert nezo.property("zoomValue") == 1.0

    def test_a_leptetes_BEAKAD_a_valodi_meretnel(self, nezo, qt_app):
        """`FUN_005d1300`: a 0,5-öt átlépő lépés pontosan ott áll meg."""
        _hivd(qt_app, nezo, "setZoomValue", 0.48)
        _hivd(qt_app, nezo, "lepjZoom", 0.05)      # 0,53 lenne
        assert nezo.property("zoomValue") == 0.5
        assert nezo.property("zoomMode") == "actual"

    def test_a_beakadas_LEFELE_is_all(self, nezo, qt_app):
        _hivd(qt_app, nezo, "setZoomValue", 0.52)
        _hivd(qt_app, nezo, "lepjZoom", -0.05)
        assert nezo.property("zoomValue") == 0.5

    def test_a_detentrol_TOVABB_lehet_lepni(self, nezo, qt_app):
        """⚠️ Enélkül a csúszka beragadna a 100 %-on: a beakadás nem
        zárhatja be a felhasználót."""
        _hivd(qt_app, nezo, "setZoomValue", 0.5)
        _hivd(qt_app, nezo, "lepjZoom", 0.05)
        assert nezo.property("zoomValue") > 0.5

    def test_a_detenten_ATUGRO_nagy_lepes_sem_ugorja_at(self, nezo, qt_app):
        _hivd(qt_app, nezo, "setZoomValue", 0.1)
        _hivd(qt_app, nezo, "lepjZoom", 0.8)
        assert nezo.property("zoomValue") == 0.5


class TestACsuszkaBekotese:
    def test_a_csuszka_ertekkeszlete_a_MERT_normalizalt(self, nezo, qml_app, qt_app):
        window, _controller, _engine = qml_app
        csuszka = window.findChild(QObject, "zoomSlider")
        assert csuszka is not None
        assert csuszka.property("from") == 0.0
        assert csuszka.property("to") == 1.0

    def test_a_csuszka_a_zoomValue_t_koveti(self, nezo, qml_app, qt_app):
        window, _controller, _engine = qml_app
        csuszka = window.findChild(QObject, "zoomSlider")
        _hivd(qt_app, nezo, "setZoomValue", 0.75)
        assert abs(csuszka.property("value") - 0.75) < 1e-6
