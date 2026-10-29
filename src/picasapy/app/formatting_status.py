"""Szűrési eredmény, alsó állapotsor és feedcsoportok formázói."""

from __future__ import annotations

import re

from PySide6.QtCore import QLocale

from .formatting_dates import first_date_text, long_date, photo_dates
from .formatting_sizes import format_size

# Útvonal-vég leválasztása mappa-névhez (per- és backslash-tűrő).
PATH_TAIL = re.compile(r"[/\\]")

def filter_status_text(records, elapsed: float, locale: QLocale, tr) -> str:
    """A zöld eredménysáv szövege (Picasa-minta)."""
    folders = len({r.folder_path for r in records})
    total_gb = sum(r.size for r in records) / (1024**3)
    return (
        tr("%1 folders / %2 pictures visible (%3 seconds) %4 GB")
        .replace("%1", str(folders))
        .replace("%2", str(len(records)))
        .replace("%3", locale.toString(elapsed, "f", 3))
        .replace("%4", locale.toString(total_gb, "f", 1))
    )


def status_text(records, locale: QLocale, tr, tr_n) -> str:
    """Az alsó állapotsor szövege: darabszám, dátumtartomány, összméret.

    A `tr_n` a többes számot kezelő fordító (`%n picture(s)` minta)."""
    if not records:
        return tr("0 pictures")
    meret = format_size(sum(r.size for r in records), locale, tr)
    # #2304: EXIF-felvételi idő híján a FÁJL ideje a tartalék. Enélkül egy
    # csupa EXIF-nélküli mappánál (letöltött vagy generált képek) a
    # dátumtartomány egyszerűen kimaradt az állapotsorból, holott az
    # eredeti Picasa ott is ír dátumot. A `photo_dates` KÖZÖS a
    # mappa-fejléccel, hogy a két felirat ne mondhasson mást ugyanarról a
    # halmazról; a „mindent vagy semmit" tartalék indoklása is ott áll.
    dates = photo_dates(records)
    first = last = ""
    if dates:
        first = long_date(dates[0], locale)
        last = long_date(dates[-1], locale)
    # ⚠️ A MÉRTÉKEGYSÉG a méret-argumentum RÉSZE, nem a formátumé: az eredeti
    # `     %s      %s on disk` második `%s`-e a kész méretszöveg (például
    # „174 KB” vagy „1,5 MB”). Enélkül a sávról eltűnik az egység.
    # #1913: a méret-feliratnak KÉT alakja van, és a választás feltétele a két
    # FORMÁZOTT dátum sztring-egyenlősége (mérve: `0x00570266 sete al`) — nem
    # időbélyeg-összehasonlítás. Ebből következik, hogy nincs időablak:
    # ugyanaznap 00:01 és 23:59 is az „egy dátum" alakot adja, mert a napra
    # pontos formátum ugyanazt a szöveget adja.
    #
    # A két formátum az eredeti `il_GetSelectionInfo::5` és `::4` kulcsa; a
    # magyar alakjuk KÜLÖNBÖZIK („%2$s/lemez" vs „%3$s a lemezen"), ezért két
    # külön fordítható sztring, nem egy közös + külön dátum-rész.
    if not dates:
        meretjel = "__PICASAPY_MERET__"
        mb_resz = tr("%1 MB").replace("%1", meretjel)
        on_disk = tr("%1 MB on disk").replace("%1", meretjel)
        farok = "   " + on_disk.replace(mb_resz, meret, 1)
    elif first == last:
        #: `il_GetSelectionInfo::5` — EGY dátum
        farok = (
            tr("     %1      %2 on disk")
            .replace("%1", first)
            .replace("%2", meret)
        )
    else:
        #: `il_GetSelectionInfo::4` — dátum-TARTOMÁNY
        farok = (
            tr("     %1 to %2     %3 on disk")
            .replace("%1", first)
            .replace("%2", last)
            .replace("%3", meret)
        )
    return (
        tr_n("%n picture(s)", "", len(records))
        + farok
        + _cimke_resz(records, tr)
    )


def _cimke_resz(records, tr) -> str:
    """A sáv UTOLSÓ, feltételes darabja: `     Címkék: <név> (<db>)` (#1913).

    Mérve (`0x0057040e`–`0x00570442`): a honosított `Címkék: ` előtag után
    címkénként a BEÉGETETT `%s (%d)` alak (a zárójeles darabszám nincs a
    szövegtárban, tehát minden nyelven ugyanaz), az egész rész előtt ÖT
    szóköz elválasztó — és ha nincs címke, **az elválasztó sem kerül ki**
    (a `0x00570424` NULL-ága és a `0x00570430` üres-ága).

    A darabszám a CÍMKÉZETT képek száma, nem a kijelöltek — a referencia
    felvételen `67 képek … Címkék: AI image (66)`.

    ⚠️ **Ami NINCS mérve:** több címke esetén az EGYES tételek közti
    elválasztó. A referencia-felvételen egyetlen címke van, és a bináris
    ciklusa a tételeket egyenként formázza. Itt vesszőt használunk (a
    kulcsszavak amúgy is vesszővel tagoltak a `.picasa.ini`-ben); ha egyszer
    előkerül egy több címkés felvétel, ez a pont felülvizsgálandó.
    """
    szamlalo: dict[str, int] = {}
    for record in records:
        for nyers in (getattr(record, "keywords", "") or "").split(","):
            cimke = nyers.strip()
            if cimke:
                szamlalo[cimke] = szamlalo.get(cimke, 0) + 1
    if not szamlalo:
        return ""
    tetelek = ", ".join(
        f"{nev} ({db})"
        for nev, db in sorted(szamlalo.items(), key=lambda p: (-p[1], p[0]))
    )
    return "     " + tr("Tags: ") + tetelek


def build_feed_groups(records, locale: QLocale) -> tuple:
    """Mappa-csoportok a rács-feedhez (#64): az egymást követő azonos
    mappájú futamok, {path, name, start, count, dateText} alakban."""
    runs: list[list] = []
    for row, record in enumerate(records):
        if not runs or runs[-1][0] != record.folder_path:
            runs.append([record.folder_path, row, 0])
        runs[-1][2] += 1
    return tuple(
        {
            "path": path,
            "name": PATH_TAIL.split(path)[-1],
            "start": start,
            "count": count,
            "dateText": first_date_text(records[start : start + count], locale),
        }
        for path, start, count in runs
    )
