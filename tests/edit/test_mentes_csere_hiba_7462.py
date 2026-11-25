"""#7462: sikertelen mentésnél a kész kép `<név>.<kit>.jpg` néven megmarad.

Forrás: `docs/specs/paritas-folyamat-7345.md`, „B7 / #7428 eredménye”: írásvédett
célnál (`job-957`) az eredeti változatlan, `.picasaoriginals` mentés nincs, a
kész kimenet `color_patches.jpg.jpg` néven ott marad; írható célnál (`job-963`)
`.jpg.jpg` nem keletkezik.

Két út méri a csere hibáját:

* a valódi írásvédett fájl (`chmod`) csak POSIX-on: Windowson a próba a csere
  hibáját szimulálja;
* a szimulált csere-hiba (`ioutil._replace`) mindkét CI-lábon fut.
"""

from __future__ import annotations

import errno
import stat
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

import picasapy.edit.save as save_modul
import picasapy.edit.save_storage as save_storage
import picasapy.ioutil as ioutil
from picasapy.app.save_error_kind import KIND_DISK, save_error_code, save_error_kind
from picasapy.edit import (
    LEGACY_ORIGINALS_DIR_NAME,
    ORIGINALS_DIR_NAME,
    EditSession,
    revert,
    save_edited,
)

_INI_NAME = ".picasa.ini"
_NEV = "color_patches.jpg"
_MARADVANY = "color_patches.jpg.jpg"
_INI = f"[{_NEV}]\nfilters=enhance=1;\nunknownfield=marad\n"
_UJ_SZIN = (200, 40, 40)


def _kep(szin: tuple[int, int, int], meret: int = 16) -> np.ndarray:
    kep = np.zeros((meret, meret, 3), dtype=np.uint8)
    kep[:, :] = szin
    return kep


def _jpeg(kep: np.ndarray) -> bytes:
    ok, kodolt = cv2.imencode(".jpg", kep)
    assert ok
    return kodolt.tobytes()


