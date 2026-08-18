"""A vászon körüli NÉGY gombcsoport, KIRAJZOLVA — #948 (1/2).

Spec: `docs/specs/kollazs-panel-ui-spec.md` **2.4** és **4.4**.

A jegy egyetlen mondata: **a négy csoport a LAPHOZ tapad, nem a kerethez.**
A `collagepanel.tre` mind a négyet a `previewshadow` (= maga a lap)
gyerekeként hordozza, tehát oldalformátum- vagy ablakméret-váltáskor is a
lap szélén marad. Ezt property-olvasással nem lehet ellenőrizni: a lap
téglalapja a panel méretezési törvényéből (#945) számolódik, és csak a
KIRAJZOLT fában derül ki, hogy a gombsor tényleg oda került-e.

A három helyi menü a testvérfájlban van (`test_collage_menus_948.py`) — a
`scripts/run_tests.py` fájlonként külön processzt indít (#155), és egy
900 soros fájl egy processzben túl sok QML-engine-életciklust tartana.
"""

from __future__ import annotations

import pytest
from PySide6.QtGui import QGuiApplication

from picasapy.collage.themes import COLLAGE_THEMES, capability_map

from support.collage_canvas_harness import (
    _ablakban,
    _child,
    _lap,
    _panel,
    keszits_kepeket,
    nyitott_vezerlo,
)


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)


def _var():
    QGuiApplication.instance().processEvents()


#: A `.tre` csoportméretei (`picasa-create-features.md` 1.10.4).
AKCIOSOR = (445, 28)
RAND_SOR = (354, 28)
OSZLOP = (17, 65)


# --- 1. A négy csoport a LAPHOZ tapad ----------------------------------------


@pytest.mark.parametrize("meret", [(800, 534), (1280, 800), (1920, 1080)])
def test_az_akciosor_a_lap_folott_2_px_re_kozepen_all(controller, meret):
    """`action_group`: `m_centerX` + `YConstraint 1, 0, -2` (spec 2.4).

    Az ALSÓ éle van a lap TETEJE fölött 2 képponttal — nem a felső éle a
    lap tetejénél. A kettő 28 képponttal tér el; aki elnézi, a gombsort a
    lapra rajzolja."""
    panel = _panel(controller, *meret)
    lap_x, lap_y, lap_sz, _ = _ablakban(_lap(panel))
    sor_x, sor_y, sor_sz, sor_m = _ablakban(_child(panel, "collageActionRow"))

    assert (sor_sz, sor_m) == AKCIOSOR
    assert sor_y + sor_m == pytest.approx(lap_y - 2, abs=0.5)
    assert sor_x + sor_sz / 2 == pytest.approx(lap_x + lap_sz / 2, abs=0.5)


@pytest.mark.parametrize("meret", [(800, 534), (1280, 800), (1920, 1080)])
def test_a_rand_sor_a_lap_alatt_2_px_re_kozepen_all(controller, meret):
    """`rand_group`: `m_centerX` + `YConstraint 0, 1, 2` (spec 2.4)."""
    panel = _panel(controller, *meret)
    lap_x, lap_y, lap_sz, lap_m = _ablakban(_lap(panel))
    sor_x, sor_y, sor_sz, sor_m = _ablakban(_child(panel, "collageRandomRow"))

    assert (sor_sz, sor_m) == RAND_SOR
    assert sor_y == pytest.approx(lap_y + lap_m + 2, abs=0.5)
    assert sor_x + sor_sz / 2 == pytest.approx(lap_x + lap_sz / 2, abs=0.5)


@pytest.mark.parametrize("meret", [(800, 534), (1280, 800), (1920, 1080)])
def test_a_ket_oldalso_oszlop_a_lap_ket_szelen_ul(controller, meret):
    """`z_order_group` jobbra, `snap_rotation_group` balra — mindkettő a lap
    szélétől 2 px-re, FÜGGŐLEGESEN középen (spec 2.4)."""
    panel = _panel(controller, *meret)
    controller.selectAllNodes()
    _var()
    lap_x, lap_y, lap_sz, lap_m = _ablakban(_lap(panel))

    z_x, z_y, z_sz, z_m = _ablakban(_child(panel, "collageZOrderColumn"))
    assert (z_sz, z_m) == OSZLOP
    assert z_x == pytest.approx(lap_x + lap_sz + 2, abs=0.5)
    assert z_y + z_m / 2 == pytest.approx(lap_y + lap_m / 2, abs=0.5)

    s_x, s_y, s_sz, s_m = _ablakban(_child(panel, "collageSnapColumn"))
    assert (s_sz, s_m) == OSZLOP
    assert s_x + s_sz == pytest.approx(lap_x - 2, abs=0.5)
    assert s_y + s_m / 2 == pytest.approx(lap_y + lap_m / 2, abs=0.5)


