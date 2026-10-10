"""A „Társítás…" (Open With) párbeszéd háttere (#4533).

Az eredeti Picasa a Windows héjára bízta a „Megnyitás ezzel" listát: a
fájltípushoz társított alkalmazásokat a rendszer adta. Windowson mi is ezt a
héj-párbeszédet nyitjuk meg (`OpenAs_RunDLL`). Linuxon nincs ilyen héj, ezért
a freedesktop-szabványt követjük:

- a MIME-típushoz tartozó alkalmazásokat a `mimeapps.list` (felhasználói és
  rendszerszintű) és a `mimeinfo.cache` adja, ebben a sorrendben;
- a nevet és az indító parancsot a `.desktop` fájlból vesszük;
- `NoDisplay=true` és `Hidden=true` bejegyzés nem jelenik meg.

macOS-en nincs egységes lista, ott a választó üres marad.
"""

from __future__ import annotations

import configparser
import logging
import mimetypes
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_log = logging.getLogger(__name__)

#: A `Exec=` sorban a fájlt jelölő mezőkódok: ezek helyére a fájl útvonala kerül.
_FAJL_KODOK = frozenset({"%f", "%F", "%u", "%U"})

#: Minden más `%x` kód a parancsból kimarad; a `%%` egy valódi `%`.
_KOD_MINTA = re.compile(r"%[a-zA-Z%]")

_MIME_SZAKASZOK = ("Default Applications", "Added Associations")

#: Modulszintű fogantyú az indításhoz — a teszt ezt cseréli, nem a globális
#: `subprocess.Popen`-t (#1375).
_popen = subprocess.Popen


@dataclass(frozen=True)
class OpenWithApp:
    """Egy társított alkalmazás a választóban: azonosító, név, indító parancs."""

    app_id: str
    name: str
    exec_line: str


def _platform() -> str:
    """A futó platform — külön függvény, hogy a teszt helyettesíthesse (#1217)."""
    return sys.platform


def has_native_open_with() -> bool:
    """Windowson a rendszer saját „Megnyitás ezzel" párbeszéde van."""
    return _platform().startswith("win")


