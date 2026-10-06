"""#4420: a tiszta profil főmenü-parancsainak kattintásos bejárása."""

from __future__ import annotations


import re
import time
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.app import collage_output, movie_output
from support.jpeg_factory import make_jpeg


_MENUK = (
    ("View", "&View"),
    ("Folder", "F&older"),
    ("Picture", "&Picture"),
    ("Edit", "&Edit"),
    ("Tools", "&Tools"),
    ("Create", "&Create"),
    ("Help", "&Help"),
    ("File", "&File"),
)
_NINCS_LATHATO_HATAS = {
    "menuEditCut": (
        "Nincs látható változás: vágólap-művelet, a bejáró előtte/utána "
        "összeveti a vágólapot is."
    ),
    "menuEditCopy": (
        "Nincs látható változás: vágólap-művelet, a bejáró előtte/utána "
        "összeveti a vágólapot is."
    ),
    "menuEditCopyEffects": (
        "Nincs látható változás: hatáslista kerül a belső vágólapra, "
        "amit a felület nem jelenít meg."
    ),
    "menuEditCopyText": (
        "Nincs látható változás: feliratszöveg kerül a vágólapra; "
        "a mintaképen nincs feliratréteg."
    ),
    "menuEditPasteEffects": (
        "Nincs beilleszthető hatáslista: a tiszta profil belső "
        "hatás-vágólapja üres."
    ),
    "menuFolderRefreshThumbnails": (
        "Nincs látható változás: a bélyegképek frissítése háttérmunka."
    ),
}
_NINCS_LATHATO_HATAS_UTVONAL = {
    ("Folder", "Refresh Thumbnails"): (
        "Nincs látható változás: a bélyegképek frissítése háttérmunka."
    ),
}
_LETILTOTT_A_TISZTA_MINTABAN = {
    "menuViewTimeline": (
        "A Timeline funkció ebben a tiszta mintában szándékosan letiltott."
    ),
    "menuViewAlbumThumbnails": (
        "A könyvtári bélyegkép-kapcsoló fanézetben letiltott; a teszt ezt az "
        "állapotot is meghagyja a menüsorban."
    ),
    "menuPictureShowText": (
        "A kijelölt mintaképeken nincs feliratszöveg, ezért a Show Text "
        "feltételesen letiltott."
    ),
    "menuPictureHideText": (
        "A kijelölt mintaképeken nincs feliratszöveg, ezért a Hide Text "
        "feltételesen letiltott."
    ),
    "menuEditPaste": (
        "A mintában nincs beilleszthető fájl a vágólapon."
    ),
    "menuEditPasteText": (
        "A kijelölt mintaképeken nincs beilleszthető feliratszöveg."
    ),
    "menuEditUndoPasteAllEffects": (
        "Nem történt hatáslista-beillesztés, ezért nincs mit visszavonni."
    ),
    "menuToolsSaveSearch": (
        "A parancs előfeltétele aktív, találatokat adó keresés; minden "
        "menüparancs előtt a keresést alaphelyzetbe állítjuk."
    ),
    "menuFileRevert": (
        "A mintaképen nincs mentett eredeti példány, amelyre vissza lehetne térni."
    ),
    "menuHelpSendLog": (
        "A naplóátadás tesztüzemet igényel; ezt a parancsot nem aktiváljuk, "
        "mert a napló és a célmappa helyének keresése NAS-t is érinthet."
    ),
}
_ABLAK_ALAPMAGASSAG = 760
_NYELV_ALMENU_MIN_MAGASSAG = 2195
_ABLAKMAGASSAG_ELTOLASOK = (-5, 5)
_UTAK: list[dict[str, object]] = []
_QML_ELEMEK: list[object] = []
_UI_ELEMEK: dict[int, list[tuple[QObject, str, str]]] = {}
_DIALOG_ELEMEK: dict[int, list[QObject]] = {}
_LOADER_ELEMEK: dict[int, list[QObject]] = {}
_MENU_ELEMEK: dict[int, list[QObject]] = {}
_MENU_FEJLECEK: dict[int, list[QObject]] = {}


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(feltetel())


def _szoveg(elem, nev: str) -> str:
    ertek = elem.property(nev)
    return str(ertek) if ertek is not None else ""


def _normalizal(felirat: str) -> str:
    return felirat.split("\t", 1)[0].replace("&", "").strip().casefold()


def _menu_e(elem) -> bool:
    if elem is None:
        return False
    try:
        if not shiboken6.isValid(elem):
            return False
        osztaly = elem.metaObject().className()
        cim = elem.property("title")
        darab = elem.property("count")
    except RuntimeError:
        return False
    return (
        "Menu" in osztaly
        and cim is not None
        and darab is not None
    )


def _menupont(menu, index: int) -> QQuickItem:
    kifejezes = QQmlExpression(
        qmlContext(menu), menu, f"itemAt({index})"
    )
    eredmeny, hiba = kifejezes.evaluate()
    assert not hiba, kifejezes.error()
    assert eredmeny is not None, f"a menü {index}. eleme hiányzik"
    pont = shiboken6.getCppPointer(eredmeny)[0]
    elem = shiboken6.wrapInstance(pont, QQuickItem)
    _QML_ELEMEK.append(elem)
    return elem


def _menuk(menu_bar) -> list[QObject]:
    azon = id(menu_bar)
    if azon not in _MENU_ELEMEK:
        _MENU_ELEMEK[azon] = [
            elem
            for elem in menu_bar.findChildren(QObject)
            if shiboken6.isValid(elem) and _menu_e(elem)
        ]
    return [elem for elem in _MENU_ELEMEK[azon] if shiboken6.isValid(elem)]


def _almenu(menu_bar, szulo, sor):
    nev = sor.objectName()
    if nev:
        talalat = next(
            (menu for menu in _menuk(menu_bar) if menu.objectName() == nev), None
        )
        if talalat is not None and talalat is not szulo:
            return talalat

    felirat = _normalizal(_szoveg(sor, "text") or _szoveg(sor, "title"))
    jeloltek = [
        menu
        for menu in _menuk(menu_bar)
        if menu is not szulo
        and _normalizal(_szoveg(menu, "title")) == felirat
    ]
    kapcsolt = [
        menu for menu in jeloltek if menu.property("parentMenu") is szulo
    ]
    if len(kapcsolt) == 1:
        return kapcsolt[0]
    return jeloltek[0] if len(jeloltek) == 1 else None


def _felirat(sor, menu_bar) -> str:
    felirat = _szoveg(sor, "text")
    if not felirat:
        felirat = _szoveg(sor, "title")
    if not felirat:
        almenu = _almenu(menu_bar, None, sor)
        felirat = _szoveg(almenu, "title") if almenu is not None else ""
    return felirat.split("\t", 1)[0].replace("&", "").strip() or "(felirat nélkül)"


