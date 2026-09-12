"""#819: a `full_res` sáv-jelzőnek VAN fogyasztója az előnézetben.

## A lelet (a jegy törzse)

A szűrő-regiszterben három sáv-jelző van (`fullres`, `slow`, `resizes`);
a #382 adatként bevezette őket, de egyetlen fogyasztójuk sem volt. Az
előnézet megkapta a jelentést, és a jelzőket eldobta.

**19 szűrő** `fullres`-t kér: ezek csak teljes felbontáson adnak helyes
eredményt. Nálunk mindet a 2560 képpontra kicsinyített előnézeten
futtattuk, tehát a felhasználó MÁST látott, mint amit a mentett kép
tartalmaz.

## Amit ez a próba mér

A dekódolás felbontását — nem a jelző értékét. A jelző olvasása
önmagában semmit nem bizonyít: a hiba pont az volt, hogy megvolt az adat,
és nem történt tőle semmi.
"""

from __future__ import annotations

import pytest
from PIL import Image

from picasapy.ini.filters import FilterOp


def _nagy_jpeg(path, size=(3200, 2400)):
    """A 2560-as előnézeti korlátnál NAGYOBB kép."""
    kep = Image.new("RGB", size)
    szeles, magas = size
    for x in range(0, szeles, 16):
        for y in range(0, magas, 16):
            ertek = 40 + (x * 180 // szeles)
            kep.paste((ertek, ertek // 2, 255 - ertek), (x, y, x + 16, y + 16))
    kep.save(path, "JPEG", quality=60)
    return path


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


def _forras_meret(provider, kulcs: str):
    """A GYORSÍTÓTÁRAZOTT forráskép mérete — ezen dől el a kérdés."""
    bejegyzes = provider._sources.get(kulcs)
    assert bejegyzes is not None, "nincs eltárolt forrás"
    tomb = bejegyzes[2]
    assert tomb is not None, "a forrás nem dekódolódott"
    return tomb.shape[1], tomb.shape[0]


class TestAFullResLanc:
    """`fullres` szűrőnél a forrás TELJES felbontásban dekódolódik."""

    def test_a_fullres_szuro_teljes_felbontast_kap(self, provider, tmp_path):
        foto = _nagy_jpeg(tmp_path / "nagy.jpg")
        #: az `unsharp2` a 19 `fullres` szűrő egyike
        provider.register("1", foto, (FilterOp("unsharp2", ("1", "0.5")),))

        assert _forras_meret(provider, "1") == (3200, 2400), (
            "a fullres lánc forrása kicsinyítve dekódolódott — a felhasználó "
            "mást lát, mint amit a mentett kép tartalmaz"
        )

    def test_fullres_NELKUL_marad_a_korlat(self, provider, tmp_path):
        """A korlát nem díszítés: a kicsinyített dekód teszi gyorssá az
        előnézetet. Csak ott adjuk fel, ahol a jelző kéri."""
        foto = _nagy_jpeg(tmp_path / "nagy2.jpg")
        provider.register("2", foto, (FilterOp("sepia", ("1",)),))

        szeles, _magas = _forras_meret(provider, "2")
        assert szeles == 2560, f"a korlát nem érvényesült: {szeles}"

    def test_ures_lancnal_is_marad_a_korlat(self, provider, tmp_path):
        foto = _nagy_jpeg(tmp_path / "nagy3.jpg")
        provider.register("3", foto, ())

        assert _forras_meret(provider, "3")[0] == 2560


class TestAMegjelenitettKep:
    """A MEGJELENÍTETT előnézet a felbontástól függetlenül korlátos marad."""

    def test_a_fullres_elonezet_is_a_korlatra_kicsinyul(
        self, provider, tmp_path
    ):
        foto = _nagy_jpeg(tmp_path / "nagy4.jpg")
        provider.register("4", foto, (FilterOp("unsharp2", ("1", "0.5")),))

        kep = provider.requestImage("4", None, None)

        assert max(kep.width(), kep.height()) == 2560, (
            f"a megjelenített előnézet {kep.width()}×{kep.height()} — a "
            "teljes felbontású kép a felületre is kikerült"
        )


class TestAGyorsitotar:
    """A kicsinyített és a teljes forrás NEM keveredhet."""

    def test_a_korlatos_forras_utan_a_fullres_UJRA_dekodol(
        self, provider, tmp_path
    ):
        foto = _nagy_jpeg(tmp_path / "nagy5.jpg")
        provider.register("5", foto, (FilterOp("sepia", ("1",)),))
        assert _forras_meret(provider, "5")[0] == 2560

        provider.register("5", foto, (FilterOp("unsharp2", ("1", "0.5")),))

        assert _forras_meret(provider, "5") == (3200, 2400), (
            "a gyorsítótárazott, kicsinyített forrást használta fel a "
            "fullres lánchoz"
        )