def open_with_dialog_windows(path: Path) -> None:
    """A Windows héj „Megnyitás ezzel" párbeszédét indítja a fájlra."""
    _popen(
        ["rundll32.exe", "shell32.dll,OpenAs_RunDLL", str(path)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def apps_for_file(path: Path) -> list[OpenWithApp]:
    """A fájl MIME-típusához társított, megjeleníthető alkalmazások listája.

    Üres lista, ha a típus nem ismert, vagy nincs hozzá társítás."""
    mime, _kodolas = mimetypes.guess_type(str(path))
    if not mime:
        return []
    alkalmazasok: list[OpenWithApp] = []
    for app_id in _application_ids(mime):
        app = _load_desktop_app(app_id)
        if app is not None and app.app_id not in {a.app_id for a in alkalmazasok}:
            alkalmazasok.append(app)
    return alkalmazasok


def launch_app(app: OpenWithApp, path: Path) -> None:
    """Elindítja az alkalmazást a fájllal. Hiba esetén `OSError`-t emel."""
    _popen(
        exec_argv(app.exec_line, path),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def exec_argv(exec_line: str, path: Path) -> list[str]:
    """A `.desktop` `Exec=` sorából az indító argumentumlista.

    Ha a parancs nem tartalmaz fájlmezőt (`%f`, `%U`…), a fájlt a végére
    tesszük: a képnek így is át kell adódnia az alkalmazásnak."""
    argv: list[str] = []
    fajl_kezelve = False
    for token in shlex.split(exec_line):
        if token in _FAJL_KODOK:
            argv.append(str(path))
            fajl_kezelve = True
            continue
        tisztitott = _KOD_MINTA.sub(lambda m: "%" if m.group() == "%%" else "", token)
        if tisztitott:
            argv.append(tisztitott)
    if not fajl_kezelve:
        argv.append(str(path))
    return argv


def _adatkonyvtarak() -> list[Path]:
    """Az XDG adatkönyvtárak, a felhasználóié elöl."""
    otthon = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    rendszer = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
    return [Path(otthon), *(Path(p) for p in rendszer.split(":") if p)]


def _konfigkonyvtarak() -> list[Path]:
    """Az XDG konfigurációs könyvtárak, a felhasználóié elöl."""
    otthon = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    rendszer = os.environ.get("XDG_CONFIG_DIRS") or "/etc/xdg"
    return [Path(otthon), *(Path(p) for p in rendszer.split(":") if p)]


def _ini(fajl: Path) -> configparser.RawConfigParser | None:
    """Beolvassa az ini-jellegű fájlt; hibás vagy hiányzó fájlnál `None`."""
    if not fajl.is_file():
        return None
    parser = configparser.RawConfigParser(strict=False, interpolation=None)
    parser.optionxform = str  # type: ignore[assignment,method-assign]
    try:
        parser.read(fajl, encoding="utf-8")
    except (configparser.Error, UnicodeDecodeError, OSError):
        _log.warning("Nem olvasható társítási fájl: %s", fajl)
        return None
    return parser


def _application_ids(mime: str) -> list[str]:
    """A MIME-típushoz rendelt `.desktop` azonosítók, a prioritás szerint."""
    forrasok: list[configparser.RawConfigParser] = []
    for konyvtar in _konfigkonyvtarak():
        forrasok.append(_ini(konyvtar / "mimeapps.list"))
    for konyvtar in _adatkonyvtarak():
        forrasok.append(_ini(konyvtar / "applications" / "mimeapps.list"))
    ids: list[str] = []
    for parser in forrasok:
        if parser is None:
            continue
        for szakasz in _MIME_SZAKASZOK:
            ids.extend(_lista(parser, szakasz, mime))
    for konyvtar in _adatkonyvtarak():
        cache = _ini(konyvtar / "applications" / "mimeinfo.cache")
        if cache is not None:
            ids.extend(_lista(cache, "MIME Cache", mime))
    egyedi: list[str] = []
    for app_id in ids:
        if app_id not in egyedi:
            egyedi.append(app_id)
    return egyedi


def _lista(parser: configparser.RawConfigParser, szakasz: str, mime: str) -> list[str]:
    if not parser.has_section(szakasz) or not parser.has_option(szakasz, mime):
        return []
    return [azon.strip() for azon in parser.get(szakasz, mime).split(";") if azon.strip()]


def _desktop_fajl(app_id: str) -> Path | None:
    for konyvtar in _adatkonyvtarak():
        jelolt = konyvtar / "applications" / app_id
        if jelolt.is_file():
            return jelolt
    return None


def _load_desktop_app(app_id: str) -> OpenWithApp | None:
    fajl = _desktop_fajl(app_id)
    if fajl is None:
        return None
    parser = _ini(fajl)
    if parser is None or not parser.has_section("Desktop Entry"):
        return None
    adatok = parser["Desktop Entry"]
    if adatok.get("Type") != "Application":
        return None
    if adatok.get("NoDisplay") == "true" or adatok.get("Hidden") == "true":
        return None
    exec_line = adatok.get("Exec", "")
    nev = _lokalizalt_nev(adatok) or app_id
    if not exec_line:
        return None
    return OpenWithApp(app_id=app_id, name=nev, exec_line=exec_line)


def _lokalizalt_nev(adatok) -> str:
    """A `Name[nyelv]` kulcsot választja, ha van; különben az alapnevet."""
    for kulcs in _nyelvi_kulcsok():
        if kulcs in adatok and adatok[kulcs].strip():
            return adatok[kulcs].strip()
    return adatok.get("Name", "").strip()


def _nyelvi_kulcsok() -> list[str]:
    """A `Name[...]` kulcsok a LANG-környezeti változóból, a pontosabbal elöl."""
    nyelv = (os.environ.get("LANG") or "").split(".")[0].split("@")[0]
    if not nyelv:
        return []
    rovid = nyelv.split("_")[0]
    kulcsok = [f"Name[{nyelv}]", f"Name[{rovid}]"]
    return list(dict.fromkeys(kulcsok))
