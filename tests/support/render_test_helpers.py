"""Közös, gépfüggetlen alapok a képpontos QML-render tesztekhez."""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator

from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication
from PySide6.QtQuick import QQuickItem

from tests.support.betucsalad import BETU_FORRAS

TEXT_ITEM_CLASS_NAMES = ("QQuickText", "QQuickTextInput", "QQuickTextEdit")


def is_text_item(item: QQuickItem) -> bool:
    """Felirat, beviteli mező vagy helyőrző az öröklési lánca alapján."""
    return any(item.inherits(name) for name in TEXT_ITEM_CLASS_NAMES)


@contextmanager
def rogzitett_betu_context() -> Iterator[None]:
    """A QML-szöveghez a csomagolt Open Sans betűt állítja be."""
    azonosito = QFontDatabase.addApplicationFont(str(BETU_FORRAS))
    assert azonosito >= 0, "a csomagolt betű nem tölthető be"
    csalad = QFontDatabase.applicationFontFamilies(azonosito)[0]
    eredeti = QGuiApplication.font()
    rogzitett = QFont(eredeti)
    rogzitett.setFamilies([csalad])
    QGuiApplication.setFont(rogzitett)
    QFont.insertSubstitution("Georgia", csalad)
    try:
        yield
    finally:
        QFont.removeSubstitutions("Georgia")
        QGuiApplication.setFont(eredeti)
        QFontDatabase.removeApplicationFont(azonosito)
