"""`picasapy.ini.text_overlay` — a `text=`/`textactive=` kulcsok típusos
parse/serialize tesztjei (#148, #371).

A formátum **hossz-előtagos és többblokkos** (#371, megfejtve a 859 fájlos
`.picasa.ini`-korpusz két valódi `text=` sorából). A legerősebb állítás itt a
**GOLDEN round-trip**: a két valódi, Picasa által írt sort beolvassuk és
visszaírjuk, és az eredménynek **bájtra azonosnak** kell lennie.
"""

from __future__ import annotations

import math

import pytest

from picasapy.ini.text_overlay import (
    TextBlock,
    TextGeometry,
    TextOverlay,
    TextStyle,
    parse_text,
    parse_text_active,
    serialize_text,
    serialize_text_active,
)

#: A korpusz EGYBLOKKOS valódi mintája (a `text=` kulcs értéke).
GOLDEN_EGYBLOKKOS = (
    "1;161;19;Boldog Karácsonyt!;Bickham Script Pro Regular;"
    "0.023961,0.841368,0.100000,0.000000;"
    "v1,4294899423,4278190080,128.000000,1.000000,0.000000,1.000000,700,0,49152;;"
)

#: A korpusz KÉTBLOKKOS valódi mintája — a felirat `&#010;` sortörést
#: tartalmaz, ami maga is pontosvesszőre végződik: a naiv `;`-szerinti
#: szétvágás elrontja. Ez a minta a hossz-előtag létjogosultsága.
GOLDEN_KETBLOKKOS = (
    "2;187;63;Kellemes karácsonyi ünnepeket és&#010;boldog újévet kívánunk!;Arial;"
    "0.105605,0.008726,0.059259,-4.712389;"
    "v1,4292215592,4293454056,128.000000,1.000000,0.500000,1.000000,700,258,49152;;"
    "126;4;2010;Arial;"
    "0.943794,0.039316,0.112127,1.308997;"
    "v1,4292215592,4293454056,128.000000,1.000000,0.500000,1.000000,700,258,49152;;"
)


class TestGoldenRoundTrip:
    """A legerősebb állítás: valódi Picasa-sor → beolvasás → kiírás →
    BÁJTAZONOS. Ha ez zöld, a formátum-modellünk hiánytalan."""

    @pytest.mark.parametrize(
        "golden", [GOLDEN_EGYBLOKKOS, GOLDEN_KETBLOKKOS], ids=["egyblokkos", "ketblokkos"]
    )
    def test_valodi_sor_bajtazonosan_ir_vissza(self, golden: str) -> None:
        assert serialize_text(parse_text(golden)) == golden


class TestParseGoldenEgyblokkos:
    def test_egyetlen_blokk(self) -> None:
        assert len(parse_text(GOLDEN_EGYBLOKKOS).blocks) == 1

    def test_szoveg_es_betutipus(self) -> None:
        block = parse_text(GOLDEN_EGYBLOKKOS).blocks[0]
        assert block.content == "Boldog Karácsonyt!"
        assert block.font == "Bickham Script Pro Regular"

    def test_geometria_normalizalt(self) -> None:
        geom = parse_text(GOLDEN_EGYBLOKKOS).blocks[0].geometry
        assert geom.x == pytest.approx(0.023961)
        assert geom.y == pytest.approx(0.841368)
        assert geom.size == pytest.approx(0.100000)
        assert geom.rotation == pytest.approx(0.0)

    def test_stilus_szinei(self) -> None:
        style = parse_text(GOLDEN_EGYBLOKKOS).blocks[0].style
        assert style.fill_argb == 0xFFFEF6DF
        assert style.outline_argb == 0xFF000000
        assert style.weight == 700


class TestParseGoldenKetblokkos:
    def test_ket_blokk(self) -> None:
        assert len(parse_text(GOLDEN_KETBLOKKOS).blocks) == 2

    def test_sortores_valodi_ujsorra_dekodolva(self) -> None:
        """⚠️ A `&#010;` entitás valódi újsorra dekódolódik — a naiv `;`-
        szétvágás itt vágná el a feliratot a `&#010` után."""
        block = parse_text(GOLDEN_KETBLOKKOS).blocks[0]
        assert block.content == "Kellemes karácsonyi ünnepeket és\nboldog újévet kívánunk!"
        assert len(block.content.encode("utf-8")) == 63

    def test_masodik_blokk_onallo(self) -> None:
        block = parse_text(GOLDEN_KETBLOKKOS).blocks[1]
        assert block.content == "2010"
        assert block.font == "Arial"
        assert block.geometry.x == pytest.approx(0.943794)

    def test_forgatas_radianban(self) -> None:
        """A korpusz értékei kerek FOKOKAT adnak radiánban: −4.712389 =
        −270°, 1.308997 = +75°. Ez bizonyítja a radián-egységet."""
        blocks = parse_text(GOLDEN_KETBLOKKOS).blocks
        assert math.degrees(blocks[0].geometry.rotation) == pytest.approx(-270.0, abs=1e-3)
        assert math.degrees(blocks[1].geometry.rotation) == pytest.approx(75.0, abs=1e-3)