def _atlagszin(ut: Path) -> tuple[int, ...]:
    kep = cv2.imdecode(np.frombuffer(ut.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)
    assert kep is not None, f"nem nyitható meg képként: {ut}"
    return tuple(int(round(float(c))) for c in kep.reshape(-1, 3).mean(axis=0))


def _kozel(szin: tuple[int, ...], vart: tuple[int, int, int]) -> bool:
    return all(abs(a - b) <= 6 for a, b in zip(szin, vart, strict=True))


def _nevek(mappa: Path) -> list[str]:
    return sorted(p.name for p in mappa.iterdir())


@pytest.fixture
def foto(tmp_path):
    ut = tmp_path / _NEV
    eredeti = _jpeg(_kep((10, 20, 30)))
    ut.write_bytes(eredeti)
    (tmp_path / _INI_NAME).write_text(_INI, encoding="utf-8")
    return ut, eredeti


def _mentes(ut: Path, szin: tuple[int, int, int] = _UJ_SZIN) -> None:
    save_edited(ut, _kep(szin), EditSession.from_value("enhance=1;"))


def _csere_elbukik(monkeypatch, cel: Path) -> None:
    """A `cel`-re irányuló csere `PermissionError`-ral bukik, minden más megy."""
    valodi = ioutil._replace

    def csere(forras, hova):
        if Path(hova) == cel:
            raise PermissionError(errno.EACCES, "Access is denied")
        return valodi(forras, hova)

    monkeypatch.setattr(ioutil, "_replace", csere)
    monkeypatch.setattr(save_modul, "_ZAR_KESLELTETES", 0.0)


def _ellenorizd_a_hibas_mentest(ut: Path, eredeti: bytes, ini_elotte: bytes) -> None:
    mappa = ut.parent
    assert ut.read_bytes() == eredeti
    assert (mappa / _INI_NAME).read_bytes() == ini_elotte
    assert not (mappa / ORIGINALS_DIR_NAME).exists()
    assert _nevek(mappa) == sorted([_INI_NAME, _NEV, _MARADVANY])
    assert _kozel(_atlagszin(mappa / _MARADVANY), _UJ_SZIN)


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windowson a chmod nem véd írás ellen (#7462)"
)
class TestValodiIrasvedettFajl:
    def test_az_eredeti_marad_a_kesz_kep_jpg_jpg_neven_all(self, foto):
        ut, eredeti = foto
        ini_elotte = (ut.parent / _INI_NAME).read_bytes()
        ut.chmod(0o444)

        with pytest.raises(PermissionError) as hiba:
            _mentes(ut)

        _ellenorizd_a_hibas_mentest(ut, eredeti, ini_elotte)
        # a hibaablak a mostani: lemezhiba-ág, `hiba(11)`
        assert save_error_kind(hiba.value) == KIND_DISK
        assert save_error_code(hiba.value) == 11

    def test_a_maradvany_nem_orokli_az_irasvedettseget(self, foto):
        ut, _eredeti = foto
        ut.chmod(0o444)

        with pytest.raises(PermissionError):
            _mentes(ut)

        assert stat.S_IMODE(ut.stat().st_mode) == 0o444
        assert (ut.parent / _MARADVANY).stat().st_mode & stat.S_IWRITE


class TestNemJpegCel:
    def test_png_celnel_nem_marad_jpg_utotagu_fajl(self, tmp_path, monkeypatch):
        """A `.jpg.jpg` a JPEG-író terméke (#7428); PNG-re nincs mérés,
        ezért ott a mai viselkedés marad: a kész kép nem marad meg."""
        ut = tmp_path / "color_patches.png"
        ok, kodolt = cv2.imencode(".png", _kep((10, 20, 30)))
        assert ok
        eredeti = kodolt.tobytes()
        ut.write_bytes(eredeti)
        (tmp_path / _INI_NAME).write_text(
            "[color_patches.png]\nfilters=enhance=1;\n", encoding="utf-8"
        )
        _csere_elbukik(monkeypatch, ut)

        with pytest.raises(PermissionError):
            _mentes(ut)

        assert ut.read_bytes() == eredeti
        assert not (tmp_path / "color_patches.png.jpg").exists()
        assert not (tmp_path / ORIGINALS_DIR_NAME).exists()


class TestACsereHibaja:
    def test_az_eredeti_marad_a_kesz_kep_jpg_jpg_neven_all(self, foto, monkeypatch):
        ut, eredeti = foto
        ini_elotte = (ut.parent / _INI_NAME).read_bytes()
        _csere_elbukik(monkeypatch, ut)

        with pytest.raises(PermissionError) as hiba:
            _mentes(ut)

        _ellenorizd_a_hibas_mentest(ut, eredeti, ini_elotte)
        assert save_error_code(hiba.value) == 11

    def test_nem_PermissionError_csere_hibanal_is_megmarad(self, foto, monkeypatch):
        ut, eredeti = foto
        valodi = ioutil._replace

        def csere(forras, hova):
            if Path(hova) == ut:
                raise OSError(errno.EIO, "Input/output error")
            return valodi(forras, hova)

        monkeypatch.setattr(ioutil, "_replace", csere)

        with pytest.raises(OSError):
            _mentes(ut)

        assert ut.read_bytes() == eredeti
        assert (ut.parent / _MARADVANY).is_file()
        assert not (ut.parent / ORIGINALS_DIR_NAME).exists()

    def test_a_korabbi_mentes_eredetije_es_pillanatkepe_megmarad(
        self, foto, monkeypatch
    ):
        ut, eredeti = foto
        _mentes(ut, (40, 90, 40))
        elso = ut.read_bytes()
        originals = ut.parent / ORIGINALS_DIR_NAME
        elotte = sorted(p.relative_to(originals) for p in originals.rglob("*"))
        _csere_elbukik(monkeypatch, ut)

        with pytest.raises(PermissionError):
            _mentes(ut)

        assert ut.read_bytes() == elso
        assert (originals / _NEV).read_bytes() == eredeti
        assert sorted(p.relative_to(originals) for p in originals.rglob("*")) == elotte
        assert _kozel(_atlagszin(ut.parent / _MARADVANY), _UJ_SZIN)

    def test_regi_Originals_mappa_mellett_sem_marad_uj_mappa(self, foto, monkeypatch):
        ut, eredeti = foto
        regi = ut.parent / LEGACY_ORIGINALS_DIR_NAME
        regi.mkdir()
        (regi / _NEV).write_bytes(eredeti)
        _csere_elbukik(monkeypatch, ut)

        with pytest.raises(PermissionError):
            _mentes(ut)

        assert (regi / _NEV).read_bytes() == eredeti
        assert not (ut.parent / ORIGINALS_DIR_NAME).exists()

    def test_meglevo_jpg_jpg_fajlt_nem_ir_felul(self, foto, monkeypatch):
        """A `.jpg.jpg` nevű fájl lehet a felhasználó saját képe is."""
        ut, _eredeti = foto
        sajat = ut.parent / _MARADVANY
        sajat.write_bytes(b"a felhasznalo sajat fajlja")
        _csere_elbukik(monkeypatch, ut)

        with pytest.raises(PermissionError):
            _mentes(ut)

        assert sajat.read_bytes() == b"a felhasznalo sajat fajlja"
        assert _nevek(ut.parent) == sorted([_INI_NAME, _NEV, _MARADVANY])

    def test_a_megtartas_hibaja_nem_takarja_el_a_csere_hibajat(
        self, foto, monkeypatch
    ):
        """Ha a `.jpg.jpg` név nem hozható létre, a csere hibája megy tovább,
        és ideiglenes fájl sem marad."""
        ut, eredeti = foto
        _csere_elbukik(monkeypatch, ut)

        def nem_nevezheto(forras, cel):
            raise OSError(errno.ENAMETOOLONG, "File name too long")

        monkeypatch.setattr(save_storage, "_atnevez", nem_nevezheto)

        with pytest.raises(PermissionError):
            _mentes(ut)

        assert ut.read_bytes() == eredeti
        assert _nevek(ut.parent) == sorted([_INI_NAME, _NEV])


class TestAholNemKeletkezhetMaradvany:
    def test_irhato_celnal_nincs_jpg_jpg(self, foto):
        ut, eredeti = foto

        _mentes(ut)

        assert not (ut.parent / _MARADVANY).exists()
        assert (ut.parent / ORIGINALS_DIR_NAME / _NEV).read_bytes() == eredeti
        assert _kozel(_atlagszin(ut), _UJ_SZIN)

    def test_a_kep_irasanak_hibaja_torli_az_ideiglenes_fajlt(self, foto, monkeypatch):
        """Még nincs kész kép (tele lemez írás közben): mint eddig, takarítás."""
        ut, eredeti = foto
        valodi_temp = ioutil._mkstemp
        valodi_fsync = ioutil._fsync
        utolso_mappa: list[Path] = []

        def temp(**kwargs):
            utolso_mappa.append(Path(kwargs["dir"]))
            return valodi_temp(**kwargs)

        def fsync(fd):
            # csak a képmappába szánt ideiglenes fájl írása bukik el
            if utolso_mappa and utolso_mappa[-1] == ut.parent:
                raise OSError(errno.ENOSPC, "No space left on device")
            return valodi_fsync(fd)

        monkeypatch.setattr(ioutil, "_mkstemp", temp)
        monkeypatch.setattr(ioutil, "_fsync", fsync)

        with pytest.raises(OSError, match="No space left"):
            _mentes(ut)

        assert ut.read_bytes() == eredeti
        assert set(_nevek(ut.parent)) <= {_INI_NAME, _NEV, ORIGINALS_DIR_NAME}

    def test_a_visszaallitas_csere_hibaja_nem_hagy_jpg_jpg_fajlt(self, foto, monkeypatch):
        ut, _eredeti = foto
        _mentes(ut)
        mentett = ut.read_bytes()
        elotte = _nevek(ut.parent)
        _csere_elbukik(monkeypatch, ut)

        with pytest.raises(PermissionError):
            revert(ut)

        assert ut.read_bytes() == mentett
        assert _nevek(ut.parent) == elotte
        assert _MARADVANY not in elotte
