"""A Retusálás panel, a visszavonás-megerősítő és a megerősített visszavonás utáni panel
renderelt próbája (#7379, #7391).

Referencia: az eredeti Picasa felvétele (job-838 `__10`, `__36`; job-907 `__24`). A
képfájlok az eredeti program grafikáját tartalmazzák, ezért NEM kerülnek a
repóba: a teszt a róluk MÉRT számokat tartalmazza (`_REF_*`), a mi oldalunkon
pedig a valódi, offscreen renderelt képkockából mér (`grabWindow`).

Mi LÁTÁS és mi csak SZÁMOLÁS:
- látás (képpontmérés a renderelt képkockán): a cím tintájának helye, a gombok
  szövegének sötétsége (engedélyezett vs tiltott), a megerősítő ablak gombjainak
  kitöltése, kerete és a „No" gomb pontozott fókuszkerete, az ablak alatti háttér
  változatlansága, a bal panel Undo/Redo gombjainak szövege a megerősített
  visszavonás után;
- számolás (tulajdonság-olvasás): az ablak címe, ikontípusa, gombfeliratai,
  a jelölő és a Cancel hiánya, a fókusz, a gombok engedélyezettsége.

⚠️ Az ECSETMÉRET (csúszka alapállása, az ecsetkör átmérője) itt NEM szerepel: az
eredeti leképezése nincs lezárva (7327-11, külön jegy 7327-11c/11d), ezért a
#7379 nem módosítja, és nem is állítja.

MÉRT, de NEM állított eltérések az eredetitől (a teszt ezeket nem védi, nyitott
kérdések; a mért értékek a `PICASAPY_7379_KIMENET` naplóból olvashatók):
- a panel: a #7386 után az eszköz-fülsáv a Retusálás panel fölött is látszik,
  a panel tartalma a sáv alatt kezdődik; a „Brush Size" felirat balra igazított
  (az eredetin a csúszka fölé középre); az útmutató betűje kisebb (4 sor az
  eredeti 5-jével szemben); a tiltott gombok szövege sötétebb;
- a megerősítő ablak: 332 x 113 képpont (az eredeti 347 x 108, a rendszer
  címsorával együtt); nálunk nincs rendszer-címsor (a cím az ablak törzsében áll),
  az ablak háttere sötétebb szürke (az eredetin 245), az ikon más rajzolat, a betű
  más; a gombok és a „No" fókusza a mért alakot követik (lásd az állításokat).

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
# __10: a gombok szövegzónájának legsötétebb szürkéje: tiltott 184-185, engedélyezett (Cancel) 46.
_REF_TILTOTT_SZOVEG_MIN = 184
_REF_ENGEDELYEZETT_SZOVEG_MIN = 46
# __36: a megerősítő ablak (467..813, 456..563), azaz 347 x 108 (címsorral együtt).
_REF_PARBESZED = (347, 108)
# __36: a két gomb külső mérete (a keretekkel) 75 x 21, belül 73 x 19 (Undo: x 650-724, No: x 729-803,
# y 533-553); a keret 1 képpont: Undo szürke (174), No kék (48, 150, 250); a belső fehér (255).
_REF_GOMB = (75, 21)
# __36: a „No" pontozott fókuszkerete a külső széltől 3 képponttal beljebb fut (x 732-800, y 536-550),
# minden második képpont fekete: a felső sorban 35 festett képpont.
_REF_FOKUSZKERET_BEHUZAS = 3
_REF_FOKUSZKERET_FELSO_PONTOK = 35
# job-907 __24: a megerősített visszavonás után a bal panel Undo és Redo gombja is tiltott,
# a szövegzónájuk legsötétebb szürkéje mindkettőn 185.
_REF_TILTOTT_UNDO_REDO_SZOVEG_MIN = 185

_NYUGODT_PONT = QPoint(1280, 1010)  # a jobb alsó sarok: semmilyen vezérlő fölött nincs
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


#: A képkocka-összevetésből kivett, saját ütemben mozgó elemek: az állapotsor háttérmunka-hulláma
#: (`busySweep`, időzítésfüggő) és a PicasaPy saját lánc-nézete (`viewerEffectSliceBox`, 0 lépéses
#: láncnál, azaz egy visszavonás után folyamatosan forog). Egyik sem az Undo/Redo vagy a megerősítő
#: része; a rajzolás idejére átlátszatlanságuk 0.
_MOZGO_ELEMEK = ("busySweep", "viewerEffectSliceBox")


def _kep(ablak) -> QImage:
    """Képkocka a saját ütemben mozgó elemek (`_MOZGO_ELEMEK`) elrejtésével."""
    elrejtett = []
    for nev in _MOZGO_ELEMEK:
        elem = ablak.findChild(QObject, nev)
        if isinstance(elem, QQuickItem):
            elrejtett.append((elem, elem.opacity()))
            elem.setOpacity(0.0)
    try:
        kep = ablak.grabWindow()
    finally:
        for elem, regi_atlatszosag in elrejtett:
            elem.setOpacity(regi_atlatszosag)
    assert not kep.isNull(), "a főablakról nem készült képkocka"
    return kep


def _nyugodt_kep(ablak, qt_app) -> QImage:
    """Megvárja, hogy két, 200 ms-ra követő képkocka azonos legyen (a késve frissülő, pl. láncinfó-doboz
    nem hamisítja a háttér-összevetést), és az utolsót adja vissza."""
    # mentés (Undo, Apply) után a háttérben bélyegkép-frissítés fut, ami a képkockát változtatja;
    # a hullám jelzője (`busySweep`) addig látszik, amíg a vezérlő dolgozik
    hullam = ablak.findChild(QObject, "busySweep")
    if isinstance(hullam, QQuickItem):
        assert _var(qt_app, lambda: not hullam.property("visible"), 60.0), "a háttérmunka nem fejeződött be"
    allapot = {"regi": _kep(ablak), "elozo": _kep(ablak), "elteres": "nincs"}

    def stabil() -> bool:
        QTest.qWait(200)
        mostani = _kep(ablak)
        kulonbseg = np.abs(_szurke(allapot["elozo"]) - _szurke(mostani))
        ys, xs = np.nonzero(kulonbseg)
        allapot["elteres"] = (
            f"{xs.size} képpont, x {xs.min()}-{xs.max()}, y {ys.min()}-{ys.max()}" if xs.size else "nincs"
        )
        allapot["regi"], allapot["elozo"] = allapot["elozo"], mostani
        return xs.size == 0

    if not _var(qt_app, stabil, 40.0):
        # kézi vizsgálathoz a két utolsó képkocka kimentődik (csak ha a kimeneti mappa meg van adva)
        _ment(allapot["regi"], "nem_nyugodt_regi")
        _ment(allapot["elozo"], "nem_nyugodt_uj")
        raise AssertionError(f"a képkocka nem nyugodott meg; az utolsó eltérés: {allapot['elteres']}")
    return allapot["elozo"]


def _kattint(ablak, elem: QQuickItem) -> None:
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, pos=QPoint(round(kozep.x()), round(kozep.y())))


def _nezo_megnyit(ablak, qt_app) -> None:
    """Beállítja a referencia nagyságú ablakot, és megnyitja a nézőt az első képpel."""
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


def _megnyit(
    ablak,
    qt_app,
    csempe_nev: str = "editToolRetouch",
    jelzo: str = "retouchActive",
    cim_nev: str = "retouchTitle",
) -> QQuickItem:
    """Megnyitja a nézőt és az eszközt (alapból a Retusálást)."""
    _nezo_megnyit(ablak, qt_app)
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


def _eltér_a_hatterol(szurke: np.ndarray, hatter: int) -> np.ndarray:
    return np.abs(szurke - hatter) > 12


def _gomb_alakja_a_kepen(kep: QImage, elem: QQuickItem, *, fokuszos: bool) -> None:
    """A megerősítő gombját a renderelt képkockán méri: külső méret, keret, kitöltés, pontozott keret.

    Referencia: job-838 `__36` (lásd a `_REF_GOMB`, `_REF_FOKUSZKERET_*` állandókat). A keret szürke
    és kék SZÍNE nálunk a téma tokenjeiből jön (nem azonos az eredeti pontos értékével), ezért a
    színt csak a jellegére állítjuk (semleges szürke, illetve kék); a pontos különbség a naplóba megy.
    """
    bal, felso, jobb, also = _teglalap(elem)
    nev = elem.property("objectName")
    rgb = _kepadat(kep)[:, :, :3].astype(int)
    szurke = _szurke(kep)
    hatter = int(szurke[felso - 6, bal + 20])  # a párbeszéd törzse a gomb fölött

    # külső méret a KÉPPONTOKBÓL: a szegély az első/utolsó, a háttértől eltérő képpont
    sor = _eltér_a_hatterol(szurke[felso + 10, bal - 3 : bal + 7], hatter)
    bal_el = bal - 3 + int(np.argmax(sor))
    sor = _eltér_a_hatterol(szurke[felso + 10, jobb - 7 : jobb + 3], hatter)
    jobb_el = jobb - 7 + int(len(sor) - 1 - np.argmax(sor[::-1]))
    oszl = _eltér_a_hatterol(szurke[felso - 3 : felso + 7, bal + 8], hatter)
    felso_el = felso - 3 + int(np.argmax(oszl))
    oszl = _eltér_a_hatterol(szurke[also - 7 : also + 3, bal + 8], hatter)
    also_el = also - 7 + int(len(oszl) - 1 - np.argmax(oszl[::-1]))
    meret = (jobb_el - bal_el + 1, also_el - felso_el + 1)
    _jegyez(f"{nev}_kulso_meret_kepponton (eredeti {_REF_GOMB[0]} x {_REF_GOMB[1]})", meret)
    assert meret == _REF_GOMB, f"a(z) {nev} gomb külső mérete {meret}, eredeti: {_REF_GOMB}"

    # kitöltés: a szegély és a pontozott keret között, a felirattól távol, fehér (az eredetin 255)
    belso = rgb[felso + 8 : felso + 13, bal + 6 : bal + 11]
    _jegyez(f"{nev}_kitoltes_min (eredeti 255)", int(belso.min()))
    assert int(belso.min()) >= 250, f"a(z) {nev} gomb kitöltése nem fehér: min {int(belso.min())}"

    # szegély: a bal él közepe. Undo semleges szürke (eredeti 174), a fókuszos No kék (48, 150, 250)
    el = tuple(int(c) for c in rgb[felso + 10, bal_el])
    _jegyez(f"{nev}_szegely_szine (eredeti Undo (174,174,174), No (48,150,250))", el)
    if fokuszos:
        assert el[2] >= 200 and el[0] <= 80, f"a fókuszos gomb szegélye nem kék: {el}"
    else:
        assert max(el) - min(el) <= 8 and 140 <= el[0] <= 205, f"a gomb szegélye nem semleges szürke: {el}"

    # pontozott fókuszkeret: a külső széltől 3 képponttal beljebb, minden második képpont fekete
    sorszam = felso_el + _REF_FOKUSZKERET_BEHUZAS
    pontok = szurke[sorszam, bal_el + _REF_FOKUSZKERET_BEHUZAS : jobb_el - _REF_FOKUSZKERET_BEHUZAS + 1]
    sotet = int((pontok < 90).sum())
    _jegyez(
        f"{nev}_pontozott_keret_felso_sor_festett_kepponttal (eredeti {_REF_FOKUSZKERET_FELSO_PONTOK} a No-n, 0 az Undo-n)",
        sotet,
    )
    if fokuszos:
        assert sotet == _REF_FOKUSZKERET_FELSO_PONTOK, (
            f"a fókuszos gomb pontozott keretének felső sorában {sotet} festett képpont van, "
            f"eredeti: {_REF_FOKUSZKERET_FELSO_PONTOK}"
        )
        # a festett képpontok között fehér áll (nem tömör vonal)
        kozok = pontok[1::2]
        assert int(kozok.min()) >= 240, "a pontozott keret képpontjai között nem fehér a rés"
    else:
        assert sotet == 0, "a nem fókuszos gombon nem lehet pontozott keret"


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
    QTest.mouseMove(ablak, _NYUGODT_PONT)
    elotte = _nyugodt_kep(ablak, qt_app)
    _kattint(ablak, visszavonas)
    parbeszed = ablak.findChild(QObject, "undoDataLossDialog")
    assert parbeszed is not None
    assert _var(qt_app, lambda: parbeszed.property("visible") is True and parbeszed.property("opened") is True)
    QTest.mouseMove(ablak, _NYUGODT_PONT)
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
    # a két gomb egymás mellett áll, az Undo balra, a No jobbra, a jobb szélhez igazítva
    igen_t, nem_t = _teglalap(igen), _teglalap(nem)
    assert igen_t[2] <= nem_t[0] + 1 and abs(igen_t[1] - nem_t[1]) <= 1
    assert nem_t[2] <= jobb and igen_t[0] >= bal
    # az eredetin a két gomb szegélye között 4 képpont a rés (Undo x 724, No x 729)
    assert nem_t[0] - igen_t[2] == 4, f"a gombok közti rés {nem_t[0] - igen_t[2]} px, eredeti: 4"
    _gomb_alakja_a_kepen(utana, igen, fokuszos=False)
    _gomb_alakja_a_kepen(utana, nem, fokuszos=True)

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


# --- #7391: a megerősített retusálás-visszavonás utáni bal panel -----------------------------


def _szoveg_min(szurke: np.ndarray, elem: QQuickItem) -> int:
    """A gomb szövegzónájának legsötétebb szürkéje (a szegélysoroktól távol)."""
    bal, felso, jobb, also = _teglalap(elem)
    return int(szurke[felso + 3 : also - 3, bal + 25 : jobb - 25].min())


def _bezarodik(qt_app, parbeszed) -> None:
    assert _var(qt_app, lambda: parbeszed.property("visible") is False)


def test_megerositett_visszavonas_utan_az_undo_es_a_redo_tiltott_csupasz_felirattal(atmenetes_app, qt_app):
    """#7391 (1) és (3): a megerősített „Undo" után a bal panel Undo és Redo gombja tiltott, a felirat
    csupasz; a gombok szövegének halványsága a `job-907 __24` mért értékével vethető össze."""
    ablak, _controller, _engine = atmenetes_app
    parbeszed, _elotte = _megerosito_megnyitasa(ablak, qt_app)
    undo = _elem(ablak, "editUndoButton")
    redo = _elem(ablak, "editRedoButton")
    assert undo.property("enabled") is True
    assert redo.property("enabled") is False, "a retusálás Apply után az Újra még tiltott"

    _kattint(ablak, _elem(ablak, "undoDataLossYesButton"))
    _bezarodik(qt_app, parbeszed)
    assert _var(qt_app, lambda: undo.property("enabled") is False), "az Undo gomb tiltott marad"
    assert redo.property("enabled") is False, "az Újra gomb a megerősített visszavonás után is tiltott"
    assert undo.property("label") == "Undo"
    assert redo.property("label") == "Redo", "az Újra felirata csupasz: nincs „Redo Retouches”"

    QTest.mouseMove(ablak, _NYUGODT_PONT)
    kep = _nyugodt_kep(ablak, qt_app)
    _ment(kep, "retus_visszavonas_utan")
    szurke = _szurke(kep)
    undo_min, redo_min = _szoveg_min(szurke, undo), _szoveg_min(szurke, redo)
    _jegyez(
        f"undo_redo_szoveg_min_szurke tiltva (eredeti mindkettő {_REF_TILTOTT_UNDO_REDO_SZOVEG_MIN})",
        f"Undo {undo_min}, Redo {redo_min}",
    )
    # Mindkét gomb a tiltott sávban van: a szövegük a retusálás-panel tiltott gombjaiéval azonos
    # halványságú (119-121, lásd fent), és látványosan halványabb az engedélyezett gombénál (68). A
    # két felirat betűformája eltér (Undo, Redo), ezért a legsötétebb képpontjuk néhány árnyalattal
    # különbözhet; az eredetin mindkettő 185 (nálunk a tiltott szöveg sötétebb: mért eltérés).
    assert min(undo_min, redo_min) >= 100, f"a tiltott gombok szövege nem halvány: Undo {undo_min}, Redo {redo_min}"
    assert abs(undo_min - redo_min) <= 25, f"Undo {undo_min}, Redo {redo_min}: nem azonosan tiltottak"


def test_megerosito_no_gombja_utan_a_kep_es_a_gombok_az_undo_elottiek(atmenetes_app, qt_app):
    """#7391 (2): a „No" után a teljes képkocka képpontra azonos a visszavonás kérése előttivel."""
    ablak, _controller, engine = atmenetes_app
    parbeszed, elotte = _megerosito_megnyitasa(ablak, qt_app)
    undo = _elem(ablak, "editUndoButton")
    redo = _elem(ablak, "editRedoButton")
    cimke_elotte = (undo.property("label"), redo.property("label"))

    _kattint(ablak, _elem(ablak, "undoDataLossNoButton"))
    _bezarodik(qt_app, parbeszed)
    QTest.mouseMove(ablak, _NYUGODT_PONT)
    utana = _nyugodt_kep(ablak, qt_app)

    assert (undo.property("label"), redo.property("label")) == cimke_elotte
    assert undo.property("enabled") is True and redo.property("enabled") is False
    _ment(elotte, "no_elotte")
    _ment(utana, "no_utana")
    kulonbseg = np.abs(_szurke(elotte) - _szurke(utana))
    ys, xs = np.nonzero(kulonbseg)
    _jegyez(
        "no_utan_kulonbozo_kepponotok / legnagyobb elteres / tartomany",
        f"{int((kulonbseg > 0).sum())} / {int(kulonbseg.max())} / "
        + (f"x {xs.min()}-{xs.max()}, y {ys.min()}-{ys.max()}" if xs.size else "nincs"),
    )
    # MÉRVE: a párbeszéd helyén egyetlen oszlopban 1 szürkeárnyalatnyi eltérés marad (a ramp-kép
    # kvantálása a részleges újrafestésnél, nem állapotváltozás); minden ennél nagyobb eltérés hiba.
    assert int(kulonbseg.max()) <= 1, (
        "a „No” után a képkocka eltér a visszavonás kérése előttitől: "
        f"{int((kulonbseg > 0).sum())} képpont, legnagyobb eltérés {int(kulonbseg.max())}, "
        f"x {xs.min()}-{xs.max()}, y {ys.min()}-{ys.max()}"
    )
    assert int((kulonbseg > 0).sum()) <= 200, "az 1 szürkeárnyalatos eltérés nem lehet nagy területű"
    assert _vissza_akcio(engine) == "retouch"