class TestBlokkhossz:
    """A `blokkhossz` mező LEVEZETHETŐ, ezért a serialize újraszámolja —
    a parszernek nincs rá szüksége (a `szöveghossz` elég)."""

    def test_ujraszamolt_hossz_egyezik_a_valodival(self) -> None:
        """Ha a képlet hibás lenne, a golden round-trip elbukna; ez a teszt
        a KONKRÉT számot is kimondja, hogy a hiba olvasható legyen."""
        assert serialize_text(parse_text(GOLDEN_EGYBLOKKOS)).split(";")[1] == "161"

    def test_a_dekodolt_hosszon_alapul_nem_a_taroltan(self) -> None:
        """A kétblokkos minta első blokkja `&#010;`-t tárol (6 bájt), de a
        `blokkhossz` a dekódolt (1 bájtos újsoros) alakot számolja: a tárolt
        alapú számítás 5-tel többet adna."""
        assert serialize_text(parse_text(GOLDEN_KETBLOKKOS)).split(";")[1] == "187"


class TestSerializeSajat:
    def test_picasapy_eredetu_round_trip(self) -> None:
        overlay = TextOverlay(
            blocks=(
                TextBlock(
                    content="Nyár 2026",
                    font="Arial",
                    geometry=TextGeometry(x=0.25, y=0.5, size=0.1, rotation=0.0),
                    style=TextStyle(fill_argb=0xFFFFFFFF, outline_argb=0xFF000000),
                ),
            )
        )
        assert parse_text(serialize_text(overlay)) == overlay

    def test_sortores_entitaskent_irodik_ki(self) -> None:
        overlay = TextOverlay(
            blocks=(
                TextBlock(
                    content="első\nmásodik",
                    font="Arial",
                    geometry=TextGeometry(x=0.1, y=0.1, size=0.1, rotation=0.0),
                    style=TextStyle(fill_argb=0xFFFFFFFF, outline_argb=0xFF000000),
                ),
            )
        )
        value = serialize_text(overlay)
        assert "&#010;" in value
        assert "\n" not in value
        assert parse_text(value) == overlay

    def test_pontosvesszos_szoveg_is_round_trippel(self) -> None:
        """A hossz-előtag miatt a feliratban álló nyers `;` sem baj."""
        overlay = TextOverlay(
            blocks=(
                TextBlock(
                    content="a;b;c",
                    font="Arial",
                    geometry=TextGeometry(x=0.1, y=0.1, size=0.1, rotation=0.0),
                    style=TextStyle(fill_argb=0xFFFFFFFF, outline_argb=0xFF000000),
                ),
            )
        )
        assert parse_text(serialize_text(overlay)) == overlay

    def test_ures_blokklista_ures_erteket_ad(self) -> None:
        assert serialize_text(TextOverlay(blocks=())) == "0;"


class TestHibasBemenet:
    """Értelmezhetetlen bemenetnél `ValueError` — a hívó ilyenkor
    ÉRINTETLENÜL hagyja a sort (a generikus round-trip réteg megőrzi)."""

    def test_hianyzo_mezok(self) -> None:
        with pytest.raises(ValueError):
            parse_text("1;161;19")

    def test_nem_szam_blokkszam(self) -> None:
        with pytest.raises(ValueError):
            parse_text("abc;161;19;x;Arial;0,0,0,0;v1,0,0,0,0,0,0,0,0,0;;")

    def test_szoveghossz_nem_illeszkedik(self) -> None:
        """Ha a hossz-előtag nem esik mező-határra, a sor sérült — nem
        találgatunk, hanem elutasítjuk."""
        with pytest.raises(ValueError):
            parse_text(
                "1;161;99;Boldog Karácsonyt!;Arial;0,0,0,0;v1,0,0,0,0,0,0,0,0,0;;"
            )

    def test_a_regi_rovidites_nem_ertelmezheto(self) -> None:
        """A spec RÖVIDÍTETT példája (`1; 136;11;sample text;Aharoni;...`)
        nem teljes sor: geometria/stílus híján elutasítjuk."""
        with pytest.raises(ValueError):
            parse_text("1; 136;11;sample text;Aharoni;...")


class TestOrokoltPicasaPyAlak:
    """A 0.8.88-ig írt, PicasaPy-saját `<1>;<x*10000>;<y*10000>;<szöveg>;
    <font>` alak — a felhasználó feliratai ne vesszenek el."""

    def test_beolvasható_es_a_pozicio_atszamolodik(self) -> None:
        overlay = parse_text("1;2500;8000;Nyár 2026;Arial")
        assert len(overlay.blocks) == 1
        block = overlay.blocks[0]
        assert block.content == "Nyár 2026"
        assert block.geometry.x == pytest.approx(0.25)
        assert block.geometry.y == pytest.approx(0.80)

    def test_visszairaskor_mar_a_picasa_alakot_kapja(self) -> None:
        value = serialize_text(parse_text("1;2500;8000;Nyár 2026;Arial"))
        assert value.endswith(";;")
        assert parse_text(value).blocks[0].content == "Nyár 2026"


class TestTextActive:
    def test_parse_1_aktiv(self) -> None:
        assert parse_text_active("1") is True

    def test_parse_0_inaktiv(self) -> None:
        assert parse_text_active("0") is False

    def test_parse_ures_inaktiv(self) -> None:
        assert parse_text_active("") is False

    def test_serialize_round_trip(self) -> None:
        assert parse_text_active(serialize_text_active(True)) is True
        assert parse_text_active(serialize_text_active(False)) is False
