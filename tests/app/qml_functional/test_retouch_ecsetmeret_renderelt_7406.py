"""A Retusálás ecsetkörének mérete a renderelt képkockán (#7406).

Referencia: az eredeti Picasa felvételei (`job-907 __12`, `job-908 __14`/`__20`,
`job-917 __14`/`__20`, `job-918 __12`/`__18`/`__24`). A képfájlok az eredeti program
grafikáját tartalmazzák, ezért NEM kerülnek a repóba: a teszt a róluk MÉRT számokat tartalmazza
(`_REF_*`), a mi oldalunkon pedig a valódi, offscreen renderelt képkockából mér (`grabWindow`).

A mérés: a gyűrű fehér képpontpárjainak távolsága a gyűrű közepén átmenő vízszintes ÉS függőleges
vonal mentén (a fehér vonal súlyozott középpontjai között). Ugyanez a mérés a mi gyűrűnkön és a
referenciakockákon, ±1 képpont tűréssel (a jegy névleges számai: 6, 46, 142, 194; 54, 214, 6).

A beállítás VALÓDI egérrel történik: a csúszka fogantyúját húzza a teszt a futás kívánt helyére,
a gyűrű pedig a kép fölé vitt egérrel jelenik meg. A nagyítást a nézőn állítja be, hogy a `z`
megegyezzen a referenciáéval (0,97 a 1024 x 256-os képen, 1,07 a 768 x 512-esen).

Ha a `PICASAPY_7406_KIMENET` környezeti változó egy mappa, a képkockák oda is kimentődnek
(kézi szemrevételezéshez); ezt a normál futás nem használja.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre

_KIMENET_VALTOZO = "PICASAPY_7406_KIMENET"
#: A referencia ablakán a 1024 x 256-os kép 989 képpont szélesen látszott (x 287-1275): a nagyítás
#: 989 / 1024 = 0,966, a „Zoomed to 97%" felirat. Ezen a szélességen a kép nálunk is 989 széles.
_ABLAK = (1297, 1024)
_PONT_TOLERANCIA = 1.0

# A referenciakockák gyűrűinek fehér képpontpár-távolsága: a kockákon UGYANEZZEL a méréssel mérve
# (vízszintes és függőleges átlaga). A jegy névleges számai (6, 46, 142, 194; 54, 214, 6) a
# `2 · R` értékek: a mért pár-távolság az egy képpont vastag vonalnál nagyjából eggyel nagyobb
# (a vonal képpontjai közti távolság), ezért a ±1 tűrés a mért értékekhez igazodik.
_REF_BAL_VEG = 6.0  # job-908 __14 (z 0,97, mért 5,96) és job-918 __24 (z 1,07): R = 3,0
_REF_24_2_SZAZALEK = 47.0  # job-917 __14: a futás 24,2%-án (R = 23,0)
_REF_73_5_SZAZALEK = 142.8  # job-917 __20: a futás 73,5%-án (R = 71,0; mért 142,55 és 143,0)
_REF_JOBB_VEG_097 = 194.8  # job-908 __20: jobb vég (R = 97,0; mért 194,57 és 195,0)
_REF_INDULO_097 = 49.0  # job-907 __12: induló állás (R = 24,0)
_REF_INDULO_107 = 55.0  # job-918 __12: induló állás (R = 27,0)
_REF_JOBB_VEG_107 = 215.0  # job-918 __18: jobb vég (R = 107,0)
_REF_INDULO_080 = 40.0  # a job #314 képernyőképe: 1024 x 1024-es kép, 80%, R = 20,0 (nincs kocka: a lap száma)


def _szurke_atmenet(lib: Path) -> None:
    """A referencia `gray_ramp.jpg` mása: 1024 x 256, fekete-fehér vízszintes átmenet."""
    szelesseg, magassag = 1024, 256
    sor = np.linspace(0, 255, szelesseg).astype(np.uint8)
    adat = np.tile(sor[None, :, None], (magassag, 1, 3))
    Image.fromarray(adat, "RGB").save(lib / "gray_ramp.jpg", quality=95)


def _szines_atmenet(szelesseg: int, magassag: int):
    def keszit(lib: Path) -> None:
        """A referencia `rgb_gradient.jpg` jellegű kép: kék bal felül, piros jobb felül, cián bal
        alul, sárga jobb alul (R = x, G = y, B = 1 - x)."""
        x = np.broadcast_to(np.linspace(0.0, 1.0, szelesseg)[None, :], (magassag, szelesseg))
        y = np.broadcast_to(np.linspace(0.0, 1.0, magassag)[:, None], (magassag, szelesseg))
        adat = np.stack([x, y, 1.0 - x], axis=-1)
        Image.fromarray((adat * 255).astype(np.uint8), "RGB").save(lib / "rgb_gradient.jpg", quality=95)

    return keszit


_KEPEK = {
    "szurke_1024x256": _szurke_atmenet,
    "szines_768x512": _szines_atmenet(768, 512),
    "szines_1024x1024": _szines_atmenet(1024, 1024),
}


@pytest.fixture
def kep_app(request, rogzitett_betu, qt_app, tmp_path):
    """A kért képpel felépített app (a `request.param` a `_KEPEK` kulcsa)."""
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_KEPEK[request.param],
        belyegkep_meret=256,
        valodi_belyegkep=True,
        keep_modul=request.module,
    )


def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _elem(ablak, nev: str) -> QQuickItem:
    elem = ablak.findChild(QObject, nev)
    assert isinstance(elem, QQuickItem), f"a(z) {nev} nem található a QML-fában"
    return elem


def _ment(kep: QImage, nev: str) -> None:
    mappa = os.environ.get(_KIMENET_VALTOZO)
    if not mappa:
        return
    cel = Path(mappa)
    cel.mkdir(parents=True, exist_ok=True)
    assert kep.save(str(cel / f"{nev}.png"), "PNG")


def _szurke(kep: QImage) -> np.ndarray:
    rgba = kep.convertToFormat(QImage.Format.Format_RGBA8888)
    adat = np.frombuffer(rgba.constBits(), dtype=np.uint8)
    rgb = (
        adat.reshape(rgba.height(), rgba.bytesPerLine())[:, : rgba.width() * 4]
        .reshape(rgba.height(), rgba.width(), 4)[:, :, :3]
        .astype(int)
    )
    return (rgb[:, :, 0] * 299 + rgb[:, :, 1] * 587 + rgb[:, :, 2] * 114) // 1000


def _kattint(ablak, elem: QQuickItem) -> None:
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, pos=QPoint(round(kozep.x()), round(kozep.y())))


def _retusalas_megnyit(ablak, qt_app) -> tuple[QQuickItem, QQuickItem]:
    """Megnyitja a nézőt és a Retusálás eszközt; visszaadja a nézőt és a kattintási területet."""
    szelesseg, magassag = _ABLAK
    ablak.setWidth(szelesseg)
    ablak.setHeight(magassag)
    assert _var(qt_app, lambda: ablak.width() == szelesseg and ablak.height() == magassag)
    ablak.setProperty("viewerOpen", True)
    nezo = _elem(ablak, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    kep = _elem(ablak, "viewerImage")
    assert _var(qt_app, lambda: kep.property("visible") and kep.property("paintedWidth") > 0)
    csempe = _elem(ablak, "editToolRetouch")
    assert _var(qt_app, lambda: csempe.isVisible() and csempe.width() > 0)
    _kattint(ablak, csempe)
    panel = _elem(ablak, "viewerEditorPanel")
    assert _var(qt_app, lambda: panel.property("retouchActive") is True)
    terulet = _elem(ablak, "retouchClickArea")
    assert _var(qt_app, lambda: terulet.width() > 0 and terulet.property("viewZoom") > 0)
    qt_app.processEvents()
    return nezo, terulet


def _nagyitast_allit(qt_app, nezo, terulet, cel: float) -> float:
    """A nézőn beállítja a `cel` nagyítást (megjelenített képpont / forrásképpont): előbb végigtapogatja
    a `zoomValue` [0, 1] tartományát, megkeresi, hol lépi át a célt, majd felezéssel pontosítja."""

    def zoom_ennel(ertek: float) -> float:
        nezo.setProperty("zoomValue", ertek)
        qt_app.processEvents()
        return float(terulet.property("viewZoom"))

    pontok = [i / 100 for i in range(101)]
    zoomok = [zoom_ennel(v) for v in pontok]
    for i in range(100):
        if (zoomok[i] - cel) * (zoomok[i + 1] - cel) <= 0:
            also, felso = pontok[i], pontok[i + 1]
            novekvo = zoomok[i + 1] > zoomok[i]
            break
    else:
        raise AssertionError(f"a {cel} nagyítás nem érhető el a nézőn ({min(zoomok)} .. {max(zoomok)})")
    for _ in range(40):
        kozep = (also + felso) / 2
        if abs(zoom_ennel(kozep) - cel) < 0.0004:
            break
        if (terulet.property("viewZoom") < cel) == novekvo:
            also = kozep
        else:
            felso = kozep
    return float(terulet.property("viewZoom"))


def _csuszka_huzasa(ablak, qt_app, t: float) -> None:
    """A „Brush Size" csúszka fogantyúját valódi egérrel a futás `t` helyére húzza (a fogantyú
    KÖZEPE kerül oda)."""
    csuszka = _elem(ablak, "retouchBrushSizeSlider")
    fogantyu = csuszka.property("handle")
    assert isinstance(fogantyu, QQuickItem)
    bal = csuszka.property("leftPadding") + fogantyu.width() / 2
    futas = csuszka.property("availableWidth") - fogantyu.width()
    kozep_y = csuszka.height() / 2
    innen = fogantyu.mapToScene(QPointF(fogantyu.width() / 2, fogantyu.height() / 2))
    ide = csuszka.mapToScene(QPointF(bal + t * futas, kozep_y))
    QTest.mousePress(ablak, Qt.MouseButton.LeftButton, pos=QPoint(round(innen.x()), round(innen.y())))
    kozbulso = QPoint(round((innen.x() + ide.x()) / 2), round(ide.y()))
    QTest.mouseMove(ablak, kozbulso)
    QTest.mouseMove(ablak, QPoint(round(ide.x()), round(ide.y())))
    QTest.mouseRelease(ablak, Qt.MouseButton.LeftButton, pos=QPoint(round(ide.x()), round(ide.y())))
    qt_app.processEvents()


def _kep_a_kurzorral(ablak, qt_app, terulet) -> tuple[QImage, QPointF]:
    """A kép fölé viszi az egeret (a kép bal oldali harmadába, ahol az átmenet még nem fehér), és
    visszaadja a képkockát és a gyűrű közepét az ablak képpontjaiban."""
    pont = terulet.mapToScene(QPointF(terulet.width() * 0.32, terulet.height() * 0.45))
    QTest.mouseMove(ablak, QPoint(round(pont.x()), round(pont.y())))
    kurzor = _elem(ablak, "retouchBrushCursor")
    assert _var(qt_app, lambda: kurzor.property("visible") and terulet.property("containsMouse"))
    qt_app.processEvents()
    kep = ablak.grabWindow()
    assert not kep.isNull()
    kozep = kurzor.mapToScene(QPointF(kurzor.width() / 2, kurzor.height() / 2))
    return kep, kozep


def _fenyes_csoportok(vonal: np.ndarray) -> list[float]:
    """A helyi háttérnél legalább 60 szürkeárnyalattal világosabb képpontok folytonos csoportjainak
    súlyozott középpontjai."""
    vonal = vonal.astype(float)
    kitoltve = np.pad(vonal, 4, mode="edge")
    hatter = np.convolve(kitoltve, np.ones(9) / 9, mode="valid")
    kulonbseg = vonal - hatter
    maszk = kulonbseg > 60
    csoportok: list[float] = []
    i = 0
    while i < len(vonal):
        if maszk[i]:
            j = i
            while j < len(vonal) and maszk[j]:
                j += 1
            suly = kulonbseg[i:j]
            csoportok.append(float((np.arange(i, j) * suly).sum() / suly.sum()))
            i = j
        else:
            i += 1
    return csoportok


def _par_tavolsagok(kep: QImage, kozep: QPointF, felsugar: float) -> tuple[float, float]:
    """A gyűrű fehér képpontpárjainak távolsága vízszintesen és függőlegesen."""
    szurke = _szurke(kep)
    cx, cy = round(kozep.x()), round(kozep.y())
    fel = int(felsugar) + 14
    sor = szurke[cy, cx - fel : cx + fel + 1]
    oszlop = szurke[cy - fel : cy + fel + 1, cx]
    eredmeny = []
    for nev, vonal in (("vízszintes", sor), ("függőleges", oszlop)):
        csoportok = _fenyes_csoportok(vonal)
        assert len(csoportok) >= 2, f"a {nev} vonalon nem látszik a gyűrű két oldala: {csoportok}"
        eredmeny.append(csoportok[-1] - csoportok[0])
    return eredmeny[0], eredmeny[1]


def _jegyez(felirat: str, ertek) -> None:
    """A mért érték a kimeneti mappa `meres.txt` fájljába kerül (csak ha a mappa meg van adva)."""
    mappa = os.environ.get(_KIMENET_VALTOZO)
    if not mappa:
        return
    cel = Path(mappa)
    cel.mkdir(parents=True, exist_ok=True)
    with (cel / "meres.txt").open("a", encoding="utf-8") as fajl:
        fajl.write(f"{felirat}: {ertek}\n")


def _ellenoriz(kep, kozep, mert_ref: float, felirat: str, kimenet: str) -> None:
    _ment(kep, kimenet)
    vizszintes, fuggoleges = _par_tavolsagok(kep, kozep, mert_ref / 2)
    _jegyez(felirat, f"referencia {mert_ref}, mért vízszintes {vizszintes:.2f}, függőleges {fuggoleges:.2f}")
    for irany, ertek in (("vízszintes", vizszintes), ("függőleges", fuggoleges)):
        assert abs(ertek - mert_ref) <= _PONT_TOLERANCIA + 1e-6, (
            f"{felirat}: a gyűrű fehér képpontpárjainak {irany} távolsága {ertek:.2f}, "
            f"a referencia {mert_ref} (±{_PONT_TOLERANCIA})"
        )


@pytest.mark.parametrize("kep_app", ["szurke_1024x256"], indirect=True)
def test_szurke_kepen_097_nagyitasnal_a_gyuru_a_referenciakockakkal_egyezik(kep_app, qt_app):
    """job-907 __12 (induló), job-908 __14 (bal vég), job-917 __14 és __20 (a futás 24,2% és 73,5%-a),
    job-908 __20 (jobb vég): ugyanazon a képen és nagyításon (z = 0,97, „Zoomed to 97%")."""
    ablak, _controller, _engine = kep_app
    nezo, terulet = _retusalas_megnyit(ablak, qt_app)
    zoom = float(terulet.property("viewZoom"))
    assert 0.964 <= zoom <= 0.975, f"a nagyítás {zoom}, a referencián 97% (989 képpont széles kép)"
    csuszka = _elem(ablak, "retouchBrushSizeSlider")
    assert abs((csuszka.property("visualPosition")) - 0.5) <= 0.01, "induláskor a fogantyú a futás közepén áll"

    # induláskor a csúszka érintetlen: s = 0,25, R = 24,0
    kep, kozep = _kep_a_kurzorral(ablak, qt_app, terulet)
    _ellenoriz(kep, kozep, _REF_INDULO_097, "induló állás (job-907 __12)", "097_indulo")

    sorrend = (
        (0.0, _REF_BAL_VEG, "bal vég (job-908 __14)", "097_bal_veg"),
        (0.242, _REF_24_2_SZAZALEK, "a futás 24,2%-án (job-917 __14)", "097_24_2"),
        (0.735, _REF_73_5_SZAZALEK, "a futás 73,5%-án (job-917 __20)", "097_73_5"),
        (1.0, _REF_JOBB_VEG_097, "jobb vég (job-908 __20)", "097_jobb_veg"),
    )
    for t, mert_ref, felirat, kimenet in sorrend:
        _csuszka_huzasa(ablak, qt_app, t)
        assert abs(csuszka.property("visualPosition") - t) <= 0.01, (felirat, csuszka.property("visualPosition"))
        kep, kozep = _kep_a_kurzorral(ablak, qt_app, terulet)
        _ellenoriz(kep, kozep, mert_ref, felirat, kimenet)


@pytest.mark.parametrize("kep_app", ["szines_768x512"], indirect=True)
def test_szines_kepen_107_nagyitasnal_a_gyuru_a_referenciakockakkal_egyezik(kep_app, qt_app):
    """job-918 __12 (induló), __18 (jobb vég), __24 (bal vég): a 768 x 512-es képen, z = 1,07."""
    ablak, _controller, _engine = kep_app
    nezo, terulet = _retusalas_megnyit(ablak, qt_app)
    # a referencián a kép 824 képpont széles: 824 / 768 = 1,0729 („Zoomed to 107%")
    zoom = _nagyitast_allit(qt_app, nezo, terulet, 1.0716)
    assert 1.065 <= zoom <= 1.075

    kep, kozep = _kep_a_kurzorral(ablak, qt_app, terulet)
    _ellenoriz(kep, kozep, _REF_INDULO_107, "induló állás (job-918 __12)", "107_indulo")
    for t, mert_ref, felirat, kimenet in (
        (1.0, _REF_JOBB_VEG_107, "jobb vég (job-918 __18)", "107_jobb_veg"),
        (0.0, _REF_BAL_VEG, "bal vég (job-918 __24)", "107_bal_veg"),
    ):
        _csuszka_huzasa(ablak, qt_app, t)
        kep, kozep = _kep_a_kurzorral(ablak, qt_app, terulet)
        _ellenoriz(kep, kozep, mert_ref, felirat, kimenet)


@pytest.mark.parametrize("kep_app", ["szines_1024x1024"], indirect=True)
def test_negyzetes_kepen_080_nagyitasnal_az_indulo_gyuru_a_job_314_mereteve_egyezik(kep_app, qt_app):
    """A job #314 képernyőképe: 1024 x 1024-es kép, 80%, induló állás, R = 20,0 (átmérő 40,0)."""
    ablak, _controller, _engine = kep_app
    nezo, terulet = _retusalas_megnyit(ablak, qt_app)
    zoom = _nagyitast_allit(qt_app, nezo, terulet, 0.80)
    assert 0.795 <= zoom <= 0.805
    kep, kozep = _kep_a_kurzorral(ablak, qt_app, terulet)
    _ellenoriz(kep, kozep, _REF_INDULO_080, "induló állás (job #314, 1024 x 1024)", "080_indulo")


@pytest.mark.parametrize("kep_app", ["szurke_1024x256"], indirect=True)
def test_a_gyuru_a_nagyitassal_aranyosan_no_es_a_kepernyokorbe_illeszkedik(kep_app, qt_app):
    """Az induló kör R-je a nagyítással arányos (R = 25 · z): z = 0,966 és z = 1,5-nél is."""
    ablak, _controller, _engine = kep_app
    nezo, terulet = _retusalas_megnyit(ablak, qt_app)
    for cel in (0.966, 1.5):
        zoom = _nagyitast_allit(qt_app, nezo, terulet, cel) if cel > 1 else float(terulet.property("viewZoom"))
        # a nagyított nézetben a kép kilóg a keretből: a gyűrűt a kép látható részére visszük
        kep, kozep = _kep_a_kurzorral(ablak, qt_app, terulet)
        _ellenoriz(kep, kozep, 2 * 25.0 * zoom, f"induló kör z = {zoom:.3f}-nél", f"aranyos_{cel}")