def test_a_csoportok_a_lappal_egyutt_mozognak_formatumvaltaskor(controller):
    """A jegy lényege: ÁLLÓ tájolásnál a lap keskenyebb lesz, és a négy
    csoport VELE megy — nem a vászonkerethez tapad.

    Ha valaki a vászon abszolút koordinátáiból (383 / 727) rajzolná meg
    őket — ahogy a `picasa-kollazs-felulet.md` régi olvasata sugallta —,
    ez a teszt fogná meg: fekvőben még stimmelne, állóban már nem."""
    panel = _panel(controller)
    controller.selectAllNodes()
    _var()
    fekvo_lap = _ablakban(_lap(panel))
    fekvo_snap = _ablakban(_child(panel, "collageSnapColumn"))

    controller.setCollageOrientation("portrait")
    _var()
    allo_lap = _ablakban(_lap(panel))
    allo_snap = _ablakban(_child(panel, "collageSnapColumn"))

    # a lap tényleg megváltozott — különben a teszt semmit nem mérne
    assert allo_lap[2] < fekvo_lap[2]
    assert allo_snap != fekvo_snap

    for lap, oszlop in ((fekvo_lap, fekvo_snap), (allo_lap, allo_snap)):
        assert oszlop[0] + oszlop[2] == pytest.approx(lap[0] - 2, abs=0.5)
        assert oszlop[1] + oszlop[3] / 2 == pytest.approx(lap[1] + lap[3] / 2, abs=0.5)

    for nev, jel in (("collageActionRow", -1), ("collageRandomRow", 1)):
        allo = _ablakban(_child(panel, nev))
        assert allo[0] + allo[2] / 2 == pytest.approx(
            allo_lap[0] + allo_lap[2] / 2, abs=0.5
        )
        if jel < 0:
            assert allo[1] + allo[3] == pytest.approx(allo_lap[1] - 2, abs=0.5)
        else:
            assert allo[1] == pytest.approx(allo_lap[1] + allo_lap[3] + 2, abs=0.5)


# --- 2. A két oldalsó oszlop alapból REJTETT ---------------------------------


def test_a_ket_oszlop_kijeloles_nelkul_nem_latszik(controller):
    """`m_hidden` mindkét oldalsó csoporton (spec 2.4): kijelöléskor jönnek
    elő, és a kijelölés megszüntetésekor újra eltűnnek."""
    panel = _panel(controller)
    _var()
    assert not _child(panel, "collageZOrderColumn").isVisible()
    assert not _child(panel, "collageSnapColumn").isVisible()

    controller.setCollageSelection([1])
    _var()
    assert _child(panel, "collageZOrderColumn").isVisible()
    assert _child(panel, "collageSnapColumn").isVisible()

    controller.selectNoNodes()
    _var()
    assert not _child(panel, "collageZOrderColumn").isVisible()
    assert not _child(panel, "collageSnapColumn").isVisible()


def test_a_ket_vizszintes_sor_kijeloles_nelkul_is_latszik(controller):
    """A felső és az alsó soron NINCS `m_hidden` — mindig ott vannak, csak a
    gombjaik halványodnak el (spec 4.4)."""
    panel = _panel(controller)
    _var()
    assert _child(panel, "collageActionRow").isVisible()
    assert _child(panel, "collageRandomRow").isVisible()


# --- 3. A gombok elrendezése a csoporton belül -------------------------------


def test_az_akciosor_negy_gombja_a_tre_meretevel_es_3_px_resel_all(controller):
    """`select_all` 100 · `select_none` 100 · `remove_node` 100 ·
    `set_background` 134, 3 px réssel, 1 px belső margóval (1.10.4)."""
    panel = _panel(controller)
    vart = (
        ("collageSelectAllButton", 100),
        ("collageSelectNoneButton", 100),
        ("collageRemoveButton", 100),
        ("collageSetBackgroundButton", 134),
    )
    sor_x, sor_y, _, _ = _ablakban(_child(panel, "collageActionRow"))
    kovetkezo = sor_x + 1
    for nev, szelesseg in vart:
        x, y, sz, m = _ablakban(_child(panel, nev))
        assert (sz, m) == (szelesseg, 26), nev
        assert x == pytest.approx(kovetkezo, abs=0.5), nev
        assert y == pytest.approx(sor_y + 1, abs=0.5), nev
        kovetkezo = x + sz + 3


