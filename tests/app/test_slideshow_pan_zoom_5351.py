"""A Pan and Zoom kivágások a spec 4.6 szerkezetében (#5351).

Minden várt szám a `.eredeti/picasa-create-features.md` 4.6 képletéből jön,
rögzített törtekkel. Forrás 1000×500, nézet 1024×768.

- Alap (`0x009b4aa0`): k = min((1000 + 0.499) / 1024, (500 + 0.499) / 768),
  az egész méret round(1024·k) × round(768·k) = 667 × 500.
- B a forrás jobb széléhez tolódik: x = 1000 - 667 = 333, y = 0, mert a
  magasság egyezik. Így a méretezés előtti középpontok C_A = (333.5, 250)
  és C_B = (666.5, 250).
- A két csere (`0x0076d790`) a skálázás előtt fut; u, v a helyi LCG-ből,
  ρ0…ρ3 a CRT `_rand`-ból jön.
- Nagyobb skála: x = cx - w/2 + W·(0.2ρ1 - 0.1), y = cy - h/2 + H·(0.2ρ0 - 0.1).
  Kisebb skála: x = cx - w/2 + W·(0.2ρ3 - 0.1), y = cy - h/2 - H·0.2ρ2.
- Határolás: x' = min(max(x, 0), W - w), y' = min(max(y, 0), H - h).
"""

import pytest

from picasapy.app.slideshow_pan_zoom import _alap_meret, pan_zoom_rectangles

FORRAS = (1000, 500)
NEZET = (1024, 768)
RHO = [0.625, 0.4375, 0.25, 0.75]  # ρ0, ρ1, ρ2, ρ3
PARATLAN_CSERE = 16385 / 32768  # a 16. állapotbit 1: csere
PAROS_CSERE = 0.0  # a 16. állapotbit 0: nincs csere


def _sorozat(tortek):
    """Rögzített törtsorozat véletlenforrásként; a hívásait is visszaadja."""
    huzasok = []
    it = iter(tortek)

    def kovetkezo():
        ertek = next(it)
        huzasok.append(ertek)
        return ertek

    return kovetkezo, huzasok


def test_alap_egesz_meret_a_fit_0_499_utan():
    assert _alap_meret(*FORRAS, *NEZET) == (667, 500)
    assert _alap_meret(300, 600, *NEZET) == (300, 225)


def test_jeloltenkent_a_sajat_alapteglalap_kozepe_adja_a_kivagast():
    """u = 0.875 (A), v = 0.25 (B): A a nagyobb skálájú, ezért ρ0, ρ1 jár neki.

    A: w = 667·0.925 = 616.975, h = 500·0.925 = 462.5;
       x = 0 + (667 - 616.975)/2 - 12.5 = 12.5125, y = (500 - 462.5)/2 + 12.5 = 31.25.
    B: w = 667·0.80 = 533.6, h = 400; a bal felső sarka (333, 0):
       x = 333 + (667 - 533.6)/2 + 50 = 449.7, y = (500 - 400)/2 - 25 = 25.
    """
    helyi, helyi_huzasok = _sorozat([PAROS_CSERE, PAROS_CSERE, 0.875, 0.25])
    crt, crt_huzasok = _sorozat(RHO)

    a, b = pan_zoom_rectangles(*FORRAS, *NEZET, helyi, crt)

    assert (a.x, a.y, a.width, a.height) == pytest.approx(
        (12.5125, 31.25, 616.975, 462.5)
    )
    assert (b.x, b.y, b.width, b.height) == pytest.approx(
        (449.7, 25.0, 533.6, 400.0)
    )
    assert len(helyi_huzasok) == 4  # két csere, majd u és v
    assert len(crt_huzasok) == 4  # ρ0…ρ3


def test_nagyobb_skala_kapja_az_elso_csoportot_forditott_u_v_eseten():
    """u = 0.25 (A), v = 0.875 (B): most B a nagyobb, ő kapja ρ0, ρ1-et.

    A: kisebb, w = 533.6, h = 400, a bal felső sarka (0, 0):
       x = (667 - 533.6)/2 + 50 = 116.7, y = 25.
    B: nagyobb, w = 616.975, h = 462.5, a bal felső sarka (333, 0):
       x = 333 + (667 - 616.975)/2 - 12.5 = 345.5125, y = 31.25.
    """
    helyi, _helyi_huzasok = _sorozat([PAROS_CSERE, PAROS_CSERE, 0.25, 0.875])
    crt, _crt_huzasok = _sorozat(RHO)

    a, b = pan_zoom_rectangles(*FORRAS, *NEZET, helyi, crt)

    assert (a.x, a.y, a.width, a.height) == pytest.approx(
        (116.7, 25.0, 533.6, 400.0)
    )
    assert (b.x, b.y, b.width, b.height) == pytest.approx(
        (345.5125, 31.25, 616.975, 462.5)
    )


def test_csere_a_skalazas_elott_cserel_helyet_az_alapteglalapok_kozott():
    """Az első csere páratlan, a második páros: A és B helye felcserélődik.

    Így A (a nagyobb skálájú, u = 0.875) a B eredeti helyéről (333, 0) indul:
    x = 345.5125, y = 31.25; B a (0, 0) helyről: x = 116.7, y = 25.
    """
    helyi, helyi_huzasok = _sorozat([PARATLAN_CSERE, PAROS_CSERE, 0.875, 0.25])
    crt, _crt_huzasok = _sorozat(RHO)

    a, b = pan_zoom_rectangles(*FORRAS, *NEZET, helyi, crt)

    assert (a.x, a.y, a.width, a.height) == pytest.approx(
        (345.5125, 31.25, 616.975, 462.5)
    )
    assert (b.x, b.y, b.width, b.height) == pytest.approx(
        (116.7, 25.0, 533.6, 400.0)
    )
    assert len(helyi_huzasok) == 4
