"""A Létrehozás kollázshoz tartozó QML-felülete (#6252)."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot
from picasapy.app.collage_preview import CollagePreviewProvider
from picasapy.collage.picasa_render import PicasaCollageSettings
from picasapy.collage.themes import NOBORDER

class _LegacyCollageCall:
    """A régi modul patchpontjának futásidejű továbbítása."""

    def __call__(self, *args, **kwargs):
        legacy = import_module("picasapy.app.create_controller")
        return legacy._collage_call(*args, **kwargs)


_collage_call = _LegacyCollageCall()

class _LegacyAttribute:
    """Egy régi modulnév futásidejű, patchbarát továbbítása."""

    def __init__(self, name: str) -> None:
        self.name = name

    def _value(self):
        legacy = import_module("picasapy.app.create_controller")
        return getattr(legacy, self.name)

    def __getattr__(self, name: str):
        return getattr(self._value(), name)

    def __call__(self, *args, **kwargs):
        return self._value()(*args, **kwargs)


# A régi modulnevek futásidőben oldódnak fel, ezért a create_controller patchjei
# a már kiszervezett metódusokban is érvényben maradnak.
collage_output = _LegacyAttribute("collage_output")
collage_prefs = _LegacyAttribute("collage_prefs")
discard_autosave = _LegacyAttribute("discard_autosave")
has_recoverable_draft = _LegacyAttribute("has_recoverable_draft")
logger = _LegacyAttribute("logger")
project_from_nodes = _LegacyAttribute("project_from_nodes")
recover_orphan_draft = _LegacyAttribute("recover_orphan_draft")
write_autosave = _LegacyAttribute("write_autosave")


class _CreateCollageMixin:
    """A CreateMixin kollázs-piszkozata, előnézete és műveletei."""

    collageFinished = Signal(str, int, int, int)

    collageFailed = Signal(str)

    collagePreviewReady = Signal(int)

    collagePreviewFailed = Signal(str)

    collageDraftAvailableChanged = Signal()

    def _ensure_collage_wired(self) -> None:
        """Lusta, egyszeri állapot-inicializálás (a `TrayMixin.
        _ensure_tray_wired` mintája) — a `controller.py` FORRÓ FÁJL, ezért a
        szelet a saját állapotát maga hozza létre, nem az `__init__`-ben.
        """
        if getattr(self, "_collage_wired", False):
            return
        self._collage_wired = True
        self._collage_preview = CollagePreviewProvider()
        self._collage_preview_revision = 0
        self._collage_seed = 0

    @property
    def collage_preview_provider(self) -> CollagePreviewProvider:
        """A képszolgáltató, amit az `application.py` regisztrál."""
        self._ensure_collage_wired()
        return self._collage_preview

    def _collage_draft_dir(self) -> Path:
        """A piszkozat mappája: a „Kollázsok" album (spec 1.5).

        A piszkozatnak RÖGZÍTETT helye kell legyen: az összeomlás utáni
        felajánlás akkor is meg kell találja, ha a felhasználó a célfájlt
        még ki sem választotta."""
        return collage_output.output_dir(
            self._get_settings().value(collage_prefs.OUTPUT_DIR_KEY)
        )

    def _save_collage_draft(self, nodes, settings: PicasaCollageSettings) -> None:
        """A vászon csomópontjaiból piszkozat a lemezre, atomi írással.

        Csomópont nélkül (Többszörös exponálás) NEM ír: kitalált geometria
        rosszabb volna a semminél. A hiba nyelt — a piszkozat baja sosem
        viheti el a felhasználó kollázsát."""
        if not nodes:
            return
        try:
            write_autosave(
                self._collage_draft_dir(), project_from_nodes(nodes, settings)
            )
        except (OSError, ValueError) as hiba:
            logger.warning("A kollázs-piszkozat nem írható: %s", hiba)
            return
        self.collageDraftAvailableChanged.emit()

    def _drop_collage_draft(self) -> None:
        """A piszkozat eldobása — sikeres mentés után, vagy ha a felhasználó
        nemet mond a visszaállításra."""
        if discard_autosave(self._collage_draft_dir()):
            self.collageDraftAvailableChanged.emit()

    @Property(bool, notify=collageDraftAvailableChanged)
    def collageDraftAvailable(self) -> bool:  # noqa: N802 (QML-stílusú név)
        """Van-e ÉP, visszaállítható kollázs-piszkozat.

        A QML ezen a property-n át tudja felajánlani a visszaállítást
        induláskor (spec 1.5, `collage::recoveredautosave`). Szándékosan a
        tényleges beolvasással válaszol: sérült piszkozatot felajánlani
        rosszabb, mint nem felajánlani semmit."""
        return has_recoverable_draft(self._collage_draft_dir())

    @Slot()
    def refreshCollageDraft(self) -> None:  # noqa: N802 (QML-stílusú név)
        """A felajánlás újraértékelése (pl. induláskor, a felület
        felépülése után)."""
        self.collageDraftAvailableChanged.emit()

    @Slot()
    def discardCollageDraft(self) -> None:  # noqa: N802 (QML-stílusú név)
        """A felhasználó nemet mond a visszaállításra (#979).

        ⚠️ **Ez NEM törlés.** Az eredeti Picasa az elárvult automentést
        nem dobja el, hanem ÁTNEVEZI („Helyreállított automatikus
        másolat") és indexeli, hogy a felhasználó megtalálja a Kollázsok
        albumban (spec 9.2/b, `0x008419e0`). A munkája így akkor sem
        vész el, ha a felajánlásra nemet mondott — meggondolhatja magát.

        A mentés utáni eldobás (`_drop_collage_draft`) továbbra is
        TÖRLÉS: ott a piszkozat betöltötte a szerepét, és a megőrzése
        csak szemetelne.

        ⚠️ Az eredeti mindezt INDULÁSKOR, kérdés nélkül teszi. Nálunk van
        egy felajánlás-lépés (#1064), ami az eredetiben nincs; ha
        induláskor neveznénk át, a felajánlásnak nem maradna mit
        felajánlania. Ezért a „nem" ágra kötjük — a végeredmény ugyanaz:
        a piszkozat megmarad, néven nevezve.
        """
        uj_ut = recover_orphan_draft(self._collage_draft_dir())
        if uj_ut is not None:
            self.collageDraftAvailableChanged.emit()

    def _selected_sources(self, rows) -> tuple[Path, ...]:
        """A kijelölt sorokból forrás-útvonalak, a rács sorrendjében."""
        return _collage_call("_selected_sources", self, rows)

    def _tray_sources(self) -> tuple[Path, ...]:
        """A KÉPTÁLCA tartalma forrás-útvonalként, beszúrási sorrendben
        (#455, 3. teendő).

        Az eredetiben a tálca alatti műveletsor a tálca tartalmán futott,
        nem a pillanatnyi kijelölésen. A tálca mappákon átnyúlik, ezért itt
        nem rács-sorokból, hanem a `heldPaths`-ből dolgozunk — az a globális
        indexből olvas, és az időközben eltűnt képeket kihagyja.
        """
        return _collage_call("_tray_sources", self)

    def _sources_for(self, rows) -> tuple[Path, ...]:
        """A művelet forrása: a TÁLCA, ha van benne kép; egyébként a
        kijelölés (így az üres tálcás, mai viselkedés nem romlik el)."""
        return _collage_call("_sources_for", self, rows)

    @Slot(list, str, str)
    def requestCollagePreview(self, rows, kind: str, border: str = NOBORDER) -> None:
        """#920: élő előnézet a jelenlegi beállításokkal, háttérszálon.

        A Kollázs eddig VAKON dolgozott: a felhasználó választott, a program
        fájlba renderelt, és csak utána derült ki, mit kapott. Az eredetiben
        a panel jobb oldalán élő vászon áll.

        Az előnézet szándékosan KICSI (`_PREVIEW_SIZE`): a Képkupac pakolója
        időkorlátos keresést futtat, és a teljes felbontású renderelés minden
        csúszka-mozdulatnál használhatatlanná tenné a felületet.
        """
        return _collage_call("requestCollagePreview", self, rows, kind, border)

    @Slot()
    def shuffleCollage(self) -> None:
        """#920: a két véletlenszerűsítő gomb magja — új elrendezés ugyanazokból
        a képekből. A Képkupac szórása és a Mozaik pakolója is a magból dolgozik.
        """
        return _collage_call("shuffleCollage", self)

    @property
    def collageSeed(self) -> int:
        self._ensure_collage_wired()
        return self._collage_seed

    @Slot(list, str, str)
    @Slot(list, str, str, str)
    def makeCollage(self, rows, kind: str, target_url: str, border: str = NOBORDER) -> None:
        """Kollázs a kijelölt képekből a megadott célfájlba (JPEG).

        `kind`: a `picasapy.collage.themes.COLLAGE_THEMES` egyike — a HAT
        Picasa-elrendezés. `border`: a `BORDER_THEMES` egyike.

        **#431: ez a slot a #29-es, saját tervezésű négy elrendezésről a
        Picasa-hű hatra állt át.** A mag (`picasa_render`) 2026-08-16 óta
        készen állt, de senki nem hívta — a felület a régi rajzolót
        használta, tehát a kollázs működött, csak nem a Picasa
        elrendezéseivel.
        """
        return _collage_call("makeCollage", self, rows, kind, target_url, border)
