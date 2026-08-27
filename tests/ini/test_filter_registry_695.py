"""#695 — az ÍRÓ oldal kanonikus szűrőneve és paraméterszám-korlátja.

Mérési háttér: `docs/specs/picasa-ini-format.md`, „A `filters=` lánc
beolvasása SZIGORÚ — mérve (2026-08-15, #685)" szakasz. Az eredeti Picasa a
szűrőnevet BÁJTRA illeszti (`Tint=`/`vignette=` → néma elejtés), és a
FÖLÖSLEGES paramétert is néma elejtéssel bünteti (`grain2=1,0.5;`).

A kanonikus alakok forrása a `docs/specs/filterdesc-registry.md` 2. szakasza
(84 szűrő), a paraméterszámoké ugyanennek a 3. és 4.1–4.2 szakasza.

Elvi korlát: az OLVASÁS marad megengedő (`FilterOp.matches` casefold) — a
szigorítás kizárólag az író oldalra vonatkozik.
"""

import pytest

from picasapy.edit.session import EditSession
from picasapy.ini.filter_registry import (
    CANONICAL_FILTER_NAMES,
    MAX_PARAM_COUNTS,
    UNKNOWN_PARAM_COUNT_FILTERS,
    FilterWriteError,
    canonical_filter_name,
)
from picasapy.ini.filters import (
    FilterOp,
    parse_filters,
    serialize_filters,
    serialize_filters_for_write,
)


class TestKanonikusNevIraskor:
    """1. kész-feltétel: MINDEN regiszterbeli szűrőre a kiírt név a
    kanonikus alak — akkor is, ha a láncban rossz írásmóddal szerepelt."""

    @pytest.mark.parametrize("canonical", CANONICAL_FILTER_NAMES)
    def test_rossz_irasmod_kanonikusra_javul(self, canonical):
        rossz = canonical.swapcase()
        assert rossz != canonical, "a próba-írásmódnak el kell térnie"
        kiirt = serialize_filters_for_write((FilterOp(rossz, ("1",)),))
        assert kiirt == f"{canonical}=1;"

    @pytest.mark.parametrize("canonical", CANONICAL_FILTER_NAMES)
    def test_a_kanonikus_alak_valtozatlan(self, canonical):
        kiirt = serialize_filters_for_write((FilterOp(canonical, ("1",)),))
        assert kiirt == f"{canonical}=1;"

    def test_a_mert_harom_esete_695(self):
        # A #685 mérés három néma elejtése: Tint / vignette / Sepia.
        ops = (
            FilterOp("Tint", ("1", "79.842102", "ffff")),
            FilterOp("VIGNETTE", ("1", "35", "1.4", "0", "00000000")),
            FilterOp("Sepia", ("1",)),
        )
        assert serialize_filters_for_write(ops) == (
            "tint=1,79.842102,ffff;"
            "Vignette=1,35,1.4,0,00000000;"
            "sepia=1;"
        )

    def test_ismeretlen_nev_valtozatlanul_megy_ki(self):
        # Round-trip elv: amit nem ismerünk, ahhoz nem nyúlunk.
        ops = (FilterOp("FutureFilter", ("1", "2")),)
        assert serialize_filters_for_write(ops) == "FutureFilter=1,2;"


class TestModositottLancRoundTrip:
    """2. kész-feltétel: a MÓDOSÍTOTT lánc is helyes írásmóddal megy vissza,
    az ismeretlen bejegyzések pedig bájtra megőrződnek."""

    def test_effekt_hozzafuzese_utan_kanonikus_a_teljes_lanc(self):
        eredeti = "Tint=1,79.842102,ffff;futurefilter=1,2;"
        session = EditSession.from_value(eredeti).append_effect("SEPIA")
        assert session.to_value() == (
            "tint=1,79.842102,ffff;futurefilter=1,2;sepia=1;"
        )

    def test_valos_picasa_lanc_modositatlan_tagjai_bajtra_megmaradnak(self):
        eredeti = (
            "enhance=1;crop64=1,45930000ba03defe;"
            "finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;"
        )
        session = EditSession.from_value(eredeti)
        # Kanonikus alakban érkezett → a kiírás bájtra azonos.
        assert session.to_value() == eredeti

    def test_a_lanc_sorrendje_nem_valtozik(self):
        session = EditSession.from_value("BW=1;SAT=1,0.500000;")
        assert session.to_value() == "bw=1;sat=1,0.500000;"

    def test_crop_beallitas_utan_is_kanonikus(self):
        from picasapy.ini.rect64 import decode_rect64

        session = EditSession.from_value("VIGNETTE=1;").append_crop(
            decode_rect64("45930000ba03defe")
        )
        assert session.to_value().startswith("Vignette=1;crop64=1,")


