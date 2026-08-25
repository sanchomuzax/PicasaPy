"""A Kollázs-panel „Klipek" lapja, KIRAJZOLVA — #949.

Spec: `docs/specs/kollazs-panel-ui-spec.md` **4.3** és **12.**

Miért kirajzolt teszt: a lap tartalma egy `GridView`, aminek a delegáltjait
a `findChild` **nem** találja meg — a `_walk()` a vizuális fán jár. A
gombok VALÓDI egérkattintást kapnak, nem függvényhívást, és a vezérlő az
IGAZI `CollageMixin` (a #947 harness-e): így a „a fülfelirat a tényleges
darabszámot követi" állítás a teljes láncon mérődik — modell → property →
fülsáv-felirat —, nem egy utánzat egy pontján.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from support.collage_canvas_harness import (
    _ablakban,
    _child,
    _panel,
    _van,
    _walk,
    keszits_kepeket,
    nyitott_vezerlo,
)

#: A spec 4.3 táblája: `objectName` → (x, y, szélesség, magasság) a
#: `collageClipsTab` bal-felső sarkához mérve. Ez a SZERZŐDÉS.
GEOMETRIA = {
    "collageGetMoreClips": (6, 5, 166, 28),
    "collageAddClips": (201, 5, 28, 28),
    "collageDeleteClips": (234, 5, 28, 28),
}

#: A klip-lista bal-felső sarka; a szélessége a laptól függ, ezért nem
#: szerepel a fenti táblában.
LISTA_X, LISTA_Y = 4, 36

#: A lista alsó behúzása (spec 4.3: „alul −10").
LISTA_ALSO_HEZAG = 10

_QML_FORRAS = (
    Path(picasapy.app.__file__).parent
    / "qml"
    / "PicasaPy"
    / "CollageClipsTab.qml"
).read_text(encoding="utf-8")

_TS_FORRAS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)


@pytest.fixture
def panel(controller):
    root = _panel(controller)
    _klipek_lapra(root)
    return root


def _var(feltetel, ms: int = 3000) -> bool:
    """Esemény-pörgetés HATÁRIDŐVEL, amíg a feltétel teljesül — #1463.

    A fali órás `QTest.qWait(N)` arra fogad, hogy N ezredmásodperc alatt
    megtörténik valami; egy terhelt, négymagos gépen ez hamis pirosat ad. Ez
    a poll a VALÓDI feltételt figyeli, és amint teljesül, azonnal
    továbbenged — így gyorsabb IS, meg megbízhatóbb IS.

    (A `test_collage_output_ui_949._var` mintája. Az `AssertionError` azért
    van elkapva, mert a `_child()` nem-létező elemre azzal jelez, és a
    keresett csempe a poll elején még hiányozhat.)"""
    eltelt = 0
    while eltelt < ms:
        try:
            if feltetel():
                return True
        except (AssertionError, AttributeError, TypeError, RuntimeError):
            pass
        QTest.qWait(25)
        eltelt += 25
    try:
        return bool(feltetel())
    except (AssertionError, AttributeError, TypeError, RuntimeError):
        return False


def _klipek_lapra(panel):
    """A „Klipek" fülre kattint — VALÓDI egérrel, ahogy a felhasználó."""
    gomb = _child(panel, "collageClipsTabButton")
    kozep = gomb.mapToScene(gomb.boundingRect().center())
    QTest.mouseClick(
        panel.property("_view"),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    # #1463: itt korábban fix `QTest.qWait(50)` állt. A fülváltás VALÓDI
    # következménye az, hogy a Klipek lap láthatóvá válik — erre várunk.
    assert _var(lambda: _child(panel, "collageClipsTab").isVisible() is True), (
        "a Klipek fülre kattintva a lap nem lett látható"
    )


def _kattints(panel, item, amig=None):
    """Valódi egérkattintás az elemre; `amig` a kattintás KÖVETKEZMÉNYE.

    #1463: korábban a kattintás után fix `QTest.qWait(50)` állt, a hívók
    pedig azonnal állítottak — vagyis a teszt arra fogadott, hogy 50 ms
    elég. Az `amig` predikátummal a hívóhely megmondja, MIRE vár, és a
    várakozás azonnal továbbenged, amint az bekövetkezett."""
    kozep = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        panel.property("_view"),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    if amig is None:
        # Nincs megnevezett következmény: marad a fali óra. Új hívónál ez
        # ne maradjon így — a hívóhelyre illő feltételt kell megadni.
        QTest.qWait(50)
        return
    assert _var(amig), "a kattintás várt következménye nem következett be"


def _lap(panel):
    return _child(panel, "collageClipsTab")


def _relativ(panel, nev):
    """Az elem doboza a `collageClipsTab` sarkához képest."""
    lap_x, lap_y, _, _ = _ablakban(_lap(panel))
    x, y, w, h = _ablakban(_child(panel, nev))
    return (round(x - lap_x), round(y - lap_y), round(w), round(h))


def _fulfelirat(panel):
    for item in _walk(panel):
        if item.objectName() == "collageClipsTabButton":
            return item.property("text")
    raise AssertionError("a Klipek fül nem található")


class TestGeometria:
    """A `.tre`-ből származó számok — ez a lap szerződése."""

    @pytest.mark.parametrize("nev", sorted(GEOMETRIA))
    def test_a_harom_gomb_a_helyen_van(self, panel, nev):
        assert _relativ(panel, nev) == GEOMETRIA[nev]

    def test_a_klip_lista_bal_felso_sarka(self, panel):
        x, y, _, _ = _relativ(panel, "collageClipList")
        assert (x, y) == (LISTA_X, LISTA_Y)

    def test_a_klip_lista_vizszintesen_nyulik(self, panel):
        _, _, lap_w, lap_h = _ablakban(_lap(panel))
        _, _, w, h = _relativ(panel, "collageClipList")
        assert w == round(lap_w) - LISTA_X
        assert h == round(lap_h) - LISTA_Y - LISTA_ALSO_HEZAG

    def test_a_lap_csak_a_masodik_fulon_latszik(self, controller):
        root = _panel(controller)
        assert _child(root, "collageClipsTab").isVisible() is False
        _klipek_lapra(root)
        assert _child(root, "collageClipsTab").isVisible() is True
        assert _child(root, "collageSettingsTab").isVisible() is False


class TestFulfelirat:
    """„Klipek (%1)" — a TÉNYLEGES darabszámmal, minden művelet után."""

    def test_a_nyitaskori_darabszam(self, panel, controller):
        assert controller.collageClipCount == 3
        assert _fulfelirat(panel) == "Clips (3)"

    def test_torles_utan_ujrairodik(self, panel, controller):
        controller.setCollageSelection([0])
        _kattints(
            panel,
            _child(panel, "collageDeleteClips"),
            amig=lambda: controller.collageClipCount == 2,
        )
        assert controller.collageClipCount == 2
        assert _fulfelirat(panel) == "Clips (2)"

    def test_felvetel_utan_ujrairodik(self, panel, controller):
        controller.addClips([1])
        # #1463: fix `QTest.qWait(50)` helyett a felvétel VALÓDI eredményére
        # várunk — a klipszám négyre nőtt.
        assert _var(lambda: controller.collageClipCount == 4), (
            "az addClips() után a klipszám nem lett 4"
        )
        assert controller.collageClipCount == 4
        assert _fulfelirat(panel) == "Clips (4)"

    def test_a_felirat_NEM_a_statikus_Kepek(self, panel):
        """A `.tre` statikus címkéje „Képek", a futó programé „Klipek (N)".

        A kettő keveréke („Képek (%1)") olyan felirat, ami az eredetiben nem
        létezik — a #945 első köre pont ebbe esett bele."""
        felirat = _fulfelirat(panel)
        assert felirat.startswith("Clips (")
        assert "Pictures" not in felirat


class TestKlipLista:
    def test_minden_kliphez_tartozik_csempe(self, panel, controller):
        assert all(
            _van(panel, f"collageClip{i}")
            for i in range(controller.collageClipCount)
        )

    def test_a_csempe_a_KEP_utvonalat_mutatja(self, panel, controller):
        csempe = _child(panel, "collageClip0")
        assert controller.collageNodes.nodes[0].path in str(
            csempe.property("path")
        )

    def test_a_csempere_kattintva_kijelolodik(self, panel, controller):
        _kattints(
            panel,
            _child(panel, "collageClip1"),
            amig=lambda: list(controller.collageSelection) == [1],
        )
        assert list(controller.collageSelection) == [1]

    def test_a_kijelolt_csempe_jelolve_van(self, panel, controller):
        controller.setCollageSelection([2])
        # #1463: fix `QTest.qWait(50)` helyett arra várunk, ami az állítás
        # tárgya — a harmadik csempe felvette a kijelölt állapotot.
        assert _var(
            lambda: _child(panel, "collageClip2").property("selected") is True
        ), "a kijelölés nem jelent meg a csempén"
        assert _child(panel, "collageClip2").property("selected") is True
        assert _child(panel, "collageClip0").property("selected") is False

    def test_torles_utan_eltunik_a_csempe(self, panel, controller):
        controller.setCollageSelection([0])
        _kattints(
            panel,
            _child(panel, "collageDeleteClips"),
            amig=lambda: not _van(panel, "collageClip2"),
        )
        assert _van(panel, "collageClip1")
        assert not _van(panel, "collageClip2")


class TestGombok:
    def test_a_torles_a_KIJELOLT_klipeket_veszi_ki(self, panel, controller):
        elso = controller.collageNodes.nodes[0].path
        controller.setCollageSelection([0])
        _kattints(
            panel,
            _child(panel, "collageDeleteClips"),
            amig=lambda: controller.collageClipCount == 2,
        )
        assert [n.path for n in controller.collageNodes.nodes] != [elso]
        assert controller.collageClipCount == 2

    def test_kijeloles_nelkul_a_torles_TILTOTT(self, panel, controller):
        # #1463: ez a fali óra SZÁNDÉKOSAN marad. Az állítás TÁVOLLÉTRE
        # fogad („a gomb NEM aktív"), amihez nincs olyan feltétel, aminek a
        # bekövetkeztét ki lehetne várni: a kikapcsolt állapot már a
        # `setCollageSelection([])` pillanatában fennállhat. A kockázat itt
        # fordított: terhelt gépen nem hamis PIROS, hanem hamis ZÖLD — ha a
        # kötés lassan futna le, a teszt a még-nem-frissült állapotot látná.
        # Az 50 ms ezért a kötés lefutásának ideje, nem várakozási határidő.
        controller.setCollageSelection([])
        QTest.qWait(50)
        assert _child(panel, "collageDeleteClips").property("enabled") is False

    def test_a_felvetel_a_konyvtar_kijeloleset_hasznalja(self, panel, controller):
        panel.setProperty("librarySelection", [0, 1])
        # #1463: fix `QTest.qWait(50)` helyett a gomb ENGEDÉLYEZETTSÉGÉRE
        # várunk. Ez nem kényelmi kérdés: a következő sor VALÓDI egérrel
        # kattint, és egy letiltott gomb a kattintást elnyeli — a teszt így
        # nem a felvételt, hanem a saját sietségét mérné.
        assert _var(
            lambda: _child(panel, "collageAddClips").property("enabled") is True
        ), "a könyvtár-kijelölés nem tette aktívvá a felvétel gombot"
        _kattints(
            panel,
            _child(panel, "collageAddClips"),
            amig=lambda: controller.collageClipCount == 5,
        )
        assert controller.collageClipCount == 5

    def test_ures_konyvtar_kijelolesnel_a_felvetel_TILTOTT(self, panel):
        # #1463: ez a fali óra SZÁNDÉKOSAN marad — ugyanaz az eset, mint a
        # törlés-gombnál fentebb. Az állítás TÁVOLLÉTRE fogad („a felvétel
        # gomb NEM aktív"), amire nincs kivárható feltétel. Terhelt gépen a
        # kockázat hamis ZÖLD (a kötés még nem futott le), nem hamis piros.
        panel.setProperty("librarySelection", [])
        QTest.qWait(50)
        assert _child(panel, "collageAddClips").property("enabled") is False

    def test_a_tovabbiak_jelzest_ad_es_NEM_zarja_a_lapot(self, panel, controller):
        """A „Továbbiak..." a Könyvtár fülre vált — a kollázs lapja NYITVA
        marad (spec 4.3). A fülváltás a gazdáé (Main.qml, az integrátor
        dolga), ezért a panel jelzést ad; a lapot nem zárja be."""
        kaptunk = []
        panel.getMoreClipsRequested.connect(lambda: kaptunk.append(1))
        _kattints(
            panel,
            _child(panel, "collageGetMoreClips"),
            amig=lambda: kaptunk == [1],
        )
        assert kaptunk == [1]
        assert controller.collageOpen is True


class TestFeliratok:
    """A hivatalos magyar a `.ts`-ben él; a forrásszöveg itt az angol.

    A buboréksúgó `ToolTip` CSATOLT tulajdonság — Pythonból nem olvasható
    ki a kirajzolt elemről, ezért a forrást és a fordítást állítjuk (a
    `test_editor_look.py` mintája). A `.ts`-beli oldal a fontosabb: az
    dönti el, mit LÁT a felhasználó."""

    def test_a_gombok_forrasszovege(self, panel):
        assert _child(panel, "collageGetMoreClips").property("text") == "Get more..."
        assert _child(panel, "collageAddClips").property("text") == "+"
        assert _child(panel, "collageDeleteClips").property("text") == "–"

    @pytest.mark.parametrize(
        "sugo",
        [
            "Add selected clips to the collage",
            "Remove the selected pictures from the tray",
            "Load more pictures from the library",
        ],
    )
    def test_mindharom_buboreksugo_forrasa_megvan(self, sugo):
        assert f'qsTr("{sugo}")' in _QML_FORRAS

    @pytest.mark.parametrize(
        "angol,magyar",
        [
            ("Get more...", "Továbbiak..."),
            (
                "Add selected clips to the collage",
                "Kijelölt klipek felvétele a kollázsba",
            ),
            (
                "Remove the selected pictures from the tray",
                "A kijelölt képek eltávolítása a tálcáról",
            ),
            (
                "Load more pictures from the library",
                "További képek beolvasása a könyvtárból",
            ),
        ],
    )
    def test_a_hivatalos_magyar_a_ts_ben_all(self, angol, magyar):
        """A `picasa-create-features.md` 1.10.6 szövegei SZÓ SZERINT."""
        assert f"<source>{angol}</source>" in _TS_FORRAS
        assert f"<translation>{magyar}</translation>" in _TS_FORRAS
