"""#333/#3555: nyelvválasztó az Eszközök menüben.

A menüpontok a vezérlő `pendingLanguage`-ét (a KÖVETKEZŐ indításra kért
választást) tükrözik — a futó felület nyelve ezen keresztül nem vált
azonnal: a kattintás megerősítő kérdést nyit (Main.qml `menuLanguageConfirm*`
ConfirmDialog-ja), és csak az „Igen" hívja a `setLanguage`-et.

⚠️ A menütételre és a kérdés gombjaira VALÓDI egérkattintás megy
(`QTest.mouseClick` a vezérlő közepére, jelenet-koordinátában) — a jel
kibocsátása a néma bekötési hibát (rossz `enabled`, takaró elem, elgépelt
jelnév) nem fogná meg.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.app import application


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _gyerek(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kattints(window, qt_app, elem) -> None:
    """Valódi bal kattintás a vezérlő KÖZEPÉRE."""
    assert _var(qt_app, lambda: elem.width() > 0 and elem.height() > 0), (
        f"{elem.objectName()}: nincs mérete, nem kattintható"
    )
    os_ = elem
    while os_ is not None:
        os_.ensurePolished()
        os_ = os_.parentItem()
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _vizualis(window, feltetel):
    """Az első LÁTHATÓ elem a vizuális fában, amelyre a feltétel igaz — a
    menüsáv és a menük tételeinek nincs mind objectName-je."""
    sor = [window.contentItem().parentItem() or window.contentItem()]
    while sor:
        elem = sor.pop()
        if elem.isVisible() and feltetel(elem):
            return elem
        sor.extend(elem.childItems())
    return None


def _menu_tetelre_kattint(window, qt_app, nev) -> None:
    """Eszközök (menüsáv) ▸ Nyelv ▸ `nev` — mindhárom lépés KATTINTÁS."""
    eszkozok = _vizualis(
        window,
        lambda e: "MenuBarItem" in e.metaObject().className()
        and e.property("text") == "&Tools",
    )
    assert eszkozok is not None, "az Eszközök menü nincs a menüsávon"
    _kattints(window, qt_app, eszkozok)

    nyelv = None

    def _nyelv_tetel():
        nonlocal nyelv
        nyelv = _vizualis(
            window,
            lambda e: "MenuItem" in e.metaObject().className()
            and e.property("text") == "Language",
        )
        return nyelv is not None

    assert _var(qt_app, _nyelv_tetel), "az Eszközök menüben nincs Nyelv tétel"
    _kattints(window, qt_app, nyelv)

    menu = _gyerek(window, "menuToolsLanguage")
    assert _var(qt_app, lambda: menu.property("opened") is True), "a Nyelv almenü nem nyílt meg"
    _kattints(window, qt_app, _gyerek(window, nev))


def _kerdes_nyitva(window) -> bool:
    dialog = window.findChild(QObject, "menuLanguageConfirmDialog")
    return dialog is not None and dialog.property("opened") is True


def _valaszol(window, qt_app, *, igen: bool) -> None:
    assert _var(qt_app, lambda: _kerdes_nyitva(window)), "a megerősítő kérdés nem nyílt meg"
    gomb = "menuLanguageConfirmYesButton" if igen else "menuLanguageConfirmNoButton"
    _kattints(window, qt_app, _gyerek(window, gomb))
    assert _var(qt_app, lambda: not _kerdes_nyitva(window)), "a kérdés nyitva maradt"


@pytest.fixture
def menu_items(qml_app):
    window, controller, _engine = qml_app
    system = _gyerek(window, "menuLanguageSystem")
    english = _gyerek(window, "menuLanguageEnglish")
    hungarian = _gyerek(window, "menuLanguageHungarian")
    return window, controller, system, english, hungarian


class TestLanguageMenu:
    def test_menu_exists(self, qml_app):
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, "menuToolsLanguage") is not None

    def test_english_is_checked_by_default(self, menu_items):
        _window, controller, system, english, hungarian = menu_items
        assert controller.pendingLanguage == "en"
        assert system.property("checked") is False
        assert english.property("checked") is True
        assert hungarian.property("checked") is False

    def test_names_are_the_official_own_language_names(self, menu_items):
        _window, _controller, _system, english, hungarian = menu_items
        assert english.property("text") == "English (US)"  # Lang::enUS
        assert hungarian.property("text") == "Magyar"

    def test_clicking_hungarian_opens_a_confirmation(self, menu_items, qt_app):
        window, controller, _system, _english, _hungarian = menu_items
        _menu_tetelre_kattint(window, qt_app, "menuLanguageHungarian")
        assert _var(qt_app, lambda: _kerdes_nyitva(window)), "a kérdés nem nyílt meg"
        assert controller.pendingLanguage == "en", (
            "#3555: a menüpont önmagában nem válthat, csak kérdez"
        )
        uzenet = _gyerek(window, "menuLanguageConfirmMessageLabel").property("text")
        assert uzenet.startswith("Change the language Picasa uses?")

    def test_yes_click_queues_for_the_next_start(self, menu_items, qt_app, monkeypatch):
        window, controller, _system, _english, _hungarian = menu_items
        monkeypatch.delenv("PICASAPY_LANG", raising=False)
        settings = controller._get_settings()
        _menu_tetelre_kattint(window, qt_app, "menuLanguageHungarian")
        _valaszol(window, qt_app, igen=True)

        assert controller.pendingLanguage == "hu"
        assert controller.language == "en", (
            "#3555: a futó felület nyelve a következő indításig nem vált"
        )
        # futás közben az alkalmazás nyelve a régi marad…
        assert application._configured_language(settings) == "en"
        # …a következő indítás viszont a függő választást tölti be
        assert application._startup_language(settings) == "hu"

    def test_no_click_changes_nothing(self, menu_items, qt_app, monkeypatch):
        window, controller, _system, english, hungarian = menu_items
        monkeypatch.delenv("PICASAPY_LANG", raising=False)
        settings = controller._get_settings()
        _menu_tetelre_kattint(window, qt_app, "menuLanguageHungarian")
        _valaszol(window, qt_app, igen=False)

        assert controller.pendingLanguage == "en"
        assert controller.language == "en"
        assert english.property("checked") is True
        assert hungarian.property("checked") is False
        assert application._startup_language(settings) == "en"

    def test_check_marks_follow_the_pending_setting(self, menu_items, qt_app):
        window, _controller, system, english, hungarian = menu_items
        _menu_tetelre_kattint(window, qt_app, "menuLanguageHungarian")
        _valaszol(window, qt_app, igen=True)
        assert hungarian.property("checked") is True
        assert english.property("checked") is False
        assert system.property("checked") is False

        _menu_tetelre_kattint(window, qt_app, "menuLanguageEnglish")
        _valaszol(window, qt_app, igen=True)
        assert english.property("checked") is True
        assert hungarian.property("checked") is False

    def test_clicking_the_pending_entry_asks_nothing(self, menu_items, qt_app):
        window, controller, _system, english, _hungarian = menu_items
        _menu_tetelre_kattint(window, qt_app, "menuLanguageEnglish")
        qt_app.processEvents()
        assert not _kerdes_nyitva(window)
        assert controller.pendingLanguage == "en"
        assert english.property("checked") is True

    def test_system_entry_label_has_the_locale_suffix(self, menu_items):
        _window, controller, system, _english, _hungarian = menu_items
        assert controller.systemLanguageSuffix in system.property("text")

    def test_choosing_system_opens_a_confirmation_and_applies(self, menu_items, qt_app):
        window, controller, system, _english, _hungarian = menu_items
        _menu_tetelre_kattint(window, qt_app, "menuLanguageSystem")
        _valaszol(window, qt_app, igen=True)
        assert controller.pendingLanguage == controller.systemLanguageCode
        assert system.property("checked") is True
