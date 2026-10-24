"""#5683: az eredeti nyomtatási méretlista megjelenése a valódi párbeszédben."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest

from tests.support.varakozas import var_feltetelre


_EREDTI_AZONOSITOK = [
    "M3X4",
    "M3_5X5",
    "M4X5",
    "M4X6",
    "M5X7",
    "M8X10",
    "M5X8CM",
    "M9X13CM",
    "M10X15CM",
    "M13X18CM",
    "M15X20CM",
    "M20X25CM",
    "TARCA",
    "CDSIZE",
    "PASSPORT",
    "CONTACT",
    "TELJES_OLDAL",
]


def _lista(ertek):
    return ertek.toVariant() if hasattr(ertek, "toVariant") else ertek


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_eredeti_lista_letiltott_cd_es_valodi_foto_elonezet(
    qml_app, qt_app, tmp_path, magassag_elteres
):
    window, _controller, _engine = qml_app
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    menu = window.findChild(QObject, "menuFilePrint")
    assert menu is not None
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()

    dialog = window.findChild(QObject, "printDialog")
    assert dialog is not None
    assert var_feltetelre(qt_app, lambda: dialog.property("visible"), 10.0)
    dialog.setProperty(
        "height", dialog.property("height") + magassag_elteres
    )
    qt_app.processEvents()

    azonositok = _lista(dialog.property("printSizeIds"))
    assert azonositok == _EREDTI_AZONOSITOK
    opciok = _lista(dialog.property("printSizeOptions"))
    cd_sor = opciok[azonositok.index("CDSIZE")]
    assert cd_sor["id"] == "CDSIZE"
    assert cd_sor["enabled"] is False

    box = _elem(dialog, "printSizeBox")
    pont = box.mapToScene(QPointF(box.width() / 2, box.height() / 2)).toPoint()
    QTest.mouseClick(
        dialog, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )
    assert var_feltetelre(
        qt_app, lambda: box.findChild(QObject, "picasaComboList") is not None
    ), "a méretválasztó nem nyílt meg"
    lista = box.findChild(QObject, "picasaComboList")
    cd_index = azonositok.index("CDSIZE")
    lista.setProperty(
        "contentY",
        min(
            float(lista.property("contentHeight")) * cd_index / len(azonositok),
            max(
                0.0,
                float(lista.property("contentHeight")) - float(lista.height()),
            ),
        ),
    )
    qt_app.processEvents()
    kifejezes = QQmlExpression(
        qmlContext(lista), lista, f"itemAtIndex({cd_index})"
    )

    def _cd_sor_felepult():
        ertek, hiba = kifejezes.evaluate()
        assert not hiba, kifejezes.error()
        _cd_sor_felepult.elem = ertek
        return ertek is not None

    _cd_sor_felepult.elem = None
    assert var_feltetelre(qt_app, _cd_sor_felepult), "a CD-borító sora nem épült fel"
    assert _cd_sor_felepult.elem.property("enabled") is False
    popup = box.findChild(QObject, "picasaComboPopup")
    assert popup is not None
    QMetaObject.invokeMethod(popup, "close", Qt.ConnectionType.DirectConnection)
    assert var_feltetelre(qt_app, lambda: not popup.property("visible"))

    # A kiadáskép a fixture valódi JPEG-fájlját mutatja a párbeszéd
    # nyomtatási előnézetében; a külön kimeneti teszt méri a renderelést.
    kep_path = (
        Path(__file__).resolve().parents[3]
        / "tests"
        / "fixtures"
        / "face_type_a_name_reference_en38.png"
    )
    kep_url = QUrl.fromLocalFile(str(kep_path))
    dialog.setProperty("previewPageCount", 1)
    dialog.setProperty("previewSource", kep_url.toString())

    kep = _elem(dialog, "printPreviewImage")
    allapot = QQmlExpression(qmlContext(kep), kep, "status === Image.Ready")

    def _kep_betoltodott():
        ertek, hiba = allapot.evaluate()
        assert not hiba, allapot.error()
        return bool(ertek)

    assert var_feltetelre(
        qt_app, _kep_betoltodott, 3.0
    ), "a próbakép nem töltődött be a kiadásképhez"

    kep = dialog.grabWindow()
    assert not kep.isNull(), "a Nyomtatás párbeszéd képe üres"
    assert kep.save(str(tmp_path / "nyomtatas-meretek-5683.png"))

    elonezet = QImage(str(tmp_path / "nyomtatas-meretek-5683.png"))
    assert not elonezet.isNull(), "a párbeszéd kiadásképe nem olvasható"


def _elem(root, nev):
    elem = root.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem
