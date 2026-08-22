"""A Mappakezelő fájában megjelennek a MEGHAJTÓK Windowson (#1206).

## A tulajdonos jelentése (v0.8.34, Windows), képpel

> „Mappakezelőben látszódjon a többi drive és hálózati mappa is."

A fa csak a felhasználói mappát mutatta: a `C:` és a többi meghajtó, meg a
hálózati helyek elérhetetlenek voltak.

## A lelet

A gyökér-lista LINUX-alapú volt — a függvény saját docstringje mondta ki
(„A Picasa-sorrendű fa-gyökerek **Linuxon**"): a `/` gyökér és a
`/media`, `/run/media` felsorolás Windowson értelmetlen, meghajtó-
felsorolás pedig egyáltalán nem volt.

## Az eredeti — bizonyíték a binárisból

| API | mire | hivatkozó |
|---|---|---|
| `KERNEL32.GetLogicalDrives` | a meghajtók felsorolása | `0x004fdd10`, `0x004fea70` |
| `KERNEL32.GetLogicalDriveStringsA` | ugyanaz, sztringként | `0x00510500` |
| `KERNEL32.GetDriveTypeA` | a meghajtó TÍPUSA | `0x004e2790` és 8 további |
| `MPR.WNetGetConnectionA` | a HÁLÓZATI meghajtó megosztás-neve | `0x00c06da6` |

⚠️ A hálózati helyek tehát **a betűjelükön át** jelennek meg, a megosztás
nevével — nem külön „hálózat" ágként.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.app import folder_tree_controller as ftc


def test_windowson_a_MEGHAJTOK_is_gyokerek(monkeypatch, tmp_path):
    """⚠️ A jegy magja: a `C:` és társai elérhetők legyenek."""
    monkeypatch.setattr(ftc, "_platform", lambda: "win32")
    monkeypatch.setattr(
        ftc, "_windows_meghajtok", lambda: [("C:", Path("C:/")), ("D:", Path("D:/"))]
    )

    gyokerek = ftc._root_entries(home=tmp_path, user="teszt")

    # ⚠️ A NEVET állítjuk, nem az útvonalat: linuxon a `Path("C:/")`
    # RELATÍVKÉNT oldódik fel (a futó könyvtár alá), tehát az útvonal-
    # összehasonlítás a tesztkörnyezetet mérné, nem a terméket.
    nevek = [bejegyzes["name"] for bejegyzes in gyokerek]
    assert "C:" in nevek, f"a C: meghajtó nincs a gyökerek között: {nevek}"
    assert "D:" in nevek


def test_windowson_NINCS_perjel_gyoker(monkeypatch, tmp_path):
    """A `/` gyökér Windowson értelmetlen — félrevezető sor volt."""
    monkeypatch.setattr(ftc, "_platform", lambda: "win32")
    monkeypatch.setattr(ftc, "_windows_meghajtok", lambda: [("C:", Path("C:/"))])

    gyokerek = ftc._root_entries(home=tmp_path, user="teszt")

    assert "/" not in [bejegyzes["name"] for bejegyzes in gyokerek]


def test_a_halozati_meghajto_a_MEGOSZTAS_nevet_kapja(monkeypatch, tmp_path):
    """`WNetGetConnection` — a betűjel mellett a megosztás neve látszik."""
    monkeypatch.setattr(ftc, "_platform", lambda: "win32")
    monkeypatch.setattr(
        ftc,
        "_windows_meghajtok",
        lambda: [("Z: (\\\\nas\\photo)", Path("Z:/"))],
    )

    gyokerek = ftc._root_entries(home=tmp_path, user="teszt")

    nevek = [bejegyzes["name"] for bejegyzes in gyokerek]
    assert any("nas" in nev for nev in nevek), (
        "a hálózati meghajtó neve nem tartalmazza a megosztást"
    )


def test_linuxon_valtozatlan(monkeypatch, tmp_path):
    """⚠️ A működő linuxos viselkedés nem romolhat el."""
    monkeypatch.setattr(ftc, "_platform", lambda: "linux")

    gyokerek = ftc._root_entries(home=tmp_path, user="teszt")

    assert "/" in [bejegyzes["name"] for bejegyzes in gyokerek]