class TestParameterszamValidacio:
    """3. kész-feltétel: a FÖLÖSLEGES paraméter íráskor HIBA, nem néma
    kimenet. Mérve (#685): `grain2=1;` lefut, `grain2=1,0.500000;` néma
    elejtés."""

    def test_folosleges_parameter_hibat_ad(self):
        with pytest.raises(FilterWriteError):
            serialize_filters_for_write((FilterOp("grain2", ("1", "0.500000")),))

    def test_a_helyes_alak_atmegy(self):
        assert serialize_filters_for_write((FilterOp("grain2", ("1",)),)) == "grain2=1;"

    def test_a_hiba_uzenete_megnevezi_a_szurot_es_a_szamokat(self):
        with pytest.raises(FilterWriteError) as hiba:
            serialize_filters_for_write((FilterOp("sepia", ("1", "0.5")),))
        szoveg = str(hiba.value)
        assert "sepia" in szoveg

    def test_rossz_irasmodu_nev_alatt_is_a_kanonikus_korlat_szamit(self):
        with pytest.raises(FilterWriteError):
            serialize_filters_for_write((FilterOp("GRAIN2", ("1", "0.5")),))

    def test_zaro_ures_mezo_tolerált(self):
        # Mérve: `grain=1,;` LEFUT — a záró üres mező nem paraméter.
        assert serialize_filters_for_write((FilterOp("grain", ("1", "")),)) == "grain=1,;"

    def test_kevesebb_parameter_nem_hiba(self):
        # Mérve (edit_controller megjegyzése): `unsharp=1` azonos az
        # `unsharp2=1,0.600000`-val — a hiányzó paraméter az alapértékre
        # esik vissza, tehát NEM néma elejtés.
        assert serialize_filters_for_write((FilterOp("unsharp", ("1",)),)) == "unsharp=1;"

    def test_ismeretlen_szuronel_nincs_validacio(self):
        ops = (FilterOp("futurefilter", ("1", "1", "2", "3", "4", "5")),)
        assert serialize_filters_for_write(ops) == "futurefilter=1,1,2,3,4,5;"

    def test_nem_levezetheto_parameterszamu_szuro_atmegy(self):
        # A `retouch`/`redeye` PicasaPy-saját, változó hosszú kiterjesztés,
        # a `crop64` pedig nem csúszkás — ezekre nincs regiszterbeli szám.
        ops = (FilterOp("crop64", ("1", "45930000ba03defe")),)
        assert serialize_filters_for_write(ops) == "crop64=1,45930000ba03defe;"

    def test_append_effect_azonnal_hibat_ad(self):
        # Az író-oldali kapu ott is zár, ahol a lánc-elem KELETKEZIK.
        with pytest.raises(FilterWriteError):
            EditSession().append_effect("grain2", ("1", "0.5"))


class TestOlvasasMaradMegengedo:
    """A beolvasás nem dob és nem kanonizál — de a FUTTATÁS pontos.

    ⚠️ #1141 (2026-08-22) HELYESBÍTETTE ezt az osztályt. A #695-ös elvi
    korlát („a beolvasás kis-nagybetű-tűrő") a nyers ÉRTELMEZÉSRE
    továbbra is igaz — a régi fájl nem válik olvashatatlanná, a lánc
    bájtra megőrződik. A NÉV-ILLESZTÉS viszont az eredetiben
    kis-nagybetű-ÉRZÉKENY: hat mért képen (`merokit-2` export) a `Tint` /
    `TINT` / `tInT` alak NEM futott le, csak a kanonikus `tint`.
    """

    @pytest.mark.parametrize("irasmod", ["Tint", "TINT", "tInT"])
    def test_a_nem_kanonikus_irasmod_NEM_illeszkedik(self, irasmod):
        """#1141: mérve — az eredeti ezeket nem futtatja le."""
        ops = parse_filters(f"{irasmod}=1,5;")
        assert not ops[0].matches("tint")
        assert ops[0].name == irasmod, "a parse NEM kanonizál"

    def test_a_kanonikus_irasmod_illeszkedik(self):
        ops = parse_filters("tint=1,5;")
        assert ops[0].matches("tint")

    def test_serialize_filters_bajtra_pontos_marad(self):
        # A nyers `serialize_filters` a bélyegkép-kulcshoz kell: nem
        # kanonizál és nem dob — idegen lánc se szökjön ki kivétellel (#301).
        ertek = "Tint=1,5;grain2=1,0.5;"
        assert serialize_filters(parse_filters(ertek)) == ertek

    def test_session_has_PONTOS(self):
        """#1141: a `has()` is pontos — a `VIGNETTE` nem a `Vignette`."""
        assert not EditSession.from_value("VIGNETTE=1;").has("Vignette")
        assert EditSession.from_value("Vignette=1;").has("Vignette")


