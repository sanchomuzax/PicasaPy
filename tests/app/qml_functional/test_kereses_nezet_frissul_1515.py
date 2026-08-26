"""#1515: a keresési nézet KÖVESSE a felirat módosítását — a vezérlőn át.

## A tulajdonos jelentése

> „A keresési nézetben állva törlöm a kép feliratát — azt, ami miatt a kép
> egyáltalán találat volt —, és a kép ottmarad, amíg újra rá nem keresek."

## A mérés (a javítás előtt)

A keresés — a csillagozott nézethez (#1443) hasonlóan — **lekérdezés**, nem
élő szűrő: a `search()` (`app/search_controller.py`) egyszer lefuttatja a
`search_photos()`-t, és a tagságot innentől semmi nem tartja karban. A
felirat-mentés (`setCaption`, `app/photo_ops_controller.py`) a
`_run_photo_write` úton megy, ami CSAK a rács sorát frissíti.

| út | mit tett a javítás előtt |
|---|---|
| **felirat** (`setCaption`) | a sor `caption`-je frissült, de a kép a találati listában maradt — ez a bejelentett hiba |
| **kulcsszó** (`addKeywordToRows`/`removeKeywordFromRows`) | az `_apply_keywords` a végén `_refresh_view()`-t hív — MÁR JÓ VOLT |
| **átnevezés** (`renamePhotosMany`) | az `_on_rename_batch_done` `_refresh_view()`-t hív — MÁR JÓ VOLT |

A bal hasáb „Search results for … (N)" fejléce (`searchResultCount`) — a
keresési nézet megfelelője a #1443 zöld eredménysávjának — ugyanúgy
elavult maradt.

A #1443 „a sáv hazudik" hibájának a keresésnél is van párja, csak
másféle: a `search()` nem kapcsolta ki a csillagozott/album szűrő zöld
sávját (`filterActive`), ezért a Csillagozottakból a keresőmezőbe gépelve
a sáv ottmaradt a szűrő elavult darabszámával (`TestZoldEredmenysav`).

A teljes mérés: `docs/benchmarks/2026-08-26-kereses-ujralekerdezes.md`.

## Miért nem elég „mindig újralekérdezni"

Mért adatok valósághű indexen (140 755 kép / 3 000 mappa, a felhasználó
gyűjteményének mérete a `docs/benchmarks/2026-08-26-dedup-gyorskulcs.md`
szerint), RPi5, medián:

| művelet | idő |
|---|---|
| `search_photos("nyaralas")` (27 179 találat) | **597 ms** |
| `search_photos("zzzkulcs")` (0 találat) | 6 ms |
| `starred_photos()` (#1443 újralekérdezése, 7 038 sor) | 162 ms |
| **egy képre szűkített** tagság-lekérdezés | **6–11 ms** |

Vagyis a keresés újrafuttatása a #1443-hoz képest is nagyságrenddel
drágább, és a költséget a TALÁLATSZÁM viszi (a rekordépítés), nem az SQL.
Ezért a javítás előbb egy **egy képre szűkített, ugyanazon a kódúton futó**
tagság-lekérdezéssel megkérdezi, változott-e a tagság, és csak akkor
kérdezi újra a teljes nézetet. Küszöb, szabad paraméter nincs benne.

## Amit NEM őrzünk itt, és miért

Az ELLENKEZŐ irány (a felirat megadásakor a kép BEKERÜL a nézetbe) a
felületről nem érhető el ugyanabban a nézetben állva: a keresési nézet
csak a találatokat tartalmazza, tehát nincs olyan sor, amelyre kattintva
egy nem-találatnak feliratot lehetne adni (a néző is csak a látszó
képeken lép). Az irányt ezért — a #1443 mintájára — a nézetbe visszatéréssel
mérjük (`test_visszaadott_felirattal_ujra_bekerul`); ez azt is kizárja,
hogy a javítás „kitiltott sorok" listájával oldja meg a feladatot.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from support.qt_wait import wait_for_photo_op

KULCS = "zzzkulcs"
CIMKE = "zzzcimke"


def _child(root, name: str) -> QObject:
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _nevek(controller) -> list[str]:
    return [photo.name for photo in controller.photos.photos]


def _keress(window, qt_app, szoveg: str) -> None:
    """Keresés a KERESŐMEZŐN át (`textEdited` → `MainToolbar.searchEdited`
    → `controller.search`), nem a Python-slot közvetlen hívásával."""
    field = _child(window, "searchField")
    field.setProperty("text", szoveg)
    QMetaObject.invokeMethod(
        field, "textEdited", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _torold_a_keresest(window, qt_app) -> None:
    """A keresőmező ✕ gombjának megfelelője (`searchCleared`)."""
    _keress(window, qt_app, "")


def _felirat(window, controller, qt_app, index: int, szoveg: str) -> None:
    """Felirat írása a NÉZŐ felirat-mezőjén át (`captionField.accepted`).

    Ez az EGYETLEN felületi belépési pont a felirathoz (grep: `setCaption`
    csak a `PhotoViewer.qml` `captionField`-jéből hívódik)."""
    window.setProperty("viewerOpen", True)
    viewer = _child(window, "photoViewer")
    QMetaObject.invokeMethod(
        viewer, "show", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", index),
    )
    qt_app.processEvents()
    field = _child(window, "captionField")
    field.setProperty("text", szoveg)
    try:
        wait_for_photo_op(
            controller,
            lambda: QMetaObject.invokeMethod(
                field, "accepted", Qt.ConnectionType.DirectConnection
            ),
            qt_app=qt_app,
        )
        for _ in range(3):
            qt_app.processEvents()
    finally:
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()


def _kiindulas(window, controller, qt_app) -> None:
    """`a.jpg` felirata a keresett kulcs, `b.jpg`-é nem — mappa-nézetben."""
    _felirat(window, controller, qt_app, 0, KULCS)
    _felirat(window, controller, qt_app, 1, "valami mas")
    assert _nevek(controller) == ["a.jpg", "b.jpg"]


class TestFeliratTorlese:
    def test_a_felirat_torlese_azonnal_kikeruli_a_kepet(
        self, qml_app, qt_app
    ) -> None:
        """⚠️ A jegy magja: a képnek AZONNAL el kell tűnnie a nézetből."""
        window, controller, _engine = qml_app
        _kiindulas(window, controller, qt_app)

        _keress(window, qt_app, KULCS)
        assert _nevek(controller) == ["a.jpg"], "a kiinduló keresés nem talál"

        _felirat(window, controller, qt_app, 0, "")

        assert _nevek(controller) == [], (
            "a keresési nézet nem követte a felirat törlését: a kép "
            "ottmaradt (a modellben a felirat már üres)"
        )

    def test_a_talalatszam_is_kovet(self, qml_app, qt_app) -> None:
        """A bal hasáb „Search results for … (N)" fejléce is frissüljön."""
        window, controller, _engine = qml_app
        _kiindulas(window, controller, qt_app)
        _keress(window, qt_app, KULCS)
        assert controller.searchResultCount == 1

        _felirat(window, controller, qt_app, 0, "")

        assert controller.searchResultCount == 0, (
            "a keresési találatszám elavult: "
            f"{controller.searchResultCount}"
        )

    def test_a_masik_kep_felirata_nem_bant_semmit(
        self, qml_app, qt_app
    ) -> None:
        """A találatban maradó kép feliratának ÁTÍRÁSA nem üríti a nézetet."""
        window, controller, _engine = qml_app
        _kiindulas(window, controller, qt_app)
        _keress(window, qt_app, KULCS)

        _felirat(window, controller, qt_app, 0, f"{KULCS} 2024")

        assert _nevek(controller) == ["a.jpg"]
        assert controller.searchResultCount == 1


