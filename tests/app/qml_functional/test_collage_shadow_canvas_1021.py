"""A vetett árnyék az ÉLŐ VÁSZNON, kirajzolva — #1021.

A #977 az árnyékot a magba építette be: a **mentett kép** azóta témánként
helyes árnyékot kap. Az élő vászon viszont változatlan maradt, és a
felhasználó a **v0.8.4-en** jelezte, hogy a jelölőnégyzet kapcsolgatása nem
csinál semmit. Ez a lap azt méri, amit ő lát: a **kirajzolt képpontokat**.

## Miért mérhető ez fejnélküli környezetben is

A #1010 tanulsága az volt, hogy a képpont-alapú mérés a CI-ban félrevisz:
a szoftveres rasterizáló az ÉLSIMÍTÁST a hibás kódon is elvégzi, tehát ott
a mérés a hiba mellett is zöld maradt. **Itt más a helyzet, és ezt ki kell
mondani:** az árnyék nem a rasterizáló egy tulajdonsága, hanem egy
kirajzolt, alfás textúra. Ha a `BorderImage` nincs ott vagy üres, a
szoftveres háttér is pontosan annyit rajzol: **semmit**. A mérés tehát a
hibás kódon MEGBUKIK, nem zöldül.

Shader itt szándékosan nincs (a `QtQuick.Effects` a felhasználó gépén nincs
telepítve — ld. `collage/shadow_sprite.py`), ezért a szoftveres és a GPU-s
háttér ugyanazt a képet adja.

A képpontmérés MELLETT geometria-szintű őrök is állnak: hogy a csempe
mérete a saját szegélyéhez illeszkedjen, és hogy a Többszörös exponálásnál
elem se szülessen.

## ⚠️ Amit ez a lap NEM állít, mert külön hiba

A vászon és a rajzoló **ellentétes irányba forgat**: ugyanarra a `theta`-ra
a `_rotated_paste` (OpenCV, óramutatóval szemben) és a QML `rotation`
(óramutató szerint) tükörképet ad. Mérve ugyanazon a jeleneten: a mag
−43 képpontot, a QML +43-at dönt. Ez a #947 óta fennálló, az árnyéktól
FÜGGETLEN eltérés — az árnyék a csomópont gyereke, tehát vele EGYÜTT fordul
akármelyik irányba. Ezért a képpontos egyezést itt `theta = 0`-n mérjük, a
forgatott esetben pedig azt, ami az árnyékról szól: hogy az eltolás a
vászon tengelyei szerint marad jobbra-le.

Beégetett kivonat sehol (#942): minden állítás tűréssel mér.
"""

from __future__ import annotations

import re

import math

import numpy as np
import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

from picasapy.collage.shadow import ShadowParams, draw_shadow
from picasapy.collage.themes import CONTACTSHEET, MULTIEXP, PICTUREPILE

