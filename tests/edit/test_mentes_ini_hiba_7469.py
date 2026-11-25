"""#7469: ha az ini írása bukik el, a mentés visszavonása ne törölje a szerkesztéseket.

Ilyenkor a kép már le van cserélve, a #297 viszont visszagörgeti. A
pillanatkép eddig mégis ott maradt, és az utána indított „Utolsó mentés
visszavonása” törölte az ini `filters=` sorát, pedig mentés nem történt.

Az ini-hibát az `ini.io` írási fogantyúja (`write_atomic`), a visszagörgetés
hibáját az `ioutil` cseréje (`_replace`) szimulálja, ezért a próbák mindkét
CI-lábon futnak. A mentés két ini-t ír: a kép melletti `.picasa.ini`-t, majd
az eredeti-mappáét; mindkettőt célzottan buktatjuk el.
"""

from __future__ import annotations

import errno
from pathlib import Path

import cv2
import numpy as np
import pytest

import picasapy.ini.io as ini_io
import picasapy.ioutil as ioutil
from picasapy.app.save_error_kind import KIND_DISK, save_error_code, save_error_kind
from picasapy.edit import (
    ORIGINALS_DIR_NAME,
    SNAPSHOT_DIR_NAME,
    EditSession,
    SaveError,
    save_edited,
    undo_save,
)

_INI_NAME = ".picasa.ini"
_NEV = "color_patches.jpg"
_INI = f"[{_NEV}]\nfilters=enhance=1;\nunknownfield=marad\n"

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


def _eredeti_mappa(mappa: Path) -> dict[str, bytes | None]:
    """A `.picasaoriginals` tartalma: út -> bájtok (mappánál `None`).

    Az ini-író `.bak` másolata kimarad: az minden ini-írás előtt készül, és
    nem része a mentés visszavonásának.
    """
    originals = mappa / ORIGINALS_DIR_NAME
    return {
        p.relative_to(originals).as_posix(): p.read_bytes() if p.is_file() else None
        for p in originals.rglob("*")
        if p.suffix != ".bak"
    }


def _ini_irasok_elbuknak(monkeypatch, cel: Path, *, ennyi_utan: int = 0) -> None:
    """A `cel` ini írása `OSError`-t dob (az első `ennyi_utan` még sikerül)."""
    valodi = ini_io.write_atomic
    sikeres = [0]

    def iro(target, payload, **kwargs):
        if Path(target) == cel:
            if sikeres[0] >= ennyi_utan:
                raise OSError(errno.ENOSPC, "No space left on device")
            sikeres[0] += 1
        return valodi(target, payload, **kwargs)

    monkeypatch.setattr(ini_io, "write_atomic", iro)


def _visszagorgeto_csere(monkeypatch, kep: Path, viselkedes) -> None:
    """A kép MÁSODIK cseréje (a visszagörgetés) helyett `viselkedes` fut.

    `viselkedes(valodi_csere)` dönti el, megtörténik-e a csere, és mi lesz
    utána.
    """
    valodi = ioutil._replace
    cserek = [0]

    def csere(forras, hova):
        if Path(hova) != kep:
            return valodi(forras, hova)
        cserek[0] += 1
        if cserek[0] == 1:
            return valodi(forras, hova)
        return viselkedes(lambda: valodi(forras, hova))

    monkeypatch.setattr(ioutil, "_replace", csere)


def _nem_cserel(_csere) -> None:
    raise OSError(errno.EIO, "a visszagorgetes nem sikerult")


def _cserel_de_hibat_jelez(csere) -> None:
    csere()
    raise OSError(errno.EIO, "a visszagorgetes nem igazolhato")


def _mentes_elbukik(
    monkeypatch, ut: Path, hely: str, hibatipus=OSError
) -> BaseException:
    """Egy meghiúsult mentés; a szimuláció a végén visszaáll."""
    with monkeypatch.context() as m:
        _ini_irasok_elbuknak(m, _ini_ut(ut.parent, hely))
        with pytest.raises(hibatipus) as elkapott:
            _mentes(ut, (30, 200, 200))
    return elkapott.value


@pytest.fixture
def foto(tmp_path):
    ut = tmp_path / _NEV
    ok, kodolt = cv2.imencode(".jpg", _kep((10, 20, 30)))
    assert ok
    ut.write_bytes(kodolt.tobytes())
    (tmp_path / _INI_NAME).write_bytes(_INI.encode("utf-8"))
    return ut


