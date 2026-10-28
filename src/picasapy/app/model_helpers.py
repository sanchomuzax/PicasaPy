"""A könyvtár listamodelljeinek közös, tiszta segédfüggvényei."""

from __future__ import annotations

import re
import zlib

from PySide6.QtCore import QModelIndex

from picasapy.index import PhotoRecord
from picasapy.metadata import megjelenitett_meret

from .arc_nagyitas_url import arc_cimke
from .display_mode_paint import current_display_mode, display_mode_url_suffix

_PATH_SEPARATORS = re.compile(r"[/\\]")


_YEAR_PREFIX = re.compile(r"^(\d{4})")


_ROOT_INDEX = QModelIndex()


REJTETT_MAPPAK_FEJLEC = "Rejtett mappák"


def _felbontas(photo) -> str:
    """A MEGJELENÍTETT felbontás felirata (#2996).

    Az index a fájlban TÁROLT méretet őrzi — a megjelenített kép viszont
    az EXIF-orientációval jön. Enélkül minden álló tájolású telefonkép
    fordítva mutatta a felbontását."""
    szelesseg, magassag = megjelenitett_meret(
        photo.width, photo.height, getattr(photo, "orientation", None)
    )
    return f"{szelesseg}x{magassag}" if szelesseg and magassag else ""


def _has_edits(photo: PhotoRecord) -> bool:
    """Van-e a képen Picasa-szerkesztés (#100) — a kék visszahajtás-jelölő
    feltétele. A `filters=` lánc megléte dönt: a vágott képeknél a crop64 a
    filters-történetben is szerepel, így a crop= külön indexelése nélkül is
    lefedett; a sima forgatás (rotate=) és a csillag NEM módosítás."""
    return bool(photo.filters and photo.filters.strip())


def _thumb_url(
    photo: PhotoRecord,
    display_mode: str | None = None,
    szint: int | None = None,
    arc: tuple[float, float, float, float] | None = None,
) -> str:
    """Thumb-URL forgatás-, szerkesztés- és FÁJLVÁLTOZÁS-érzékeny
    cache-busterrel (#59, #1186), megjelenítési mód-cimkével (#1596).

    #1656: a `display_mode` alapértéke MOSTANTÓL a jelenlegi mód, nem az
    üres sztring. Az üres alapérték volt az oka, hogy az idővonal, a
    keresési találatok és a képtálca bélyegképein a mód hatástalan
    maradt: mind ezt a függvényt hívja, csak mód nélkül. A rács modellje
    továbbra is a SAJÁT másolatát adja át (`self._display_mode`), mert az
    a `set_display_mode()`-dal együtt lépteti a `revision`-t is.

    ⚠️ Az `mtime_ns`/`size` nélkül a felülírt fájl URL-je változatlan
    marad (ugyanaz a sor, forgatás és lánc), a Qt pedig URL szerint
    gyorstárazza a képet — a rácson a RÉGI képpontok maradnak. A
    bélyegkép-gyorstár maga jól működik: az is a (útvonal, mtime, méret)
    hármasra kulcsol, csak épp senki nem kérte el az újat. A tulajdonos
    ezt a kollázs véglegesítésekor látta (a „PISZKOZAT" felirat ottmaradt
    a bélyegképen), de minden külső felülírásra igaz volt.

    A `display_mode` (#1596) pontosan ugyanezért kell: a `Nézet ▸
    Megjelenítési mód` a KIRAJZOLT képpontokat írja át, tehát a mód
    ugyanúgy az URL része, mint a forgatás. Képpontot nem mozdító módra a
    cimke elmarad, vagyis az URL bájtra a mód bevezetése előtti — a rendes
    használat semmivel nem lassul, a módból kilépve pedig a Qt gyorstárában
    már ott lévő, festetlen kép jelenik meg azonnal. A cimkét a
    `thumbnail_provider` olvassa vissza; a két felet a
    `display_mode_paint` tartja együtt.
    """
    if display_mode is None:
        display_mode = current_display_mode()
    filters_tag = zlib.crc32((photo.filters or "").encode("utf-8"))
    return (
        f"image://thumbs/{photo.id}"
        #: #2902: a tükrözés-jelző is gyorstár-törő — enélkül a rácson a
        #: régi állású kép maradna. Elnézően olvassuk: a kollázs-sáv
        #: rekord-hasonmásai nem ismerik a mezőt, és a 0 a helyes rájuk.
        f"?r={photo.rotate_steps}"
        f"&fl={getattr(photo, 'flip_flags', 0)}&f={filters_tag}"
        f"&m={photo.mtime_ns}&s={photo.size}"
        #: #598: a SZINT is az URL része, ugyanabból az okból, mint a
        #: megjelenítési mód: az URL egyértelműen határozza meg a
        #: képpontokat, különben a Qt URL-kulcsú gyorstárába más szintű kép
        #: ragadhatna be. A cimke csak akkor kerül ki, ha nem a felső
        #: szintről van szó — így a mai URL-ek bájtra változatlanok, és a
        #: meglévő gyorstár érvényes marad.
        f"{'' if szint is None else f'&sz={szint}'}"
        #: #2187: az arc-nagyítás kerete — csak személy-album arc-módjában
        #: kerül ki, tehát minden más URL bájtra változatlan
        f"{'' if arc is None else arc_cimke(arc)}"
        f"{display_mode_url_suffix(display_mode)}"
    )


