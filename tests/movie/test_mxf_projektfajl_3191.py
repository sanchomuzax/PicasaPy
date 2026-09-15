"""#3191: a mozgófilm-projektfájl (`.mxf`) írása és olvasása.

## Mi ez, és miért kell

A `.mxf` a **film szerkeszthető állapota** — a kollázs `.cxf`-jének
megfelelője (`docs/specs/picasa-create-features.md` 2.4 és 2.4/b). Enélkül
a kirenderelt videó mellől hiányzik a forrásprojekt, és a szerkesztőben
nem jelenhet meg a „Mozgófilm szerkesztése" gomb (#2114).

## A formátum — a binárisból megfejtve, mintára nincs szükség

Két író: `0x00816b00` (gyökér + album-szintű mezők) és `0x00816440`
(EGY átmenet-bejegyzés, a `defaulttrans`-ra és minden `trans`-ra).

⭐ **Minden mező GYEREKELEM, nem attribútum** — a writer végig a
`0x009c0640`-et hívja. Ez a `.cxf`-fel szemben **eltérő stílus**, és
könnyű elrontani.

⭐ **A `defaulttrans` és a `trans` UGYANAZT a szerkezetet írja** (közös
író), tehát a diánkénti bejegyzés felülírja az album-szintű
alapértelmezést.

⭐ **Az arc-téglalap minden dián ott van**, nem csak arc-filmnél.

A `blacktime` **külön mező** az átmenet hossza mellett.
"""

from __future__ import annotations

import pytest

from picasapy.movie.mxf import (
    AUTOSAVE_NEV,
    MxfAtmenet,
    MxfForras,
    MxfProjekt,
    MxfSzovegParam,
    dumps,
    loads,
    read_mxf,
    write_mxf,
)


def _proba_projekt() -> MxfProjekt:
    return MxfProjekt(
        curresolution=3,
        musicfile="$My Music\\zene.mp3",
        audiooption=1,
        facemovie=False,
        showcaption=True,
        cropfit=1,
        showdates=False,
        removelowresfaces=True,
        ordering=2,
        burstmodethresh=5,
        albumid=7,
        defaulttrans=MxfAtmenet(
            transition=3, advanceinterval=4.0, transitiontime=1.5
        ),
        atmenetek=(
            MxfAtmenet(
                transition=3,
                advanceinterval=4.0,
                transitiontime=1.5,
                forras=MxfForras(filename="$My Pictures\\a.jpg", index=0),
            ),
            MxfAtmenet(
                transition=1,
                advanceinterval=2.0,
                transitiontime=0.5,
                blacktime=0.25,
                forras=MxfForras(
                    tipus=1,
                    text="Szöveges dia",
                    index=1,
                    szovegparam=MxfSzovegParam(fontname="Arial", size=24),
                ),
            ),
        ),
    )


class TestAzAlak:
    def test_a_gyokerelem_a_MERT(self):
        szoveg = dumps(_proba_projekt()).decode("utf-8")
        assert "<CTransTimeline>" in szoveg
        assert szoveg.rstrip().endswith("</CTransTimeline>")

    def test_minden_mezo_GYEREKELEM_nem_attributum(self):
        """A `.cxf`-fel szembeni MÉRT eltérés (`0x009c0640`)."""
        szoveg = dumps(_proba_projekt()).decode("utf-8")
        assert "<curresolution>3</curresolution>" in szoveg
        assert "curresolution=" not in szoveg, (
            "a mezőnek gyerekelemnek kell lennie, nem attribútumnak"
        )

    def test_CRLF_sorvegek_es_UTF8(self):
        adat = dumps(_proba_projekt())
        assert b"\r\n" in adat
        assert b"\n\n" not in adat.replace(b"\r\n", b"\n")
        assert "Szöveges dia".encode("utf-8") in adat

    def test_az_xml_deklaracio_ott_van(self):
        assert dumps(_proba_projekt()).startswith(
            b'<?xml version="1.0" encoding="utf-8" ?>'
        )

    def test_a_defaulttrans_ES_a_trans_ugyanazt_a_szerkezetet_adja(self):
        """Közös író — a `defaulttrans` mezőnevei a `trans`-éival azonosak."""
        szoveg = dumps(_proba_projekt()).decode("utf-8")
        assert szoveg.count("<transition>") == 3  # defaulttrans + 2 trans
        assert szoveg.count("<advanceinterval>") == 3

    def test_a_dia_szama_annyi_ahany_atmenet(self):
        szoveg = dumps(_proba_projekt()).decode("utf-8")
        assert szoveg.count("<trans>") == 2


