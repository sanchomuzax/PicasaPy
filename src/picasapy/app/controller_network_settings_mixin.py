"""A hálózati naplózás és a feltöltési méret QML-beállításai."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Property, Slot
from picasapy import network_log, web_upload_size
from .controller_signals import AppControllerSignalsMixin as _Signals

class NetworkSettingsMixin:
    """A hálózati naplózás és a feltöltési méret QML-beállításai."""

    @Property(int, notify=_Signals.statusChanged)
    def networkLogLevel(self) -> int:  # noqa: N802
        """A hálózati napló szintje (0-4); az eredeti `LogLevel` kulcs, alapértéke 2."""
        return network_log.read_level(self._get_settings().value("Preferences/LogLevel"))

    @Slot(int)
    def setNetworkLogLevel(self, value: int) -> None:  # noqa: N802
        self._get_settings().setValue(
            "Preferences/LogLevel", network_log.clamp_level(value)
        )
        self._apply_network_log()
        self.statusChanged.emit()

    @Property(str, constant=True)
    def networkLogFile(self) -> str:  # noqa: N802
        """A naplófájl rögzített helye: az adatkönyvtárban, `network.log` néven."""
        return str(Path(self._db_path).parent / network_log.NAPLO_FAJLNEV)

    def _apply_network_log(self) -> None:
        """A mentett szintet a futó naplózóra alkalmazza, a naplófájllal együtt."""
        network_log.configure(self.networkLogLevel, Path(self.networkLogFile))

    @Property(int, notify=_Signals.statusChanged)
    def webUploadSizeIndex(self) -> int:  # noqa: N802
        """A webalbum-feltöltési méret legördülő-indexe (0-4); hiányzó kulcsnál az 1600 (2)."""
        return web_upload_size.read_index(
            self._get_settings().value(web_upload_size.KULCS)
        )

    @Slot(int)
    def setWebUploadSizeIndex(self, index: int) -> None:  # noqa: N802
        self._get_settings().setValue(
            web_upload_size.KULCS, web_upload_size.size_at(index)
        )
        self.statusChanged.emit()
