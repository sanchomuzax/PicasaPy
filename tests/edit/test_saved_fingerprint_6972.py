"""#6972: a mentéskor rögzített ujjlenyomat jelzi, ha a kép a mentés óta
kívülről módosult (az eredeti `0x0053b87e`: „changed outside of Picasa")."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from picasapy.edit import EditSession, save_edited
from picasapy.edit.saved_fingerprint import (
    changed_outside,
    content_signature,
    forget,
    record_saved,
)
from picasapy.metadata import write_iptc_caption

_NEV = "IMG_6972.jpg"


def _jpeg(szin: tuple[int, int, int], meret: int = 16) -> bytes:
    ok, kodolt = cv2.imencode(".jpg", np.full((meret, meret, 3), szin, dtype=np.uint8))
    assert ok
    return kodolt.tobytes()


def _mentett_kep(mappa: Path) -> tuple[Path, Path]:
    """Egy valódi mentés után: a kép és a tár fájlja."""
    kep = mappa / _NEV
    kep.write_bytes(_jpeg((10, 20, 30)))
    save_edited(kep, np.full((16, 16, 3), (90, 80, 70), dtype=np.uint8),
                EditSession.from_value("bw=1;"))
    tar = mappa / "adat" / "saved-fingerprints.json"
    tar.parent.mkdir()
    record_saved(tar, [kep])
    return kep, tar


class TestTartalomAlairas:
    def test_a_metaadat_szegmens_nem_szamit(self, tmp_path):
        kep = tmp_path / _NEV
        kep.write_bytes(_jpeg((1, 2, 3)))
        elotte = content_signature(kep.read_bytes())
        assert write_iptc_caption(kep, "Nyaralás")
        assert kep.read_bytes() != _jpeg((1, 2, 3)), "az IPTC-írás nem változtatott"
        assert content_signature(kep.read_bytes()) == elotte

    def test_a_kepadat_valtozasa_szamit(self):
        assert content_signature(_jpeg((1, 2, 3))) != content_signature(_jpeg((200, 2, 3)))

    def test_nem_jpeg_bemenetnel_a_teljes_bajtsor_szamit(self):
        assert content_signature(b"PNGDATA-1") != content_signature(b"PNGDATA-2")
        assert content_signature(b"PNGDATA-1") == content_signature(b"PNGDATA-1")

    def test_csonka_jpeg_nem_dob_kivetelt(self):
        assert content_signature(b"\xff\xd8\xff\xe0\x00") != ""


class TestKulsoModositas:
    def test_valtozatlan_mentett_kep_nem_modosult(self, tmp_path):
        kep, tar = _mentett_kep(tmp_path)
        assert changed_outside(tar, kep) is False

    def test_kivulrol_felulirt_kep_modosultnak_szamit(self, tmp_path):
        kep, tar = _mentett_kep(tmp_path)
        kep.write_bytes(_jpeg((250, 5, 5), meret=32))
        assert changed_outside(tar, kep) is True

    def test_a_sajat_felirat_iras_nem_kulso_modositas(self, tmp_path):
        kep, tar = _mentett_kep(tmp_path)
        assert write_iptc_caption(kep, "Nyaralás")
        assert changed_outside(tar, kep) is False

    def test_rogzites_nelkul_nincs_figyelmeztetes(self, tmp_path):
        kep = tmp_path / _NEV
        kep.write_bytes(_jpeg((10, 20, 30)))
        assert changed_outside(tmp_path / "nincs.json", kep) is False

    def test_az_elfelejtett_bejegyzes_nem_jelez(self, tmp_path):
        kep, tar = _mentett_kep(tmp_path)
        kep.write_bytes(_jpeg((250, 5, 5), meret=32))
        forget(tar, [kep])
        assert changed_outside(tar, kep) is False

    def test_hianyzo_kep_nem_jelez(self, tmp_path):
        kep, tar = _mentett_kep(tmp_path)
        kep.unlink()
        assert changed_outside(tar, kep) is False

    def test_a_masik_eredetihez_tartozo_bejegyzes_elavult(self, tmp_path):
        """Ugyanarra az útvonalra később másik kép és másik eredeti került:
        a régi ujjlenyomat nem riaszthat."""
        kep, tar = _mentett_kep(tmp_path)
        eredeti = tmp_path / ".picasaoriginals" / _NEV
        eredeti.write_bytes(eredeti.read_bytes() + b"\x00" * 7)
        kep.write_bytes(_jpeg((250, 5, 5), meret=32))
        assert changed_outside(tar, kep) is False

    def test_serult_tarfajl_nem_dob_es_nem_jelez(self, tmp_path):
        kep, tar = _mentett_kep(tmp_path)
        tar.write_text("{ez nem json", encoding="utf-8")
        kep.write_bytes(_jpeg((250, 5, 5), meret=32))
        assert changed_outside(tar, kep) is False

    def test_a_tar_tobb_kepet_kulon_kezel(self, tmp_path):
        kep, tar = _mentett_kep(tmp_path)
        masik = tmp_path / "MASIK.jpg"
        masik.write_bytes(_jpeg((5, 5, 5)))
        save_edited(masik, np.full((16, 16, 3), (9, 9, 9), dtype=np.uint8),
                    EditSession.from_value("bw=1;"))
        record_saved(tar, [masik])
        masik.write_bytes(_jpeg((250, 5, 5), meret=32))
        assert changed_outside(tar, masik) is True
        assert changed_outside(tar, kep) is False
        assert set(json.loads(tar.read_text(encoding="utf-8"))) == {
            str(kep), str(masik),
        }
