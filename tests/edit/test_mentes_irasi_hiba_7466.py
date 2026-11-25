"""#7466: a csere előtti írási hiba (pl. tele lemez) után se maradjon mentés-nyom.

A #7462 csak a csere hibájánál takarított. Ha már az írás bukott el, a
`.picasaoriginals`-másolat és a pillanatkép ott maradt, és az utána indított
„Utolsó mentés visszavonása” törölte az ini `filters=` sorát.

A tele lemezt az `ioutil` írási fogantyúja szimulálja (`_fdopen`), ezért a
próbák mindkét CI-lábon futnak. A mentés három helyre ír a csere előtt:
eredeti-másolat, pillanatkép, kép; mindegyiket célzottan buktatjuk el.
"""

from __future__ import annotations

import errno
from pathlib import Path

import cv2
import numpy as np
import pytest

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

_ELSO_MENTES_HELYEI = ("eredeti-masolat", "pillanatkep", "kep")
#: ismételt mentésnél az eredeti-másolat már megvan, oda nincs írás
_ISMETELT_MENTES_HELYEI = ("pillanatkep", "kep")


def _hely(mappa: Path, nev: str) -> Path:
    originals = mappa / ORIGINALS_DIR_NAME
    return {
        "eredeti-masolat": originals,
        "pillanatkep": originals / SNAPSHOT_DIR_NAME,
        "kep": mappa,
    }[nev]


def _kep(szin: tuple[int, int, int]) -> np.ndarray:
    kep = np.zeros((16, 16, 3), dtype=np.uint8)
    kep[:, :] = szin
    return kep


def _mentes(ut: Path, szin: tuple[int, int, int] = (200, 40, 40)) -> None:
    save_edited(ut, _kep(szin), EditSession.from_value("enhance=1;"))


def _fa(mappa: Path) -> dict[str, bytes | None]:
    """A mappa teljes tartalma: út -> bájtok (mappánál `None`)."""
    return {
        p.relative_to(mappa).as_posix(): p.read_bytes() if p.is_file() else None
        for p in mappa.rglob("*")
    }


class _HibasFogantyu:
    """Megnyitott fájl, amelynek az írása a megadott hibát dobja."""

    def __init__(self, fogantyu, hiba: OSError, elotte) -> None:
        self._fogantyu = fogantyu
        self._hiba = hiba
        self._elotte = elotte

    def __enter__(self):
        return self

    def __exit__(self, *_kivetel) -> None:
        self._fogantyu.close()

    def write(self, _adat) -> int:
        self._elotte()
        raise self._hiba


def _iras_elbukik(
    monkeypatch, mappa: Path, hiba: OSError | None = None, elotte=lambda: None
) -> None:
    """A `mappa`-ba szánt ideiglenes fájl írása bukik el, minden más megy."""
    hiba = hiba or OSError(errno.ENOSPC, "No space left on device")
    valodi_temp = ioutil._mkstemp
    valodi_fdopen = ioutil._fdopen
    celzott: set[int] = set()

    def temp(**kwargs):
        fd, nev = valodi_temp(**kwargs)
        if Path(kwargs["dir"]) == mappa:
            celzott.add(fd)
        return fd, nev

    def fdopen(fd, mod):
        fogantyu = valodi_fdopen(fd, mod)
        if fd not in celzott:
            return fogantyu
        celzott.discard(fd)
        return _HibasFogantyu(fogantyu, hiba, elotte)

    monkeypatch.setattr(ioutil, "_mkstemp", temp)
    monkeypatch.setattr(ioutil, "_fdopen", fdopen)


def _mentes_elbukik(
    monkeypatch, ut: Path, hely: str, hiba: OSError | None = None
) -> OSError:
    """Egy meghiúsult mentés; a szimuláció a végén visszaáll."""
    with monkeypatch.context() as m:
        _iras_elbukik(m, _hely(ut.parent, hely), hiba)
        with pytest.raises(OSError) as elkapott:
            _mentes(ut, (30, 200, 200))
    return elkapott.value


