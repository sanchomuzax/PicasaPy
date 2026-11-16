"""A mappamozgatás védelmének vezérlő-oldala (#7108).

A három QML menü (Mappa menü, mappa helyi menü, fa helyi menüje) ugyanazt a
vezérlő-kérdést teszi fel: védett-e a mappa a mozgatástól? A válasz ugyanaz a
predikátum, amit a végrehajtás is használ (`is_system_path`), tehát a menü
szürke tétele és a megálló végrehajtás nem térhet el egymástól.

A renderelt menüket a `qml_functional/test_mappa_athelyezes_szurke_7108.py`
méri.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.fileops_controller import FileOpsController
from support.ismert_mappak_7108 import ISMERT_NEVEK, kiegyenesit, profil_utak


@pytest.fixture
def vezerlo(tmp_path, qt_app):
    beallitasok = QSettings(str(tmp_path / "b.ini"), QSettings.Format.IniFormat)
    return FileOpsController(settings=beallitasok)


@pytest.fixture
def profil(monkeypatch, tmp_path) -> dict[str, Path]:
    utak = profil_utak(tmp_path / "profil")
    for ut in utak.values():
        ut.mkdir(parents=True)
    kiegyenesit(monkeypatch, utak)
    return utak


@pytest.mark.parametrize("nev", ISMERT_NEVEK)
def test_az_ismert_mappa_mozgatasa_vedett(vezerlo, profil, nev):
    assert vezerlo.isMoveProtectedFolder(str(profil[nev])) is True, nev


@pytest.mark.parametrize("nev", ISMERT_NEVEK)
def test_az_alattuk_allo_mappa_mozgathato(vezerlo, profil, nev):
    alatta = profil[nev] / "nyaralas"
    alatta.mkdir()

    assert vezerlo.isMoveProtectedFolder(str(alatta)) is False, nev


def test_a_home_es_a_rendszerut_tovabbra_is_vedett(vezerlo, profil):
    assert vezerlo.isMoveProtectedFolder(str(Path.home())) is True
    assert vezerlo.isMoveProtectedFolder(str(Path(Path.home().anchor))) is True


def test_a_hetkoznapi_mappa_mozgathato(vezerlo, profil, tmp_path):
    mappa = tmp_path / "kepek"
    mappa.mkdir()

    assert vezerlo.isMoveProtectedFolder(str(mappa)) is False


def test_az_ures_es_hianyzo_ut_nem_vedett_mappa(vezerlo, profil):
    """A QML a mappa kiválasztása ELŐTT is kérdezhet: üres szövegre a
    munkakönyvtárat tilthatná le a hibás feloldás."""
    assert vezerlo.isMoveProtectedFolder("") is False


def test_a_file_url_alak_is_feloldodik(vezerlo, profil):
    """A QML FolderDialog `file://` URL-t ad: ugyanúgy védett."""
    from picasapy.app.formatting import to_file_url

    assert vezerlo.isMoveProtectedFolder(
        to_file_url(str(profil["Pictures"])).toString()
    ) is True


@pytest.mark.parametrize("nev", ISMERT_NEVEK)
def test_a_vegrehajtas_is_megall_es_hibat_jelez(vezerlo, profil, tmp_path, nev):
    """A célválasztó UTÁN is megáll (az eredeti `0x0053f878`)."""
    cel = tmp_path / "cel"
    cel.mkdir()
    (profil[nev] / "a.jpg").write_bytes(b"kep")
    hibak: list[tuple[str, str]] = []
    athelyezve: list[tuple[str, str]] = []
    vezerlo.operationFailed.connect(lambda m, u: hibak.append((m, u)))
    vezerlo.folderMoved.connect(lambda a, b: athelyezve.append((a, b)))

    vezerlo.moveFolder(str(profil[nev]), str(cel))

    assert [muvelet for muvelet, _ in hibak] == ["move_folder"], nev
    assert "Rendszermappa" in hibak[0][1]
    assert athelyezve == []
    assert (profil[nev] / "a.jpg").exists()
    assert list(cel.iterdir()) == []


def test_halozati_mappan_nem_old_fel_utvonalat_7108(monkeypatch):
    """A menükötés mappaváltáskor fut; hálózati úton a `resolve()` a fő
    szálat megakaszthatná (#7086), ezért ott a predikátum meg sem hívódik."""
    import picasapy.halozati_ut as hu
    from picasapy.app import fileops_controller as fc

    hivas = []
    monkeypatch.setattr(hu, "is_network_path", lambda ut, **k: True)
    monkeypatch.setattr(fc, "is_system_path", lambda *a, **k: hivas.append(a) or True)
    vezerlo = fc.FileOpsController.__new__(fc.FileOpsController)
    assert vezerlo.isMoveProtectedFolder("/mnt/nas/kepek") is False
    assert hivas == []
