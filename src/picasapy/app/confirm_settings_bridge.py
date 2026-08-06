"""#367: vékony QML-híd a `confirm_settings.py` fölött.

Az általános `ConfirmDialog.qml` ezen a `confirmSettings` context property-n
keresztül olvassa/írja a „Ne kérdezze újra" jelölő állapotát döntés-
kulcsonként. A tényleges logika a `confirm_settings.py`-ban él (tesztelhető,
QSettings-injektálható); ez a modul csak QML-ből hívható metódusokká
csomagolja.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QSettings, Slot

from picasapy.app.confirm_settings import (
    is_confirm_suppressed,
    set_confirm_suppressed,
)


class ConfirmSettingsBridge(QObject):
    """QML-ből hívható wrapper a döntés-kulcsonkénti „ne kérdezze újra"
    állapothoz. `settings=None` esetén a valós alkalmazás közös
    `QSettings("PicasaPy", "PicasaPy")`-jét használja (lusta létrehozással,
    az `AppController._get_settings()` mintájára); tesztekhez injektálható
    elszigetelt `QSettings`."""

    def __init__(self, settings: QSettings | None = None, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings

    def _get_settings(self) -> QSettings:
        if self._settings is None:
            self._settings = QSettings("PicasaPy", "PicasaPy")
        return self._settings

    @Slot(str, result=bool)
    def isSuppressed(self, decision_key: str) -> bool:
        return is_confirm_suppressed(self._get_settings(), decision_key)

    @Slot(str, bool)
    def setSuppressed(self, decision_key: str, remember: bool) -> None:
        set_confirm_suppressed(self._get_settings(), decision_key, remember)
