"""Windowson a rendszer LOMTÁRÁBA töröljünk, ne egy rejtett mappába (#1182).

## A tulajdonos jelentése (v0.8.34, Windows)

> „Az előbb a kép törlésre került a lemezen is. Azonban nem került a
> kukába, nem találom ott. Hiába azt választottam."

## A lelet

A `trash.py` teljes egészében a **freedesktop.org Trash-specifikációra**
épül (`$XDG_DATA_HOME/Trash`, `files/` + `info/` páros, `$topdir/.Trash-$uid`)
— ez **linuxos szabvány**. Windowson emiatt a fájl egy rejtett mappába
kerül, amiről a Lomtár nem tud: a felhasználó számára **eltűnik, és nem
állítható vissza**.

## Az eredeti — bizonyíték

A `Picasa3.exe` a **`SHELL32.DLL` → `SHFileOperationW`** függvényt
importálja (`referencia/binary-index/imports.csv:11282`, cím `0x009b1d50`
/ `0x005b1d50`). Ez a Windows shell fájlművelet-API-ja; a Lomtárba
helyezést a `FOF_ALLOWUNDO` jelző adja.

⚠️ Ez a teszt **nem a Win32-hívást** méri (linuxon nem is lehetne), hanem
azt, hogy a platformválasztás megtörténik-e: windowsos platformon NEM a
freedesktop-ág fusson.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.fileops import trash


def test_windowson_NEM_a_freedesktop_agat_hasznaljuk(tmp_path, monkeypatch):
    """⚠️ A jegy magja: Windowson a rendszer Lomtára a cél.

    A freedesktop-ág `files/` + `info/` párost hoz létre — ha ez fut le
    Windowson, a fájl egy rejtett mappába kerül, és a Lomtárban nem
    található meg."""
    kep = tmp_path / "kep.jpg"
    kep.write_bytes(b"tartalom")

    hivasok: list[Path] = []
    monkeypatch.setattr(trash, "_platform", lambda: "win32")
    monkeypatch.setattr(
        trash, "_windows_lomtarba", lambda p: hivasok.append(Path(p))
    )

    trash.delete_to_trash(kep)

    assert hivasok == [kep], (
        "windowsos platformon a rendszer Lomtárát hívó ágnak kell futnia"
    )


def test_linuxon_valtozatlan_a_freedesktop_ag(tmp_path, monkeypatch):
    """⚠️ A meglévő, működő viselkedés nem romolhat el."""
    monkeypatch.setattr(trash, "_platform", lambda: "linux")
    kuka = tmp_path / "kuka"
    kep = tmp_path / "kep.jpg"
    kep.write_bytes(b"tartalom")

    cel = trash.delete_to_trash(kep, trash_dir=kuka)

    assert cel.parent == kuka / "files"
    assert (kuka / "info" / "kep.jpg.trashinfo").exists()
    assert not kep.exists()


def test_a_windowsos_ag_hibaja_NEM_nema(tmp_path, monkeypatch):
    """Ha a Lomtárba helyezés nem megy, a hívó tudjon róla.

    ⚠️ A néma elnyelés itt ADATVESZTÉS: a felhasználó azt hinné, a fájl a
    Lomtárban van, holott sehol."""
    kep = tmp_path / "kep.jpg"
    kep.write_bytes(b"tartalom")

    def robban(_p):
        raise OSError("a shell művelet elbukott")

    monkeypatch.setattr(trash, "_platform", lambda: "win32")
    monkeypatch.setattr(trash, "_windows_lomtarba", robban)

    with pytest.raises(OSError):
        trash.delete_to_trash(kep)


def test_windowson_VAN_lomtar(tmp_path, monkeypatch):
    """A `trash_available` Windowson IGAZAT adjon.

    ⚠️ Ez dönti el, mit kérdez a program a felhasználótól: ha hamisat ad,
    a `deleteConfirmDialog` a VÉGLEGES törlés ágára megy (#457), és a
    felhasználó azt a szöveget kapja, hogy nincs visszaút — holott a
    Windows Lomtára létezik és működik.

    A linuxos `find_trash_dir` Windowson értelmetlen: `$XDG_DATA_HOME`-ot
    és mount-specifikus `.Trash-$uid` mappát keres.

    ⚠️ A teszt SZÁNDÉKOSAN elveszi a freedesktop-lomtárat
    (`find_trash_dir` → None). Enélkül a linuxos fejlesztői gépen a
    `$XDG_DATA_HOME/Trash` VÉLETLENÜL megtalálódna, és a teszt zöld lenne
    a javítás nélkül is — hamis biztonság.
    """
    monkeypatch.setattr(trash, "_platform", lambda: "win32")
    monkeypatch.setattr(trash, "find_trash_dir", lambda *a, **k: None)
    kep = tmp_path / "kep.jpg"
    kep.write_bytes(b"tartalom")

    assert trash.trash_available(kep) is True