def _parancsok(menu, menu_bar, utvonal=(), feliratok=(), kihagyas=None):
    parancsok = []
    kihagyas = kihagyas if kihagyas is not None else {"placeholder": 0, "nyugdijazott": 0}
    for index in range(int(menu.property("count") or 0)):
        sor = _menupont(menu, index)
        osztaly = sor.metaObject().className()
        if "Separator" in osztaly:
            continue

        almenu = _almenu(menu_bar, menu, sor)
        felirat = _felirat(sor, menu_bar)
        if almenu is not None:
            if bool(sor.property("placeholder")):
                kihagyas["placeholder"] += 1
                continue
            if bool(sor.property("retired")):
                kihagyas["nyugdijazott"] += 1
                continue
            if bool(sor.property("enabled")) and bool(almenu.property("enabled")):
                parancsok.extend(
                    _parancsok(
                        almenu,
                        menu_bar,
                        utvonal + (index,),
                        feliratok + (felirat,),
                        kihagyas,
                    )
                )
            continue

        if bool(sor.property("placeholder")):
            kihagyas["placeholder"] += 1
            continue
        if bool(sor.property("retired")):
            kihagyas["nyugdijazott"] += 1
            continue
        parancsok.append(
            {
                "utvonal": utvonal + (index,),
                "feliratok": feliratok + (felirat,),
                "nev": sor.objectName(),
            }
        )
    return parancsok


def _kattints(qt_app, elem) -> None:
    assert elem is not None, "a kattintandó felületi elem hiányzik"
    assert shiboken6.isValid(elem), "a kattintandó felületi elem már megszűnt"
    assert elem.property("enabled") is True, (
        f"{elem.objectName() or _szoveg(elem, 'text')}: tiltott"
    )
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName() or _szoveg(elem, 'text')}: nincs kattintható mérete"
    )
    elem.ensurePolished()
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _kattints_qobject(qt_app, elem) -> None:
    assert shiboken6.isValid(elem), "a kattintandó Qt-elem már megszűnt"
    pont = shiboken6.getCppPointer(elem)[0]
    elem_item = shiboken6.wrapInstance(pont, QQuickItem)
    _QML_ELEMEK.append(elem_item)
    _kattints(qt_app, elem_item)


def _gyoker_menu(menu_bar, cim: str):
    jeloltek = [
        menu
        for menu in _menuk(menu_bar)
        if _normalizal(_szoveg(menu, "title")) == _normalizal(cim)
    ]
    assert len(jeloltek) == 1, f"a felső {cim} menü nem egyértelmű"
    return jeloltek[0]


def _menu_fejlec(menu_bar, cim: str):
    azon = id(menu_bar)
    if azon not in _MENU_FEJLECEK:
        _MENU_FEJLECEK[azon] = [
            elem
            for elem in menu_bar.findChildren(QObject)
            if "MenuBarItem" in elem.metaObject().className()
        ]
    jeloltek = [
        elem
        for elem in _MENU_FEJLECEK[azon]
        if shiboken6.isValid(elem)
        and _normalizal(_szoveg(elem, "text")) == _normalizal(cim)
    ]
    assert len(jeloltek) == 1, f"a felső {cim} menü fejléce nem található"
    return jeloltek[0]


def _megnyit(menu_bar, qt_app, cim: str):
    menu = _gyoker_menu(menu_bar, cim)
    if menu.property("opened") is not True:
        fejlec = _menu_fejlec(menu_bar, cim)
        for _ in range(2):
            _kattints(qt_app, fejlec)
            if _varj(qt_app, lambda: menu.property("opened") is True, 0.5):
                break
    assert _varj(qt_app, lambda: menu.property("opened") is True), (
        f"a felső {cim} menü nem nyílt meg"
    )
    return menu


def _menu_melyseg(menu) -> int:
    melyseg = 0
    szulo = menu.property("parentMenu")
    latott = set()
    while szulo is not None:
        azon = shiboken6.getCppPointer(szulo)[0]
        if azon in latott:
            break
        latott.add(azon)
        melyseg += 1
        szulo = szulo.property("parentMenu")
    return melyseg


def _zarj_menuket(menu_bar, qt_app) -> None:
    for _ in range(4):
        nyitottak = [
            menu for menu in _menuk(menu_bar) if menu.property("opened") is True
        ]
        if not nyitottak:
            return
        for menu in sorted(nyitottak, key=_menu_melyseg, reverse=True):
            QMetaObject.invokeMethod(
                menu, "close", Qt.ConnectionType.DirectConnection
            )
        qt_app.processEvents()
    assert _varj(
        qt_app,
        lambda: not any(
            menu.property("opened") is True for menu in _menuk(menu_bar)
        ),
    ), "a menüsor nem zárult be"


def _elero_menu(menu_bar, qt_app, cim: str, utvonal: tuple[int, ...]):
    aktualis = _megnyit(menu_bar, qt_app, cim)
    for index in utvonal[:-1]:
        sor = _menupont(aktualis, index)
        almenu = _almenu(menu_bar, aktualis, sor)
        assert almenu is not None, (
            f"az almenü eltűnt: {_szoveg(sor, 'text') or sor.objectName()}"
        )
        if almenu.property("opened") is not True:
            _kattints(qt_app, sor)
        assert _varj(qt_app, lambda almenu=almenu: almenu.property("opened") is True), (
            f"az almenü nem nyílt meg: {_szoveg(almenu, 'title')}"
        )
        aktualis = almenu
    return _menupont(aktualis, utvonal[-1])


def _ertek(ertek):
    if ertek is None or isinstance(ertek, (bool, int, float, str)):
        return ertek
    if isinstance(ertek, (list, tuple)):
        return tuple(_ertek(elem) for elem in ertek)
    if hasattr(ertek, "toString"):
        try:
            return str(ertek.toString())
        except RuntimeError:
            return "<Qt-objektum>"
    return None


def _betoltott_feluleti_objektumok(ablak):
    """Adja vissza a nézet objektumait a már aktív DeferredDialogokkal együtt."""
    objektumok = [ablak, *ablak.findChildren(QObject)]
    for masik in QGuiApplication.allWindows():
        if masik is not ablak:
            objektumok.extend((masik, *masik.findChildren(QObject)))

    eredmeny = []
    sor = list(objektumok)
    latott = set()
    while sor:
        objektum = sor.pop()
        try:
            if not shiboken6.isValid(objektum):
                continue
            azon = shiboken6.getCppPointer(objektum)[0]
            if azon in latott:
                continue
            latott.add(azon)
            nev = objektum.objectName()
            osztaly = objektum.metaObject().className()
        except RuntimeError:
            continue
        eredmeny.append(objektum)
        if "Loader" not in osztaly and "DeferredDialog" not in osztaly and "Loader" not in nev:
            continue
        try:
            betoltott = objektum.property("item")
            if betoltott is not None and shiboken6.isValid(betoltott):
                sor.extend((betoltott, *betoltott.findChildren(QObject)))
        except RuntimeError:
            continue
    return eredmeny