class TestRegiszterTeljesseg:
    """A regiszter maga: a `filterdesc-registry.md` 2. szakaszának 84
    szűrője, ütközés nélkül."""

    def test_nyolcvannegy_szuro(self):
        assert len(CANONICAL_FILTER_NAMES) == 84

    def test_nincs_irasmod_utkozes(self):
        kicsik = [name.casefold() for name in CANONICAL_FILTER_NAMES]
        assert len(set(kicsik)) == len(kicsik)

    def test_a_parameterszam_kulcsai_kanonikusak(self):
        assert set(MAX_PARAM_COUNTS) <= set(CANONICAL_FILTER_NAMES)

    def test_a_korlat_nelkuli_szurok_listaja_pontosan_a_maradek(self):
        # A „miért nincs korlát" indoklás (modul-docsztring) nem csúszhat el
        # a tényleges lefedettségtől.
        assert (
            set(CANONICAL_FILTER_NAMES) - set(MAX_PARAM_COUNTS)
            == UNKNOWN_PARAM_COUNT_FILTERS
        )

    def test_a_belso_szuronev_konstansok_kanonikusak(self):
        # Amit a saját rétegeink konstansként írnak a láncba, annak eleve a
        # Picasa által várt alakban kell lennie.
        from picasapy.ini.redeye import REDEYE_FILTER_NAME
        from picasapy.ini.retouch import RETOUCH_FILTER_NAME

        for name in (
            REDEYE_FILTER_NAME,
            RETOUCH_FILTER_NAME,
            "crop64",
            "tilt",
            "finetune2",
        ):
            assert canonical_filter_name(name) == name

    def test_canonical_filter_name_ismeretlenre_none(self):
        assert canonical_filter_name("futurefilter") is None
        assert canonical_filter_name("VIGNETTE") == "Vignette"

    #: Valódi Picasa-exportokból származó láncok (a `test_filters.py`
    #: #190/#347 mintái és a `filterdesc-registry.md` 3–4.1 táblái). Egyik
    #: sem sértheti a regiszter felső korlátját — ez az a fék, ami
    #: megakadályozza, hogy a korlátot a mért valóság ALÁ húzzuk.
    VALODI_MINTAK = (
        "IR=1,0.000000;",
        "Lomo=1,50.000000,0.000000;",
        "Holga=1,70.000000,30.000000,0.000000;",
        "HDR=1,20.000000,3.000000,0.000000;",
        "Cinemascope=1,0;",
        "Orton=1,25.000000,50.000000,0.000000;",
        "Sixties=1,20.000000,00ffffff,0;",
        "Invert=1;",
        "HeatMap=1,0.000000,0.000000;",
        "CrossProcess=1,0.000000;",
        "QuantizePalette=1,8.000000,80.000000,0.000000;",
        "TwoTone=1,0.000000,20.000000,0.000000,00004488,00ffff00;",
        "Boost=1,50.000000;",
        "Soften=1,50.000000,50.000000;",
        "Pixelate=1,20.000000,9.000000,0.000000;",
        "FocalZoom=1,0.500000,0.500000,50.000000,50.000000,50.000000,0.000000;",
        "PencilSketch=1,2.000000,100.000000,0.000000;",
        "Neon=1,0.000000,00ff0000;",
        "Comicize=1,20.000000,50.000000,50.000000;",
        "Border=1,20.000000,5.000000,0.000000,00000000,00ffffff,0.000000;",
        "DropShadow=1,4.000000,90.000000,10.000000,00000000,00ffffff,30.000000;",
        "MuseumMatte=1,25.000000,40.000000,001a0e03,00f0eae4;",
        "Polaroid=1,5.000000,00e2e2e2;",
        "grain=1;",
        "radtint=1,0.500000,0.500000,0.500000,00ff0000;",
        "RoundedEdges=1,20.000000;",
        "Matte=1,00ffffff;",
        "NightVision=1;",
        "picnik=1;",
        "radblur=1,0.500000,0.500000,0.300000,0.500000;",
        "dir_tint=1,0.432422,0.554167,0.250000,0.250000,ffffffff;",
        "glow2=1,0.650000,3.000000;",
        "tint=1,79.842102,ffff;",
        "ansel=1,ffffffff;",
        "Vignette=1,35.000000,1.400000,0.000000,00000000;",
        "enhance=1;",
        "finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;",
    )

    @pytest.mark.parametrize("minta", VALODI_MINTAK)
    def test_valodi_picasa_minta_atmegy_az_iro_kapun(self, minta):
        assert serialize_filters_for_write(parse_filters(minta)) == minta
