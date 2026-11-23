"""A Retusálás panel és a visszavonás-megerősítő renderelt próbája (#7379).

Referencia: az eredeti Picasa felvétele (job-838 `__10`, `__12`, `__36`). A
képfájlok az eredeti program grafikáját tartalmazzák, ezért NEM kerülnek a
repóba: a teszt a róluk MÉRT számokat tartalmazza (`_REF_*`), a mi oldalunkon
pedig a valódi, offscreen renderelt képkockából mér (`grabWindow`).

Mi LÁTÁS és mi csak SZÁMOLÁS:
- látás (képpontmérés a renderelt képkockán): a cím tintájának helye, a
  csúszka fogantyújának helye, a gombok szövegének sötétsége (engedélyezett vs
  tiltott), az ecsetkör külső átmérője (a kurzorral és anélkül készült kép
  különbségéből), a megerősítő ablak mérete és az alatta lévő háttér változatlansága;
- számolás (tulajdonság-olvasás): az ablak címe, ikontípusa, gombfeliratai,
  a jelölő és a Cancel hiánya, a fókusz, a csúszka értéke.
A gyűrű KINÉZETÉT (szín, vastagság) ez a teszt nem méri, csak az átmérőt.

MÉRT, de NEM állított eltérések az eredetitől (a teszt ezeket nem védi, nyitott
kérdések; a mért értékek a `PICASAPY_7379_KIMENET` naplóból olvashatók):
- a panel: eszköz-módban a fülsáv nálunk rejtett (az eredetin látszik, halványan),
  ezért a cím függőlegesen feljebb áll; a „Brush Size" felirat balra igazított
  (az eredetin a csúszka fölé középre); az útmutató betűje kisebb (4 sor az
  eredeti 5-jével szemben); a tiltott gombok szövege sötétebb;
- a megerősítő ablak: 332 x 121 képpont (az eredeti 347 x 108, a rendszer
  címsorával együtt); nálunk nincs rendszer-címsor, az „Undo" gomb zöld 51 x 29
  (az eredetin fehér 74 x 19), a „No" 37 x 29 (az eredetin 73 x 19), a „No"
  fókuszát nem jelzi pontozott keret, az ikon más rajzolat;
- az ecsetkör gyűrűje: nálunk 2 képpontos fekete külső és 1 képpontos fehér belső
  vonal, az eredetin vékony világos külső és vékony sötét belső vonal.

Ha a `PICASAPY_7379_KIMENET` környezeti változó egy mappa, a képkockák oda is
kimentődnek (kézi szemrevételezéshez); ezt a normál futás nem használja.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre

# --- az eredeti Picasa mért adatai (job-838) -------------------------------
# __10: a bal panel. A cím tintája x 75-203 (közép 139,0; szélesség 129).
_REF_CIM_KOZEP_X = 139.0
_REF_CIM_SZELESSEG = 129
# __10: a csúszka sávja x 74-193 (közép 133,5), a fogantyú oszlopai x 133-140
# (közép 136,5): a fogantyú 3,0 képponttal a sáv közepétől jobbra áll.
_REF_FOGANTYU_ELTOLAS = 3.0
# __10: a gombok szövegzónájának legsötétebb szürkéje: tiltott 184-185, engedélyezett (Cancel) 46.
_REF_TILTOTT_SZOVEG_MIN = 184
_REF_ENGEDELYEZETT_SZOVEG_MIN = 46
# __12: a megjelenített kép 987 x 247 képpont, az alapállású ecsetkör külső átmérője 50.
_REF_KEP = (987, 247)
_REF_GYURU_ATMERO = 50
# __36: a megerősítő ablak (467..813, 456..563), azaz 347 x 108 (címsorral együtt).
_REF_PARBESZED = (347, 108)

_ABLAK = (1295, 1024)  # ezen a szélességen a kép pontosan 987 x 246,75 képpont
_KIMENET_VALTOZO = "PICASAPY_7379_KIMENET"


def _szurke_atmenet(lib: Path) -> None:
    """A referencia `gray_ramp.jpg` mása: 1024 x 256, fekete-fehér vízszintes átmenet."""
    kep = QImage(1024, 256, QImage.Format.Format_RGB32)
    festo = QPainter(kep)
    atmenet = QLinearGradient(0, 0, 1024, 0)
    atmenet.setColorAt(0.0, QColor(0, 0, 0))
    atmenet.setColorAt(1.0, QColor(255, 255, 255))
    festo.fillRect(0, 0, 1024, 256, atmenet)
    festo.end()
    assert kep.save(str(lib / "gray_ramp.jpg"), "JPG", 95)


@pytest.fixture
def atmenetes_app(rogzitett_betu, qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_szurke_atmenet,
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


def _jegyez(nev: str, ertek) -> None:
    """A mért érték a kimeneti mappa `meres.txt` fájljába kerül (csak ha a mappa meg van adva)."""
    mappa = os.environ.get(_KIMENET_VALTOZO)
    if not mappa:
        return
    cel = Path(mappa)
    cel.mkdir(parents=True, exist_ok=True)
    with (cel / "meres.txt").open("a", encoding="utf-8") as fajl:
        fajl.write(f"{nev}: {ertek}\n")


def _kepadat(kep: QImage) -> np.ndarray:
    rgba = kep.convertToFormat(QImage.Format.Format_RGBA8888)
    adat = np.frombuffer(rgba.constBits(), dtype=np.uint8)
    return adat.reshape(rgba.height(), rgba.bytesPerLine())[:, : rgba.width() * 4].reshape(
        rgba.height(), rgba.width(), 4
    ).copy()


def _szurke(kep: QImage) -> np.ndarray:
    rgb = _kepadat(kep)[:, :, :3].astype(int)
    return (rgb[:, :, 0] * 299 + rgb[:, :, 1] * 587 + rgb[:, :, 2] * 114) // 1000


def _teglalap(elem: QQuickItem) -> tuple[int, int, int, int]:
    bal_felso = elem.mapToScene(QPointF(0, 0))
    bal, felso = round(bal_felso.x()), round(bal_felso.y())
    return bal, felso, bal + round(elem.width()), felso + round(elem.height())


def _kep(ablak) -> QImage:
    """Képkocka az állapotsor háttérmunka-hullámának (`busySweep`, időzítésfüggő) elrejtésével."""
    hullam = ablak.findChild(QObject, "busySweep")
    hullam = hullam if isinstance(hullam, QQuickItem) else None
    regi_atlatszosag = hullam.opacity() if hullam is not None else None
    if hullam is not None:
        hullam.setOpacity(0.0)
    try:
        kep = ablak.grabWindow()
    finally:
        if hullam is not None:
            hullam.setOpacity(regi_atlatszosag)
    assert not kep.isNull(), "a főablakról nem készült képkocka"
    return kep


def _nyugodt_kep(ablak, qt_app) -> QImage:
    """Megvárja, hogy két, 200 ms-ra követő képkocka azonos legyen (a késve frissülő, pl. láncinfó-doboz
    nem hamisítja a háttér-összevetést), és az utolsót adja vissza."""
    allapot = {"elozo": _kep(ablak)}

    def stabil() -> bool:
        QTest.qWait(200)
        mostani = _kep(ablak)
        egyezik = np.array_equal(_kepadat(allapot["elozo"]), _kepadat(mostani))
        allapot["elozo"] = mostani
        return egyezik

    assert _var(qt_app, stabil, 20.0), "a képkocka nem nyugodott meg"
    return allapot["elozo"]


def _kattint(ablak, elem: QQuickItem) -> None:
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, pos=QPoint(round(kozep.x()), round(kozep.y())))


def _megnyit(
    ablak,
    qt_app,
    csempe_nev: str = "editToolRetouch",
    jelzo: str = "retouchActive",
    cim_nev: str = "retouchTitle",
) -> QQuickItem:
    """Beállítja a referencia nagyságú ablakot, megnyitja a nézőt és az eszközt (alapból a Retusálást)."""
    szelesseg, magassag = _ABLAK
    ablak.setWidth(szelesseg)
    ablak.setHeight(magassag)
    assert _var(qt_app, lambda: ablak.width() == szelesseg and ablak.height() == magassag)
    ablak.setProperty("viewerOpen", True)
    nezo = ablak.findChild(QObject, "photoViewer")
    assert nezo is not None
    nezo.setProperty("currentIndex", 0)
    kep = _elem(ablak, "viewerImage")
    assert _var(qt_app, lambda: kep.property("visible") and kep.property("paintedWidth") > 0)
    csempe = _elem(ablak, csempe_nev)
    assert _var(qt_app, lambda: csempe.isVisible() and csempe.width() > 0)
    _kattint(ablak, csempe)
    panel = _elem(ablak, "viewerEditorPanel")
    assert _var(qt_app, lambda: panel.property(jelzo) is True)
    cim = _elem(ablak, cim_nev)
    assert _var(qt_app, lambda: cim.isVisible() and cim.width() > 0)
    qt_app.processEvents()
    _ment(_kep(ablak), "retus_panel_megnyitva")
    return panel


def test_retusalas_panel_cime_es_felepitese(atmenetes_app, qt_app):
    """Cím: „Retouch blemishes", középre igazítva, ikon és „Regions selected" sor nélkül."""
    ablak, _controller, _engine = atmenetes_app
    _megnyit(ablak, qt_app)

    cim = _elem(ablak, "retouchTitle")
    assert cim.property("text") == "Retouch blemishes"
    assert ablak.findChild(QObject, "retouchRegionCountLabel") is None
    oszlop = _elem(ablak, "retouchColumn")
    for gyerek in oszlop.childItems():
        assert gyerek.metaObject().className() != "QQuickImage", "a panel címe mellett nem lehet ikon"

    kep = _kep(ablak)
    assert not kep.isNull()
    _ment(kep, "retus_panel")
    bal, felso, jobb, also = _teglalap(cim)
    szurke = _szurke(kep)[felso:also, bal:jobb]
    hatter = int(np.bincount(szurke.ravel()).argmax())
    oszlopok = np.nonzero((np.abs(szurke - hatter) > 45).any(axis=0))[0]
    assert oszlopok.size > 0, "a cím tintája nem látszik a képkockán"
    kozep = bal + (oszlopok.min() + oszlopok.max()) / 2
    szelesseg = int(oszlopok.max() - oszlopok.min() + 1)
    _jegyez("cim_kozep_x (eredeti 139.0)", kozep)
    _jegyez("cim_szelesseg (eredeti 129)", szelesseg)
    # A betűkészlet és a méret eltér az eredetitől: a középpont ±4, a szélesség ±12 képpont.
    assert abs(kozep - _REF_CIM_KOZEP_X) <= 4, f"a cím közepe x={kozep}, mért eredeti: {_REF_CIM_KOZEP_X}"
    assert abs(szelesseg - _REF_CIM_SZELESSEG) <= 12, f"a cím tintája {szelesseg} px, eredeti: {_REF_CIM_SZELESSEG}"


def test_retusalas_panel_csuszka_alapallasa_kozepen_van(atmenetes_app, qt_app):
    ablak, _controller, _engine = atmenetes_app
    _megnyit(ablak, qt_app)
    csuszka = _elem(ablak, "retouchBrushSizeSlider")
    assert csuszka.property("value") == 50

    kep = _kep(ablak)
    bal, felso, jobb, also = _teglalap(csuszka)
    szurke = _szurke(kep)[felso:also, bal - 10 : jobb + 10]
    hatter = int(np.bincount(szurke.ravel()).argmax())
    tinta = np.abs(szurke - hatter) > 20
    # a vízszintes sín soraiban a tinta a szélesség nagy részén fut; a fogantyú a többi sorban áll
    sin_sorok = tinta.sum(axis=1) > 0.6 * tinta.shape[1]
    assert sin_sorok.any() and (~sin_sorok & tinta.any(axis=1)).any(), "a csúszka sínje vagy fogantyúja nem látszik"
    sin_oszlopok = np.nonzero(tinta[sin_sorok].any(axis=0))[0]
    fogantyu_oszlopok = np.nonzero(tinta[~sin_sorok].any(axis=0))[0]
    sav_kozep = (sin_oszlopok.min() + sin_oszlopok.max()) / 2
    fogantyu_kozep = (fogantyu_oszlopok.min() + fogantyu_oszlopok.max()) / 2
    eltolas = fogantyu_kozep - sav_kozep
    sav_szelesseg = int(sin_oszlopok.max() - sin_oszlopok.min() + 1)
    _jegyez("csuszka_fogantyu_eltolas (eredeti +3.0)", eltolas)
    _jegyez("csuszka_sav_szelesseg (eredeti 120)", sav_szelesseg)
    # Az eredetin a fogantyú +3,0 képponttal áll a sáv közepétől (119 px-es sávon); nálunk 1..100 között
    # az 50 értéknél a közép körül. A teszt azt állítja, hogy a fogantyú a sáv középső tizedében áll.
    assert abs(eltolas) <= 0.1 * sav_szelesseg, (
        f"a fogantyú eltolása a sáv közepétől {eltolas:.1f} px ({sav_szelesseg} px-es sávon), "
        f"eredeti: +{_REF_FOGANTYU_ELTOLAS} (119 px-es sávon)"
    )


def test_retusalas_panel_gombjainak_allapota_es_sotetsege(atmenetes_app, qt_app):
    """Üres pufferrel: Reset, Undo Patch, Redo Patch, Apply tiltott, Cancel engedélyezett.

    Az eredetin a tiltott gombok szövege nagyon halvány (min szürke 184-185), az engedélyezetté sötét (46).
    Nálunk a tiltott gombok szövege sötétebb (a különbség mért, lásd a hibaüzenetet); a teszt azt állítja,
    hogy az engedélyezett szövege LÁTHATÓAN sötétebb, mint a tiltotté (legalább 30 szürkeárnyalat).
    """
    ablak, _controller, _engine = atmenetes_app
    _megnyit(ablak, qt_app)
    szurke = _szurke(_kep(ablak))

    def szoveg_min(nev: str) -> int:
        gomb = _elem(ablak, nev)
        bal, felso, jobb, also = _teglalap(gomb)
        return int(szurke[felso:also, bal + 25 : jobb - 25].min())

    tiltottak = ("retouchResetButton", "retouchUndoPatchButton", "retouchRedoPatchButton", "retouchApplyButton")
    for nev in tiltottak:
        assert _elem(ablak, nev).property("enabled") is False, nev
    assert _elem(ablak, "retouchCancelButton").property("enabled") is True
    cancel = szoveg_min("retouchCancelButton")
    for nev in (*tiltottak, "retouchCancelButton"):
        _jegyez(f"gomb_szoveg_min_szurke {nev} (eredeti tiltott 184-185, Cancel 46)", szoveg_min(nev))
    legsotetebb_tiltott = min(szoveg_min(nev) for nev in tiltottak)
    assert cancel + 30 <= legsotetebb_tiltott, (
        f"az engedélyezett Cancel szövege (min szürke {cancel}) nem látványosan sötétebb a tiltottakénál "
        f"({ {nev: szoveg_min(nev) for nev in tiltottak} }); eredeti: {_REF_ENGEDELYEZETT_SZOVEG_MIN} "
        f"engedélyezett, {_REF_TILTOTT_SZOVEG_MIN} tiltott"
    )


def test_alapallasu_ecsetkor_atmeroje_50_kepont_a_987_szeles_kepen(atmenetes_app, qt_app):
    ablak, _controller, _engine = atmenetes_app
    _megnyit(ablak, qt_app)
    kep = _elem(ablak, "viewerImage")
    terulet = _elem(ablak, "retouchClickArea")
    assert abs(terulet.width() - _REF_KEP[0]) <= 1 and abs(terulet.height() - _REF_KEP[1]) <= 1, (
        f"a megjelenített kép {terulet.width()} x {terulet.height()}, eredeti: {_REF_KEP}"
    )
    assert kep.property("paintedWidth") > 0

    # kurzor nélküli alapkép: az egér a képterületen kívül áll
    QTest.mouseMove(ablak, QPoint(5, 5))
    ecset = _elem(ablak, "retouchBrushCursor")
    assert _var(qt_app, lambda: not ecset.isVisible())
    alap = _kep(ablak)

    pont = terulet.mapToScene(QPointF(terulet.width() * 0.4, terulet.height() * 0.45))
    QTest.mouseMove(ablak, QPoint(round(pont.x()), round(pont.y())))
    assert _var(qt_app, lambda: ecset.isVisible() and terulet.property("containsMouse") is True)
    qt_app.processEvents()
    kurzoros = _kep(ablak)
    _ment(kurzoros, "retus_ecsetkor")

    kulonbseg = np.abs(_kepadat(alap)[:, :, :3].astype(int) - _kepadat(kurzoros)[:, :, :3].astype(int)).sum(axis=2)
    ys, xs = np.nonzero(kulonbseg > 30)
    assert xs.size > 0, "az ecsetkör nem látszik a képkockán"
    atmero_x = int(xs.max() - xs.min() + 1)
    atmero_y = int(ys.max() - ys.min() + 1)
    _jegyez("kep_merete (eredeti 987x247)", f"{terulet.width()} x {terulet.height()}")
    _jegyez("ecsetkor_kulso_atmero (eredeti 50)", f"{atmero_x} x {atmero_y}")
    assert abs(atmero_x - _REF_GYURU_ATMERO) <= 1 and abs(atmero_y - _REF_GYURU_ATMERO) <= 1, (
        f"az ecsetkör külső átmérője {atmero_x} x {atmero_y} px, eredeti: {_REF_GYURU_ATMERO}"
    )


# --- a visszavonás-megerősítő ablak ---------------------------------------


def _retusalast_alkalmaz(ablak, qt_app) -> None:
    """Valódi egérrel: cél, forrás, majd Apply; a panel bezárul, a lánc egy `retouch` lépést kap."""
    panel = _elem(ablak, "viewerEditorPanel")
    terulet = _elem(ablak, "retouchClickArea")
    cel = terulet.mapToScene(QPointF(terulet.width() * 0.30, terulet.height() * 0.45))
    forras = terulet.mapToScene(QPointF(terulet.width() * 0.65, terulet.height() * 0.55))
    QTest.mouseMove(ablak, QPoint(round(cel.x()), round(cel.y())))
    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, pos=QPoint(round(cel.x()), round(cel.y())))
    assert _var(qt_app, lambda: panel.property("retouchPatchPending") is True)
    QTest.mouseMove(ablak, QPoint(round(forras.x()), round(forras.y())))
    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, pos=QPoint(round(forras.x()), round(forras.y())))
    assert _var(qt_app, lambda: panel.property("retouchRegionCount") == 1)
    _kattint(ablak, _elem(ablak, "retouchApplyButton"))
    assert _var(qt_app, lambda: panel.property("retouchActive") is False)


def _parbeszed_teglalap(parbeszed) -> tuple[int, int, int, int]:
    """A megnyitott ablak látható téglalapja az ablak képpontjaiban (a háttérelem helye)."""
    hatter = parbeszed.property("background")
    assert isinstance(hatter, QQuickItem), "a párbeszéd háttéreleme nem érhető el"
    return _teglalap(hatter)


def _megerosito_megnyitasa(ablak, qt_app):
    """Retusálás alkalmazása után az „Undo Retouches" gombra kattint; visszaadja az ablakot."""
    _megnyit(ablak, qt_app)
    _retusalast_alkalmaz(ablak, qt_app)
    visszavonas = _elem(ablak, "editUndoButton")
    assert _var(qt_app, lambda: visszavonas.isVisible() and visszavonas.width() > 0)
    qt_app.processEvents()
    elotte = _nyugodt_kep(ablak, qt_app)
    _kattint(ablak, visszavonas)
    parbeszed = ablak.findChild(QObject, "undoDataLossDialog")
    assert parbeszed is not None
    assert _var(qt_app, lambda: parbeszed.property("visible") is True and parbeszed.property("opened") is True)
    qt_app.processEvents()
    return parbeszed, elotte


