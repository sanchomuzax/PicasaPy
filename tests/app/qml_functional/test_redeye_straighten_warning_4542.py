"""#4542 / #7378: mentett kiegyenesítésnél a Vörösszem csempe Info ablakot ad.

Az eredeti Picasa a csempére kattintva, a panel megnyitása ELŐTT, felugró
„Info” ablakot mutat (`IDS_WARN_REDEYE_ACCURACY`), és a panelt csak az „OK”
után nyitja meg; a panelben nincs figyelmeztető sor (`job-837`, `__22` az
ablak, `__24` a panel, `__10` a kiegyenesítés nélküli eset).

A `job-837 __22` képkockáról mért adatok (a kliens-terület a WM-címsáv nélkül):

- szélesség 320 px, a szöveg 7 sorban törik, a bal széltől 56 px-re, a
  címsávtól 10 px-re kezdődik;
- az „OK” gomb 48 x 24 px, vízszintesen az ablak közepén (+1,5 px);
- a kék „i” ikon a bal széltől 13 px-re áll, a szöveg előtt.

A kliens-terület MAGASSÁGÁT (132 px) nem tartjuk: a mért sorköz 12 px, a mi
Open Sans betűnk természetes sorköze 15 px, a különbség 7 sorra 21 px. A
sorközt nem szorítjuk, mert a Thai és a Vietnami fordítás bontaná.
"""

from __future__ import annotations

import pytest

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from tests.support.varakozas import var_feltetelre

#: a `job-837 __22` mért adatai (px)
REF_SZELESSEG = 320
REF_SORSZAM = 7
REF_OK_MERET = (48, 24)
REF_SZOVEG_BAL = 56
REF_SZOVEG_FENT = 10
REF_IKON_BAL = 13
#: a mért képpont-pontosság: egy-két képpont a tördelés és a keret miatt
TURES = 3


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _kattints(window, elem, qt_app) -> None:
    assert elem.width() > 0 and elem.height() > 0, "a Vörösszem csempe nem látható"
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _ablak_elokeszit(window, qt_app, engine, tmp_path):
    """Megnyitja a nézőt az `a.jpg`-n (mentett kiegyenesítéssel)."""
    ini = tmp_path / "kepek" / ".picasa.ini"
    ini.write_text(
        "[a.jpg]\nfilters=tilt=1,0.250000,0.000000;\n[b.jpg]\n",
        encoding="utf-8",
    )
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)
    edit = engine.rootContext().contextProperty("editController")
    assert _varj(qt_app, lambda: edit.property("tiltParam") == 0.25)
    return viewer, edit


def _hely(elem):
    """(x, y, szélesség, magasság) az ablak koordinátáiban."""
    pont = elem.mapToScene(QPointF(0, 0))
    return pont.x(), pont.y(), elem.width(), elem.height()


