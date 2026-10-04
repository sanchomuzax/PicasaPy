"""A webkamera-panel kimeneti útvonalai (#4137).

A képkockák és a klipek a Picasa „Rögzített videoklipek” projektmappájába
kerülnek. A fájlnevek ütközéskor a leírt, kötőjeles, legalább háromjegyű
sorszámot kapják. A mappa `.picasa.ini`-jét kizárólag a meglévő
`movie_output.write_album_ini()` írja, az `ini/` API-n keresztül.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Property, QSettings, Signal, Slot

from .frame_capture_controller import capture_folder
from .movie_output import write_album_ini

logger = logging.getLogger(__name__)

_FAJLTIPUSOK = {
    "snapshot": ("snapshot", ".jpg"),
    # A bináris leírás a webkamerás videó kódolását hatókörön kívül hagyja;
    # a Qt Multimedia hordozható MP4-kimenetéhez ezt a nevet választjuk.
    "video": ("video", ".mp4"),
}
_MAX_EGYEDISETO = 4096
_VIDEO_KITERJESZTESEK = {".avi", ".mkv", ".mov", ".mp4", ".wmv"}


class CameraCaptureController(QObject):
    """A QML médiaobjektumainak biztonságos, Picasa-kompatibilis célmappája."""

    capturePathFailed = Signal(str)
    captureSettingsChanged = Signal()

    def __init__(self, settings: QSettings | None = None, parent=None) -> None:
        super().__init__(parent)
        self._settings = (
            settings if settings is not None else QSettings("PicasaPy", "PicasaPy")
        )

    @Property(str, notify=captureSettingsChanged)
    def captureSize(self) -> str:
        return str(self._settings.value("cameraCapture/size", "640x480"))

    @Property(str, notify=captureSettingsChanged)
    def cameraId(self) -> str:
        return str(self._settings.value("cameraCapture/cameraId", ""))

    @Property(str, notify=captureSettingsChanged)
    def audioId(self) -> str:
        return str(self._settings.value("cameraCapture/audioId", ""))

    @Slot(str)
    def setCaptureSize(self, value: str) -> None:
        if value in {"320x240", "640x480", "800x600", "1280x720"}:
            self._settings.setValue("cameraCapture/size", value)
            self.captureSettingsChanged.emit()

    @Slot(str)
    def setCameraId(self, value: str) -> None:
        self._settings.setValue("cameraCapture/cameraId", value)
        self.captureSettingsChanged.emit()

    @Slot(str)
    def setAudioId(self, value: str) -> None:
        self._settings.setValue("cameraCapture/audioId", value)
        self.captureSettingsChanged.emit()

    @Slot(result="QVariantList")
    def capturedVideos(self) -> list[str]:
        """A rögzített videók közvetlen gyerekei, kiszámítható névsorrendben."""
        try:
            return [
                str(path)
                for path in sorted(
                    (
                        item for item in capture_folder().iterdir()
                        if item.is_file()
                        and item.suffix.casefold() in _VIDEO_KITERJESZTESEK
                    ),
                    key=lambda item: item.name.casefold(),
                )
            ]
        except FileNotFoundError:
            return []
        except OSError as exc:
            logger.exception("#4137: nem olvasható a rögzített videók mappája")
            self.capturePathFailed.emit(str(exc))
            return []

    @Slot(str, result=str)
    def reserveCapturePath(self, kind: str) -> str:
        """Visszaad egy még nem használt fájlnevet a megfelelő médiatípushoz."""
        fajlnev, kiterjesztes = _FAJLTIPUSOK.get(kind, ("", ""))
        if not fajlnev:
            self.capturePathFailed.emit("Ismeretlen kamerafelvétel-típus.")
            return ""

        mappa = capture_folder()
        uj_mappa = not mappa.exists()
        try:
            mappa.mkdir(parents=True, exist_ok=True)
            if uj_mappa:
                write_album_ini(mappa, mappa.name)
            for sorszam in range(1, _MAX_EGYEDISETO + 1):
                cel = mappa / f"{fajlnev}-{sorszam:03d}{kiterjesztes}"
                if not cel.exists():
                    return str(cel)
        except OSError as exc:
            logger.exception("#4137: nem készíthető elő a kamerafelvétel célja")
            self.capturePathFailed.emit(str(exc))
            return ""

        self.capturePathFailed.emit("A mappában elfogyott a szabad fájlnév.")
        return ""


__all__ = ["CameraCaptureController"]
