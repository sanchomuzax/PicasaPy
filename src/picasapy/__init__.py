"""PicasaPy — modern, nyílt Picasa-utód.

**A verzió egyetlen igazságforrása a `pyproject.toml` (#642).** Korábban a
szám itt is le volt írva, és csak a `pyproject.toml`-t emelték kiadáskor — a
kettő 26 kiadásnyira szétcsúszott, a program `v0.6.86`-ot mutatott 0.7.35
helyett. Ez nem kozmetikai hiba: a felhasználó jóhiszeműen a kijelzett
verziót jelenti a hibabejelentésben, és az rossz nyomra viszi a keresést.

A feloldás sorrendje szándékosan a FORRÁSSAL kezd:

1. **`pyproject.toml`**, ha a forrásfából futunk — így a kijelzett szám azt
   azonosítja, ami TÉNYLEG fut, nem azt, amit legutóbb telepítettek;
2. **`importlib.metadata`** a telepített csomagnál (wheel, pipx);
3. végső esetben `"0.0.0+ismeretlen"` — jobb egy nyilvánvalóan hamis szám,
   mint egy hihető, de rossz.

A `pyproject.toml` a `release.yml`-ben SZÖVEGESEN olvasódik (`grep`), ezért
ott marad a szó szerinti szám; a `dynamic = ["version"]` irányba fordítás
elrontaná a kiadási munkafolyamatot.
"""

from __future__ import annotations

from pathlib import Path

_ISMERETLEN = "0.0.0+ismeretlen"


def _verzio_a_forrasbol() -> str | None:
    """A `pyproject.toml` verziója, ha a forrásfából futunk.

    A csomag a `src/picasapy/`-ban él, tehát a `pyproject.toml` két szinttel
    feljebb van. Telepített csomagnál ez a fájl nincs meg — ilyenkor None.
    """
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        nyers = pyproject.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        import tomllib  # stdlib 3.11+ — nincs új függőség
    except ImportError:  # pragma: no cover — a projekt 3.12+-t kér
        return None
    try:
        adat = tomllib.loads(nyers)
    except ValueError:
        return None
    ertek = adat.get("project", {}).get("version")
    return ertek if isinstance(ertek, str) and ertek else None


def _verzio_a_telepitesbol() -> str | None:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("picasapy")
    except PackageNotFoundError:
        return None


__version__ = _verzio_a_forrasbol() or _verzio_a_telepitesbol() or _ISMERETLEN

__all__ = ["__version__"]