def _frissitsd_a_halasztott_objektumokat(ablak) -> None:
    """Az első állapotfelvétel után megnyitott Loader-tartalmakat is cache-eli."""
    ablak_azon = id(ablak)
    if ablak_azon not in _UI_ELEMEK:
        return
    ismert = set()
    for objektum, _nev, _osztaly in _UI_ELEMEK[ablak_azon]:
        try:
            if shiboken6.isValid(objektum):
                ismert.add(shiboken6.getCppPointer(objektum)[0])
        except RuntimeError:
            continue
    varakozo = []
    for loader in _LOADER_ELEMEK.get(ablak_azon, ()):
        try:
            if not shiboken6.isValid(loader):
                continue
            betoltott = loader.property("item")
            if betoltott is not None and shiboken6.isValid(betoltott):
                varakozo.extend((betoltott, *betoltott.findChildren(QObject)))
        except RuntimeError:
            continue
    while varakozo:
        objektum = varakozo.pop()
        try:
            if not shiboken6.isValid(objektum):
                continue
            azon = shiboken6.getCppPointer(objektum)[0]
            if azon in ismert:
                continue
            ismert.add(azon)
            nev = objektum.objectName()
            osztaly = objektum.metaObject().className()
        except RuntimeError:
            continue
        if nev and nev.casefold() != "label":
            _UI_ELEMEK[ablak_azon].append((objektum, nev, osztaly))
        if "dialog" in (nev + osztaly).casefold():
            _DIALOG_ELEMEK[ablak_azon].append(objektum)
        if "Loader" in osztaly or "DeferredDialog" in osztaly or "Loader" in nev:
            _LOADER_ELEMEK[ablak_azon].append(objektum)
            try:
                betoltott = objektum.property("item")
                if betoltott is not None and shiboken6.isValid(betoltott):
                    varakozo.extend((betoltott, *betoltott.findChildren(QObject)))
            except RuntimeError:
                pass


def _feluleti_allapot(ablak):
    ertekek = {}
    ablak_azon = id(ablak)
    if ablak_azon not in _UI_ELEMEK:
        objektumok = _betoltott_feluleti_objektumok(ablak)
        elemek = []
        dialogusok = []
        for objektum in objektumok:
            try:
                nev = objektum.objectName()
                osztaly = objektum.metaObject().className()
                if "dialog" in (nev + osztaly).casefold():
                    dialogusok.append(objektum)
                if nev and nev.casefold() != "label":
                    elemek.append((objektum, nev, osztaly))
                if "Loader" in osztaly or "DeferredDialog" in osztaly or "Loader" in nev:
                    _LOADER_ELEMEK.setdefault(ablak_azon, []).append(objektum)
            except RuntimeError:
                continue
        _UI_ELEMEK[ablak_azon] = elemek
        _DIALOG_ELEMEK[ablak_azon] = dialogusok
    else:
        _frissitsd_a_halasztott_objektumokat(ablak)

    duplikatumok = {}
    for objektum, nev, osztaly in _UI_ELEMEK[ablak_azon]:
        try:
            if not shiboken6.isValid(objektum):
                continue
        except RuntimeError:
            continue
        # A több ezer névtelen QML-részletet nem kell minden 50 ms-os
        # állapotellenőrzéskor kiolvasni; a képernyőn megfigyelhető panelek,
        # ablakok és vezérlők mind névvel szerepelnek a QML-ben.
        if not nev:
            continue
        if "Menu" in osztaly and "MenuBar" not in osztaly and "MenuItem" not in osztaly:
            continue
        sorszam = duplikatumok.get(nev, 0)
        duplikatumok[nev] = sorszam + 1
        kulcs = f"{nev}[{sorszam}]"
        mezok = {}
        for tulajdonsag in ("visible", "opened", "checked", "currentIndex", "active"):
            try:
                ertek = _ertek(objektum.property(tulajdonsag))
            except RuntimeError:
                continue
            if ertek is not None:
                if tulajdonsag in {"visible", "opened"} and "MenuItem" in osztaly:
                    continue
                mezok[tulajdonsag] = ertek
        if mezok:
            ertekek[kulcs] = mezok
    return ertekek


def _allapot(ablak, vezerlo, minta):
    ertekek = _feluleti_allapot(ablak)

    vezerloertekek = {}
    meta = vezerlo.metaObject()
    for index in range(meta.propertyOffset(), meta.propertyCount()):
        tulajdonsag = meta.property(index).name()
        try:
            ertek = _ertek(vezerlo.property(tulajdonsag))
        except RuntimeError:
            continue
        if ertek is not None:
            vezerloertekek[tulajdonsag] = ertek

    ablakertekek = {}
    for tulajdonsag in (
        "selectedIndexes",
        "selectedIndex",
        "activeDrawerTab",
        "viewerOpen",
        "slideshowRunning",
        "thumbSize",
        "libraryFrameVisible",
    ):
        try:
            ertek = _ertek(ablak.property(tulajdonsag))
        except RuntimeError:
            continue
        if ertek is not None:
            ablakertekek[tulajdonsag] = ertek

    beallitasok = QSettings(
        str(minta.parent / "settings.ini"), QSettings.Format.IniFormat
    )
    beallitasok.sync()
    beallitasertekek = {
        str(kulcs): _ertek(beallitasok.value(kulcs))
        for kulcs in beallitasok.allKeys()
    }

    fajlok = {}
    for ut in sorted(minta.rglob("*")):
        if ut.is_file():
            info = ut.stat()
            fajlok[str(ut.relative_to(minta))] = (info.st_size, info.st_mtime_ns)

    vagolap = QGuiApplication.clipboard().mimeData()
    vagolap_allapot = (
        (tuple(vagolap.formats()), vagolap.text(), tuple(
            url.toLocalFile() for url in vagolap.urls()
        ))
        if vagolap is not None
        else ((), "", ())
    )
    mappa_modell = vezerlo.folders
    mappalista = tuple(mappa_modell.folder_paths())
    mappa_rejtett = bool(vezerlo.isFolderHidden(str(minta)))
    return {
        "felulet": ertekek,
        "vezerlo": vezerloertekek,
        "ablak": ablakertekek,
        "beallitasok": beallitasertekek,
        "fajlok": fajlok,
        "vagolap": vagolap_allapot,
        "mappalista": mappalista,
        "mappa_rejtett": mappa_rejtett,
    }


def _kulonbsegek(elotte, utana) -> list[str]:
    eredmeny = []
    for csoport in ("felulet", "vezerlo"):
        regi = elotte[csoport]
        uj = utana[csoport]
        for nev in sorted(set(regi) | set(uj)):
            regi_mezok = regi.get(nev, {})
            uj_mezok = uj.get(nev, {})
            for mezok in sorted(set(regi_mezok) | set(uj_mezok)):
                if regi_mezok.get(mezok) == uj_mezok.get(mezok):
                    continue
                elozo, kovetkezo = regi_mezok.get(mezok), uj_mezok.get(mezok)
                if mezok in {"visible", "opened"} and kovetkezo is True:
                    eredmeny.append(f"megnyílt: {nev}")
                elif mezok in {"visible", "opened"}:
                    # A menüpont kattintás utáni bezáródása nem bizonyítja,
                    # hogy a parancs végrehajtott valamit.
                    continue
                elif mezok == "checked":
                    eredmeny.append(f"pipa: {nev} {elozo} → {kovetkezo}")
                else:
                    eredmeny.append(f"állapot: {nev}.{mezok} {elozo} → {kovetkezo}")

    for csoport, cimke in (("ablak", "ablakállapot"), ("beallitasok", "beállítás")):
        regi = elotte[csoport]
        uj = utana[csoport]
        for nev in sorted(set(regi) | set(uj)):
            if regi.get(nev) != uj.get(nev):
                eredmeny.append(
                    f"{cimke}: {nev} {regi.get(nev)!r} → {uj.get(nev)!r}"
                )

    if elotte["fajlok"] != utana["fajlok"]:
        elteres = sorted(set(elotte["fajlok"]) ^ set(utana["fajlok"]))
        valtozott = sorted(
            nev
            for nev in set(elotte["fajlok"]) & set(utana["fajlok"])
            if elotte["fajlok"][nev] != utana["fajlok"][nev]
        )
        eredmeny.append("mintamappa-fájl: " + ", ".join((elteres + valtozott)[:3]))
    if elotte["vagolap"] != utana["vagolap"]:
        eredmeny.append("a vágólap tartalma megváltozott")
    if elotte["mappalista"] != utana["mappalista"]:
        eredmeny.append(
            "mappalista: "
            f"{elotte['mappalista']!r} → {utana['mappalista']!r}"
        )
    if elotte["mappa_rejtett"] != utana["mappa_rejtett"]:
        eredmeny.append(
            "mappa rejtett állapota: "
            f"{elotte['mappa_rejtett']} → {utana['mappa_rejtett']}"
        )
    return eredmeny


