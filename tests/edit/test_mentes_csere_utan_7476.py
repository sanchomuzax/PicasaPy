"""#7476: ha a kép cseréje megtörtént, de utána hiba jön, kép és ini illeszkedjen.

Eddig ilyenkor a kép már a szerkesztett volt, az ini `filters=` sora viszont a
régi lánc, így a kép következő megnyitáskor kétszer szerkesztettnek látszott.
Ha ráadásul maga a csere hívása jelzett hibát, a megőrzött eredeti is törlődött.

A hibát az `ioutil` fogantyúi (`_replace`, `_fsync_directory`) szimulálják, ezért
a próbák mindkét CI-lábon futnak.
"""

from __future__ import annotations

import errno
import shutil
from pathlib import Path

import cv2
import numpy as np
import pytest

import picasapy.edit.save as save_modul
import picasapy.ini.io as ini_io
import picasapy.ioutil as ioutil
from picasapy.edit import (
    ORIGINALS_DIR_NAME,
    SNAPSHOT_DIR_NAME,
    EditSession,
    SaveError,
    save_edited,
    undo_save,
)
from picasapy.ini import load_document, update_document

_INI_NAME = ".picasa.ini"
_NEV = "color_patches.jpg"
_INI = f"[{_NEV}]\nfilters=enhance=1;\nunknownfield=marad\n"
_UJ_SZIN = (30, 200, 200)


def _kep(szin: tuple[int, int, int]) -> np.ndarray:
    kep = np.zeros((16, 16, 3), dtype=np.uint8)
    kep[:, :] = szin
    return kep


def _mentes(ut: Path, szin: tuple[int, int, int] = (200, 40, 40)):
    return save_edited(ut, _kep(szin), EditSession.from_value("enhance=1;"))


def _fa(mappa: Path) -> dict[str, bytes | None]:
    """A mappa tartalma: út -> bájtok (mappánál `None`), `.bak` nélkül."""
    return {
        p.relative_to(mappa).as_posix(): p.read_bytes() if p.is_file() else None
        for p in mappa.rglob("*")
        if p.suffix != ".bak"
    }


def _ertek(ini: Path, kulcs: str) -> str | None:
    szakasz = load_document(ini).section(_NEV)
    return szakasz.get(kulcs) if szakasz is not None else None


def _hiba() -> OSError:
    return OSError(errno.EIO, "Input/output error")


def _kep_cserei(monkeypatch, kep: Path, *viselkedesek) -> None:
    """A kép N-edik cseréje helyett az N-edik `viselkedes(forras, cel, csere)`.

    A felsoroltak utáni cserék és a többi fájl cseréje a valódi.
    """
    valodi = ioutil._replace
    hatra = list(viselkedesek)

    def csere(forras, hova):
        if Path(hova) != kep or not hatra:
            return valodi(forras, hova)
        return hatra.pop(0)(Path(forras), Path(hova), valodi)

    monkeypatch.setattr(ioutil, "_replace", csere)
    monkeypatch.setattr(save_modul, "_ZAR_KESLELTETES", 0.0)


def _cserel_majd_hiba(forras, cel, csere):
    csere(forras, cel)
    raise _hiba()


def _cserel_majd_zarolast_jelez(forras, cel, csere):
    """Windows-minta: a `PermissionError` után a helper újrapróbál."""
    csere(forras, cel)
    raise PermissionError(errno.EACCES, "Access is denied")


def _masol_a_temp_marad(forras, cel, _csere):
    """Nem atomikus átnevezés: a cél már az új, a forrás is megvan még."""
    shutil.copyfile(forras, cel)
    raise _hiba()


def _nem_cserel(_forras, _cel, _csere):
    raise _hiba()