from support.collage_canvas_harness import (
    _ablakban,
    _child,
    _csomopontok,
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


# --------------------------------------------------------------------------
# Kiszolgáló
# --------------------------------------------------------------------------

_KEEPALIVE: list[object] = []


def _var(korok=8):
    """Eseménypörgetés határidővel — az elrendezés és a `data:` URL-ből
    érkező csempe sem áll elő azonnal (a Qt a nem helyi URL-t a hálózati
    rétegen keresztül tölti, tehát aszinkron)."""
    from PySide6.QtGui import QGuiApplication

    for _ in range(korok):
        QGuiApplication.processEvents()
        szunet = QEventLoop()
        QTimer.singleShot(20, szunet.quit)
        szunet.exec()


def _keppontok(view) -> np.ndarray:
    """Az ablak VÖRÖS csatornája `float32` tömbként.

    Szürke háttéren és fekete árnyéknál a három csatorna együtt mozog, egy
    is elég — és így a mérés a színtértől független marad."""
    kep = view.grabWindow()
    assert not kep.isNull(), "az ablakot nem lehetett kirajzolni"
    magas, szeles = kep.height(), kep.width()
    return np.array(
        [[kep.pixelColor(x, y).red() for x in range(szeles)] for y in range(magas)],
        dtype=np.float32,
    )


def _sotetedes(panel, controller, theme) -> np.ndarray:
    """MENNYIVEL sötétebb a vászon az árnyékkal, mint nélküle.

    Két kirajzolás különbsége: ami az árnyék bekapcsolásától sötétedik, az
    az árnyék. Ez a mérés nem függ attól, milyen színűek a képek — és nem
    tartalmaz beégetett várt értéket."""
    view = panel.property("_view")
    controller.setCollageTheme(theme)
    controller.setCollageShadows(False)
    _var()
    nelkule = _keppontok(view)
    controller.setCollageShadows(True)
    _var()
    vele = _keppontok(view)
    return nelkule - vele


def _lapon(panel, terkep: np.ndarray) -> np.ndarray:
    """A különbség-térkép LAPRA eső része — a panel többi része nem érdekes."""
    x, y, w, h = _ablakban(_lap(panel))
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1 = min(terkep.shape[1], int(x + w))
    y1 = min(terkep.shape[0], int(y + h))
    return terkep[y0:y1, x0:x1]


# --------------------------------------------------------------------------
# 1. A felhasználó bejelentése: LÁTSZIK-e egyáltalán
# --------------------------------------------------------------------------


class TestLatszikEAVasznon:
    def test_a_bekapcsolt_arnyek_SOTETITI_a_vasznat(self, controller, qt_app):
        """A jegy szíve. A jelölőnégyzet bekapcsolása mérhető, sötét
        képpontokat hoz a lapra — ez az, ami a v0.8.4-ben nem történt meg."""
        panel = _panel(controller)
        terkep = _lapon(panel, _sotetedes(panel, controller, PICTUREPILE))
        assert terkep.max() > 20, (
            "az árnyék bekapcsolása nem sötétített a vásznon "
            f"(legnagyobb változás {terkep.max():.1f}/255)"
        )
        assert int((terkep > 5).sum()) > 200, (
            f"csak {int((terkep > 5).sum())} képpont változott — az árnyék "
            "nem egy folt, hanem a csempék körüli sáv"
        )

    def test_a_kikapcsolas_ELTUNTETI(self, controller, qt_app):
        """A másik irány: aki kikapcsolja, tiszta lapot kap vissza.

        Enélkül a jelölőnégyzet »egyirányú« volna: bekapcsol, de nem old."""
        panel = _panel(controller)
        view = panel.property("_view")
        controller.setCollageTheme(PICTUREPILE)
        controller.setCollageShadows(True)
        _var()
        controller.setCollageShadows(False)
        _var()
        elso = _keppontok(view)
        controller.setCollageShadows(True)
        _var()
        controller.setCollageShadows(False)
        _var()
        masodik = _keppontok(view)
        assert np.abs(elso - masodik).max() <= 2.0, (
            "az árnyék kikapcsolása nem állította vissza a lapot"
        )

    def test_a_tobbszoros_exponalasnal_NINCS_arnyek(self, controller, qt_app):
        """A maszk 11. bitje. A felhasználó be sem tudja kapcsolni — a
        vásznon sem szabad megjelennie."""
        panel = _panel(controller)
        controller.setCollageTheme(MULTIEXP)
        controller.setCollageShadows(True)
        _var()
        for index in range(len(_csomopontok(controller))):
            elem = _child(panel, f"collageNodeShadow{index}")
            assert elem.property("visible") is False, (
                f"a(z) {index}. csomópontnak árnyék-eleme látszik a "
                "Többszörös exponálásban"
            )

    def test_az_arnyek_a_SAJAT_kepe_ALATT_marad(self, controller, qt_app):
        """A rétegsorrend: minden csempe árnyéka a csempe ALATT van.

        A rajzoló ezt úgy mondja ki, hogy „minden csempének a saját árnyéka
        közvetlenül előtte rajzolódik" (`draw_nodes`) — ettől esik a felül
        lévő kép árnyéka az alatta lévőre, és ettől plasztikus a Képkupac.
        A vásznon ennek a megfelelője az, hogy az árnyék a csomópont
        GYEREKE, negatív `z`-vel. Ha közös felső rétegbe kerülne, a
        legfelső kép a SAJÁT árnyékát kapná magára.

        A mérés a legfelső csomópont KÖZEPÉRE esik: a doboz sarkai a
        forgatás miatt a csomóponton kívülre lógnak, ott az árnyék jogosan
        látszik."""
        panel = _panel(controller)
        terkep = _sotetedes(panel, controller, PICTUREPILE)
        felso = _child(panel, f"collageNode{len(_csomopontok(controller)) - 1}")
        x, y, w, h = _ablakban(felso)
        kozep = terkep[
            int(y + 0.3 * h) : int(y + 0.7 * h), int(x + 0.3 * w) : int(x + 0.7 * w)
        ]
        assert kozep.max() <= 2.0, (
            f"a legfelső kép közepére árnyék esett ({kozep.max():.1f}/255) — "
            "a saját árnyéka került fölé"
        )
        # …és tényleg VAN mit takarnia: a lapon rajzolódott árnyék.
        # ⚠️ A mérés a LAPRA szűkül: a panel többi része (a jelölőnégyzet
        # rajza, a „mentetlen" jelzés) az árnyéktól függetlenül is változik
        # a kapcsolgatástól — mérve, e nélkül a szűkítés nélkül ez az őr a
        # hibás kódon is zöld maradt.
        assert _lapon(panel, terkep).max() > 20, "sehol nincs árnyék a lapon"


# --------------------------------------------------------------------------
# 2. Geometria-szintű őrök — a képpont mellé
# --------------------------------------------------------------------------


def _csomopontja(elem):
    """Az árnyék-csempét viselő CSOMÓPONT — a szülője ma már a rajz-tartó.

    A #1016 óta a csomópont rajza egy külön, a doboznál nagyobb tartóban ül
    (`collageNodeLayer*`): a réteg-alapú élsimításnak átlátszó peremre van
    szüksége, és az árnyéknak is el kell férnie benne. Az árnyék tehát a
    csomópont LESZÁRMAZOTTJA, nem közvetlen gyereke — az őrizni való
    állítás (a saját csomópontjához tartozik, nem közös felső rétegbe
    került) változatlan."""
    szulo = elem.parentItem()
    while szulo is not None:
        if re.fullmatch(r"collageNode\d+", szulo.objectName()):
            return szulo
        szulo = szulo.parentItem()
    return None


class TestAGeometria:
    def test_a_csempe_szegelye_a_halo_ketszerese(self, controller, qt_app):
        """A `BorderImage` szegélye a haló kétszerese, mert az átmenet a
        doboz éle KÖRÜL zajlik. Ha ez elcsúszik, a nyújtott középső sáv nem
        telített képpontokat nyújt, és a nagy csempéken csík keletkezik."""
        panel = _panel(controller)
        controller.setCollageTheme(PICTUREPILE)
        controller.setCollageShadows(True)
        _var()
        elem = _child(panel, "collageNodeShadow0")
        csomopont = _csomopontja(elem)
        halo = csomopont.property("shadowSupport")
        assert halo >= 1
        assert csomopont.property("shadowBorder") == 2 * halo

    def test_az_arnyek_TULLOG_a_csomoponton(self, controller, qt_app):
        """A csempe minden élen egy halónyival nagyobb a csomópontnál —
        különben az árnyék a saját dobozán belül végződne, azaz nem
        látszana ki mögüle."""
        panel = _panel(controller)
        controller.setCollageTheme(PICTUREPILE)
        controller.setCollageShadows(True)
        _var()
        elem = _child(panel, "collageNodeShadow0")
        csomopont = _csomopontja(elem)
        halo = csomopont.property("shadowSupport")
        assert elem.width() == pytest.approx(csomopont.width() + 2 * halo)
        assert elem.height() == pytest.approx(csomopont.height() + 2 * halo)

    def test_az_arnyek_a_csomopont_GYEREKE_negativ_z_vel(self, controller, qt_app):
        """A rétegsorrend fa-szintű őre a képpontmérés mellé.

        Ha az árnyékok közös, legfelső rétegbe kerülnének (kézenfekvő
        „egyszerűsítés"), a képpontmérés ugyan bukna, de az ok csak ebből
        derülne ki: az árnyéknak a SAJÁT csomópontja alatt a helye."""
        panel = _panel(controller)
        controller.setCollageTheme(PICTUREPILE)
        controller.setCollageShadows(True)
        _var()
        for index in range(len(_csomopontok(controller))):
            elem = _child(panel, f"collageNodeShadow{index}")
            szulo = _csomopontja(elem)
            assert szulo is not None and szulo.objectName() == f"collageNode{index}", (
                f"a(z) {index}. árnyék nem a saját csomópontja leszármazottja"
            )
            assert elem.z() < 0, "az árnyék a saját keretének és képének fölé kerül"

    def test_minden_csomopont_UGYANAZT_a_csempet_kapja(self, controller, qt_app):
        """350 csomópont EGY textúrát oszt meg: a `data:` URL szövege
        azonos, ezért a Qt egyszer tölti be. Ha csomópontonként külön URL
        születne, a nagy kollázs memóriája ezzel szorzódna."""
        panel = _panel(controller)
        controller.setCollageTheme(PICTUREPILE)
        controller.setCollageShadows(True)
        _var()
        urlek = {
            _child(panel, f"collageNodeShadow{i}").property("source").toString()
            for i in range(len(_csomopontok(controller)))
        }
        assert len(urlek) == 1, f"{len(urlek)} különböző árnyék-csempe született"


# --------------------------------------------------------------------------
# 3. Egyezik-e a MENTETT képpel — próbajelenet, képpontról képpontra
# --------------------------------------------------------------------------

#: FEHÉR lap: az árnyék sötétedése ezen mérhető a legtisztábban, és a
#: `draw_shadow` is fehér vászonnal hasonlítható össze.
_PROBA_LAP = b'import QtQuick\nRectangle { width: 300; height: 300; color: "white" }\n'

#: A próbacsomópont doboza — jóval nagyobb a halónál, hogy a kilenc szelet
#: mindegyike valódi területet kapjon.
PROBA_W, PROBA_H = 160, 120
PROBA_X, PROBA_Y = 70, 90
PROBA_ELMOSAS = 6.0
PROBA_ALFA = 153
PROBA_OFFSET = (4.0, 6.0)


def _proba_ablak(
    controller, theta: float, elmosas: float = PROBA_ELMOSAS, alfa: int = PROBA_ALFA
) -> QQuickView:
    """Egyetlen `CollageNode` fehér lapon, KÉZZEL megadott árnyékkal.

    A `CollageNode` nincs kiajánlva a `qmldir`-ben (a panel belső eleme),
    ezért fájl-URL-lel töltjük be — a tesztért nem ajánljuk ki nyilvános
    típusnak. A minta a #1010 próbaablaka."""
    import picasapy.app.application as app_module

    qml_dir = app_module._APP_DIR / "qml"
    view = QQuickView()
    view.engine().addImportPath(str(qml_dir))

    hatter = QQmlComponent(view.engine())
    hatter.setData(_PROBA_LAP, QUrl())
    assert [e.toString() for e in hatter.errors()] == []
    lap = hatter.create()
    lap.setParentItem(view.contentItem())

    forras = QQmlComponent(
        view.engine(), QUrl.fromLocalFile(str(qml_dir / "PicasaPy" / "CollageNode.qml"))
    )
    assert [e.toString() for e in forras.errors()] == []
    csomopont = forras.create()
    csomopont.setParentItem(lap)

    csempe = controller.collageShadowSprite(elmosas, alfa)
    for nev, ertek in (
        ("unit", 1.0),
        ("centerX", PROBA_X + PROBA_W / 2.0),
        ("centerY", PROBA_Y + PROBA_H / 2.0),
        ("nodeWidth", float(PROBA_W)),
        ("nodeHeight", float(PROBA_H)),
        ("theta", theta),
        ("border", "noborder"),
        ("missing", False),
        ("shadowSource", csempe["url"]),
        ("shadowSupport", csempe["support"]),
        ("shadowBorder", csempe["border"]),
        ("shadowOffsetX", PROBA_OFFSET[0]),
        ("shadowOffsetY", PROBA_OFFSET[1]),
    ):
        csomopont.setProperty(nev, ertek)

    view.resize(300, 300)
    view.show()
    assert QTest.qWaitForWindowExposed(view, 5000), "a próbaablak nem jelent meg"
    _var()
    _KEEPALIVE.extend((view, lap, csomopont, hatter, forras))
    return view


def _mag_rajza(theta: float) -> np.ndarray:
    """UGYANAZ az árnyék a magtól, `draw_shadow`-val, fehér vásznon."""
    vaszon = np.full((300, 300, 3), 255, np.uint8)
    draw_shadow(
        vaszon,
        x=PROBA_X,
        y=PROBA_Y,
        width=PROBA_W,
        height=PROBA_H,
        theta=theta,
        params=ShadowParams(
            offset_x=PROBA_OFFSET[0],
            offset_y=PROBA_OFFSET[1],
            blur=PROBA_ELMOSAS,
            opacity=PROBA_ALFA / 256.0,
        ),
    )
    return vaszon[..., 0].astype(np.float32)


class TestATemankentiRecept:
    """A négy paraméterkészlet a VÁSZNON is négy — nem egy közös.

    ⚠️ Ezt a valódi panelen mérni **nem lehet**: ott a témák elrendezése is
    más. Mérve: a Képkupacnál (alfa 102) a lap legsötétebb képpontja 64, az
    Indexképnél (alfa 153) 69 — mert a kupac egymást fedő képein az
    árnyékok EGYMÁSRA rakódnak, és a különbség eltűnik a zajban. A recept
    tehát csak azonos geometrián mérhető: ugyanaz a próbacsomópont, csak a
    téma alfájával.

    Ha valaki a vásznat egyetlen közös átlátszatlansággal írná meg, a két
    téma `collageShadow["alpha"]`-ja egyenlő lenne, és ez a lap bukna."""

    def _temak_alfaja(self, controller, theme) -> int:
        controller.setCollageTheme(theme)
        controller.setCollageShadows(True)
        return controller.collageShadow["alpha"]

    def test_az_indexkep_arnyeka_sotetebb_a_kepkupacenal(self, controller, qt_app):
        gyenge_alfa = self._temak_alfaja(controller, PICTUREPILE)
        eros_alfa = self._temak_alfaja(controller, CONTACTSHEET)
        assert eros_alfa > gyenge_alfa, "a két téma alfája azonos lett"

        gyenge = 255.0 - _keppontok(
            _proba_ablak(controller, 0.0, alfa=gyenge_alfa)
        ).min()
        eros = 255.0 - _keppontok(_proba_ablak(controller, 0.0, alfa=eros_alfa)).min()
        # az arány az alfák aránya (153/102 = 1,5); a tűrés bőven tág
        assert eros > gyenge * 1.25, (
            f"az Indexkép árnyéka ({eros:.1f}) nem sötétebb érdemben a "
            f"Képkupacénál ({gyenge:.1f}) — közös paraméterkészlet szaga van"
        )


class TestAzEgyezesAMentettel:
    def test_a_vasznon_UGYANAZ_az_arnyek_mint_a_mentett_kepen(
        self, controller, qt_app
    ):
        """A #920 elfogadási feltétele: „a mentett kép pontosan azt mutatja,
        amit a vásznon látsz."

        A csomópont doboza kimarad az összevetésből — ott a vásznon a kép
        (illetve `noborder`-nél a semmi) van, a mag pedig csak az árnyékot
        rajzolta. Az árnyék KÖRÜLÖTTE lévő sávja viszont mindkét oldalon
        ugyanaz kell legyen."""
        view = _proba_ablak(controller, 0.0)
        vaszon = _keppontok(view)
        mag = _mag_rajza(0.0)

        kivul = np.ones_like(mag, dtype=bool)
        kivul[PROBA_Y : PROBA_Y + PROBA_H, PROBA_X : PROBA_X + PROBA_W] = False
        elteres = np.abs(vaszon - mag)[kivul]
        assert elteres.max() <= 6.0, (
            f"a vászon árnyéka {elteres.max():.1f}/255-tel tér el a mentettétől"
        )
        # …és tényleg VAN mit összevetni: az árnyék nem üres
        assert (255.0 - mag)[kivul].max() > 20

    def test_az_arnyek_iranya_jobbra_le_forgatott_csomoponton_is(
        self, controller, qt_app
    ):
        """A forgatott csomópontnál az eltolás a VÁSZON tengelyei szerint
        marad jobbra-le — ezért forgatja vissza a `CollageNode` az eltolást
        a saját rendszerébe.

        Aki a visszaforgatást kihagyja, annál az árnyék iránya képenként
        más lesz. A Képkupac 0…−5°-ánál épp csak annyira, hogy a
        felhasználó azt mondja: „valami nem stimmel"."""
        view = _proba_ablak(controller, math.radians(30.0))
        vaszon = _keppontok(view)
        sotet = np.argwhere(vaszon < 250)
        assert sotet.size > 0, "a forgatott csomópontnak nincs árnyéka"
        suly = (255.0 - vaszon)[vaszon < 250]
        kozep_y = float((sotet[:, 0] * suly).sum() / suly.sum())
        kozep_x = float((sotet[:, 1] * suly).sum() / suly.sum())
        assert kozep_x > PROBA_X + PROBA_W / 2.0, (
            f"az árnyék súlypontja ({kozep_x:.1f}) nem jobbra esik a "
            "csomópont közepétől"
        )
        assert kozep_y > PROBA_Y + PROBA_H / 2.0, (
            f"az árnyék súlypontja ({kozep_y:.1f}) nem lefelé esik a "
            "csomópont közepétől"
        )
