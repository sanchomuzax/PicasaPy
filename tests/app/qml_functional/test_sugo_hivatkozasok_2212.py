"""#2212 — a súgó kék hivatkozásaira kattintva megnyílik a fejezet.

A nyitólap a súgó **tartalomjegyzéke**: 18 hivatkozás. Kezelő nélkül
kékek voltak, de a kattintás nem csinált semmit — a felhasználó jelentette
(2026-09-03).

⚠️ A próbák a **jelet bocsátják ki** (`linkActivated`), amit a valódi
kattintás is kivált, nem a Python-metódust hívják közvetlenül: máskülönben
zöldek lennének akkor is, ha a QML-oldali kötés hiányzik.
"""

from __future__ import annotations

import re
import time

from PySide6.QtCore import QMetaObject, QObject, Q_ARG, Qt


def _gyerek(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"nincs ilyen elem: {nev}"
    return obj


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


def _nyisd_meg_a_sugot(window, qt_app):
    tetel = _gyerek(window, "menuHelpContents")
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    assert _var(qt_app, lambda: window.findChild(QObject, "helpDialog") is not None)
    return _gyerek(window, "helpDialog")


def _kattints_a_hivatkozasra(nezo, link, qt_app):
    """A `linkActivated` jel kibocsátása — ezt adja a valódi kattintás is."""
    QMetaObject.invokeMethod(
        nezo,
        "linkActivated",
        Qt.ConnectionType.DirectConnection,
        Q_ARG(str, link),
    )
    qt_app.processEvents()


class TestAHivatkozasMegnyitjaAFejezetet:
    def test_a_nyitolap_elso_hivatkozasa_atvisz(self, qml_app, qt_app):
        window, controller, _e = qml_app
        parbeszed = _nyisd_meg_a_sugot(window, qt_app)
        nezo = _gyerek(window, "helpTopicText")

        kezdo = controller.helpHomeTopic
        parbeszed.setProperty("topic", kezdo)
        qt_app.processEvents()

        szoveg = controller.helpTopicText(kezdo)
        celok = re.findall(r"\[[^\]]*\]\(([^)]+)\)", szoveg)
        assert celok, "a nyitólapon nincs hivatkozás"

        _kattints_a_hivatkozasra(nezo, celok[0], qt_app)

        assert _var(qt_app, lambda: parbeszed.property("topic") != kezdo), (
            f"a {celok[0]!r} hivatkozásra kattintva a súgó nem lépett sehova"
        )
        assert parbeszed.property("topic") == controller.helpResolveLink(
            kezdo, celok[0]
        )

    def test_a_megnyilt_fejezet_SZOVEGE_is_valtozik(self, qml_app, qt_app):
        """Nem elég a `topic` átállítása — a néző is kövesse."""
        window, controller, _e = qml_app
        parbeszed = _nyisd_meg_a_sugot(window, qt_app)
        nezo = _gyerek(window, "helpTopicText")
        kezdo = controller.helpHomeTopic
        parbeszed.setProperty("topic", kezdo)
        qt_app.processEvents()
        regi_szoveg = nezo.property("text")

        celok = re.findall(
            r"\[[^\]]*\]\(([^)]+)\)", controller.helpTopicText(kezdo)
        )
        _kattints_a_hivatkozasra(nezo, celok[0], qt_app)

        assert _var(qt_app, lambda: nezo.property("text") != regi_szoveg), (
            "a néző szövege nem frissült a hivatkozás után"
        )


class TestAmiNEM_visz_sehova:
    def test_a_kulso_hivatkozas_nem_valt_fejezetet(self, qml_app, qt_app):
        window, controller, _e = qml_app
        parbeszed = _nyisd_meg_a_sugot(window, qt_app)
        nezo = _gyerek(window, "helpTopicText")
        kezdo = controller.helpHomeTopic
        parbeszed.setProperty("topic", kezdo)
        qt_app.processEvents()

        _kattints_a_hivatkozasra(nezo, "https://example.com/akarmi", qt_app)
        qt_app.processEvents()
        assert parbeszed.property("topic") == kezdo

    def test_az_utvonal_kilepes_nem_visz_ki(self, qml_app, qt_app):
        """A cél a felületről jön: `../../` nem vihet ki a csomagból."""
        window, controller, _e = qml_app
        parbeszed = _nyisd_meg_a_sugot(window, qt_app)
        nezo = _gyerek(window, "helpTopicText")
        kezdo = controller.helpHomeTopic
        parbeszed.setProperty("topic", kezdo)
        qt_app.processEvents()

        _kattints_a_hivatkozasra(nezo, "../../../etc/passwd", qt_app)
        qt_app.processEvents()
        assert parbeszed.property("topic") == kezdo


class TestAzAlmappabolIsMukodik:
    def test_egy_features_lap_hivatkozasai_feloldodnak(self, qml_app, qt_app):
        """A `features/` alatti lapokról a `../` a gyökérbe kell vigyen."""
        window, controller, _e = qml_app
        parbeszed = _nyisd_meg_a_sugot(window, qt_app)
        nezo = _gyerek(window, "helpTopicText")

        almappas = [
            t["nev"]
            for t in controller.helpTopics
            if "/" in t["nev"] and re.search(r"\[[^\]]*\]\(([^)]+)\)",
                                             controller.helpTopicText(t["nev"]))
        ]
        if not almappas:
            import pytest

            pytest.skip("ma nincs almappás lap hivatkozással")

        honnan = almappas[0]
        parbeszed.setProperty("topic", honnan)
        qt_app.processEvents()
        cel = re.findall(
            r"\[[^\]]*\]\(([^)]+)\)", controller.helpTopicText(honnan)
        )[0]

        _kattints_a_hivatkozasra(nezo, cel, qt_app)
        vart = controller.helpResolveLink(honnan, cel)
        assert vart, f"a {honnan} lap {cel!r} hivatkozása nem oldható fel"
        assert _var(qt_app, lambda: parbeszed.property("topic") == vart)
