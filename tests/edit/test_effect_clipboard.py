"""`effect_clipboard` — „Az összes effektus másolása/beillesztése" tiszta
logikája (#426, javítva a #1544-ben).

## Miért íródott át ez a fájl (#1544)

A korábbi tesztkészlet a lánc **szűrését** rögzítette: azt állította, hogy a
`crop64`/`crop`/`redeye`/`retouch`/`save`/`rot`/`picnik`/`moviestart`/
`movieend` bejegyzések nem mennek át. Ez az állítás **téves volt**. A #426
a `filterdesc.xml` `mode="history"`/`persist` oszlopából KÖVETKEZTETTE a
kizárást, holott az eredeti Picasa másolás-kezelője ezt az attribútumot
soha nem olvassa:

* a `Picasa3.exe` másolójának (`0x005fecd0`) és beillesztőjének
  (`0x005fefc0`) teljes hívási útján **nincs szűrő-névre vonatkozó
  összehasonlítás** — sem fehér-, sem feketelista;
* függetlenül a bináris-indexből: a `"filters"` sztringnek **33**
  kódhivatkozása van (köztük a `0x006af3e0`/`0x006af650` getter/setter),
  a `crop64` sztringnek **nulla** ⇒ a program sehol nem hasonlít össze
  semmit ezzel a névvel.

Bizonyíték és döntés: `docs/decisions/effektus-vagolap-ket-reteg.md` (#1534).
"""

from picasapy.edit.effect_clipboard import (
    copy_all_effects,
    crop_mirror_value,
    paste_all_effects,
)


class TestCopyAllEffects:
    """A másolás NEM szűr — a lánc egészében kerül a vágólapra."""

    def test_a_teljes_lancot_atveszi(self):
        """A jegy (#1544) mért lánca: a `crop64` és a `redeye` is átmegy.

        A régi teszt (`test_strips_excluded_entries`) ennek az ELLENKEZŐJÉT
        állította — a bináris-bizonyíték szerint tévesen."""
        lanc = (
            "crop64=1,45930000ba03defe;bw=1;sepia=1;redeye=1,abc;"
            "tilt=1,0.500000,0.200000;"
        )
        assert copy_all_effects(lanc) == lanc

    def test_a_regi_kizart_nevek_mind_atmennek(self):
        """A #426 kizárási listájának MINDEN tagja átvihető.

        A régi `test_issue_named_entries_all_excluded` ugyanezt a hat nevet
        sorolta fel — azzal az állítással, hogy egyik sem megy át."""
        lanc = (
            "save=1;crop64=1,45930000ba03defe;crop=1;redeye=1;"
            "retouch=1,10000000f1ddff49;picnik=1;rot=1;"
            "moviestart=1,0.1;movieend=1,0.9;"
        )
        assert copy_all_effects(lanc) == lanc

    def test_megorzi_a_sorrendet(self):
        lanc = "sat=1,0.2;contrast=1,0.1;Vignette=1,35.0,1.4,0.0,00000000;"
        assert copy_all_effects(lanc) == lanc

    def test_none_bemenet_ures_lancot_ad(self):
        assert copy_all_effects(None) == ""

    def test_ures_bemenet_ures_lancot_ad(self):
        assert copy_all_effects("") == ""

    def test_ismeretlen_szuronev_is_atmegy(self):
        # ismeretlen (jövőbeli) szűrőnév a round-trip elv szerint átmegy
        lanc = "brandNewFilter=1,1.0;"
        assert copy_all_effects(lanc) == lanc

    def test_a_hianyzo_zaro_pontosvesszot_potolja(self):
        """Az egyetlen megengedett normalizálás: a Picasa maga is mindig
        lezárja a láncot pontosvesszővel."""
        assert copy_all_effects("bw=1") == "bw=1;"


class TestPasteAllEffects:
    def test_a_vagolap_erteket_valtozatlanul_adja(self):
        vagolap = "sat=1,0.2;contrast=1,0.1;"
        assert paste_all_effects(vagolap) == vagolap

    def test_ures_vagolap_torli_a_cel_lancat(self):
        assert paste_all_effects("") == ""

    def test_masolas_majd_beillesztes_a_GEOMETRIAT_is_atviszi(self):
        """A körút vége: a célkép ugyanazt a láncot kapja, a vágással és a
        régió-adatokkal együtt.

        A régi `test_roundtrip_copy_then_paste_excludes_geometry` azt
        állította, hogy a `crop64` és a `retouch` elveszik — az eredeti
        Picasa viszont a `filters` sztringet EGÉSZBEN írja vissza."""
        forras = "crop64=1,45930000ba03defe;sat=1,0.2;retouch=1,10000000f1ddff49;"
        assert paste_all_effects(copy_all_effects(forras)) == forras


class TestCropMirrorValue:
    """A `crop=` tükör-kulcs értéke a láncból (#1544).

    A rendereléshez az eredeti Picasa a külön `crop=rect64(...)` kulcsot
    olvassa (`docs/specs/filters-decoded.md`), és az ÉLES korpuszban
    (18 801 szekció, 5658 lánc) **761/761** esetben a `crop=` értéke pontosan
    a lánc UTOLSÓ `crop64`-jének hexe — nulla kivétellel. A beillesztésnek
    ezért a tükör-kulcsot is követnie kell."""

    def test_a_lanc_crop64_ebol_szarmazik(self):
        assert (
            crop_mirror_value("crop64=1,45930000ba03defe;bw=1;")
            == "rect64(45930000ba03defe)"
        )

    def test_az_UTOLSO_crop64_szamit(self):
        """Több crop64-es (valódi Picasa-)láncnál az effektív az utolsó —
        ugyanaz a szabály, mint a renderelésben (#130)."""
        lanc = "crop64=1,45930000ba03defe;bw=1;crop64=1,1b7c0000dbbdffff;"
        assert crop_mirror_value(lanc) == "rect64(1b7c0000dbbdffff)"

    def test_crop64_nelkuli_lanc_eseten_nincs_tukorkulcs(self):
        assert crop_mirror_value("bw=1;sepia=1;") is None

    def test_ures_lanc_eseten_nincs_tukorkulcs(self):
        assert crop_mirror_value("") is None

    def test_hibas_hex_eseten_nincs_tukorkulcs(self):
        """#301: sérült/idegen lánc olvasása nem szökhet ki kivétellel."""
        assert crop_mirror_value("crop64=1,zzz;") is None