def _kepernyokep(ablak, cel: Path) -> bool:
    cel.parent.mkdir(parents=True, exist_ok=True)
    kep = ablak.grabWindow()
    if kep.isNull():
        return False
    return bool(kep.save(str(cel), "PNG"))


def _kepernyout(cel: Path, cim: str, leiras) -> Path:
    # Az útvonal-indexek egyedivé teszik a nevet azonos vagy nem ASCII feliratoknál.
    indexek = "-".join(str(index) for index in leiras["utvonal"])
    parancsnev = leiras.get("nev") or "command"
    nev = re.sub(r"[^A-Za-z0-9._-]+", "-", f"{cim}-{indexek}-{parancsnev}")
    return cel / f"{nev.strip('-')}.png"


def _lathato_dialogusok(ablak):
    # A DeferredDialog a QML Loader `item` tulajdonságába teszi a párbeszédet;
    # az új fa nem feltétlenül lesz QObject-gyereke a főablaknak.
    ablak_azon = id(ablak)
    if ablak_azon not in _UI_ELEMEK:
        _feluleti_allapot(ablak)
    else:
        _frissitsd_a_halasztott_objektumokat(ablak)
    elemek = _DIALOG_ELEMEK.get(ablak_azon, ())
    talalatok = []
    latott = set()
    for elem in elemek:
        try:
            if not shiboken6.isValid(elem):
                continue
            azon = shiboken6.getCppPointer(elem)[0]
            osztaly = elem.metaObject().className()
            nev = elem.objectName()
        except RuntimeError:
            continue
        if azon in latott or "Menu" in osztaly:
            continue
        latott.add(azon)
        tipus = (nev + osztaly).casefold()
        if "dialog" not in tipus or any(
            resz in tipus
            for resz in ("loader", "buttonbox", "deferreddialog", "dialogs")
        ):
            continue
        if elem.property("opened") is True or elem.property("visible") is True:
            talalatok.append(elem)
    return talalatok


def _zarj_parbeszedeket(ablak, qt_app, naplo: list[str]) -> None:
    for _ in range(4):
        dialogusok = _lathato_dialogusok(ablak)
        if not dialogusok:
            return
        kezelt_nevek = set()
        for dialogus in dialogusok:
            if not shiboken6.isValid(dialogus):
                continue
            nev = dialogus.objectName() or dialogus.metaObject().className()
            if nev in kezelt_nevek:
                continue
            kezelt_nevek.add(nev)
            keres_fut = dialogus.property("scanning") is True
            gombok = []
            for elem in dialogus.findChildren(QObject):
                if (
                    not shiboken6.isValid(elem)
                    or "Button" not in elem.metaObject().className()
                    or elem.property("visible") is not True
                    or elem.property("enabled") is not True
                ):
                    continue
                gombnev = elem.objectName().casefold()
                felirat = _normalizal(_szoveg(elem, "text"))
                dedup_ablak = "dedup" in nev.casefold()
                if any(szo in gombnev for szo in ("cancel", "megse")) or (
                    felirat in {"cancel", "mégse"}
                ):
                    rang = 1 if dedup_ablak else 0
                    gombok.append((rang, elem))
                elif "close" in gombnev or felirat == "close":
                    rang = 0 if dedup_ablak else 1
                    gombok.append((rang, elem))
            if gombok:
                gombok.sort(key=lambda adat: adat[0])
                gomb = gombok[0][1]
                gombnev = gomb.objectName().casefold()
                _kattints_qobject(qt_app, gomb)
                if keres_fut and "close" not in gombnev:
                    naplo.append(f"{nev}: Cancel gombbal a keresés megszakítva")
                    _varj(
                        qt_app,
                        lambda dialogus=dialogus: dialogus.property("scanning")
                        is False,
                        3.0,
                    )
                elif keres_fut:
                    naplo.append(
                        f"{nev}: Close gombbal bezárva; a keresés megszakítása is elindult"
                    )
                else:
                    naplo.append(f"{nev}: Mégse/Close gombbal bezárva")
                continue

            # A natív Qt Quick FolderDialogban nincs QML Mégse-gomb, a close()
            # viszont a visszautasító útvonalon zárja be.
            if QMetaObject.invokeMethod(
                dialogus, "close", Qt.ConnectionType.DirectConnection
            ):
                qt_app.processEvents()
                naplo.append(f"{nev}: close() útvonalon, Mégse-ként bezárva")
                continue

            celablak = next(
                (
                    masik
                    for masik in QGuiApplication.allWindows()
                    if masik.objectName() == nev
                    and masik.property("visible") is True
                ),
                None,
            )
            if celablak is None:
                masodlagos_ablakok = [
                    masik
                    for masik in QGuiApplication.allWindows()
                    if masik is not ablak and masik.property("visible") is True
                ]
                celablakok = masodlagos_ablakok or [ablak]
            else:
                celablakok = [celablak]
            for celablak in celablakok:
                QTest.keyClick(celablak, Qt.Key.Key_Escape)
            qt_app.processEvents()
            naplo.append(f"{nev}: Escape billentyűvel, Mégse útvonalon bezárva")
        if not _varj(qt_app, lambda: not _lathato_dialogusok(ablak), 1.0):
            naplo.append("Mégse útvonal után is nyitva maradt párbeszédablak")


def _zarj_nezot_es_fiokot(ablak, qt_app) -> None:
    if ablak.property("viewerOpen") is True:
        vissza = ablak.findChild(QObject, "viewerBackButton")
        if (
            vissza is not None
            and vissza.property("visible") is True
            and vissza.property("enabled") is True
        ):
            _kattints(qt_app, vissza)
        else:
            ablak.setProperty("viewerOpen", False)
            qt_app.processEvents()
    if ablak.property("slideshowRunning") is True:
        QTest.keyClick(ablak, Qt.Key.Key_Escape)
        _varj(qt_app, lambda: ablak.property("slideshowRunning") is False)
    ablak.setProperty("activeDrawerTab", "")
    qt_app.processEvents()
    tabsor = ablak.findChild(QObject, "documentTabStrip")
    konyvtar_ful = ablak.findChild(QObject, "documentTabLibrary")
    if (
        tabsor is not None
        and tabsor.property("libraryActive") is False
        and konyvtar_ful is not None
        and konyvtar_ful.property("visible") is True
        and konyvtar_ful.property("enabled") is True
    ):
        _kattints_qobject(qt_app, konyvtar_ful)


