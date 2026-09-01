"""#1421 — a KIHELYEZETT eszköztárgombok (`newalbum`, `timelinebutton`).

## A lelet

A jegy szerint a felső eszköztár hét hiányzó gombja **hiányzó FUNKCIÓ**.
Mérve a mai kódon: **négynél ez már nem áll** — a funkció megvan, csak az
eszköztárról hiányzik. Az `newalbum` ezek egyike: a „Fájl ▸ Új album…"
párbeszéd és a `createAlbum()` vezérlő régóta él.

A bináris szerint a menütétel maga is a `thumbui/newalbum` **kattintást
szimulálja** (eszköztár-viselkedés spec, 2. szakasz) — vagyis a gomb és a
menüpont az eredetiben is UGYANAZ az út. Nálunk is: mindkettő a
`fileOpsDialogs.openNewAlbum()`-ot hívja.

## ⚠️ Amit a rejtés jelent

A gomb az eredetiben MINDIG aktív (a `.tre`-ben nincs feltétele). Nálunk
szűk ablaknál **elrejtőzik**, a szűrő-zóna mintájára (#423): minden fix
szélességű elem a sáv NEM zsugorodó alapját növeli, és a sávnak egyetlen
csíkban kell maradnia. Ez a MI alkalmazkodásunk, nem az eredeti
viselkedés — ezért méri külön teszt.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

_TOOLBAR = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/MainToolbar.qml"
)
_MAIN = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml/Main.qml"


class TestAGombLETEZIK:
    def test_ott_van_a_savon(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, "toolbarNewAlbumButton") is not None

    def test_IKONOS_es_nem_feliratos(self):
        """Az eredeti `newalbum` IKONOS (`newalbum_icon` 19 × 14).

        ⚠️ Először feliratos gombnak írtam meg, és a felirat-őr megfogta:
        a magyar „Új album" 15,1 × 24,5 a 19 × 22-es helyen — 2,5 px
        túllógás. A MÉRT méret maga mondta meg, hogy ikonnak kell lennie."""
        forras = _TOOLBAR.read_text(encoding="utf-8")
        kezdet = forras.index('objectName: "toolbarNewAlbumButton"')
        blokk = forras[kezdet : kezdet + 1200]
        assert 'text: qsTr("New Album")' not in blokk, "feliratos gomb — nem fér el"
        assert 'text: "＋"' in blokk

    def test_a_MERT_meretet_hasznalja(self):
        """29 × 22 — `konyvtar-ablak-meretek.md` 2. szakasz."""
        forras = _TOOLBAR.read_text(encoding="utf-8")
        kezdet = forras.index('objectName: "toolbarNewAlbumButton"')
        blokk = forras[kezdet : kezdet + 1200]
        assert "Layout.preferredWidth: 29" in blokk
        assert "Layout.preferredHeight: 22" in blokk

    def test_van_hozza_buboreksugo(self):
        """Az eredeti `newalbum` súgója — a gomb ikon-méretű, felirat nélkül
        nem lenne kitalálható."""
        forras = _TOOLBAR.read_text(encoding="utf-8")
        kezdet = forras.index('objectName: "toolbarNewAlbumButton"')
        assert "ToolTip.text" in forras[kezdet : kezdet + 1200]


class TestUGYANAZ_az_ut:
    def test_a_gomb_es_a_menu_ugyanoda_vezet(self):
        """A bináris szerint a menütétel a gomb kattintását szimulálja —
        nálunk is egy dialógus, egy út."""
        fo = _MAIN.read_text(encoding="utf-8")
        assert fo.count("onNewAlbumRequested: fileOpsDialogs.openNewAlbum") >= 2, (
            "a menü és az eszköztár nem ugyanahhoz a párbeszédhez köt"
        )


class TestAszukAblak:
    """#423: a sávnak egyetlen csíkban kell maradnia."""

    def test_szuk_ablaknal_elrejtozik(self):
        forras = _TOOLBAR.read_text(encoding="utf-8")
        kezdet = forras.index('objectName: "toolbarNewAlbumButton"')
        blokk = forras[kezdet : kezdet + 1200]
        assert "visible: !toolbar.toolbarCompact" in blokk

    def test_nem_novel_nem_zsugorodo_alapot(self):
        """`Layout.minimumWidth: 0` — a zsugorodási sorrend érintetlen.

        Fix `minimumWidth`-szel a sáv szűk ablaknál kilógna, és a #423
        egész zsugorodás-tervét elrontaná."""
        forras = _TOOLBAR.read_text(encoding="utf-8")
        kezdet = forras.index('objectName: "toolbarNewAlbumButton"')
        assert "Layout.minimumWidth: 0" in forras[kezdet : kezdet + 1200]


class TestIdorendGomb:
    """A második kihelyezett gomb: a NÉZET megvolt, a gomb hiányzott."""

    def test_ott_van_a_savon(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, "toolbarTimelineButton") is not None

    def test_a_MERT_meretet_hasznalja(self):
        """132 × 28 — `konyvtar-ablak-meretek.md` 2. szakasz.

        Ez az EGYETLEN feliratos a kihelyezett gombok közül, és épp azért
        fér bele a szöveg, mert a mért hely ekkora. Az `newalbum` 29 × 22-je
        nem fért — ott a méret mondta meg, hogy ikonnak kell lennie."""
        forras = _TOOLBAR.read_text(encoding="utf-8")
        kezdet = forras.index('objectName: "toolbarTimelineButton"')
        blokk = forras[kezdet : kezdet + 900]
        assert "Layout.preferredWidth: 132" in blokk
        assert "Layout.preferredHeight: 28" in blokk

    def test_a_nyitott_nezetet_JELZI(self):
        """A gomb váltó — a Ctrl+5 és a menütétel ugyanezt kapcsolja.

        Enélkül a `timelineActive` holt kötés lenne, és a felhasználó sem
        látná, hogy a gomb be van nyomva."""
        forras = _TOOLBAR.read_text(encoding="utf-8")
        kezdet = forras.index('objectName: "toolbarTimelineButton"')
        assert "toolbar.timelineActive" in forras[kezdet : kezdet + 900]

    def test_ugyanaz_az_ut_mint_a_menu(self):
        fo = _MAIN.read_text(encoding="utf-8")
        assert fo.count("onTimelineRequested: window.toggleTimeline()") >= 2, (
            "a menü és az eszköztár nem ugyanazt a váltást hívja"
        )

    def test_szuk_ablaknal_elrejtozik(self):
        forras = _TOOLBAR.read_text(encoding="utf-8")
        kezdet = forras.index('objectName: "toolbarTimelineButton"')
        blokk = forras[kezdet : kezdet + 900]
        assert "visible: !toolbar.toolbarCompact" in blokk
        assert "Layout.minimumWidth: 0" in blokk
