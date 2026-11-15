"""#7044 / #7045: a hálózati (UNC) mappaút normalizálása nem ér hálózatot, és a
kis-nagybetű-érzéketlen összehasonlítás ugyanazt a mappát adja.

## A hiba

A `normalize_path` `Path.resolve()`-ot hívott, ami Windowson UNC-úton minden
útvonal-komponensre hálózati körülfordulás (elérhetetlen NAS-nál 20-40 s). Az
indulás ezt a fő szálon, mappánként ismételte (`_dedupe_roots`,
`merge_duplicate_folders`, `_find_root`), ezért a program percekig állt. A
feloldás ráadásul MÁS kis-nagybetűs alakot adhat (`\\\\ds215j\\...`), mint amit
a felhasználó felvett (`\\\\DS215j\\...`), és a két alak az indexben két sor lett.

## A rögzítés módja

A Windows-viselkedést a `paths._platform` fogantyúval rögzítjük (#1217), a
lassú hálózatot pedig a `paths._feloldas` fogantyúval: a megfigyelt
névrészletet tartalmazó útvonalon a feloldás vár és nyilvántartja a szálat."""

from __future__ import annotations

import threading
import time

import pytest

from picasapy import paths

#: a szimulált szerver neve; a teszt-függvények neve SZÁNDÉKOSAN nem tartalmazza
SZERVER = "ds215j"
EREDETI = r"\\DS215j\photo\2026\2026-11-14"
KISBETUS = r"\\ds215j\photo\2026\2026-11-14"


@pytest.fixture
def windows(monkeypatch):
    monkeypatch.setattr(paths, "_platform", lambda: "win32")


@pytest.fixture
def lassu_halozat(monkeypatch):
    """A szervert érintő fájlrendszeri feloldás 0,4 s-ot vár; a hívó szálakat gyűjti."""
    hivasok: list[int] = []
    eredeti = paths._feloldas

    def lassu(szoveg):
        if SZERVER in szoveg.lower():
            hivasok.append(threading.get_ident())
            time.sleep(0.4)
        return eredeti(szoveg)

    monkeypatch.setattr(paths, "_feloldas", lassu)
    return hivasok


def test_a_halozati_ut_normalizalasa_nem_er_halozatot(windows, lassu_halozat):
    kezdet = time.monotonic()
    paths.normalize_path(EREDETI)
    paths.path_key(KISBETUS)
    eltelt = time.monotonic() - kezdet
    assert lassu_halozat == [], "a normalizálás hálózati stat-ot hívott"
    assert eltelt < 0.2, f"a normalizálás {eltelt:.2f} s-ig várt a hálózatra"


def test_a_halozati_ut_alakja_a_megadott_kis_nagybetut_megorzi(windows):
    assert paths.normalize_path(EREDETI) == EREDETI
    assert paths.normalize_path(r"\\DS215j\photo\2026\..\2026\2026-11-14") == EREDETI


def test_az_elore_perjeles_halozati_ut_visszaperjeles_lesz_windowson(windows):
    assert paths.normalize_path("//DS215j/photo/2026/2026-11-14/") == EREDETI


def test_a_ket_kis_nagybetus_alak_ugyanazt_a_kulcsot_adja_windowson(windows):
    assert paths.path_key(EREDETI) == paths.path_key(KISBETUS)
    assert paths.path_key(EREDETI) != paths.path_key(r"\\DS215j\photo\2026\2026-11-15")


def test_a_kulcs_a_ket_elvalasztot_is_egynek_veszi_windowson(windows):
    assert paths.path_key(EREDETI) == paths.path_key("//ds215j/photo/2026/2026-11-14")


def test_posixon_a_kis_nagybetu_valodi_kulonbseg(monkeypatch):
    monkeypatch.setattr(paths, "_platform", lambda: "linux")
    assert paths.path_key("/mnt/nas/Photo") != paths.path_key("/mnt/nas/photo")


def test_posixon_a_dupla_perjeles_ut_nem_lesz_halozati_ut(monkeypatch):
    """Linuxon a `//mnt/nas` a `/mnt/nas`: a hálózati ág nem nyúlhat hozzá."""
    monkeypatch.setattr(paths, "_platform", lambda: "linux")
    assert "\\" not in paths.normalize_path("//mnt/nas/kepek")


def test_a_helyi_windowsos_ut_tovabbra_a_feloldas_utjan_megy(monkeypatch, tmp_path):
    """Nem hálózati útvonalra a `resolve()` (szimbolikus link, `..`) marad."""
    monkeypatch.setattr(paths, "_platform", lambda: "win32")
    cel = tmp_path / "cel"
    cel.mkdir()
    assert paths.normalize_path(tmp_path / "a" / ".." / "cel") == str(cel.resolve())