def _kek_pixelek(kep, x, y, szelesseg, magassag) -> int:
    """A kék „i” ikon jelenlétét méri: azon képpontok száma, ahol a kék
    csatorna jóval nagyobb a pirosnál."""
    db = 0
    for yy in range(int(y), int(y + magassag)):
        for xx in range(int(x), int(x + szelesseg)):
            szin = kep.pixelColor(xx, yy)
            if szin.blue() > szin.red() + 60:
                db += 1
    return db


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_redeye_csempe_info_ablakot_ad_kiegyenesitett_kepen(
    qml_app, qt_app, tmp_path, rogzitett_betu, magassag_elteres
):
    window, _controller, engine = qml_app
    alapmagassag = window.height()
    window.setHeight(alapmagassag + magassag_elteres)
    assert _varj(qt_app, lambda: window.height() == alapmagassag + magassag_elteres)
    _viewer, edit = _ablak_elokeszit(window, qt_app, engine, tmp_path)

    panel = window.findChild(QObject, "viewerEditorPanel")
    csempe = window.findChild(QObject, "editToolRedeyeIcon")
    dialog = window.findChild(QObject, "redeyeStraightenInfoDialog")
    szoveg = window.findChild(QObject, "redeyeStraightenInfoText")
    assert panel is not None and csempe is not None
    assert dialog is not None, "a kiegyenesítés utáni Info ablak hiányzik"
    assert szoveg is not None
    assert not dialog.property("visible")
    assert edit.property("redeyeFoundCount") == -1
    kep_alap = window.grabWindow()
    assert not kep_alap.isNull(), "a kiinduló nézet nem renderelődött"

    # az előkészítés késői revíziója (aszinkron betöltés) még ne számítson:
    # a figyelés csak akkor indul, ha tíz körön át nem jött revíziójel
    kesoi = []
    edit.revisionChanged.connect(lambda: kesoi.append(1))
    csend = 0
    for _ in range(300):
        elotte = len(kesoi)
        qt_app.processEvents()
        csend = csend + 1 if len(kesoi) == elotte else 0
        if csend >= 10:
            break
    # a belépés-kilépés zaja (az automatika futtatása) a vezérlőn látszana
    zaj = []
    edit.revisionChanged.connect(lambda: zaj.append(1))

    _kattints(window, csempe, qt_app)
    assert _varj(qt_app, lambda: dialog.property("visible")), (
        "kiegyenesített képen a vörösszem-csempe nem nyit Info ablakot"
    )
    for _ in range(10):
        qt_app.processEvents()

    # --- az ablak: a panel még NEM nyílt meg, az automatika NEM futott ---
    assert not panel.property("redeyeActive"), (
        "az Info ablak előtt már megnyílt a Vörösszem panel"
    )
    assert panel.property("activeTab") == 0, "az Alapjavítások fülnek kell maradnia"
    assert edit.property("redeyeFoundCount") == -1, (
        "a vörösszem-automatika az OK előtt lefutott"
    )
    assert zaj == [], "a csempekattintás a panel nyitása nélkül is érintette a vezérlőt"
    assert dialog.property("modal")
    assert dialog.property("title") == "Info"
    assert szoveg.property("text") == (
        "This image's orientation has been modified by the Straighten tool, "
        "which can cause inaccuracies when selecting red eye  rectangles.\n"
        "If your redeye fixes appear to be misaligned (or non-existent), try "
        "undoing the Straighten fix, then reapply red eye fixes, and "
        "Straighten again if necessary."
    )

    # --- az ablak mérete és belső elrendezése a `job-837 __22`-höz mérve ---
    ablak_x = dialog.property("x")
    ablak_y = dialog.property("y")
    ablak_sz = dialog.property("width")
    ablak_m = dialog.property("height")
    assert abs(ablak_sz - REF_SZELESSEG) <= TURES, (
        f"az Info ablak szélessége {ablak_sz}, a mért {REF_SZELESSEG}"
    )
    assert abs(ablak_x + ablak_sz / 2 - window.width() / 2) <= TURES, "nincs középen"
    assert abs(ablak_y + ablak_m / 2 - window.height() / 2) <= TURES, "nincs középen"
    assert szoveg.property("lineCount") == REF_SORSZAM, (
        "a szöveg sorainak száma eltér a mérttől"
    )
    fejlec = dialog.property("header")
    kliens_teteje = ablak_y + (fejlec.property("height") if fejlec else 0)
    sz_x, sz_y, _sz_w, _sz_h = _hely(szoveg)
    assert abs((sz_x - ablak_x) - REF_SZOVEG_BAL) <= TURES, "a szöveg bal széle eltér"
    assert abs((sz_y - kliens_teteje) - REF_SZOVEG_FENT) <= TURES, "a szöveg teteje eltér"

    ikon = window.findChild(QObject, "redeyeStraightenInfoIcon")
    assert ikon is not None
    i_x, i_y, i_w, i_h = _hely(ikon)
    assert abs((i_x - ablak_x) - REF_IKON_BAL) <= TURES, "az ikon bal széle eltér"
    assert i_x + i_w <= sz_x, "az ikonnak a szöveg előtt kell állnia"

    ok_gomb = window.findChild(QObject, "redeyeStraightenInfoOkButton")
    gombsor = window.findChild(QObject, "redeyeStraightenInfoButtonBox")
    assert ok_gomb is not None, "az Info ablak OK gombja hiányzik"
    assert gombsor is not None and gombsor.findChild(
        QObject, "redeyeStraightenInfoOkButton"
    ) is ok_gomb
    assert gombsor.findChild(QObject, "redeyeStraightenInfoCancelButton") is None, (
        "az Info ablakon csak az OK gomb jelenhet meg"
    )
    assert ok_gomb.property("text") == "OK"
    assert ok_gomb.property("activeFocus"), "az OK gombnak fókuszban kell lennie"
    o_x, _o_y, o_w, o_h = _hely(ok_gomb)
    assert (o_w, o_h) == REF_OK_MERET, "az OK gomb mérete eltér a mérttől"
    assert abs(o_x + o_w / 2 - (ablak_x + ablak_sz / 2)) <= TURES, (
        "az OK gomb nincs vízszintesen középen"
    )

    # --- a renderelt kép: az ablak és a kék „i” ikon tényleg látszik ---
    kep_dialog = window.grabWindow()
    assert not kep_dialog.isNull(), "az Info ablak nem renderelődött"
    ikon_kek = _kek_pixelek(kep_dialog, i_x, i_y, i_w, i_h)
    assert ikon_kek > 100, f"a kék „i” ikon nem látszik a képen ({ikon_kek} kék képpont)"
    assert _kek_pixelek(kep_alap, i_x, i_y, i_w, i_h) < ikon_kek // 4, (
        "az ikon helyén az ablak előtt is kék képpontok voltak"
    )

    # --- Return: az ablak bezárul, a panel megnyílik, az automatika lefut ---
    QTest.keyClick(window, Qt.Key.Key_Return)
    assert _varj(qt_app, lambda: not dialog.property("visible")), (
        "a Return nem zárta be az Info ablakot"
    )
    assert _varj(qt_app, lambda: panel.property("redeyeActive")), (
        "az OK után nem nyílt meg a Vörösszem panel"
    )
    assert _varj(qt_app, lambda: edit.property("redeyeFoundCount") >= 0), (
        "az OK után nem futott le a vörösszem-automatika"
    )
    assert window.findChild(QObject, "redeyeStraightenWarning") is None, (
        "a figyelmeztetés sora a panelben maradt"
    )
    cim = window.findChild(QObject, "redeyeTitleText")
    megjegyzes = window.findChild(QObject, "redeyeFrameHintLabel")
    automatikus = window.findChild(QObject, "redeyeAutoResultLabel")
    assert cim is not None and cim.property("text") == "Redeye Repair"
    assert megjegyzes is not None and megjegyzes.property("text") == (
        "Note: You can click on a box to delete a change."
    )
    assert automatikus is not None and not automatikus.property("visible"), (
        "a találat nélküli állapotban ne jelenjen meg automatikus-találat üzenet"
    )
    for _ in range(10):
        qt_app.processEvents()
    kep_panel = window.grabWindow()
    assert not kep_panel.isNull(), "a Vörösszem panel nem renderelődött"
    assert _kek_pixelek(kep_panel, i_x, i_y, i_w, i_h) < ikon_kek // 4, (
        "az Info ablak ikonja az OK után is a képen maradt"
    )


