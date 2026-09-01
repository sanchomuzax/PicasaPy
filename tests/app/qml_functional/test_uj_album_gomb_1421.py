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
    """⚠️ A gomb a #1903-ban VISSZAVONVA — a mérés MEGDŐLT.

    Ez az osztály eredetileg azt állította, hogy az „Időrend" váltógomb
    ott van az eszköztáron (a #1421 mért helyével és méretével). A
    tulajdonos élesben jelentette, két képernyőképpel, hogy amit a gomb
    megnyit, az **nem az eredeti funkció**: a Picasa Időrendje TELJES
    KÉPERNYŐS, ANIMÁLT BEMUTATÓ a diavetítő motorján
    (`oneup/timeline` + `BigSlideshow2`, `0x008037e0`), saját RÁTÉTES
    vezérlősávval (`overlays/timeline` · `timelinedot` · `sliderthumb` ·
    `startbutton` · `exit`, `0x007fb210`) és „Időrend előkészítése…"
    fázissal — a miénk lapos rács volt hónap-fejlécekkel.

    ⇒ A fejlécben ilyen gomb az eredetiben ezen a helyen NEM létezik: az
    Időrend vezérlői a teljes képernyős rátéten ülnek. A #1421 mérése a
    HELYET és a MÉRETET jól adta meg, de rossz funkcióhoz — a felirat
    egyezése („Timeline" → „Időrend") nem jelenti, hogy ugyanazt a
    funkciót építettük meg.

    A tesztek ezért **megfordultak**: azt őrzik, hogy a gomb NINCS ott,
    amíg a valódi nézet nincs megépítve (#1903). A többi kihelyezett gomb
    (Új album, lapos/fa nézetváltó) érintetlen — azok mérése áll.
    """

    def test_NINCS_idorend_gomb_a_savon(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, "toolbarTimelineButton") is None

    def test_a_forrasban_sincs_benne(self):
        forras = _TOOLBAR.read_text(encoding="utf-8")
        assert 'objectName: "toolbarTimelineButton"' not in forras

    def test_a_MENUTETEL_helye_megmarad(self):
        """A hely az eredetiben létezik — csak a tartalma nincs kész."""
        menu = (_TOOLBAR.parent / "PicasaMenuBar.qml").read_text(
            encoding="utf-8"
        )
        assert 'objectName: "menuViewTimeline"' in menu


