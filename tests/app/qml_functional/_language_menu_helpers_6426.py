"""Segéd a lustán létrehozott nyelvmenü felépítéséhez a menübejáróban."""

from __future__ import annotations

import shiboken6
from PySide6.QtCore import QObject

from tests.app.qml_functional._fomenu_4420_menu import _varj


def _aktivald_nyelv_almenut(ablak, qt_app, magassag: int) -> None:
    """A menübejáró statikus menülistájához hozza létre a nyelvi tételeket.

    A kattintásos működést a `test_language_menu_lazy_6426.py` méri. A régi
    teljesmenü-bejáró viszont zárt almenü mellett gyűjti ki az összes útvonalat;
    ott az Instantiator aktiválása elég, a tényleges kattintást minden útvonalnál
    maga a bejáró végzi.
    """
    ablak.setHeight(magassag)
    assert _varj(qt_app, lambda: ablak.height() == magassag), (
        f"az ablak magassága nem állt be a {magassag} px értékre"
    )
    nyelv_menu = ablak.findChild(QObject, "menuToolsLanguage")
    assert nyelv_menu is not None, "a nyelv-almenü hiányzik"
    assert nyelv_menu.setProperty("additionalLanguageItemsActive", True), (
        "a nyelv-almenü lustasági kapcsolója nem állítható"
    )
    tovabbi = ablak.findChild(QObject, "menuLanguageAdditionalChoices")
    assert tovabbi is not None
    assert _varj(qt_app, lambda: int(tovabbi.property("count")) == 39), (
        "a nyelv-almenü további elemei nem aktiválódtak"
    )
    assert shiboken6.isValid(ablak), "a nyelvmenü aktiválása törölte a főablakot"
