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
    record_saved_chains,
    save_journal,
)

HOLGA = "holga=1;"
LUCKY = "enhance=1;"
HOLGA_ES_LUCKY = "holga=1;enhance=1;"


#: #699: platformfüggetlen próba-útvonal. A napló kulcsát a KÖZÖS
#: `naplo_kulcs()` szabály adja, ami Windowson visszaperjelre normalizál —
#: a nyers "/k/a.jpg" ezért ott NEM egyezne. A windows-CI-láb fogta meg.
_UT = str(Path("/k/a.jpg"))
_UT2 = str(Path("/k/b.jpg"))


def _naplo(**parok) -> dict[str, JournalEntry]:
    return {
        ut: JournalEntry(path=ut, chain=lanc, saved_at="2026-08-14T10:00:00")
        for ut, lanc in parok.items()
    }


class TestFelvetel:
    def test_a_lancot_felirja(self) -> None:
        naplo = record_saved_chain({}, _UT, HOLGA, saved_at="2026-08-14T10:00:00")

        assert naplo[_UT].chain == HOLGA
        assert naplo[_UT].saved_at == "2026-08-14T10:00:00"

    def test_az_ujabb_mentes_felulirja_a_regit(self) -> None:
        naplo = _naplo(**{_UT: HOLGA})

        uj = record_saved_chain(naplo, _UT, HOLGA_ES_LUCKY, saved_at="2026-08-14T11:00:00")

        assert uj[_UT].chain == HOLGA_ES_LUCKY

    def test_az_ures_lanc_torli_a_bejegyzest(self) -> None:
        """Ha a felhasználó MAGA vonta vissza az összes szerkesztést, nincs
        mit védeni — különben örökre riasztanánk egy szándékos törlésre."""
        naplo = _naplo(**{_UT: HOLGA})

        uj = record_saved_chain(naplo, _UT, "", saved_at="2026-08-14T11:00:00")

        assert _UT not in uj

    def test_nem_mutalja_a_bemenetet(self) -> None:
        naplo = _naplo(**{_UT: HOLGA})

        record_saved_chain(naplo, _UT2, LUCKY, saved_at="2026-08-14T11:00:00")

        assert set(naplo) == {_UT}


class TestKotegeltFelvetel:
    """`record_saved_chains` — a kötegelt írók egyetlen menetben naplóznak.

    #750: a csoportos effekt és a beillesztések mappánként több száz képet
    írnak; ha a napló képenként töltődne be és íródna ki, a védelem lenne a
    köteg szűk keresztmetszete.
    """

    def test_egyszerre_tobb_lancot_felvesz(self) -> None:
        naplo = record_saved_chains(
            {}, ((_UT, HOLGA), (_UT2, LUCKY)), saved_at="2026-08-14T11:00:00"
        )

        assert naplo[_UT].chain == HOLGA
        assert naplo[_UT2].chain == LUCKY

    def test_az_ures_lanc_a_kotegben_is_torol(self) -> None:
        naplo = _naplo(**{_UT: HOLGA, _UT2: LUCKY})

        uj = record_saved_chains(
            naplo, ((_UT, ""), (_UT2, HOLGA)), saved_at="2026-08-14T11:00:00"
        )

        assert _UT not in uj
        assert uj[_UT2].chain == HOLGA

    def test_ugyanarra_az_utra_a_kesobbi_nyer(self) -> None:
        naplo = record_saved_chains(
            {}, ((_UT, HOLGA), (_UT, LUCKY)), saved_at="2026-08-14T11:00:00"
        )

        assert naplo[_UT].chain == LUCKY

    def test_nem_mutalja_a_bemenetet(self) -> None:
        naplo = _naplo(**{_UT: HOLGA})

        record_saved_chains(naplo, ((_UT2, LUCKY),), saved_at="2026-08-14T11:00:00")

        assert set(naplo) == {_UT}

    def test_az_ures_koteg_valtozatlanul_hagyja(self) -> None:
        naplo = _naplo(**{_UT: HOLGA})

        uj = record_saved_chains(naplo, (), saved_at="2026-08-14T11:00:00")

        assert uj == naplo


