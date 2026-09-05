"""#1637: a jelszó-párbeszéd VISELKEDÉSE — a felület oldala.

A vezérlő kapuját a `tests/app/test_rejtett_jelszo_kapu_1637.py` méri. Ez a
fájl azt, hogy a párbeszéd maga helyesen viselkedik: az OK LÁTHATÓAN tiltott,
amíg nincs érvényes bevitel, és a hatókör-figyelmeztetés OTT VAN.

⚠️ A figyelmeztetés jelenléte állítás, nem stílus: a jegy kifejezetten
megköveteli, hogy a felület kimondja, ez nem fájl-szintű védelem.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent


@pytest.fixture
def parbeszed(qml_app):
    window, _controller, engine = qml_app
    komponens = QQmlComponent(engine)
    komponens.setData(
        b"""
        import QtQuick
        import QtQuick.Controls
        import PicasaPy 1.0
        ApplicationWindow { width: 700; height: 500
          HiddenPasswordDialog { } }
        """,
        QUrl(),
    )
    ablak = komponens.create()
    assert ablak is not None, komponens.errorString()
    yield ablak.findChild(QObject, "hiddenPasswordDialog")
    ablak.deleteLater()


def _mezo(p, nev):
    m = p.findChild(QObject, nev)
    assert m is not None, f"hiányzó vezérlő: {nev}"
    return m


class TestHatokorFigyelmeztetes:
    def test_a_figyelmeztetes_OTT_van_es_kimondja_a_lenyeget(self, parbeszed):
        szoveg = _mezo(parbeszed, "hiddenPasswordScopeWarning").property("text")
        assert szoveg, "a hatókör-figyelmeztetés üres"
        alacsony = szoveg.lower()
        assert "disk" in alacsony or "lemez" in alacsony, (
            "a figyelmeztetés nem mondja ki, hogy a fájlok a lemezen maradnak: "
            f"{szoveg!r}"
        )

    def test_MINDKET_modban_latszik(self, parbeszed, qt_app):
        for nyit in ("openUnlock", "openSet"):
            parbeszed.metaObject().invokeMethod(parbeszed, nyit)
            qt_app.processEvents()
            assert _mezo(parbeszed, "hiddenPasswordScopeWarning").property("visible"), (
                f"a hatókör-figyelmeztetés nem látszik a(z) {nyit} módban"
            )


class TestFeloldoMod:
    def test_ures_jelszoval_az_OK_TILTOTT(self, parbeszed, qt_app):
        parbeszed.metaObject().invokeMethod(parbeszed, "openUnlock")
        qt_app.processEvents()
        assert parbeszed.property("enteredPassword") == ""

    def test_a_masodik_mezo_es_a_kapcsolo_REJTVE_van(self, parbeszed, qt_app):
        parbeszed.metaObject().invokeMethod(parbeszed, "openUnlock")
        qt_app.processEvents()
        assert not _mezo(parbeszed, "hiddenPasswordVerify").property("visible")
        assert not _mezo(parbeszed, "hiddenPasswordModern").property("visible")


class TestBeallitoMod:
    def test_a_masodik_mezo_es_a_kapcsolo_LATSZIK(self, parbeszed, qt_app):
        parbeszed.metaObject().invokeMethod(parbeszed, "openSet")
        qt_app.processEvents()
        assert _mezo(parbeszed, "hiddenPasswordVerify").property("visible")
        assert _mezo(parbeszed, "hiddenPasswordModern").property("visible")

    def test_elteronel_a_NEM_EGYEZIK_uzenet_jon_elo(self, parbeszed, qt_app):
        parbeszed.metaObject().invokeMethod(parbeszed, "openSet")
        _mezo(parbeszed, "hiddenPasswordField").setProperty("text", "titok")
        _mezo(parbeszed, "hiddenPasswordVerify").setProperty("text", "masik")
        qt_app.processEvents()
        assert _mezo(parbeszed, "hiddenPasswordMismatch").property("visible")

    def test_egyezonel_az_uzenet_ELTUNIK(self, parbeszed, qt_app):
        parbeszed.metaObject().invokeMethod(parbeszed, "openSet")
        _mezo(parbeszed, "hiddenPasswordField").setProperty("text", "titok")
        _mezo(parbeszed, "hiddenPasswordVerify").setProperty("text", "titok")
        qt_app.processEvents()
        assert not _mezo(parbeszed, "hiddenPasswordMismatch").property("visible")

    def test_a_jelszo_mezok_NEM_lathato_szoveget_mutatnak(self, parbeszed):
        """A jelszó nem jelenhet meg olvashatóan a képernyőn.

        Az `echoMode` enumot a Python oldaláról nem lehet kiolvasni
        („Can't find converter"), ezért a QML maga adja meg logikai
        alakban — enélkül ez az állítás mérhetetlen volna."""
        assert parbeszed.property("jelszoRejtve") is True


class TestJelszoTorles:
    """#1637: a beállított jelszó LEVEHETŐ a felületről.

    A vezérlőnek megvolt a törlő tagja, csak nem vezetett hozzá út a
    felületről — a felhasználó egyszer beállította volna a jelszót, és soha
    többé nem tud megszabadulni tőle. A képesség-őr (#1476) fogta meg.

    ⚠️ A gombra KATTINTUNK, nem a jelet emitáljuk: a néma vezérlő (rossz
    `visible`, elgépelt `objectName`) csak így derül ki.
    """

    def test_nincs_torles_gomb_amig_nincs_jelszo(self, parbeszed, qt_app):
        parbeszed.setProperty("jelszoLetezik", False)
        parbeszed.metaObject().invokeMethod(parbeszed, "openSet")
        qt_app.processEvents()
        assert not _mezo(parbeszed, "hiddenPasswordClear").property("visible"), (
            "a törlés akkor is felkínálva, amikor nincs beállított jelszó"
        )

    def test_a_torles_gomb_latszik_ha_van_jelszo(self, parbeszed, qt_app):
        parbeszed.setProperty("jelszoLetezik", True)
        parbeszed.metaObject().invokeMethod(parbeszed, "openSet")
        qt_app.processEvents()
        assert _mezo(parbeszed, "hiddenPasswordClear").property("visible"), (
            "beállított jelszó mellett sem látszik a törlés"
        )

    def test_a_feloldas_modban_NINCS_torles(self, parbeszed, qt_app):
        """Feloldáskor a jelszót nem lehet egy kattintással megkerülni."""
        parbeszed.setProperty("jelszoLetezik", True)
        parbeszed.metaObject().invokeMethod(parbeszed, "openUnlock")
        qt_app.processEvents()
        assert not _mezo(parbeszed, "hiddenPasswordClear").property("visible"), (
            "a feloldás módban is felkínálja a törlést — a kapu megkerülhető"
        )

    def test_a_KATTINTAS_jelez_es_bezar(self, parbeszed, qt_app):
        parbeszed.setProperty("jelszoLetezik", True)
        parbeszed.metaObject().invokeMethod(parbeszed, "openSet")
        qt_app.processEvents()

        jelzett = []
        parbeszed.torlesKert.connect(lambda: jelzett.append(True))
        gomb = _mezo(parbeszed, "hiddenPasswordClear")
        gomb.metaObject().invokeMethod(gomb, "clicked")
        qt_app.processEvents()

        assert jelzett == [True], "a törlés gombja nem jelzett a gazdának"
        assert not parbeszed.property("visible"), (
            "a törlés után a párbeszéd nyitva maradt"
        )
