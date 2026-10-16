"""#4609: az e-mailhez készült `picasapy-mail-*` másolatok indításkor törlődnek.

A vezérlő minden küldésnél új ideiglenes mappába írja az átméretezett
csatolmányokat, és soha nem takarítja ki őket — a lemez évről évre telne.
Az indulás a `EmailController` egyszeri példányosítása (`application.py`);
ott a régi mappák törlődnek. Az ideiglenes gyökér a `_gettempdir` modul-
szintű fogantyún át érkezik, hogy a teszt a valódi `/tmp`-hez ne nyúljon."""

from __future__ import annotations

import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication

from picasapy.app import email_controller as email_controller_module
from picasapy.app.email_controller import EmailController


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


@pytest.fixture
def ideiglenes_gyoker(tmp_path, monkeypatch):
    """Az ideiglenes gyökér: egy üres mappa a basetempben."""
    gyoker = tmp_path / "gyoker"
    gyoker.mkdir()
    monkeypatch.setattr(email_controller_module, "_gettempdir", lambda: str(gyoker))
    return gyoker


def _oregit(*mappak):
    """Két órával korábbi módosítási idő: a takarítás csak ilyet töröl."""
    regen = time.time() - 2 * 3600
    for mappa in mappak:
        os.utime(mappa, (regen, regen))


def _vezerlo(tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return EmailController(photo_source=lambda: [], settings=settings)


def test_indulaskor_a_regi_mail_mappak_torlodnek(qt_app, tmp_path, ideiglenes_gyoker):
    """A régi másolat-mappa (benne fájllal) indulás után eltűnik."""
    regi = ideiglenes_gyoker / "picasapy-mail-regi"
    regi.mkdir()
    (regi / "kep.jpg").write_bytes(b"\xff\xd8 teszt")
    masik_regi = ideiglenes_gyoker / "picasapy-mail-masik"
    masik_regi.mkdir()
    _oregit(regi, masik_regi)

    _vezerlo(tmp_path)

    assert not regi.exists()
    assert not masik_regi.exists()


def test_mas_mappak_erintetlenek(qt_app, tmp_path, ideiglenes_gyoker):
    """Csak a `picasapy-mail-*` mappák mennek: más mappa és fájl marad."""
    idegen_mappa = ideiglenes_gyoker / "mas-program"
    idegen_mappa.mkdir()
    idegen_fajl = ideiglenes_gyoker / "picasapy-mail-fajl.txt"
    idegen_fajl.write_text("nem mappa", encoding="utf-8")

    _vezerlo(tmp_path)

    assert idegen_mappa.is_dir()
    assert idegen_fajl.is_file()


def test_ures_gyokernel_nincs_hiba(qt_app, tmp_path, ideiglenes_gyoker):
    """Nincs régi másolat: a példányosítás nem bukik el."""
    vezerlo = _vezerlo(tmp_path)

    assert vezerlo is not None
    assert list(ideiglenes_gyoker.iterdir()) == []


def test_a_mappa_nevevel_egyezo_symlink_nem_torlodik_celpontjaval(
    qt_app, tmp_path, ideiglenes_gyoker
):
    """Symlink nem követhető törléshez: a célmappa (a gyökéren kívül) megmarad."""
    cel = tmp_path / "kulso-cel"
    cel.mkdir()
    (cel / "adat.txt").write_text("maradjon", encoding="utf-8")
    link = ideiglenes_gyoker / "picasapy-mail-link"
    link.symlink_to(cel, target_is_directory=True)

    _vezerlo(tmp_path)

    assert (cel / "adat.txt").is_file()


def test_a_friss_mappa_megmarad(qt_app, tmp_path, ideiglenes_gyoker):
    """Egy óránál frissebb mappa marad: egy másik példány épp küldhet belőle."""
    friss = ideiglenes_gyoker / "picasapy-mail-friss"
    friss.mkdir()

    _vezerlo(tmp_path)

    assert friss.is_dir()