@pytest.fixture
def foto(tmp_path):
    ut = tmp_path / _NEV
    ok, kodolt = cv2.imencode(".jpg", _kep((10, 20, 30)))
    assert ok
    ut.write_bytes(kodolt.tobytes())
    (tmp_path / _INI_NAME).write_text(_INI, encoding="utf-8")
    return ut


class TestElsoMentes:
    @pytest.mark.parametrize("hely", _ELSO_MENTES_HELYEI)
    def test_a_mappa_bajtra_valtozatlan_es_nyom_nem_marad(
        self, foto, monkeypatch, hely
    ):
        elotte = _fa(foto.parent)

        hiba = _mentes_elbukik(monkeypatch, foto, hely)

        assert hiba.errno == errno.ENOSPC
        assert _fa(foto.parent) == elotte

    def test_a_hibaablak_tele_lemeznel_hiba_2(self, foto, monkeypatch):
        hiba = _mentes_elbukik(monkeypatch, foto, "kep")

        assert save_error_kind(hiba) == KIND_DISK
        assert save_error_code(hiba) == 2

    def test_a_39_es_windows_kod_hiba_12_marad(self, foto, monkeypatch):
        tele = OSError(errno.ENOSPC, "The disk is full")
        tele.winerror = 39  # Linuxon a konstruktor nem veszi át
        elotte = _fa(foto.parent)

        hiba = _mentes_elbukik(monkeypatch, foto, "kep", tele)

        assert save_error_code(hiba) == 12
        assert _fa(foto.parent) == elotte

    @pytest.mark.parametrize("hely", _ELSO_MENTES_HELYEI)
    def test_a_visszavonas_nem_torli_a_filters_sort(self, foto, monkeypatch, hely):
        _mentes_elbukik(monkeypatch, foto, hely)
        elotte = _fa(foto.parent)

        with pytest.raises(SaveError):
            undo_save(foto)

        assert _fa(foto.parent) == elotte
        assert "filters=enhance=1;" in (foto.parent / _INI_NAME).read_text(encoding="utf-8")


class TestIsmeteltMentes:
    @pytest.mark.parametrize("hely", _ISMETELT_MENTES_HELYEI)
    def test_a_korabbi_mentes_eredetije_es_pillanatkepe_megmarad(
        self, foto, monkeypatch, hely
    ):
        _mentes(foto)
        elotte = _fa(foto.parent)

        _mentes_elbukik(monkeypatch, foto, hely)

        assert _fa(foto.parent) == elotte

    @pytest.mark.parametrize("hely", _ISMETELT_MENTES_HELYEI)
    def test_a_visszavonas_a_korabbi_sikeres_mentest_vonja_vissza(
        self, foto, monkeypatch, hely
    ):
        eredeti = foto.read_bytes()
        _mentes(foto)
        _mentes_elbukik(monkeypatch, foto, hely)

        undo_save(foto)

        assert foto.read_bytes() == eredeti
        assert "filters=enhance=1;" in (foto.parent / _INI_NAME).read_text(encoding="utf-8")


class TestAmikorAMasolatNemTorolheto:
    """A takarítás csak addig jogos, amíg a kép bizonyíthatóan változatlan."""

    def test_olvashatatlan_kepnel_a_masolat_marad_es_az_irasi_hiba_megy_tovabb(
        self, foto, monkeypatch
    ):
        """Ha a kép az írási hiba közben eltűnik (pl. leszakadt megosztás),
        a másolat lehet az egyetlen példány."""
        eredeti = foto.read_bytes()
        _iras_elbukik(monkeypatch, foto.parent, elotte=foto.unlink)

        with pytest.raises(OSError, match="No space left"):
            _mentes(foto)

        assert (foto.parent / ORIGINALS_DIR_NAME / _NEV).read_bytes() == eredeti