def test_retusalas_visszavonas_megerositoje_a_mert_alakot_adja(atmenetes_app, qt_app):
    ablak, _controller, _engine = atmenetes_app
    parbeszed, elotte = _megerosito_megnyitasa(ablak, qt_app)

    # --- számolás: a tulajdonságok ---
    assert parbeszed.property("title") == "Confirm"
    assert parbeszed.property("iconType") == "picasa"
    igen = _elem(ablak, "undoDataLossYesButton")
    nem = _elem(ablak, "undoDataLossNoButton")
    megse = _elem(ablak, "undoDataLossCancelButton")
    jelolo = _elem(ablak, "undoDataLossRememberCheck")
    assert igen.property("text") == "Undo"
    assert nem.property("text") == "No"
    assert not megse.isVisible(), "a retusálás megerősítőjén nincs Cancel"
    assert not jelolo.isVisible(), "a retusálás megerősítőjén nincs „Do not ask again” jelölő"
    assert nem.property("activeFocus") is True, "a fókusz a „No” gombon áll"
    uzenet = _elem(ablak, "undoDataLossMessageLabel")
    assert uzenet.property("text") == (
        "Retouch fixes cannot be recovered with redo.\nAre you sure you want to undo?"
    )

    # --- látás: a renderelt képkockán ---
    utana = _nyugodt_kep(ablak, qt_app)
    _ment(utana, "retus_megerosito")
    bal, felso, jobb, also = _parbeszed_teglalap(parbeszed)
    _jegyez("megerosito_ablak_merete (eredeti 347 x 108 a cimsorral)", f"{jobb - bal} x {also - felso}")
    _jegyez(
        "megerosito_ablak_kozepe (az ablak kozepe)",
        f"{(bal + jobb) / 2} , {(felso + also) / 2} ({ablak.width() / 2} , {ablak.height() / 2})",
    )
    for nev, elem in (("igen", igen), ("nem", nem)):
        gomb = _teglalap(elem)
        _jegyez(
            f"megerosito_gomb_{nev} (eredeti Undo 74 x 19, No 73 x 19)",
            f"{gomb[2] - gomb[0]} x {gomb[3] - gomb[1]}",
        )
    # a két gomb egymás mellett áll, az Undo balra, a No jobbra, a jobb szélhez igazítva
    igen_t, nem_t = _teglalap(igen), _teglalap(nem)
    assert igen_t[2] <= nem_t[0] + 1 and abs(igen_t[1] - nem_t[1]) <= 1
    assert nem_t[2] <= jobb and igen_t[0] >= bal

    # a háttér (a bal panel gombja és a kép) a párbeszéd alatt változatlan
    kulonbseg = np.abs(_szurke(elotte) - _szurke(utana))
    kulonbseg[max(0, felso - 4) : also + 4, max(0, bal - 4) : jobb + 4] = 0
    _jegyez(
        "hatter_valtozas_a_parbeszeden_kivul: kulonbozo kepponotok / legnagyobb elteres",
        f"{int((kulonbseg > 0).sum())} / {int(kulonbseg.max())}",
    )
    _ment(elotte, "retus_megerosito_elotte")
    ys, xs = np.nonzero(kulonbseg)
    assert int((kulonbseg > 0).sum()) == 0, (
        "a párbeszéd a háttér képpontjait is megváltoztatta; "
        f"x {xs.min()}-{xs.max()}, y {ys.min()}-{ys.max()}"
    )
    assert parbeszed.property("dim") is False


