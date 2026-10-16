"""#4611: a felhasználó saját `.tpl` sablonja a Weboldal-exportálás
párbeszédben (WebExportDialog.qml) listázódik, kiválasztható és exportál —
valódi egérkattintással és billentyűvel, −5/0/+5 px ablakmagasságnál."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtTest import QTest

SABLON_NEV = "Saját sablon"


def _varj(qt_app, feltetel, masodperc: float = 20.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.02)
    qt_app.processEvents()
    return bool(feltetel())


def _gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattint(qt_app, elem) -> None:
    """Valódi egérkattintás az elem közepén (nem `clicked` hívás)."""
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(elem.window(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kozep)
    qt_app.processEvents()


@pytest.fixture
def sajat_sablon(monkeypatch, tmp_path):
    """Egy saját sablon a felhasználói mappában (XDG_DATA_HOME alatt).
    A kép-hurok csak a képet írja ki, a videó-ágak üresek maradnak."""
    xdg = tmp_path / "xdg"
    monkeypatch.setenv("XDG_DATA_HOME", str(xdg))
    mappa = xdg / "picasapy" / "webexport" / "templates" / "sajat"
    mappa.mkdir(parents=True)
    (mappa / "index.tpl").write_text(
        f'#templatefile -v "1.0" -n "{SABLON_NEV}" -d "Teszt sablon"\n'
        "define exportFileName index.html\n"
        "loop elem.html\n",
        encoding="utf-8",
    )
    (mappa / "elem.html").write_text(
        "<%if isImage%>KEP:<%itemNameOnly%><%endif%>"
        "<%if isSimpleEmbed%>SIMPLE<%endif%>\n",
        encoding="utf-8",
    )
    return mappa


def _webexport_vezerlo(engine, controller):
    """A `WebExportController` a `application.py`-hoz hasonlóan: a
    `photo_source` a látható fotók. A visszaadott objektumot a hívónak
    kell életben tartania."""
    from picasapy.app.webexport_controller import WebExportController

    vezerlo = WebExportController(photo_source=lambda: controller.photos.photos)
    engine.rootContext().setContextProperty("webExportController", vezerlo)
    return vezerlo


@pytest.fixture
def kimeno(tmp_path):
    return tmp_path / "ki"


class TestSajatSablonExport:
    @pytest.mark.parametrize("delta", [-5, 0, 5], ids=["-5px", "0px", "+5px"])
    def test_user_template_is_picked_and_exported_by_clicks(
        self, qml_app, qt_app, sajat_sablon, kimeno, delta
    ):
        window, controller, engine = qml_app
        # az `application.py` bekötését tükrözzük: a fixture nem kapcsolja be
        exporter_vezerlo = _webexport_vezerlo(engine, controller)
        QMetaObject.invokeMethod(window, "openWebExport", Qt.ConnectionType.DirectConnection)
        assert _varj(qt_app, lambda: window.findChild(QObject, "webExportDialog") is not None)
        dialog = window.findChild(QObject, "webExportDialog")
        dialog.setProperty("targetFolder", str(kimeno))
        dialog.show()
        qt_app.processEvents()

        valaszto = _gyerek(dialog, "webExportTemplateBox")
        nevek = list(valaszto.property("model"))
        assert SABLON_NEV in nevek, f"a saját sablon nincs a listában: {nevek}"
        index = nevek.index(SABLON_NEV)

        _kattint(qt_app, valaszto)
        for _ in range(index):
            QTest.keyClick(valaszto.window(), Qt.Key.Key_Down)
            qt_app.processEvents()
        QTest.keyClick(valaszto.window(), Qt.Key.Key_Return)
        qt_app.processEvents()
        assert dialog.property("templateId") == "sajat"
        # a tartalom a sablonválasztás után változhat: a magasságot ITT,
        # a már beállt elrendezéshez képest mérjük, ±5 px-re
        dialog.setProperty("height", dialog.property("fitHeight") + delta)
        qt_app.processEvents()

        gomb = _gyerek(dialog, "webExportGenerateButton")
        allas = gomb.mapToScene(QPointF(0, 0)).y() + gomb.height()
        assert allas <= dialog.property("height"), "a Létrehozás gomb kilóg az ablakból"
        assert gomb.property("enabled") is True

        _kattint(qt_app, gomb)
        assert _varj(qt_app, lambda: (kimeno / "index.html").is_file())
        assert exporter_vezerlo.waitForExport(20.0)
        html = (kimeno / "index.html").read_text(encoding="utf-8")
        assert "KEP:a" in html
        assert "SIMPLE" not in html