def _mappa_fsync_hiba(monkeypatch, kep: Path, *, egyszer: bool) -> None:
    """A kép cseréje utáni könyvtár-fsync dob (`egyszer`, vagy mindig)."""
    valodi = ioutil._fsync_directory
    elsult = [False]

    def fsync(mappa):
        if Path(mappa) == kep.parent and not (egyszer and elsult[0]):
            elsult[0] = True
            raise _hiba()
        valodi(mappa)

    monkeypatch.setattr(ioutil, "_fsync_directory", fsync)


_CSERE_UTANI_HIBAK = {
    "mappa-fsync": lambda m, kep: _mappa_fsync_hiba(m, kep, egyszer=True),
    "mappa-fsync-tartosan": lambda m, kep: _mappa_fsync_hiba(m, kep, egyszer=False),
    "csere-jelez-hibat": lambda m, kep: _kep_cserei(m, kep, _cserel_majd_hiba),
    "csere-zarolast-jelez": lambda m, kep: _kep_cserei(
        m, kep, _cserel_majd_zarolast_jelez
    ),
    "masolat-temp-marad": lambda m, kep: _kep_cserei(m, kep, _masol_a_temp_marad),
}


def _mentes_elbukik(monkeypatch, ut: Path, hibaut: str) -> OSError:
    """Egy meghiúsult mentés; a szimuláció a végén visszaáll."""
    with monkeypatch.context() as m:
        _CSERE_UTANI_HIBAK[hibaut](m, ut)
        with pytest.raises(OSError) as elkapott:
            _mentes(ut, _UJ_SZIN)
    return elkapott.value


@pytest.fixture
def foto(tmp_path):
    ut = tmp_path / _NEV
    ok, kodolt = cv2.imencode(".jpg", _kep((10, 20, 30)))
    assert ok
    ut.write_bytes(kodolt.tobytes())
    (tmp_path / _INI_NAME).write_bytes(_INI.encode("utf-8"))
    return ut


@pytest.mark.parametrize("hibaut", _CSERE_UTANI_HIBAK)
class TestACsereUtaniHibaVisszaallit:
    def test_elso_mentes_utan_minden_a_regi_nyom_nelkul(
        self, foto, monkeypatch, hibaut
    ):
        elotte = _fa(foto.parent)

        _mentes_elbukik(monkeypatch, foto, hibaut)

        assert _fa(foto.parent) == elotte

    def test_a_visszavonas_nem_torol_szerkesztest(self, foto, monkeypatch, hibaut):
        elotte = _fa(foto.parent)
        _mentes_elbukik(monkeypatch, foto, hibaut)

        with pytest.raises(SaveError):
            undo_save(foto)

        assert _fa(foto.parent) == elotte

    def test_ismetelt_mentesnel_a_korabbi_mentes_vonhato_vissza(
        self, foto, monkeypatch, hibaut
    ):
        eredeti = foto.read_bytes()
        _mentes(foto)
        update_document(
            foto.parent / _INI_NAME,
            lambda doc: doc.with_value(_NEV, "filters", "enhance=1;"),
            touch=False,
        )
        elotte = _fa(foto.parent)

        _mentes_elbukik(monkeypatch, foto, hibaut)

        assert _fa(foto.parent) == elotte
        undo_save(foto)
        assert foto.read_bytes() == eredeti
        assert _ertek(foto.parent / _INI_NAME, "filters") == "enhance=1;"


class TestHaAzUjTartalomAzonosARegivel:
    def test_a_hiba_tovabbmegy_es_minden_a_regi(self, foto, monkeypatch):
        """A bájtokból nem látszik a csere, és a kép sem változott."""
        _mentes(foto, _UJ_SZIN)
        elotte = _fa(foto.parent)

        _mentes_elbukik(monkeypatch, foto, "mappa-fsync")

        assert _fa(foto.parent) == elotte


