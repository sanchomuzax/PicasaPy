"""A képtálca (#455) FELÜLET-FÜGGETLEN magja — `picasapy.tray`.

A mag azért Qt-mentes, mert **két** felület ül majd rajta: a főablak alsó
sávjának képtálcája és a kollázs-szerkesztő „Klipek" lapja (#1276, #1153).
A Picasa saját szövegforrása mondja ki, hogy a kettő ugyanaz a
munkafolyamat: a `collagepanel/deleteclips` súgója szerint a „–" gomb
*„Remove selected clips from the **tray**"*, a filmszalag neve pedig
`Unused Pictures` — vagyis „a tálca elemei, a felhasználtság jelölésével".

A viselkedés forrása: `docs/specs/picasa-keptalca.md` és
`docs/decisions/keptalca-modell.md`.
"""

from __future__ import annotations

import dataclasses

import pytest

from picasapy import tray


class TestUresTalca:
    def test_az_ures_talca_semmit_nem_tart(self):
        assert tray.photo_ids(tray.EMPTY) == ()
        assert tray.held_ids(tray.EMPTY) == ()
        assert tray.unused_ids(tray.EMPTY) == ()
        assert tray.used_ids(tray.EMPTY) == ()

    def test_az_allapot_valtozhatatlan(self):
        """Immutábilis: a művelet ÚJ állapotot ad, a régit nem írja át."""
        elozo = tray.with_selection(tray.EMPTY, [1, 2])
        uj = tray.with_selection(elozo, [3])
        assert tray.photo_ids(elozo) == (1, 2)
        assert tray.photo_ids(uj) == (3,)
        with pytest.raises(dataclasses.FrozenInstanceError):
            elozo.items = ()  # type: ignore[misc]


class TestAKijelolesBekerul:
    """„A kijelölés automatikusan a tálcába kerül" (#455)."""

    def test_a_kijeloles_a_talcaba_kerul_beszurasi_sorrendben(self):
        allapot = tray.with_selection(tray.EMPTY, [7, 3, 9])
        assert tray.photo_ids(allapot) == (7, 3, 9)

    def test_az_ismetlodo_azonosito_egyszer_szerepel(self):
        allapot = tray.with_selection(tray.EMPTY, [4, 4, 5])
        assert tray.photo_ids(allapot) == (4, 5)

    def test_a_kovetkezo_kijeloles_ELSOPRI_a_nem_rogzitetteket(self):
        elso = tray.with_selection(tray.EMPTY, [1, 2])
        masodik = tray.with_selection(elso, [8])
        assert tray.photo_ids(masodik) == (8,)

    def test_ures_kijeloles_kiuriti_a_nem_rogzitetteket(self):
        allapot = tray.with_selection(tray.with_selection(tray.EMPTY, [1]), [])
        assert tray.photo_ids(allapot) == ()


class TestMegtartas:
    """A „Kijelölés megtartása" (Hold Selection) — ez teszi a tálcát
    MAPPÁKON ÁTNYÚLÓ gyűjtővé."""

    def test_a_rogzitett_kepet_a_kovetkezo_kijeloles_NEM_sopri_el(self):
        allapot = tray.with_hold(tray.with_selection(tray.EMPTY, [1, 2]))
        utana = tray.with_selection(allapot, [8])
        assert tray.photo_ids(utana) == (1, 2, 8)
        assert tray.held_ids(utana) == (1, 2)

    def test_tobb_mappa_gyujtese_egymas_utan(self):
        """A kör lényege: A mappából 2 kép, B mappából 1 — mind a három
        bent marad, beszúrási sorrendben."""
        allapot = tray.with_hold(tray.with_selection(tray.EMPTY, [11, 12]))
        allapot = tray.with_selection(allapot, [21, 22])
        allapot = tray.with_hold(allapot)
        allapot = tray.with_selection(allapot, [31])
        assert tray.photo_ids(allapot) == (11, 12, 21, 22, 31)

    def test_a_rogzites_celzottan_is_kerheto(self):
        allapot = tray.with_selection(tray.EMPTY, [1, 2, 3])
        allapot = tray.with_hold(allapot, [2])
        assert tray.held_ids(allapot) == (2,)
        assert tray.photo_ids(tray.with_selection(allapot, [9])) == (2, 9)

    def test_a_rogzites_a_talcan_kivuli_kepet_is_felveszi(self):
        """A `Tray` helyi menü parancsa akkor is működjön, ha az elem még
        nincs a tálcán (spec 3.: EGY parancs, egy belépési pont)."""
        allapot = tray.with_hold(tray.EMPTY, [5])
        assert tray.photo_ids(allapot) == (5,)
        assert tray.held_ids(allapot) == (5,)

    def test_a_rogzites_megtartja_a_sorrendet_es_a_jelzoket(self):
        allapot = tray.with_selection(tray.EMPTY, [1, 2])
        allapot = tray.with_used(allapot, [1])
        allapot = tray.with_hold(allapot)
        assert tray.photo_ids(allapot) == (1, 2)
        assert tray.used_ids(allapot) == (1,)


