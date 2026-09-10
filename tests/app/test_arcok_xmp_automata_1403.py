"""Az arc elnevezése után AUTOMATIKUSAN kiíródik az XMP (#1403).

## A mérés

Az eredetiben ez a parancs MÁSODIK belépési pontja: az arc elnevezése után a
program magától kiírja az arc-adatot a fájlba — kezelő `0x004852e0` (734 b), a
kapu a `0x00485382`-n, **alapérték 1 (BE)**. A hibaágai szó szerint:

```
Face tag write failed for read only file: %s
Face tag write failed for: %s
```

⚠️ A kapcsolóhoz NEM építünk felületi jelölőnégyzetet: az eredetiben a
`Preferences`-ág tartja, de hogy MELYIK panel mutatja, nincs kimérve. A
viselkedés (automatikus írás, alapból BE) enélkül is az eredetié — a
kitalált helyre tett vezérlő rosszabb volna, mint a hiánya.
"""

from __future__ import annotations

import os
import stat

import pytest
from PySide6.QtCore import QSettings
from support.jpeg_factory import make_jpeg

from picasapy.app.face_scan_controller import FaceScanController
from picasapy.index import open_index, sync_tree


class _FakeFacesHelper:
    """A `FacesHelper.addFace()` szerződése: ennyit használ a vezérlő."""

    def __init__(self, ini_path):
        self._ini = ini_path
        self.calls = []

    def addFace(self, path, left, top, right, bottom, name):  # noqa: N802
        self.calls.append((path, name))
        # a valódi helper a `.picasa.ini`-be ír — itt is ezt tesszük, mert az
        # XMP-építő EZT olvassa (nem az indexet)
        self._ini.write_text(
            f"[{os.path.basename(path)}]\n"
            f"faces=rect64(4000400080008000),1\n"
            f"[Contacts2]\n1={name};;\n",
            encoding="utf-8",
        )
        return True


@pytest.fixture
def kornyezet(qt_app, tmp_path):
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    kep = gyoker / "a.jpg"
    make_jpeg(kep)
    ini = gyoker / ".picasa.ini"
    ini.write_text("", encoding="utf-8")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
        foto_id = conn.execute("SELECT id FROM photos").fetchone()["id"]
        conn.execute(
            "INSERT INTO face(photo_id, rect_left, rect_top, rect_right,"
            " rect_bottom, det_conf, right_eye_x, right_eye_y, left_eye_x,"
            " left_eye_y, nose_x, nose_y, mouth_right_x, mouth_right_y,"
            " mouth_left_x, mouth_left_y, state)"
            " VALUES (?, 0.25, 0.25, 0.5, 0.5, 0.9,"
            " 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'unnamed')",
            (foto_id,),
        )
        conn.commit()
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    helper = _FakeFacesHelper(ini)
    ctl = FaceScanController(db, faces_helper=helper, settings=settings)
    return ctl, gyoker, kep, settings


def _arc_id(ctl):
    from picasapy.index import unnamed_faces

    with open_index(ctl._db_path) as conn:
        arcok = unnamed_faces(conn)
    assert arcok, "a próbához kell egy névtelen arc"
    return arcok[0].id


class TestAzAutomatikusIras:
    def test_nevadas_utan_van_sidecar(self, kornyezet):
        ctl, _gyoker, kep, _settings = kornyezet

        assert ctl.assignNameToFaces([_arc_id(ctl)], "Anna") is True

        sidecar = kep.with_name(kep.name + ".xmp")
        assert sidecar.exists(), (
            "az arc elnevezése után az eredeti MAGÁTÓL kiírja az XMP-t "
            "(alapérték BE) — nálunk nem történt meg"
        )
        szoveg = sidecar.read_text(encoding="utf-8")
        assert "Anna" in szoveg
        assert "mwg-rs:Regions" in szoveg
        assert "MP:RegionInfo" in szoveg

    def test_a_kapcsolo_KIKAPCSOLHATO(self, kornyezet):
        ctl, _gyoker, kep, settings = kornyezet
        settings.setValue(FaceScanController.XMP_ON_NAME_KEY, False)

        assert ctl.assignNameToFaces([_arc_id(ctl)], "Anna") is True

        assert not kep.with_name(kep.name + ".xmp").exists(), (
            "kikapcsolt kapcsolóval nem szabad XMP-t írni"
        )

    def test_az_alapertek_BE(self, kornyezet):
        """Az eredeti alapértéke 1 — a kulcs hiányában is írnunk kell."""
        ctl, _gyoker, _kep, settings = kornyezet
        settings.remove(FaceScanController.XMP_ON_NAME_KEY)

        assert ctl._xmp_iras_bekapcsolva() is True


@pytest.mark.skipif(
    os.name != "posix",
    reason="#1864: a `chmod` csak POSIX-on érvényesíti a jogosultságot — "
    "windowson a hibahelyzet elő sem áll, tehát az állítás hamisan zöld lenne",
)
class TestAzIrasvedettHely:
    def test_a_nevadas_SIKERES_marad_es_a_hiba_megnevezve_jon(self, kornyezet):
        """Az XMP-hiba nem vonhatja vissza a névadást.

        Az eredeti is külön hibaüzenetet ad a csak olvasható fájlra — a
        névadás maga sikeres."""
        ctl, gyoker, kep, _settings = kornyezet
        hibak = []
        ctl.xmpAutoWriteFailed.connect(hibak.append)
        # a mappa írásvédett: az ini-t a fake helper memóriában „írja", de a
        # sidecar kiírása elhasal
        gyoker.chmod(stat.S_IRUSR | stat.S_IXUSR)
        try:
            eredmeny = ctl.assignNameToFaces([_arc_id(ctl)], "Anna")
        finally:
            gyoker.chmod(stat.S_IRWXU)

        assert eredmeny is True, "a névadás sikeres volt — csak az XMP hasalt el"
        assert hibak, "a hibát MEG KELL nevezni (az eredeti is megnevezi)"
        assert "a.jpg" in hibak[0]
