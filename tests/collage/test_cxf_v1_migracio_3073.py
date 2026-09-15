"""#3073: a `.cxf` `version="1"` → `2` migrációja.

## A mérés

`docs/specs/kollazs-eletciklus.md` **68. szakasz** (#2593, 299. kör). A
betöltő (`FUN_00834520`) **kétszeres kapu** mögött végigszorozza a
csomópontok `scale`-jét, majd a mentés beégetve `version="2"`-t ír:

| kapu | cím |
|---|---|
| `version == 1` | `0x00834585 cmp eax,1` |
| téma == `picturepile` | `0x008345b3 repe cmpsb` (`0x00cbea2c`) |

A szorzás **helyben** történik (`0x0083468a lea` → `0x00834696 fstp`, 56
bájtos lépésköz), és a tényező a ciklus ELŐTT készül el EGYSZER:
`1024,0` (`0x0083466b`) × `0,33` (`0x00834671`) ×
`min(1/√(√k − 1), 1)`, ahol `k` a **csomópontok száma**
(`0x00834698 mov eax,[ebx+0x4c]`).

⚠️ Tehát **minden csomópont UGYANAZT a tényezőt kapja** — ez nem a
sorszám-alapú `pile_scale()`, ami az elrendezéskor ad képenként külön
méretet.

## Amit ez a lap mér

- a két kapu mindegyikét külön-külön (verzió ÉS téma);
- hogy a szorzás **egyszeri**: a migrált projekt `version`-je 2, tehát a
  visszaolvasás már nem szoroz újra. Ez a KONTROLL — enélkül a négyzetre
  emelés némán átcsúszna, és a #2593 mérése kimondja, hogy a ciklus
  „szoroz, nem értéket ad".
"""

from __future__ import annotations

import math

import pytest

from picasapy.collage.cxf import CXF_VERSION, dumps, loads
from picasapy.collage.themes import PICTUREPILE


def _cxf(version: int, theme: str, scales: list[float]) -> str:
    csomopontok = "\n".join(
        f'  <node src="k{i}.jpg" x="0.1" y="0.1" w="0.2" h="0.2"'
        f' theta="0.0" scale="{s}"></node>'
        for i, s in enumerate(scales)
    )
    return (
        '<?xml version="1.0" encoding="utf-8" ?>\n'
        f'<collage version="{version}" format="4:3" orientation="landscape"'
        f' theme="{theme}" shadows="0" captions="0">\n{csomopontok}\n</collage>\n'
    )


def _varhato_tenyezo(k: int) -> float:
    """`1024 × 0,33 × min(1/√(√k − 1), 1)` — a ciklus előtt EGYSZER."""
    belso = math.sqrt(k) - 1.0
    arany = 1.0 if belso <= 0.0 else min(1.0, 1.0 / math.sqrt(belso))
    return 1024.0 * 0.33 * arany


class TestAMigracioLefut:
    @pytest.mark.parametrize("k", [1, 2, 4, 9, 25])
    def test_minden_csomopont_UGYANAZT_a_tenyezot_kapja(self, k: int) -> None:
        eredeti = [0.1 * (i + 1) for i in range(k)]
        projekt = loads(_cxf(1, PICTUREPILE, eredeti))

        tenyezo = _varhato_tenyezo(k)
        kapott = [n.scale for n in projekt.nodes]
        assert kapott == pytest.approx([s * tenyezo for s in eredeti], rel=1e-6)

    def test_a_verzio_2_lesz(self) -> None:
        projekt = loads(_cxf(1, PICTUREPILE, [0.2, 0.3]))
        assert projekt.version == CXF_VERSION == 2


class TestAKetKapu:
    def test_mas_verzio_valtozatlan(self) -> None:
        eredeti = [0.2, 0.3]
        projekt = loads(_cxf(2, PICTUREPILE, eredeti))
        assert [n.scale for n in projekt.nodes] == pytest.approx(eredeti)

    def test_mas_tema_valtozatlan(self) -> None:
        """A téma-kapu ugyanoda ugrik, mint a verzió-kapu (`0x008346a3`)."""
        eredeti = [0.2, 0.3]
        projekt = loads(_cxf(1, "picturegrid", eredeti))
        assert [n.scale for n in projekt.nodes] == pytest.approx(eredeti)
        assert projekt.theme == "picturegrid"

    def test_a_masik_temanal_a_verzio_AKKOR_IS_2_lesz(self) -> None:
        """Az író beégetve `2`-t ír (`0x00834801 push 2`), a témától
        függetlenül — a migráció elmarad, de a fájl `version`-je akkor is
        frissül. ⚠️ Ez a mért viselkedés, nem elnézés: a `version` a FÁJL
        alakját jelöli, nem azt, hogy a `scale`-eken futott-e a szorzás."""
        projekt = loads(_cxf(1, "picturegrid", [0.2]))
        assert projekt.version == 2


class TestAzEgYSZERISEG:
    """⛳ A KONTROLL: kétszer lefuttatva a tényező négyzetre emelődne."""

    def test_a_korbejaras_stabil(self) -> None:
        eredeti = [0.2, 0.3, 0.4]
        elso = loads(_cxf(1, PICTUREPILE, eredeti))
        elso_scale = [n.scale for n in elso.nodes]

        #: mentés → visszaolvasás: a fájl már `version="2"`
        masodik = loads(dumps(elso))

        assert [n.scale for n in masodik.nodes] == pytest.approx(
            elso_scale, rel=1e-6
        ), "a második betöltés ÚJRA szorzott — a tényező négyzetre emelődött"

    def test_a_kontroll_maga_is_er_valamit(self) -> None:
        """Ha a tényező 1 volna, az előző próba vakon átmenne. Három
        csomópontra a tényező ~338, tehát a különbség mérhető."""
        assert _varhato_tenyezo(3) > 100
