"""#6972: hálózati mappán a Revert külső-módosítás vizsgálata nem olvassa be a
fájlt a fő szálon (#6948), ezért ott ujjlenyomat és figyelmeztetés sincs."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from picasapy.app import save_external_change as modul


class _Vezerlo(modul.SaveExternalChangeMixin):
    def __init__(self, db_path: Path, rekordok: list) -> None:
        self._db_path = db_path
        self._rekordok = rekordok

    def _selected_records(self, rows):
        return [self._rekordok[i] for i in rows]


def test_halozati_kep_nem_kerul_ujjlenyomatba(tmp_path, monkeypatch):
    rogzitett: list[list[Path]] = []
    monkeypatch.setattr(modul, "record_saved", lambda tar, utak: rogzitett.append(list(utak)))
    vezerlo = _Vezerlo(tmp_path / "index.db", [])

    vezerlo._record_saved_fingerprints(
        [Path("//szerver/kepek/a.jpg"), tmp_path / "b.jpg"]
    )

    assert rogzitett == [[tmp_path / "b.jpg"]]


def test_csak_halozati_kepnel_nincs_tarirasa(tmp_path, monkeypatch):
    rogzitett: list = []
    monkeypatch.setattr(modul, "record_saved", lambda tar, utak: rogzitett.append(utak))
    vezerlo = _Vezerlo(tmp_path / "index.db", [])

    vezerlo._record_saved_fingerprints([Path("//szerver/kepek/a.jpg")])

    assert rogzitett == []


def test_halozati_kepet_a_revert_elott_nem_vizsgal(tmp_path, monkeypatch):
    vizsgalt: list[Path] = []

    def _valtozott(tar, ut):
        vizsgalt.append(ut)
        return True

    monkeypatch.setattr(modul, "changed_outside", _valtozott)
    rekordok = [
        SimpleNamespace(folder_path="//szerver/kepek", name="a.jpg"),
        SimpleNamespace(folder_path=str(tmp_path), name="b.jpg"),
    ]
    vezerlo = _Vezerlo(tmp_path / "index.db", rekordok)

    assert vezerlo.externallyChangedCount([0, 1]) == 1
    assert vizsgalt == [tmp_path / "b.jpg"]
