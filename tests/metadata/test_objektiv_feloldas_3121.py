"""Az objektívnév feloldása a MÉRT táblákból (#3121).

## A mérés

`docs/specs/picasa-metaadat-tulajdonsagok.md` 9. szakasz: a Picasa két külön
táblát visel, és a beolvasója (`FUN_00a35a60` / `FUN_00a35d80`) két külön
kulccsal keres:

| gyártó | tábla | kulcs |
|---|---|---|
| Canon | `0x00c79c98`, 230 × 24 bájt | `LensType` + a gyújtó/rekesz négyes |
| Nikon | `0x00c7b230`, 416 × 12 bájt | a 8 bájtos `LensID` |

Két részlet, amit a mérés kimondott, és amit ez a próbasor betartat:

1. a Canon `LensType` **ISMÉTLŐDHET** (egy azonosító több objektívet takar) —
   ilyenkor a **gyújtótávolság/rekesz négyes** választ;
2. a float-egyezés **nem pontos, hanem 8 ULP tűréssel** megy: a Picasa a két
   `float` BITMINTÁJÁT vonja ki egészként, és az abszolút különbséget
   hasonlítja 8-hoz (9.8). Tehát `35.0` helyett `34.999996` is találat.

## Amit ez a próbasor NEM mér

Hogy a `LensType`/`LensID` a MakerNote MELYIK bájtjain áll — azt a gyártói
formátum adja. Ez a próbasor a FELOLDÁST méri: kulcs → név. A Canon
MakerNote-kiolvasás és a teljes Canon-ág őre:
`test_canon_objektiv_makernote_3121.py`.
"""

from __future__ import annotations

import json

import pytest

from picasapy.metadata.objektiv import (
    TABLA_UT,
    canon_objektiv,
    nikon_objektiv,
    objektiv_neve,
)


@pytest.fixture(scope="module")
def tabla() -> dict:
    return json.loads(TABLA_UT.read_text(encoding="utf-8"))


class TestATabla:
    def test_a_MERT_darabszamok(self, tabla) -> None:
        assert len(tabla["canon"]) == 230
        assert len(tabla["nikon"]) == 416

    def test_a_forras_meg_van_nevezve(self, tabla) -> None:
        """A kinyert adat provenienciája a fájlban áll, nem csak a commitban."""
        assert "Picasa3.exe" in tabla["_forras"]
        assert "#3121" in tabla["_forras"]

    def test_a_canon_tabla_lens_type_szerint_RENDEZETT(self, tabla) -> None:
        """A beolvasó ezt kihasználja (`ja` → kilépés), tehát mérce."""
        azonositok = [r["lens_type"] for r in tabla["canon"]]
        assert azonositok == sorted(azonositok)

    def test_a_nikon_kulcs_8_bajt(self, tabla) -> None:
        for rekord in tabla["nikon"]:
            assert len(rekord["lens_id"]) == 16, rekord


class TestCanonFeloldas:
    def test_egyertelmu_azonosito(self) -> None:
        assert canon_objektiv(1, 50.0, 0.0, 1.8, 0.0) == "Canon EF 50mm f/1.8"

    def test_ISMETLODO_azonositot_a_szamnegyes_dont_el(self) -> None:
        """A mért példa: a `4` két objektívet takar (9.7 táblája)."""
        egyik = canon_objektiv(4, 35.0, 105.0, 3.5, 4.5)
        masik = canon_objektiv(4, 35.0, 135.0, 4.0, 5.6)
        assert egyik == "Canon EF 35-105mm f/3.5-4.5 or Sigma Lens"
        assert masik == "Sigma UC Zoom 35-135mm f/4-5.6"
        assert egyik != masik

    def test_a_8_ULP_TURES(self) -> None:
        """A mért tűrés: a bitminták egész különbsége < 8."""
        import struct

        def ulp_el(ertek: float, lepes: int) -> float:
            (bit,) = struct.unpack("<I", struct.pack("<f", ertek))
            return struct.unpack("<f", struct.pack("<I", bit + lepes))[0]

        assert canon_objektiv(1, ulp_el(50.0, 7), 0.0, 1.8, 0.0) == \
            "Canon EF 50mm f/1.8"

    def test_a_TURESEN_TUL_nincs_talalat(self) -> None:
        """Ellenpróba: 9 ULP-vel már nem találat — a tűrés nem korlátlan."""
        import struct

        (bit,) = struct.unpack("<I", struct.pack("<f", 50.0))
        tul = struct.unpack("<f", struct.pack("<I", bit + 9))[0]
        assert canon_objektiv(1, tul, 0.0, 1.8, 0.0) is None

    def test_ismeretlen_azonosito_None(self) -> None:
        assert canon_objektiv(99999, 50.0, 0.0, 1.8, 0.0) is None


class TestNikonFeloldas:
    """⚠️ A kulcs a tábla BÁJTSORRENDJÉBEN áll (ahogy a fájlban van), nem
    DWORD-ökre bontva megfordítva — a kinyerő és a feloldó ugyanezt az
    alakot használja, tehát a kettő nem csúszhat el."""

    def test_a_MERT_kulcsok(self) -> None:
        assert nikon_objektiv(bytes.fromhex("00361C2D343C0006")).startswith(
            "TC-20E")
        assert nikon_objektiv(bytes.fromhex("003E80A0383F0002")) == \
            "Tokina AT-X 124 AF PRO DX (AF 12-24mm f/4)"

    def test_a_kulcs_hexben_is_mehet(self) -> None:
        assert nikon_objektiv("003e80a0383f0002") == nikon_objektiv(
            bytes.fromhex("003E80A0383F0002"))

    def test_ismeretlen_kulcs_None(self) -> None:
        assert nikon_objektiv(b"\x00" * 8) is None

    def test_rossz_hosszu_kulcs_HIBA(self) -> None:
        """A csendes None elrejtené a hívó hibáját."""
        with pytest.raises(ValueError):
            nikon_objektiv(b"\x01\x02")


class TestAGyartoValaszt:
    """A mért elosztó a **Make** mezőből dönt (9.9)."""

    def test_canon_make(self) -> None:
        assert objektiv_neve(
            "Canon", lens_type=1, gyujto_min=50.0, rekesz_min=1.8
        ) == "Canon EF 50mm f/1.8"

    def test_nikon_make(self) -> None:
        assert objektiv_neve(
            "NIKON CORPORATION", lens_id="003E80A0383F0002"
        ).startswith("Tokina AT-X 124")

    def test_ismeretlen_gyarto_None(self) -> None:
        assert objektiv_neve("Fujifilm", lens_type=1) is None

    def test_hianyzo_kulcs_None(self) -> None:
        assert objektiv_neve("Canon") is None
