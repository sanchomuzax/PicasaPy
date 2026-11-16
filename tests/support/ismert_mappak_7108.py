"""Hamis felhasználói profil az ismert mappák (#7108) teszteléséhez.

A `picasapy.fileops.known_folders` a Qt szabványos útvonalait a modul
fogantyúin át kérdezi (#1217, #1375). Ez a segéd ezeket cseréli egy hívó
által megadott mappakészletre, hogy a teszt ne függjön a gép valódi
profiljától, és ne a globális `QStandardPaths`-t írja át.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QStandardPaths

from picasapy.fileops import known_folders

_HELY = QStandardPaths.StandardLocation

#: A teszt-profil mappanevei; a kulcs a mappa szerepe az eredeti táblában.
ISMERT_NEVEK = (
    "Pictures",
    "Desktop",
    "Music",
    "Movies",
    "Documents",
    "Local",
    "Roaming",
    "ProgramData",
)


def profil_utak(gyoker: Path) -> dict[str, Path]:
    """A hamis profil mappái a `gyoker` alatt (a mappákat nem hozza létre)."""
    return {nev: gyoker / nev for nev in ISMERT_NEVEK}


def kiegyenesit(monkeypatch, utak: dict[str, Path]) -> None:
    """A `known_folders` fogantyúit a `utak` készletére téríti."""
    irhato = {
        _HELY.PicturesLocation: utak["Pictures"],
        _HELY.DesktopLocation: utak["Desktop"],
        _HELY.MusicLocation: utak["Music"],
        _HELY.MoviesLocation: utak["Movies"],
        _HELY.DocumentsLocation: utak["Documents"],
        _HELY.GenericDataLocation: utak["Local"],
        # a Qt az alkalmazásadat-útvonalhoz hozzáfűzi a szervezet/alkalmazás nevét
        _HELY.AppDataLocation: utak["Roaming"] / "Szervezet" / "Alkalmazas",
    }
    osszes = {_HELY.GenericDataLocation: [utak["Local"], utak["ProgramData"]]}
    monkeypatch.setattr(
        known_folders, "_writable_location", lambda hely: str(irhato.get(hely, ""))
    )
    monkeypatch.setattr(
        known_folders,
        "_standard_locations",
        lambda hely: [str(ut) for ut in osszes.get(hely, ())],
    )
    monkeypatch.setattr(
        known_folders, "_alkalmazas_nevek", lambda: ("Szervezet", "Alkalmazas")
    )