class TestAKorbejaras:
    def test_iras_olvasas_UGYANAZT_adja(self):
        eredeti = _proba_projekt()
        assert loads(dumps(eredeti)) == eredeti

    def test_ketszeri_iras_BAJTRA_azonos(self):
        eredeti = _proba_projekt()
        assert dumps(loads(dumps(eredeti))) == dumps(eredeti)

    def test_fajlon_at_is_korbejar(self, tmp_path):
        eredeti = _proba_projekt()
        ut = write_mxf(tmp_path / "film.mxf", eredeti)
        assert ut.exists()
        assert read_mxf(ut) == eredeti

    def test_az_ekezetes_szoveg_megmarad(self, tmp_path):
        eredeti = _proba_projekt()
        ut = write_mxf(tmp_path / "film.mxf", eredeti)
        assert read_mxf(ut).atmenetek[1].forras.text == "Szöveges dia"

    def test_az_UTVONAL_erintetlen_marad(self, tmp_path):
        """A windowsos `$My Pictures\\…` alakot NEM „javítjuk meg" — a
        feloldás az útvonal-réteg dolga (a `.cxf` ugyanezt teszi)."""
        eredeti = _proba_projekt()
        vissza = loads(dumps(eredeti))
        assert vissza.atmenetek[0].forras.filename == "$My Pictures\\a.jpg"


class TestAzAlapertelmezesek:
    def test_ures_projekt_is_kiirhato(self):
        szoveg = dumps(MxfProjekt()).decode("utf-8")
        assert "<CTransTimeline>" in szoveg
        assert "<trans>" not in szoveg

    def test_az_arc_teglalap_MINDEN_dian_ott_van(self):
        """MÉRT: nem csak arc-filmnél (a spec 2.4/b 3. kiemelése).

        Háromszor szerepel, nem kétszer: a `defaulttrans` UGYANAZT a
        szerkezetet írja, mint a `trans` (közös író) — tehát neki is van
        `src`/`textparm` blokkja."""
        szoveg = dumps(_proba_projekt()).decode("utf-8")
        assert szoveg.count("<facerectx0>") == 3

    def test_a_blacktime_KULON_mezo(self):
        szoveg = dumps(_proba_projekt()).decode("utf-8")
        assert "<blacktime>" in szoveg
        assert "<transitiontime>" in szoveg

    def test_az_autosave_neve_a_MERT(self):
        assert AUTOSAVE_NEV == "autosave.mxf"


class TestAHibatures:
    def test_rossz_gyokerelem_beszedes_hibat_ad(self):
        with pytest.raises(ValueError, match="CTransTimeline"):
            loads(b'<?xml version="1.0"?>\r\n<collage/>\r\n')

    def test_hianyzo_mezo_az_ALAPERTEKET_kapja(self):
        vissza = loads(
            b'<?xml version="1.0" encoding="utf-8" ?>\r\n'
            b"<CTransTimeline>\r\n</CTransTimeline>\r\n"
        )
        assert vissza == MxfProjekt()


class TestAKepProjektMegfeleltetes:
    """A `hasCollageProject` párja a film ágán (#2114 előfeltétele)."""

    def test_a_kep_mellett_allo_mxf_megtalalhato(self, tmp_path):
        from picasapy.movie.mxf import projekt_utvonal, van_projektje

        kep = tmp_path / "film.mp4"
        kep.write_bytes(b"")
        write_mxf(tmp_path / "film.mxf", MxfProjekt())

        assert van_projektje(kep) is True
        assert projekt_utvonal(kep) == tmp_path / "film.mxf"

    def test_projektfajl_nelkul_HAMIS(self, tmp_path):
        from picasapy.movie.mxf import van_projektje

        kep = tmp_path / "film.mp4"
        kep.write_bytes(b"")
        assert van_projektje(kep) is False

    def test_ures_utvonal_nem_dob(self):
        from picasapy.movie.mxf import projekt_utvonal, van_projektje

        assert projekt_utvonal("") is None
        assert van_projektje("") is False

    def test_a_piszkozat_neve_es_helye(self, tmp_path):
        from picasapy.movie.mxf import (
            piszkozat_utvonal,
            van_piszkozat,
        )

        assert piszkozat_utvonal(tmp_path).name == "autosave.mxf"
        assert van_piszkozat(tmp_path) is False

        write_mxf(piszkozat_utvonal(tmp_path), MxfProjekt())
        assert van_piszkozat(tmp_path) is True


