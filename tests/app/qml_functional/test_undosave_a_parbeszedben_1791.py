"""#1791 — az „Undo Save" a Visszaállítás párbeszéd gombja, nem menütétel.

## A lelet (#1774 mérése)

A tulajdonos képernyőmentésén a Picasa **Fájl** menüjének mentés-csoportja
pontosan két tételből áll: **Mentés** és **Visszaállítás** (inaktív).
Harmadik tétel nincs — és a mentésen az inaktív tételek is látszanak,
tehát nem rejtőzhet el.

Az „Undo Save" az eredetiben **létezik**, csak máshol:

| kulcs | mi ez |
|---|---|
| `CThumbUI::FileRevert::undosave` | **gomb a Visszaállítás párbeszédben** |
| `CThumbUI::FileRevert::message1undo` | a párbeszéd magyarázó sora |
| `CFilterStackUI::savetip` | tipp a szerkesztősávon |

Az `eMenuFile` névtér 21 kulcsa közt **nincs** hozzá tartozó `ID_*`.

## Miért nem lehetett a #1774-ben megcsinálni

Mert a menütétel törlése akkor **elvágta volna az egyetlen elérési utat**:
a párbeszédünkben nem volt „Undo Save" gomb. Előbb a gombnak kellett
megszületnie — ez a jegy azt teszi, és csak UTÁNA veszi ki a tételt.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from support.halasztott_parbeszed import nyisd_meg

_MENU_QML = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml"
)


def _gyerek(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _nyisd_a_visszaallitast(window, qt_app):
    nyisd_meg(window, "saveDialogs")
    qt_app.processEvents()
    QMetaObject.invokeMethod(
        _gyerek(window, "saveDialogs"), "openRevert",
        Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", [0]),
    )
    qt_app.processEvents()


class TestAGombAParbeszedben:
    def test_a_visszaallitas_parbeszedeben_van_undo_save_gomb(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        _nyisd_a_visszaallitast(window, qt_app)

        assert _gyerek(window, "revertConfirmDialog").property("visible")
        gomb = window.findChild(QObject, "revertUndoSaveButton")
        assert gomb is not None, (
            "a Visszaállítás párbeszédben nincs „Undo Save\" gomb — az "
            "eredetiben ez a funkció EGYETLEN helye (#1791)"
        )

    def test_a_magyarazo_sor_is_ott_van(self, qml_app, qt_app):
        """`CThumbUI::FileRevert::message1undo` — a gomb önmagában nem
        mondja meg, hogy a szerkesztések MEGMARADNAK."""
        window, _controller, _engine = qml_app
        _nyisd_a_visszaallitast(window, qt_app)

        magyarazat = window.findChild(QObject, "revertUndoSaveHint")
        assert magyarazat is not None, "hiányzik a magyarázó sor"
        assert "Undo Save" in (magyarazat.property("text") or "")

    def test_a_gomb_a_visszavonas_utjat_hivja(self, qml_app, qt_app):
        """A gomb NEM a visszaállítást futtatja: a két művelet más —
        a Visszaállítás eldobja a szerkesztéseket, ez megtartja őket."""
        window, controller, _engine = qml_app
        _nyisd_a_visszaallitast(window, qt_app)
        gomb = _gyerek(window, "revertUndoSaveButton")

        hivasok = []
        eredeti = controller.undoLastSave
        controller.undoLastSave = lambda sorok: hivasok.append(list(sorok))
        try:
            QMetaObject.invokeMethod(
                gomb, "clicked", Qt.ConnectionType.DirectConnection
            )
            qt_app.processEvents()
        finally:
            controller.undoLastSave = eredeti

        assert hivasok == [[0]], (
            f"a gomb nem az `undoLastSave`-et hívta: {hivasok}"
        )

    def test_a_gomb_bezarja_a_parbeszedet(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _nyisd_a_visszaallitast(window, qt_app)
        gomb = _gyerek(window, "revertUndoSaveButton")

        eredeti = controller.undoLastSave
        controller.undoLastSave = lambda sorok: None
        try:
            QMetaObject.invokeMethod(
                gomb, "clicked", Qt.ConnectionType.DirectConnection
            )
            qt_app.processEvents()
        finally:
            controller.undoLastSave = eredeti

        assert (
            _gyerek(window, "revertConfirmDialog").property("visible") is False
        )


class TestAMenutetelElkerult:
    def test_a_fajl_menuben_MAR_NINCS_undo_save_tetel(self):
        """A mért eredeti Fájl menüjében nincs ilyen tétel."""
        forras = _MENU_QML.read_text(encoding="utf-8")
        assert "menuFileUndoSave" not in forras, (
            "az „Undo Save\" még mindig menütétel — a mért eredetiben a "
            "Fájl menü mentés-csoportja két tételből áll (#1791)"
        )

    def test_a_jelzes_es_a_belepesi_pont_is_elkerult(self):
        """Az őr foga: a `placeholder` nélküli, kezelő nélküli maradék
        jelzés némán ott ragadna."""
        forras = _MENU_QML.read_text(encoding="utf-8")
        assert "undoSaveRequested" not in forras
