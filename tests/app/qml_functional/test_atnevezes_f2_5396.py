"""Az egyképes F2-átnevezés a mért Picasa-dialógust és fájlhatást adja (#5396)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    kattints,
    kijelolt,
    varj,
)
from tests.app.qml_functional._racs_maradek_5150_helpers import kep_cellaja


def _gyerek(window, object_name: str):
    item = window.findChild(QObject, object_name)
    assert item is not None, f"{object_name} nem található"
    return item


@pytest.mark.parametrize("magassag_elteres", (-5, 0, 5))
def test_f2_atnevezes_egyetlen_kepre_megorizza_a_picasa_parbeszedet_es_fajlt(
    qml_app, qt_app, tmp_path, magassag_elteres
):
    window, controller, _engine = qml_app
    window.show()
    window.setHeight(window.height() + magassag_elteres)
    window.requestActivate()
    assert varj(qt_app, lambda: window.property("active") is True), (
        "a főablak nem aktiválódott"
    )
    assert varj(qt_app, lambda: len(controller.photos.photos) == 2), (
        "a fixture két tesztképe nem töltődött be"
    )

    regi_nev = str(controller.photos.itemAt(0)["name"])
    mappa = Path(str(controller.photos.filePathAt(0))).parent
    assert not (mappa / ".picasa.ini").exists(), (
        "a kiinduló képhez nem tartozhat .picasa.ini"
    )

    # A kijelölés valódi bélyegképkattintással történik.
    kattints(window, qt_app, kep_cellaja(window, 0))
    assert kijelolt(window) == [0], "a bélyegképkattintás nem jelölte ki a képet"
    QTest.keyClick(window, Qt.Key.Key_F2)
    qt_app.processEvents()

    assert varj(
        qt_app,
        lambda: (
            (dialog := window.findChild(QObject, "renameManyDialog")) is not None
            and dialog.property("visible") is True
        ),
    ), "az F2 nem a Rename Files párbeszédet nyitotta meg"
    dialog = _gyerek(window, "renameManyDialog")
    assert dialog.property("title") == "Rename Files"
    assert _gyerek(window, "renameManySelectionLabel").property("text") == (
        "1 file(s) selected for rename."
    )
    assert _gyerek(window, "renameManyPromptLabel").property("text") == (
        "Please enter a new name for these files:"
    )
    gombfeliratok = {
        str(child.property("text"))
        for child in dialog.findChildren(QObject)
        if child.property("text") is not None
    }
    assert {"Rename", "Cancel"} <= gombfeliratok, (
        f"az elfogadó és megszakító gomb hiányzik: {gombfeliratok}"
    )

    mezo = _gyerek(window, "renameManyField")
    assert mezo.property("text") == "", "az új név mezője nem üresen nyílt meg"
    datum = _gyerek(window, "renameManyDateCheck")
    felbontas = _gyerek(window, "renameManySizeCheck")
    assert datum.property("text") == "Date"
    assert datum.property("checked") is False
    assert felbontas.property("text") == "Image resolution"
    assert felbontas.property("checked") is False
    assert float(felbontas.property("y")) > float(datum.property("y")), (
        "az eredeti Picasában az Image resolution a Date alatti sorban áll"
    )
    minta = _gyerek(window, "renameManySampleLabel")

    for karakter in "atnevezett":
        QTest.keyClick(window, karakter)
        qt_app.processEvents()
    assert mezo.property("text") == "atnevezett"
    assert minta.property("text") == "Example: atnevezett.jpg", (
        "az Example sor nem követte élőben a begépelt nevet és kiterjesztést"
    )

    kep = window.grabWindow()
    assert not kep.isNull(), "a párbeszéd képernyőképe üres"
    kep_path = tmp_path / "atnevezes_f2_parbeszed.png"
    assert kep.save(str(kep_path)), f"nem menthető a párbeszéd képe: {kep_path}"

    # A mező fókuszában az Enter fogadja el a párbeszédet.
    QTest.keyClick(window, Qt.Key.Key_Return)
    cel = mappa / "atnevezett.jpg"
    assert varj(
        qt_app,
        lambda: (
            cel.exists()
            and not (mappa / regi_nev).exists()
            and len(controller.photos.photos) == 2
            and str(controller.photos.itemAt(0)["name"]) == cel.name
        ),
    ), "az Enter nem nevezte át és frissítette a kijelölt képet"
    assert kijelolt(window) == [0], "az átnevezés után elveszett a kijelölés"
    assert not (mappa / ".picasa.ini").exists(), (
        "szakasz nélküli kép átnevezése .picasa.ini-t hozott létre"
    )
    assert varj(qt_app, lambda: dialog.property("visible") is False), (
        "az Enter után az átnevező párbeszéd nyitva maradt"
    )
