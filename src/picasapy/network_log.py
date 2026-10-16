"""Hálózati napló: a Beállítások ▸ Hálózat fül naplózási szintje (#5145).

Az eredeti options.fen „Network” fülén a `loglevel` legördülő öt szintet kínál,
a kiválasztott szint a `LogLevel` kulcsba (Preferences csoport) kerül, az
alapértéke 2. A naplófájl az eredetiben `network.log` néven készül az
adatkönyvtárban; a FEN-ben ehhez csak egy `pathbox` van, tallózó nincs, ezért a
PicasaPy-ban a helye is rögzített.

Szintek (docs/specs/picasa-fen-dialogs.md, „Network fül - naplózás"):
  0  nincs napló
  1  a hibák
  2  HTTP-összefoglaló (alapérték)
  3  fejlécek és átirányítás
  4  a válasz mérete

Eltérés az eredetitől: a nem képi válasz TARTALMÁT nem írjuk ki. A letöltött
modell bináris fájl (az SFace közel 38 MB), a tartalma a naplóban nem segít.

A naplózó a gyökér-loggerre NEM propagál, így a hibanaplót (errorlog.txt) nem
bővíti. A `configure()` futás közben is hívható: a szint a beállításból jön, a
fájl helyét a controller adja át.
"""

from __future__ import annotations

import logging
from pathlib import Path

NAPLO_NEV = "picasapy.network"
NAPLO_FAJLNEV = "network.log"

LEVEL_MIN = 0
LEVEL_MAX = 4
DEFAULT_LEVEL = 2

_logger = logging.getLogger(NAPLO_NEV)
_logger.setLevel(logging.INFO)
_logger.propagate = False

_szint = DEFAULT_LEVEL
_kezelo: logging.Handler | None = None


def clamp_level(value: int) -> int:
    """A szintet a 0-4 tartományba szorítja."""
    return max(LEVEL_MIN, min(LEVEL_MAX, int(value)))


def read_level(value: object) -> int:
    """A tárolt értékből szint lesz; hibás vagy hiányzó érték az alapérték."""
    if value is None or isinstance(value, bool):
        return DEFAULT_LEVEL
    try:
        szint = int(str(value).strip())
    except ValueError:
        return DEFAULT_LEVEL
    return clamp_level(szint)


def configure(level: int, path: Path | None) -> None:
    """Beállítja a szintet és a naplófájlt; a korábbi fájlkezelőt lecseréli.

    0-s szinten, vagy ha nincs útvonal, nem nyit fájlt. A fájl az első
    bejegyzéskor jön létre; ha a mappája nem hozható létre, a napló kimarad, de
    a letöltés attól még működik.
    """
    global _szint, _kezelo
    _szint = clamp_level(level)
    if _kezelo is not None:
        _logger.removeHandler(_kezelo)
        _kezelo.close()
        _kezelo = None
    if _szint == LEVEL_MIN or path is None:
        return
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        kezelo = logging.FileHandler(path, encoding="utf-8", delay=True)
    except OSError:
        return
    kezelo.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _logger.addHandler(kezelo)
    _kezelo = kezelo


def log_failure(url: str, hiba: BaseException) -> None:
    """1-es szinttől: a sikertelen kérés hibája."""
    if _szint >= 1:
        _logger.info("Error: %s (%s)", hiba, url)


def log_response(url: str, valasz) -> None:
    """2-es szinttől az összefoglaló; 3-astól a fejlécek és az átirányítás."""
    if _szint < 2:
        return
    _logger.info("Stream summary: GET request: %s (%d)", url, valasz.status)
    if _szint < 3:
        return
    veglegesen = valasz.geturl()
    if veglegesen != url:
        _logger.info("Redirected to URL: %s", veglegesen)
    for nev, ertek in valasz.headers.items():
        _logger.info("Header: %s: %s", nev, ertek)


def log_size(url: str, meret: int) -> None:
    """4-es szinttől a letöltött válasz mérete."""
    if _szint >= 4:
        _logger.info("Response size: %d bytes (%s)", meret, url)
