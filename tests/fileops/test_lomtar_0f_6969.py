"""A Lomtár `0x0f` eredménye külön ág, minden más hibakód hiba (#6969).

## Az eredeti - bizonyíték

A `0x005c9b00` a Lomtárba helyezést a Shell-művelettől kéri. Ha az
eredmény PONTOSAN `0x0f`, a `0x005fdb80` külön `Delete` / `Cancel` kérdést
nyit (`CThumbUI::ConfirmImmediateDeletion::Message`: „This file cannot be
moved to the Trash and will be deleted immediately. Are you sure you want
to continue?"), és jóváhagyásra a `0x009929b0` végleges törlést próbál.
Más hibakód NEM indít végleges törlést.

## Nálunk a javítás előtt

A `trash._windows_lomtarba` minden nem nulla `SHFileOperationW` eredményt
ugyanúgy `OSError`-ra fordított: a `0x0f` külön kérdése és a jóváhagyott
végleges törlés hiányzott.

## A teszt mércéje

⚠️ A Shell-hívás a modulszintű `trash._shfileoperation` fogantyún át van
cserélve (#1217/#1375), NEM a globális `ctypes.windll`-t írjuk át. A
platform a `trash._platform` fogantyún át van rögzítve.

⚠️ Kétirányú őr: a `0x0f` ág KÜLÖN kivételt ad, a többi hibakód viszont NEM
ezt - és egyik ág sem érintheti a fájlt, mert a végleges törlést csak a
felhasználó jóváhagyása indíthatja.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.fileops import photo_delete, trash

_FO_DELETE = 3
_FOF_ALLOWUNDO = 0x0040


class _Shell:
    """A `SHFileOperationW` helyettese: rögzíti a hívást, adott kódot ad."""

    def __init__(self, kod: int, megszakitva: bool = False) -> None:
        self.kod = kod
        self.megszakitva = megszakitva
        self.hivasok: list[tuple[int, int, str]] = []

    def __call__(self, muvelet) -> int:
        self.hivasok.append((muvelet.wFunc, muvelet.fFlags, muvelet.pFrom))
        muvelet.fAnyOperationsAborted = self.megszakitva
        return self.kod


@pytest.fixture
def windows(monkeypatch):
    """Windowsos platform + a Shell-hívás helyettesítője (kód utólag állítható)."""
    monkeypatch.setattr(trash, "_platform", lambda: "win32")

    def beallit(kod: int, megszakitva: bool = False) -> _Shell:
        shell = _Shell(kod, megszakitva)
        monkeypatch.setattr(trash, "_shfileoperation", shell)
        return shell

    return beallit


def _kep(tmp_path: Path) -> Path:
    kep = tmp_path / "kep.jpg"
    kep.write_bytes(b"tartalom")
    return kep


class TestAHibakodAgak:
    def test_a_0f_kod_kulon_kivetelt_ad(self, tmp_path, windows):
        shell = windows(0x0F)
        kep = _kep(tmp_path)

        with pytest.raises(trash.ImmediateDeletionNeededError) as hiba:
            trash.delete_to_trash(kep)

        assert isinstance(hiba.value, OSError), (
            "az OSError-szűrő hívók ne csússzanak el mellette némán"
        )
        assert kep.exists(), "a 0x0f ág NEM törölhet jóváhagyás nélkül"
        assert len(shell.hivasok) == 1

    @pytest.mark.parametrize("kod", [0x01, 0x02, 0x05, 0x0E, 0x10, 0x7C, 0x402])
    def test_minden_mas_hibakod_sima_hiba_es_nem_torol(
        self, tmp_path, windows, kod
    ):
        """Az eredeti csak a PONTOSAN `0x0f`-nél kérdez - a szomszédos
        értékek (`0x0e`, `0x10`) is hibák maradnak."""
        windows(kod)
        kep = _kep(tmp_path)

        with pytest.raises(OSError) as hiba:
            trash.delete_to_trash(kep)

        assert not isinstance(hiba.value, trash.ImmediateDeletionNeededError)
        assert kep.exists(), f"a {kod:#x} hibakód nem indíthat végleges törlést"

    def test_a_sikeres_lomtarazas_nem_dob(self, tmp_path, windows):
        shell = windows(0)
        kep = _kep(tmp_path)

        assert trash.delete_to_trash(kep) == kep

        assert len(shell.hivasok) == 1

    def test_a_megszakitott_muvelet_hiba_marad(self, tmp_path, windows):
        """Nulla kód + megszakítás jelző: ez NEM a 0x0f ág."""
        windows(0, megszakitva=True)
        kep = _kep(tmp_path)

        with pytest.raises(OSError) as hiba:
            trash.delete_to_trash(kep)

        assert not isinstance(hiba.value, trash.ImmediateDeletionNeededError)

    def test_a_hivas_a_lomtar_jelzoit_kuldi(self, tmp_path, windows):
        """A Lomtárba helyezés `FOF_ALLOWUNDO`-val megy: a 0x0f ág ettől
        különbözik a végleges törléstől."""
        shell = windows(0)

        trash.delete_to_trash(_kep(tmp_path))

        funkcio, jelzok, forras = shell.hivasok[0]
        assert funkcio == _FO_DELETE
        assert jelzok & _FOF_ALLOWUNDO
        assert forras.endswith("kep.jpg")


class TestAKepTorlesCsakJovahagyasra:
    def test_a_kep_lomtarazasa_a_0f_kivetelt_tovabbadja(self, tmp_path, windows):
        windows(0x0F)
        kep = _kep(tmp_path)

        with pytest.raises(trash.ImmediateDeletionNeededError):
            photo_delete.delete_photo_to_trash(kep)

        assert kep.exists()

    def test_jovahagyas_utan_a_vegleges_torles_tenyleg_torol(
        self, tmp_path, windows
    ):
        windows(0x0F)
        kep = _kep(tmp_path)
        with pytest.raises(trash.ImmediateDeletionNeededError):
            photo_delete.delete_photo_to_trash(kep)

        photo_delete.delete_photo_permanently(kep)

        assert not kep.exists()
