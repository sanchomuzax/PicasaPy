"""#1436: a „Mappa rendezésének alapja ▸" vezérlő-szelete.

A menü a mappa TARTALMÁT rendezi (`Folder::SortFolderBy`, spec
`ui-audit-context-menus.md` 6.3) — korábban tévesen a rács MAPPA-sorrendjét
állító `setFolderSort`-ra volt kötve, ezért a menüpont mást tett, mint amit
a neve ígért.

Két, egymástól független beállítás marad tehát a rácson:

| beállítás | mit rendez | honnan állítható |
|---|---|---|
| `folderPhotoSort` (ez a szelet) | a mappa KÉPEIT | mappa-jobbklikk ▸ Mappa rendezésének alapja |
| `folderSort` (#321) | a MAPPÁK sorrendjét | Mappa ▸ Rendezés |

#1454: a `folderSort` sora korábban a Nézet ▸ Mappanézet menüre
mutatott. Az az almenü az eredetiben NEM rendez, hanem a bal hasáb
szerkezetét állítja (`docs/specs/picasa-mappanezet.md`) — a mappák
sorrendje a Mappa ▸ Rendezés és a bal hasáb helyi menüje alatt van.

A tényleges átrendezést a `PhotoGridModel` végzi (`photo_sort.sort_folder_blocks`),
mert a rács sorrendje a modellé; ez a szelet a BEÁLLÍTÁST tartja, menti és
tolja a modellbe.

A szelet az `AppearanceMixin`-en át kapcsolódik az `AppController`-hez (a
bázislista a forró `controller.py`-ban él, amihez nem nyúlunk) — ugyanaz a
minta, ahogy a `CollageMixin` is magával hozza a saját szeleteit.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import logging

from PySide6.QtCore import Property, Signal, Slot

from picasapy.color import avgcolor_to_rgb, pixel_hue
from picasapy.index import open_index
from picasapy.index.colors import load_avgcolors

from picasapy.ini.io import IniConflictError

from .kezi_sorrend import (
    atrendezett_prioritasok,
    ellenorizd_az_egy_mappat,
    mappa_prioritasai,
    mentsd_a_prioritasokat,
)
from .photo_sort import (
    FOLDER_PHOTO_SORT_KEY,
    FOLDER_PHOTO_SORT_REVERSE_KEY,
    SORT_MODES,
    coerce_reverse_flag,
    coerce_sort_mode,
)


class FolderPhotoSortMixin:
    """A mappán belüli képsorrend — perzisztens, jelzéssel a QML-pipáknak."""

    folderPhotoSortChanged = Signal()

    def _init_folder_photo_sort(self) -> None:
        """Az `AppearanceMixin._init_appearance()` hívja (a mixinek nem
        definiálnak saját `__init__`-et — a repó konvenciója)."""
        settings = self._get_settings()
        self._folder_photo_sort = coerce_sort_mode(
            settings.value(FOLDER_PHOTO_SORT_KEY)
        )
        self._folder_photo_sort_reverse = coerce_reverse_flag(
            settings.value(FOLDER_PHOTO_SORT_REVERSE_KEY, False)
        )
        self._apply_folder_photo_sort()

    @Property(str, notify=folderPhotoSortChanged)
    def folderPhotoSort(self) -> str:
        """A mappa KÉPEINEK rendezése: date / name / size."""
        return self._folder_photo_sort

    @Property(bool, notify=folderPhotoSortChanged)
    def folderPhotoSortReverse(self) -> bool:
        """Fordított sorrend — az alapérték mindhárom szempontnál növekvő."""
        return self._folder_photo_sort_reverse

    @Slot(str)
    def setFolderPhotoSort(self, mode: str) -> None:
        """A mappa képsorrendjének váltása; ismeretlen szempont = nincs hatás."""
        if mode not in SORT_MODES or mode == self._folder_photo_sort:
            return
        self._folder_photo_sort = mode
        self._get_settings().setValue(FOLDER_PHOTO_SORT_KEY, mode)
        self._apply_folder_photo_sort()
        self.folderPhotoSortChanged.emit()
        self._refresh_view()

    @Slot()
    def toggleFolderPhotoSortReverse(self) -> None:
        """A „Fordított sorrend" tétel: a kiválasztott szempont megfordítása."""
        self._folder_photo_sort_reverse = not self._folder_photo_sort_reverse
        self._get_settings().setValue(
            FOLDER_PHOTO_SORT_REVERSE_KEY,
            "true" if self._folder_photo_sort_reverse else "false",
        )
        self._apply_folder_photo_sort()
        self.folderPhotoSortChanged.emit()
        self._refresh_view()

    def _apply_folder_photo_sort(self) -> None:
        """A beállítás átadása a rács-modellnek.

        A hatókör-őr itt van: a rendezés CSAK a mappa-feedben él. A keresési
        találatok sorindexeit a `search_results.groups_to_qml` a rendezetlen
        rekordokból számolja, az albumok sorrendje pedig a felhasználóé —
        ezekbe a nézetekbe a mappa-menü nem szólhat bele.

        A rács-modell hiánya nem hiba: a szeletet ÖNMAGÁBAN példányosító
        próbáknak (`test_appearance_controller.py`) nincs rácsuk. A valódi
        `AppController`-ben a modell már az `__init__` elején elkészül, jóval
        a `_init_appearance()` előtt — hogy ott tényleg megérkezik-e a
        beállítás, azt az integrációs őr méri
        (`tests/app/test_folder_photo_sort_1436.py`).
        """
        grid = getattr(self, "_photos", None)
        if grid is None:
            return
        grid.set_folder_photo_sort(
            self._folder_photo_sort,
            self._folder_photo_sort_reverse,
            is_active=lambda: getattr(self, "_view_mode", ("", ""))[0] == "folder",
            hues=self._folder_photo_hues,
            prioritasok=self._folder_photo_prioritasok,
        )

    def _folder_photo_prioritasok(self, records) -> dict:
        """#1721: (mappa, fájlnév) → kézi hely, a mappák `.picasa.ini`-jéből.

        Mappánként EGY olvasás (a rács több mappa futamait is mutatja), és
        minden hiba üres szótárra fut: a rács sosem ürülhet ki egy
        olvashatatlan ini miatt — ilyenkor a mappa fájlnév-sorrendben áll.
        A modell csak `priority` szempontnál hívja.
        """
        prioritasok: dict = {}
        for mappa in dict.fromkeys(r.folder_path for r in records):
            for nev, ertek in mappa_prioritasai(mappa).items():
                prioritasok[(mappa, nev)] = ertek
        return prioritasok

    @Slot("QVariantList", int)
    def reorderPhotos(self, rows, target_row: int) -> None:
        """A rácson húzással átrendezett képek kézi sorrendjének mentése.

        `rows`: a MOZGATOTT képek sorindexei (a kijelölés), `target_row`: a
        beszúrás helye — ELÉ kerül a blokk. A `-1` a mappa végét jelenti.

        Három dolgot tesz, ebben a sorrendben:

        1. kiszámolja az új sorrendet a mappa MAI (megjelenített) rendjéből;
        2. kiírja a szükséges `priority=` kulcsokat (ld. `kezi_sorrend`);
        3. a rendezést „kézi sorrend"-re állítja.

        ⚠️ A 3. lépés SAJÁT döntés, és kimondva: ha a felhasználó név szerint
        rendezett rácson húz, a művelet látszólag visszaugrana, mert a
        megjelenítést továbbra is a név adná. A húzás szándéka viszont
        egyértelműen a kézi sorrend — ezért váltunk rá.

        Mappahatárt nem lép át (#1219): ha a kijelölés több mappát érint, a
        művelet ELMARAD, és semmit nem írunk.
        """
        grid = getattr(self, "_photos", None)
        if grid is None:
            return
        osszes = list(getattr(grid, "_photos", ()) or ())
        indexek = [int(i) for i in rows if 0 <= int(i) < len(osszes)]
        if not indexek or not osszes:
            return
        mozgatott_kepek = [osszes[i] for i in sorted(indexek)]
        mappa = ellenorizd_az_egy_mappat(mozgatott_kepek)
        if mappa is None:
            return

        mappa_kepei = [kep for kep in osszes if kep.folder_path == mappa]
        mozgatott_nevek = {kep.name for kep in mozgatott_kepek}
        cel_kep = (
            osszes[target_row]
            if 0 <= int(target_row) < len(osszes)
            else None
        )
        uj_sorrend = _uj_nevsorrend(mappa_kepei, mozgatott_nevek, cel_kep)

        ertekek = atrendezett_prioritasok(
            uj_sorrend, mappa_prioritasai(mappa), mozgatott_nevek
        )
        try:
            mentsd_a_prioritasokat(mappa, ertekek)
        except (OSError, IniConflictError) as hiba:
            _log.warning("a kézi sorrend mentése nem sikerült: %s", hiba)
            return
        if self._folder_photo_sort != "priority":
            self.setFolderPhotoSort("priority")
        else:
            self._apply_folder_photo_sort()
            self._refresh_view()

    def _folder_photo_hues(self, records) -> dict:
        """#467: fájl-azonosság → színezet a szín-rendezéshez.

        A #383 átlagszín-indexéből (`photo_colors.avgcolor`) olvas, és a MÉRT
        színezet-számítással (`color.pixel_hue`) alakítja rendezhető értékké.
        A telítetlen képek `None`-t kapnak — a rendező azokat a színesek után
        teszi; ami az indexben nincs meg, az ki sem kerül a szótárból, és a
        lista végére esik.

        A modell csak `color` szempontnál hívja, tehát a többi rendezés nem
        nyit indexet. Index-hiba esetén ÜRES szótárat adunk: a rendezés
        ilyenkor fájlnév-sorrendre esik vissza — a rács sosem ürül ki egy
        adatbázis-hiba miatt."""
        db_path = getattr(self, "_db_path", None)
        if db_path is None or not records:
            return {}
        kulcsok = [
            (str(Path(r.folder_path) / r.name), r.mtime_ns, r.size) for r in records
        ]
        try:
            with open_index(db_path) as conn:
                nyers = load_avgcolors(conn, kulcsok)
        except sqlite3.Error:
            return {}
        hues: dict = {}
        for kulcs, avgcolor in nyers.items():
            hues[kulcs] = pixel_hue(*avgcolor_to_rgb(avgcolor))
        return hues


_log = logging.getLogger(__name__)


def _uj_nevsorrend(mappa_kepei, mozgatott_nevek, cel_kep) -> list[str]:
    """A mappa fájlnevei a húzás UTÁNI sorrendben.

    A mozgatott képek a cél ELÉ kerülnek, a mai relatív sorrendjüket
    megtartva; `cel_kep = None` (vagy a mappán kívüli cél) esetén a mappa
    VÉGÉRE. A cél maga sosem része a mozgatott blokknak — ha mégis az lenne,
    a beszúrás helye a következő nem mozgatott kép.
    """
    maradek = [kep.name for kep in mappa_kepei if kep.name not in mozgatott_nevek]
    blokk = [kep.name for kep in mappa_kepei if kep.name in mozgatott_nevek]
    if cel_kep is None or cel_kep.folder_path != mappa_kepei[0].folder_path:
        return maradek + blokk
    if cel_kep.name in maradek:
        hely = maradek.index(cel_kep.name)
    else:
        hely = len(maradek)
    return maradek[:hely] + blokk + maradek[hely:]