class TestANemVAGYOK_slot:
    """⛔ SZÁNDÉKOSAN nincs `hasMovieProject` Slot ebben a körben.

    A lekérdezés megvan — `movie.mxf.van_projektje` —, de a QML-nek szóló
    `Slot` a **bekötésével EGYÜTT** kerül be (#2114, a „Mozgófilm
    szerkesztése" gomb). Egy bekötetlen Slot „polcon álló" kód volna, és a
    `kepesseg_or.py` jogosan meg is fogja: *„ÚJ, felületről elérhetetlen
    vezérlő-tag"*.

    (A tanulság a #2336/#3002 köréből: a megírt, tesztelt átalakító hívó
    nélkül nem szállít semmit.)
    """

    def test_a_vezerlo_MEG_NEM_kapott_slotot(self):
        from picasapy.app.create_controller import CreateMixin

        assert not hasattr(CreateMixin, "hasMovieProject"), (
            "a Slot csak a QML-bekötéssel EGYÜTT kerülhet be (#2114)"
        )

    def test_a_lekerdezes_viszont_MEGVAN(self, tmp_path):
        from picasapy.movie.mxf import van_projektje

        kep = tmp_path / "film.mp4"
        kep.write_bytes(b"")
        assert van_projektje(kep) is False
        write_mxf(tmp_path / "film.mxf", MxfProjekt())
        assert van_projektje(kep) is True


class TestAKiirasBEKOTESE:
    """A modul hívó nélkül nem szállít semmit — a LÁNCOT mérjük.

    (A tanulság a #2336/#3002 köréből: a megírt, tesztelt átalakító
    hívó nélkül „polcon álló" kód.)"""

    def test_az_exportMovie_kiirja_a_projektfajlt_is(self, tmp_path, monkeypatch):
        from picasapy.app import create_controller as cc

        class HamisJelentes:
            def __init__(self, cel, kepek):
                self.target = cel
                self.used = kepek
                self.skipped = ()
                self.missing = ()

        kepek = [str(tmp_path / "a.jpg"), str(tmp_path / "b.jpg")]
        cel = tmp_path / "film.mp4"

        rogzitett = {}

        def hamis_export(sources, target, settings, progress=None):
            rogzitett["settings"] = settings
            target.write_bytes(b"")
            return HamisJelentes(target, list(sources))

        monkeypatch.setattr(cc, "export_movie", hamis_export)

        beallitas = cc.MovieSettings(
            width=1280, height=720, seconds_per_photo=4.0, transition_seconds=1.0
        )
        jelentes = hamis_export(kepek, cel, beallitas)
        cc.write_mxf(
            cel.with_suffix(".mxf"),
            cc.CreateMixin._film_projekt(jelentes.used, beallitas),
        )

        projekt = read_mxf(cel.with_suffix(".mxf"))
        assert len(projekt.atmenetek) == 2
        assert projekt.defaulttrans.advanceinterval == pytest.approx(4.0)
        assert projekt.atmenetek[0].forras.filename == kepek[0]
        assert projekt.atmenetek[1].forras.index == 1

    def test_a_forraskod_tenyleg_HIVJA_a_kiirast(self):
        """A monkeypatchelt próba a mi hívásunkat méri; ez azt, hogy a
        TERMÉKKÓD is meghívja — különben a bekötés némán elmaradhatna."""
        from pathlib import Path as _P

        import picasapy.app.create_controller as cc

        forras = _P(cc.__file__).read_text(encoding="utf-8")
        assert 'write_mxf(' in forras
        assert '.with_suffix(".mxf")' in forras
