"""A nyomtatás kis kép figyelmeztetésének három kimenete (#4275)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPointF, Qt, QTranslator, QUrl
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest
from support.qt_wait import varj_feltetelre


@pytest.fixture
def magyar_forditas(qt_app):
    from picasapy.app import application

    translator = QTranslator(qt_app)
    qm = Path(application.__file__).parent / "i18n" / "picasapy_hu.qm"
    assert translator.load(str(qm)), f"a magyar fordítás nem tölthető be: {qm}"
    assert qt_app.installTranslator(translator)
    yield
    qt_app.removeTranslator(translator)


@pytest.fixture
def qml_app_magyar(magyar_forditas, qml_app):
    return qml_app


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _lista(ertek):
    return ertek.toVariant() if hasattr(ertek, "toVariant") else ertek


def _kattints(item, qt_app):
    qt_app.processEvents()
    os_ = item
    while os_ is not None:
        os_.ensurePolished()
        os_ = os_.parentItem()
    ablak = item.window()
    pont = item.mapToItem(ablak.contentItem(), item.boundingRect().center()).toPoint()
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont,
    )
    qt_app.processEvents()


def _listaelem(qt_app, lista, index):
    kifejezes = QQmlExpression(qmlContext(lista), lista, f"itemAtIndex({index})")

    def _elkeszult():
        ertek, hiba = kifejezes.evaluate()
        assert not hiba, kifejezes.error()
        _elkeszult.ertek = ertek
        return ertek is not None

    _elkeszult.ertek = None
    assert varj_feltetelre(qt_app, _elkeszult, masodperc=3), (
        f"a lista {index}. sora nem épült fel"
    )
    ertek = _elkeszult.ertek
    return ertek.toQObject() if hasattr(ertek, "toQObject") else ertek


def _nyomtatasi_parbeszed(window, qt_app):
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    menu = _elem(window, "menuFilePrint")
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return _elem(window, "printDialog")


@pytest.fixture
def nyomtatasi_parbeszed(qml_app_magyar, qt_app):
    window, _controller, _engine = qml_app_magyar
    dialog = _nyomtatasi_parbeszed(window, qt_app)
    yield dialog
    dialog.setProperty("visible", False)
    qt_app.processEvents()


def _nyisd_meg_az_atnezest(dialog, qt_app):
    QMetaObject.invokeMethod(
        dialog,
        "openForRows",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", [0, 1]),
    )
    qt_app.processEvents()
    _kattints(_elem(dialog, "printReviewButton"), qt_app)
    panel = _elem(dialog, "printReviewPanel")
    assert varj_feltetelre(
        qt_app, lambda: panel.property("visible") is True, masodperc=3
    ), (
        "az Ellenőrzés kattintása nem nyitotta meg a felülvizsgálatot"
    )
    return panel


def test_a_harom_kimenet_valodi_kattintassal_magyarul_es_valtozo_ablakmagassaggal(
    nyomtatasi_parbeszed, qt_app, tmp_path
):
    dialog = nyomtatasi_parbeszed
    alapmagassag = int(dialog.property("height"))

    for elteres in (-5, 0, 5):
        dialog.setProperty("height", alapmagassag + elteres)
        qt_app.processEvents()

        panel = _nyisd_meg_az_atnezest(dialog, qt_app)
        figyelmeztetes = _elem(dialog, "printReviewWarningText")
        assert figyelmeztetes.property("text") == (
            "Néhány kép túl kicsi a jó minőségű nyomtatáshoz. "
            "Ezeket eltávolíthatja, mégis kinyomtathatja, vagy megszakíthatja "
            "a nyomtatást, és módosíthatja a nyomtatási méretet."
        )
        lista = _elem(dialog, "printReviewList")
        assert len(_lista(lista.property("model"))) == 2

        # 1. kimenet: egy kijelölt, gyenge minőségű kép eltávolítása.
        sor = _listaelem(qt_app, lista, 0)
        sor_felirat = sor.findChild(QObject, "printReviewListRowText")
        assert sor_felirat is not None
        assert "Gyenge minőség (" in sor_felirat.property("text")
        assert "képpont/hüvelyk" in sor_felirat.property("text")
        dpi = str(_lista(lista.property("model"))[0]["dpi"])
        assert dpi in sor_felirat.property("text")
        assert int(lista.property("currentIndex")) == 0
        remove_selected = _elem(dialog, "printReviewRemoveSelectedButton")
        assert remove_selected.property("enabled") is True
        _kattints(sor, qt_app)
        _kattints(remove_selected, qt_app)
        sikerult_eltavolitani = varj_feltetelre(
            qt_app,
            lambda: _lista(dialog.property("quality"))["total"] == 1,
            masodperc=3,
        )
        assert sikerult_eltavolitani, (
            f"az eltávolító kattintás nem változtatott: rows="
            f"{_lista(dialog.property('rows'))}, quality="
            f"{_lista(dialog.property('quality'))}, elem="
            f"{_lista(lista.property('model'))[0]}, gombhely="
            f"{remove_selected.mapToScene(QPointF(0, 0)).toPoint()} "
            f"+ {remove_selected.width()}×{remove_selected.height()}, "
            f"ablak={dialog.width()}×{dialog.height()}"
        )
        assert len(_lista(lista.property("model"))) == 1
        assert _elem(dialog, "printReviewRemoveSelectedButton").property(
            "text"
        ) == "Kijelölt elemek eltávolítása"
        assert _elem(dialog, "printReviewRemoveLowButton").property("text") == (
            "Gyenge minőségű képek eltávolítása"
        )

        # 2. kimenet: minden gyenge minőségű kép eltávolítása.
        panel = _nyisd_meg_az_atnezest(dialog, qt_app)
        _kattints(_elem(dialog, "printReviewRemoveLowButton"), qt_app)
        assert varj_feltetelre(
            qt_app,
            lambda: _lista(dialog.property("quality"))["total"] == 0,
            masodperc=3,
        )
        assert _elem(dialog, "printReviewEmptyText").property("text") == (
            "Nincs több nyomtatni való kép."
        )
        assert panel.property("visible") is True

        # 3. kimenet: Mégse visszatér a méretválasztóhoz, a képek megmaradnak.
        panel = _nyisd_meg_az_atnezest(dialog, qt_app)
        _kattints(_elem(dialog, "printReviewCancelButton"), qt_app)
        assert varj_feltetelre(
            qt_app,
            lambda panel=panel: panel.property("visible") is False,
            masodperc=3,
        )
        assert _lista(dialog.property("rows")) == [0, 1]
        assert _lista(dialog.property("quality"))["total"] == 2
        assert _elem(dialog, "printSizeBox").property("enabled") is True

        # A Picasa OK gombja a „kinyomtatja őket” kimenet: valódi PDF készül.
        panel = _nyisd_meg_az_atnezest(dialog, qt_app)
        cel = tmp_path / f"review-{elteres}.pdf"
        dialog.setProperty("pdfTarget", QUrl.fromLocalFile(str(cel)).toString())
        qt_app.processEvents()
        _kattints(_elem(dialog, "printReviewAcceptButton"), qt_app)
        assert varj_feltetelre(
            qt_app,
            lambda cel=cel, panel=panel: (
                cel.exists() and panel.property("visible") is False
            ),
            masodperc=3,
        ), "az OK gomb nem indította el a nyomtatást"
        assert cel.read_bytes().startswith(b"%PDF")
        assert panel.property("visible") is False