def test_a_rand_sor_harom_gombja_a_tre_meretevel_all(controller):
    """`rand_placement` 115 · `rand_order` 116 · `view_and_edit` 115 — EBBEN
    a sorrendben (1.10.4)."""
    panel = _panel(controller)
    vart = (
        ("collageScrambleButton", 115),
        ("collageShuffleButton", 116),
        ("collageViewAndEditButton", 115),
    )
    sor_x, sor_y, _, _ = _ablakban(_child(panel, "collageRandomRow"))
    kovetkezo = sor_x + 1
    for nev, szelesseg in vart:
        x, y, sz, m = _ablakban(_child(panel, nev))
        assert (sz, m) == (szelesseg, 26), nev
        assert x == pytest.approx(kovetkezo, abs=0.5), nev
        assert y == pytest.approx(sor_y + 1, abs=0.5), nev
        kovetkezo = x + sz + 3


@pytest.mark.parametrize(
    "oszlop,gombok",
    [
        (
            "collageSnapColumn",
            ("collageSnap12", "collageSnap3", "collageSnap6", "collageSnap9"),
        ),
        (
            "collageZOrderColumn",
            (
                "collageMoveTop",
                "collageMoveUp",
                "collageMoveDown",
                "collageMoveBottom",
            ),
        ),
    ],
)
def test_az_oszlopok_negy_gombja_15x15_es_16_px_osztassal_all(
    controller, oszlop, gombok
):
    """A `.tre`: 15 × 15-ös gombok, 16 képpontos osztással, 1 px belső
    margóval (`snap_3` 247, `snap_6` 263, `snap_9` 279)."""
    panel = _panel(controller)
    controller.selectAllNodes()
    _var()
    _, cs_y, _, _ = _ablakban(_child(panel, oszlop))
    for sorszam, nev in enumerate(gombok):
        _, y, sz, m = _ablakban(_child(panel, nev))
        assert (sz, m) == (15, 15), nev
        assert y == pytest.approx(cs_y + 1 + 16 * sorszam, abs=0.5), nev


def test_csak_a_move_up_es_move_down_ismetel_nyomva_tartva(controller):
    """`m_autorepeat` a `move_up`/`move_down`-on van, a `move_top`/
    `move_bottom`-on NINCS (spec 2.5). A rétegsorrend két szélső parancsa
    idempotens: ismételve semmit nem tenne, csak villogna."""
    panel = _panel(controller)
    controller.selectAllNodes()
    _var()
    assert _child(panel, "collageMoveUp").property("autoRepeat") is True
    assert _child(panel, "collageMoveDown").property("autoRepeat") is True
    assert _child(panel, "collageMoveTop").property("autoRepeat") is False
    assert _child(panel, "collageMoveBottom").property("autoRepeat") is False


def test_a_nyolc_oszlop_ikon_tenylegesen_kirajzolodik(controller):
    """A fájl LÉTEZÉSE nem bizonyítja, hogy a felhasználó lát is valamit: a
    Qt SVG-motorja (SVG Tiny 1.2) némán kihagyja, amit nem ismer, és a gomb
    üresen marad. Ezért a KIRAJZOLT szélességet mérjük, nem a fájlt.

    Ahol a Qt SVG-bővítménye hiányzik (Debian/Ubuntu `qt6-svg-plugins`),
    egyetlen ikon sem rajzolódik ki — ott a mérésnek nincs értelme."""
    from PySide6.QtGui import QImageReader

    if b"svg" not in QImageReader.supportedImageFormats():
        pytest.skip("a Qt SVG-képformátum-bővítménye hiányzik ezen a gépen")

    panel = _panel(controller)
    controller.selectAllNodes()
    _var()
    for nev in (
        "collageSnap12",
        "collageSnap3",
        "collageSnap6",
        "collageSnap9",
        "collageMoveTop",
        "collageMoveUp",
        "collageMoveDown",
        "collageMoveBottom",
    ):
        kep = _child(panel, nev + "Icon")
        # A `QQuickImageBase::Status`-hoz nincs Python-oldali konverter
        # (Qt-korlát, #664), ezért a ténylegesen kirajzolt méretet nézzük:
        # egy törött vagy hiányzó kép 0-t hagyna.
        assert kep.property("paintedWidth") > 0, f"{nev}: az ikon üres maradt"
        assert kep.property("paintedHeight") > 0, f"{nev}: az ikon üres maradt"


# --- 4. A gombok engedélyezése -----------------------------------------------


def test_kijeloles_nelkul_negy_gomb_halvany(controller):
    """A felhasználó 2. képernyőképe: kijelölés nélkül az „Az összes
    kijelölés megszüntetése", az „Eltávolítás", a „Beállítás háttérként" és
    a „Megjelenítés és szerkesztés" HALVÁNY (spec 4.4)."""
    panel = _panel(controller)
    _var()
    for nev in (
        "collageSelectNoneButton",
        "collageRemoveButton",
        "collageSetBackgroundButton",
        "collageViewAndEditButton",
    ):
        assert not _child(panel, nev).isEnabled(), nev
    # …az „Az összes kijelölése" viszont aktív, mert van kép
    assert _child(panel, "collageSelectAllButton").isEnabled()


