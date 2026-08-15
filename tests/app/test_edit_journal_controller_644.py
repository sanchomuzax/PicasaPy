"""A külső felülírás észlelése és helyreállítása — controller-szelet (#644).

A mixin ÖNÁLLÓAN, minimális host-osztályon tesztelt (a projekt bevett
mintája). A hangsúly két dolgon van:

- **ne zajongjon**: csak a SAJÁT, mentett szerkesztés elvesztésekor szóljunk;
- **egyszer szóljon**: a nézet másodpercenként többször is frissülhet, a
  felhasználót nem szabad ugyanazzal a veszteséggel újra és újra riasztani.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject

from picasapy.edit.edit_journal import load_journal
from picasapy.index.queries import PhotoRecord
from picasapy.ini.io import load_document

HOLGA = "holga=1;"
LUCKY = "enhance=1;"


def _Rekord(path: str, filters: str | None = None) -> PhotoRecord:
    """VALÓDI `index.queries.PhotoRecord` a megadott útvonalra.

    #699: itt korábban egy csonk dataclass állt `path` mezővel — olyan
    szerződést rögzített, amit a valóságban EGYIK `PhotoRecord` sem
    teljesít (`folder_path` + `name` van). Emiatt a #644 tesztje végig zöld
    volt, miközben a termékkód az első valódi rekordon elszállt, és a
    v0.7.53 EL SEM INDULT. A csonk visszavezetése tilos.
    """
    cel = Path(path)
    return PhotoRecord(
        id=0,
        folder_path=str(cel.parent),
        name=cel.name,
        kind="image",
        size=0,
        mtime_ns=0,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=filters,
        taken_at=None,
        orientation=1,
        width=None,
        height=None,
    )


@pytest.fixture
def host(tmp_path):
    from picasapy.app.edit_journal_controller import EditJournalMixin

    class _Host(EditJournalMixin, QObject):
        def __init__(self, db_path):
            super().__init__()
            self._db_path = db_path
            self.refresh_count = 0

        def _refresh_view(self) -> None:
            self.refresh_count += 1

    return _Host(tmp_path / "index.sqlite")


def _jelzesek(host):
    kapott = []
    host.editsOverwritten.connect(lambda lista: kapott.append(lista))
    return kapott


class TestNaplozas:
    def test_a_mentett_lanc_bekerul(self, host, tmp_path) -> None:
        host.recordSavedChain("/k/a.jpg", HOLGA)

        naplo = load_journal(tmp_path / "edit-journal.json")
        assert naplo["/k/a.jpg"].chain == HOLGA

    def test_az_ures_lanc_torol(self, host) -> None:
        host.recordSavedChain("/k/a.jpg", HOLGA)
        host.recordSavedChain("/k/a.jpg", "")

        assert load_journal(host._journal_file()) == {}


class TestEszleles:
    def test_a_letorolt_lanc_jelzest_ad(self, host) -> None:
        host.recordSavedChain("/k/a.jpg", HOLGA)
        kapott = _jelzesek(host)

        host._check_external_overwrites([_Rekord("/k/a.jpg", "")])

        assert len(kapott) == 1
        assert kapott[0][0]["path"] == "/k/a.jpg"
        assert kapott[0][0]["name"] == "a.jpg"
        assert kapott[0][0]["chain"] == HOLGA

    def test_a_valtozatlan_lanc_nem_jelez(self, host) -> None:
        host.recordSavedChain("/k/a.jpg", HOLGA)
        kapott = _jelzesek(host)

        host._check_external_overwrites([_Rekord("/k/a.jpg", HOLGA)])

        assert kapott == []

    def test_a_hozzafuzes_nem_jelez(self, host) -> None:
        """Ami MINKET nem érint, az ne zajongjon."""
        host.recordSavedChain("/k/a.jpg", HOLGA)
        kapott = _jelzesek(host)

        host._check_external_overwrites([_Rekord("/k/a.jpg", HOLGA + LUCKY)])

        assert kapott == []

    def test_kepenkent_csak_egyszer_jelez(self, host) -> None:
        """A nézet sokszor frissül — a felhasználót nem riasztjuk újra."""
        host.recordSavedChain("/k/a.jpg", HOLGA)
        kapott = _jelzesek(host)

        for _ in range(5):
            host._check_external_overwrites([_Rekord("/k/a.jpg", "")])

        assert len(kapott) == 1

    def test_ures_naplonal_nem_csinal_semmit(self, host) -> None:
        kapott = _jelzesek(host)

        host._check_external_overwrites([_Rekord("/k/a.jpg", "")])

        assert kapott == []


class TestHelyreallitas:
    def _kep_es_ini(self, tmp_path: Path):
        kep = tmp_path / "kepek" / "a.jpg"
        kep.parent.mkdir(parents=True)
        kep.write_bytes(b"nem valodi jpeg")
        (kep.parent / ".picasa.ini").write_text(
            "[a.jpg]\nstar=yes\n", encoding="utf-8"
        )
        return kep

    def test_visszairja_a_lancot(self, host, tmp_path) -> None:
        kep = self._kep_es_ini(tmp_path)
        host.recordSavedChain(str(kep), HOLGA)

        assert host.restoreOverwrittenEdit(str(kep)) is True

        szakasz = load_document(kep.parent / ".picasa.ini").section("a.jpg")
        assert szakasz.get("filters") == HOLGA

    def test_a_tobbi_kulcsot_megorzi(self, host, tmp_path) -> None:
        """A helyreállítás nem söpörheti el a Picasa saját bejegyzéseit —
        épp az ilyen felülírás ellen szól ez az egész jegy."""
        kep = self._kep_es_ini(tmp_path)
        host.recordSavedChain(str(kep), HOLGA)

        host.restoreOverwrittenEdit(str(kep))

        szakasz = load_document(kep.parent / ".picasa.ini").section("a.jpg")
        assert szakasz.get("star") == "yes"

    def test_frissiti_a_nezetet(self, host, tmp_path) -> None:
        kep = self._kep_es_ini(tmp_path)
        host.recordSavedChain(str(kep), HOLGA)
        elotte = host.refresh_count

        host.restoreOverwrittenEdit(str(kep))

        assert host.refresh_count == elotte + 1

    def test_naplo_nelkul_hamis(self, host, tmp_path) -> None:
        kep = self._kep_es_ini(tmp_path)

        assert host.restoreOverwrittenEdit(str(kep)) is False

    def test_ujra_jelez_ha_megint_elveszik(self, host, tmp_path) -> None:
        """Helyreállítás után egy ÚJABB felülírás megint jelzést érdemel."""
        kep = self._kep_es_ini(tmp_path)
        host.recordSavedChain(str(kep), HOLGA)
        kapott = _jelzesek(host)
        host._check_external_overwrites([_Rekord(str(kep), "")])
        host.restoreOverwrittenEdit(str(kep))

        host._check_external_overwrites([_Rekord(str(kep), "")])

        assert len(kapott) == 2