def _vissza_akcio(engine) -> str:
    return engine.rootContext().contextProperty("editController").property("undoAction")


def test_megerosito_nem_gombja_nem_von_vissza(atmenetes_app, qt_app):
    ablak, _controller, engine = atmenetes_app
    parbeszed, _elotte = _megerosito_megnyitasa(ablak, qt_app)
    assert _vissza_akcio(engine) == "retouch"

    _kattint(ablak, _elem(ablak, "undoDataLossNoButton"))
    assert _var(qt_app, lambda: parbeszed.property("visible") is False)
    assert _vissza_akcio(engine) == "retouch", "a „No” nem változtathat az állapoton"


def test_megerosito_undo_gombja_visszavon(atmenetes_app, qt_app):
    ablak, _controller, engine = atmenetes_app
    parbeszed, _elotte = _megerosito_megnyitasa(ablak, qt_app)
    assert _vissza_akcio(engine) == "retouch"

    _kattint(ablak, _elem(ablak, "undoDataLossYesButton"))
    assert _var(qt_app, lambda: parbeszed.property("visible") is False)
    assert _vissza_akcio(engine) != "retouch", "az „Undo” gomb visszavonja a retusálást"


def test_voroszem_visszavonas_megerositoje_valtozatlan(atmenetes_app, qt_app):
    """A Vörösszem ága ugyanazt a komponenst használja, de az eredeti Vörösszem-megerősítő alakja nincs
    mérve (7327-10), ezért a régi alak marad: „Undo" cím, Igen/Nem/Mégse, jelölő, halványított háttér.
    Ez a próba tulajdonságot olvas (számol), a Vörösszem ablak képét nem veti össze semmivel."""
    ablak, _controller, engine = atmenetes_app
    panel = _megnyit(ablak, qt_app, "editToolRedeye", "redeyeActive", "redeyeGuideText")
    szerkeszto = engine.rootContext().contextProperty("editController")
    szerkeszto.addRedeyeRegion(0.40, 0.40, 0.10, 0.10)
    alkalmaz = _elem(ablak, "redeyeApplyButton")
    assert _var(qt_app, lambda: alkalmaz.property("enabled") is True)
    _kattint(ablak, alkalmaz)
    assert _var(qt_app, lambda: panel.property("redeyeActive") is False)
    assert _vissza_akcio(engine) == "redeye"

    visszavonas = _elem(ablak, "editUndoButton")
    assert _var(qt_app, lambda: visszavonas.isVisible() and visszavonas.width() > 0)
    _kattint(ablak, visszavonas)
    parbeszed = ablak.findChild(QObject, "undoDataLossDialog")
    assert parbeszed is not None
    assert _var(qt_app, lambda: parbeszed.property("visible") is True and parbeszed.property("opened") is True)

    assert parbeszed.property("title") == "Undo"
    assert parbeszed.property("iconType") == "none"
    assert _elem(ablak, "undoDataLossYesButton").property("text") == "Yes"
    assert _elem(ablak, "undoDataLossNoButton").property("text") == "No"
    assert _elem(ablak, "undoDataLossCancelButton").isVisible()
    assert _elem(ablak, "undoDataLossRememberCheck").isVisible()
    assert parbeszed.property("dim") is True


def test_regi_elnyomas_nem_nemitja_el_a_retusalas_megerositojet(atmenetes_app, qt_app):
    """A korábbi felület „Do not ask again" jelölőjével elmentett `undo-retouch` elnyomás mellett
    is megnyílik az ablak (az eredetin nincs ilyen jelölő, tehát nincs mit elnyomni)."""
    ablak, _controller, engine = atmenetes_app
    engine.rootContext().contextProperty("confirmSettings").setSuppressed("undo-retouch", True)
    parbeszed, _elotte = _megerosito_megnyitasa(ablak, qt_app)
    assert parbeszed.property("visible") is True
    assert _vissza_akcio(engine) == "retouch", "megerősítés nélkül nem vonódhat vissza"