def _zarj_ertesitosavot(ablak, vezerlo, qt_app) -> None:
    """A keresési művelet után zárja le a maradó jelzést és munkát.

    A színkeresés a fotók gyorsítótárát háttérben tölti fel. A menühatás
    képernyőképe már elkészült, ezért a tiszta következő parancs érdekében a
    valódi Leállítás/Bezárás vezérlővel zárjuk le a sávot.
    """
    szoveg = ablak.findChild(QObject, "errorBannerText")
    if szoveg is None or not _szoveg(szoveg, "text"):
        return

    leallitas = ablak.findChild(QObject, "errorBannerStopButton")
    if leallitas is not None and leallitas.property("visible") is True:
        _kattints_qobject(qt_app, leallitas)
        assert vezerlo.waitForBackgroundWorkers(3.0), (
            "a színkeresés háttérmunkája nem állt le a tiszta visszaállításra"
        )
    else:
        bezaras = ablak.findChild(QObject, "errorBannerCloseButton")
        assert bezaras is not None and bezaras.property("visible") is True, (
            "a látható tájékoztató sávnak nincs bezáró vezérlője"
        )
        _kattints_qobject(qt_app, bezaras)

    assert _varj(qt_app, lambda: _szoveg(szoveg, "text") == ""), (
        "a tájékoztató sáv nem záródott be"
    )
    assert vezerlo.color_index_fut() is False, (
        "a színkeresés háttérmunkája a sáv bezárása után is fut"
    )


def _allitsd_vissza_a_mintamappat(
    ablak, vezerlo, minta: Path, menu_bar, qt_app, *, parancs_nev: str = ""
) -> None:
    """Zárja a felületi rétegeket, ürítse a keresőt, majd álljon a mintamappára."""
    _zarj_menuket(menu_bar, qt_app)
    _zarj_parbeszedeket(ablak, qt_app, [])
    _zarj_nezot_es_fiokot(ablak, qt_app)
    ablak.setProperty("unnamedFacesOpen", False)
    for nev in ("giftCdHost", "backupHost"):
        host = ablak.findChild(QObject, nev)
        if host is not None and host.property("nyitva") is True:
            host.setProperty("nyitva", False)

    if vezerlo.property("tesztuzemEnabled") is True:
        vezerlo.setTesztuzemEnabled(False)

    # A Hide/Unhide és a korábbi parancsok rejtett fotó-állapotát a következő
    # megfigyelés előtt visszaállítjuk. Az Unhide saját előfeltételét az
    # _akcio készíti elő külön, így maga a kattintás is mérhető.
    rejtett_sorok = [
        index
        for index, photo in enumerate(vezerlo.photos.photos)
        if photo.hidden
    ]
    if rejtett_sorok:
        vezerlo.toggleHiddenRows(rejtett_sorok)
    if vezerlo.showHidden:
        vezerlo.setShowHidden(False)

    toolbar = ablak.findChild(QObject, "mainToolbar")
    assert toolbar is not None, "a keresősáv hiányzik"
    assert QMetaObject.invokeMethod(
        toolbar, "clearSearch", Qt.ConnectionType.DirectConnection
    ), "a próba nem tudta kiüríteni a keresőmezőt"
    vezerlo.search("")
    _zarj_ertesitosavot(ablak, vezerlo, qt_app)

    minta_ut = str(minta)
    if vezerlo.isFolderHidden(minta_ut):
        vezerlo.toggleFolderHidden(minta_ut)
    if vezerlo.property("showHidden") is True:
        vezerlo.setShowHidden(False)
    vezerlo.selectFolder(minta_ut)

    # A „Show” parancs csak rejtett mappán tesztelhető. A rejtett mappák
    # listájának engedélyezése után ugyanazt a mintamappát jelöljük ki.
    if parancs_nev == "menuFolderShow":
        vezerlo.toggleFolderHidden(minta_ut)
        vezerlo.setShowHidden(True)
        vezerlo.selectFolder(minta_ut)

    ablak.setProperty("selectedIndexes", [0])
    ablak.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    assert _varj(
        qt_app,
        lambda: _szoveg(toolbar, "searchText") == ""
        and vezerlo.property("searchActive") is False
        and vezerlo.property("currentFolder") == minta_ut
        and minta_ut in tuple(vezerlo.folders.folder_paths())
        and not any(
            menu.property("opened") is True for menu in _menuk(menu_bar)
        ),
    ), "a bejáró nem állt vissza a kereső és a mintamappa alaphelyzetébe"


