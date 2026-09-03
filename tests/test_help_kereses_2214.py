"""#2214 — a súgó keresője fejezetenként EGY sort adjon.

A felhasználó képernyőképe: az „effekt" keresésre a lista háromszor
„PicasaPy súgó", háromszor „Mi változott?", ötször „Csoportos szerkesztés
és az effektus-vágól…", négyszer „Effektek listája". A sorok
megkülönböztethetetlenek voltak, mert:

* a `kereses()` fejezetenként MINDEN előfordulásra külön találatot adott,
* de a `cim` mindegyiknél ugyanaz — a fejezet első `#` címsora,
* a `reszlet` pedig csak egérrámutatásra (tooltip) látszott.

Ráadásul a felső korlát az ELŐFORDULÁSOKAT számolta, így egyetlen
bőbeszédű fejezet kiszoríthatta a hátrébb lévőket.
"""

from __future__ import annotations

from picasapy.help_content import fejezetek, kereses


class TestEgyFejezetEgySor:
    def test_ugyanaz_a_fejezet_nem_szerepel_ketszer(self):
        """Olyan kifejezés, ami biztosan sokszor előfordul egy lapon."""
        talalatok = kereses("a")
        fejezetnevek = [t["fejezet"] for t in talalatok]
        assert len(fejezetnevek) == len(set(fejezetnevek)), (
            "ugyanaz a fejezet többször szerepel a találatok közt"
        )

    def test_a_cimek_sem_ismetlodnek(self):
        """A felhasználó a CÍMET látja — az sem lehet duplán."""
        talalatok = kereses("kép")
        cimek = [t["cim"] for t in talalatok]
        assert len(cimek) == len(set(cimek))

    def test_tobb_elofordulasnal_is_egy_sor_jon(self):
        talalatok = kereses("Picasa")
        assert talalatok
        assert len({t["fejezet"] for t in talalatok}) == len(talalatok)


class TestADarabszamLatszik:
    """Ha egy fejezetben több előfordulás van, azt meg kell mondani."""

    def test_minden_talalatnak_van_darabszama(self):
        for t in kereses("a"):
            assert "db" in t, "a találatból hiányzik az előfordulás-szám"
            assert isinstance(t["db"], int) and t["db"] >= 1

    def test_a_darabszam_a_VALODI_elofordulasok_szama(self):
        """Nem 1-re rögzített helykitöltő."""
        talalatok = kereses("a")
        assert any(t["db"] > 1 for t in talalatok), (
            "egyetlen fejezetben sincs több előfordulás — gyanús"
        )


class TestARekeszLatszik:
    def test_minden_talalatnak_van_reszlete(self):
        for t in kereses("Picasa"):
            assert t["reszlet"].strip(), "üres részlet"

    def test_a_reszlet_TARTALMAZZA_a_keresett_szot(self):
        for t in kereses("effekt"):
            assert "effekt" in t["reszlet"].casefold()


class TestAKorlatAFejezeteketSzamolja:
    """Egyetlen bőbeszédű fejezet nem szoríthat ki másikat."""

    def test_a_talalatok_szama_nem_lehet_tobb_a_fejezetekenel(self):
        assert len(kereses("a")) <= len(fejezetek())

    def test_a_gyakori_szo_MINDEN_erintett_fejezetet_meghoz(self):
        """A régi korlát (200 előfordulás) a lista elején elfogyott."""
        minta = "a"
        vart = {
            nev
            for nev in fejezetek()
            if minta in (__import__("picasapy.help_content", fromlist=["x"])
                         .fejezet_szovege(nev) or "").casefold()
        }
        kapott = {t["fejezet"] for t in kereses(minta)}
        assert kapott == vart, (
            f"kimaradt fejezetek: {sorted(vart - kapott)[:5]}"
        )


class TestAzUresKeresesValtozatlan:
    def test_ures_kifejezesre_nincs_talalat(self):
        assert kereses("") == []
        assert kereses("   ") == []

    def test_nem_letezo_kifejezesre_nincs_talalat(self):
        assert kereses("zzzqqqxxx-nincs-ilyen") == []
