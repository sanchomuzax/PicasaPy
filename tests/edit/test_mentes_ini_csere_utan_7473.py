"""#7473: ha egy ini már lecserélődött, és csak utána jön hiba, az is álljon vissza.

A visszagörgetés eddig csak a hiba nélkül visszatért írást tartotta számon. Ha
az írás a fájlt lecserélte, de utána dobott (pl. a könyvtár fsync-je), azt az
ini-t semmi nem írta vissza: a fő ininél eltűnt a `filters=` sor, az
eredeti-mappáé az új tartalmon maradt.

A hibát az `ioutil` fogantyúi (`_replace`, `_fsync_directory`) szimulálják: a
csere megtörténik, az utána következő könyvtár-fsync dob. Így a próbák mindkét
CI-lábon futnak. Ha a hiba a csere ELŐTT jön, azt a #7469 próbái fedik.
"""

from __future__ import annotations

import errno
from pathlib import Path

import cv2
import numpy as np
import pytest

import picasapy.edit.save as save_modul
import picasapy.ioutil as ioutil
from picasapy.app.save_error_kind import KIND_DISK, save_error_code, save_error_kind
from picasapy.edit import (
    ORIGINALS_DIR_NAME,
    EditSession,
    SaveError,
    revert,
    save_edited,
    undo_save,
)
from picasapy.ini import load_document, update_document

_INI_NAME = ".picasa.ini"
_NEV = "color_patches.jpg"
_INI = f"[{_NEV}]\nfilters=enhance=1;\nunknownfield=marad\n"
_HIBA = "Input/output error"

_INI_HELYEI = ("fo-ini", "eredeti-ini")


def _ini_ut(mappa: Path, hely: str) -> Path:
    return {
        "fo-ini": mappa / _INI_NAME,
        "eredeti-ini": mappa / ORIGINALS_DIR_NAME / _INI_NAME,
    }[hely]


def _kep(szin: tuple[int, int, int]) -> np.ndarray:
    kep = np.zeros((16, 16, 3), dtype=np.uint8)
    kep[:, :] = szin
    return kep


def _mentes(ut: Path, szin: tuple[int, int, int] = (200, 40, 40)) -> None:
    save_edited(ut, _kep(szin), EditSession.from_value("enhance=1;"))


def _fa(mappa: Path) -> dict[str, bytes | None]:
    """A mappa tartalma: út -> bájtok (mappánál `None`).

    Az ini-író `.bak` másolata kimarad: az minden ini-írás előtt készül.
    """
    return {
        p.relative_to(mappa).as_posix(): p.read_bytes() if p.is_file() else None
        for p in mappa.rglob("*")
        if p.suffix != ".bak"
    }


def _ertek(ini: Path, kulcs: str) -> str | None:
    szakasz = load_document(ini).section(_NEV)
    return szakasz.get(kulcs) if szakasz is not None else None


def _csere_utan_hiba(monkeypatch, cel: Path, kozben=lambda: None) -> None:
    """A `cel` következő cseréje megtörténik, az utána jövő könyvtár-fsync dob.

    Csak egyszer: a visszaíró csere már sikerül. A `kozben` a hiba előtt fut
    le (a párhuzamosan író program helye).
    """
    valodi_csere, valodi_fsync = ioutil._replace, ioutil._fsync_directory
    allapot = {"cserelt": False, "elsult": False}

    def csere(forras, hova):
        valodi_csere(forras, hova)
        if Path(hova) == cel and not allapot["elsult"]:
            allapot["cserelt"] = True

    def fsync(mappa):
        if allapot["cserelt"] and not allapot["elsult"]:
            allapot["elsult"] = True
            kozben()
            raise OSError(errno.EIO, _HIBA)
        valodi_fsync(mappa)

    monkeypatch.setattr(ioutil, "_replace", csere)
    monkeypatch.setattr(ioutil, "_fsync_directory", fsync)


def _elbukik(monkeypatch, cel: Path, muvelet, kozben=lambda: None) -> OSError:
    """Egy meghiúsult művelet; a szimuláció a végén visszaáll."""
    with monkeypatch.context() as m:
        _csere_utan_hiba(m, cel, kozben)
        with pytest.raises(OSError, match=_HIBA) as elkapott:
            muvelet()
    return elkapott.value


def _mentes_elbukik(monkeypatch, ut: Path, hely: str, kozben=lambda: None) -> OSError:
    return _elbukik(
        monkeypatch,
        _ini_ut(ut.parent, hely),
        lambda: _mentes(ut, (30, 200, 200)),
        kozben,
    )


def _uj_szerkesztes(ut: Path, lanc: str = "enhance=1;") -> None:
    """A felhasználó új szerkesztése: `filters=` kerül a fő ini-be."""
    update_document(
        ut.parent / _INI_NAME,
        lambda doc: doc.with_value(_NEV, "filters", lanc),
        touch=False,
    )


@pytest.fixture
def foto(tmp_path):
    ut = tmp_path / _NEV
    ok, kodolt = cv2.imencode(".jpg", _kep((10, 20, 30)))
    assert ok
    ut.write_bytes(kodolt.tobytes())
    (tmp_path / _INI_NAME).write_bytes(_INI.encode("utf-8"))
    return ut


@pytest.fixture
def mentett_foto(foto):
    """Egyszer már mentett kép, azóta új szerkesztéssel."""
    _mentes(foto)
    _uj_szerkesztes(foto)
    return foto