def _sort_key(sort_mode: str):
    """Rendezőkulcs; dátum-módokban a dátumtalan mappák a sor végére."""
    if sort_mode == "name":
        return lambda f: f[0].casefold()
    if sort_mode == "size":
        return lambda f: f[4]
    if sort_mode == "changed":
        return lambda f: f[5]
    return lambda f: (f[3] is not None, f[3] or "", f[1])


def _descending(sort_mode: str) -> bool:
    """A Picasa alapértéke: dátum/változás/méret csökkenő, név növekvő."""
    return sort_mode != "name"


def _rejtett_csomopont(
    rejtettek: tuple[tuple[str, str, str, int, bool, bool], ...],
) -> tuple[tuple[str, str, str, int, bool, bool], ...]:
    """A rejtett mappák a saját fejlécük alatt, a lista végén (#1637/2).

    ÜRESEN nem ad fejlécet: aki nem rejtett el semmit, ne lásson egy
    örökké ott ülő, tartalmatlan csomópontot a hasáb alján.

    A fejléc `hidden` FAJTÁJÚ sor, útvonal nélkül — a delegate ugyanúgy
    nem engedi kijelölni, mint az évszám-elválasztót.
    """
    if not rejtettek:
        return ()
    fejlec = ("hidden", REJTETT_MAPPAK_FEJLEC, "", len(rejtettek), False, False)
    return (fejlec,) + rejtettek


def _with_year_separators(
    folders,
) -> tuple[tuple[str, str, str, int, bool, bool], ...]:
    """Évszám-elválasztók a mappa-dátum évéből (fallback: név-prefix).

    Audit (`docs/specs/ui-audit-mainwindow.md`, 1.1 pont): ha a listában
    MINDEN mappa dátumos ÉS ugyanabba az egyetlen évbe esik, a Picasa nem
    rajzol évszám-fejlécet — a mappák egyenesen a gyűjtemény-fejléc alá
    kerülnek (ez csak a homogén esetben áll fenn; ha akár egyetlen mappa is
    dátumtalan, vagy legalább két különböző év van jelen, az elválasztók a
    szokásos módon jelennek meg).
    """
    folders = list(folders)
    years = [
        _folder_year(name, date)
        for name, _path, _count, date, _offline, _unread in folders
    ]
    distinct_years = {year for year in years if year}
    if years and len(distinct_years) <= 1 and all(years):
        return tuple(
            ("folder", name, path, count, offline, unread)
            for name, path, count, _date, offline, unread in folders
        )

    rows = []
    last_year = None
    for (name, path, count, _date, offline, unread), year in zip(
        folders, years, strict=True
    ):
        if year and year != last_year:
            rows.append(("year", year, "", 0, False, False))
        last_year = year
        rows.append(("folder", name, path, count, offline, unread))
    return tuple(rows)


def _folder_year(name: str, date: str | None) -> str | None:
    """A mappa évszáma: a dátumból, vagy ennek híján a névből (`YYYY…`)."""
    if date:
        return date[:4]
    match = _YEAR_PREFIX.match(name)
    return match.group(1) if match else None

