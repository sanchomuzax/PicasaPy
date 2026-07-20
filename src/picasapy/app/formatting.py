"""Megjelenítési formázók: méret, dátum, infó-sáv és Tulajdonságok-panel
szövegépítése (#150 — az AppControllerből kiemelve).

Tiszta függvények: nincs Qt-objektum-állapotuk, a lokalizációt a hívó adja
át (`locale` + a fordítási kontextust őrző, kötött `tr`). Így a fordítások
kontextusa változatlanul az `AppController` marad."""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QDate, QDateTime, QLocale

from picasapy.metadata import read_exif_details

# útvonal-vég leválasztása mappa-névhez (per- és backslash-tűrő)
PATH_TAIL = re.compile(r"[/\\]")


def to_local_path(path_or_url: str) -> str:
    """file:// URL vagy sima útvonal → OS-natív lokális útvonal.

    A QUrl.toLocalFile Windowson per-jeles utat ad (C:/...) — a Path-on
    átfuttatás normalizálja, különben ugyanaz a mappa két alakban
    szerepelhetne a figyeltek közt."""
    from PySide6.QtCore import QUrl

    text = path_or_url.strip()
    if text.startswith("file:"):
        text = QUrl(text).toLocalFile()
    return str(Path(text)) if text else ""


def format_size(size_bytes: int, locale: QLocale, tr) -> str:
    """Fájlméret Picasa-stílusban: 1 MB alatt KB-ban, fölötte MB-ban."""
    if size_bytes < 1024 * 1024:
        return tr("%1 KB").replace("%1", str(round(size_bytes / 1024)))
    return tr("%1 MB").replace(
        "%1", locale.toString(size_bytes / (1024 * 1024), "f", 1)
    )


def long_date(iso: str, locale: QLocale) -> str:
    """Picasa-stílusú hosszú dátum: `2026. január 2., péntek`."""
    date = QDate.fromString(iso[:10], "yyyy-MM-dd")
    return locale.toString(date, QLocale.FormatType.LongFormat)


def first_date_text(records, locale: QLocale) -> str:
    """A csoport fejléc-dátuma: a legkorábbi felvétel hosszú dátuma."""
    dates = sorted(r.taken_at for r in records if r.taken_at)
    return long_date(dates[0], locale) if dates else ""


def format_exposure(seconds: float, locale: QLocale) -> str:
    """Záridő fotós alakban: 1 mp alatt `1/N s`, fölötte `N s`."""
    if 0 < seconds < 1:
        return f"1/{round(1 / seconds)} s"
    return f"{locale.toString(seconds, 'g', 3)} s"


def _dimensions_text(photo, tr) -> str:
    """`SZxM képpont` szöveg a felbontáshoz."""
    return (
        tr("%1x%2 pixels")
        .replace("%1", str(photo.width))
        .replace("%2", str(photo.height))
    )


def photo_info_text(photo, locale: QLocale, tr) -> str:
    """A kék infó-sáv kijelöléskori tartalma, Picasa-stílusban:
    `név   dátum   SZxM képpont   méret`."""
    parts = [photo.name]
    if photo.taken_at:
        taken = QDateTime.fromString(photo.taken_at, "yyyy-MM-ddTHH:mm:ss")
        parts.append(locale.toString(taken, QLocale.FormatType.ShortFormat))
    if photo.width and photo.height:
        parts.append(_dimensions_text(photo, tr))
    parts.append(format_size(photo.size, locale, tr))
    return "   ".join(parts)


def properties_entries(photo, locale: QLocale, tr) -> list:
    """A Tulajdonságok-panel (#13) sorai: (címke, érték) párok.

    Az alap-adatok az indexből jönnek; az expozíciós EXIF-mezők
    igény szerinti fájl-olvasással (csak a panel megnyitásakor fut,
    griden sosem). Üres mezők kimaradnak — csak olvasás."""
    entries = [
        (tr("File name"), photo.name),
        (tr("Folder"), photo.folder_path),
        (tr("File size"), format_size(photo.size, locale, tr)),
    ]
    if photo.width and photo.height:
        entries.append((tr("Dimensions"), _dimensions_text(photo, tr)))
    if photo.taken_at:
        taken = QDateTime.fromString(photo.taken_at, "yyyy-MM-ddTHH:mm:ss")
        entries.append((
            tr("Date taken"),
            locale.toString(taken, QLocale.FormatType.ShortFormat),
        ))
    if photo.kind == "photo":
        entries.extend(exif_entries(photo, locale, tr))
    return entries


def exif_entries(photo, locale: QLocale, tr) -> list:
    """Fényképezőgép-adatok a Tulajdonságok-panelre (üresek kihagyva)."""
    details = read_exif_details(Path(photo.folder_path) / photo.name)
    entries = []
    if details.camera:
        entries.append((tr("Camera"), details.camera))
    if details.exposure_seconds:
        entries.append((
            tr("Exposure"),
            format_exposure(details.exposure_seconds, locale),
        ))
    if details.f_number:
        entries.append((
            tr("Aperture"),
            f"f/{locale.toString(details.f_number, 'g', 3)}",
        ))
    if details.iso:
        entries.append((tr("ISO"), str(details.iso)))
    if details.focal_mm:
        entries.append((
            tr("Focal length"),
            tr("%1 mm").replace(
                "%1", locale.toString(details.focal_mm, "g", 4)
            ),
        ))
    if details.flash_fired is not None:
        entries.append((
            tr("Flash"),
            tr("Fired") if details.flash_fired else tr("Did not fire"),
        ))
    if details.white_balance:
        entries.append((
            tr("White balance"),
            tr("Automatic") if details.white_balance == "auto"
            else tr("Manual"),
        ))
    return entries


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
    total_mb = sum(r.size for r in records) / (1024 * 1024)
    dates = sorted(r.taken_at for r in records if r.taken_at)
    date_part = ""
    if dates:
        first = long_date(dates[0], locale)
        last = long_date(dates[-1], locale)
        date_part = first if first == last else f"{first}-{last}"
    return tr_n("%n picture(s)", "", len(records)) + (
        f"   {date_part}   " if date_part else "   "
    ) + tr("%1 MB on disk").replace(
        "%1", locale.toString(total_mb, "f", 1)
    )


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
