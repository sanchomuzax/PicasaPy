"""Meglévő Picasa-telepítés felderítése (#146).

Cél: az első induláskor (vagy a Mappakezelőből indítva) a PicasaPy fel tudja
ajánlani egy meglévő (Windows-os, Wine alatt futtatott, vagy NAS-ra másolt)
Picasa-telepítés `WatchedFolders.txt`-jének átvételét, path-remappel.

Két forrásból gyűjtünk jelölteket:
1. **Ismert Wine-útvonalak** — a Linuxon futó Wine a Windows `%LocalAppData%`-t
   a `<prefix>/drive_c/users/<felhasználó>/AppData/Local` (újabb Wine) vagy
   `<prefix>/drive_c/users/<felhasználó>/Local Settings/Application Data`
   (XP-stílusú profil) alá képezi le.
2. **Kézzel megadott mappák** (`extra_candidates`) — pl. NAS-ra másolt
   `Picasa2Albums`/`Picasa2` könyvtár, vagy ezek szülője.

A `WatchedFolders.txt` felismerése kis-nagybetű-független (#145,
`scanner.config_files`), csakúgy, mint a `Google`/`Picasa2`/`Picasa2Albums`
alkönyvtárak neve (élesben NAS/Samba-másolatoknál előfordul kisbetűsen is).

A tényleges útvonal-átírást a `pmpimport.PathRemapper` végzi (7. rögzített
döntés: az import/felderítés bármikor ismételhető, idempotens eredménnyel —
ez a modul csak *javaslatot* ad, fájlt nem ír).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..pmpimport.remap import PathRemapper
from .config_files import find_config_file
from .watched import WATCHED_FOLDERS_NAME, read_watched_folders

_PICASA2_DIR_NAME = "Picasa2"
_PICASA2ALBUMS_DIR_NAME = "Picasa2Albums"
_GOOGLE_DIR_NAME = "Google"

# A Wine az %LocalAppData%-t ezekre a relatív útvonalakra képezi le a
# felhasználói profil könyvtárán belül (a sorrend nem számít, mindkettőt
# megnézzük).
_WINE_APPDATA_RELATIVE_DIRS = (
    "AppData/Local",
    "Local Settings/Application Data",
)


@dataclass(frozen=True)
class PicasaInstallation:
    """Egy felismert (vagy kézzel megadott) Picasa-adatkönyvtár.

    A három mező bármelyike lehet `None` — pl. ha csak a `Picasa2Albums`
    (WatchedFolders.txt) van meg, a db3-könyvtár (`Picasa2`) nincs a közelben.
    """

    label: str
    picasa2_dir: Path | None
    picasa2albums_dir: Path | None
    watched_folders_file: Path | None


def _find_subdir_ci(parent: Path, name: str) -> Path | None:
    """`name` nevű alkönyvtár kis-nagybetű-független keresése `parent`-ben."""
    if not parent.is_dir():
        return None
    target = name.lower()
    for entry in sorted(parent.iterdir()):
        if entry.is_dir() and entry.name.lower() == target:
            return entry
    return None


def _installation_from_appdata(label: str, appdata: Path) -> PicasaInstallation | None:
    """Egy `%LocalAppData%`-szerű könyvtár vizsgálata: van-e alatta
    `Google/Picasa2` és/vagy `Google/Picasa2Albums`."""
    google_dir = _find_subdir_ci(appdata, _GOOGLE_DIR_NAME)
    if google_dir is None:
        return None
    return _installation_from_google_dir(label, google_dir)


def _installation_from_google_dir(label: str, google_dir: Path) -> PicasaInstallation | None:
    picasa2_dir = _find_subdir_ci(google_dir, _PICASA2_DIR_NAME)
    picasa2albums_dir = _find_subdir_ci(google_dir, _PICASA2ALBUMS_DIR_NAME)
    if picasa2_dir is None and picasa2albums_dir is None:
        return None
    watched_file = (
        find_config_file(picasa2albums_dir, WATCHED_FOLDERS_NAME)
        if picasa2albums_dir is not None
        else None
    )
    return PicasaInstallation(
        label=label,
        picasa2_dir=picasa2_dir,
        picasa2albums_dir=picasa2albums_dir,
        watched_folders_file=watched_file,
    )


def _installation_from_manual_dir(directory: str | Path) -> PicasaInstallation | None:
    """Kézzel megadott mappa vizsgálata (pl. NAS-ra másolt db3-könyvtár).

    A megadott mappa lehet:
    1. maga a `Picasa2Albums` (közvetlenül tartalmazza a `WatchedFolders.txt`-t),
    2. a `Picasa2`/`Picasa2Albums`-t tartalmazó `Google`-szülő,
    3. egy `%LocalAppData%`-szerű szülő (benne `Google/...`).
    """
    base = Path(directory)
    if not base.is_dir():
        return None

    label = f"Kézi mappa ({base})"

    direct_watched = find_config_file(base, WATCHED_FOLDERS_NAME)
    if direct_watched is not None:
        return PicasaInstallation(
            label=label,
            picasa2_dir=None,
            picasa2albums_dir=base,
            watched_folders_file=direct_watched,
        )

    installation = _installation_from_google_dir(label, base)
    if installation is not None:
        return installation

    return _installation_from_appdata(label, base)


def _wine_appdata_candidates(
    home: Path, wineprefix: Path | None
) -> tuple[tuple[str, Path], ...]:
    """Ismert Wine-prefixek felhasználói `%LocalAppData%`-szerű könyvtárai."""
    prefixes: list[tuple[str, Path]] = []

    default_wine = home / ".wine"
    if default_wine.is_dir():
        prefixes.append(("Wine (~/.wine)", default_wine))

    if wineprefix is not None and wineprefix.is_dir() and wineprefix != default_wine:
        prefixes.append((f"Wine ({wineprefix})", wineprefix))

    candidates: list[tuple[str, Path]] = []
    for prefix_label, prefix in prefixes:
        users_dir = prefix / "drive_c" / "users"
        if not users_dir.is_dir():
            continue
        for user_dir in sorted(p for p in users_dir.iterdir() if p.is_dir()):
            for rel in _WINE_APPDATA_RELATIVE_DIRS:
                appdata = user_dir / rel
                if appdata.is_dir():
                    candidates.append((f"{prefix_label}, {user_dir.name}", appdata))
    return tuple(candidates)


def discover_installations(
    extra_candidates: tuple[str | Path, ...] = (),
    *,
    home: str | Path | None = None,
    wineprefix: str | Path | None = None,
) -> tuple[PicasaInstallation, ...]:
    """Meglévő Picasa-telepítések felderítése.

    Két forrás: ismert Wine-útvonalak (`home`/`wineprefix` — alapértelmezés
    `Path.home()` és a `WINEPREFIX` környezeti változó, de teszteléshez és
    egyedi beállításhoz felülírhatók) és a hívó által megadott kézi jelöltek
    (`extra_candidates`, pl. NAS-mount). Csak azokat a jelölteket adja
    vissza, amelyekben ténylegesen van `Picasa2` és/vagy `Picasa2Albums`
    alkönyvtár; duplikátumokat (ugyanaz a könyvtárpár) kiszűri.
    """
    resolved_home = Path(home) if home is not None else Path.home()
    resolved_wineprefix = (
        Path(wineprefix)
        if wineprefix is not None
        else (Path(os.environ["WINEPREFIX"]) if os.environ.get("WINEPREFIX") else None)
    )

    results: list[PicasaInstallation] = []
    seen: set[Path] = set()

    def _add(installation: PicasaInstallation | None) -> None:
        if installation is None:
            return
        # A dedup-kulcs a Picasa2Albums (ha van), különben a Picasa2
        # könyvtár — így egy ugyanazon telepítést közvetlenül (pl. NAS-
        # mount a Picasa2Albums-ra) és a szülőn át (Wine-jelölt) is
        # felismerő két hívás nem duplikálódik.
        key = installation.picasa2albums_dir or installation.picasa2_dir
        if key is not None:
            if key in seen:
                return
            seen.add(key)
        results.append(installation)

    for label, appdata in _wine_appdata_candidates(resolved_home, resolved_wineprefix):
        _add(_installation_from_appdata(label, appdata))

    for candidate in extra_candidates:
        _add(_installation_from_manual_dir(candidate))

    return tuple(results)


def propose_watched_folders(
    installation: PicasaInstallation, remap: PathRemapper
) -> tuple[Path, ...]:
    """A telepítés `WatchedFolders.txt`-jének beolvasása és útvonal-átírása
    a helyi (pl. NAS-mount) megfelelőre.

    Az át nem írható (nem egyező prefixű) bejegyzéseket kihagyja, a
    duplikátumokat (a remap után egyező célútvonalakat) összevonja. Tisztán
    olvasó, mellékhatásmentes függvény — csak *javaslatot* ad, semmit nem ír;
    ismételt hívása ugyanarra a bemenetre mindig ugyanazt az eredményt adja
    (7. rögzített döntés: a felderítés bármikor újrafuttatható)."""
    if installation.watched_folders_file is None:
        return ()

    raw_folders = read_watched_folders(installation.watched_folders_file)

    proposed: list[Path] = []
    seen: set[Path] = set()
    for raw in raw_folders:
        remapped = remap.remap(raw)
        if remapped is None:
            continue
        path = Path(remapped)
        if path in seen:
            continue
        seen.add(path)
        proposed.append(path)

    return tuple(proposed)
