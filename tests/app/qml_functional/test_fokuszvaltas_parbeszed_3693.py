"""#3693: a „Szerkesztés jóváhagyása" kérdés két változatának renderelt
elrendezése, és hogy a kapun át alkalmazott módosítás hova kerül.

A kérdés-párbeszéd (`EndEditModalityDialog.qml`) EGY példány: a mód-belépés
(#3651, `0x005f8d80(this, 1, 0, 0)`) Mégse NÉLKÜL, a fókuszváltás
(`0x005f8d80(this, 1, 0, 1)`) Mégsével nyitja (`docs/specs/ui-audit-editor.md`
3/c 2. pont). A mód-belépés párbeszédének elrendezése nem változhat a
Mégse miatt; a fókuszváltásé háromgombos, jobbra zárt sor.

Külön fájl a `test_fokuszvaltas_johagyasa_3693.py` mellett: tesztenként
teljes alkalmazás épül, és egy fájlban együtt a memóriaplafont (#2646)
átlépnék.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import (
    Q_ARG,
    Q_RETURN_ARG,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QRectF,
    Qt,
    QTranslator,
    QUrl,
)
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

_VAMPIRSZEM_LANC = "ReanimatedEyeColor=1,6.000000,20.000000;"

_I18N_DIR = (
    Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "i18n"
)
#: a gombsor `spacing`-je (`EndEditModalityDialog.qml`)
_RES = 8
#: a `RowLayout` egész képpontra kerekíti a gombok szélességét
_TURES = 1.0


def _gyerek(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _kattints(window, qt_app, nev):
    """Valódi egérkattintás a vezérlő/kép közepére."""
    elem = _gyerek(window, nev)
    kozep = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _nezot_nyit(window, qt_app):
    window.setProperty("viewerOpen", True)
    viewer = _gyerek(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    return viewer


def _ab_belep(window, qt_app):
    """A nézőt „ab" módba viszi — a fókuszváltó gomb és a kép-kattintás
    csak 2-up módban él. ⚠️ SZÁNDÉKOSAN „ab", nem „aa": az „aa" mód a
    #3014/#3649 szerint a KIJELÖLT fél láncát írja az inibe, a másikat
    memóriában tartja, és a fókuszváltás a kettőt CSERÉLI — Alkalmazás
    UTÁN a fókuszváltás így a frissen alkalmazott vágást a memóriás
    (aznap nem írt) oldalra teszi át, ami a #3649 mérése szerint helyes,
    de itt csak zavarná az „azonnal az inibe kerül" ellenőrzést. „ab"
    módban két KÜLÖNBÖZŐ fotó áll a két félen, saját inisorral — a
    fókuszváltás kapuja ugyanaz, a lánc-csere mellékhatása nélkül."""
    nezo = _nezot_nyit(window, qt_app)
    _kattints(window, qt_app, "viewerLayoutAb")
    assert nezo.property("layoutMode") == "ab"
    return nezo


def _parbeszed(window):
    return _gyerek(window, "endEditModalityDialog")


def _nyitva(window) -> bool:
    return _parbeszed(window).property("opened") is True


def _kijelol(overlay, qt_app, teglalap):
    overlay.setProperty("cropRect", teglalap)
    overlay.setProperty("hasSelection", True)
    qt_app.processEvents()


def _vagast_nyit_modositva(window, qt_app):
    """A vágó-eszköz megnyitása, húzott (de nem alkalmazott) kijelöléssel."""
    panel = _gyerek(window, "viewerEditorPanel")
    panel.setProperty("cropActive", True)
    qt_app.processEvents()
    overlay = _gyerek(window, "cropOverlay")
    _kijelol(overlay, qt_app, QRectF(0.25, 0.25, 0.5, 0.5))
    return panel, overlay


def _eszkozt_nyit_kattintva(window, qt_app, gomb, allapot):
    """Az eszköz megnyitása a csempéjére kattintva (Alapvető javítások fül)."""
    panel = _gyerek(window, "viewerEditorPanel")
    panel.setProperty("activeTab", 0)
    qt_app.processEvents()
    _kattints(window, qt_app, gomb)
    assert panel.property(allapot) is True, f"a {gomb} kattintása nem nyitotta meg"
    return panel


# -- a párbeszéd elrendezése (renderelt geometria) ---------------------------


@pytest.fixture
def magyar(qml_app, qt_app):
    """A hivatalos magyar feliratokkal mér: a gombok szélessége a
    felirattól függ, és a mód-belépés hibája (a rejtett Mégse is beleszámít
    a sor szélességébe) csak ott látszik, ahol a háromgombos sor szélesebb
    a jelölőnégyzet soránál — a magyar feliratokkal ez így van."""
    _window, _controller, engine = qml_app
    fordito = QTranslator(qt_app)
    assert fordito.load("picasapy_hu", str(_I18N_DIR))
    qt_app.installTranslator(fordito)
    engine.retranslate()
    qt_app.processEvents()
    try:
        yield qml_app
    finally:
        qt_app.removeTranslator(fordito)
        engine.retranslate()
        qt_app.processEvents()


def _jelenet_teglalap(window, nev) -> QRectF:
    elem = window.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    bal_felso = elem.mapToScene(QPointF(0, 0))
    return QRectF(bal_felso.x(), bal_felso.y(), elem.width(), elem.height())


def _parbeszed_teglalap(window) -> QRectF:
    d = _parbeszed(window)
    return QRectF(
        d.property("x"), d.property("y"), d.property("width"), d.property("height")
    )


def _elrendezes(window, qt_app):
    for _ in range(5):
        qt_app.processEvents()
    return {
        nev: _jelenet_teglalap(window, f"endEditModality{nev}")
        for nev in (
            "Tartalom",
            "Gombsor",
            "ApplyButton",
            "DiscardButton",
            "CancelButton",
            "NeKerdezzenCheck",
        )
    }


def _ketgombos_sor_szelessege(g) -> float:
    return g["ApplyButton"].width() + _RES + g["DiscardButton"].width()


def _assert_ketgombos_modbelepes(window, qt_app):
    """A mód-belépés (#3651) párbeszéde: Alkalmaz + Elvetés, jobbra zárva,
    és a párbeszéd szélességét a rejtett Mégse NEM növeli — a main
    kétgombos `RowLayout`-jával azonos elrendezés."""
    g = _elrendezes(window, qt_app)
    megse = _gyerek(window, "endEditModalityCancelButton")
    assert megse.property("visible") is False
    ket_gomb = _ketgombos_sor_szelessege(g)
    jelolo = _gyerek(window, "endEditModalityNeKerdezzenCheck")
    tartalom_min = max(320.0, jelolo.property("implicitWidth"), ket_gomb)
    # rontás-kontroll: a mérés csak akkor fogja meg a hibát, ha a Mégsével
    # együtt számolt sor szélesebb volna a jelölő sornál
    harom_gomb = ket_gomb + _RES + megse.property("implicitWidth")
    assert harom_gomb > tartalom_min + _TURES

    assert abs(g["Gombsor"].width() - ket_gomb) <= _TURES
    assert abs(g["Tartalom"].width() - tartalom_min) <= _TURES
    assert abs(
        g["DiscardButton"].left() - (g["ApplyButton"].right() + _RES)
    ) <= _TURES
    assert abs(g["DiscardButton"].right() - g["Tartalom"].right()) <= _TURES
    assert _parbeszed_teglalap(window).contains(g["Tartalom"])


def _assert_haromgombos_fokuszvaltas(window, qt_app):
    """A fókuszváltás (#3693) párbeszéde: Alkalmaz + Elvetés + Mégse egy
    sorban, a Mégse zárja jobbról, és mind a párbeszéden BELÜL van."""
    g = _elrendezes(window, qt_app)
    assert _gyerek(window, "endEditModalityCancelButton").property("visible")
    assert abs(
        g["DiscardButton"].left() - (g["ApplyButton"].right() + _RES)
    ) <= _TURES
    assert abs(
        g["CancelButton"].left() - (g["DiscardButton"].right() + _RES)
    ) <= _TURES
    assert abs(g["CancelButton"].right() - g["Tartalom"].right()) <= _TURES
    assert g["CancelButton"].top() == g["ApplyButton"].top()
    assert _parbeszed_teglalap(window).contains(g["Tartalom"])


class TestAParbeszedElrendezese:
    """A két kérdés-változat renderelt geometriája. A mód-belépés
    párbeszéde képpontra a #3651-es (Mégse nélküli) marad; a fókuszváltásé
    háromgombos, jobbra zárt sor."""

    def test_modbelepesnel_ketgombos_mint_eddig(self, magyar, qt_app):
        window, _controller, _engine = magyar
        _nezot_nyit(window, qt_app)
        _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerLayoutAa")

        assert _nyitva(window)
        _assert_ketgombos_modbelepes(window, qt_app)

    def test_fokuszvaltasnal_a_megse_zarja_jobbrol_a_sort(self, magyar, qt_app):
        window, _controller, _engine = magyar
        _ab_belep(window, qt_app)
        _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerSwapFocus")

        assert _nyitva(window)
        _assert_haromgombos_fokuszvaltas(window, qt_app)

    def test_ujranyitaskor_a_ket_valtozat_nem_hat_egymasra(self, magyar, qt_app):
        """Ugyanaz a párbeszéd-példány nyílik mindkét úton: a Mégse
        megjelenése, majd újra elrejtése után is a saját elrendezését kapja
        mindkét változat — és a Mégse valódi kattintásra a Mégsét találja."""
        window, _controller, _engine = magyar
        nezo = _nezot_nyit(window, qt_app)
        _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerLayoutAa")
        _assert_ketgombos_modbelepes(window, qt_app)
        _kattints(window, qt_app, "endEditModalityDiscardButton")
        assert nezo.property("layoutMode") == "aa"

        _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerSwapFocus")
        _assert_haromgombos_fokuszvaltas(window, qt_app)
        eredeti = nezo.property("aktivOldal")
        _kattints(window, qt_app, "endEditModalityCancelButton")
        assert not _nyitva(window)
        assert nezo.property("aktivOldal") == eredeti

        _kattints(window, qt_app, "viewerLayoutAb")
        assert _nyitva(window)
        _assert_ketgombos_modbelepes(window, qt_app)

    def test_a_megse_felirata_magyar(self, magyar, qt_app):
        window, _controller, _engine = magyar
        _ab_belep(window, qt_app)
        _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerSwapFocus")

        gomb = _gyerek(window, "endEditModalityCancelButton")
        assert gomb.property("text") == "Mégse"


# -- hova kerül az alkalmazott módosítás -------------------------------------


def _ini_szakasz(ini: Path, fajlnev: str) -> str:
    """A `.picasa.ini` egy fájl-szakaszának szövege (fejléc nélkül)."""
    szakasz: list[str] = []
    bent = False
    for sor in ini.read_text(encoding="utf-8").splitlines():
        if sor.startswith("["):
            bent = sor.strip() == f"[{fajlnev}]"
            continue
        if bent:
            szakasz.append(sor)
    return "\n".join(szakasz)


def _fajlnev(nezo, sor: int) -> str:
    url = QMetaObject.invokeMethod(
        nezo,
        "urlAt",
        Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG("QVariant"),
        Q_ARG("QVariant", sor),
    )
    return Path(QUrl(str(url)).path()).name


class TestAzAlkalmazottModositasHelye:
    def test_ab_modban_a_kijelolt_fel_fajljaba_kerul_a_vagas(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, _engine = qml_app
        nezo = _ab_belep(window, qt_app)
        kijelolt = _fajlnev(nezo, nezo.property("aktivSor"))
        masik = _fajlnev(nezo, nezo.property("abMasikSor"))
        assert kijelolt != masik
        _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerSwapFocus")

        _kattints(window, qt_app, "endEditModalityApplyButton")

        ini = tmp_path / "kepek" / ".picasa.ini"
        assert "crop64=1," in _ini_szakasz(ini, kijelolt)
        assert "crop64" not in _ini_szakasz(ini, masik)

    @pytest.mark.parametrize("alkalmaz", (True, False))
    def test_modositott_vorosszem_kerdez_es_a_valasz_szerint_ment(
        self, qml_app, qt_app, tmp_path, alkalmaz
    ):
        window, _controller, _engine = qml_app
        nezo = _ab_belep(window, qt_app)
        eredeti = nezo.property("aktivOldal")
        kijelolt = _fajlnev(nezo, nezo.property("aktivSor"))
        panel = _eszkozt_nyit_kattintva(
            window, qt_app, "editToolRedeye", "redeyeActive"
        )
        nezo.property("editCtl").addRedeyeRegion(0.4, 0.4, 0.1, 0.1)
        qt_app.processEvents()
        assert panel.property("redeyeRegionCount") == 1

        _kattints(window, qt_app, "viewerSwapFocus")
        assert _nyitva(window)
        assert nezo.property("aktivOldal") == eredeti

        gomb = "ApplyButton" if alkalmaz else "DiscardButton"
        _kattints(window, qt_app, f"endEditModality{gomb}")

        assert not _nyitva(window)
        assert nezo.property("aktivOldal") != eredeti
        assert panel.property("redeyeActive") is False
        ini = tmp_path / "kepek" / ".picasa.ini"
        szakasz = _ini_szakasz(ini, kijelolt) if ini.exists() else ""
        assert ("redeye=" in szakasz) is alkalmaz


def _aa_belep(window, qt_app):
    nezo = _nezot_nyit(window, qt_app)
    _kattints(window, qt_app, "viewerLayoutAa")
    assert nezo.property("layoutMode") == "aa"
    return nezo


class TestAzAaModKapuja:
    """„aa" módban a két fél ugyanannak a fotónak két önálló szerkesztése
    (#3014/#3649): a fókuszváltás a két láncot CSERÉLI. A kapunak ezt nem
    szabad megzavarnia."""

    def test_megse_utan_a_festes_a_sajat_felen_marad(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _aa_belep(window, qt_app)
        edit_ctl = nezo.property("editCtl")
        masik_hid = nezo.property("masodikEditCtl")
        edit_ctl.setChainValue(_VAMPIRSZEM_LANC)
        qt_app.processEvents()
        edit_ctl.paintStroke(0.5, 0.5)
        qt_app.processEvents()
        eredeti = nezo.property("aktivOldal")
        panel, _overlay = _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerSwapFocus")
        assert _nyitva(window)
        _kattints(window, qt_app, "endEditModalityCancelButton")

        assert nezo.property("aktivOldal") == eredeti
        assert panel.property("cropActive") is True
        assert edit_ctl._paint_strokes()
        assert not masik_hid.controller._paint_strokes()

    def test_alkalmaz_utan_a_vagas_a_regi_aktiv_fel_lancaba_kerul(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        nezo = _aa_belep(window, qt_app)
        edit_ctl = nezo.property("editCtl")
        masik_hid = nezo.property("masodikEditCtl")
        assert "crop64" not in edit_ctl.property("chainValue")
        assert "crop64" not in masik_hid.property("chainValue")
        eredeti = nezo.property("aktivOldal")
        _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerSwapFocus")
        _kattints(window, qt_app, "endEditModalityApplyButton")

        # a fókusz átment: a fő vezérlő MOST a másik (vágatlan) felet
        # szerkeszti, a vágás a régi aktív fél láncával a memóriás oldalra
        # került — nem veszett el, és nem a másik félre íródott.
        assert nezo.property("aktivOldal") != eredeti
        assert "crop64" not in edit_ctl.property("chainValue")
        assert "crop64" in masik_hid.property("chainValue")
