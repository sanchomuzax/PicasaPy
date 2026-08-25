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

from PySide6.QtCore import Property, Signal, Slot

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
        )