def test_redeye_info_ablak_esc_bezarja_panel_nelkul_es_ujra_megjelenik(
    qml_app, qt_app, tmp_path
):
    """Az Esc/X elvetésének eredeti viselkedése NINCS lemérve (nyitott kérdés);
    a mi választásunk: az ablak bezárul, a panel nem nyílik meg, és a csempe
    újabb kattintására az ablak újra megjelenik."""
    window, _controller, engine = qml_app
    _viewer, edit = _ablak_elokeszit(window, qt_app, engine, tmp_path)
    panel = window.findChild(QObject, "viewerEditorPanel")
    csempe = window.findChild(QObject, "editToolRedeyeIcon")
    dialog = window.findChild(QObject, "redeyeStraightenInfoDialog")

    _kattints(window, csempe, qt_app)
    assert _varj(qt_app, lambda: dialog.property("visible"))
    QTest.keyClick(window, Qt.Key.Key_Escape)
    assert _varj(qt_app, lambda: not dialog.property("visible")), "az Esc nem zárta be"
    assert not panel.property("redeyeActive"), "az Esc után megnyílt a panel"
    assert edit.property("redeyeFoundCount") == -1

    _kattints(window, csempe, qt_app)
    assert _varj(qt_app, lambda: dialog.property("visible")), (
        "az Esc után a csempe nem hozta vissza az Info ablakot"
    )
    ok_gomb = window.findChild(QObject, "redeyeStraightenInfoOkButton")
    _kattints(window, ok_gomb, qt_app)
    assert _varj(qt_app, lambda: panel.property("redeyeActive")), (
        "az OK gomb kattintása nem nyitotta meg a panelt"
    )
    assert not dialog.property("visible")


def test_redeye_csempe_kiegyenesites_nelkul_nem_ad_ablakot(qml_app, qt_app, tmp_path):
    window, _controller, engine = qml_app
    viewer, edit = _ablak_elokeszit(window, qt_app, engine, tmp_path)
    panel = window.findChild(QObject, "viewerEditorPanel")
    csempe = window.findChild(QObject, "editToolRedeyeIcon")
    dialog = window.findChild(QObject, "redeyeStraightenInfoDialog")

    viewer.setProperty("currentIndex", 1)
    assert _varj(qt_app, lambda: edit.property("tiltParam") == 0)
    assert not panel.property("straightenActive")
    _kattints(window, csempe, qt_app)
    assert _varj(qt_app, lambda: panel.property("redeyeActive")), (
        "kiegyenesítés nélkül nem nyílt meg a Vörösszem panel"
    )
    assert not dialog.property("visible"), "kiegyenesítés nélkül nem jelenhet meg Info ablak"
    assert window.findChild(QObject, "redeyeStraightenWarning") is None
