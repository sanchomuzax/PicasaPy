"""#6358: a frissítési ablak gombjai az ablakon belül, egymás mellett,
jobbra igazítva állnak, és a leírás látszik (a ConfirmDialog mintája)."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, QPointF

from tests.app.qml_functional.test_update_dialog_6340 import (
    _FakeUpdateController,
    _wait_for,
)


class _EgykattintasosFake(_FakeUpdateController):
    @Property(bool, notify=_FakeUpdateController.updateAvailableChanged)
    def oneClickUpdateSupported(self):  # noqa: N802
        return True


def _keret(elem, gyoker):
    bal_felso = elem.mapToItem(gyoker, QPointF(0, 0))
    return (bal_felso.x(), bal_felso.y(),
            bal_felso.x() + elem.property("width"),
            bal_felso.y() + elem.property("height"))


def test_a_gombok_az_ablakon_belul_egymas_mellett_allnak(qml_app, qt_app):
    window, _controller, engine = qml_app
    window.resize(1280, 800)
    fake = _EgykattintasosFake()
    engine.rootContext().setContextProperty("updateController", fake)
    dialog = window.findChild(QObject, "updateDialog")
    dialog.open()
    _wait_for(qt_app, lambda: bool(dialog.property("opened")), "az ablak nem nyílt meg")
    for _ in range(5):
        qt_app.processEvents()

    tartalom = dialog.property("contentItem")
    hatter = dialog.property("background")
    ablak = _keret(hatter, tartalom)
    nevek = ("updateDialogDownloadButton", "updateDialogLaterButton",
             "updateDialogSkipButton")
    gombok = [_keret(window.findChild(QObject, n), tartalom) for n in nevek]

    for nev, (bal, fent, jobb, lent) in zip(nevek, gombok, strict=True):
        assert window.findChild(QObject, nev).property("visible"), nev
        assert ablak[0] <= bal and jobb <= ablak[2], nev
        assert ablak[1] <= fent and lent <= ablak[3] - 4, f"{nev} kilóg az ablak aljából"
    for (_, f1, j1, _), (b2, f2, _, _) in zip(gombok, gombok[1:], strict=False):
        assert abs(f1 - f2) < 1, "a gombok nem egy sorban állnak"
        assert 0 <= b2 - j1 <= 12, "a gombok között túl nagy a rés"
    assert ablak[2] - gombok[-1][2] <= 30, "a gombsor nincs jobbra igazítva"

    jegyzet = window.findChild(QObject, "updateDialogReleaseNotes")
    assert jegyzet.property("visible")
    assert jegyzet.property("height") > 0
    dialog.close()
    del fake
