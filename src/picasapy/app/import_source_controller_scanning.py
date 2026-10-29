"""Az importforrás-vezérlő háttérszálas szkennelése és előnézete."""

from __future__ import annotations

from PySide6.QtCore import Slot


def _controller_module():
    """A régi modulon keresztül feloldott függőségek a monkeypatch-célpontokhoz."""
    from . import import_source_controller

    return import_source_controller


class ImportSourceControllerScanningMixin:
    """Forrásmappák és kiválasztott fájlok háttérszálas beolvasása."""

    # -- forrás-szkennelés ---------------------------------------------------

    @Slot(result=str)
    def wipeCardWarning(self) -> str:  # noqa: N802 — QML-stílus
        """A „minden fájl törlése a forrásról" ÖSSZEÁLLÍTOTT figyelmeztetése.

        Az eredeti hét erőforrás-darabból fűzi össze (#860,
        `wipe_card_warning`); a darabszámokat a legutóbbi pásztázásból
        vesszük. Ha még nem pásztáztunk, a szöveg ezt KIMONDJA, nem
        találgat számot."""
        controller = _controller_module()
        return controller.wipe_card_warning(
            controller.WipeCardFacts(
                scan_done=self._unrecognized >= 0,
                total=len(self._candidates) + max(0, self._unrecognized),
                duplicates=len(self._duplicate_paths),
                unrecognized=max(0, self._unrecognized),
            )
        )

    @Slot(str, result=bool)
    def isValidFolderName(self, name: str) -> bool:  # noqa: N802
        """#4837: a kézi importmappanév érvényes-e (a QML az Import gomb
        tiltásához használja)."""
        return _controller_module().is_valid_folder_name(name)
