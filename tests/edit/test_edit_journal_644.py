"""A szerkesztés-napló: külső felülírás észlelése és helyreállítás (#644).

**A hiba.** A `.picasa.ini` a projekt igazságforrása, és a szerkesztési lánc
(`filters=`) MÁS SEHOL nem él. Ha a párhuzamosan futó eredeti Picasa kiírja a
saját adatbázis-rekordját ugyanabba az iniba, a mi láncunk — amit a rekordja
nem tartalmaz — egyszerűen elmarad. A felhasználó munkája **figyelmeztetés
nélkül megsemmisül**, a belőle épülő visszavonás-veremmel együtt.

**A napló** ezért a saját írásainkat egy tőlünk függő, tartós helyre is
felírja. Ebből három dolog lesz:

1. **észlelés** — a lánc eltűnését látjuk, nem csak elszenvedjük;
2. **figyelmeztetés** — meg tudjuk mondani, MELYIK kép szerkesztése veszett;
3. **helyreállítás** — a lánc visszaírható.

A napló NEM a fotó mappájába ír: egy külső program azt is felülírhatja.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.edit.edit_journal import (
    JournalEntry,
    detect_lost_edits,
    load_journal,
    record_saved_chain,
    save_journal,
)

HOLGA = "holga=1;"
LUCKY = "enhance=1;"
HOLGA_ES_LUCKY = "holga=1;enhance=1;"


def _naplo(**parok) -> dict[str, JournalEntry]:
    return {
        ut: JournalEntry(path=ut, chain=lanc, saved_at="2026-08-14T10:00:00")
        for ut, lanc in parok.items()
    }


class TestFelvetel:
    def test_a_lancot_felirja(self) -> None:
        naplo = record_saved_chain({}, "/k/a.jpg", HOLGA, saved_at="2026-08-14T10:00:00")

        assert naplo["/k/a.jpg"].chain == HOLGA
        assert naplo["/k/a.jpg"].saved_at == "2026-08-14T10:00:00"

    def test_az_ujabb_mentes_felulirja_a_regit(self) -> None:
        naplo = _naplo(**{"/k/a.jpg": HOLGA})

        uj = record_saved_chain(naplo, "/k/a.jpg", HOLGA_ES_LUCKY, saved_at="2026-08-14T11:00:00")

        assert uj["/k/a.jpg"].chain == HOLGA_ES_LUCKY

    def test_az_ures_lanc_torli_a_bejegyzest(self) -> None:
        """Ha a felhasználó MAGA vonta vissza az összes szerkesztést, nincs
        mit védeni — különben örökre riasztanánk egy szándékos törlésre."""
        naplo = _naplo(**{"/k/a.jpg": HOLGA})

        uj = record_saved_chain(naplo, "/k/a.jpg", "", saved_at="2026-08-14T11:00:00")

        assert "/k/a.jpg" not in uj

    def test_nem_mutalja_a_bemenetet(self) -> None:
        naplo = _naplo(**{"/k/a.jpg": HOLGA})

        record_saved_chain(naplo, "/k/b.jpg", LUCKY, saved_at="2026-08-14T11:00:00")

        assert set(naplo) == {"/k/a.jpg"}


class TestEszleles:
    def test_a_teljesen_eltunt_lanc_veszteseg(self) -> None:
        """A bejelentett eset: a Picasa írása után a `filters=` eltűnt."""
        naplo = _naplo(**{"/k/a.jpg": HOLGA})

        veszteseg = detect_lost_edits(naplo, {"/k/a.jpg": ""})

        assert [v.path for v in veszteseg] == ["/k/a.jpg"]
        assert veszteseg[0].chain == HOLGA

    def test_a_masik_effektre_cserelt_lanc_is_veszteseg(self) -> None:
        """A Picasa a SAJÁT effektjét írta a helyünkre — a miénk elveszett."""
        naplo = _naplo(**{"/k/a.jpg": HOLGA})

        veszteseg = detect_lost_edits(naplo, {"/k/a.jpg": LUCKY})

        assert [v.path for v in veszteseg] == ["/k/a.jpg"]

    def test_a_valtozatlan_lanc_nem_veszteseg(self) -> None:
        naplo = _naplo(**{"/k/a.jpg": HOLGA})

        assert detect_lost_edits(naplo, {"/k/a.jpg": HOLGA}) == ()

    def test_a_hozzafuzes_nem_veszteseg(self) -> None:
        """A jegy kikötése: ami MINKET nem érint, az ne zajongjon. Ha a
        Picasa a mi láncunk MELLÉ írt, a miénk megvan — nincs mit jelenteni."""
        naplo = _naplo(**{"/k/a.jpg": HOLGA})

        assert detect_lost_edits(naplo, {"/k/a.jpg": HOLGA_ES_LUCKY}) == ()

    def test_a_sorrend_nem_szamit(self) -> None:
        """A Picasa a saját rekordjából más sorrendben írhatja ki a láncot —
        attól a mi effektünk még megvan."""
        naplo = _naplo(**{"/k/a.jpg": HOLGA})

        assert detect_lost_edits(naplo, {"/k/a.jpg": "enhance=1;holga=1;"}) == ()

    def test_a_lancbol_egy_elem_elvesztese_is_veszteseg(self) -> None:
        naplo = _naplo(**{"/k/a.jpg": HOLGA_ES_LUCKY})

        veszteseg = detect_lost_edits(naplo, {"/k/a.jpg": LUCKY})

        assert [v.path for v in veszteseg] == ["/k/a.jpg"]

    def test_a_nem_vizsgalt_kep_kimarad(self) -> None:
        """Csak arról nyilatkozunk, aminek a mai állapotát láttuk — egy be
        nem olvasott mappa nem jelent veszteséget."""
        naplo = _naplo(**{"/k/a.jpg": HOLGA, "/mas/b.jpg": LUCKY})

        veszteseg = detect_lost_edits(naplo, {"/k/a.jpg": HOLGA})

        assert veszteseg == ()

    def test_tobb_veszteseg_utvonal_szerint_rendezve(self) -> None:
        """Determinisztikus sorrend — a felhasználónak mutatott lista ne
        ugráljon futásonként."""
        naplo = _naplo(**{"/k/b.jpg": HOLGA, "/k/a.jpg": HOLGA})

        veszteseg = detect_lost_edits(naplo, {"/k/a.jpg": "", "/k/b.jpg": ""})

        assert [v.path for v in veszteseg] == ["/k/a.jpg", "/k/b.jpg"]


class TestTarolas:
    def test_korbejar(self, tmp_path: Path) -> None:
        utvonal = tmp_path / "napló.json"
        naplo = _naplo(**{"/k/a.jpg": HOLGA, "/k/b.jpg": LUCKY})

        save_journal(naplo, utvonal)

        assert load_journal(utvonal) == naplo

    def test_hianyzo_fajl_ures_naplo(self, tmp_path: Path) -> None:
        assert load_journal(tmp_path / "nincs.json") == {}

    def test_serult_fajl_ures_naplo(self, tmp_path: Path) -> None:
        """Sérült napló nem omlaszthatja el a programot — legfeljebb a
        védelmet veszítjük el, a fotókat nem."""
        utvonal = tmp_path / "napló.json"
        utvonal.write_text("{ ez nem json", encoding="utf-8")

        assert load_journal(utvonal) == {}

    def test_a_konyvtarat_letrehozza(self, tmp_path: Path) -> None:
        utvonal = tmp_path / "mely" / "abb" / "napló.json"

        save_journal(_naplo(**{"/k/a.jpg": HOLGA}), utvonal)

        assert utvonal.exists()


class TestHelyreallitas:
    def test_a_veszteseg_hordozza_a_visszairando_lancot(self) -> None:
        """A helyreállításhoz a jelzésnek magával kell hoznia a láncot —
        a napló időközben felülíródhat."""
        naplo = _naplo(**{"/k/a.jpg": HOLGA_ES_LUCKY})

        veszteseg = detect_lost_edits(naplo, {"/k/a.jpg": ""})

        assert veszteseg[0].chain == HOLGA_ES_LUCKY

    @pytest.mark.parametrize("ervenytelen", ["", "   ", None])
    def test_az_ures_naplobejegyzes_nem_kepez_vesztesget(self, ervenytelen) -> None:
        naplo = {
            "/k/a.jpg": JournalEntry(
                path="/k/a.jpg", chain=ervenytelen or "", saved_at="2026-08-14T10:00:00"
            )
        }

        assert detect_lost_edits(naplo, {"/k/a.jpg": ""}) == ()
