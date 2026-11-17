"""#7151: mentés-szűrő módban (`mentesSzuroAktiv`) a mappasor dupla kattintása
NEM nyit Folder Properties ablakot: a sor ott pipa.

A `test_mappa_dupla_kattintas_7151.py` párja. A mentés-módot a VALÓDI úton
nyitjuk (`Eszközök ▸ Képek biztonsági mentése…`, készlet kiválasztása), és a
`test_mentes_fa_kattintas_5210.py` appját és segédeit használjuk.

Üres átmenet ellen: minden próba ELŐTT egy egyszeres kattintás ellenőrzi, hogy
a sor valóban megkapja az egeret (pipálódik), és csak utána jön a dupla
kattintás. Így a „nincs ablak" nem abból áll elő, hogy a kattintás elkerülte
a sort.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.qml_functional.test_mentes_fa_kattintas_5210 import (
    _epitsd_az_appot,
    _fa_latszo,
    _fanezet,
    _latszo,
    _lista,
    _nyisd_a_mentest,
)
from support.qt_wait import varj_feltetelre


@pytest.fixture
def app(qt_app, tmp_path, monkeypatch):
    yield from _epitsd_az_appot(qt_app, tmp_path, monkeypatch)


def _kozep(elem: QQuickItem) -> QPoint:
    os_ = elem
    while os_ is not None:
        os_.ensurePolished()
        os_ = os_.parentItem()
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    return QPoint(round(kozep.x()), round(kozep.y()))


def _kattints(window, qt_app, elem, *, dupla: bool) -> None:
    pont = _kozep(elem)
    QTest.mouseMove(window, pont)
    qt_app.processEvents()
    kattintas = QTest.mouseDClick if dupla else QTest.mouseClick
    kattintas(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _nyitva(window) -> bool:
    dialog = window.findChild(QObject, "folderPropertiesDialog")
    return dialog is not None and dialog.property("opened") is True


def _pipalva(host, ut: str) -> bool:
    return ut in _lista(host.property("pipaltMappak"))


class TestMentesModDuplaKattintas:
    def test_a_lapos_lista_mentetlen_sora_dupla_kattintasra_nem_nyit_ablakot(
        self, app, qt_app
    ):
        window, _c, _e, _v, lib, _cel = app
        host = _nyisd_a_mentest(window, qt_app)
        ut = str(lib / "2024" / "nyaralas")
        sor = [
            e for e in _latszo(window, "folderRowMouse")
            if e.property("folderPath") == ut
        ]
        assert len(sor) == 1, "a mentetlen mappa sora nem látszik a lapos listán"

        _kattints(window, qt_app, sor[0], dupla=False)
        assert varj_feltetelre(
            qt_app, lambda: _pipalva(host, ut)
        ), "a sor nem kapta meg a kattintást: nem pipálódott (üres átmenet)"
        assert not _nyitva(window)

        _kattints(window, qt_app, sor[0], dupla=True)

        assert not _nyitva(window), (
            "mentés-szűrő módban a dupla kattintás megnyitotta a Folder Properties ablakot"
        )

    def test_a_fa_mentetlen_levelsora_dupla_kattintasra_nem_nyit_ablakot(
        self, app, qt_app
    ):
        window, _c, engine, _v, lib, _cel = app
        fa = engine.rootContext().contextProperty("folderHierarchyController")
        fa.setSimplified(True)
        _fanezet(engine, qt_app, True)
        host = _nyisd_a_mentest(window, qt_app)
        ut = str(lib / "masik")
        sor = _fa_latszo(window, "hierRowMouse:" + ut)
        assert len(sor) == 1, "a mentetlen levélsor nem látszik a fában"

        _kattints(window, qt_app, sor[0], dupla=False)
        assert varj_feltetelre(
            qt_app, lambda: _pipalva(host, ut)
        ), "a sor nem kapta meg a kattintást: nem pipálódott (üres átmenet)"
        assert not _nyitva(window)

        _kattints(window, qt_app, sor[0], dupla=True)

        assert not _nyitva(window), (
            "mentés-szűrő módban a fa levélsorának dupla kattintása ablakot nyitott"
        )