@pytest.mark.parametrize("hely", _INI_HELYEI)
class TestElsoMentes:
    def test_a_kep_es_az_ini_bajtra_a_mentes_elotti_nyom_nem_marad(
        self, foto, monkeypatch, hely
    ):
        eredeti = foto.read_bytes()

        _mentes_elbukik(monkeypatch, foto, hely)

        assert foto.read_bytes() == eredeti
        assert (foto.parent / _INI_NAME).read_bytes() == _INI.encode("utf-8")
        assert not (foto.parent / ORIGINALS_DIR_NAME).exists()

    def test_a_visszavonas_nem_torli_a_filters_sort(self, foto, monkeypatch, hely):
        _mentes_elbukik(monkeypatch, foto, hely)

        with pytest.raises(SaveError):
            undo_save(foto)

        assert (foto.parent / _INI_NAME).read_bytes() == _INI.encode("utf-8")

    def test_a_hibaablak_es_a_hibaszam_valtozatlan(self, foto, monkeypatch, hely):
        hiba = _mentes_elbukik(monkeypatch, foto, hely)

        assert hiba.errno == errno.ENOSPC
        assert save_error_kind(hiba) == KIND_DISK
        assert save_error_code(hiba) == 2


@pytest.mark.parametrize("hely", _INI_HELYEI)
class TestIsmeteltMentes:
    def test_a_korabbi_mentes_allapota_marad(self, foto, monkeypatch, hely):
        _mentes(foto)
        mentett = foto.read_bytes()
        ini = (foto.parent / _INI_NAME).read_bytes()
        eredeti_mappa = _eredeti_mappa(foto.parent)

        _mentes_elbukik(monkeypatch, foto, hely)

        assert foto.read_bytes() == mentett
        assert (foto.parent / _INI_NAME).read_bytes() == ini
        assert _eredeti_mappa(foto.parent) == eredeti_mappa

    def test_a_visszavonas_a_korabbi_sikeres_mentest_vonja_vissza(
        self, foto, monkeypatch, hely
    ):
        eredeti = foto.read_bytes()
        _mentes(foto)
        _mentes_elbukik(monkeypatch, foto, hely)

        undo_save(foto)

        assert foto.read_bytes() == eredeti
        ini = (foto.parent / _INI_NAME).read_text(encoding="utf-8")
        assert "filters=enhance=1;" in ini


class TestAmikorAMasolatMegmarad:
    """Ha a kép visszagörgetése nem igazolt, a másolat az eredeti példánya."""

    @pytest.mark.parametrize("hely", _INI_HELYEI)
    @pytest.mark.parametrize("viselkedes", [_nem_cserel, _cserel_de_hibat_jelez])
    def test_elbukott_visszagorgetesnel(self, foto, monkeypatch, hely, viselkedes):
        eredeti = foto.read_bytes()
        _visszagorgeto_csere(monkeypatch, foto, viselkedes)

        hiba = _mentes_elbukik(monkeypatch, foto, hely, SaveError)

        originals = foto.parent / ORIGINALS_DIR_NAME
        assert str(foto) in str(hiba)
        assert (originals / _NEV).read_bytes() == eredeti
        assert (originals / SNAPSHOT_DIR_NAME / "color_patches.1.jpg").read_bytes() == (
            eredeti
        )

    def test_ha_a_visszagorgetett_kep_nem_olvashato(self, foto, monkeypatch):
        """Pl. leszakadt megosztás: a csere lefutott, de a kép nincs meg."""
        eredeti = foto.read_bytes()

        def eltunik(csere):
            csere()
            foto.unlink()

        _visszagorgeto_csere(monkeypatch, foto, eltunik)

        hiba = _mentes_elbukik(monkeypatch, foto, "fo-ini")

        assert hiba.errno == errno.ENOSPC
        assert (foto.parent / ORIGINALS_DIR_NAME / _NEV).read_bytes() == eredeti


class TestElbukottIniVisszagorgetes:
    def test_visszaallt_kepnel_a_nyom_torlodik_a_hibauzenet_marad(
        self, foto, monkeypatch
    ):
        """A fő ini visszaírása is elbukik, a képé sikerül: a másolatok a
        mostani képpel azonosak, a „visszavonás” nem futhat rájuk."""
        eredeti = foto.read_bytes()
        _ini_irasok_elbuknak(monkeypatch, _ini_ut(foto.parent, "eredeti-ini"))
        _ini_irasok_elbuknak(
            monkeypatch, _ini_ut(foto.parent, "fo-ini"), ennyi_utan=1
        )

        with pytest.raises(SaveError, match="teljes visszaállítása sem sikerült"):
            _mentes(foto)

        assert foto.read_bytes() == eredeti
        assert not (foto.parent / ORIGINALS_DIR_NAME).exists()