def _akcio(ablak, vezerlo, minta, menu_bar, qt_app, cim, leiras, cel, kulsok):
    nev = str(leiras.get("nev", ""))
    nyelvi_parancs = nev.startswith("menuLanguage")
    if nyelvi_parancs and not (
        _NYELV_ALMENU_MIN_MAGASSAG - 5
        <= ablak.height()
        <= _NYELV_ALMENU_MIN_MAGASSAG + 5
    ):
        celmagassag = _NYELV_ALMENU_MIN_MAGASSAG
        ablak.setHeight(celmagassag)
        assert _varj(qt_app, lambda: ablak.height() == celmagassag), (
            f"az ablakmagasság nem állt be a {celmagassag} px értékre"
        )
    elif not nyelvi_parancs and ablak.height() > 1000:
        ablak.setHeight(_ABLAK_ALAPMAGASSAG)
        assert _varj(qt_app, lambda: ablak.height() == _ABLAK_ALAPMAGASSAG)
    _allitsd_vissza_a_mintamappat(
        ablak,
        vezerlo,
        minta,
        menu_bar,
        qt_app,
        parancs_nev=str(leiras.get("nev", "")),
    )
    ablak.setProperty("selectedIndexes", [0])
    ablak.setProperty("selectedIndex", 0)
    if nev == "menuPictureUnhide":
        vezerlo.toggleHiddenRows([0])
        vezerlo.setShowHidden(True)
        vezerlo.selectFolder(str(minta))
        assert vezerlo.photos.photos[0].hidden is True, (
            "az Unhide parancs előfeltétele nem állt elő"
        )
        ablak.setProperty("selectedIndexes", [0])
        ablak.setProperty("selectedIndex", 0)
        qt_app.processEvents()
    qt_app.processEvents()
    sor = _elero_menu(menu_bar, qt_app, cim, leiras["utvonal"])
    nev = sor.objectName()
    parancs = " › ".join(leiras["feliratok"])
    keput = _kepernyout(cel, cim, leiras)
    if sor.property("visible") is not True:
        kepkesz = _kepernyokep(ablak, keput)
        _allitsd_vissza_a_mintamappat(ablak, vezerlo, minta, menu_bar, qt_app)
        indok = _LETILTOTT_A_TISZTA_MINTABAN.get(nev)
        return {
            "menu": cim,
            "utvonal": tuple(leiras["utvonal"]),
            "parancs": parancs,
            "eredmeny": "rejtett állapotban maradt; nem kattintható"
            + (f"; indoklás: {indok}" if indok else ""),
            "kep": str(keput) if kepkesz else "",
            "hiba": indok is None,
        }
    if sor.property("enabled") is not True:
        kepkesz = _kepernyokep(ablak, keput)
        _allitsd_vissza_a_mintamappat(ablak, vezerlo, minta, menu_bar, qt_app)
        indok = _LETILTOTT_A_TISZTA_MINTABAN.get(nev)
        return {
            "menu": cim,
            "utvonal": tuple(leiras["utvonal"]),
            "parancs": parancs,
            "eredmeny": "feltételesen letiltott; nem kattintható"
            + (f"; indoklás: {indok}" if indok else ""),
            "kep": str(keput) if kepkesz else "",
            "hiba": indok is None,
        }

    elotte = _allapot(ablak, vezerlo, minta)
    dialogusok_elotte = {
        dialogus.objectName() or dialogus.metaObject().className()
        for dialogus in _lathato_dialogusok(ablak)
    }
    kulso_elotte = len(kulsok)
    elsult = []
    sor.triggered.connect(lambda *_args: elsult.append(True))
    _kattints(qt_app, sor)

    _varj(
        qt_app,
        lambda: bool(_lathato_dialogusok(ablak))
        or _feluleti_allapot(ablak) != elotte["felulet"],
        1.0,
    )
    if nev == "menuToolsPassportPhoto":
        assert vezerlo.waitForBackgroundWorkers(3.0), (
            "az útlevélkép háttérmunkája nem fejeződött be"
        )
        qt_app.processEvents()
    if nyelvi_parancs and ablak.height() > _ABLAK_ALAPMAGASSAG + 5:
        # A hosszú nyelvlistát ideiglenesen magas ablakban kattintjuk; a
        # párbeszéd középre igazodik, így a lementett bizonyító kép normál
        # méretű marad és nem foglal nyelvenként nagy képkocka-puffert.
        ablak.setHeight(_ABLAK_ALAPMAGASSAG)
        assert _varj(qt_app, lambda: ablak.height() == _ABLAK_ALAPMAGASSAG), (
            "a nyelvparancs utáni ablakméret-visszaállítás nem sikerült"
        )
    utana = _allapot(ablak, vezerlo, minta)
    hatasok = _kulonbsegek(elotte, utana)
    for dialogus in _lathato_dialogusok(ablak):
        dialogusnev = dialogus.objectName() or dialogus.metaObject().className()
        if dialogusnev not in dialogusok_elotte:
            hatasok.append(f"megnyílt párbeszédablak: {dialogusnev}")
    if len(kulsok) > kulso_elotte:
        hatasok.append("külső művelet átadva: " + "; ".join(kulsok[kulso_elotte:]))

    kepkesz = _kepernyokep(ablak, keput)
    hiba = False
    if not elsult:
        eredmeny = "a menüsori kattintás nem bocsátott ki aktiválást"
        hiba = True
    elif not hatasok:
        if bool(sor.property("checkable")) and sor.property("checked") is True:
            eredmeny = "már kiválasztott állapot; az érték nem változott"
        elif nev in _NINCS_LATHATO_HATAS or (cim, parancs) in _NINCS_LATHATO_HATAS_UTVONAL:
            eredmeny = _NINCS_LATHATO_HATAS.get(
                nev, _NINCS_LATHATO_HATAS_UTVONAL.get((cim, parancs), "")
            )
        elif nev == "menuFileExit":
            eredmeny = "a kilépési parancs a kattintásra elsült"
        else:
            eredmeny = "kattintás után nem látszott ablak-, panel- vagy állapotváltozás"
            hiba = True
    else:
        eredmeny = "; ".join(hatasok[:4])
    if not kepkesz:
        eredmeny += "; nem sikerült képernyőképet menteni"
        hiba = True

    bezaras = []
    _zarj_parbeszedeket(ablak, qt_app, bezaras)
    _zarj_nezot_es_fiokot(ablak, qt_app)
    if bezaras:
        eredmeny += "; " + ", ".join(bezaras)
        if any("nyitva maradt" in sor for sor in bezaras):
            hiba = True

    allapot_menulista = utana["mappalista"]
    allapot_mappa_rejtett = utana["mappa_rejtett"]
    _allitsd_vissza_a_mintamappat(ablak, vezerlo, minta, menu_bar, qt_app)

    return {
        "menu": cim,
        "utvonal": tuple(leiras["utvonal"]),
        "parancs": parancs,
        "eredmeny": eredmeny,
        "kep": str(keput),
        "hiba": hiba,
        "mappalista": allapot_menulista,
        "mappa_rejtett": allapot_mappa_rejtett,
    }


def _minta_kepek(lib: Path) -> None:
    make_jpeg(lib / "a.jpg", size=(400, 300))
    make_jpeg(lib / "b.jpg", size=(500, 400))
    make_jpeg(lib / "c.jpg", size=(640, 480))


@pytest.fixture
def tiszta_menuproba(qt_app, tmp_path, monkeypatch):
    from tests.app.qml_functional.conftest import _build_qml_app

    epito = _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_minta_kepek,
        email_vezerlo=True,
        show_only_big_images=None,
    )
    ablak, vezerlo, motor = next(epito)
    # A közös fixture teszt-alapértékeit töröljük: a bejárás tiszta
    # profilból indul, a képernyőképek és az index kivételével.
    beallitas = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    beallitas.clear()
    beallitas.sync()
    assert not beallitas.allKeys(), "a próba felhasználói profilja nem üres"

    # A funkcionális QML-építő az alkalmazás többi vezérlőjét beköti, de a
    # DedupController-t a legtöbb meglévő próba nem használja. A menü teljes
    # bejárása viszont megnyitja a DedupDialogot, ezért a produkciós
    # context propertyt is meg kell adni a tiszta tesztalkalmazásnak.
    from picasapy.app.dedup_controller import DedupController

    dedup_controller = DedupController(tmp_path / "index.db", vezerlo._provider)
    motor.rootContext().setContextProperty("dedupController", dedup_controller)
    from picasapy.app.backup_controller import BackupController

    backup_controller = BackupController(tmp_path / "index.db", (str(tmp_path / "kepek"),))
    motor.rootContext().setContextProperty("backupController", backup_controller)

    # A kimenő kép/fájl műveletek a mintamappát használják; asztali programot
    # és fájlkezelőt nem indítunk el.
    monkeypatch.setattr(collage_output, "pictures_dir", lambda: tmp_path / "kepek")
    monkeypatch.setattr(movie_output, "pictures_dir", lambda: tmp_path / "kepek")
    import picasapy.app.fileops_controller as fileops_module

    kulso = []
    monkeypatch.setattr(
        fileops_module,
        "_open_url",
        lambda url: kulso.append(f"megnyitás: {url.toString()}") or True,
    )
    monkeypatch.setattr(
        fileops_module,
        "reveal_in_file_manager",
        lambda path: kulso.append(f"fájlkezelő: {path}"),
    )
    monkeypatch.setattr(
        fileops_module,
        "open_folder_in_file_manager",
        lambda path: kulso.append(f"mappakezelő: {path}"),
    )
    import picasapy.app.wallpaper as wallpaper_module

    monkeypatch.setattr(
        wallpaper_module,
        "set_desktop_background",
        lambda path: kulso.append(f"asztali háttérkép: {path}") or "",
    )
    try:
        yield ablak, vezerlo, motor, tmp_path, kulso
    finally:
        next(epito, None)
        _QML_ELEMEK.clear()
        _UI_ELEMEK.clear()
        _DIALOG_ELEMEK.clear()
        _LOADER_ELEMEK.clear()
        _MENU_ELEMEK.clear()
        _MENU_FEJLECEK.clear()


