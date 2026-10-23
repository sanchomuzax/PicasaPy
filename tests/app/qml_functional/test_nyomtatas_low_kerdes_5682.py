"""#5682: a „Remove Low Quality Pictures" megerősítése (eredeti: 0x0085cce0).

Ha a felülvizsgálati listában van legalább egy nem alacsony minőségű kép,
nincs kérdés: csak az alacsony minőségűek törlődnek. Ha MINDEN kép
alacsony minőségű, az eredeti megerősítést kér: az Igen törli a képeket
és megszakítja a nyomtatást, a Nem nem változtat a listán.

rontás-kontroll: PrintDialog.qml#removeLowQualityReviewPictures kérdés-ágát
kivéve a három minden-alacsony teszt PIROS (a kérdés nem jelenik meg).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt, QUrl
from PySide6.QtTest import QTest
from support.qt_wait import varj_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg

#: a kiadáskép mappáját a hívó adja meg; a teszt ennél mást nem ír
KIADASKEP_MAPPA = "PICASAPY_5682_KIADASKEP_MAPPA"
KIADASKEP_NEV = "nyomtatas_low_5682.png"

KERDES_SZOVEG = (
    "This will remove all of your pictures and cancel printing. "
    "Would you like to continue?"
)
IGEN_SZOVEG = "Remove and Cancel"
NEM_SZOVEG = "Don't Remove"


def _vegyes_kepek(lib) -> None:
    """Egy alacsony (100 képpont) és egy Best minőségű (2400×1800) kép."""
    make_minta_jpeg(lib / "a.jpg", size=(100, 100), seed=1)
    make_minta_jpeg(lib / "b.jpg", size=(2400, 1800), seed=2)


def _minden_alacsony_kepek(lib) -> None:
    """Két kicsi kép: mindkettő alacsony (Bad) minőségű a Teljes oldal méreten."""
    make_minta_jpeg(lib / "a.jpg", size=(100, 100), seed=1)
    make_minta_jpeg(lib / "b.jpg", size=(120, 90), seed=2)


@pytest.fixture
def vegyes_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_vegyes_kepek)


@pytest.fixture
def minden_alacsony_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=_minden_alacsony_kepek
    )


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


def _nyomtatasi_parbeszed(window, qt_app):
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    menu = _elem(window, "menuFilePrint")
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    dialog = _elem(window, "printDialog")
    # #4795: a kezdőmagasság az első elrendezés után, késleltetve áll be
    assert varj_feltetelre(
        qt_app, lambda: not dialog.property("meretezesFuggoben"), masodperc=10.0
    )
    return dialog


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
        qt_app, lambda: panel.property("visible") is True, masodperc=10.0
    ), "az Ellenőrzés kattintása nem nyitotta meg a felülvizsgálatot"
    return panel


def _kerdes(dialog):
    """A megerősítő párbeszéd, ha a dialógus épp látszik; egyébként `None`."""
    kerdes = dialog.findChild(QObject, "printRemoveAllDialog")
    if kerdes is None or kerdes.property("visible") is not True:
        return None
    return kerdes


def _nyomtatas_jelei(ctl):
    """A vezérlő nyomtatási jelei: ha a nyomtatás elindul, ezek egyike jön."""
    jelek = []
    ctl.printFinished.connect(lambda *_: jelek.append("printFinished"))
    ctl.printFailed.connect(lambda *_: jelek.append("printFailed"))
    ctl.printSkipped.connect(lambda *_: jelek.append("printSkipped"))
    ctl.printProgress.connect(lambda *_: jelek.append("printProgress"))
    return jelek


@pytest.fixture
def vegyes_parbeszed(vegyes_app, qt_app):
    window, _controller, _engine = vegyes_app
    dialog = _nyomtatasi_parbeszed(window, qt_app)
    yield dialog
    dialog.setProperty("visible", False)
    qt_app.processEvents()


@pytest.fixture
def minden_alacsony_parbeszed(minden_alacsony_app, qt_app):
    window, _controller, _engine = minden_alacsony_app
    dialog = _nyomtatasi_parbeszed(window, qt_app)
    yield dialog
    dialog.setProperty("visible", False)
    qt_app.processEvents()


def test_vegyes_lista_nincs_kerdes_es_csak_az_alacsony_kep_tunik_el(
    vegyes_parbeszed, qt_app
):
    dialog = vegyes_parbeszed
    _nyisd_meg_az_atnezest(dialog, qt_app)
    modell = _lista(_elem(dialog, "printReviewList").property("model"))
    alacsony = [kep for kep in modell if kep["qualityCode"] == 0]
    jo = [kep for kep in modell if kep["qualityCode"] != 0]
    # előfeltétel: pontosan egy alacsony és egy nem alacsony kép van
    assert len(alacsony) == 1 and len(jo) == 1, modell

    _kattints(_elem(dialog, "printReviewRemoveLowButton"), qt_app)

    assert varj_feltetelre(
        qt_app,
        lambda: _lista(dialog.property("rows")) == [jo[0]["row"]],
        masodperc=10.0,
    ), f"a Remove Low nem törölte az alacsony képet: {_lista(dialog.property('rows'))}"
    assert _lista(dialog.property("quality"))["total"] == 1
    # a vegyes listánál nincs megerősítő kérdés
    assert _kerdes(dialog) is None


def test_minden_alacsony_lista_a_kerdes_pontosan_egyszer_jelenik_meg(
    minden_alacsony_parbeszed, qt_app
):
    dialog = minden_alacsony_parbeszed
    _nyisd_meg_az_atnezest(dialog, qt_app)
    modell = _lista(_elem(dialog, "printReviewList").property("model"))
    # előfeltétel: minden kép alacsony minőségű
    assert modell and all(kep["qualityCode"] == 0 for kep in modell), modell
    sorok_elotte = _lista(dialog.property("rows"))

    _kattints(_elem(dialog, "printReviewRemoveLowButton"), qt_app)

    assert varj_feltetelre(
        qt_app, lambda: _kerdes(dialog) is not None, masodperc=10.0
    ), "a minden-alacsony listánál nem jelent meg a megerősítés"
    assert len(dialog.findChildren(QObject, "printRemoveAllDialog")) == 1
    assert _elem(dialog, "printRemoveAllMessage").property("text") == KERDES_SZOVEG
    assert _elem(dialog, "printRemoveAllYesButton").property("text") == IGEN_SZOVEG
    assert _elem(dialog, "printRemoveAllNoButton").property("text") == NEM_SZOVEG
    # a kérdés még nem töröl semmit
    assert _lista(dialog.property("rows")) == sorok_elotte

    kerdes = _kerdes(dialog)
    assert varj_feltetelre(
        qt_app, lambda: kerdes.property("opacity") >= 0.99, masodperc=10.0
    )
    kiadaskep_mappa = os.environ.get(KIADASKEP_MAPPA)
    if kiadaskep_mappa:
        ablak = _elem(dialog, "printRemoveAllMessage").window()
        kep = ablak.grabWindow()
        assert not kep.isNull(), "a kérdés kiadásképe üres"
        cel = Path(kiadaskep_mappa) / KIADASKEP_NEV
        cel.parent.mkdir(parents=True, exist_ok=True)
        assert kep.save(str(cel), "PNG"), f"nem menthető a kiadáskép: {cel}"


def test_minden_alacsony_nem_gomb_a_listat_nem_valtoztatja(
    minden_alacsony_parbeszed, qt_app
):
    dialog = minden_alacsony_parbeszed
    panel = _nyisd_meg_az_atnezest(dialog, qt_app)
    sorok_elotte = _lista(dialog.property("rows"))

    _kattints(_elem(dialog, "printReviewRemoveLowButton"), qt_app)
    assert varj_feltetelre(
        qt_app, lambda: _kerdes(dialog) is not None, masodperc=10.0
    )
    _kattints(_elem(dialog, "printRemoveAllNoButton"), qt_app)

    assert varj_feltetelre(
        qt_app, lambda: _kerdes(dialog) is None, masodperc=10.0
    ), "a Nem gomb nem zárta be a megerősítést"
    assert _lista(dialog.property("rows")) == sorok_elotte
    assert _lista(dialog.property("quality"))["total"] == 2
    assert len(_lista(_elem(dialog, "printReviewList").property("model"))) == 2
    # a felülvizsgálat marad nyitva, a nyomtatás nem indult
    assert panel.property("visible") is True


def test_minden_alacsony_igen_torli_a_kepeket_es_bezarja_a_nyomtatast(
    minden_alacsony_parbeszed, qt_app, tmp_path
):
    dialog = minden_alacsony_parbeszed
    ctl = dialog.property("printCtl")
    assert ctl is not None, "a nyomtatási vezérlő nem érhető el a teszthez"
    jelek = _nyomtatas_jelei(ctl)
    cel = tmp_path / "minden-alacsony-5682.pdf"
    dialog.setProperty("pdfTarget", QUrl.fromLocalFile(str(cel)).toString())
    panel = _nyisd_meg_az_atnezest(dialog, qt_app)

    _kattints(_elem(dialog, "printReviewRemoveLowButton"), qt_app)
    assert varj_feltetelre(
        qt_app, lambda: _kerdes(dialog) is not None, masodperc=10.0
    )
    _kattints(_elem(dialog, "printRemoveAllYesButton"), qt_app)

    # a képek törlődnek, és a nyomtatási ablak a Close (pcancelbutton) ágon zárul
    assert varj_feltetelre(
        qt_app,
        lambda: _lista(dialog.property("quality"))["total"] == 0,
        masodperc=10.0,
    ), "az Igen gomb nem törölte a képeket"
    assert _lista(dialog.property("rows")) == []
    assert _kerdes(dialog) is None
    assert varj_feltetelre(
        qt_app, lambda: panel.property("visible") is False, masodperc=10.0
    )
    assert varj_feltetelre(
        qt_app, lambda: dialog.property("visible") is False, masodperc=10.0
    ), "az Igen után a nyomtatási ablaknak be kell zárulnia (0x00745726)"

    # a nyomtatás nem futott le: sem hiba-, sem eredmény-üzenet, sem jel, sem PDF
    qt_app.processEvents()
    assert dialog.property("lastError") == ""
    assert dialog.property("lastResult") == ""
    assert jelek == []
    assert not cel.exists()