def test_crop_visszavonasa_utan_a_redo_aktiv_marad_a_panelen(atmenetes_app, qt_app):
    """#7391 (4): más művelet (Crop) visszavonása után az Újra gomb aktív, nem csupasz felirattal."""
    ablak, _controller, engine = atmenetes_app
    _megnyit(ablak, qt_app)
    _kattint(ablak, _elem(ablak, "retouchCancelButton"))
    panel = _elem(ablak, "viewerEditorPanel")
    assert _var(qt_app, lambda: panel.property("retouchActive") is False)

    szerkeszto = engine.rootContext().contextProperty("editController")
    szerkeszto.applyCrop(0.1, 0.1, 0.5, 0.5)
    undo = _elem(ablak, "editUndoButton")
    redo = _elem(ablak, "editRedoButton")
    assert _var(qt_app, lambda: undo.isVisible() and undo.property("enabled") is True)
    assert redo.property("enabled") is False

    _kattint(ablak, undo)
    assert _var(qt_app, lambda: redo.property("enabled") is True), "a Crop Undo-ja után az Újra aktív"
    assert redo.property("label") != "Redo", "az Újra felirata nevezi a lépést"
    assert str(redo.property("label")).startswith("Redo")
    QTest.mouseMove(ablak, _NYUGODT_PONT)
    _ment(_nyugodt_kep(ablak, qt_app), "crop_visszavonas_utan")