@pytest.fixture(scope="module", autouse=True)
def scratch_jelentes(tmp_path_factory):
    _UTAK.clear()
    gyoker = tmp_path_factory.getbasetemp()
    yield gyoker
    sorok = [
        "# #4433 főmenü-bejárás — futási jegyzék",
        "",
        "A felvételek a scratch könyvtárban vannak; a teszt a tiszta, ideiglenes profilt használta.",
        "",
    ]
    alap_futasok = [futas for futas in _UTAK if futas["magassag"] == 0]
    parancsok = {}
    for futas in alap_futasok:
        for ut in futas["eredmenyek"]:
            parancsok[(ut["menu"], tuple(ut.get("utvonal", ())))] = ut
    osszes = list(parancsok.values())
    elteresek = [ut for ut in osszes if ut.get("hiba")]
    sorok.extend(
        [
            f"Egyedi menüútvonalak: {len(osszes)}; ismételt megfigyelések összevonva: "
            f"{sum(len(futas['eredmenyek']) for futas in alap_futasok) - len(osszes)}; "
            f"eltérésként jelölve: {len(elteresek)}.",
            "A jegyben említett 195 a korábbi futás ismétlésekkel számolt megfigyelésszáma; "
            "a menüsorban 185 különböző útvonal van.",
            "",
            "## Működési eltérések",
            "",
        ]
    )
    if elteresek:
        for ut in elteresek:
            sorok.append(
                f"- **{ut['menu']} › {ut['parancs']}** — {ut['eredmeny']}"
            )
    else:
        sorok.append("Nem észlelt működési eltérést.")
    sorok.append("")
    for futas in alap_futasok:
        eredmenyek = [
            ut
            for ut in osszes
            if ut["menu"] == futas["menu"]
        ]
        sorok.append(f"## {futas['menu']} menü, ablakmagasság-eltolás: {futas['magassag']} px")
        sorok.append("")
        sorok.append("| Parancs | Megfigyelt eredmény | Képernyőkép |")
        sorok.append("|---|---|---|")
        for ut in eredmenyek:
            kep = Path(str(ut["kep"]))
            kepnev = str(kep.relative_to(gyoker)) if ut["kep"] else "—"
            sorok.append(
                f"| {ut['menu']} › {ut['parancs']} | {ut['eredmeny']} | {kepnev} |"
            )
        sorok.append("")
    cel = gyoker / "4433-fomenuk-futas.md"
    cel.write_text("\n".join(sorok), encoding="utf-8")
    print(f"[#4420] képernyőképek és futási jegyzék: {cel}")


def test_tiszta_profilbol_valodi_kattintassal_bejarja_a_fomenuket(
    tiszta_menuproba, qt_app, scratch_jelentes
):
    ablak, vezerlo, _motor, tmp_path, kulsok = tiszta_menuproba
    _QML_ELEMEK.clear()
    ablak.setHeight(_ABLAK_ALAPMAGASSAG)
    assert _varj(qt_app, lambda: ablak.height() == _ABLAK_ALAPMAGASSAG), (
        "az ablak magassága nem állt be az alapértékre"
    )
    ablak.setProperty("selectedIndexes", [0])
    ablak.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    menu_bar = ablak.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    parancsazonositok = set()
    for rovid_nev, cim in _MENUK:
        menu = _megnyit(menu_bar, qt_app, cim)
        kihagyott = {"placeholder": 0, "nyugdijazott": 0}
        parancsok = _parancsok(menu, menu_bar, kihagyas=kihagyott)
        parancsazonositok.update(
            (rovid_nev, tuple(parancs["utvonal"])) for parancs in parancsok
        )
        varakozo = list(parancsok)
        eredmenyek = []
        kor = 0
        while varakozo and kor < 4:
            kor += 1
            kesobbre = []
            tortent_kattintas = False
            for parancs in varakozo:
                try:
                    ut = _akcio(
                        ablak,
                        vezerlo,
                        tmp_path / "kepek",
                        menu_bar,
                        qt_app,
                        rovid_nev,
                        parancs,
                        tmp_path / "kepernyokepek",
                        kulsok,
                    )
                except Exception as exc:  # a hátralévő menütételeket is végigjárjuk
                    keput = _kepernyout(
                        tmp_path / "kepernyokepek", rovid_nev, parancs
                    )
                    kepkesz = _kepernyokep(ablak, keput)
                    ut = {
                        "menu": rovid_nev,
                        "utvonal": tuple(parancs["utvonal"]),
                        "parancs": " › ".join(parancs["feliratok"]),
                        "eredmeny": f"kattintási hiba: {type(exc).__name__}: {exc}",
                        "kep": str(keput) if kepkesz else "",
                        "hiba": True,
                    }
                    _allitsd_vissza_a_mintamappat(
                        ablak, vezerlo, tmp_path / "kepek", menu_bar, qt_app
                    )
                if parancs["nev"] == "menuFolderHide":
                    assert str(tmp_path / "kepek") not in ut.get("mappalista", ()), (
                        "a Folder ▸ Hide nem vette ki a mintamappát a mappalistából"
                    )
                    assert ut.get("mappa_rejtett") is True
                elif parancs["nev"] == "menuFolderShow":
                    assert str(tmp_path / "kepek") in ut.get("mappalista", ()), (
                        "a Folder ▸ Show nem tette vissza a mintamappát a mappalistába"
                    )
                    assert ut.get("mappa_rejtett") is False
                eredmenyek.append(ut)
                if (
                    ut["hiba"]
                    and (
                        "feltételesen letiltott" in ut["eredmeny"]
                        or "rejtett állapotban" in ut["eredmeny"]
                    )
                ):
                    kesobbre.append(parancs)
                else:
                    tortent_kattintas = True
            if not tortent_kattintas:
                break
            varakozo = kesobbre

        for parancs in varakozo:
            utvonal = " › ".join(parancs["feliratok"])
            korabbi = next(
                (
                    adat
                    for adat in eredmenyek
                    if adat["menu"] == rovid_nev and adat["parancs"] == utvonal
                ),
                None,
            )
            if korabbi is not None:
                korabbi["eredmeny"] += "; a bejárás végéig letiltva/rejtve maradt"
                continue
            eredmenyek.append(
                {
                    "menu": rovid_nev,
                    "utvonal": tuple(parancs["utvonal"]),
                    "parancs": utvonal,
                    "eredmeny": "a tiszta mintában végig letiltva vagy rejtve maradt"
                    + (
                        "; indoklás: "
                        + _LETILTOTT_A_TISZTA_MINTABAN[parancs["nev"]]
                        if parancs["nev"] in _LETILTOTT_A_TISZTA_MINTABAN
                        else ""
                    ),
                    "kep": "",
                    "hiba": parancs["nev"] not in _LETILTOTT_A_TISZTA_MINTABAN,
                }
            )

        _UTAK.append(
            {
                "menu": rovid_nev,
                "magassag": 0,
                "kihagyott": kihagyott,
                "eredmenyek": eredmenyek,
            }
        )
        for ut in eredmenyek:
            if not ut["kep"]:
                continue
            assert Path(str(ut["kep"])).is_file(), (
                f"hiányzik a képernyőkép: {ut['menu']} › {ut['parancs']}"
            )
    assert len(parancsazonositok) == 185, (
        "a menüsorban mért különböző parancsútvonalak száma eltér a 185-től: "
        f"{len(parancsazonositok)}"
    )
    vegso_eredmenyek = {}
    for futas in _UTAK:
        if futas["magassag"] != 0:
            continue
        for eredmeny in futas["eredmenyek"]:
            vegso_eredmenyek[(eredmeny["menu"], tuple(eredmeny.get("utvonal", ())))] = eredmeny
    hibak = [
        f"{eredmeny['menu']} › {eredmeny['parancs']}: {eredmeny['eredmeny']}"
        for eredmeny in vegso_eredmenyek.values()
        if eredmeny.get("hiba")
    ]
    assert not hibak, "a menü-bejárás észlelt hibái:\n" + "\n".join(hibak)


