"""#2998: a címke-panel felülete írásvédett kijelölésnél.

Az eredeti `keywords/readonly_label` szövege szerint egyetlen írásvédett
elem is elég a jelzéshez. A panel ilyenkor NEM engedi a bevitelt — se a
mezőt, se a hozzáadás gombot, se a gyorscímke-gombokat.

A vezérlő-oldalt a `tests/app/test_irasvedett_cimke_2998.py` méri; itt a
kötések a kérdés, a panel közvetlen felépítésével (a `controller`
context property nélkül, a `test_qml_quicktags.py` mintájára).
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem

_QML = Path(picasapy.app.__file__).parent / "qml"


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _nevvel(gyoker, nev: str):
    if (gyoker.objectName() or "") == nev:
        return gyoker
    for it in _walk(gyoker):
        if (it.objectName() or "") == nev:
            return it
    return None


@pytest.fixture
def panel(qt_app):
    motor = QQmlEngine()
    motor.addImportPath(str(_QML))
    komponens = QQmlComponent(
        motor, QUrl.fromLocalFile(str(_QML / "PicasaPy" / "TagsPanel.qml"))
    )
    elem = komponens.create()
    assert elem is not None, komponens.errorString()
    yield elem
    elem.deleteLater()


class TestAPanelKotesei:
    def test_irhato_kijeloles_ENGEDI_a_bevitelt(self, panel):
        panel.setProperty("hasSelection", True)
        panel.setProperty("readOnlySelection", False)
        assert panel.property("cimkezheto") is True
        mezo = _nevvel(panel, "tagInput")
        assert mezo is not None and mezo.property("enabled") is True

    def test_irasvedett_kijeloles_TILTJA_a_bevitelt(self, panel):
        panel.setProperty("hasSelection", True)
        panel.setProperty("readOnlySelection", True)
        assert panel.property("cimkezheto") is False
        mezo = _nevvel(panel, "tagInput")
        assert mezo is not None and mezo.property("enabled") is False

    def test_a_JELZES_csak_irasvedettnel_latszik(self, panel):
        jelzes = _nevvel(panel, "tagsReadOnlyNotice")
        assert jelzes is not None, "nincs meg az írásvédettség-felirat"

        panel.setProperty("hasSelection", True)
        panel.setProperty("readOnlySelection", False)
        assert jelzes.property("visible") is False

        panel.setProperty("readOnlySelection", True)
        assert jelzes.property("visible") is True

    def test_kijeloles_NELKUL_nem_a_jelzes_szol(self, panel):
        """Kijelölés nélkül a régi, kijelölést kérő szöveg a helyes — az
        írásvédettség ott még nem eldönthető."""
        panel.setProperty("hasSelection", False)
        panel.setProperty("readOnlySelection", True)
        assert _nevvel(panel, "tagsReadOnlyNotice").property("visible") is False

    def test_a_felirat_MAGYARUL_jelenik_meg(self, panel, qt_app):
        """A szöveg felhasználónak látszik, tehát a fordítása is kötelező
        (a `.ts` + `pyside6-lrelease` lépés)."""
        from PySide6.QtCore import QTranslator

        forditas = QTranslator()
        assert forditas.load(
            str(Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.qm")
        ), "a picasapy_hu.qm nem tölthető be — lefutott a pyside6-lrelease?"
        magyar = forditas.translate(
            "TagsPanel",
            "Tags cannot be modified because one or more items are read-only.",
        )
        assert magyar and "írásvédett" in magyar, f"nincs magyar fordítás: {magyar!r}"
