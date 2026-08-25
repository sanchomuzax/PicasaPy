"""SZINKRON bélyegkép-szolgáltató a QML-tesztekhez (#1457).

## Miért létezik ez

A `ThumbnailProvider` és az `EffectThumbnailProvider` **aszinkron**: saját
`QThreadPool`-t tartanak, és a kész képet egy `QQuickImageResponse`-on át
adják vissza. Ez a felhasználónál helyes és szükséges — hálózati mappán a
felület nem várhat a renderre.

A QML-funkcionális tesztekben viszont **teher, haszon nélkül**. Azok a
tesztek a felület bekötését mérik (mi látszik, mi kattintható, mi
frissül), nem a bélyegkép-készítés párhuzamosságát — arra saját,
motor nélküli tesztek vannak (`test_thumbnail_async.py`,
`test_effect_thumbnails.py`, `test_thumbnail_response_lifetime_1457.py`).

Cserébe viszont behozzák a folyamatba a pool-szálakat, a szálak közti
jelzéseket és a motor halasztott törléseit — vagyis pontosan azt a
felületet, amin a #999/#1457 összeomlásai keletkeznek. Egy nap alatt öt
különböző QML-tesztfájl esett ki jel nélkül, mindegyik terhelés alatt.

## A döntés

**Nem a versenyt tesszük biztonságossá a tesztek alatt, hanem kivesszük a
versenyt onnan, ahol nincs rá szükség.** A QML-fixture ezt a szinkron
szolgáltatót regisztrálja: azonnal ad képet, szál nélkül, válasz-objektum
nélkül.

⚠️ **Amit ez NEM tesz meg:** nem javítja a #1457-et. A termékkód
változatlanul aszinkron, és a hibaosztály nyitva marad — csak a
QML-tesztek nem szenvednek tőle. A valódi aszinkron utat a fenti,
célzott tesztek mérik, ahol a hiba reprodukálható és elemezhető.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QImage
from PySide6.QtQuick import QQuickImageProvider


class SzinkronKepSzolgaltato(QQuickImageProvider):
    """Azonnali, egyszínű kép — szál és válasz-objektum nélkül."""

    def __init__(self, szin: QColor | None = None, meret: int = 32) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._szin = szin if szin is not None else QColor(200, 200, 200)
        self._meret = meret

    def requestImage(self, image_id, size, requested_size):  # noqa: N802 (Qt API)
        szelesseg = self._meret
        magassag = self._meret
        if requested_size is not None and requested_size.isValid():
            szelesseg = max(1, requested_size.width())
            magassag = max(1, requested_size.height())
        kep = QImage(szelesseg, magassag, QImage.Format.Format_RGB32)
        kep.fill(self._szin)
        if size is not None:
            size.setWidth(kep.width())
            size.setHeight(kep.height())
        return kep