class TestHaARegiKepNemIrhatoVissza:
    """A szerkesztett kép a helyén marad, ezért a mentés befejeződik."""

    @staticmethod
    def _szimulal(m, kep: Path, hibaut: str) -> None:
        if hibaut == "mappa-fsync":
            _mappa_fsync_hiba(m, kep, egyszer=True)
            _kep_cserei(m, kep, lambda f, c, csere: csere(f, c), _nem_cserel)
        else:
            _kep_cserei(m, kep, _cserel_majd_hiba, _nem_cserel)

    @pytest.mark.parametrize("hibaut", ["mappa-fsync", "csere-jelez-hibat"])
    def test_az_ini_a_mentett_allapotot_kapja_es_a_nyom_marad(
        self, foto, monkeypatch, hibaut
    ):
        eredeti = foto.read_bytes()

        with monkeypatch.context() as m:
            self._szimulal(m, foto, hibaut)
            eredmeny = _mentes(foto, _UJ_SZIN)

        originals = foto.parent / ORIGINALS_DIR_NAME
        assert eredmeny.backup_created_now
        assert foto.read_bytes() != eredeti
        assert _ertek(foto.parent / _INI_NAME, "filters") is None
        assert _ertek(foto.parent / _INI_NAME, "backuphash") is not None
        assert _ertek(originals / _INI_NAME, "filters") == "enhance=1;"
        assert (originals / _NEV).read_bytes() == eredeti
        assert (originals / SNAPSHOT_DIR_NAME / "color_patches.1.jpg").read_bytes() == (
            eredeti
        )
        assert not (foto.parent / f"{_NEV}.jpg").exists()

    def test_a_visszavonas_a_mentes_elotti_allapotot_adja(self, foto, monkeypatch):
        eredeti = foto.read_bytes()
        with monkeypatch.context() as m:
            self._szimulal(m, foto, "csere-jelez-hibat")
            _mentes(foto, _UJ_SZIN)

        undo_save(foto)

        assert foto.read_bytes() == eredeti
        assert _ertek(foto.parent / _INI_NAME, "filters") == "enhance=1;"
        assert _ertek(foto.parent / _INI_NAME, "unknownfield") == "marad"

    @staticmethod
    def _ini_nem_irhato(m) -> None:
        def tele(*_args, **_kwargs):
            raise OSError(errno.ENOSPC, "No space left on device")

        m.setattr(ini_io, "write_atomic", tele)

    def test_ha_az_ini_sem_irhato_hangos_hiba_es_az_eredeti_marad(
        self, foto, monkeypatch
    ):
        eredeti = foto.read_bytes()

        with monkeypatch.context() as m:
            _kep_cserei(m, foto, _cserel_majd_hiba, _nem_cserel, _nem_cserel)
            self._ini_nem_irhato(m)
            with pytest.raises(SaveError, match="kétszer szerkesztettnek"):
                _mentes(foto, _UJ_SZIN)

        assert (foto.parent / ORIGINALS_DIR_NAME / _NEV).read_bytes() == eredeti

    def test_ha_az_ini_hibaja_utan_megis_visszairhato_minden_a_regi(
        self, foto, monkeypatch
    ):
        elotte = _fa(foto.parent)

        with monkeypatch.context() as m:
            self._szimulal(m, foto, "csere-jelez-hibat")
            self._ini_nem_irhato(m)
            with pytest.raises(OSError, match="No space left"):
                _mentes(foto, _UJ_SZIN)

        assert _fa(foto.parent) == elotte


class TestHaAKepNemOlvashato:
    def test_a_megorzott_eredeti_nem_torlodik(self, foto, monkeypatch):
        """Pl. a csere után leszakad a megosztás: nem dönthető el, mi történt."""
        eredeti = foto.read_bytes()

        def cserel_majd_eltunik(forras, cel, csere):
            csere(forras, cel)
            cel.unlink()
            raise _hiba()

        with monkeypatch.context() as m:
            _kep_cserei(m, foto, cserel_majd_eltunik)
            with pytest.raises(OSError, match="Input/output"):
                _mentes(foto, _UJ_SZIN)

        assert (foto.parent / ORIGINALS_DIR_NAME / _NEV).read_bytes() == eredeti
