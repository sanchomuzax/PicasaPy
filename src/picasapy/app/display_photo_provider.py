"""A megjelenítési mód a TELJES FELBONTÁSÚ képen — a diavetítésnek (#1640).

## Miért kell külön szolgáltató

A `Nézet ▸ Megjelenítési mód` átalakítói két úton jutnak a képernyőre:

| felület | út |
|---|---|
| nagy néző | `editpreview` (a szerkesztési munkamenet előnézete) |
| könyvtár rácsa és a többi bélyegkép-felület | `thumbs`, az URL `&d=<mód>` cimkéjével (#1596) |

A **diavetítés egyiket sem használja**: a `SlideshowView.qml` a NYERS fájl
URL-jét tölti be, tehát a mód rajta soha nem látszott — pedig a „Projektor
mód" (`ID_VIEW_PROJECTOR`, −14,1 % egyenletes sötétítés) épp a kivetítéshez
való (#1640, a #1598 mérése).

A két meglévő út egyike sem alkalmas:

* az `editpreview` **szerkesztési munkamenetet** igényel — a diavetítés
  másodpercenként lapoz, képenként munkamenetet nyitni a szerkesztő
  állapotával is ütközne;
* a `thumbs` **bélyegképet** ad (és lemezre ír): a vetített kép teljes
  felbontású, a bélyegkép-gyorstárat pedig nem szennyezhetjük.

Ez a szolgáltató ezért a fájlt tölti be, és **ugyanazt az egyetlen
átfestőt** hívja rá, amit a másik két út (`display_mode_paint`) — a mód
matematikája egy helyen marad.

## A mód az URL-ben van, nem a szolgáltató állapotában

Ugyanaz az elv, mint a #1596-nál: **az URL egyértelműen meghatározza a
képpontokat.** Így egy gyors módváltás nem tud rossz módú képet beragasztani
a Qt URL-kulcsú gyorstárába, és a módok külön rekeszben élnek (oda-vissza
kapcsolgatva nincs újrarenderelés).

Alak: `image://displayphoto/<abszolút útvonal>?d=<mód>`

⚠️ **Cimke nélkül nem is ide jön a kérés.** A `models.py` `displayUrlAt()`-je
a mód nélküli (rendes) esetben a sima `file://` URL-t adja vissza — a
diavetítés így a mindennapi használatban semmivel nem lassul, és a Qt
gyorstárában a mód bevezetése előtti kulcs marad.
"""

from __future__ import annotations

import logging
from urllib.parse import parse_qs, unquote

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from picasapy.app.display_mode_paint import (
    DISPLAY_MODE_QUERY_KEY,
    apply_display_mode_to_qimage,
)
from picasapy.render.display_modes import display_mode_changes_pixels

_log = logging.getLogger(__name__)

#: A szolgáltató neve a QML-ben (`image://displayphoto/…`).
PROVIDER_NAME = "displayphoto"


def _szetszed(azonosito: str) -> tuple[str, str]:
    r"""(fájlútvonal, mód) a szolgáltatónak átadott azonosítóból.

    A Qt a `image://displayphoto/` utáni részt adja át, a lekérdezéssel
    együtt. Az útvonal URL-kódolt lehet (ékezet, szóköz).

    ⚠️ **`urlparse` NEM használható itt** (mérve a windows-lábon, #1640): a
    `C:\kepek\a.jpg` alakú útvonalban a **meghajtó betűjét URL-sémának
    olvassa** (`scheme='c'`), és az útvonal fele elveszik — a diavetítés képe
    ilyenkor be sem töltődik. A kettéválasztás ezért kézzel megy az ELSŐ
    `?`-nél: a lekérdezést mi magunk írjuk, az útvonalat pedig `quote()`-tal
    kódoljuk (ami a `?`-et `%3F`-re cseréli), tehát az első `?` mindig a
    lekérdezés kezdete.
    """
    kodolt_ut, _, lekerdezes = azonosito.partition("?")
    mod = parse_qs(lekerdezes).get(DISPLAY_MODE_QUERY_KEY, [""])[0]
    return unquote(kodolt_ut), mod


class DisplayPhotoProvider(QQuickImageProvider):
    """`image://displayphoto/<útvonal>?d=<mód>` — a fájl, a móddal átfestve."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id: str, size, requestedSize) -> QImage:  # noqa: A002
        utvonal, mod = _szetszed(id)
        kep = QImage(utvonal)
        if kep.isNull():
            # A hívónak a Qt `Error` státuszt ad; a diavetítés ilyenkor a
            # következő képre lép — ez ugyanaz, mint a nyers fájl útján.
            _log.warning("a diavetítés képe nem tölthető be: %s", utvonal)
            return QImage()
        # #3832: képpontot mozdító módban (a szín a KIRAJZOLT képpontokon
        # dől el, ld. `apply_display_mode_to_qimage`) a jelölésnek a
        # TÉNYLEGES, méretezett képen kell megtörténnie — natív méreten
        # jelölve a kirajzolás nyújtaná szét a jelölőszínt a szomszédokba
        # (ugyanaz az elv, mint `edit_preview.EditPreviewProvider
        # .requestImage`-ben, #3819).
        jelol = display_mode_changes_pixels(mod)
        if requestedSize is not None and requestedSize.width() > 0:
            # ⚠️ A `mode=1` NEM működik (mérve: `ValueError: … called with
            # wrong argument values` a QML-hívásban, #1640) — a PySide az
            # enumot várja. A hiba csak a QML-úton jött elő: az egységpróba
            # `None` méretet adott át, tehát ez az ág méretlen volt.
            width, height = requestedSize.width(), requestedSize.height()
            # #3832: a `sourceSize` a QML-ben befoglaló doboz — csak
            # KICSINYÍTÜNK bele, a kis képet nem nagyítjuk fel (a régi,
            # feltétel nélküli `scaledToWidth` egy 9:16-os, legalább 2560
            # széles telefonfotót 2560×4551-esre nyújtott, a V3D 4096-os
            # textúraplafonja fölé). A KIVÉTEL a jelölő mód: ott a
            # méretezés akkor is megtörténik, ha a kép már belefér, hogy a
            # jelölés a VÉGLEGES képpontrácson történjen.
            if not (_belefer(kep, width, height) and not jelol):
                smooth = Qt.TransformationMode.SmoothTransformation
                if width > 0 and height > 0:
                    kep = kep.scaled(requestedSize, Qt.AspectRatioMode.KeepAspectRatio, smooth)
                elif width > 0:
                    kep = kep.scaledToWidth(width, smooth)
                elif height > 0:
                    kep = kep.scaledToHeight(height, smooth)
        kep = apply_display_mode_to_qimage(kep, mod)
        if size is not None:
            size.setWidth(kep.width())
            size.setHeight(kep.height())
        return kep


def _belefer(image: QImage, width: int, height: int) -> bool:
    """A kép a kért (`0` = korlátlan) dobozba már méretezés nélkül is
    belefér (#3832, ld. `edit_preview._belefer`)."""
    return (width <= 0 or image.width() <= width) and (
        height <= 0 or image.height() <= height
    )


__all__ = ["PROVIDER_NAME", "DisplayPhotoProvider"]
