"""#5704: valódi kattintások a gyűjtemény-jelszó menüjén és ajánlatán."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index
from tests.support.jpeg_factory import make_jpeg
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre


def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _elem(window, nev):
    return window.findChild(QObject, nev)


def _vizualis_elem(window, nev):
    sor = [window.contentItem()]
    while sor:
        item = sor.pop()
        if item.objectName() == nev and item.isVisible():
            return item
        sor.extend(item.childItems())
    return None


def _kattint(qt_app, window, item, gomb=Qt.MouseButton.LeftButton):
    assert item is not None
    assert _var(qt_app, lambda: item.width() > 0 and item.height() > 0)
    pont = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
    QTest.mouseClick(window, gomb, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_felhasznaloi_gyujtemeny_jelszo_menu_valodi_kattintassal(
    qml_app, qt_app, magassag_elteres
):
    window, controller, _engine = qml_app
    window.setHeight(window.height() + magassag_elteres)
    controller.createCollection("Családi")
    fejlec_nev = "customCollection_CsaládiRow"
    assert _var(qt_app, lambda: _vizualis_elem(window, fejlec_nev) is not None)
    fejlec = _vizualis_elem(window, fejlec_nev)

    _kattint(qt_app, window, fejlec, Qt.MouseButton.RightButton)
    menu = _elem(window, "collectionContextMenu")
    assert _var(qt_app, lambda: menu.property("opened") is True)
    jelszo_tetel = _elem(window, "collectionMenuPassword")
    assert jelszo_tetel.property("enabled") is True
    _kattint(qt_app, window, jelszo_tetel)

    dialog = _elem(window, "collectionPasswordDialog")
    assert _var(qt_app, lambda: dialog is not None and dialog.property("visible"))
    jelszo = _elem(dialog, "collectionPasswordField")
    ellenorzes = _elem(dialog, "collectionPasswordVerify")
    jelszo.setProperty("text", "regi-titok")
    ellenorzes.setProperty("text", "regi-titok")
    # a gomb felirata nem mutathatja a nyers & gyorsbillentyű-jelet
    assert "&" not in _elem(dialog, "collectionPasswordSubmit").property("text")
    _kattint(qt_app, window, _elem(dialog, "collectionPasswordSubmit"))
    assert controller.collectionPasswordLocked("Családi") is True

    _kattint(qt_app, window, fejlec, Qt.MouseButton.RightButton)
    assert _var(qt_app, lambda: menu.property("opened") is True)
    _kattint(qt_app, window, jelszo_tetel)
    assert _var(qt_app, lambda: dialog.property("visible") is True)
    jelenlegi = _elem(dialog, "collectionPasswordCurrent")
    jelenlegi.setProperty("text", "rossz")
    _kattint(qt_app, window, _elem(dialog, "collectionPasswordSubmit"))
    assert dialog.property("visible") is True
    assert _elem(dialog, "collectionPasswordError").property("visible") is True

    jelenlegi.setProperty("text", "regi-titok")
    _kattint(qt_app, window, _elem(dialog, "collectionPasswordSubmit"))
    assert controller.collectionPasswordLocked("Családi") is False

    # A helyi menüből a régi jelszó igazolása után lehet cserélni.
    _kattint(qt_app, window, fejlec, Qt.MouseButton.RightButton)
    assert _var(qt_app, lambda: menu.property("opened") is True)
    _kattint(qt_app, window, jelszo_tetel)
    assert _var(qt_app, lambda: dialog.property("visible") is True)
    jelenlegi = _elem(dialog, "collectionPasswordCurrent")
    jelenlegi.setProperty("text", "hibás")
    _kattint(qt_app, window, _elem(dialog, "collectionPasswordChangeButton"))
    assert dialog.property("visible") is True
    assert _elem(dialog, "collectionPasswordError").property("visible") is True

    jelenlegi.setProperty("text", "regi-titok")
    _kattint(qt_app, window, _elem(dialog, "collectionPasswordChangeButton"))
    uj_jelszo = _elem(dialog, "collectionPasswordField")
    uj_ellenorzes = _elem(dialog, "collectionPasswordVerify")
    uj_jelszo.setProperty("text", "uj-titok")
    uj_ellenorzes.setProperty("text", "uj-titok")
    _kattint(qt_app, window, _elem(dialog, "collectionPasswordSubmit"))
    assert _var(qt_app, lambda: not dialog.property("visible"))
    assert controller.verifyCollectionPassword("Családi", "uj-titok") is True

    # A törlés is hitelesítést kér; a hibás próbálkozás nyitva hagyja a dialógust.
    _kattint(qt_app, window, fejlec, Qt.MouseButton.RightButton)
    assert _var(qt_app, lambda: menu.property("opened") is True)
    _kattint(qt_app, window, jelszo_tetel)
    assert _var(qt_app, lambda: dialog.property("visible") is True)
    jelenlegi = _elem(dialog, "collectionPasswordCurrent")
    jelenlegi.setProperty("text", "regi-titok")
    _kattint(qt_app, window, _elem(dialog, "collectionPasswordRemoveButton"))
    assert dialog.property("visible") is True
    assert controller.collectionPasswordSet("Családi") is True

    jelenlegi.setProperty("text", "uj-titok")
    _kattint(qt_app, window, _elem(dialog, "collectionPasswordRemoveButton"))
    assert _var(qt_app, lambda: not dialog.property("visible"))
    assert controller.collectionPasswordSet("Családi") is False


def test_mappa_elrejtese_utan_ajanl_es_a_nem_kerdezd_ujra_megmarad(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    gyoker = Path(controller.watchedFolders[0])
    elso = gyoker / "ajanlott"
    masodik = gyoker / "ajanlat_nelkul"
    harmadik = gyoker / "optout_utan"
    elso.mkdir(parents=True, exist_ok=True)
    masodik.mkdir(parents=True, exist_ok=True)
    harmadik.mkdir(parents=True, exist_ok=True)
    make_jpeg(elso / "kep.jpg", size=(80, 60))
    make_jpeg(masodik / "kep.jpg", size=(80, 60))
    make_jpeg(harmadik / "kep.jpg", size=(80, 60))
    controller.rescan()

    def _mappak_bent_vannak_az_indexben():
        controller.waitForBackgroundWorkers(0.05)
        with open_index(controller._db_path) as conn:
            indexed = {
                row[0]
                for row in conn.execute(
                    "SELECT path FROM folders WHERE path IN (?, ?, ?)",
                    (str(elso), str(masodik), str(harmadik)),
                )
            }
        return indexed == {str(elso), str(masodik), str(harmadik)}

    assert _var(qt_app, _mappak_bent_vannak_az_indexben), (
        "az új mappák nem kerültek be az indexbe"
    )

    ajanlatok = []
    controller.hiddenPasswordOfferRequested.connect(lambda: ajanlatok.append(True))
    controller.toggleFolderHidden(str(elso))
    ajanlat = _elem(window, "hiddenPasswordOfferDialog")
    assert controller.isFolderHidden(str(elso)) is True
    assert len(ajanlatok) == 1
    assert _var(qt_app, lambda: ajanlat is not None and ajanlat.property("visible"))

    # Opt-out nélkül sem a felfedés, sem a Rejtett képek nézet nem ajánl jelszót.
    _kattint(qt_app, window, _elem(window, "hiddenPasswordOfferNoButton"))
    assert _var(qt_app, lambda: ajanlat.property("visible") is False)
    controller.toggleFolderHidden(str(elso))
    assert controller.isFolderHidden(str(elso)) is False
    assert len(ajanlatok) == 1
    assert ajanlat.property("visible") is False
    controller.setShowHidden(True)
    assert len(ajanlatok) == 1
    assert ajanlat.property("visible") is False
    controller.setShowHidden(False)

    # Egy újabb elrejtésnél az ajánlat megjelenik, az elutasítás pedig megjegyezhető.
    controller.toggleFolderHidden(str(masodik))
    assert len(ajanlatok) == 2
    assert _var(qt_app, lambda: ajanlat.property("visible") is True)
    _kattint(qt_app, window, _elem(window, "hiddenPasswordOfferRememberCheck"))
    _kattint(qt_app, window, _elem(window, "hiddenPasswordOfferNoButton"))
    assert controller._get_settings().value(
        "confirm/DoNotConfirmHiddenPwd/remember"
    ) in (True, "true")

    controller.toggleFolderHidden(str(harmadik))
    assert len(ajanlatok) == 2
    assert ajanlat.property("visible") is False
