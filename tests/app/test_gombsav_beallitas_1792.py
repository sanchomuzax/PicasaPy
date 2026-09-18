"""#1792 — az album-fejléc gombsorának testreszabása: a TÁROLÁS és a
műveletek.

## A mérés, amire épül

Az eredetiben a fejléc (`headerpanel`) gombsora testreszabható volt: a
felhasználó eldönthette, mely gombok látszanak és milyen sorrendben. Két
registry-kulcs tárolta (`picasa-menu-parancsok-viselkedes.md` 44.):

| kulcs | mit tart |
|---|---|
| `Preferences\\Buttons\\UserConfig` | az összeállítás (sorrend) |
| `Preferences\\Buttons\\Exclude` | a KIHAGYOTT gombok |

⇒ A gombok nemcsak átrendezhetők, hanem elrejthetők is — ezért tart a
modul is **kettőt**: a sorrendet és a kihagyottakat.

⛔ A GUID→gombnév megfeleltetés nincs meg (a `#buttons\\` adatmappából
jönne), és nem is kell: nálunk a gomb saját **objektumneve** az
azonosító, kompatibilitási kötelezettség nélkül (a jegy törzse mondja ki).

## A készlet

A fejléc négy MŰVELET-gombja (`picasa-menu-parancsok-viselkedes.md` 56.1
élő listája, a nálunk meglévőkre szűkítve). Ami NEM tagja: a megszűnt
szolgáltatás gombja (`headerUploadButton`) és a személy-album
javaslat-vezérlői (#2187) — azok nem testreszabhatók, hanem
állapotfüggők.
"""

from __future__ import annotations

from PySide6.QtCore import QSettings

from picasapy.app.gombsav_beallitas import (
    ALAP_SORREND,
    TESTRESZABHATO,
    betoltsd,
    elerheto_gombok,
    lejjebb,
    feljebb,
    hozzaad,
    mentsd,
    torold,
    visszaall_alapra,
)


def _settings(tmp_path) -> QSettings:
    return QSettings(str(tmp_path / "proba.ini"), QSettings.Format.IniFormat)


class TestAKeszlet:
    def test_negy_testreszabhato_gomb(self):
        assert len(TESTRESZABHATO) == 4

    def test_az_alap_sorrend_a_teljes_keszlet(self):
        """Alapból MINDEN testreszabható gomb látszik — az eredetiben is a
        teljes készlet az alapállapot, a `Exclude` üresen indul."""
        assert list(ALAP_SORREND) == list(TESTRESZABHATO)

    def test_a_megszunt_szolgaltatas_gombja_NEM_tagja(self):
        """Ellenpróba: a feltöltés-gomb nem testreszabható, mert nem is
        működik (a Picasa Webalbumok 2016-ban megszűnt)."""
        assert "headerUploadButton" not in TESTRESZABHATO

    def test_a_javaslat_vezerlok_sem(self):
        """Azok ÁLLAPOTFÜGGŐK (#2187): akkor látszanak, ha van javaslat —
        ezt nem a felhasználó állítja."""
        assert "headerConfirmSuggestionsButton" not in TESTRESZABHATO


