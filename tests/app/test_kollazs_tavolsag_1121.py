r"""A rácsvastagság-csúszka ÚJRARENDEZI a vásznat (#1121).

## A tulajdonos jelentése (v0.8.26)

> „A Mozaik elrendezés esetén nem működik a rács vastagsága, hiába
> állítom be."

## A lelet — a rajzoló jó, a KÖTÉS hiányzott

A kollázs-kutató kör mérése (hat kép, `picturegrid`, háttérképpontok a
lapon): térköz 0,0 → **0**, 0,5 → **103 428**, 1,0 → **178 469**. A rajzoló
tehát helyesen veszi figyelembe a térközt.

A `setCollageSpacing` viszont eltárolta az értéket és jelzett, de **nem
rendezte újra** a vásznat — a `setCollageFormat`/`setCollageOrientation`
mintájából hiányzott a `_relayout_for_page_shape()`. A felhasználó ezért a
RÉGI elrendezést látta, és jogosan mondta, hogy a csúszka nem csinál semmit.

A térköz ugyanis nem csak rajzolási paraméter: a **rácsos témák
cellamérete** tőle függ, tehát a PAKOLÁS bemenete.

⚠️ **Nem mai regresszió** — a v0.8.20-on ugyanez a mérés ugyanezt adja.
"""

from __future__ import annotations

import pytest

from tests.app.test_collage_controller_943 import host, library  # noqa: F401


def _geometria(gazda) -> list[tuple[float, float, float, float]]:
    """A csomópontok helye és mérete — ez változik újrarendezéskor."""
    return [
        (n.center_x, n.center_y, n.width, n.height) for n in gazda._nodes()
    ]


@pytest.fixture
def racs(host):  # noqa: F811
    """Rácsos témára állított, nyitott kollázs."""
    host.openCollage([0, 1, 2])
    host.setCollageTheme("picturegrid")
    return host


class TestATavolsagUjrarendez:
    def test_a_csuszka_MEGVALTOZTATJA_az_elrendezest(self, racs):
        elotte = _geometria(racs)

        racs.setCollageSpacing(1.0)

        assert _geometria(racs) != elotte, (
            "a térköz-csúszka nem rendezte újra a vásznat (#1121)"
        )

    def test_a_visszaallitas_is_hat(self, racs):
        racs.setCollageSpacing(1.0)
        nagy = _geometria(racs)

        racs.setCollageSpacing(0.0)

        assert _geometria(racs) != nagy

    def test_az_ertek_tenylegesen_eltarolodik(self, racs):
        racs.setCollageSpacing(0.5)

        assert racs.collageSpacing == pytest.approx(0.5)

    def test_az_azonos_ertek_NEM_rendez_ujra(self, racs):
        """Fölösleges újrarendezés a kézi elrendezést vinné el."""
        racs.setCollageSpacing(0.5)
        elotte = _geometria(racs)

        racs.setCollageSpacing(0.5)

        assert _geometria(racs) == elotte
