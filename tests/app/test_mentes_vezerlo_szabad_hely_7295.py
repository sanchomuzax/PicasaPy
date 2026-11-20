"""#7295: A biztonsági mentés vezérlője kevés hely esetén a hivatalos szöveget jelez.

Mappába mentésnél és lemezkép-írásnál, ha a cél szabad helye kisebb, mint a
terv összmérete, a vezérlő leállítja a folyamatot és a
"Not Enough Disk Space to Backup Files" (HU: "Nincs elegendő hely a fájlok
biztonsági mentéséhez") hivatalos szöveggel jelez hibát a felület felé.
"""

from __future__ import annotations

from collections import namedtuple

import pytest

from picasapy.app.backup_controller import BackupController
from picasapy.burn import CD
from picasapy.index import open_index
from support.jpeg_factory import make_jpeg

_Usage = namedtuple("_Usage", ["total", "used", "free"])


@pytest.fixture
def gyujtemeny(tmp_path):
    gyoker = tmp_path / "kepek"
    (gyoker / "nyaralas").mkdir(parents=True)
    make_jpeg(gyoker / "nyaralas" / "a.jpg")
    make_jpeg(gyoker / "nyaralas" / "b.jpg")
    return gyoker


@pytest.fixture
def vezerlo(qt_app, tmp_path, gyujtemeny):
    from picasapy.index import sync_tree

    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyujtemeny)
    return BackupController(db, (str(gyujtemeny),))


def _vard_be(vezerlo, qt_app) -> None:
    assert vezerlo.waitForBackgroundWorkers(20.0), "a háttérszál nem állt le"
    qt_app.processEvents()


class TestVezerloSzabadHely:
    def test_keves_hely_mappaba_mentesnel_hivatalos_szoveget_jelez(
        self, qt_app, vezerlo, tmp_path, monkeypatch
    ):
        from picasapy.backup import futtatas as futtatas_modul

        cel = tmp_path / "mentes_cel"
        vezerlo.ujKeszlet("Mentes", str(cel), "minden")
        keszlet_id = vezerlo.keszletek()[0]["id"]

        hibak: list[str] = []
        vezerlo.hibatJelez.connect(hibak.append)

        # Szimulált kevés hely (0 szabad bájt)
        monkeypatch.setattr(
            futtatas_modul,
            "_disk_usage",
            lambda path: _Usage(total=10_000_000, used=10_000_000, free=0),
        )

        vezerlo.futtasdMost(keszlet_id)
        _vard_be(vezerlo, qt_app)

        assert hibak, "nem jelzett hibát kevés lemezhely esetén"
        # A hivatalos szöveg (angol / magyar)
        vart_szovegek = {
            "Not Enough Disk Space to Backup Files",
            "Nincs elegendő hely a fájlok biztonsági mentéséhez",
        }
        assert any(
            vart in hibak[0] or hibak[0] in vart_szovegek for vart in vart_szovegek
        ), f"nem a hivatalos szöveg jelent meg: {hibak[0]}"
        assert not (cel / "nyaralas" / "a.jpg").exists()

    def test_keves_hely_lemezkepnel_hivatalos_szoveget_jelez(
        self, qt_app, vezerlo, tmp_path, monkeypatch
    ):
        from picasapy.backup import lemezkep as lemezkep_modul

        cel = tmp_path / "iso_cel"
        vezerlo.ujKeszlet("ISO_Mentes", str(cel), "minden")
        keszlet_id = vezerlo.keszletek()[0]["id"]

        hibak: list[str] = []
        vezerlo.hibatJelez.connect(hibak.append)

        # Szimulált kevés hely (0 szabad bájt)
        monkeypatch.setattr(
            lemezkep_modul,
            "_disk_usage",
            lambda path: _Usage(total=10_000_000, used=10_000_000, free=0),
        )

        vezerlo.futtasdLemezkepbe(keszlet_id, CD)
        _vard_be(vezerlo, qt_app)

        assert hibak, "nem jelzett hibát kevés lemezhely esetén"
        vart_szovegek = {
            "Not Enough Disk Space to Backup Files",
            "Nincs elegendő hely a fájlok biztonsági mentéséhez",
        }
        assert any(
            vart in hibak[0] or hibak[0] in vart_szovegek for vart in vart_szovegek
        ), f"nem a hivatalos szöveg jelent meg: {hibak[0]}"
        assert list(cel.glob("*.iso")) == []