@pytest.mark.parametrize("hely", _INI_HELYEI)
class TestElsoMentes:
    def test_minden_a_mentes_elotti_marad_nyom_nelkul(self, foto, monkeypatch, hely):
        elotte = _fa(foto.parent)

        _mentes_elbukik(monkeypatch, foto, hely)

        assert _fa(foto.parent) == elotte
        assert not (foto.parent / ORIGINALS_DIR_NAME).exists()

    def test_a_visszavonas_nem_torol_szerkesztest(self, foto, monkeypatch, hely):
        elotte = _fa(foto.parent)
        _mentes_elbukik(monkeypatch, foto, hely)

        with pytest.raises(SaveError):
            undo_save(foto)

        assert _fa(foto.parent) == elotte

    def test_a_hibaablak_es_a_hibaszam_valtozatlan(self, foto, monkeypatch, hely):
        hiba = _mentes_elbukik(monkeypatch, foto, hely)

        assert hiba.errno == errno.EIO
        assert save_error_kind(hiba) == KIND_DISK
        assert save_error_code(hiba) == 2


@pytest.mark.parametrize("hely", _INI_HELYEI)
class TestIsmeteltMentes:
    def test_a_korabbi_mentes_es_az_uj_szerkesztes_allapota_marad(
        self, mentett_foto, monkeypatch, hely
    ):
        elotte = _fa(mentett_foto.parent)

        _mentes_elbukik(monkeypatch, mentett_foto, hely)

        assert _fa(mentett_foto.parent) == elotte

    def test_a_visszavonas_a_korabbi_sikeres_mentest_vonja_vissza(
        self, foto, monkeypatch, hely
    ):
        eredeti = foto.read_bytes()
        _mentes(foto)
        _uj_szerkesztes(foto)
        _mentes_elbukik(monkeypatch, foto, hely)

        undo_save(foto)

        assert foto.read_bytes() == eredeti
        assert _ertek(foto.parent / _INI_NAME, "filters") == "enhance=1;"

    def test_a_megorzott_eredeti_ideje_nem_valtozik(
        self, mentett_foto, monkeypatch, hely
    ):
        """Az eredeti-mappa ini-jének visszaírása nem érintheti meg."""
        monkeypatch.setenv("PICASAPY_TOUCH_PHOTO_MTIME", "1")
        megorzott = mentett_foto.parent / ORIGINALS_DIR_NAME / _NEV
        elotte = megorzott.stat().st_mtime_ns

        _mentes_elbukik(monkeypatch, mentett_foto, hely)

        assert megorzott.stat().st_mtime_ns == elotte


class TestKulsoValtozasKozben:
    """A csere és a hiba között más program is ír az ini-be: az ő sora marad."""

    @staticmethod
    def _hozzafuz(ini: Path, sor: bytes):
        return lambda: ini.write_bytes(ini.read_bytes() + sor)

    def test_a_fo_ininel(self, foto, monkeypatch):
        ini = foto.parent / _INI_NAME

        _mentes_elbukik(
            monkeypatch, foto, "fo-ini", self._hozzafuz(ini, b"star=yes\n")
        )

        assert _ertek(ini, "star") == "yes"
        assert _ertek(ini, "filters") == "enhance=1;"
        assert _ertek(ini, "unknownfield") == "marad"
        assert _ertek(ini, "backuphash") is None

    def test_az_eredeti_ininel(self, foto, monkeypatch):
        ini = _ini_ut(foto.parent, "eredeti-ini")

        _mentes_elbukik(
            monkeypatch, foto, "eredeti-ini", self._hozzafuz(ini, b"star=yes\r\n")
        )

        assert _ertek(ini, "star") == "yes"
        assert _ertek(ini, "filters") is None
        assert _ertek(ini, "moddate") is None
        assert (foto.parent / _INI_NAME).read_bytes() == _INI.encode("utf-8")

    def test_a_kulsoleg_atirt_kulcsot_nem_irjuk_felul(self, foto, monkeypatch):
        ini = foto.parent / _INI_NAME

        _mentes_elbukik(
            monkeypatch, foto, "fo-ini", self._hozzafuz(ini, b"filters=sepia=1;\n")
        )

        assert _ertek(ini, "filters") == "sepia=1;"
        assert _ertek(ini, "backuphash") is None

    def test_ha_az_ini_nem_olvashato_vissza_az_irasi_hiba_megy_tovabb(
        self, foto, monkeypatch
    ):
        """Az ellenőrzés hibája nem takarhatja el az eredeti hibát."""

        def nem_olvashato(_ut):
            raise PermissionError(errno.EACCES, "locked")

        hiba = _mentes_elbukik(
            monkeypatch,
            foto,
            "fo-ini",
            lambda: monkeypatch.setattr(save_modul, "load_or_empty", nem_olvashato),
        )

        assert hiba.errno == errno.EIO


@pytest.mark.parametrize("hely", _INI_HELYEI)
@pytest.mark.parametrize("muvelet", [undo_save, revert])
class TestVisszavonasEsVisszaallitas:
    """Ugyanez a visszagörgetés szolgálja a másik két mentés-műveletet is."""

    def test_a_mar_lecserelt_ini_is_visszaall(
        self, mentett_foto, monkeypatch, muvelet, hely
    ):
        _uj_szerkesztes(mentett_foto, "sepia=1;")
        elotte = _fa(mentett_foto.parent)

        _elbukik(
            monkeypatch,
            _ini_ut(mentett_foto.parent, hely),
            lambda: muvelet(mentett_foto),
        )

        assert _fa(mentett_foto.parent) == elotte
