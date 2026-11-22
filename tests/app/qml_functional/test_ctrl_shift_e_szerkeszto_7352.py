"""#7352: a Ctrl+Shift+E a szerkesztőben is a Jó napom van műveletet futtatja.

Az eredetiben a billentyű a szerkesztőben is a Jó napom van eszközt aktiválja
(`0x005e638b` -> `0x005fe370(panel, "enhance")`, mérés: `job-810`: a csempe
elhalványul, az Undo felirat a műveletet nevezi meg). Nálunk a kötés csak a
könyvtárban élt: a `viewerOpen` kapu a nézőben letiltotta.

Mérce: valódi billentyűleütés (`QTest.keyClick`) a megnyitott nézőben. Parancsot
nem hívunk közvetlenül. A hatást a felhasználó felől mérjük: a Jó napom van
csempe elhalványul, az Undo felirat nevezi a műveletet, és a lemezen a
`.picasa.ini` a `filters=enhance=1;` sort kapja. A könyvtári út (egy- és
többképes kijelölés) külön ellenőrzött: ott a hatás változatlan.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from _szerkeszto_5150_helpers import (
    item,
    kattint,
    nyitott_panel,
    szerkeszto,
    varj,
)

CTRL_SHIFT = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
KULCS = "enhance=1;"


def _ini(tmp_path: Path) -> str:
    ut = tmp_path / "kepek" / ".picasa.ini"
    return ut.read_text(encoding="utf-8") if ut.is_file() else ""


def _blokk(ini: str, fajl: str) -> str:
    """A `[fajl]` szakasz szövege (üres, ha nincs ilyen)."""
    resz = ini.split(f"[{fajl}]", 1)
    if len(resz) < 2:
        return ""
    return resz[1].split("\n[", 1)[0]


def _ctrl_shift_e(window, qt_app) -> None:
    """Valódi (spontán) Ctrl+Shift+E az ablakon."""
    window.requestActivate()
    QTest.keyClick(window, Qt.Key.Key_E, CTRL_SHIFT)
    for _ in range(5):
        qt_app.processEvents()


def _nyitott_nezo(qml_app, qt_app):
    window, _controller, viewer, panel = nyitott_panel(qml_app, qt_app)
    return window, viewer, panel, szerkeszto(viewer)


class TestSzerkesztoben:
    def test_a_billentyu_a_jo_napom_van_muveletet_futtatja(
        self, qml_app_negyzet_kepek, qt_app, tmp_path
    ):
        window, viewer, panel, szerk = _nyitott_nezo(qml_app_negyzet_kepek, qt_app)
        csempe = item(window, "editToolEnhance")
        assert csempe.property("enabled") is True, "a próba feltétele: a csempe él"
        assert szerk.property("undoAction") != "enhance", (
            "a próba feltétele: a Jó napom van még nincs a láncon"
        )

        _ctrl_shift_e(window, qt_app)

        assert varj(qt_app, lambda: szerk.property("undoAction") == "enhance"), (
            "a Ctrl+Shift+E a szerkesztőben nem futtatta a Jó napom van műveletet"
        )
        assert varj(qt_app, lambda: csempe.property("enabled") is False), (
            "a Jó napom van csempe nem halványult el a művelet után"
        )
        assert "I'm Feeling Lucky" in str(panel.property("undoLabel")), (
            "az Undo felirat nem nevezi meg a Jó napom van műveletet"
        )
        assert varj(
            qt_app, lambda: KULCS in _blokk(_ini(tmp_path), "a.jpg")
        ), "a művelet nem került a megnyitott kép .picasa.ini láncába"
        assert KULCS not in _blokk(_ini(tmp_path), "b.jpg"), (
            "a másik kép is megkapta az effektet"
        )

    def test_a_masodik_leutes_nem_halmozza_a_muveletet(
        self, qml_app_negyzet_kepek, qt_app, tmp_path
    ):
        """A csempe a lánc végén álló Jó napom van után tiltott: a billentyű is."""
        window, _viewer, _panel, szerk = _nyitott_nezo(qml_app_negyzet_kepek, qt_app)
        _ctrl_shift_e(window, qt_app)
        assert varj(qt_app, lambda: szerk.property("undoAction") == "enhance")

        _ctrl_shift_e(window, qt_app)

        assert _blokk(_ini(tmp_path), "a.jpg").count(KULCS) == 1, (
            "a második leütés újabb Jó napom van réteget tett a láncra"
        )

    def test_szovegmezoben_gepelve_nem_sul_el(
        self, qml_app_negyzet_kepek, qt_app, tmp_path
    ):
        window, _viewer, _panel, szerk = _nyitott_nezo(qml_app_negyzet_kepek, qt_app)
        felirat = item(window, "captionField")
        QMetaObject.invokeMethod(
            felirat, "forceActiveFocus", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        fokusz = window.activeFocusItem()
        assert fokusz is not None and fokusz.property("selectedText") is not None, (
            "a próba feltétele: szövegmezőn áll a fókusz"
        )

        _ctrl_shift_e(window, qt_app)

        assert szerk.property("undoAction") != "enhance", (
            "szövegmezőben gépeléskor a Ctrl+Shift+E lefuttatta a műveletet"
        )
        assert KULCS not in _ini(tmp_path), "a lánc megváltozott a szövegmezőben"

    @pytest.mark.parametrize(
        ("csempe", "allapot"),
        [
            ("editToolRetouch", "retouchActive"),
            ("editToolRedeye", "redeyeActive"),
            ("editToolTilt", "tiltActive"),
        ],
    )
    def test_nyitott_eszkoz_kozben_nem_sul_el(
        self, qml_app_negyzet_kepek, qt_app, tmp_path, csempe, allapot
    ):
        """Mód-eszköznél a csempe-rács el van takarva: a billentyű sem fut."""
        window, _viewer, panel, szerk = _nyitott_nezo(qml_app_negyzet_kepek, qt_app)
        kattint(window, item(window, csempe), qt_app)
        assert varj(qt_app, lambda: panel.property(allapot) is True), (
            f"a próba feltétele: a {csempe} eszköz nyitva van"
        )

        _ctrl_shift_e(window, qt_app)

        assert szerk.property("undoAction") != "enhance", (
            f"a {allapot} eszköz nyitva, mégis lefutott a Jó napom van"
        )
        assert KULCS not in _ini(tmp_path), "a lánc megváltozott nyitott eszköz mellett"


def _videos_konyvtar(lib: Path) -> None:
    from PIL import Image

    Image.new("RGB", (600, 600), (255, 0, 0)).save(lib / "a.jpg")
    # A scannernek elég a kiterjesztés; a videót sosem dekódoljuk.
    (lib / "c-video.mp4").write_bytes(b"fake video; never decoded")


@pytest.fixture
def qml_app_videos(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_videos_konyvtar)


def test_videon_a_szerkeszto_nem_erintett(qml_app_videos, qt_app, tmp_path, capfd):
    """Videónál a szerkesztő-eszközök nem értelmezettek: a billentyű no-op.

    Védőkapu nélkül a vezérlő `toggleTool`-ja `ValueError`-t dobna (nincs aktív
    szerkesztés): a Python-slot kivétele csak a hibakimenetre nyomtatódik, ezért
    azt a `capfd` olvassa, és a hiányát követeli meg."""
    window, _controller, _engine = qml_app_videos
    window.requestActivate()
    window.setProperty("viewerOpen", True)
    viewer = item(window, "photoViewer")
    viewer.setProperty("currentIndex", 1)
    for _ in range(8):
        qt_app.processEvents()
    assert viewer.property("isCurrentVideo") is True, (
        "a próba feltétele: a megnyitott elem videó"
    )

    capfd.readouterr()  # a megnyitás zaját (pl. a videó-dekóder üzenetei) eldobjuk

    _ctrl_shift_e(window, qt_app)

    hibakimenet = capfd.readouterr().err
    assert "ValueError" not in hibakimenet, (
        f"a billentyű kivételt dobott videón:\n{hibakimenet}"
    )
    assert KULCS not in _ini(tmp_path), "videóra is bekerült a Jó napom van"


class TestKonyvtarban:
    @pytest.mark.parametrize(
        ("kijelolt", "kijeloletlen"),
        [([0], [1]), ([0, 1], [])],
        ids=["egykepes", "tobbkepes"],
    )
    def test_a_hatas_valtozatlanul_a_kijeloltekre_kerul(
        self, qml_app_negyzet_kepek, qt_app, tmp_path, kijelolt, kijeloletlen
    ):
        window, controller, _engine = qml_app_negyzet_kepek
        window.show()
        window.requestActivate()
        assert varj(qt_app, lambda: controller.photos.rowCount() == 2), (
            "a próbakönyvtár két képe nem töltődött be"
        )
        assert window.property("viewerOpen") is not True
        window.setProperty("selectedIndexes", kijelolt)
        window.setProperty("selectedIndex", kijelolt[0])
        qt_app.processEvents()
        nevek = {0: "a.jpg", 1: "b.jpg"}

        _ctrl_shift_e(window, qt_app)

        for sor in kijelolt:
            assert varj(
                qt_app, lambda sor=sor: KULCS in _blokk(_ini(tmp_path), nevek[sor])
            ), f"a könyvtári Ctrl+Shift+E nem írta a {nevek[sor]} láncába a Jó napom van"
        for sor in kijeloletlen:
            assert KULCS not in _blokk(_ini(tmp_path), nevek[sor]), (
                f"a kijelöletlen {nevek[sor]} is megkapta az effektet"
            )