class TestEszleles:
    def test_a_teljesen_eltunt_lanc_veszteseg(self) -> None:
        """A bejelentett eset: a Picasa írása után a `filters=` eltűnt."""
        naplo = _naplo(**{_UT: HOLGA})

        veszteseg = detect_lost_edits(naplo, {_UT: ""})

        assert [v.path for v in veszteseg] == [_UT]
        assert veszteseg[0].chain == HOLGA

    def test_a_masik_effektre_cserelt_lanc_is_veszteseg(self) -> None:
        """A Picasa a SAJÁT effektjét írta a helyünkre — a miénk elveszett."""
        naplo = _naplo(**{_UT: HOLGA})

        veszteseg = detect_lost_edits(naplo, {_UT: LUCKY})

        assert [v.path for v in veszteseg] == [_UT]

    def test_a_valtozatlan_lanc_nem_veszteseg(self) -> None:
        naplo = _naplo(**{_UT: HOLGA})

        assert detect_lost_edits(naplo, {_UT: HOLGA}) == ()

    def test_a_hozzafuzes_nem_veszteseg(self) -> None:
        """A jegy kikötése: ami MINKET nem érint, az ne zajongjon. Ha a
        Picasa a mi láncunk MELLÉ írt, a miénk megvan — nincs mit jelenteni."""
        naplo = _naplo(**{_UT: HOLGA})

        assert detect_lost_edits(naplo, {_UT: HOLGA_ES_LUCKY}) == ()

    def test_a_sorrend_nem_szamit(self) -> None:
        """A Picasa a saját rekordjából más sorrendben írhatja ki a láncot —
        attól a mi effektünk még megvan."""
        naplo = _naplo(**{_UT: HOLGA})

        assert detect_lost_edits(naplo, {_UT: "enhance=1;holga=1;"}) == ()

    def test_a_lancbol_egy_elem_elvesztese_is_veszteseg(self) -> None:
        naplo = _naplo(**{_UT: HOLGA_ES_LUCKY})

        veszteseg = detect_lost_edits(naplo, {_UT: LUCKY})

        assert [v.path for v in veszteseg] == [_UT]

    def test_a_nem_vizsgalt_kep_kimarad(self) -> None:
        """Csak arról nyilatkozunk, aminek a mai állapotát láttuk — egy be
        nem olvasott mappa nem jelent veszteséget."""
        naplo = _naplo(**{_UT: HOLGA, "/mas/b.jpg": LUCKY})

        veszteseg = detect_lost_edits(naplo, {_UT: HOLGA})

        assert veszteseg == ()

    def test_tobb_veszteseg_utvonal_szerint_rendezve(self) -> None:
        """Determinisztikus sorrend — a felhasználónak mutatott lista ne
        ugráljon futásonként."""
        naplo = _naplo(**{_UT2: HOLGA, _UT: HOLGA})

        veszteseg = detect_lost_edits(naplo, {_UT: "", _UT2: ""})

        assert [v.path for v in veszteseg] == [_UT, _UT2]


class TestTarolas:
    def test_korbejar(self, tmp_path: Path) -> None:
        utvonal = tmp_path / "napló.json"
        naplo = _naplo(**{_UT: HOLGA, _UT2: LUCKY})

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

        save_journal(_naplo(**{_UT: HOLGA}), utvonal)

        assert utvonal.exists()


class TestHelyreallitas:
    def test_a_veszteseg_hordozza_a_visszairando_lancot(self) -> None:
        """A helyreállításhoz a jelzésnek magával kell hoznia a láncot —
        a napló időközben felülíródhat."""
        naplo = _naplo(**{_UT: HOLGA_ES_LUCKY})

        veszteseg = detect_lost_edits(naplo, {_UT: ""})

        assert veszteseg[0].chain == HOLGA_ES_LUCKY

    @pytest.mark.parametrize("ervenytelen", ["", "   ", None])
    def test_az_ures_naplobejegyzes_nem_kepez_vesztesget(self, ervenytelen) -> None:
        naplo = {
            _UT: JournalEntry(
                path=_UT, chain=ervenytelen or "", saved_at="2026-08-14T10:00:00"
            )
        }

        assert detect_lost_edits(naplo, {_UT: ""}) == ()
