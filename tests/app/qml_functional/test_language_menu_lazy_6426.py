"""#6426: a nyelvek saját nevét tartalmazó menüpontok csak nyitáskor épülnek fel."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest

from tests.support.varakozas import var_feltetelre


def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _gyerek(window, nev):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(window, qt_app, elem) -> None:
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


def _lathato(window, feltetel):
    sor = [window.contentItem().parentItem() or window.contentItem()]
    while sor:
        elem = sor.pop()
        if elem.isVisible() and feltetel(elem):
            return elem
        sor.extend(elem.childItems())
    return None


def _nyelv_menu_megnyit(window, qt_app):
    eszkozok = _lathato(
        window,
        lambda elem: "MenuBarItem" in elem.metaObject().className()
        and elem.property("text") == "&Tools",
    )
    assert eszkozok is not None, "az Eszközök menü nincs a menüsávon"
    _kattints(window, qt_app, eszkozok)

    nyelv = None

    def _nyelv_tetel_megjelent():
        nonlocal nyelv
        nyelv = _lathato(
            window,
            lambda elem: "MenuItem" in elem.metaObject().className()
            and elem.property("text") == "Language",
        )
        return nyelv is not None

    assert _var(qt_app, _nyelv_tetel_megjelent), "az Eszközök menüben nincs Nyelv tétel"
    _kattints(window, qt_app, nyelv)
    menu = _gyerek(window, "menuToolsLanguage")
    assert _var(qt_app, lambda: menu.property("opened") is True), (
        "a Nyelv almenü nem nyílt meg"
    )
    return menu


def _menu_adatok(menu, kifejezes: str) -> list[str]:
    qml = QQmlExpression(qmlContext(menu), menu, kifejezes)
    eredmeny, hiba = qml.evaluate()
    assert not hiba, qml.error()
    return str(eredmeny).split("|") if eredmeny else []


def _menupont_nev(code: str) -> str:
    return {
        "en": "menuLanguageEnglish",
        "hu": "menuLanguageHungarian",
    }.get(code, f"menuLanguage{code}")


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_a_nyelv_almenu_csak_elso_megnyitaskor_epiti_fel_a_teteleket(
    qml_app, qt_app, magassag_elteres
):
    window, controller, _engine = qml_app
    alapmagassag = float(window.property("height"))
    window.setProperty("height", alapmagassag + magassag_elteres)
    qt_app.processEvents()
    menu = _gyerek(window, "menuToolsLanguage")
    tovabbi = _gyerek(window, "menuLanguageAdditionalChoices")

    assert menu.property("opened") is False
    assert int(tovabbi.property("count")) == 0
    assert window.findChild(QObject, "menuLanguagede") is None

    nyelvek = list(controller.availableLanguages)
    tovabbi_darab = len([code for code in nyelvek if code not in ("en", "hu")])
    kivalsztott = controller.pendingLanguage
    pipa_nev = (
        "menuLanguageSystem"
        if kivalsztott == controller.systemLanguageCode
        else _menupont_nev(kivalsztott)
    )
    menu = _nyelv_menu_megnyit(window, qt_app)
    tovabbi = _gyerek(window, "menuLanguageAdditionalChoices")
    assert _var(qt_app, lambda: int(tovabbi.property("count")) == tovabbi_darab), (
        "az almenü megnyitásakor nem jött létre minden nyelvi tétel"
    )

    nevek = _menu_adatok(
        menu,
        "(function () { var r = []; for (var i = 0; i < count; ++i) "
        "r.push(itemAt(i).objectName); return r.join('|'); })()",
    )
    assert nevek == [
        "menuLanguageSystem",
        *[_menupont_nev(code) for code in nyelvek],
    ]

    pipak = _menu_adatok(
        menu,
        "(function () { var r = []; for (var i = 0; i < count; ++i) "
        "if (itemAt(i).checked) r.push(itemAt(i).objectName); "
        "return r.join('|'); })()",
    )
    assert pipak == [pipa_nev]
