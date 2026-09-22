"""#2187 — a javaslat-szűrő (`sug_filter`) a személy-album fejlécén.

MÉRT geometria (`respack.yt`, a jegy 15.6 táblája): `sug_filter`
**29 × 27**, a helye **(316,55)** — közvetlenül a jóváhagyás-pár
((348,55)) BAL oldalán. MÉRT súgó (`faceheaderpaneltext.tre:35`):
„Show only suggestions (when toggled on)".

Amit ez a fájl MÉR: a gomb létét, méretét, a sorrendjét a jóváhagyás-párhoz
képest, a láthatósági feltételét, a súgó szövegét és azt, hogy a
kattintás az ELLENKEZŐ állapotot kéri (a kötés nem szakad el).

Amit NEM mér: hogy a rács tényleg szűkül-e — az a vezérlő dolga
(`tests/app/test_javaslat_szuro_2187.py`), és hogy a gomb a képernyőn
tényleg látszik-e a mért képponton.
"""

from __future__ import annotations

import picasapy.app.application as app_module
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent

_KEEP_ALIVE: list = []


def _fejlec(engine, **props):
    comp = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml")
        ),
    )
    _KEEP_ALIVE.append(comp)
    fejlec = comp.createWithInitialProperties(props)
    assert comp.errors() == [], comp.errors()
    assert fejlec is not None
    _KEEP_ALIVE.append(fejlec)
    return fejlec


def _gomb(fejlec, nev="headerSuggestionFilterButton"):
    gomb = fejlec.findChild(QObject, nev)
    assert gomb is not None, f"{nev} nem található"
    return gomb


class TestLathatosag:
    def test_mappa_fejlecen_nincs(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, folderName="Nyaralás", personName="")
        assert _gomb(fejlec).property("visible") is False

    def test_javaslattal_latszik(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=3)
        assert _gomb(fejlec).property("visible") is True

    def test_javaslat_nelkul_nem_latszik(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=0)
        assert _gomb(fejlec).property("visible") is False

    def test_bekapcsolva_akkor_is_latszik_ha_elfogytak(self, qml_app):
        """Az utolsó javaslat jóváhagyása után a darabszám nullára esik. Ha
        a gomb ilyenkor eltűnne, a rács bent ragadna az üres, szűrt
        nézetben — visszakapcsolás nélkül."""
        _, _, engine = qml_app
        fejlec = _fejlec(
            engine, personName="Anna", suggestionCount=0, suggestionsOnly=True
        )
        assert _gomb(fejlec).property("visible") is True


class TestGeometria:
    def test_a_mert_29x27(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=3)
        gomb = _gomb(fejlec)
        assert gomb.property("width") == 29
        assert gomb.property("height") == 27

    def test_a_jovahagyas_elott_all(self, qml_app):
        """MÉRT sorrend: a szűrő (316) a jóváhagyás-pár (348) BAL oldalán."""
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=3)
        szuro = _gomb(fejlec)
        jovahagy = _gomb(fejlec, "headerConfirmSuggestionsButton")
        assert szuro.property("x") < jovahagy.property("x")

    def test_a_jovahagyas_nem_log_ra(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=3)
        szuro = _gomb(fejlec)
        jovahagy = _gomb(fejlec, "headerConfirmSuggestionsButton")
        assert (jovahagy.property("x")
                >= szuro.property("x") + szuro.property("width"))

    def test_a_tovabbi_javaslatok_is_utana_all(self, qml_app):
        """Nulla javaslatnál a `moresug` veszi át a helyet — az sem
        csúszhat a szűrő alá, amikor az ki van kapcsolva."""
        _, _, engine = qml_app
        fejlec = _fejlec(
            engine, personName="Anna", suggestionCount=0, suggestionsOnly=True
        )
        szuro = _gomb(fejlec)
        tovabbi = _gomb(fejlec, "headerMoreSuggestionsButton")
        assert (tovabbi.property("x")
                >= szuro.property("x") + szuro.property("width"))


class TestJelzes:
    def test_kikapcsoltbol_bekapcsolast_ker(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(
            engine, personName="Anna", suggestionCount=3, suggestionsOnly=False
        )
        kert = []
        fejlec.suggestionsOnlyToggled.connect(lambda csak: kert.append(csak))
        _gomb(fejlec).clicked.emit()
        assert kert == [True]

    def test_bekapcsoltbol_kikapcsolast_ker(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(
            engine, personName="Anna", suggestionCount=3, suggestionsOnly=True
        )
        kert = []
        fejlec.suggestionsOnlyToggled.connect(lambda csak: kert.append(csak))
        _gomb(fejlec).clicked.emit()
        assert kert == [False]

    def test_a_pipa_a_vezerlo_allapotat_koveti(self, qml_app):
        """#1468 rádió-csapda: a kattintás után a gomb NEM a saját belső
        állapotát mutatja, hanem a gazdáét — a kötést vissza kell állítani.
        Itt a gazda állapota nem változik (nincs bekötve vezérlő), tehát a
        gomb a kattintás után is kikapcsolt marad."""
        _, _, engine = qml_app
        fejlec = _fejlec(
            engine, personName="Anna", suggestionCount=3, suggestionsOnly=False
        )
        gomb = _gomb(fejlec)
        gomb.clicked.emit()
        assert gomb.property("checked") is False


class TestSugo:
    def test_a_sugo_a_mert_angol_alak(self, qml_app):
        """A buboréksúgó csatolt tulajdonság — a QML-objektumról nem
        olvasható ki `property()`-vel, ezért a FORRÁST méri. Amit ez nem
        mér: hogy a súgó a képernyőn tényleg megjelenik-e."""
        forras = (
            app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml"
        ).read_text(encoding="utf-8")
        assert (
            'ToolTip.text: qsTr("Show only suggestions (when toggled on)")'
            in forras
        )
