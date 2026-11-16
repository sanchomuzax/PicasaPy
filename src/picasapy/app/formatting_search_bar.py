"""A keresősáv eredményszövege és az ezres tagolás (#7079).

Az eredeti `CThumbUI` keresési fejléc-építője (`0x00662b20`, #7072 E9) a
szövegtár kulcsaiból rakja össze a sávot:

- `searchmatchstr`: `Search results for "%s"` (kifejezéses keresés találattal),
- `nomatch`: `No matches` (találat nélkül),
- `sresults`: `%d results: ` és a bekapcsolt gombok szavai: `sfaces`,
  `sstarred`, `smovies`, `sgeotag` (gombos szűrő, kifejezés nélkül).

A `CThumbUI::searchmatch` (` (%d matches)`) kulcsra az EXE-ben nincs hivatkozó
literál, ezért a kifejezéses fejléc NEM kap darabszám-utótagot; a darabszám a
zöld sáv `searchdisplay` mondatában él (`formatting_status.filter_status_text`).

A `sonline` szó (online elemek) szándékosan hiányzik: a hozzá tartozó
webalbum-szűrő megszűnt szolgáltatás, a PicasaPy-ban nincs ilyen nézetmód.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QLocale


def group_digits(value: int, locale: QLocale) -> str:
    """Az egész szám ezres tagolással, a nyelv csoport-elválasztójával.

    A `QLocale.toString` itt kevés két okból: a magyar nyelvi adat az 1000 és
    9999 közötti számot nem tagolja (legalább két számjegy kell a csoport
    elé), a `C` helyi beállítás pedig `OmitGroupSeparator`-ral indul. A #7079
    szerint 1000 fölött mindig tagolni kell, ezért a csoportokat magunk
    képezzük, és csak az elválasztó jelet kérjük a nyelvtől.
    """
    elvalaszto = locale.groupSeparator() or " "
    szam = int(value)
    jegyek = str(abs(szam))
    csoportok: list[str] = []
    while len(jegyek) > 3:
        csoportok.append(jegyek[-3:])
        jegyek = jegyek[:-3]
    csoportok.append(jegyek)
    szoveg = elvalaszto.join(reversed(csoportok))
    return f"-{szoveg}" if szam < 0 else szoveg


def _filter_button_word(view_mode: str, tr: Callable[[str], str]) -> str:
    """A gombos szűrő szava (`sfaces`, `sstarred`, `smovies`, `sgeotag`)."""
    if view_mode == "faces":
        return tr("faces")
    if view_mode == "starred":
        return tr("starred")
    if view_mode == "videos":
        return tr("movies")
    if view_mode == "geo":
        return tr("geotagged")
    return ""


def search_bar_text(
    *,
    view_mode: str,
    query: str,
    search_count: int,
    shown_count: int,
    status: str,
    locale: QLocale,
    tr: Callable[[str], str],
) -> str:
    """A keresési beállítások `searchresult` elemének szövege.

    `search_count` az ÖSSZES találat (mappára szűkítve is), `shown_count` a
    rácson látszó képek száma, `status` a zöld sáv szövege. Ahol az eredetinek
    nincs külön szövege (album, életkor, hasonlóság, másodpéldány), a meglévő
    állapotszöveg marad: a viselkedést a #7079 nem változtatja.
    """
    if view_mode in ("search", "search-folder"):
        if not query:
            return status
        if search_count <= 0:
            return tr("No matches")
        return tr('Search results for "%1"').replace("%1", query)
    szo = _filter_button_word(view_mode, tr)
    if szo:
        return tr("%1 results: ").replace("%1", group_digits(shown_count, locale)) + szo
    return status
