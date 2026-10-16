"""A rács helyi menüinek VALÓDI kattintásos teszt-segédei (#5150, 6. rész).

Minden helyi menü a sorára (mappa, album, személy, fotó, címke) jobbkattintással
nyílik, és a tétel valódi `QTest.mouseClick`-kel indul. Parancsot közvetlenül
nem indítunk: nincs `triggered`/`clicked`/`activated` hívás és nincs `.emit()`.
A hatást a vezérlő állapotán, a lemezen maradt fájlokon vagy a párbeszédek
láthatóságán mérjük. A párbeszédek takarításához a `close` hívás szabad.

A külső programot (fájlkezelő, társított alkalmazás, arcfelismerő) helyettesítjük;
ezt a teszt mindig kimondja.
"""

from __future__ import annotations

from pathlib import Path

import shutil
import shiboken6
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from picasapy.edit.save import ORIGINALS_DIR_NAME
from picasapy.ini import load_document
from picasapy.ini.document import parse_document
from picasapy.ini.priority import olvasd_a_prioritasokat
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    KEPEK,
    MAPPA,
    elokeszit,
)


def varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def vizualis_bejaras(item):
    """A VIZUÁLIS fa bejárása: a delegátumoknak nincs QObject-szülőjük."""
    for gyerek_elem in item.childItems():
        yield gyerek_elem
        yield from vizualis_bejaras(gyerek_elem)


def vizualis(window, nev: str):
    for item in vizualis_bejaras(window.contentItem()):
        if item.objectName() == nev:
            return item
    raise AssertionError(f"{nev} vizuális elem nem található")


def _elem_ablaka(window, elem):
    """Az ablak, amelyben `elem` RAJZOLÓDIK.

    A helyi menük többsége a főablak fájában él, de a fotó-menü
    `popupType: Popup.Window`, tehát külön `QQuickWindow`-ban. A kattintást
    annak az ablaknak kell küldeni, különben a koordináta a rossz ablakba esik.
    A `elem.window()` helyett a nyitott ablakokat járjuk be: a Python-wrapper
    GC-je a `elem.window()` ablakát megsemmisítené (ld. a
    `qml-teszt-python-wrapper-torles` tanulságot)."""
    cel = shiboken6.getCppPointer(elem)[0]
    for ablak in [window, *QGuiApplication.topLevelWindows()]:
        if not isinstance(ablak, QQuickWindow):
            continue
        for item in vizualis_bejaras(ablak.contentItem()):
            if shiboken6.getCppPointer(item)[0] == cel:
                return ablak
    raise AssertionError(f"{elem.objectName()}: az ablaka nem található")


def keres_vizualis_mindenablakban(window, nev: str):
    """Mint a `keres_vizualis`, de a főablak MELLETT a nyitott menü-ablakokban is keres."""
    for ablak in [window, *QGuiApplication.topLevelWindows()]:
        if not isinstance(ablak, QQuickWindow):
            continue
        for item in vizualis_bejaras(ablak.contentItem()):
            if item.objectName() == nev and item.isVisible():
                return item
    return None


def keres_vizualis(window, nev: str):
    """Mint a `vizualis`, de nincs találat esetén `None`-t ad (a sor még nem él)."""
    for item in vizualis_bejaras(window.contentItem()):
        if item.objectName() == nev and item.isVisible():
            return item
    return None


def kattints(window, qt_app, elem, gomb=Qt.MouseButton.LeftButton) -> None:
    """Valódi egérkattintás az elem közepén, a `window` ablakba.

    ⚠️ Az ablakot a hívó adja át, nem az `elem.window()`-ból veszi: a
    Python-wrapper GC után megsemmisítené az ablakot (ld. a
    `qml-teszt-python-wrapper-torles` tanulságot)."""
    assert elem.isVisible() and elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nem látszik / nulla méretű, nem kattintható"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        _elem_ablaka(window, elem),
        gomb,
        Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def kijelolt(window) -> list[int]:
    ertek = window.property("selectedIndexes")
    return sorted(ertek.toVariant() if hasattr(ertek, "toVariant") else ertek)


def kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def almenu_sora(menu, almenu) -> QQuickItem:
    """A szülőmenü azon sora, amely az almenüt nyitja (a címe egyezik)."""
    cim = almenu.property("title")
    pending = [menu.property("contentItem")]
    while pending:
        item = pending.pop()
        if (
            "MenuItem" in item.metaObject().className()
            and item.property("text") == cim
            and not item.objectName()
        ):
            return item
        pending.extend(item.childItems())
    raise AssertionError(f"{cim!r} almenüsora nem található")


def almenu_megnyitasa(window, qt_app, menu, almenu_nev: str) -> None:
    """Valódi kattintással megnyitja a `almenu_nev` almenüt a `menu`-ben."""
    almenu = gyerek(window, almenu_nev)
    kattints(window, qt_app, almenu_sora(menu, almenu))
    assert varj(qt_app, lambda: almenu.property("visible") is True), (
        f"a(z) {almenu_nev} almenü nem nyílt meg a valódi kattintásra"
    )


