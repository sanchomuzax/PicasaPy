"""A Mappa áthelyezése megjegyzi az utolsó célmappát (#7067).

Az eredeti `0x0053f4a0` a `Preferences/MoveFolderLastPath` kulcsot olvassa és
írja vissza. Ez az őr a vezérlő oldalát méri: mikor jegyzi meg, mikor nem,
és mi a kezdőhely, ha a megjegyzett út nincs vagy eltűnt. A valódi
kattintásos folyamatot a `qml_functional/test_mappa_athelyezes_cim_es_
utolso_cel_7067.py` próbálja.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings, QUrl

from picasapy.app.fileops_controller import FileOpsController

KULCS = "Preferences/MoveFolderLastPath"


@pytest.fixture
def beallitasok(tmp_path):
    return QSettings(str(tmp_path / "beallitasok.ini"), QSettings.Format.IniFormat)


@pytest.fixture
def vezerlo(beallitasok, qt_app):
    return FileOpsController(settings=beallitasok)


def _hibak(vezerlo) -> list[tuple[str, str]]:
    lista: list[tuple[str, str]] = []
    vezerlo.operationFailed.connect(lambda muvelet, uzenet: lista.append((muvelet, uzenet)))
    return lista


def _helyi(url: QUrl) -> Path:
    return Path(url.toLocalFile())


def test_megjegyzett_ut_nelkul_a_kezdohely_a_forras_szuloje(vezerlo, tmp_path):
    forras = tmp_path / "gyujtemeny" / "forras"
    forras.mkdir(parents=True)

    assert _helyi(vezerlo.moveFolderStartUrl(str(forras))) == forras.parent


def test_sikeres_athelyezes_utan_a_celmappa_megmarad(vezerlo, beallitasok, tmp_path):
    forras = tmp_path / "gyujtemeny" / "forras"
    cel = tmp_path / "cel"
    forras.mkdir(parents=True)
    cel.mkdir()

    vezerlo.moveFolder(str(forras), QUrl.fromLocalFile(str(cel)).toString())

    assert (cel / "forras").is_dir()
    assert Path(str(beallitasok.value(KULCS))) == cel


def test_a_kovetkezo_kezdohely_a_megjegyzett_celmappa(vezerlo, tmp_path):
    elso = tmp_path / "gyujtemeny" / "elso"
    masodik = tmp_path / "gyujtemeny" / "masodik"
    cel = tmp_path / "cel"
    elso.mkdir(parents=True)
    masodik.mkdir()
    cel.mkdir()

    vezerlo.moveFolder(str(elso), str(cel))

    assert _helyi(vezerlo.moveFolderStartUrl(str(masodik))) == cel


def test_eltunt_megjegyzett_cel_utan_a_forras_szuloje_a_kezdohely(vezerlo, tmp_path):
    elso = tmp_path / "gyujtemeny" / "elso"
    masodik = tmp_path / "gyujtemeny" / "masodik"
    cel = tmp_path / "cel"
    elso.mkdir(parents=True)
    masodik.mkdir()
    cel.mkdir()
    vezerlo.moveFolder(str(elso), str(cel))

    (cel / "elso").rmdir()
    cel.rmdir()

    assert _helyi(vezerlo.moveFolderStartUrl(str(masodik))) == masodik.parent


def test_sikertelen_athelyezes_nem_jegyez_meg_celt(vezerlo, beallitasok, tmp_path):
    forras = tmp_path / "gyujtemeny" / "forras"
    cel = tmp_path / "cel"
    forras.mkdir(parents=True)
    (cel / "forras").mkdir(parents=True)
    hibak = _hibak(vezerlo)

    vezerlo.moveFolder(str(forras), str(cel))

    assert [muvelet for muvelet, _ in hibak] == ["move_folder"]
    assert forras.is_dir()
    assert beallitasok.value(KULCS) is None
    assert _helyi(vezerlo.moveFolderStartUrl(str(forras))) == forras.parent


def test_ures_cel_nem_jegyez_meg_semmit(vezerlo, beallitasok, tmp_path):
    forras = tmp_path / "forras"
    forras.mkdir()
    _hibak(vezerlo)

    vezerlo.moveFolder(str(forras), "")

    assert beallitasok.value(KULCS) is None