@pytest.mark.parametrize("eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_valodi_menukattintas_ablakmagassag_elteressel(
    tiszta_menuproba, qt_app, eltolas, scratch_jelentes
):
    ablak, vezerlo, _motor, tmp_path, kulsok = tiszta_menuproba
    ablak.setHeight(_ABLAK_ALAPMAGASSAG + eltolas)
    assert _varj(
        qt_app, lambda: ablak.height() == _ABLAK_ALAPMAGASSAG + eltolas
    ), f"az ablak magassága nem állt be a kért {eltolas} px eltérésre"
    menu_bar = ablak.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    menu = _megnyit(menu_bar, qt_app, "View")
    parancs = next(
        parancs
        for parancs in _parancsok(menu, menu_bar)
        if parancs["nev"] == "menuViewProperties"
    )
    eredmeny = _akcio(
        ablak,
        vezerlo,
        tmp_path / "kepek",
        menu_bar,
        qt_app,
        "View",
        parancs,
        tmp_path / "kepernyokepek",
        kulsok,
    )
    _UTAK.append(
        {"menu": "View", "magassag": eltolas, "eredmenyek": [eredmeny]}
    )
    assert not eredmeny["hiba"], (
        f"az ablakmagasság-eltolásos valódi kattintás hibázott: {eredmeny}"
    )
    assert Path(str(eredmeny["kep"])).is_file()


def test_keresesi_parancs_utan_torolje_a_keresot_es_allitsa_vissza_a_mintamappat(
    tiszta_menuproba, qt_app
):
    ablak, vezerlo, _motor, tmp_path, kulsok = tiszta_menuproba
    minta = tmp_path / "kepek"
    vezerlo.selectFolder(str(minta))
    ablak.setProperty("selectedIndexes", [0])
    ablak.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    menu_bar = ablak.property("menuBar")
    tools_menu = _megnyit(menu_bar, qt_app, "&Tools")
    keresesi_parancs = next(
        parancs
        for parancs in _parancsok(tools_menu, menu_bar)
        if parancs["nev"] == "menuToolsSearchRed"
    )
    eredmeny = _akcio(
        ablak,
        vezerlo,
        minta,
        menu_bar,
        qt_app,
        "Tools",
        keresesi_parancs,
        tmp_path / "kepernyokepek",
        kulsok,
    )

    hibasav = ablak.findChild(QObject, "errorBannerText")
    assert hibasav is not None
    assert _szoveg(hibasav, "text") == "", (
        "a színkeresés tájékoztató sávja nyitva maradt a parancs utáni "
        f"visszaállításkor: {eredmeny}"
    )
    assert vezerlo.color_index_fut() is False, (
        "a színkeresés háttérmunkája átnyúlt a következő menüparancsra"
    )
    toolbar = ablak.findChild(QObject, "mainToolbar")
    assert _szoveg(toolbar, "searchText") == "", (
        f"a keresőmező nem ürült ki a parancs után: {eredmeny}"
    )
    assert vezerlo.property("searchActive") is False
    assert vezerlo.property("currentFolder") == str(minta)
    assert not any(menu.property("opened") is True for menu in _menuk(menu_bar))


def test_screensaver_utan_a_backup_parancs_is_elerheto(
    tiszta_menuproba, qt_app
):
    ablak, vezerlo, _motor, tmp_path, kulsok = tiszta_menuproba
    menu_bar = ablak.property("menuBar")
    minta = tmp_path / "kepek"

    tools_menu = _megnyit(menu_bar, qt_app, "&Tools")
    screensaver = next(
        parancs
        for parancs in _parancsok(tools_menu, menu_bar)
        if parancs["nev"] == "menuToolsScreensaver"
    )
    screensaver_eredmeny = _akcio(
        ablak,
        vezerlo,
        minta,
        menu_bar,
        qt_app,
        "Tools",
        screensaver,
        tmp_path / "kepernyokepek",
        kulsok,
    )

    tools_menu = _megnyit(menu_bar, qt_app, "&Tools")
    backup = next(
        parancs
        for parancs in _parancsok(tools_menu, menu_bar)
        if parancs["nev"] == "menuToolsBackup"
    )
    backup_eredmeny = _akcio(
        ablak,
        vezerlo,
        minta,
        menu_bar,
        qt_app,
        "Tools",
        backup,
        tmp_path / "kepernyokepek",
        kulsok,
    )

    assert not screensaver_eredmeny["hiba"], (
        "a Configure Screensaver parancs hatását nem ismerte fel: "
        f"{screensaver_eredmeny}"
    )
    assert "screensaverDialog" in screensaver_eredmeny["eredmeny"]
    assert not backup_eredmeny["hiba"], (
        "a Configure Screensaver után a Back Up Pictures parancs nem nyílt meg: "
        f"{backup_eredmeny}"
    )
    assert "backupHost" in backup_eredmeny["eredmeny"]


@pytest.mark.parametrize("eltolas", (-5, 0, 5))
def test_a_nyelv_almenu_utolso_parancsa_is_kattinthato(
    tiszta_menuproba, qt_app, eltolas
):
    ablak, vezerlo, _motor, tmp_path, kulsok = tiszta_menuproba
    nyelv_magassag = _NYELV_ALMENU_MIN_MAGASSAG + eltolas
    ablak.setHeight(nyelv_magassag)
    assert _varj(qt_app, lambda: ablak.height() == nyelv_magassag)
    menu_bar = ablak.property("menuBar")
    tools_menu = _megnyit(menu_bar, qt_app, "&Tools")
    korean = next(
        parancs
        for parancs in _parancsok(tools_menu, menu_bar)
        if parancs["nev"] == "menuLanguageko"
    )

    eredmeny = _akcio(
        ablak,
        vezerlo,
        tmp_path / "kepek",
        menu_bar,
        qt_app,
        "Tools",
        korean,
        tmp_path / "kepernyokepek",
        kulsok,
    )

    assert not eredmeny["hiba"], (
        "a Language almenü utolsó parancsa nem jutott el a megerősítő "
        f"párbeszédig: {eredmeny}"
    )
    assert "menuLanguageConfirmDialog" in eredmeny["eredmeny"]