def zar(qt_app, objektum) -> None:
    """Takarítás: a megnyílt párbeszédet bezárja (a `close` szabad)."""
    QMetaObject.invokeMethod(objektum, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def nyitott(elem) -> bool:
    """Látszik-e a párbeszéd: a `Popup`-alapú (`opened`) és az ablak-alapú
    (`visible`) párbeszédek egyaránt."""
    if elem is None:
        return False
    return elem.property("opened") is True or elem.property("visible") is True


def mappasor(window, path) -> QQuickItem:
    """A bal oldali lapos mappalista sora (az alapállapot).

    Útvonalat `Path`-ként vetünk össze: a felületi út Windowson előreperjeles
    lehet, a `str(Path)` pedig hátrefelé (#5155)."""
    for item in vizualis_bejaras(window.contentItem()):
        if (
            item.objectName() == "folderRowMouse"
            and Path(str(item.property("folderPath"))) == Path(str(path))
        ):
            return item
    raise AssertionError(f"a bal oldali mappasor nem található: {path}")


def jobbklikk_mappan(window, qt_app, path):
    """Valódi jobbklikk a mappasoron; a Mappa-menü megnyílását is megvárjuk."""
    kattints(window, qt_app, mappasor(window, path), Qt.MouseButton.RightButton)
    menu = gyerek(window, "folderContextMenu")
    assert varj(qt_app, lambda: menu.property("visible") is True), (
        "a bal oldali mappasor jobbklikkje nem nyitotta meg a helyi menüt"
    )
    return menu


def jobbklikk_mappalistan(window, qt_app):
    """Valódi jobbklikk a bal panel üres részén: a mappalista menüje."""
    pane = gyerek(window, "folderPane")
    pont = pane.mapToScene(QPointF(pane.width() / 2, pane.height() - 8))
    QTest.mouseClick(
        window,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()
    menu = gyerek(window, "folderListContextMenu")
    assert varj(qt_app, lambda: menu.property("opened") is True), (
        "a bal oldali mappalista üres részén a jobbklikk nem nyitotta meg a menüt"
    )
    return menu


def jobbklikk_fotón(window, qt_app, sor: int):
    """Valódi jobbklikk a `sor` indexű képen; a fotómenü megnyílását is megvárjuk."""
    for item in vizualis_bejaras(window.contentItem()):
        if item.objectName() != "thumbMouseArea":
            continue
        szulo = item
        while szulo is not None and szulo.property("index") is None:
            szulo = szulo.parentItem()
        if szulo is not None and szulo.property("index") == sor:
            kattints(window, qt_app, item, Qt.MouseButton.RightButton)
            break
    else:
        raise AssertionError(f"a {sor}. kép bélyegképe nem található")
    menu = gyerek(window, "photoContextMenu")
    assert varj(qt_app, lambda: menu.property("visible") is True), (
        "a kép jobbklikkje nem nyitotta meg a helyi menüt"
    )
    return menu



# --- közös segédek a rács helyi menü-tesztjeihez (#5150, 6. rész) ---


def cel_utja(controller) -> str:
    return str(Path(str(controller.watchedFolders[0])) / MAPPA)


def egyezik(a, b) -> bool:
    """Útvonalak összevetése `Path`-ként (Windowson a `str` alak eltérhet)."""
    return Path(str(a)) == Path(str(b))


def elokeszit_str(window, qt_app, controller) -> str:
    """Az `elokeszit` str-ként: a QML `folderPath`-jával így vethető össze."""
    return str(elokeszit(window, qt_app, controller))


def ini_sorrend(cel: str) -> list[str]:
    """A mentett sorrend képnevei, helyezés szerint."""
    return [
        nev for nev, _hely in sorted(prioritasok(cel).items(), key=lambda p: p[1])
    ]


def prioritasok(cel: str) -> dict[str, float]:
    """A mappa `.picasa.ini`-jében elmentett sorrend: képnév -> helyezés."""
    ini = Path(cel) / ".picasa.ini"
    if not ini.exists():
        return {}
    return olvasd_a_prioritasokat(parse_document(ini.read_text(encoding="utf-8")))


def sorrend(controller, cel: str) -> list[str]:
    """A `cel` mappa képeinek sorrendje a rácson."""
    return [
        foto.name
        for foto in controller.photos.photos
        if Path(str(foto.folder_path)) == Path(cel)
    ]


def uj_kep(cel: str, nev: str) -> None:
    make_jpeg(Path(cel) / nev, size=(60, 40))


def album_darab(controller, token: str) -> int:
    for album in controller.albums:
        if album["token"] == token:
            return int(album["count"])
    return -1


def foto_utja(controller, sor: int) -> Path:
    return Path(str(controller.photos.filePathAt(sor)))


def ini_ertek(controller, sor: int, kulcs: str) -> str | None:
    """A `sor` képének szakasz-kulcsa a lemezen maradt `.picasa.ini`-ből."""
    foto = controller.photos.photos[sor]
    ini = Path(foto.folder_path) / ".picasa.ini"
    if not ini.exists():
        return None
    szakasz = load_document(ini).section(foto.name)
    return None if szakasz is None else szakasz.get(kulcs)


def mentett_eredetik(controller) -> None:
    """Előkészítés: a képek mentett eredetije (a Save által hagyott másolat), hogy a
    Revert tétel engedélyezett legyen. A mappa betöltése ELŐTT készül, mert a
    menü `hasBackup`-ja a kijelölés-változáskor értékelődik újra."""
    mappa = Path(str(controller.watchedFolders[0])) / MAPPA
    eredeti = mappa / ORIGINALS_DIR_NAME
    eredeti.mkdir(exist_ok=True)
    for nev in KEPEK:
        shutil.copyfile(mappa / nev, eredeti / nev)


def fileops_athelyezo(window):
    """A `moveFolderDialog` két példányából a FILEOPS-é: ennek van `paths`-a
    (a mappapane példányának nincs)."""
    for dialog in window.findChildren(QObject, "moveFolderDialog"):
        if dialog.property("paths") is not None:
            return dialog
    return None