class TestNemSzabadEltavolitani:
    def test_mappanev_talalatnal_a_kep_marad(self, qml_app, qt_app) -> None:
        """Ellenkező irányú őr: ha a kép a MAPPA NEVE miatt találat, a
        felirat törlése nem távolíthatja el (a tagságát nem a felirat
        dönti el). Egy „töröld a sort" alakú javítás itt bukna."""
        window, controller, _engine = qml_app
        _kiindulas(window, controller, qt_app)
        _keress(window, qt_app, "kepek")  # a fixture mappájának neve
        assert _nevek(controller) == ["a.jpg", "b.jpg"]

        _felirat(window, controller, qt_app, 0, "")

        assert _nevek(controller) == ["a.jpg", "b.jpg"], (
            "a mappanév-találat eltűnt a felirat törlésekor"
        )

    def test_mappa_nezetben_a_kep_marad(self, qml_app, qt_app) -> None:
        """Mappa-nézetben a felirat semmilyen tagságot nem dönt el."""
        window, controller, _engine = qml_app
        _kiindulas(window, controller, qt_app)

        _felirat(window, controller, qt_app, 0, "")

        assert _nevek(controller) == ["a.jpg", "b.jpg"]


class TestSearchFolderMod:
    def test_mappara_szukitett_keresesben_is_kikerul(
        self, qml_app, qt_app
    ) -> None:
        """#45: keresés közben mappára kattintva a mód `search-folder` —
        a tagságot ott is a keresés dönti el."""
        window, controller, _engine = qml_app
        _kiindulas(window, controller, qt_app)
        _keress(window, qt_app, KULCS)
        pane = _child(window, "folderPane")
        pane.folderChosen.emit(controller.currentFolder)
        qt_app.processEvents()
        assert _nevek(controller) == ["a.jpg"]

        _felirat(window, controller, qt_app, 0, "")

        assert _nevek(controller) == [], (
            "a mappára szűkített keresés nem követte a felirat törlését"
        )
        assert controller.searchResultCount == 0


