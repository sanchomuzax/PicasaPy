"""Az album-fejléc két hiányzó gombja és a számlálós feliratok — #1823.

A fejlécen az eredeti Picasában két olyan gomb van, ami nálunk nem volt
sehol: **`save_edits`** („Save edited photos to disk") és **`select_star`**
(„Select starred photos"). A csillag helyén eddig egy néma díszcsempe állt
— se `objectName`, se kezelő.

## A számlálós felirat

A bináris erőforrásai minden fejléc-gombot KÉT alakban tartanak — sima és
`%d`-s (`albumbutton_save` · `albumbutton_save%d`) —, vagyis a gomb kiírja,
hány elemre hatna, és üres kijelölésnél a szám nélküli alakra vált.

⚠️ A `play` gombra ez NEM igaz: a mért listában (`save`, `sstar`, `sall`,
`album`, `cd`, `menu`, `pubaction`) **nincs `play%d`**. A jegy „a `play` és
a jövőbeli gombok is" mondata ezen a ponton a mérésnek mond ellent, ezért a
diavetítés ikon marad. Ezt az eltérést itt is kimondjuk, hogy egy későbbi
kör ne „hiányosságként" javítsa vissza.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import picasapy.app.application as app_module
import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent

_KEEP_ALIVE: list = []

_TS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")
_FEED = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "LightboxFeed.qml"
).read_text(encoding="utf-8")
_MAIN = (
    Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
).read_text(encoding="utf-8")


def _make_header(engine, **props):
    comp = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml")
        ),
    )
    _KEEP_ALIVE.append(comp)
    header = comp.createWithInitialProperties(props)
    assert comp.errors() == [], comp.errors()
    assert header is not None
    _KEEP_ALIVE.append(header)
    return header


class TestAKetHianyzoGomb:
    @pytest.mark.parametrize(
        "nev", ["headerSelectStarredButton", "headerSaveEditsButton"]
    )
    def test_ott_van_a_fejlecen(self, qml_app, nev):
        _, _, engine = qml_app
        header = _make_header(engine, folderName="Nyaralás")
        assert header.findChild(QObject, nev) is not None

    def test_a_csillag_gomb_JELET_ad(self, qml_app):
        """Eddig néma díszcsempe volt — most kattintható parancs."""
        _, _, engine = qml_app
        header = _make_header(engine, folderName="Nyaralás")
        kaptunk = []
        header.selectStarredRequested.connect(lambda: kaptunk.append(1))
        header.findChild(QObject, "headerSelectStarredButton").clicked.emit()
        assert kaptunk == [1]

    def test_a_mentes_gomb_JELET_ad(self, qml_app):
        _, _, engine = qml_app
        header = _make_header(engine, folderName="Nyaralás", selectedCount=2)
        kaptunk = []
        header.saveEditsRequested.connect(lambda: kaptunk.append(1))
        header.findChild(QObject, "headerSaveEditsButton").clicked.emit()
        assert kaptunk == [1]

    def test_ures_kijelolesnel_a_mentes_TILTOTT(self, qml_app):
        """A mentés a KIJELÖLTEKRE hat — kijelölés nélkül nincs mit menteni."""
        _, _, engine = qml_app
        header = _make_header(engine, folderName="Nyaralás", selectedCount=0)
        gomb = header.findChild(QObject, "headerSaveEditsButton")
        assert gomb.property("enabled") is False


class TestASzamlalosFelirat:
    @pytest.mark.parametrize(
        "nev,alap",
        [
            ("headerSaveEditsButton", "Save"),
            ("headerUploadButton", "Upload"),
            ("headerSelectStarredButton", "☆"),
        ],
    )
    def test_ures_kijelolesnel_NINCS_szam(self, qml_app, nev, alap):
        _, _, engine = qml_app
        header = _make_header(engine, folderName="N", selectedCount=0)
        felirat = header.findChild(QObject, nev).property("text")
        assert "(" not in felirat, f"{nev}: üres kijelölésnél is számot ír"

    @pytest.mark.parametrize(
        "nev", ["headerSaveEditsButton", "headerUploadButton",
                "headerSelectStarredButton"]
    )
    def test_kijelolesnel_a_DARABSZAM_all_a_feliratban(self, qml_app, nev):
        _, _, engine = qml_app
        header = _make_header(engine, folderName="N", selectedCount=3)
        assert "(3)" in header.findChild(QObject, nev).property("text")

    def test_a_felirat_KOVETI_a_kijelolest(self, qml_app):
        """Nem induláskori érték: a kötésnek futásidőben át kell írnia."""
        _, _, engine = qml_app
        header = _make_header(engine, folderName="N", selectedCount=0)
        gomb = header.findChild(QObject, "headerSaveEditsButton")
        assert "(" not in gomb.property("text")
        header.setProperty("selectedCount", 7)
        assert "(7)" in gomb.property("text")

    def test_a_diavetites_ikon_marad_szam_nelkul(self, qml_app):
        """A mért erőforrás-listában NINCS `play%d` — ld. a modul docstringjét."""
        _, _, engine = qml_app
        header = _make_header(engine, folderName="N", selectedCount=5)
        play = header.findChild(QObject, "headerPlayButton")
        assert play is not None
        assert "5" not in str(play.property("text") or "")


class TestABekotes:
    """A gomb csak akkor ér valamit, ha a parancsig eljut a kattintás."""

    def test_a_feed_atadja_a_kijeloles_darabszamat(self):
        assert "selectedCount: grid.appWindow" in _FEED

    def test_a_feed_bekoti_a_ket_jelet(self):
        assert "onSelectStarredRequested" in _FEED
        assert "grid.appWindow.selectStarred()" in _FEED
        assert "onSaveEditsRequested" in _FEED
        assert "grid.appWindow.saveSelectedEdits()" in _FEED

    def test_a_gazdaablaknak_VAN_ilyen_fuggvenye(self):
        """A #1153 osztálya: a jel elmegy, de a másik oldalon nincs, aki
        felvegye. Mindkét hívott függvénynek léteznie kell a Main.qml-ben."""
        assert "function selectStarred()" in _MAIN
        assert "function saveSelectedEdits()" in _MAIN

    def test_a_mentes_a_MEGLEVO_parbeszedet_nyitja(self):
        """Nem új mentés-út: a #444 párbeszéde, biztonsági mentéssel."""
        kezd = _MAIN.index("function saveSelectedEdits()")
        assert "saveDialogs.ensure().openSave(" in _MAIN[kezd : kezd + 220]


class TestAFeliratok:
    @pytest.mark.parametrize(
        "angol,magyar",
        [
            ("Select starred photos", "Csillagozott képek kijelölése"),
            ("Save edited photos to disk", "A szerkesztett képek mentése lemezre"),
            ("Save", "Mentés"),
        ],
    )
    def test_le_van_forditva(self, angol, magyar):
        assert f"<source>{angol}</source>" in _TS
        assert f"<translation>{magyar}</translation>" in _TS
