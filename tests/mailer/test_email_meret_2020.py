"""#2020 — az e-mail méret-beállítás KÉPPONTSZÁM, nem listaindex.

A korábbi `EMAIL_SIZE_PRESETS` öt fokozata **becslés** volt; a kód maga is
kimondta. A tulajdonos futó Picasa 3-ának mérése (2026-09-02,
`research/#2020-email/`) megadta a valódi fokozatokat, és a
dekompiláció is ezt támasztja alá:

* `Preferences\\EmailExportSize` **képpont-értéket** tárol, nem indexet
  (`0x00743030`), az alapértéke **480** (`0x1e0`) három független helyen
  (`0x006e1756`, `0x006e3f2b`, `0x00743094`);
* a **0** jelentése „eredeti méret" (`option_useorig`,
  `0x0074310f`–`0x0074311a`);
* a csúszka nyolc fokozata a képernyőképről: 160, 320, **480**, 640, 800,
  1024, 1200, 1600.

⚠️ A 480 a RÉGI listánkban elő sem fordult, ahogy a 160, a 320 és az 1200
sem — és az „eredeti méret" nálunk tévesen a csúszka HATODIK fokozata
volt, az eredetiben viszont nem a csúszkán van, hanem külön kapcsolón.
"""

from __future__ import annotations

import pytest

from picasapy.mailer import (
    EMAIL_SIZE_STEPS,
    EREDETI_MERET,
    resolve_email_max_dimension,
)


class TestFokozatok:
    def test_a_nyolc_MERT_fokozat(self):
        assert EMAIL_SIZE_STEPS == (160, 320, 480, 640, 800, 1024, 1200, 1600)

    def test_a_480_szerepel_benne(self):
        """A mért alapérték. Fog: a régi listánk épp ezt hagyta ki."""
        assert 480 in EMAIL_SIZE_STEPS

    def test_a_fokozatok_szigoruan_novekvok(self):
        assert list(EMAIL_SIZE_STEPS) == sorted(set(EMAIL_SIZE_STEPS))

    def test_az_eredeti_meret_NEM_fokozat(self):
        """Az eredetiben a 0 külön kapcsolóról jön, nem a csúszka végéről."""
        assert EREDETI_MERET == 0
        assert EREDETI_MERET not in EMAIL_SIZE_STEPS
        assert None not in EMAIL_SIZE_STEPS


class TestFeloldas:
    @pytest.mark.parametrize("keppont", EMAIL_SIZE_STEPS)
    def test_a_keppontszam_onmagat_adja(self, keppont):
        assert resolve_email_max_dimension(keppont) == keppont

    def test_a_nulla_eredeti_meretet_jelent(self):
        assert resolve_email_max_dimension(EREDETI_MERET) is None

    def test_a_fokozatlistan_kivuli_ertek_is_atmegy(self):
        """A mező KÉPPONTSZÁM: a Picasa 3-ból bármilyen érték jöhet.

        Fog: ha valaki visszacsempészi az index-alapú feloldást, ez bukik —
        egy régi ini-ből érkező 900 nem index, hanem méret.
        """
        assert resolve_email_max_dimension(900) == 900

    @pytest.mark.parametrize("rossz", [-1, -480])
    def test_a_negativ_ertek_hibat_ad(self, rossz):
        with pytest.raises(ValueError):
            resolve_email_max_dimension(rossz)