class TestVisszaadottFelirat:
    def test_visszaadott_felirattal_ujra_bekerul(self, qml_app, qt_app) -> None:
        """A javítás lekérdezés legyen, ne „kitiltott sorok" listája."""
        window, controller, _engine = qml_app
        _kiindulas(window, controller, qt_app)
        _keress(window, qt_app, KULCS)
        _felirat(window, controller, qt_app, 0, "")
        assert _nevek(controller) == []

        _torold_a_keresest(window, qt_app)
        assert _nevek(controller) == ["a.jpg", "b.jpg"]
        _felirat(window, controller, qt_app, 0, KULCS)

        _keress(window, qt_app, KULCS)
        assert _nevek(controller) == ["a.jpg"], (
            "a visszaadott felirattal a kép nem került vissza a nézetbe"
        )


class TestZoldEredmenysav:
    """A #1443 „a sáv hazudik" hibája a keresésnél is előfordul — másképp.

    A keresési nézetnek nincs saját zöld eredménysávja (a darabszámát a bal
    hasáb „Search results …" fejléce viszi, ld. `TestFeliratTorlese`), a
    **csillagozott/album** nézeté viszont van. A `search()` viszont nem
    kapcsolta ki (`_filter_active`), ezért a Csillagozottakból keresőmezőbe
    gépelve a sáv OTTMARADT a szűrő elavult darabszámával."""

    def test_keresesnel_eltunik_a_szuro_sava(self, qml_app, qt_app) -> None:
        window, controller, _engine = qml_app
        controller.showStarred()
        qt_app.processEvents()
        assert controller.filterActive is True

        _keress(window, qt_app, "a")

        assert _nevek(controller) == ["a.jpg"], "a keresés nem futott le"
        assert controller.filterActive is False, (
            "a csillagozott szűrő zöld sávja a keresés alatt is látszik, "
            f"elavult szöveggel: {controller.filterStatusText!r}"
        )

    def test_ures_keresesnel_is_eltunik(self, qml_app, qt_app) -> None:
        """A keresés törlése a mappa-feedhez visz vissza — ott sincs sáv."""
        window, controller, _engine = qml_app
        controller.showStarred()
        qt_app.processEvents()

        _torold_a_keresest(window, qt_app)

        assert controller.filterActive is False


