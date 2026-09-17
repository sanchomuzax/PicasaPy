"""#1721 (ADR-014) — a kézi sorrend VEZÉRLŐ-oldala: átrendezés és mentés.

A rácson húzással átrendezett képek sorrendje a mappa `.picasa.ini`-jébe
kerül (`priority=`), és a rendezés onnantól erre a szempontra áll.

## Amit a próbák kimondanak

| szabály | honnan |
|---|---|
| az átrendezés a mappa `.picasa.ini`-jét írja | ADR-014 |
| ÜRES mappánál (nincs egyetlen `priority=` sem) az egész sorrend kiíródik EGYSZER | az ADR „ne írja át az egész mappát" szabályának bootstrap-ága |
| ha már VAN kézi hely, egy áthelyezés csak a MOZGATOTT képek kulcsát írja | ADR-014 (felezőpontos beszúrás) |
| az átrendezés a rendezést „kézi sorrend"-re állítja | különben a felhasználó húzása látszólag visszaugrana (saját döntés, kimondva) |
| mappahatárt nem lép át | a kijelölés hatóköre EGY mappa (#1219, mérve) |
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from picasapy.app.kezi_sorrend import (
    atrendezett_prioritasok,
    ellenorizd_az_egy_mappat,
)
from picasapy.ini.document import parse_document
from picasapy.ini.priority import olvasd_a_prioritasokat


@dataclass(frozen=True)
class _Kep:
    folder_path: str
    name: str


def _mappa(nevek, mappa="/fotok"):
    return [_Kep(mappa, nev) for nev in nevek]


class TestAzEgyMappaSzabaly:
    def test_egy_mappaban_levo_kepek_rendben(self):
        kepek = _mappa(["a.jpg", "b.jpg"])

        assert ellenorizd_az_egy_mappat(kepek) == "/fotok"

    def test_ket_mappa_eseten_None(self):
        """A kijelölés hatóköre EGY mappa (#1219) — több mappán át nincs
        értelmezhető kézi sorrend, mert a `priority` mappánként él."""
        kepek = [_Kep("/a", "a.jpg"), _Kep("/b", "b.jpg")]

        assert ellenorizd_az_egy_mappat(kepek) is None

    def test_ures_lista_eseten_None(self):
        assert ellenorizd_az_egy_mappat([]) is None


class TestABootstrap:
    """Ha a mappában MÉG NINCS egyetlen kézi hely sem."""

    def test_az_egesz_uj_sorrend_kiirodik(self):
        sorrend = ["b.jpg", "a.jpg", "c.jpg"]

        uj = atrendezett_prioritasok(sorrend, {}, mozgatott={"b.jpg"})

        assert uj == {"b.jpg": 0.0, "a.jpg": 1.0, "c.jpg": 2.0}

    def test_a_kiirt_ertekek_a_kert_sorrendet_adjak(self):
        sorrend = ["b.jpg", "a.jpg", "c.jpg"]

        uj = atrendezett_prioritasok(sorrend, {}, mozgatott={"b.jpg"})

        assert sorted(uj, key=lambda nev: uj[nev]) == sorrend


class TestFelezopontosBeszuras:
    """Ha már VAN kézi hely: egy áthelyezés EGY kulcsot ír."""

    def test_ket_szomszed_koze_a_felezopont_kerul(self):
        # a mai sorrend: a(0) b(1) c(2); a `c`-t a és b közé húzzuk
        meglevo = {"a.jpg": 0.0, "b.jpg": 1.0, "c.jpg": 2.0}
        sorrend = ["a.jpg", "c.jpg", "b.jpg"]

        uj = atrendezett_prioritasok(sorrend, meglevo, mozgatott={"c.jpg"})

        assert uj == {"c.jpg": 0.5}

    def test_a_lista_elejere_huzva_kisebb_ertek(self):
        meglevo = {"a.jpg": 0.0, "b.jpg": 1.0}
        sorrend = ["b.jpg", "a.jpg"]

        uj = atrendezett_prioritasok(sorrend, meglevo, mozgatott={"b.jpg"})

        assert uj == {"b.jpg": -1.0}

    def test_a_lista_vegere_huzva_nagyobb_ertek(self):
        meglevo = {"a.jpg": 0.0, "b.jpg": 1.0}
        sorrend = ["b.jpg", "a.jpg"]

        uj = atrendezett_prioritasok(sorrend, meglevo, mozgatott={"a.jpg"})

        assert uj == {"a.jpg": 2.0}

    def test_tobb_kep_egyutt_mozgatva_kulon_erteket_kap(self):
        """Blokkos húzás: a mozgatott képek EGYMÁS UTÁN maradnak, és a
        felezőpontok között osztoznak."""
        meglevo = {"a.jpg": 0.0, "b.jpg": 1.0, "c.jpg": 2.0, "d.jpg": 3.0}
        sorrend = ["a.jpg", "c.jpg", "d.jpg", "b.jpg"]

        uj = atrendezett_prioritasok(
            sorrend, meglevo, mozgatott={"c.jpg", "d.jpg"}
        )

        assert sorted(uj) == ["c.jpg", "d.jpg"]
        assert uj["c.jpg"] < uj["d.jpg"]
        assert 0.0 < uj["c.jpg"] and uj["d.jpg"] < 1.0

    def test_a_nem_mozgatott_kepek_kulcsa_erintetlen(self):
        meglevo = {"a.jpg": 0.0, "b.jpg": 1.0, "c.jpg": 2.0}
        sorrend = ["a.jpg", "c.jpg", "b.jpg"]

        uj = atrendezett_prioritasok(sorrend, meglevo, mozgatott={"c.jpg"})

        assert "a.jpg" not in uj
        assert "b.jpg" not in uj


class TestAzIniIras:
    """A kiszámolt értékek tényleg a fájlba kerülnek."""

    def test_az_ini_a_szamokat_kapja(self, tmp_path):
        from picasapy.app.kezi_sorrend import mentsd_a_prioritasokat

        ini = tmp_path / ".picasa.ini"
        ini.write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")

        mentsd_a_prioritasokat(tmp_path, {"a.jpg": 1.5, "b.jpg": 2.0})

        doc = parse_document(ini.read_text(encoding="utf-8"))
        assert olvasd_a_prioritasokat(doc) == {"a.jpg": 1.5, "b.jpg": 2.0}
        assert "star=yes" in ini.read_text(encoding="utf-8")

    def test_ures_szotarra_nem_ir(self, tmp_path):
        ini = tmp_path / ".picasa.ini"
        ini.write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        elotte = ini.read_bytes()

        from picasapy.app.kezi_sorrend import mentsd_a_prioritasokat

        mentsd_a_prioritasokat(tmp_path, {})

        assert ini.read_bytes() == elotte


class TestAMegvalositasHatarai:
    def test_ismeretlen_nev_a_sorrendben_nem_hibazik(self):
        """A modell és az ini elcsúszhat (közben törölt fájl) — a számítás
        ilyenkor sem dobhat: a rács átrendezése fontosabb, mint a
        teljesség."""
        uj = atrendezett_prioritasok(["nincs.jpg"], {"a.jpg": 1.0}, mozgatott=set())

        assert isinstance(uj, dict)

    @pytest.mark.parametrize("mozgatott", [set(), {"nincs.jpg"}])
    def test_mozgatas_nelkul_nincs_iras(self, mozgatott):
        meglevo = {"a.jpg": 0.0, "b.jpg": 1.0}

        assert atrendezett_prioritasok(["a.jpg", "b.jpg"], meglevo, mozgatott) == {}


class TestAzUjNevsorrend:
    """A húzás eredménye: a mozgatott blokk a cél ELÉ kerül."""

    def _kepek(self, nevek, mappa="/fotok"):
        return [_Kep(mappa, nev) for nev in nevek]

    def test_a_blokk_a_cel_ele_kerul(self):
        from picasapy.app.folder_photo_sort_controller import _uj_nevsorrend

        kepek = self._kepek(["a.jpg", "b.jpg", "c.jpg", "d.jpg"])

        assert _uj_nevsorrend(kepek, {"d.jpg"}, kepek[1]) == [
            "a.jpg",
            "d.jpg",
            "b.jpg",
            "c.jpg",
        ]

    def test_cel_nelkul_a_mappa_vegere(self):
        from picasapy.app.folder_photo_sort_controller import _uj_nevsorrend

        kepek = self._kepek(["a.jpg", "b.jpg", "c.jpg"])

        assert _uj_nevsorrend(kepek, {"a.jpg"}, None) == [
            "b.jpg",
            "c.jpg",
            "a.jpg",
        ]

    def test_a_blokk_relativ_sorrendje_megmarad(self):
        from picasapy.app.folder_photo_sort_controller import _uj_nevsorrend

        kepek = self._kepek(["a.jpg", "b.jpg", "c.jpg", "d.jpg"])

        assert _uj_nevsorrend(kepek, {"b.jpg", "d.jpg"}, kepek[0]) == [
            "b.jpg",
            "d.jpg",
            "a.jpg",
            "c.jpg",
        ]

    def test_masik_mappa_celja_a_veget_jelenti(self):
        """A kézi sorrend mappánként él — egy másik mappa képére ejtve a
        blokk a SAJÁT mappája végére kerül, nem költözik át."""
        from picasapy.app.folder_photo_sort_controller import _uj_nevsorrend

        kepek = self._kepek(["a.jpg", "b.jpg"])
        idegen = _Kep("/masik", "x.jpg")

        assert _uj_nevsorrend(kepek, {"a.jpg"}, idegen) == ["b.jpg", "a.jpg"]
