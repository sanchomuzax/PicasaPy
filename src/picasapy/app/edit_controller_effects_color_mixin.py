"""A színválasztó MRU-listája, a színpipetták és a szín-varázspálca (#6267)."""

from __future__ import annotations

from .edit_controller_shared import (
    _PICKER_COLOR_PATTERN,
    _PICKER_MRU_SETTINGS_KEYS,
    Property,
    Slot,
    estimate_neutral_color,
)
from .edit_controller_signals import EditControllerSignalsMixin as _Signals


class EditControllerEffectsColorMixin:
    """A színválasztó, a színpipetták és a szín-varázspálca (#6267)."""

    @Property("QVariantList", notify=_Signals.pickerRecentColorsChanged)
    def recentPickerColors(self) -> list[str]:
        """A színválasztó öt MRU-rekesze (`picker/mru_0` a legfrissebb)."""
        return [
            str(self._picker_settings.value(key, "") or "")
            for key in _PICKER_MRU_SETTINGS_KEYS
        ]


    @Slot(str)
    def rememberPickerColor(self, color: str) -> None:
        """A választott `#RRGGBB` színt elölre teszi és tartósan elmenti."""
        normalized = str(color).strip().lower()
        if not _PICKER_COLOR_PATTERN.fullmatch(normalized):
            return

        colors = [normalized]
        for previous in self.recentPickerColors:
            previous = str(previous).strip().lower()
            if (
                _PICKER_COLOR_PATTERN.fullmatch(previous)
                and previous not in colors
                and len(colors) < len(_PICKER_MRU_SETTINGS_KEYS)
            ):
                colors.append(previous)

        for index, key in enumerate(_PICKER_MRU_SETTINGS_KEYS):
            self._picker_settings.setValue(
                key, colors[index] if index < len(colors) else ""
            )
        self._picker_settings.sync()
        self.pickerRecentColorsChanged.emit()


    @Slot(float, float, result=bool)
    def pickNeutralColor(self, nx: float, ny: float) -> bool:  # noqa: N802
        """A pipetta (#464): a képre kattintott pont színe lesz a
        finetune2 „semleges szín" paramétere (a lánc 4. paramétere).

        A `finetune2` négy csúszkája változatlan marad — a pipetta csak a
        semleges színt írja át. `False`, ha a pont nem mintavételezhető
        (nincs regisztrált előnézet, vagy a pont a képen kívül esik).
        """
        self._require_active()
        sample = self._provider.sample_color(self._kulcs, nx, ny)
        if sample is None:
            return False
        red, green, blue = sample
        values = self._session.finetune_values()
        self._push_undo("finetune")
        self._session = self._session.set_finetune(
            fill=values.fill if values else 0.0,
            highlights=values.highlights if values else 0.0,
            shadows=values.shadows if values else 0.0,
            temperature=values.temperature if values else 0.0,
            neutral=f"ff{red:02x}{green:02x}{blue:02x}",
        )
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()
        return True


    @Slot(float, float, result=str)
    def pickEffectColor(self, nx: float, ny: float) -> str:  # noqa: N802
        """Az effekt-színparaméter pipettája (#5674): a képre kattintott
        pont színe `#rrggbb` alakban.

        Csak adja vissza a színt: sem láncot, sem ini-t nem ír. A paramétert
        a QML állítja be a `panel.updateParamValue`-n át, így az Alkalmaz/Mégse
        az effekt szokásos útját járja be. Üres sztring, ha a pont nem
        mintavételezhető (nincs aktív szerkesztés, nincs regisztrált előnézet,
        vagy a pont a képen kívül esik).
        """
        sample = self._provider.sample_color(self._kulcs, nx, ny)
        if sample is None:
            return ""
        red, green, blue = sample
        return f"#{red:02x}{green:02x}{blue:02x}"


    @Slot(result=bool)
    def applyColorWand(self) -> bool:  # noqa: N802 — QML-stílusú név
        """A szín-varázspálca (#551): a viszonyítási színt a PROGRAM választja.

        A mérés kimondta, hogy a pálca nem külön szűrő: ugyanabba a
        `finetune2` p4 mezőbe ír, mint a kézi pipetta — a Picasa saját
        `.picasa.ini`-je bizonyítja (`finetune2=1,0,0,0,006b8088,0`). A
        színt a kevéssé telített képpontok átlagából becsüljük
        (`estimate_neutral_color`), a zöldre normálva.

        `False`, ha a forráskép nem olvasható — ilyenkor a lánc érintetlen.
        """
        self._require_active()
        if self._image_path is None:
            return False
        source = self._provider.source_image(self._kulcs, self._image_path)
        if source is None:
            return False
        red, green, blue = estimate_neutral_color(source)
        values = self._session.finetune_values()
        self._push_undo("finetune")
        self._session = self._session.set_finetune(
            fill=values.fill if values else 0.0,
            highlights=values.highlights if values else 0.0,
            shadows=values.shadows if values else 0.0,
            temperature=values.temperature if values else 0.0,
            neutral=f"ff{red:02x}{green:02x}{blue:02x}",
        )
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()
        return True