class TestMuveletek:
    def test_a_torles_kiveszi_a_sorbol(self):
        sorrend = list(ALAP_SORREND)

        uj = torold(sorrend, sorrend[1])

        assert sorrend[1] not in uj
        assert len(uj) == len(sorrend) - 1

    def test_a_torles_NEM_modositja_a_bemenetet(self):
        """Immutábilis műveletek — a Mégse csak így tud visszalépni."""
        sorrend = list(ALAP_SORREND)
        eredeti = list(sorrend)

        torold(sorrend, sorrend[0])

        assert sorrend == eredeti

    def test_a_hozzaadas_a_VEGERE_teszi(self):
        sorrend = torold(list(ALAP_SORREND), ALAP_SORREND[0])

        uj = hozzaad(sorrend, ALAP_SORREND[0])

        assert uj[-1] == ALAP_SORREND[0]

    def test_ismetelt_hozzaadas_nem_duplaz(self):
        uj = hozzaad(list(ALAP_SORREND), ALAP_SORREND[0])

        assert uj.count(ALAP_SORREND[0]) == 1

    def test_ismeretlen_gombot_nem_ad_hozza(self):
        """A készleten kívüli azonosító nem kerülhet a sorba — egy régi
        beállítás vagy elgépelés ne tegyen a fejlécre nem létező gombot."""
        uj = hozzaad(list(ALAP_SORREND), "nincsIlyenGomb")

        assert "nincsIlyenGomb" not in uj

    def test_feljebb_egyet_lep(self):
        sorrend = list(ALAP_SORREND)

        uj = feljebb(sorrend, sorrend[2])

        assert uj.index(sorrend[2]) == 1

    def test_az_elso_nem_megy_feljebb(self):
        sorrend = list(ALAP_SORREND)

        assert feljebb(sorrend, sorrend[0]) == sorrend

    def test_lejjebb_egyet_lep(self):
        sorrend = list(ALAP_SORREND)

        uj = lejjebb(sorrend, sorrend[0])

        assert uj.index(sorrend[0]) == 1

    def test_az_utolso_nem_megy_lejjebb(self):
        sorrend = list(ALAP_SORREND)

        assert lejjebb(sorrend, sorrend[-1]) == sorrend


class TestElerhetoek:
    def test_ami_nincs_a_sorban_az_elerheto(self):
        sorrend = torold(list(ALAP_SORREND), ALAP_SORREND[1])

        assert elerheto_gombok(sorrend) == [ALAP_SORREND[1]]

    def test_teljes_sornal_ures(self):
        assert elerheto_gombok(list(ALAP_SORREND)) == []


class TestTarolas:
    def test_mentes_utan_visszatoltheto(self, tmp_path):
        beallitasok = _settings(tmp_path)
        sorrend = torold(list(ALAP_SORREND), ALAP_SORREND[0])

        mentsd(beallitasok, sorrend)

        assert betoltsd(_settings(tmp_path)) == sorrend

    def test_ures_tarolonal_az_ALAP_jon(self, tmp_path):
        assert betoltsd(_settings(tmp_path)) == list(ALAP_SORREND)

    def test_ertelmetlen_ertek_az_ALAPRA_esik_vissza(self, tmp_path):
        """A `collage_prefs` elve: egy kézzel átírt beállítás sosem
        omlaszthatja el a felületet."""
        beallitasok = _settings(tmp_path)
        beallitasok.setValue("toolbar/headerButtons", "ez nem lista")
        beallitasok.sync()

        assert betoltsd(_settings(tmp_path)) == list(ALAP_SORREND)

    def test_az_ismeretlen_azonositokat_KISZURI(self, tmp_path):
        """Egy régebbi verzióból maradt gombnév ne kerüljön a fejlécre."""
        beallitasok = _settings(tmp_path)
        mentsd(beallitasok, [ALAP_SORREND[0], "regiGomb"])

        assert betoltsd(_settings(tmp_path)) == [ALAP_SORREND[0]]

    def test_az_URES_sor_is_ervenyes(self, tmp_path):
        """Minden gomb elrejthető — az üres fejléc szándékos állapot, nem
        hiba, tehát nem eshet vissza az alapra."""
        beallitasok = _settings(tmp_path)

        mentsd(beallitasok, [])

        assert betoltsd(_settings(tmp_path)) == []


class TestAlaphelyzet:
    def test_visszaall_a_teljes_keszletre(self):
        assert visszaall_alapra() == list(ALAP_SORREND)

    def test_uj_listat_ad(self):
        """Ne ugyanarra a listára mutasson, amit a hívó később módosít."""
        assert visszaall_alapra() is not ALAP_SORREND
