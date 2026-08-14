"""PicasaPy — modern, nyílt Picasa-utód.

A verzió EGYETLEN igazságforrása a `pyproject.toml` — a kiadási automatika
(`.github/workflows/release.yml`) is azt olvassa szövegesen, ezért ott kell
maradnia a szó szerinti számnak. Itt SEMMILYEN körülmények között nem
tárolunk másolatot: #642-ben pontosan az okozta a hibát, hogy a két hely
kézzel volt egyeztetve, és 26 kiadásnyira csúszott szét — a program
hónapokig hamis verziót írt ki, ami a hibabejelentéseket vitte rossz
nyomra.

A származtatás két úton, ebben a sorrendben:

1. a csomag fölött megtalált `pyproject.toml` (`tomllib`, 3.11 óta stdlib)
   — ez a forrásból futtatott fejlesztői checkout esete, és AZÉRT áll
   elöl, mert ilyenkor a futó kód a forrásfáé: egy régebbi, párhuzamosan
   telepített csomag metaadata félrevezetne (pontosan ez a #642 tünete);
2. `importlib.metadata` — a telepített csomagnál ez pontosan a
   `pyproject.toml`-ból bekerült verzió.

A `tests/test_version_single_source.py` őrzi, hogy a két út ugyanazt adja,
mint a `pyproject.toml`.
"""

from __future__ import annotations

import tomllib
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _installed_version
from pathlib import Path

#: Végső visszaesés: sem telepítve, sem a pyproject.toml mellől futtatva.
#: Nem szám, hanem beszédes jelölés — egy hamis verziószám rosszabb a
#: semminél (#642), mert azt a felhasználó jóhiszeműen továbbadja.
_UNKNOWN = "0+unknown"


def _version_from_pyproject() -> str | None:
    """A PicasaPy `pyproject.toml`-jának `[project] version`-je, vagy None.

    A fájlt a csomag helyéből keressük visszafelé (`src/picasapy/` →
    a repó gyökere). A `[project] name` ellenőrzése kötelező: telepített
    csomagnál a `site-packages` fölött is állhat egy IDEGEN
    `pyproject.toml` (a felhasználó munkakönyvtárában), annak a verziója
    pedig katasztrofálisan félrevezetne.

    Hibatűrő: ha nincs meg vagy nem olvasható, a hívó a következő útra
    esik vissza — a verzió-kiolvasás SOHA nem akadályozhatja az indulást.
    """
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "pyproject.toml"
        if not candidate.is_file():
            continue
        try:
            with candidate.open("rb") as handle:
                data = tomllib.load(handle)
        except (OSError, tomllib.TOMLDecodeError):
            continue
        project = data.get("project", {})
        if project.get("name") != "picasapy":
            continue
        value = project.get("version")
        if isinstance(value, str):
            return value
    return None


def _resolve_version() -> str:
    from_source = _version_from_pyproject()
    if from_source is not None:
        return from_source
    try:
        return _installed_version("picasapy")
    except PackageNotFoundError:
        return _UNKNOWN


__version__ = _resolve_version()
