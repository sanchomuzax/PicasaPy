"""Időrendi csoportosítás (#24) — a Picasa Timeline nézetének (Ctrl+5)
tiszta, GUI-mentes logikája.

A bemenet fotó-rekordok (azonosító + dátum) sorozata, a kimenet
immutábilis, csökkenő időrendbe (legújabb elöl) rendezett korszak-tuple
(év/hónap). Ez a modul semmit nem tud Qt-ról/QML-ről — a QML-hidat a
`picasapy.app.timeline_controller.TimelineController` adja.

Dátum-forrás (döntés, #24): a hívó dönti el fotónként, mi a "dátum" —
ehhez a `resolve_date` segédfüggvényt adjuk, ami az EXIF `taken_at`-ot
részesíti előnyben, és ennek hiányában (RAW/videó, vagy olvashatatlan
EXIF — ld. `picasapy.index.sync`) a fájl idejére esik vissza. Ez
józan alapértelmezés: az index sémájában `mtime_ns` mindig kitöltött,
`taken_at` viszont csak fényképeknél (és csak sikeres EXIF-olvasás
esetén) van jelen.

Index-rekordhoz a `record_date` a belépési pont: az a BEFAGYASZTOTT
fájlidőt adja a `resolve_date`-nek (#2486), nem az élőt.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

# ismeretlen dátumú fotók gyűjtő-korszaka — sem éve, sem hónapja nem
# ismert, ezért nem sorolható be máshova; a lista VÉGÉN jelenik meg
UNKNOWN_YEAR = 0
UNKNOWN_MONTH = 0


@dataclass(frozen=True)
class TimelinePhoto:
    """Egy fotó a csoportosításhoz: a hívó (jellemzően az index-rekord)
    azonosítója és a csoportosítás alapjául szolgáló, már feloldott
    dátuma. `date` None, ha semmilyen dátum nem állapítható meg."""

    photo_id: int
    date: date | None


@dataclass(frozen=True)
class TimelinePeriod:
    """Egy korszak (év + hónap) a hozzá tartozó fotókkal, a csoporton
    belül dátum szerint csökkenő sorrendben. `year`/`month` mindkettő
    `UNKNOWN_*`, ha ez az ismeretlen dátumú fotók gyűjtő-csoportja."""

    year: int
    month: int
    photos: tuple[TimelinePhoto, ...]


def resolve_date(taken_at: str | None, mtime_ns: int) -> date | None:
    """A csoportosítás dátuma egy fotóhoz: elsődlegesen az EXIF
    `taken_at` (ISO `yyyy-MM-ddTHH:mm:ss` — ld. `picasapy.index.schema`),
    ennek hiányában (vagy értelmezhetetlen formátum esetén) a fájl
    `mtime_ns`-éből számított naptári nap.

    Hibás/hiányzó bemenetnél (nincs sem `taken_at`, sem érvényes
    `mtime_ns`) None — ez a fotó az "ismeretlen dátum" gyűjtő-korszakba
    kerül a `build_periods`-ban.
    """
    if taken_at:
        try:
            return datetime.fromisoformat(taken_at).date()
        except ValueError:
            pass  # sérült/ismeretlen formátumú taken_at — mtime-ra esünk
    if mtime_ns:
        try:
            return datetime.fromtimestamp(mtime_ns / 1_000_000_000).date()
        except (OSError, OverflowError, ValueError):
            return None
    return None


def record_date(record) -> date | None:
    """Egy INDEX-REKORD (`picasapy.index.PhotoRecord`) időrendi dátuma.

    #2486: a fájlidő-tartalék a BEFAGYASZTOTT, első látáskori érték
    (`PhotoRecord.sort_mtime_ns`), nem az élő `mtime`. Enélkül ugyanaz az
    EXIF nélküli kép az Időrendben más korszakba kerülne, mint amilyen
    dátummal a rácsban (`app/photo_sort.photo_date`) és a mappa
    fejlécében (`app/formatting.photo_dates`) szerepel — ugyanarról a
    képről mondana mást két nézet.

    SZÁNDÉKOSAN itt, a Qt-mentes rétegben él, nem a controllerben: így a
    döntés őrizhető QML-motor nélkül is (a hívó
    `app/timeline_controller.py` csak ezt hívja).
    """
    return resolve_date(record.taken_at, record.sort_mtime_ns)


def build_periods(photos) -> tuple[TimelinePeriod, ...]:
    """Fotók (`TimelinePhoto` sorozat) csoportosítása év/hónap szerint,
    csökkenő időrendben (legújabb elöl) — Picasa Timeline-minta.

    Az ismeretlen dátumú fotók (`date is None`) egyetlen külön csoportba
    kerülnek (`UNKNOWN_YEAR`/`UNKNOWN_MONTH`), a lista VÉGÉN.

    Determinisztikus: azonos (év, hónap) csoporton belül a fotók dátum
    szerint csökkenő sorrendben állnak; azonos dátumnál a bemeneti
    sorrend dönt (Python `sorted` stabil rendezés — `reverse=True` sem
    töri meg az egyenlő kulcsú elemek eredeti sorrendjét).
    """
    dated: list[TimelinePhoto] = []
    undated: list[TimelinePhoto] = []
    for photo in photos:
        (dated if photo.date is not None else undated).append(photo)

    buckets: dict[tuple[int, int], list[TimelinePhoto]] = {}
    for photo in dated:
        key = (photo.date.year, photo.date.month)
        buckets.setdefault(key, []).append(photo)

    periods = [
        TimelinePeriod(
            year=year,
            month=month,
            photos=tuple(sorted(group, key=lambda p: p.date, reverse=True)),
        )
        for (year, month), group in buckets.items()
    ]
    periods.sort(key=lambda period: (period.year, period.month), reverse=True)

    if undated:
        periods.append(
            TimelinePeriod(
                year=UNKNOWN_YEAR, month=UNKNOWN_MONTH, photos=tuple(undated)
            )
        )

    return tuple(periods)
