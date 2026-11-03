"""Képernyő-munkaterület lekérdezése a Picasa értesítősávjához."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRect, Slot
from PySide6.QtGui import QGuiApplication


class NotifierScreenGeometry(QObject):
    """A QML képernyőneve alapján visszaadja a képernyő munkaterületét."""

    @Slot(str, result=QRect)
    def availableGeometryForName(self, screen_name: str) -> QRect:
        application = QGuiApplication.instance()
        if application is None:
            return QRect()
        for screen in application.screens():
            if screen.name() == screen_name:
                return screen.availableGeometry()
        return QRect()
