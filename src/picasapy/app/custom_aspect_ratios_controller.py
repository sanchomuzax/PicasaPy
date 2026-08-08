"""Egyéni vágás-képarányok — controller-szelet (#448).

Mixin-osztály (a `custom_collections_controller.CustomCollectionsMixin`
mintájára): a végleges `AppController` örökli. A `self._get_settings()`-t
használja (minden AppController-példányon elérhető, ld. `controller.py`) —
a tényleges adatok a `custom_aspect_ratios` modul tiszta függvényein át,
JSON-szerializált QSettings-kulcsok alatt élnek."""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

from .custom_aspect_ratios import (
    CUSTOM_ASPECT_RATIOS_SETTING_KEY,
    LAST_CROP_RATIO_SETTING_KEY,
    CustomAspectRatio,
    add_custom_aspect_ratio,
    delete_custom_aspect_ratio,
    parse_custom_aspect_ratios,
    serialize_custom_aspect_ratios,
)

#: Alapértelmezett `lastCropRatio` — a beépített preset-lista "Manual"
#: (szabad vágás) kulcsa, ha még soha nem mentettünk mást.
_DEFAULT_LAST_CROP_RATIO = "Manual"


class CustomAspectRatiosMixin:
    """Egyéni képarányok: felvétel, törlés + a legutóbb használt arány
    (`lastCropRatio`) megjegyzése/visszaadása."""

    customAspectRatiosChanged = Signal()
    lastCropRatioChanged = Signal()

    @Property("QVariant", notify=customAspectRatiosChanged)
    def customAspectRatios(self) -> list[dict]:
        """A QML-nek adott alakja: `[{name, width, height}, ...]` — mindig
        `list`/`dict` (a projekt szabálya, sosem `tuple`)."""
        return [
            {"name": r.name, "width": r.width, "height": r.height}
            for r in self._load_custom_aspect_ratios()
        ]

    def _load_custom_aspect_ratios(self) -> tuple[CustomAspectRatio, ...]:
        raw = self._get_settings().value(CUSTOM_ASPECT_RATIOS_SETTING_KEY)
        return parse_custom_aspect_ratios(raw)

    def _save_custom_aspect_ratios(
        self, ratios: tuple[CustomAspectRatio, ...]
    ) -> None:
        self._get_settings().setValue(
            CUSTOM_ASPECT_RATIOS_SETTING_KEY, serialize_custom_aspect_ratios(ratios)
        )
        self.customAspectRatiosChanged.emit()

    @Slot(float, float, str)
    def addCustomAspectRatio(self, width: float, height: float, name: str) -> None:
        """Új egyéni arány — érvénytelen méretet/üres nevet csendben
        elutasítja (ld. `custom_aspect_ratios.add_custom_aspect_ratio`)."""
        current = self._load_custom_aspect_ratios()
        self._save_custom_aspect_ratios(
            add_custom_aspect_ratio(current, width, height, name)
        )

    @Slot(str, float, float)
    def deleteCustomAspectRatio(self, name: str, width: float, height: float) -> None:
        current = self._load_custom_aspect_ratios()
        self._save_custom_aspect_ratios(
            delete_custom_aspect_ratio(current, name, width, height)
        )

    # -- lastCropRatio (#448): a legutóbb kiválasztott arány kulcsa -------

    @Property(str, notify=lastCropRatioChanged)
    def lastCropRatio(self) -> str:
        """A legutóbb kiválasztott arány kulcsa — beépített preset "key"-je
        (pl. "4x6") vagy egyéni arány "custom:<név>:<szxmag>" alakja (ld.
        EditorPanel.qml aspectList). Alapértelmezés: "Manual"."""
        value = self._get_settings().value(
            LAST_CROP_RATIO_SETTING_KEY, _DEFAULT_LAST_CROP_RATIO
        )
        return value if isinstance(value, str) and value else _DEFAULT_LAST_CROP_RATIO

    @Slot(str)
    def setLastCropRatio(self, key: str) -> None:
        if not key or key == self.lastCropRatio:
            return
        self._get_settings().setValue(LAST_CROP_RATIO_SETTING_KEY, key)
        self.lastCropRatioChanged.emit()
