"""#2054: a súgó tartalmának futásidejű elérése — net nélkül, telepítve is.

⚠️ **Miért a csomagfa alatt.** A telepíthető csomagba kizárólag a
`src/picasapy` fa alól kerül be bármi (`MANIFEST.in`: `graft
src/picasapy`; `pyproject.toml`: `packages.find where = ["src"]`). A
súgó korábban a `docs/help/` alatt volt, tehát git-másolatból működött
volna, telepített csomagból nem — és ez némán, csak a felhasználónál
derült volna ki. Ugyanaz az osztály, ami a #646-ban 40 fájlt vitt el.
"""

from __future__ import annotations


from picasapy.help_content import (
    FOOLDAL,
    fejezet_szovege,
    fejezetek,
    kereses,
    sugo_mappa,
)


class TestASugoMEGVAN:
    def test_a_mappa_a_CSOMAGFA_alatt_van(self):
        mappa = sugo_mappa()
        assert mappa.is_dir(), f"nincs súgó-mappa: {mappa}"
        # a `picasapy` csomagon BELÜL — enélkül a wheelbe sem kerülne be
        assert mappa.parent.name == "picasapy", (
            f"a súgó a csomagfán KÍVÜL van ({mappa}) — telepítve nem lenne meg"
        )

    def test_a_fooldal_letezik_es_nem_ures(self):
        szoveg = fejezet_szovege(FOOLDAL)
        assert szoveg and len(szoveg) > 200

    def test_minden_fejezet_olvashato(self):
        nevek = fejezetek()
        assert len(nevek) >= 20, f"csak {len(nevek)} fejezet — hiányzik a tartalom?"
        for nev in nevek:
            assert fejezet_szovege(nev), f"üres fejezet: {nev}"

    def test_a_fooldal_a_lista_ELEJEN_all(self):
        assert fejezetek()[0] == FOOLDAL

    def test_ismeretlen_fejezet_None(self):
        assert fejezet_szovege("nincs/ilyen.md") is None

    def test_a_konyvtaron_KIVULRE_nem_lehet_kilepni(self):
        """Útvonal-bejárás elleni védelem: a fejezetnév nem vihet ki a
        súgó mappájából."""
        assert fejezet_szovege("../../pyproject.toml") is None
        assert fejezet_szovege("/etc/passwd") is None


class TestAKereses:
    def test_megtalal_egy_letezo_szot(self):
        talalatok = kereses("kollázs")
        assert talalatok, "a „kollázs” szóra nincs találat"
        assert all("fejezet" in t and "reszlet" in t for t in talalatok)

    def test_a_talalat_a_FEJEZETRE_es_a_RESZLETRE_is_mutat(self):
        talalatok = kereses("kollázs")
        elso = talalatok[0]
        assert elso["fejezet"].endswith(".md")
        assert "kollázs" in elso["reszlet"].casefold()

    def test_kis_es_nagybetu_KOZOMBOS(self):
        assert kereses("KOLLÁZS") and kereses("kollázs")

    def test_ures_keresesre_nincs_talalat(self):
        assert kereses("") == []
        assert kereses("   ") == []

    def test_nem_letezo_szora_ures_lista(self):
        assert kereses("zzzznincsilyenszo") == []

    def test_a_talalatok_szama_KORLATOS(self):
        """Egy gyakori szó ne öntse el a listát."""
        assert len(kereses("a")) <= 200
