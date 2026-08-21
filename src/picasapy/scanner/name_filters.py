r"""Név-alapú kizárólista a mappa-bejáráshoz — az eredeti Picasa
`runtime/filters.txt` mintájára (#349, ld. `docs/specs/picasa-program-
resources.md` 3.1. szakasz).

Az eredeti fájl hat, fejléc-sorral kezdődő szekciót ismert:

    DirectoryFilters      — kizárt könyvtárnevek
    DirectoryIncludes     — kivétel a fenti kizárás alól
    FileFilters           — kizárt fájlnevek
    FileIncludes          — kivétel a fenti kizárás alól
    BundleFilters-BlackList — bundle-k tiltólistája
    BundleFilters-WhiteList — bundle-k engedélyezőlistája

Az Includes szekció mindig felülírja a Filters-t (elsőbbséget élvez) —
ez teszi lehetővé, hogy egy tág kizárási mintán belül egy konkrét nevet
mégis megtartsunk. A gyári telepítésben a `DirectoryFilters` öt nevet
tartalmazott: `windows`, `winnt`, `temp`, `Program Files`, `Originals`;
a másik három szekció üres volt.

**Egyezés-szemantika — NÉV, nem útvonal-részlet.** Az összehasonlítás a
mappa/fájl *saját nevére* (a path utolsó komponensére) vonatkozik, kis-
nagybetű-független teljes egyezéssel — NEM útvonal-substring-illesztés.
Ez szándékos: az eredeti Picasa is így viselkedett, és ez korlátozza a
kockázatot, hogy a szűrés véletlenül valódi fotómappákat nyeljen el (pl.
egy `C:\Fotok\Temp Munkák` útvonal nem esne ki, mert az útvonal
tartalmazza a "temp" szót, de a mappa NEVE nem egyezik vele). A
kis-nagybetű-függetlenség azért kell, mert élesben (ld. MEMORY
2026-07-16 tapasztalat) a hasonló gyári fájlnevek kisbetűsen is
előfordulnak — a `filters.txt`-beli `Program Files`/`Originals` írásmód
tehát nem garancia semmilyen tényleges elnevezésre.

**Kockázat, amit tudatosan vállalunk:** ha a felhasználónak ténylegesen
van egy `Temp`, `Windows` vagy `Originals` nevű fotó-almappája, annak
tartalma kimarad az indexelésből — pontosan úgy, ahogy az eredeti
Picasa is kihagyta. Ez a négyszekciós séma miatt orvosolható: a jövőbeli
felhasználói konfiguráció (nincs UI-ja ennek a jegynek, csak az
adatszerkezet) a `directory_includes`-ba felvéve visszahozhatja az adott
nevet a bejárásba.

A `.picasaoriginals` (a Picasa nem-destruktív szerkesztésének rejtett
biztonsági-mentés mappája) magától a pont-előtagtól már kimarad a
bejárásból (ld. `picasapy.scanner.walker` rejtett-mappa szabálya) — a
`DEFAULT_DIRECTORY_FILTERS`-ben mégis szerepel, hogy a védelem attól
függetlenül is álljon, ha valaki a rejtett-mappa szabályt megkerülné
(pl. jövőbeli "rejtett mappák mutatása" beállítással).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Az eredeti Picasa `runtime/filters.txt` DirectoryFilters szekciója.
DEFAULT_DIRECTORY_FILTERS: tuple[str, ...] = (
    "windows",
    "winnt",
    "temp",
    "Program Files",
    "Originals",
    ".picasaoriginals",
    "thumbs",
    "RECYCLER",
)

# Linux-first alapértelmezések: ezek útvonal-előtagok, ezért szándékosan nem
# kerülnek a könyvtárnév-alapú `DEFAULT_DIRECTORY_FILTERS` listába. A `~`
# feloldása csak az összehasonlításkor történik, hogy importkor ne rögzítsük
# a futtató felhasználó saját könyvtárát.
DEFAULT_PATH_PREFIX_FILTERS: tuple[str, ...] = (
    "~/.cache",
    "~/.local/share/Trash",
    "/proc",
    "/sys",
    "/usr",
)


@dataclass(frozen=True)
class NameFilters:
    """Könyvtár-, fájlnév- és útvonal-alapú kizárólista, Picasa-féle
    hatszekciós
    szemantikával. Immutable — a bővítés (jövőbeli felhasználói
    konfiguráció) új példány létrehozásával történik, nem mutálással."""

    directory_filters: tuple[str, ...] = field(default_factory=tuple)
    directory_includes: tuple[str, ...] = field(default_factory=tuple)
    file_filters: tuple[str, ...] = field(default_factory=tuple)
    file_includes: tuple[str, ...] = field(default_factory=tuple)
    bundle_filters_blacklist: tuple[str, ...] = field(default_factory=tuple)
    bundle_filters_whitelist: tuple[str, ...] = field(default_factory=tuple)
    path_prefix_filters: tuple[str | Path, ...] = field(default_factory=tuple)
    _normalised_path_prefixes: tuple[tuple[str, ...], ...] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_normalised_path_prefixes",
            tuple(_normalised_path_parts(prefix) for prefix in self.path_prefix_filters),
        )

    def is_directory_excluded(self, name: str) -> bool:
        """Igaz, ha `name` (a mappa saját neve, nem teljes útvonal) a
        `directory_filters` valamelyikével kis-nagybetű-függetlenül
        teljesen egyezik, ÉS a `directory_includes` egyike sem egyezik
        vele (az includes felülírja a filters-t)."""
        return _matches(name, self.directory_filters) and not _matches(
            name, self.directory_includes
        )

    def is_file_excluded(self, name: str) -> bool:
        """Igaz, ha `name` a `file_filters` valamelyikével egyezik, és a
        `file_includes` nem írja felül."""
        return _matches(name, self.file_filters) and not _matches(name, self.file_includes)

    def is_path_excluded(self, path: str | Path) -> bool:
        """Igaz, ha a teljes `path` valamely útvonal-előtag alatt van.

        Ez külön művelet a könyvtárnév-egyezéstől: például a `~/.cache`
        alatti fákat kizárja, egy máshol lévő `Cache` nevű fotómappát nem.
        A komponenshatáros összehasonlítás megakadályozza, hogy `/usr` a
        `/usrbin` vagy `/usr-local` útvonalra is tévesen illeszkedjen.
        """
        path_parts = _normalised_path_parts(path)
        return any(
            len(path_parts) >= len(prefix_parts)
            and path_parts[: len(prefix_parts)] == prefix_parts
            for prefix_parts in self._normalised_path_prefixes
        )


def default_name_filters() -> NameFilters:
    """A Picasa gyári `filters.txt`-jének megfelelő alapértelmezett
    kizárólista — üres Includes/FileFilters és BundleFilters szekciókkal."""
    return NameFilters(
        directory_filters=DEFAULT_DIRECTORY_FILTERS,
        path_prefix_filters=DEFAULT_PATH_PREFIX_FILTERS,
    )


def _matches(name: str, candidates: tuple[str, ...]) -> bool:
    lowered = name.casefold()
    return any(lowered == candidate.casefold() for candidate in candidates)


def _normalised_path_parts(path: str | Path) -> tuple[str, ...]:
    resolved = Path(path).expanduser().resolve()
    return tuple(part.casefold() for part in resolved.parts)
