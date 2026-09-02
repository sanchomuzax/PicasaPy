"""A kollázs harmadik háttérmódja: a képek ÁTLAGSZÍNE (#1004).

## Az eredeti

A `collage::avgcolor` beállítás bekapcsolva **felülír minden más
háttérbeállítást**. A beállító (`0x008364a0`):

```
spec[0x2c] = (Preferences\\collage::avgcolor != 0) ? 0 : mód
```

⚠️ Az értéket a kollázs **nem számolja**: egy adatbázis-mezőt olvas ki
(`"avgcolor"` kulcs, `0x006a4cd0`), amit a Picasa indexelője állított elő.
A képlete a kollázson KÍVÜL van, és nincs visszafejtve — a mi átlagunk
ezért **közelítés**, nem bitre azonos. Ezt a `render.py` docstringje is
kimondja, hogy egy későbbi kör ne higgye mértnek.

## Amit ez az őr állít

* a mód **felülír**: bekapcsolva a beállított egyszínű háttér NEM
  érvényesül;
* az átlag a KÉPEKBŐL jön, nem konstans;
* kép nélkül nem omlik össze (üres kollázs is renderelhető).
"""
from __future__ import annotations

import cv2
import numpy as np
import pytest

from picasapy.collage.render import CollageSettings, make_collage


def _kep(utvonal, szin_bgr) -> None:
    kep = np.full((40, 40, 3), np.array(szin_bgr, dtype=np.uint8), dtype=np.uint8)
    cv2.imwrite(str(utvonal), kep)


@pytest.fixture
def kepek(tmp_path):
    """Két egyszínű kép: tiszta kék és tiszta piros (BGR)."""
    a = tmp_path / "kek.jpg"
    b = tmp_path / "piros.jpg"
    _kep(a, (255, 0, 0))
    _kep(b, (0, 0, 255))
    return [a, b]


def _sarok(kep: np.ndarray) -> tuple[int, int, int]:
    """A vászon bal felső sarka — ott biztosan a HÁTTÉR látszik."""
    return tuple(int(c) for c in kep[0, 0])


class TestAzAvgModFelulir:
    def test_bekapcsolva_NEM_a_beallitott_szin_latszik(self, kepek):
        """A jegy lényege: az `avgcolor` minden mást felülír."""
        alap = CollageSettings(background=(0, 255, 0), background_avg=False)
        avg = CollageSettings(background=(0, 255, 0), background_avg=True)
        zold = make_collage(kepek, alap)
        atlag = make_collage(kepek, avg)
        assert _sarok(zold.image) == (0, 255, 0), "az alapeset nem a beállított szín"
        assert _sarok(atlag.image) != (0, 255, 0), (
            "az `avg` mód NEM írta felül a beállított hátteret"
        )

    def test_az_atlag_a_KEPEKBOL_jon(self, kepek):
        """Tiszta kék + tiszta piros → a kettő között, mindkét csatornán.

        Ha konstanst adnánk vissza, ez elbukna.
        """
        ki = make_collage(kepek, CollageSettings(background_avg=True))
        b, g, r = _sarok(ki.image)
        assert 100 < b < 160, f"a kék csatorna nem a két kép közt van: {b}"
        assert 100 < r < 160, f"a piros csatorna nem a két kép közt van: {r}"
        assert g < 40, f"a zöld csatornának ~0-nak kell lennie: {g}"

    def test_MAS_kepekre_MAS_atlag(self, tmp_path):
        """Ellenpróba: az érték tényleg a bemenettől függ."""
        sotet = tmp_path / "sotet.jpg"
        vilagos = tmp_path / "vilagos.jpg"
        _kep(sotet, (20, 20, 20))
        _kep(vilagos, (230, 230, 230))
        a = make_collage([sotet], CollageSettings(background_avg=True))
        b = make_collage([vilagos], CollageSettings(background_avg=True))
        assert _sarok(a.image) != _sarok(b.image)
        assert sum(_sarok(a.image)) < sum(_sarok(b.image))


class TestHataresetek:
    def test_dekodolhatatlan_kepnel_a_beallitott_hatter_marad(self, tmp_path):
        """Ha EGYETLEN kép sem dekódolható, az átlagnak nincs mihez
        nyúlnia — a beállított háttér marad, kivétel nélkül.

        ⚠️ Nem üres listával mérjük: a `make_collage` a bemenetet külön
        ellenőrzi („Kollázshoz legalább egy kép kell"), az más hibaág. A
        valós határeset az, amikor a fájlok MEGVANNAK a listában, de
        egyik sem olvasható — ilyenkor a `decoded` üres marad.
        """
        rossz = tmp_path / "nem_kep.jpg"
        rossz.write_bytes(b"ez nem jpeg")
        ki = make_collage([rossz], CollageSettings(
            background=(10, 20, 30), background_avg=True
        ))
        assert _sarok(ki.image) == (10, 20, 30)
        assert ki.used == (), "dekódolhatatlan kép mégis felhasználtnak számít"

    def test_az_alapertelmezes_KIKAPCSOLT(self):
        """A mód nem kapcsolhat be magától — az eredetiben is külön
        beállítás, és a panelen nincs is rádiógombja."""
        assert CollageSettings().background_avg is False