def test_egy_kijelolt_keppel_mind_a_negy_aktiv(controller):
    """A 3. képernyőkép: EGY kijelölt képpel mind aktív."""
    panel = _panel(controller)
    controller.setCollageSelection([0])
    _var()
    for nev in (
        "collageSelectNoneButton",
        "collageRemoveButton",
        "collageSetBackgroundButton",
        "collageViewAndEditButton",
    ):
        assert _child(panel, nev).isEnabled(), nev


def test_ket_kijelolt_keppel_az_egykepes_parancsok_halvanyak(controller):
    """„Beállítás háttérként" és „Megjelenítés és szerkesztés": PONTOSAN egy
    kijelölt kép (spec 4.4). Kettőnél halványak, az eltávolítás nem."""
    panel = _panel(controller)
    controller.setCollageSelection([0, 1])
    _var()
    assert _child(panel, "collageRemoveButton").isEnabled()
    assert not _child(panel, "collageSetBackgroundButton").isEnabled()
    assert not _child(panel, "collageViewAndEditButton").isEnabled()


def test_az_osszekeveres_ket_kep_alatt_halvany(controller):
    """„Képek összekeverése": maszk 2. bitje ÉS legalább KETTŐ kép. Egyetlen
    képet nincs mivel összekeverni."""
    panel = _panel(controller)
    _var()
    assert _child(panel, "collageShuffleButton").isEnabled()
    controller.deleteClips([0, 1])
    _var()
    assert controller.collageClipCount == 1
    assert not _child(panel, "collageShuffleButton").isEnabled()


@pytest.mark.parametrize("tema", COLLAGE_THEMES)
def test_a_gomb_engedelyezes_mind_a_hat_temara_a_maszkbol_jon(controller, tema):
    """A képesség-maszk az EGYETLEN forrás (spec 5.): a három maszkfüggő
    gomb engedélyezése témánként a `capabilities_for`-t követi, nem
    témánkénti `if`-et.

    A `multiexp` a próbája: ott nincs kijelölés, tehát még „Az összes
    kijelölése" is halvány."""
    panel = _panel(controller)
    controller.setCollageTheme(tema)
    controller.selectNoNodes()
    _var()
    kepesseg = capability_map(tema)

    assert _child(panel, "collageSelectAllButton").isEnabled() is kepesseg["selection"]
    assert _child(panel, "collageShuffleButton").isEnabled() is kepesseg["shuffle"]
    assert _child(panel, "collageScrambleButton").isEnabled() is kepesseg["scramble"]


def test_a_kep_nelkuli_kollazsban_az_osszes_kijelolese_is_halvany(controller):
    """„Az összes kijelölése": maszk 4. bitje ÉS legalább EGY kép."""
    panel = _panel(controller)
    controller.deleteClips([0, 1, 2])
    _var()
    assert controller.collageClipCount == 0
    assert not _child(panel, "collageSelectAllButton").isEnabled()
    assert not _child(panel, "collageScrambleButton").isEnabled()


# --- 5. A gombok a VEZÉRLŐT hívják -------------------------------------------


def test_a_gombok_a_vezerlo_slotjait_hivjak(controller):
    """Nyolc gomb, nyolc slot — párhuzamos logika nélkül.

    A kattintás helyett a `clicked` jelet váltjuk ki: a fejnélküli
    kirajzolásban a gomb középpontja megbízhatóan eltalálható lenne, de a
    két oldalsó oszlop 15 × 15-ös gombjainál a lap szélétől mért helyzet
    platformfüggő kerekítést hozna be."""
    from PySide6.QtCore import QMetaObject, Qt

    panel = _panel(controller)
    controller.setCollageSelection([0])
    _var()

    def kattint(nev):
        QMetaObject.invokeMethod(
            _child(panel, nev), "clicked", Qt.ConnectionType.DirectConnection
        )
        _var()

    kattint("collageSelectAllButton")
    assert list(controller.collageSelection) == [0, 1, 2]

    kattint("collageSelectNoneButton")
    assert list(controller.collageSelection) == []

    controller.setCollageSelection([2])
    _var()
    kattint("collageSetBackgroundButton")
    assert controller.collageBackgroundMode == "image"

    elotte = [n.theta for n in controller.collageNodes.nodes]
    kattint("collageSnap3")
    utana = [n.theta for n in controller.collageNodes.nodes]
    assert utana[2] != elotte[2]

    kattint("collageMoveTop")
    assert controller.collageNodes.nodes[-1].selected

    kattint("collageRemoveButton")
    assert controller.collageClipCount == 2