class TestANezoAlatt:
    def test_a_nezo_nyitva_marad_a_lista_kiurulese_utan(
        self, qml_app, qt_app
    ) -> None:
        """A felirat a NÉZŐBŐL írható, tehát a frissítés a néző alatt
        rövidíti meg a listát — egyetlen találatnál nullára.

        Ez a kör kockázatos pontja (a #1443-ban is az volt): az `autouse`
        QML-hiba-őr (ld. conftest) egy „Cannot read property … of null"
        üzenetre pirosra váltana."""
        window, controller, _engine = qml_app
        _kiindulas(window, controller, qt_app)
        _keress(window, qt_app, KULCS)

        window.setProperty("viewerOpen", True)
        viewer = _child(window, "photoViewer")
        QMetaObject.invokeMethod(
            viewer, "show", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
        )
        qt_app.processEvents()
        field = _child(window, "captionField")
        field.setProperty("text", "")
        try:
            wait_for_photo_op(
                controller,
                lambda: QMetaObject.invokeMethod(
                    field, "accepted", Qt.ConnectionType.DirectConnection
                ),
                qt_app=qt_app,
            )
            for _ in range(8):
                qt_app.processEvents()
            assert _nevek(controller) == []
        finally:
            window.setProperty("viewerOpen", False)
            qt_app.processEvents()


class TestCimkeMegorzo:
    """Megőrző: a CÍMKE-írás útja a mérés szerint MÁR JÓ VOLT.

    Az `app/keywords_controller.py:153` (`_apply_keywords` vége) feltétel
    nélkül `_refresh_view()`-t hív, ezért a keresési nézet a címke
    levételét eddig is követte. Kötegelt, ritka művelet — a #1515
    költség-megfontolása (feliratmentésenként 597 ms) itt nem áll, ezért
    SZÁNDÉKOSAN nem alakítjuk át tagság-ellenőrzésre. Ez a teszt csak azt
    őrzi, hogy jó is marad."""

    def _cimkez(self, window, qt_app, jel: str, keyword: str) -> None:
        panel = _child(window, "tagsPanel")
        QMetaObject.invokeMethod(
            window, "handleThumbClick", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0), Q_ARG("QVariant", 0),
        )
        qt_app.processEvents()
        getattr(panel, jel).emit(keyword)
        qt_app.processEvents()

    def test_a_cimke_levetele_kikeruli_a_kepet(self, qml_app, qt_app) -> None:
        window, controller, _engine = qml_app
        self._cimkez(window, qt_app, "addRequested", CIMKE)
        _keress(window, qt_app, CIMKE)
        assert _nevek(controller) == ["a.jpg"]

        self._cimkez(window, qt_app, "removeRequested", CIMKE)

        assert _nevek(controller) == [], (
            "a keresési nézet nem követte a címke levételét"
        )
        assert controller.searchResultCount == 0


class TestKoltseg:
    """A mérés (ld. modul-docstring) alapján hozott döntés őre."""

    def test_valtozatlan_tagsagnal_nincs_teljes_ujralekerdezes(
        self, qml_app, qt_app
    ) -> None:
        """A teljes keresés újrafuttatása valósághű indexen 597 ms —
        feliratmentésenként nem fizethető ki. Ha a tagság nem változott,
        a nézetnek NEM szabad újralekérdeznie."""
        window, controller, _engine = qml_app
        _kiindulas(window, controller, qt_app)
        _keress(window, qt_app, KULCS)

        hivasok: list[int] = []
        eredeti = controller._refresh_view

        def szamlalo() -> None:
            hivasok.append(1)
            eredeti()

        controller._refresh_view = szamlalo
        try:
            # a felirat átírása bent tartja a képet: tagság változatlan
            _felirat(window, controller, qt_app, 0, f"{KULCS} 2024")
            assert hivasok == [], (
                "a nézet változatlan tagság mellett is újralekérdezett "
                f"({len(hivasok)}×) — ez 140 ezer képnél 597 ms/mentés"
            )

            # a felirat törlése viszont kiejti: itt KELL az újralekérdezés
            _felirat(window, controller, qt_app, 0, "")
            assert hivasok == [1], (
                "a tagság megszűnt, mégsem futott újralekérdezés"
            )
        finally:
            del controller._refresh_view
