#!/usr/bin/env python3
"""A főablak és a PhotoViewer állapotainak képpontos mérője (#5952, #5954).

Főablak-állapotok (`main-library`, `people-album`, `menu-file`, `menu-edit`,
`menu-view`, `menu-folder`, `menu-picture`, `menu-create`, `menu-tools`,
`menu-help`, `toolbar`, `tray`, `slideshow`, `photo-viewer`,
`undo-all-edits`, `drop-geotag`, `mainSplit-min`, `mainSplit-max`): könyvtár
mappákkal és albummal; személyalbum (Emberek nézet); a Fájl, Szerkesztés,
Nézet, Mappa, Kép, Létrehozás, Eszközök és Súgó menü nyitva; eszköztár;
megtöltött tálca; a főablakból indított diavetítés; a főablakból megnyitott
fotónéző; Minden szerkesztés visszavonása párbeszéd; földrajzi címkés behúzás
párbeszéd; a fő osztott nézet minimum- és maximumszélessége. A két
visszavonási QML-azonosító (`undoAllEditsDialog`,
`undoAllEditsConfirmDialog`) ugyanazt az egy `Dialog`-példányt jelöli: a
halasztott betöltő és a látható megerősítő párbeszéd együtt kerül a képbe.
Hasonlóan a földrajzi párbeszéd betöltője és látható `Dialog` egy állapot.

PhotoViewer-állapotok (`alapnezet`, `bal-fiok-nyitva`, `filmcsik`,
`szerkeszto-0`…`szerkeszto-6`, `arcreteg`, `teljes-kepernyo`): alapnézet
(bal fiók csukva); bal fiók nyitva; filmszalag; szerkesztőpanel mind a hét füle (Gyakori javítások,
Finomhangolás, Effektek, Kreatív, Művészi, További effektek, Régi effektek);
arcréteg; teljes képernyő. Minden állapotot a
`tests/app/qml_functional/conftest.py` közös `_build_qml_app` építője állít
elő, azonos szintetikus fotókkal, rögzített mtime-mal és elszigetelt
beállításokkal. A fotónéző képszolgáltatós képe a három egyező kockából
álló korábbi mintánál későbbi kockán is megváltozott (egy megfigyelésben
18 pixel frissült). A képrögzítés ezért határidőig várja, hogy tíz
egymást követő ablakkép azonos legyen. Kihagyott állapot nincs.

Használat:
    python scripts/photo_viewer_screenshots.py capture --output /tmp/nezokep
    python scripts/photo_viewer_screenshots.py compare --before /tmp/elotte \
        --after /tmp/utana --diff-dir /tmp/elteresek
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any

import numpy as np


GYOKER = Path(__file__).resolve().parents[1]
_ALBUM_TOKEN = "604c294a68b0de9cc9222c4714f289d5"
_PERSON_ID = "0123456789abcdef"
_PERSON_NAME = "Teszt Elek"
_FACE_RECT = (0.18, 0.16, 0.62, 0.69)
_MINTA_MTIME = 1_577_836_800
_MAIN_MENU_STATES = (
    ("menu-file", "&File", "menuFileAddFolder"),
    ("menu-edit", "&Edit", "menuEditCut"),
    ("menu-view", "&View", "menuViewLibraryView"),
    ("menu-folder", "F&older", "menuFolderSlideshow"),
    ("menu-picture", "&Picture", "menuPictureViewAndEdit"),
    ("menu-create", "&Create", "menuCreateCollage"),
    ("menu-tools", "&Tools", "menuToolsFolderManager"),
    ("menu-help", "&Help", "menuHelpContents"),
)
MAIN_ALLAPOT_NEVEK = (
    "main-library",
    "people-album",
    *(name for name, _title, _item in _MAIN_MENU_STATES),
    "toolbar",
    "tray",
    "slideshow",
    "undo-all-edits",
    "drop-geotag",
    "mainSplit-min",
    "mainSplit-max",
    "photo-viewer",
)
PHOTO_VIEWER_ALLAPOT_NEVEK = (
    "alapnezet",
    "bal-fiok-nyitva",
    "filmcsik",
    *(f"szerkeszto-{index}" for index in range(7)),
    "arcreteg",
    "teljes-kepernyo",
)
ALLAPOT_NEVEK = (*MAIN_ALLAPOT_NEVEK, *PHOTO_VIEWER_ALLAPOT_NEVEK)
_AKTIV_FUL_OBJEKTUMOK = (
    "editTabFixes",
    "editTabFinetune",
    "editTabEffects",
    "editTabEffects2",
    "editTabEffects3",
    "editTabEffects4",
    "editTabLegacy",
)
_KERET_SZIN = (255, 0, 255, 255)
_STABIL_KOCKAK = 3
_STABIL_KEPKOCKAK = 10
_STABIL_KEPKOCKAK_KOZTI_VARAKOZAS_MP = 0.02
_ALAPNEZET_KEPKOCKAK_KOZTI_VARAKOZAS_MP = 0.05
_STABIL_HATARIDO_MP = 8.0
_ALLAPOT_HATARIDO_MP = 8.0


@dataclass(frozen=True)
class Allapot:
    nev: str
    nyitott_fiok: bool
    aktiv_ful: int | None = None
    arc_reteg: bool = False
    teljes_kepernyo: bool = False


ALLAPOTOK = (
    Allapot("alapnezet", nyitott_fiok=False),
    Allapot("bal-fiok-nyitva", nyitott_fiok=True),
    Allapot("filmcsik", nyitott_fiok=False),
    *(Allapot(f"szerkeszto-{index}", nyitott_fiok=True, aktiv_ful=index)
      for index in range(7)),
    Allapot("arcreteg", nyitott_fiok=False, arc_reteg=True),
    Allapot("teljes-kepernyo", nyitott_fiok=False, teljes_kepernyo=True),
)


def _elem(ablak: Any, nev: str) -> Any:
    from PySide6.QtCore import QObject

    elem = ablak.findChild(QObject, nev)
    if elem is None:
        raise RuntimeError(f"A QML-ablakból hiányzik a(z) {nev!r} objektum.")
    return elem


def _var_feltetelre(alkalmazas: Any, feltetel, leiras: str, hatarido: float) -> None:
    vege = time.monotonic() + hatarido
    while time.monotonic() < vege:
        alkalmazas.processEvents()
        if feltetel():
            return
        time.sleep(0.02)
    raise RuntimeError(f"Időtúllépés: {leiras}.")


def _var_stabil_ertekre(
    alkalmazas: Any, olvas, leiras: str, hatarido: float
) -> Any:
    """Három egymást követő eseményciklusban azonos geometriára vár."""
    vege = time.monotonic() + hatarido
    elozo = object()
    azonos = 0
    while time.monotonic() < vege:
        alkalmazas.processEvents()
        ertek = olvas()
        azonos = azonos + 1 if ertek == elozo else 1
        if azonos >= _STABIL_KOCKAK:
            return ertek
        elozo = ertek
        time.sleep(0.05)
    raise RuntimeError(f"Időtúllépés: nem stabil a(z) {leiras}.")


def _minta_kepek(lib: Path) -> None:
    """Képeket, almappát, albumot és személyalbumot készít a méréshez."""
    from support.jpeg_factory import make_minta_jpeg
    from picasapy.ini import parse_document, update_document
    from picasapy.ini.albums import with_album
    from picasapy.ini.contacts import Contact, with_contact
    from picasapy.ini.faces import Face, with_face
    from picasapy.ini.rect64 import Rect64

    fajlok = (
        (lib / "a.jpg", (640, 400), 0),
        (lib / "b.jpg", (480, 360), 1),
    )
    for ut, meret, seed in fajlok:
        make_minta_jpeg(ut, size=meret, seed=seed)
    almappa = lib / "Almappa"
    almappa.mkdir()
    almappakep = almappa / "c.jpg"
    make_minta_jpeg(almappakep, size=(320, 240), seed=2)

    arc = Face(Rect64(*_FACE_RECT), _PERSON_ID)

    def _metaadatok(_elozo):
        dokumentum = parse_document("")
        dokumentum = dokumentum.with_value(
            f".album:{_ALBUM_TOKEN}", "name", "Screenshot mérőalbum"
        )
        dokumentum = dokumentum.with_value(
            f".album:{_ALBUM_TOKEN}", "token", _ALBUM_TOKEN
        )
        dokumentum = with_album(dokumentum, "a.jpg", _ALBUM_TOKEN)
        dokumentum = with_contact(
            dokumentum, Contact(_PERSON_ID, _PERSON_NAME, "", "")
        )
        dokumentum = with_face(dokumentum, "a.jpg", arc)
        return with_face(dokumentum, "b.jpg", arc)

    update_document(lib / ".picasa.ini", _metaadatok, backup=False)
    # Az ini-író a Picasa frissítési jelzése miatt megérinti az érintett
    # fotókat. Az összes minta mtime-ját csak a metaadatok mentése után
    # rögzítjük, mert az alsó adatsor a fájl idejét is kirajzolja.
    for ut in (lib / "a.jpg", lib / "b.jpg", almappakep):
        os.utime(ut, (_MINTA_MTIME, _MINTA_MTIME))


def _kep_bajtok(kep: Any) -> bytes:
    from PySide6.QtGui import QImage

    rgba = kep.convertToFormat(QImage.Format.Format_RGBA8888)
    return bytes(rgba.constBits())


def _hatter_dolgozik() -> bool:
    """Fut-e nyilvántartott háttérmunka (pl. az `editpreview` renderje, #6078).

    A nézőkép végleges kockáját háttérszál számolja; a lassabb CI-gépen ez a
    stabil-kocka ablakon túl érkezett, és két rögzítés 16 képpontban eltért."""
    from picasapy.app.worker_thread import running_background_workers

    return bool(running_background_workers())


def _stabil_ablakkepernyo(ablak: Any, alkalmazas: Any, allapot: str) -> Any:
    """Határidővel vár tíz változatlan QImage-kockára.

    A `editpreview` képszolgáltatós kép egy megfigyelésben a korábbi
    háromkockás mintavétel után 18 pixelt frissített; tíz azonos kocka ezt
    a késői képet is megvárja. Az `alapnezet` állapot 50 ms-os mintaköze
    450 ms-nyi stabil képet hagy; a többi állapot 20 ms-os közt használ.
    Mindegyik állapot tíz egyező képkockát igényel.
    """
    elozo: bytes | None = None
    azonos = 0
    vege = time.monotonic() + _STABIL_HATARIDO_MP
    mintakoz = (
        _ALAPNEZET_KEPKOCKAK_KOZTI_VARAKOZAS_MP
        if allapot == "alapnezet"
        else _STABIL_KEPKOCKAK_KOZTI_VARAKOZAS_MP
    )
    while time.monotonic() < vege:
        alkalmazas.processEvents()
        kep = ablak.grabWindow()
        if _hatter_dolgozik():
            # futó render alatt a kép még változhat: a számlálás újraindul
            elozo = None
            azonos = 0
        elif kep.isNull():
            azonos = 0
        else:
            bajtok = _kep_bajtok(kep)
            azonos = azonos + 1 if bajtok == elozo else 1
            if azonos >= _STABIL_KEPKOCKAK:
                return kep.copy()
            elozo = bajtok
        time.sleep(mintakoz)
    raise RuntimeError(
        f"A(z) {allapot!r} állapot képe nem stabilizálódott "
        f"{_STABIL_HATARIDO_MP:g} másodpercen belül."
    )


def _objektum_lathato(elem: Any) -> bool:
    lathato_metodus = getattr(elem, "isVisible", None)
    if callable(lathato_metodus):
        return bool(lathato_metodus())
    return bool(elem.property("visible"))


def _lathato_objektumok(ablak: Any, nevek: tuple[str, ...]) -> list[str]:
    from PySide6.QtCore import QObject

    lathatok = []
    hianyzok = []
    for nev in nevek:
        elem = ablak.findChild(QObject, nev)
        if elem is not None and _objektum_lathato(elem):
            lathatok.append(nev)
        else:
            hianyzok.append(nev)
    if hianyzok:
        raise RuntimeError(
            "A képkockában nem látható kulcsobjektum(ok): "
            + ", ".join(hianyzok)
        )
    return lathatok


def _allapot_mentese(
    *,
    nev: str,
    objektumok: tuple[str, ...],
    ablak: Any,
    alkalmazas: Any,
    output: Path,
    reszletek: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lathato = _lathato_objektumok(ablak, objektumok)
    kep = _stabil_ablakkepernyo(ablak, alkalmazas, nev)
    fajl = f"{nev}.png"
    cel = output / fajl
    if not kep.save(str(cel), "PNG"):
        raise RuntimeError(f"Nem sikerült elmenteni: {cel}")
    rekord: dict[str, Any] = {
        "name": nev,
        "file": fajl,
        "width": kep.width(),
        "height": kep.height(),
        "window_size": {"width": ablak.width(), "height": ablak.height()},
        "visible_object_names": lathato,
    }
    if reszletek:
        rekord.update(reszletek)
    if nev in {"main-library", "people-album"}:
        rekord["thumbnail_sampled_colors"] = _thumbnail_sampled_colors(ablak, kep)
    return rekord


def _thumbnail_sampled_colors(ablak: Any, kep: Any) -> int:
    """A látható fotó-bélyegképekből vett mintapontok egyedi színeinek száma."""
    from PySide6.QtCore import QPointF

    mintak = set()
    varakozo = [ablak.contentItem()]
    while varakozo:
        item = varakozo.pop()
        varakozo.extend(item.childItems())
        if item.objectName() != "thumbImage":
            continue
        image = item
        if not _objektum_lathato(image):
            continue
        festett_szel = float(image.property("paintedWidth"))
        festett_mag = float(image.property("paintedHeight"))
        if festett_szel <= 0 or festett_mag <= 0:
            continue
        keret_szel = float(image.property("width"))
        keret_mag = float(image.property("height"))
        for fx, fy in ((0.2, 0.2), (0.5, 0.5), (0.8, 0.8)):
            helyi = QPointF(
                (keret_szel - festett_szel) / 2 + festett_szel * fx,
                (keret_mag - festett_mag) / 2 + festett_mag * fy,
            )
            jelenet = image.mapToScene(helyi)
            x = round(jelenet.x() * kep.width() / ablak.width())
            y = round(jelenet.y() * kep.height() / ablak.height())
            if 0 <= x < kep.width() and 0 <= y < kep.height():
                mintak.add(kep.pixelColor(x, y).rgba())
    return len(mintak)


def _foablak_menu(ablak: Any, cim: str) -> Any:
    from PySide6.QtCore import QObject

    for elem in ablak.findChildren(QObject):
        if elem.property("title") == cim:
            return elem
    raise RuntimeError(f"A főablak {cim!r} menüje nem található.")


def _foablak_allapotok(
    *,
    ablak: Any,
    alkalmazas: Any,
    vezerlo: Any,
    lib: Path,
    output: Path,
    requested_width: int,
    requested_height: int,
) -> list[dict[str, Any]]:
    from PySide6.QtGui import QWindow

    records: list[dict[str, Any]] = []
    viewer = _elem(ablak, "photoViewer")
    slideshow = _elem(ablak, "slideshowView")
    folder_list = _elem(ablak, "folderListView")
    album_repeater = _elem(ablak, "albumRepeater")
    if slideshow.isVisible():
        slideshow.stop()
    if ablak.visibility() == QWindow.Visibility.FullScreen:
        ablak.setProperty("visibility", QWindow.Visibility.Windowed)
    if viewer.isVisible():
        ablak.setProperty("viewerOpen", False)

    _var_feltetelre(
        alkalmazas,
        lambda: int(folder_list.property("count")) > 0
        and int(album_repeater.property("count")) > 0
        and not bool(getattr(vezerlo, "_sync_running", False)),
        "a mappa- és albumlista betöltése",
        _ALLAPOT_HATARIDO_MP,
    )
    vezerlo.selectFolder(str(lib))
    library_photo_index = int(vezerlo.photos.rowOfPath(str(lib / "a.jpg")))
    if library_photo_index < 0:
        raise RuntimeError("A fő könyvtár mintaképe nem található a fotófeedben.")
    ablak.setProperty("selectedIndex", library_photo_index)
    ablak.setProperty("selectedIndexes", [library_photo_index])
    _var_feltetelre(
        alkalmazas,
        lambda: ablak.isVisible()
        and not viewer.isVisible()
        and not slideshow.isVisible()
        and vezerlo.currentFolder == str(lib)
        and vezerlo.photos.rowCount() > 0,
        "a főablak könyvtárnézete",
        _ALLAPOT_HATARIDO_MP,
    )

    records.append(
        _allapot_mentese(
            nev="main-library",
            objektumok=(
                "mainSplit",
                "folderPane",
                "folderListView",
                "albumRepeater",
                "photoGrid",
            ),
            ablak=ablak,
            alkalmazas=alkalmazas,
            output=output,
            reszletek={
                "folder_count": int(folder_list.property("count")),
                "album_count": int(album_repeater.property("count")),
            },
        )
    )

    vezerlo.showPerson(_PERSON_NAME)
    person_name = _elem(ablak, "personAlbumName")
    person_header = _elem(ablak, "personAlbumHeader")
    face_strip = _elem(ablak, "personAlbumFaceStrip")
    person_avatar = _elem(ablak, "personAlbumAvatar")
    _var_feltetelre(
        alkalmazas,
        lambda: vezerlo.currentPersonName == _PERSON_NAME
        and person_header.isVisible()
        and person_name.property("text") == _PERSON_NAME
        and int(face_strip.property("count")) > 0
        and person_avatar.property("imageReady"),
        "az Emberek személyalbumának megjelenése",
        _ALLAPOT_HATARIDO_MP,
    )
    records.append(
        _allapot_mentese(
            nev="people-album",
            objektumok=(
                "mainSplit",
                "folderPane",
                "personAlbumHeader",
                "personAlbumName",
                "personAlbumFaceStrip",
                "photoGrid",
            ),
            ablak=ablak,
            alkalmazas=alkalmazas,
            output=output,
            reszletek={"person_name": vezerlo.currentPersonName},
        )
    )

    vezerlo.selectFolder(str(lib))
    library_photo_index = int(vezerlo.photos.rowOfPath(str(lib / "a.jpg")))
    if library_photo_index < 0:
        raise RuntimeError("Visszatéréskor a fő könyvtár mintaképe nem található.")
    ablak.setProperty("selectedIndex", library_photo_index)
    ablak.setProperty("selectedIndexes", [library_photo_index])
    _var_feltetelre(
        alkalmazas,
        lambda: vezerlo.currentAlbumToken == ""
        and vezerlo.currentPersonName == ""
        and not viewer.isVisible(),
        "visszatérés a könyvtárnézethez",
        _ALLAPOT_HATARIDO_MP,
    )

    for nev, cim, menu_tetel in _MAIN_MENU_STATES:
        menu = _foablak_menu(ablak, cim)
        menu_item = _elem(ablak, menu_tetel)
        menu.open()
        _var_feltetelre(
            alkalmazas,
            lambda m=menu, item=menu_item: bool(m.property("visible"))
            and _objektum_lathato(item),
            f"a {cim} főmenü megnyitása",
            _ALLAPOT_HATARIDO_MP,
        )
        records.append(
            _allapot_mentese(
                nev=nev,
                objektumok=(menu_tetel,),
                ablak=ablak,
                alkalmazas=alkalmazas,
                output=output,
                reszletek={"menu_title": cim},
            )
        )
        menu.close()
        _var_feltetelre(
            alkalmazas,
            lambda m=menu: not bool(m.property("visible")),
            f"a {cim} főmenü bezárása",
            _ALLAPOT_HATARIDO_MP,
        )

    toolbar = _elem(ablak, "mainToolbar")
    records.append(
        _allapot_mentese(
            nev="toolbar",
            objektumok=("mainToolbar", "toolbarImportButton"),
            ablak=ablak,
            alkalmazas=alkalmazas,
            output=output,
            reszletek={"toolbar_visible": toolbar.isVisible()},
        )
    )

    vezerlo.holdRows([0, 1])
    tray = _elem(ablak, "trayBar")
    tray_repeater = _elem(ablak, "trayPreviewRepeater")
    _var_feltetelre(
        alkalmazas,
        lambda: tray.isVisible()
        and int(tray_repeater.property("count")) > 0
        and len(vezerlo.trayItems) > 0,
        "a kijelölt képek megjelenése a tálcán",
        _ALLAPOT_HATARIDO_MP,
    )
    records.append(
        _allapot_mentese(
            nev="tray",
            objektumok=("trayBar", "trayMainBar", "trayStarButton"),
            ablak=ablak,
            alkalmazas=alkalmazas,
            output=output,
            reszletek={"tray_item_count": len(vezerlo.trayItems)},
        )
    )

    ablak.startSlideshow(-1)
    slideshow_image = _elem(ablak, "slideshowImage")
    _var_feltetelre(
        alkalmazas,
        lambda: slideshow.isVisible()
        and int(slideshow.property("currentIndex")) >= 0
        and float(slideshow_image.property("paintedWidth")) > 0,
        "a főablakból indított diavetítés képe",
        _ALLAPOT_HATARIDO_MP,
    )
    records.append(
        _allapot_mentese(
            nev="slideshow",
            objektumok=("slideshowView", "slideshowImage"),
            ablak=ablak,
            alkalmazas=alkalmazas,
            output=output,
            reszletek={
                "current_index": int(slideshow.property("currentIndex")),
                "fullscreen": ablak.visibility() == QWindow.Visibility.FullScreen,
            },
        )
    )
    slideshow.stop()
    _var_feltetelre(
        alkalmazas,
        lambda: not slideshow.isVisible()
        and ablak.visibility() != QWindow.Visibility.FullScreen,
        "a diavetítés lezárása",
        _ALLAPOT_HATARIDO_MP,
    )

    undo_loader = _elem(ablak, "undoAllEditsDialogLoader")
    undo_dialog = undo_loader.ensure()
    if undo_dialog is None:
        raise RuntimeError("A Minden szerkesztés visszavonása párbeszéd nem jött létre.")
    undo_dialog.openForLibrary([0])
    undo_dialog_obj = _elem(ablak, "undoAllEditsDialog")
    _var_feltetelre(
        alkalmazas,
        lambda: bool(undo_dialog_obj.property("visible")),
        "a Minden szerkesztés visszavonása párbeszéd",
        _ALLAPOT_HATARIDO_MP,
    )
    records.append(
        _allapot_mentese(
            nev="undo-all-edits",
            objektumok=("undoAllEditsDialogLoader", "undoAllEditsDialog"),
            ablak=ablak,
            alkalmazas=alkalmazas,
            output=output,
            reszletek={"selected_row_count": 1},
        )
    )
    undo_dialog.close()

    drop_loader = _elem(ablak, "dropGeotagDialogLoader")
    drop_dialog = drop_loader.ensure()
    if drop_dialog is None:
        raise RuntimeError("A földrajzi címkés behúzás párbeszéd nem jött létre.")
    drop_dialog.futtasd([0], 47.5, 19.0)
    drop_dialog_obj = _elem(ablak, "dropGeotagConfirm")
    _var_feltetelre(
        alkalmazas,
        lambda: bool(drop_dialog_obj.property("visible"))
        and bool(_elem(ablak, "dropGeotagMessage").property("text")),
        "a földrajzi címkés behúzás párbeszéd",
        _ALLAPOT_HATARIDO_MP,
    )
    records.append(
        _allapot_mentese(
            nev="drop-geotag",
            objektumok=("dropGeotagDialogLoader", "dropGeotagConfirm"),
            ablak=ablak,
            alkalmazas=alkalmazas,
            output=output,
            reszletek={"selected_row_count": 1},
        )
    )
    drop_dialog.close()

    split = _elem(ablak, "mainSplit")
    pane = _elem(ablak, "folderPane")
    target_width = max(240, float(split.property("width")) - 240)
    vezerlo.setFolderPaneWidth(240)
    _var_feltetelre(
        alkalmazas,
        lambda: abs(float(pane.property("width")) - 240) <= 1,
        "a mainSplit minimális szélessége",
        _ALLAPOT_HATARIDO_MP,
    )
    records.append(
        _allapot_mentese(
            nev="mainSplit-min",
            objektumok=("mainSplit", "folderPane", "photoGrid"),
            ablak=ablak,
            alkalmazas=alkalmazas,
            output=output,
            reszletek={
                "folder_pane_width": float(pane.property("width")),
                "main_split_width": float(split.property("width")),
            },
        )
    )
    vezerlo.setFolderPaneWidth(int(round(target_width)))
    _var_feltetelre(
        alkalmazas,
        lambda: abs(float(pane.property("width")) - target_width) <= 3,
        "a mainSplit maximális szélessége",
        _ALLAPOT_HATARIDO_MP,
    )
    records.append(
        _allapot_mentese(
            nev="mainSplit-max",
            objektumok=("mainSplit", "folderPane", "photoGrid"),
            ablak=ablak,
            alkalmazas=alkalmazas,
            output=output,
            reszletek={
                "folder_pane_width": float(pane.property("width")),
                "main_split_width": float(split.property("width")),
            },
        )
    )

    # Ugyanazt a megnyitott PhotoViewer-alapnézetet rögzítjük, amelyből
    # közvetlenül utána indul a 12 régi nézőállapot. A bezárás és újranyitás
    # 16 képpontot változtatott a fotó szélén két azonos mérés között.
    ablak.setProperty("visibility", QWindow.Visibility.Windowed)
    ablak.resize(requested_width, requested_height)
    vezerlo.setViewerFullscreenStartup(False)
    viewer_row = int(vezerlo.photos.rowOfPath(str(lib / "a.jpg")))
    if viewer_row < 0:
        raise RuntimeError("A fő könyvtár mintaképe nem nyitható meg a fotónézőben.")
    ablak.openPhotoViewer(viewer_row)
    viewer_image = _elem(ablak, "viewerImage")
    _var_feltetelre(
        alkalmazas,
        lambda: viewer.isVisible()
        and float(viewer_image.property("paintedWidth")) > 0,
        "a fotónéző megnyitása a főablakból",
        _ALLAPOT_HATARIDO_MP,
    )
    panel = _elem(ablak, "viewerEditorPanel")
    _allapot_beallitasa(
        ALLAPOTOK[0],
        ablak=ablak,
        alkalmazas=alkalmazas,
        vezerlo=vezerlo,
        viewer=viewer,
        panel=panel,
    )
    return records


def _allapot_beallitasa(
    allapot: Allapot,
    *,
    ablak: Any,
    alkalmazas: Any,
    vezerlo: Any,
    viewer: Any,
    panel: Any,
) -> None:
    from PySide6.QtCore import QMetaObject
    from PySide6.QtGui import QWindow

    if ablak.visibility() == QWindow.Visibility.FullScreen:
        ablak.setProperty("visibility", QWindow.Visibility.Windowed)
    viewer.setProperty("facesEditMode", False)
    viewer.setProperty("facesVisible", False)
    vezerlo.setEditorControlsVisible(allapot.nyitott_fiok)
    if allapot.aktiv_ful is not None:
        panel.setProperty("activeTab", allapot.aktiv_ful)
    viewer.setProperty("facesVisible", allapot.arc_reteg)
    if allapot.arc_reteg:
        viewer.setProperty(
            "facesEditRevision", int(viewer.property("facesEditRevision")) + 1
        )
    if allapot.teljes_kepernyo:
        if not QMetaObject.invokeMethod(ablak, "toggleViewerFullscreen"):
            raise RuntimeError("A főablak teljes képernyős kapcsolója nem hívható.")
    _var_feltetelre(
        alkalmazas,
        lambda: ablak.isVisible()
        and viewer.isVisible()
        and _teljes_kepernyo(ablak) == allapot.teljes_kepernyo
        and bool(_elem(ablak, "viewerPhotoArea").isVisible())
        and float(_elem(ablak, "viewerImage").property("paintedWidth")) > 0,
        f"a(z) {allapot.nev} állapot megjelenése",
        _ALLAPOT_HATARIDO_MP,
    )
    if allapot.aktiv_ful is not None:
        _var_feltetelre(
            alkalmazas,
            lambda: int(panel.property("activeTab")) == allapot.aktiv_ful,
            f"a(z) {allapot.nev} fülváltása",
            _ALLAPOT_HATARIDO_MP,
        )
    if allapot.arc_reteg:
        overlay = _elem(ablak, "facesOverlay")
        _var_feltetelre(
            alkalmazas,
            lambda: overlay.isVisible() and len(overlay.property("faces")) > 0,
            "a mentett arcréteg megjelenése",
            _ALLAPOT_HATARIDO_MP,
        )

    if not QMetaObject.invokeMethod(viewer, "zoomFit"):
        raise RuntimeError("A fotónéző illesztett nagyítása nem állítható be.")
    drawer = _elem(ablak, "viewerLeftDrawer")
    drawer_width = float(
        _var_stabil_ertekre(
            alkalmazas,
            lambda: round(float(drawer.property("width")), 3),
            "bal fiók geometriája",
            _ALLAPOT_HATARIDO_MP,
        )
    )
    if allapot.nyitott_fiok and drawer_width < 200:
        raise RuntimeError("A bal fiók nem érte el a nyitott szélességét.")
    if not allapot.nyitott_fiok and drawer_width > 2:
        raise RuntimeError("A bal fiók nem záródott be.")

    area = _elem(ablak, "viewerPhotoArea")
    image = _elem(ablak, "viewerImage")
    zoom = _elem(ablak, "zoomSlider")

    def _nezo_geometria():
        elemek = (area, image)
        return tuple(
            round(float(elem.property(tulajdonsag)), 3)
            for elem in elemek
            for tulajdonsag in ("x", "y", "width", "height")
        ) + (
            round(float(image.property("paintedWidth")), 3),
            round(float(image.property("paintedHeight")), 3),
            round(float(zoom.property("value")), 4),
            round(float(zoom.property("visualPosition")), 4),
        )

    _var_stabil_ertekre(
        alkalmazas,
        _nezo_geometria,
        f"a(z) {allapot.nev} kép- és nagyításgeometriája",
        _ALLAPOT_HATARIDO_MP,
    )


def _teljes_kepernyo(ablak: Any) -> bool:
    from PySide6.QtGui import QWindow

    return ablak.visibility() == QWindow.Visibility.FullScreen


def _nezo_geometria(ablak: Any) -> dict[str, Any]:
    from PySide6.QtCore import QPointF, QObject

    adatok: dict[str, Any] = {}
    for nev in ("viewerPhotoArea", "viewerImage", "viewerLeftDrawer", "zoomSlider"):
        elem = ablak.findChild(QObject, nev)
        if elem is None:
            continue
        mezo_nevek = ["x", "y", "width", "height"]
        if nev == "viewerImage":
            mezo_nevek.extend(("paintedWidth", "paintedHeight", "scale", "rotation"))
        if nev == "viewerLeftDrawer":
            mezo_nevek = ["x", "y", "width", "height"]
        if nev == "zoomSlider":
            mezo_nevek.extend(("value", "visualPosition"))
        adat = {
            mezo: round(float(elem.property(mezo)), 6)
            for mezo in mezo_nevek
        }
        if nev in {"viewerPhotoArea", "viewerImage"}:
            pont = elem.mapToScene(QPointF(0, 0))
            adat["scene_x"] = round(float(pont.x()), 6)
            adat["scene_y"] = round(float(pont.y()), 6)
        adatok[nev] = adat
    return adatok


def _kulcsobjektumok(allapot: Allapot) -> tuple[str, ...]:
    nevek = ["photoViewer", "viewerPhotoArea", "viewerImage"]
    if allapot.nyitott_fiok:
        nevek.extend(("viewerLeftDrawer", "viewerEditorPanel"))
    if allapot.aktiv_ful is not None:
        nevek.append(_AKTIV_FUL_OBJEKTUMOK[allapot.aktiv_ful])
    if allapot.nev == "filmcsik":
        nevek.append("viewerFilmstrip")
    if allapot.arc_reteg:
        nevek.append("facesOverlay")
    return tuple(nevek)


def _felvetel(ablak: Any, alkalmazas: Any, vezerlo: Any, output: Path,
              keresett_szel: int, keresett_mag: int) -> dict[str, Any]:
    viewer = _elem(ablak, "photoViewer")
    panel = _elem(ablak, "viewerEditorPanel")
    ablakmeret = {"width": ablak.width(), "height": ablak.height()}
    records: list[dict[str, Any]] = []
    for allapot in ALLAPOTOK:
        _allapot_beallitasa(
            allapot,
            ablak=ablak,
            alkalmazas=alkalmazas,
            vezerlo=vezerlo,
            viewer=viewer,
            panel=panel,
        )
        lathato = _lathato_objektumok(ablak, _kulcsobjektumok(allapot))
        kep = _stabil_ablakkepernyo(ablak, alkalmazas, allapot.nev)
        fajl = f"{allapot.nev}.png"
        cel = output / fajl
        if not kep.save(str(cel), "PNG"):
            raise RuntimeError(f"Nem sikerült elmenteni: {cel}")
        overlay = _elem(ablak, "facesOverlay")
        records.append(
            {
                "name": allapot.nev,
                "file": fajl,
                "width": kep.width(),
                "height": kep.height(),
                "window_size": {"width": ablak.width(), "height": ablak.height()},
                "visible_object_names": lathato,
                "active_tab": int(panel.property("activeTab"))
                if allapot.aktiv_ful is not None
                else None,
                "left_drawer_width": float(
                    _elem(ablak, "viewerLeftDrawer").property("width")
                ),
                "filmstrip_count": int(
                    _elem(ablak, "viewerFilmstrip").property("count")
                ),
                "face_count": len(overlay.property("faces"))
                if allapot.arc_reteg
                else 0,
                "fullscreen": _teljes_kepernyo(ablak),
                "viewer_geometry": _nezo_geometria(ablak),
            }
        )
    return {
        "requested_size": {"width": keresett_szel, "height": keresett_mag},
        "actual_window_size": ablakmeret,
        "states": records,
    }


def capture(output: Path, width: int, height: int) -> dict[str, Any]:
    """Felépíti a fixture appot, és a főablak, illetve a néző képeit menti."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["QT_QUICK_BACKEND"] = "software"
    if str(GYOKER / "src") not in sys.path:
        sys.path.insert(0, str(GYOKER / "src"))
    if str(GYOKER / "tests") not in sys.path:
        sys.path.insert(0, str(GYOKER / "tests"))

    from PySide6.QtGui import QGuiApplication
    from app.qml_functional.conftest import _build_qml_app

    alkalmazas = QGuiApplication.instance() or QGuiApplication(["picasapy-screenshot"])
    with tempfile.TemporaryDirectory(prefix="picasapy-window-5954-") as ideiglenes:
        gyoker = Path(ideiglenes)
        generator = _build_qml_app(
            alkalmazas,
            gyoker,
            kepeket_keszit=_minta_kepek,
            belyegkep_meret=256,
            valodi_belyegkep=True,
        )
        ablak, vezerlo, _engine = next(generator)
        try:
            vezerlo.setUITransitionsEnabled(False)
            ablak.resize(width, height)
            ablak.show()
            ablak.requestActivate()
            _var_feltetelre(
                alkalmazas,
                lambda: ablak.isVisible()
                and not _elem(ablak, "photoViewer").isVisible()
                and _elem(ablak, "mainSplit").isVisible(),
                "a főablak könyvtárnézetének megjelenése",
                _ALLAPOT_HATARIDO_MP,
            )
            output.mkdir(parents=True, exist_ok=True)
            main_records = _foablak_allapotok(
                ablak=ablak,
                alkalmazas=alkalmazas,
                vezerlo=vezerlo,
                lib=gyoker / "kepek",
                output=output,
                requested_width=width,
                requested_height=height,
            )
            viewer_manifest = _felvetel(
                ablak, alkalmazas, vezerlo, output, width, height
            )
            # A főablakból megnyitott fotónéző és a régi alapnézet ugyanaz az
            # egy QML-állapot. A második PNG-t ugyanabból a rögzített QImage-ből
            # adjuk, nem készítünk egy fölösleges új képkockát.
            alapnezet = viewer_manifest["states"][0]
            photo_viewer_record = {
                **alapnezet,
                "name": "photo-viewer",
                "file": "photo-viewer.png",
            }
            (output / "photo-viewer.png").write_bytes(
                (output / alapnezet["file"]).read_bytes()
            )
            main_records.append(photo_viewer_record)
            manifest = {
                **viewer_manifest,
                "states": [*main_records, *viewer_manifest["states"]],
                "sample_photo_mtimes_ns": [
                    (gyoker / relative).stat().st_mtime_ns
                    for relative in (
                        Path("kepek/a.jpg"),
                        Path("kepek/b.jpg"),
                        Path("kepek/Almappa/c.jpg"),
                    )
                ],
            }
            (output / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return manifest
        finally:
            try:
                next(generator)
            except StopIteration:
                pass


def _rgba_adatok(kep: Any) -> tuple[np.ndarray, int, int]:
    from PySide6.QtGui import QImage

    rgba = kep.convertToFormat(QImage.Format.Format_RGBA8888)
    sor_bajtok = bytes(rgba.constBits())
    sorhossz = rgba.bytesPerLine()
    adat = np.frombuffer(sor_bajtok, dtype=np.uint8).reshape(
        rgba.height(), sorhossz
    )[:, : rgba.width() * 4]
    return adat.reshape(rgba.height(), rgba.width(), 4), rgba.width(), rgba.height()


def _osszehasonlitott_kep(elotte: Any, utana: Any) -> tuple[int, tuple[int, int, int, int] | None, Any]:
    from PySide6.QtGui import QImage

    a, a_szel, a_mag = _rgba_adatok(elotte)
    b, b_szel, b_mag = _rgba_adatok(utana)
    szel, mag = max(a_szel, b_szel), max(a_mag, b_mag)
    elter = np.ones((mag, szel), dtype=bool)
    kozos_szel, kozos_mag = min(a_szel, b_szel), min(a_mag, b_mag)
    elter[:kozos_mag, :kozos_szel] = np.any(
        a[:kozos_mag, :kozos_szel] != b[:kozos_mag, :kozos_szel], axis=2
    )
    darab = int(np.count_nonzero(elter))
    if darab:
        sorok, oszlopok = np.nonzero(elter)
        bal, fent = int(oszlopok.min()), int(sorok.min())
        jobb, lent = int(oszlopok.max()) + 1, int(sorok.max()) + 1
        befoglalo = (bal, fent, jobb - bal, lent - fent)
    else:
        befoglalo = None
    pixels = np.zeros((mag, szel, 4), dtype=np.uint8)
    pixels[elter] = _KERET_SZIN
    diff = QImage(pixels.data, szel, mag, szel * 4, QImage.Format.Format_RGBA8888).copy()
    return darab, befoglalo, diff


def compare(before: Path, after: Path, diff_dir: Path) -> int:
    """Két PNG-mappát pontosan összevet, és a változó pixeleket kiemeli."""
    from PySide6.QtGui import QImage

    if not before.is_dir() or not after.is_dir():
        raise ValueError("Az összevetés mindkét bemenete létező mappa legyen.")
    png_a = {p.relative_to(before) for p in before.rglob("*.png") if not p.name.endswith(".diff.png")}
    png_b = {p.relative_to(after) for p in after.rglob("*.png") if not p.name.endswith(".diff.png")}
    if png_a != png_b:
        csak_a = sorted(p.as_posix() for p in png_a - png_b)
        csak_b = sorted(p.as_posix() for p in png_b - png_a)
        raise ValueError(
            "A két mappa PNG-listája eltér; csak előtte: "
            f"{csak_a}; csak utána: {csak_b}"
        )
    diff_dir.mkdir(parents=True, exist_ok=True)
    hibak = 0
    for relative in sorted(png_a):
        image_a, image_b = QImage(str(before / relative)), QImage(str(after / relative))
        if image_a.isNull() or image_b.isNull():
            raise ValueError(f"Nem olvasható PNG: {relative}")
        darab, bbox, diff = _osszehasonlitott_kep(image_a, image_b)
        diff_path = diff_dir / relative.parent / f"{relative.stem}.diff.png"
        if diff_path.exists():
            diff_path.unlink()
        if darab:
            diff_path.parent.mkdir(parents=True, exist_ok=True)
            if not diff.save(str(diff_path), "PNG"):
                raise OSError(f"Nem menthető a különbségkép: {diff_path}")
            assert bbox is not None
            x, y, bbox_szel, bbox_mag = bbox
            print(
                f"{relative.as_posix()}: {darab} eltérő képpont; "
                f"befoglaló téglalap: x={x}, y={y}, "
                f"szélesség={bbox_szel}, magasság={bbox_mag}; "
                f"különbségkép: {diff_path}"
            )
            hibak += darab
        else:
            print(f"{relative.as_posix()}: 0 eltérő képpont")
    return 1 if hibak else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture_parser = commands.add_parser("capture", help="A PhotoViewer állapotképeinek mentése")
    capture_parser.add_argument("--output", type=Path, required=True)
    capture_parser.add_argument("--width", type=int, default=1280)
    capture_parser.add_argument("--height", type=int, default=800)
    compare_parser = commands.add_parser("compare", help="Két PNG-mappa képpontos összevetése")
    compare_parser.add_argument("--before", type=Path, required=True)
    compare_parser.add_argument("--after", type=Path, required=True)
    compare_parser.add_argument("--diff-dir", type=Path, required=True)
    return parser


def _utf8_kimenet() -> None:
    """Windowson a konzol cp1252: az ékezetes kimenet nélküle elhasal (#5971)."""
    for folyam in (sys.stdout, sys.stderr):
        try:
            folyam.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _utf8_kimenet()
    args = _parser().parse_args(argv)
    try:
        if args.command == "capture":
            if args.width <= 0 or args.height <= 0:
                raise ValueError("Az ablakméretnek pozitívnak kell lennie.")
            result = capture(args.output, args.width, args.height)
            print(
                f"{len(result['states'])} állapot képe elmentve ide: {args.output} "
                f"(ablak: {result['actual_window_size']['width']}×"
                f"{result['actual_window_size']['height']})."
            )
            return 0
        return compare(args.before, args.after, args.diff_dir)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Hiba: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
