"""Hibanapló — „megnyitható napló, ne néma összeomlás" (#449).

A Picasa indulási adatbázis-hiba esetén nem omlott össze némán, és nem is
javított titokban: **felajánlotta a hibanaplót**.

    PicasaApp::DBError — „There were errors loading the Picasa database.
    Would you like to view the error log?"

Ez a modul a naplófájl oldala: egy `errorlog.txt` az alkalmazás
adatkönyvtárában, amibe a WARNING és súlyosabb üzenetek kerülnek. A
megjelenítést (a rendszer szövegszerkesztőjével) a hívó intézi.

**Miért csak WARNING-tól?** A napló akkor ér valamit, ha a felhasználó (és
a hibajelentés) rá tud nézni, és ott a HIBÁK vannak — nem egy több
tízezer soros nyomkövetés, amiben elvész a lényeg. A részletes
naplózáshoz a szokásos `PICASAPY_LOG_LEVEL` út marad.

**Méret-korlát:** a fájl indulásonként nem nő korlátlanul — ha a küszöb
fölé nőne, indításkor egyszer elforgatjuk (`errorlog.txt.1`). Két
generációnál többet nem tartunk: a régi hibák egy fotókezelőben nem érnek
annyit, hogy lemezt együnk velük.
"""

from __future__ import annotations

import logging
from pathlib import Path

#: A napló fájlneve — az eredeti `errorlog.txt` nevét követve.
ERROR_LOG_NAME = "errorlog.txt"

#: Efölött indításkor forgatunk (bájt).
MAX_LOG_BYTES = 512 * 1024

_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def error_log_path(data_dir: str | Path) -> Path:
    """A naplófájl útja az alkalmazás adatkönyvtárában."""
    return Path(data_dir) / ERROR_LOG_NAME


def rotate_if_large(path: Path, max_bytes: int = MAX_LOG_BYTES) -> None:
    """A túl nagyra nőtt naplót egyszer elforgatja (`…​.1`).

    Hibatűrő: ha a forgatás nem sikerül (jogosultság, zárolt fájl), a
    naplózás attól még elindul — a napló hiánya sosem akaszthatja meg a
    programot.
    """
    try:
        if path.exists() and path.stat().st_size > max_bytes:
            backup = path.with_suffix(path.suffix + ".1")
            backup.unlink(missing_ok=True)
            path.rename(backup)
    except OSError:
        return


def install_error_log(
    data_dir: str | Path, level: int = logging.WARNING
) -> Path | None:
    """A fájl-naplózó bekötése a gyökér-loggerre; a napló útja.

    `None`, ha a fájl nem nyitható meg (csak olvasható adatkönyvtár, teli
    lemez) — ilyenkor a program NAPLÓ NÉLKÜL, de működőképesen indul.
    """
    directory = Path(data_dir)
    path = error_log_path(directory)
    try:
        directory.mkdir(parents=True, exist_ok=True)
        rotate_if_large(path)
        handler = logging.FileHandler(path, encoding="utf-8")
    except OSError:
        return None
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_FORMAT))
    root = logging.getLogger()
    # a gyökér szintje ne legyen szigorúbb, mint a kezelőé — különben a
    # WARNING-ok el sem jutnának ide
    if root.level > level or root.level == logging.NOTSET:
        root.setLevel(level)
    root.addHandler(handler)
    return path


__all__ = [
    "ERROR_LOG_NAME",
    "MAX_LOG_BYTES",
    "error_log_path",
    "install_error_log",
    "rotate_if_large",
]
