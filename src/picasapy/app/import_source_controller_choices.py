"""Az import megjegyzett választásai és a törölhető forrás vizsgálata (#7183).

Az eredeti Picasa az import INDÍTÁSAKOR menti az almappa-módot
(`acquireUseSubFolder`, `0x00525400`) és a törlési módot
(`acquireCleanCard`, `0x0051a0c2`); az alapérték mindkettőnél 0: kézi cím,
illetve `Leave card alone` (`0x00514180`, `0x00519560`). Olvasáskor a 2
(összes törlése) az 1-re (csak a másolt) esik vissza.

A törlési mód csak törölhető forrásnál él: a csatolt meghajtó gyökerében
`DCIM` mappa van (`0x0050f590` → `0x0050f6a0`). Ezt a vizsgálatot a QML nem
tudja elvégezni, ezért az `isDeletableSource` slot adja.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Property, Signal, Slot

from picasapy.importsource import NAMING_MANUAL

from .formatting import to_local_path
from .import_source_controller_state import (
    AFTER_COPY_DELETE_ALL,
    AFTER_COPY_DELETE_COPIED,
    AFTER_COPY_LEAVE,
    _VALID_AFTER_COPYING,
    _VALID_NAMING_MODES,
)

NAMING_MODE_SETTINGS_KEY = "import/namingmode"
AFTER_COPYING_SETTINGS_KEY = "import/aftercopying"

_DCIM_NAME = "dcim"


def has_dcim_folder(root_path: str) -> bool:
    """Van-e a `root_path` gyökerében `DCIM` mappa (kis-nagybetű mindegy)?

    Csak a gyökér közvetlen elemeit listázza, bejárás nélkül; olvashatatlan
    vagy nem létező útvonalra `False`."""
    try:
        with os.scandir(root_path) as entries:
            return any(
                entry.name.casefold() == _DCIM_NAME and entry.is_dir()
                for entry in entries
            )
    except OSError:
        return False


class ImportSourceControllerChoicesMixin:
    """A megjegyzett almappa-mód és törlési mód, plusz a törölhető forrás."""

    importChoicesChanged = Signal()

    @Property(str, notify=importChoicesChanged)
    def namingMode(self) -> str:  # noqa: N802 — QML property-konvenció
        """A legutóbb indított import almappa-módja; üres profilban kézi cím."""
        stored = str(
            self._get_settings().value(NAMING_MODE_SETTINGS_KEY, NAMING_MANUAL)
        )
        return stored if stored in _VALID_NAMING_MODES else NAMING_MANUAL

    @Property(str, notify=importChoicesChanged)
    def afterCopying(self) -> str:  # noqa: N802 — QML property-konvenció
        """A legutóbb indított import törlési módja.

        Üres profilban `Leave`; a tárolt „összes törlése” (az eredeti `2`)
        olvasáskor „csak a másolt törlése” módra esik vissza."""
        stored = str(
            self._get_settings().value(AFTER_COPYING_SETTINGS_KEY, AFTER_COPY_LEAVE)
        )
        if stored == AFTER_COPY_DELETE_ALL:
            return AFTER_COPY_DELETE_COPIED
        return stored if stored in _VALID_AFTER_COPYING else AFTER_COPY_LEAVE

    def _remember_import_choices(self, naming_mode: str, after_copying: str) -> None:
        """Az import INDÍTÁSAKOR hívódik; csak érvényes értéket ment."""
        settings = self._get_settings()
        if naming_mode in _VALID_NAMING_MODES:
            settings.setValue(NAMING_MODE_SETTINGS_KEY, naming_mode)
        if after_copying in _VALID_AFTER_COPYING:
            settings.setValue(AFTER_COPYING_SETTINGS_KEY, after_copying)
        self.importChoicesChanged.emit()

    @Slot(str, result=bool)
    def isDeletableSource(self, path: str) -> bool:  # noqa: N802
        """A forrás gyökerében van `DCIM` mappa, tehát a törlési mód élhet?

        A hívó dönti el, hogy a forrás a csatolt meghajtók listájából jött-e;
        mappa-, fájl- és előzményforrás sosem törölhető."""
        local = to_local_path(path)
        return bool(local) and has_dcim_folder(local)