class TestEltavolitasEsUrites:
    def test_kijeloles_eltavolitasa(self):
        allapot = tray.with_hold(tray.with_selection(tray.EMPTY, [1, 2, 3]))
        assert tray.photo_ids(tray.without(allapot, [2])) == (1, 3)

    def test_a_nem_letezo_azonosito_eltavolitasa_nem_hiba(self):
        allapot = tray.with_selection(tray.EMPTY, [1])
        assert tray.photo_ids(tray.without(allapot, [99])) == (1,)

    def test_az_urites_mindent_elvisz_a_kuszobbel_egyutt(self):
        allapot = tray.with_hold(tray.with_selection(tray.EMPTY, [1, 2]))
        allapot = tray.with_remembered_count(allapot)
        ures = tray.cleared(allapot)
        assert tray.photo_ids(ures) == ()
        assert ures.remembered_count == 0


class TestFelhasznaltsag:
    """A Klipek fül ELŐKÉSZÍTÉSE: „a tálca elemei, a felhasználtság
    jelölésével". A `filmstrip_title` = `Unused Pictures`."""

    def test_a_felhasznalt_kep_a_talcan_MARAD(self):
        allapot = tray.with_hold(tray.with_selection(tray.EMPTY, [1, 2]))
        allapot = tray.with_used(allapot, [1])
        assert tray.photo_ids(allapot) == (1, 2)

    def test_de_kikerul_a_FEL_NEM_HASZNALTAK_kozul(self):
        allapot = tray.with_hold(tray.with_selection(tray.EMPTY, [1, 2]))
        allapot = tray.with_used(allapot, [1])
        assert tray.unused_ids(allapot) == (2,)
        assert tray.used_ids(allapot) == (1,)

    def test_a_jeloles_visszavonhato(self):
        allapot = tray.with_used(
            tray.with_selection(tray.EMPTY, [1]), [1])
        assert tray.unused_ids(tray.with_used(allapot, [1], used=False)) == (1,)

    def test_a_talcan_kivuli_azonosito_jelolese_nem_ad_uj_elemet(self):
        allapot = tray.with_used(tray.with_selection(tray.EMPTY, [1]), [42])
        assert tray.photo_ids(allapot) == (1,)

    def test_a_felhasznalt_kepet_a_kovetkezo_kijeloles_NEM_sopri_el(self):
        """A felhasználtság olyan állapot, amit a kijelölésből nem lehet
        visszaállítani — elsöpörni néma adatvesztés volna."""
        allapot = tray.with_used(tray.with_selection(tray.EMPTY, [1, 2]), [1])
        utana = tray.with_selection(allapot, [9])
        assert tray.photo_ids(utana) == (1, 9)


class TestRegotaTartottElemek:
    """A `il_ClearFromTray` felkínált takarítás küszöbe (spec 13.):
    **darabszám-növekedés**, nem kor. A feltétel: a NEM KIZÁRT elemek
    száma nagyobb, mint a legutóbb megjegyzett szám."""

    def test_ures_talcanal_nincs_kerdes(self):
        assert tray.needs_old_items_prompt(tray.EMPTY) is False

    def test_novekedeskor_van_kerdes(self):
        allapot = tray.with_hold(tray.with_selection(tray.EMPTY, [1, 2]))
        assert tray.needs_old_items_prompt(allapot) is True

    def test_a_megjegyzes_utan_nincs_kerdes(self):
        allapot = tray.with_hold(tray.with_selection(tray.EMPTY, [1, 2]))
        allapot = tray.with_remembered_count(allapot)
        assert tray.needs_old_items_prompt(allapot) is False

    def test_ujabb_novekedeskor_ismet_van(self):
        allapot = tray.with_remembered_count(
            tray.with_hold(tray.with_selection(tray.EMPTY, [1, 2])))
        allapot = tray.with_hold(tray.with_selection(allapot, [3]))
        assert tray.needs_old_items_prompt(allapot) is True

    def test_a_felhasznalt_elem_NEM_szamit_bele(self):
        """A számláló a nem kizárt elemeket számolja (`[elem+0x5a] == 0`)
        — ugyanaz a jelölő, amit a Klipek fül »Unused« számlálója kérdez."""
        allapot = tray.with_remembered_count(
            tray.with_hold(tray.with_selection(tray.EMPTY, [1, 2])))
        allapot = tray.with_hold(tray.with_selection(allapot, [3]))
        allapot = tray.with_used(allapot, [3])
        assert tray.needs_old_items_prompt(allapot) is False


class TestBemenetErvenyesites:
    @pytest.mark.parametrize("rossz", ["abc", None, 3.5])
    def test_az_ertelmezhetetlen_azonosito_hibat_dob(self, rossz):
        with pytest.raises((TypeError, ValueError)):
            tray.with_selection(tray.EMPTY, [rossz])

    @pytest.mark.parametrize("rossz", [0, -1])
    def test_a_nem_pozitiv_azonosito_hibat_dob(self, rossz):
        with pytest.raises(ValueError):
            tray.with_selection(tray.EMPTY, [rossz])

    def test_a_nem_bejarhato_bemenet_hibat_dob(self):
        with pytest.raises(TypeError):
            tray.with_selection(tray.EMPTY, 5)
