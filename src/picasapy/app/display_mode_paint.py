"""A megjelenítési mód a BÉLYEGKÉP-úton — URL-cimke és QImage-átfestés (#1596).

A `Nézet ▸ Megjelenítési mód` a #1576 óta hat a nagy nézőre, de a **könyvtár
rácsára nem**: a színezés az `editpreview` szolgáltatóban futott, a rács
viszont a `thumbs` szolgáltatóból rajzol. Ez a modul a rács oldalán adja meg
ugyanazt a hatást, és egyetlen helyen tartja a két összetartozó felet:

* `display_mode_url_suffix()` — a bélyegkép-URL **cimkéje** (a `models.py`
  írja bele),
* `display_mode_from_thumb_id()` — ugyanennek a **kiolvasása** (a
  `thumbnail_provider.py` olvassa vissza).

## Miért az URL hordozza a módot, és nem a szolgáltató állapota?

A nagy nézőnél a szolgáltató tart egy `_display_mode` mezőt, és az
`EditController` egy `?rev=` cache-busterrel kéreti újra a képet. A rácson
ez a szétválasztás **versenyt** csinálna: a Qt a bélyegképet URL szerint
gyorstárazza, a `ThumbnailProvider` pedig egy saját `QThreadPool`-on
dolgozik. Gyors módváltásnál egy még futó kérés a KÖVETKEZŐ módot tenné rá
egy olyan URL-re, amit az előző mód nevében kértek — és az eredmény
beragadna a Qt gyorstárába.

Az URL-be írt mód ezt szerkezetileg zárja ki: **az URL egyértelműen
meghatározza a képpontokat**. Ráadásul a gyorstár így módonként külön
rekeszt tart, tehát oda-vissza kapcsolgatva nem kell újrarenderelni.

## A cimke csak ott jelenik meg, ahol számít

Az `auto`/`normal` és a hét, ma még meg nem valósított mód (#1579)
képpontot nem mozdít, ezért **nem kap cimkét**: az URL bájtra ugyanaz, mint
a mód bevezetése előtt. Így (a) a rendes használat semmivel nem lassul, és
(b) a módból kilépve a Qt gyorstárában MÁR OTT LÉVŐ, festetlen kép jelenik
meg azonnal — nincs újrarenderelés.

## Amit ez a modul SZÁNDÉKOSAN nem tesz

Nem nyúl a bélyegkép-gyorstárhoz. Az átfestés a `ThumbnailProvider`
render-magja UTÁN fut, tehát sem a lemezre írt bélyegkép, sem a memóriabeli
(`_FilteredThumbMemo`) rekesz nem szennyeződik — a mód **megjelenítési
átalakító**, nem a bélyegkép tartalma. A `tests/app/test_display_mode_racs_1596.py`
és a rács QML-őre ezt külön méri.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtGui import QImage

from picasapy.render.display_modes import (
    apply_display_mode,
    display_mode_changes_pixels,
)

#: A bélyegkép-URL lekérdezés-kulcsa. Rövid, mert a meglévő cimkék is azok
#: (`r` = forgatás, `f` = filters-lánc, `m`/`s` = mtime/méret).
DISPLAY_MODE_QUERY_KEY = "d"


def display_mode_url_suffix(mode: str) -> str:
    """A bélyegkép-URL mód-cimkéje (`&d=<mód>`), vagy üres sztring.

    Üres marad minden olyan módra, amely ma képpontot nem mozdít — ld. a
    modul-docstring „A cimke csak ott jelenik meg, ahol számít" szakaszát.
    """
    if not isinstance(mode, str) or not display_mode_changes_pixels(mode):
        return ""
    return f"&{DISPLAY_MODE_QUERY_KEY}={mode}"


def display_mode_from_thumb_id(photo_id: str) -> str:
    """A `?…&d=<mód>` cimke kiolvasása a szolgáltatónak átadott azonosítóból.

    Cimke nélküli (vagyis a rendes, átalakítás nélküli) kérésre üres
    sztring. A gyors kizárás SZÁNDÉKOS: a rács minden bélyegképnél ide
    lép, és a mindennapi eset épp a cimke nélküli.
    """
    if not photo_id:
        return ""
    _, _, query = str(photo_id).partition("?")
    marker = f"{DISPLAY_MODE_QUERY_KEY}="
    if marker not in query:
        return ""
    for parameter in query.split("&"):
        key, separator, value = parameter.partition("=")
        if separator and key == DISPLAY_MODE_QUERY_KEY:
            return value
    return ""


def _qimage_to_rgb_array(image: QImage) -> np.ndarray:
    """QImage → RGB uint8 `(H, W, 3)` tömb, a Qt-pufferre hivatkozás nélkül."""
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = converted.width(), converted.height()
    stride = converted.bytesPerLine()
    raw = np.frombuffer(bytes(converted.constBits()), dtype=np.uint8)
    raw = raw.reshape((height, stride))
    return raw[:, : width * 3].reshape((height, width, 3)).copy()


def _rgb_array_to_qimage(array: np.ndarray) -> QImage:
    """RGB uint8 `(H, W, 3)` tömb → QImage (a numpy-puffer másolatával)."""
    contiguous = np.ascontiguousarray(array)
    height, width = contiguous.shape[:2]
    image = QImage(
        contiguous.data, width, height, width * 3, QImage.Format.Format_RGB888
    )
    return image.copy()


def apply_display_mode_to_qimage(image: QImage, mode: str) -> QImage:
    """A mód alkalmazása egy KIADANDÓ bélyegképre; a bemenet érintetlen.

    Képpontot nem mozdító módra (és null képre) a bemenetet adja vissza —
    a hívónak nem kell módonként elágaznia, és a rendes út nem fizet
    tömbbé alakítást.

    A bélyegképek JPEG-ből dekódolódnak, tehát alfa-csatornájuk nincs; az
    RGB888-on át vezető út ezért nem veszít adatot. (A nagy néző azonos
    okból ugyanígy dolgozik, ld. `edit_preview.requestImage`.)
    """
    if image is None or image.isNull() or not display_mode_changes_pixels(mode):
        return image
    return _rgb_array_to_qimage(
        apply_display_mode(_qimage_to_rgb_array(image), mode)
    )
