"""#1773 — a jobb fiók négy lapja KIZÁRÓ rádiócsoport.

**A lelet.** Az eredeti Picasában a Tulajdonságok · Címkék · Emberek ·
Helyek panel közül egyszerre pontosan egy látszik. A vezérlő
(`0x005d9760`) mind a négy ágon ugyanazt a négylépéses mintát futtatja:
elrejti a másik hármat, kikapcsolja a másik három fejléc-gombot,
bekapcsolja a sajátját, megjeleníti a saját panelt.

**Amit MÉRTÜNK nálunk (a javítás előtt):** négy egymástól független
billenő, kizárás nélkül — mind a négy panel nyitva lehetett egyszerre.
Ez az eredetiben nem előfordulható állapot.

**Az aktív lapra kattintás.** A bináris a vizsgált ágon feltétel nélkül
`1`-re állítja a saját gombját, tehát a kattintás NEM zárja be a panelt.
A jegy ezt adja alapértelmezésnek; a teszt ezt is rögzíti, hogy egy
későbbi kör ne „javítsa vissza" billenőre észrevétlenül.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt

#: A négy lap: menütétel-objectName → panel-objectName → ablak-tulajdonság.
LAPOK = [
    ("menuViewProperties", "propertiesPanel", "propertiesPanelOpen"),
    ("menuViewTags", "tagsPanel", "tagsPanelOpen"),
    ("menuViewPeople", "peoplePanel", "peoplePanelOpen"),
    ("menuViewPlaces", "placesPanel", "placesPanelOpen"),
]


def _gyerek(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _nyisd(window, qt_app, menu_nev):
    QMetaObject.invokeMethod(
        _gyerek(window, menu_nev),
        "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()


def _nyitott_lapok(window) -> list[str]:
    return [
        panel
        for _menu, panel, _tul in LAPOK
        if _gyerek(window, panel).property("visible")
    ]


def _pipak(window) -> list[str]:
    return [
        menu
        for menu, _panel, _tul in LAPOK
        if _gyerek(window, menu).property("checked")
    ]


class TestKizaroCsoport:
    @pytest.mark.parametrize("menu,panel,tulajdonsag", LAPOK)
    def test_egy_lap_megnyitasa_bezarja_a_tobbit(
        self, qml_app, qt_app, menu, panel, tulajdonsag
    ):
        window, _controller, _engine = qml_app
        # előbb NYISSUNK MÁST, hogy a kizárásnak legyen mit becsuknia —
        # üres fiókból indulva a teszt akkor is átmenne, ha nincs kizárás
        masik = next(m for m, _p, _t in LAPOK if m != menu)
        _nyisd(window, qt_app, masik)
        assert _nyitott_lapok(window), "a felkészítő megnyitás nem hatott"

        _nyisd(window, qt_app, menu)

        assert _nyitott_lapok(window) == [panel], (
            f"a(z) {menu} megnyitása után {_nyitott_lapok(window)} látszik "
            "— az eredetiben egyszerre pontosan egy lap van nyitva (#1773)"
        )
        assert window.property(tulajdonsag) is True

    def test_mind_a_negy_sorban_megnyitva_is_egy_marad(
        self, qml_app, qt_app
    ):
        """A négy lap körbejárása — a fiók végig egy lapot mutat."""
        window, _controller, _engine = qml_app
        for menu, panel, _tul in LAPOK:
            _nyisd(window, qt_app, menu)
            assert _nyitott_lapok(window) == [panel], (
                f"{menu} után: {_nyitott_lapok(window)}"
            )

    def test_a_menu_pipai_a_lathatosagot_kovetik(self, qml_app, qt_app):
        """A `checkable + kötött checked` rádió-csapda ellen (#1464/#1468):
        a pipa nem ragadhat be és nem tűnhet el mind."""
        window, _controller, _engine = qml_app
        for menu, _panel, _tul in LAPOK:
            _nyisd(window, qt_app, menu)
            assert _pipak(window) == [menu], (
                f"{menu} megnyitása után a pipák: {_pipak(window)}"
            )


class TestAzAktivLapraKattintas:
    def test_nem_zarja_be_a_panelt(self, qml_app, qt_app):
        """A bináris a saját gombját feltétel nélkül `1`-re állítja."""
        window, _controller, _engine = qml_app
        menu, panel, tulajdonsag = LAPOK[0]

        _nyisd(window, qt_app, menu)
        assert _gyerek(window, panel).property("visible") is True

        _nyisd(window, qt_app, menu)

        assert _gyerek(window, panel).property("visible") is True, (
            "a MÁR AKTÍV lapra kattintás bezárta a panelt — a mért "
            "eredeti nem zárja be (#1773)"
        )
        assert window.property(tulajdonsag) is True


class TestAFiokBezarasa:
    def test_a_panel_sajat_bezaro_gombja_uriti_a_fiokot(
        self, qml_app, qt_app
    ):
        """Bezárás után egyik panel sem látszik, és pipa sem marad."""
        window, _controller, _engine = qml_app
        menu, panel, _tul = LAPOK[1]
        _nyisd(window, qt_app, menu)
        assert _gyerek(window, panel).property("visible") is True

        QMetaObject.invokeMethod(
            _gyerek(window, panel),
            "closeRequested",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert _nyitott_lapok(window) == []
        assert _pipak(window) == [], (
            f"a fiók bezárása után a menüben pipa maradt: {_pipak(window)}"
        )
