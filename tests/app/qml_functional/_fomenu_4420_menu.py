"""#4420: a tiszta profil főmenü-parancsainak kattintásos bejárása."""

from __future__ import annotations


import re
import time
from pathlib import Path
from weakref import WeakKeyDictionary

import shiboken6
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest



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
_MENU_UTVONAL_DARAB = {
    "View": 43,
    "Folder": 15,
    "Picture": 20,
    "Edit": 13,
    "Tools": 70,
    "Create": 8,
    "Help": 6,
    "File": 17,
}
assert sum(_MENU_UTVONAL_DARAB.values()) == 192
_VIEW_UTVONAL_DARAB_CSOPORTONKENT = {"egyeb": 30, "mappanezet": 13}
assert sum(_VIEW_UTVONAL_DARAB_CSOPORTONKENT.values()) == _MENU_UTVONAL_DARAB[
    "View"
]
_TOOLS_UTVONAL_DARAB_CSOPORTONKENT = {
    "egyeb": 28,
    "nyelv_elso": 21,
    "nyelv_masodik": 21,
}
assert sum(_TOOLS_UTVONAL_DARAB_CSOPORTONKENT.values()) == _MENU_UTVONAL_DARAB[
    "Tools"
]
#: A három rendszermappa-gyökér: ha a mappa ezen a gépen nem létezik (CI),
#: az eredeti szerint csendben a teljes fára esik vissza (spec 4.6), így
#: nincs látható változás. Létező mappánál a hatást továbbra is megköveteli.
_RENDSZERGYOKER_TETELEK = {
    "menuViewRootMyPictures": ("mypics", "mydocs"),
    "menuViewRootMyDocuments": ("mydocs",),
    "menuViewRootDesktop": ("desktop",),
}


def _rendszergyoker_hianyzik(nev: str) -> bool:
    from picasapy.app.folder_hierarchy_controller import _rendszermappa

    tokenek = _RENDSZERGYOKER_TETELEK.get(nev)
    return bool(tokenek) and not any(_rendszermappa(t) for t in tokenek)


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
    "menuViewLibraryView": (
        "A Könyvtárnézet csak megnyitott néző mellett aktív; a tiszta minta "
        "könyvtárnézetben indul."
    ),
    "menuViewTimeline": (
        "A Timeline funkció ebben a tiszta mintában szándékosan letiltott."
    ),
    "menuViewAlbumThumbnails": (
        "A könyvtári bélyegkép-kapcsoló fanézetben letiltott; a teszt ezt az "
        "állapotot is meghagyja a menüsorban."
    ),
    "menuCreateMovieFromPeopleAlbums": (
        "A tiszta profilban nincs névvel ellátott arc, ezért nincs nem üres "
        "Emberek-albuma."
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
_MENU_ELEMEK: WeakKeyDictionary[QObject, list[QObject]] = WeakKeyDictionary()
_MENU_FEJLECEK: WeakKeyDictionary[QObject, list[QObject]] = WeakKeyDictionary()


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
    if not isinstance(elem, QObject):
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


def _menupont(menu, index: int) -> QQuickItem | None:
    kifejezes = QQmlExpression(
        qmlContext(menu), menu, f"itemAt({index})"
    )
    eredmeny, hiba = kifejezes.evaluate()
    assert not hiba, kifejezes.error()
    assert eredmeny is not None, f"a menü {index}. eleme hiányzik"
    if not isinstance(eredmeny, QObject) or not shiboken6.isValid(eredmeny):
        return None
    if not isinstance(eredmeny, QQuickItem):
        raise TypeError(
            f"a menü {index}. eleme nem QQuickItem: {type(eredmeny).__name__}"
        )
    elem = eredmeny
    _QML_ELEMEK.append(elem)
    return elem


def _menuk(menu_bar) -> list[QObject]:
    # Az app minden QML-próbánál új MenuBar-t épít. A Python `id()` a régi
    # ablak lebontása után újra kiosztható, ezért a gyorsítótár kulcsa az élő
    # QObject legyen, gyenge hivatkozással.
    if menu_bar not in _MENU_ELEMEK:
        _MENU_ELEMEK[menu_bar] = [
            elem
            for elem in menu_bar.findChildren(QObject)
            if shiboken6.isValid(elem) and _menu_e(elem)
        ]
    return [
        elem for elem in _MENU_ELEMEK[menu_bar] if shiboken6.isValid(elem)
    ]


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
        if not isinstance(sor, QObject) or not shiboken6.isValid(sor):
            continue
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
    """A MenuBar közvetlen menüi közül válassza ki a felső menüpontot."""
    jeloltek = []
    for index in range(int(menu_bar.property("count") or 0)):
        kifejezes = QQmlExpression(
            qmlContext(menu_bar), menu_bar, f"menuAt({index})"
        )
        menu, hiba = kifejezes.evaluate()
        assert not hiba, kifejezes.error()
        # a QQmlExpression a menü újraépülése közben QMetaObject-et is adhat
        # QObject helyett (CI-n előjött) — az ilyen találat nem menü
        if (
            isinstance(menu, QObject)
            and shiboken6.isValid(menu)
            and _normalizal(_szoveg(menu, "title")) == _normalizal(cim)
        ):
            jeloltek.append(menu)
    assert len(jeloltek) == 1, f"a felső {cim} menü nem egyértelmű"
    return jeloltek[0]


def _menu_fejlec(menu_bar, cim: str):
    if menu_bar not in _MENU_FEJLECEK:
        _MENU_FEJLECEK[menu_bar] = [
            elem
            for elem in menu_bar.findChildren(QObject)
            if isinstance(elem, QObject)
            and shiboken6.isValid(elem)
            and "MenuBarItem" in elem.metaObject().className()
        ]
    jeloltek = [
        elem
        for elem in _MENU_FEJLECEK[menu_bar]
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
        # A CI-n épp bezáruló ablak helyén néha QMetaObject jön vissza.
        if masik is ablak or not isinstance(masik, QObject):
            continue
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
    # A mappanézet gyökere a menü saját állapota: Képek mappa nélküli
    # gépen (CI) a fa nem változik, a választott gyökér viszont igen.
    mappanezet = ablak.findChild(QObject, "menuViewFolderView")
    if mappanezet is not None:
        for tulajdonsag in ("viewRootToken", "albumThumbsMode"):
            ertek = _ertek(mappanezet.property(tulajdonsag))
            if ertek is not None:
                ablakertekek[f"mappanezet.{tulajdonsag}"] = ertek

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
