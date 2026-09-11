"""`image://foldercover/<mappa>` — a mappa fotó-kupac borítója (#2049).

A bal hasáb fasorain az eredeti Picasa nem sárga mappaikont mutat, hanem
a mappa első néhány fotójából összeállított kis képhalmot. A mértant a
`picasapy.thumbs.album_borito` számolja; ez a modul csak a képeket szedi
össze és adja át a QML-nek.

## Miért SZINKRON, szemben a rács providerével

A `thumbs` provider aszinkron, mert a rácson egyszerre több száz cella
kérhet nagy bélyegképet. Itt a nagyságrend más: egyszerre annyi borító
látszik, ahány fasor, mindegyik legfeljebb négy KIS képből áll, és a
kész borítót gyorstárazzuk. A szinkron ág ezért olcsóbb — és nincs
szükség az aszinkron providernél kimért élettartam-tánchoz (#1457).

Hibatűrés (#66): a rajzolásból kivétel SOHA nem szökhet ki — hibánál üres
képet adunk vissza, és a fasor a szokásos mappaikonjára esik vissza.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Sequence

import numpy as np

from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from picasapy.thumbs.album_borito import (
    LAPOK_MAXIMUMA,
    keszits_boritot,
    mappa_magja,
)

_log = logging.getLogger(__name__)

#: #2983: a Qt az `image://` URL útvonalát dekódolja, a KÓDOLT ELVÁLASZTÓT
#: viszont meghagyja — szándékosan, mert a dekódolás megváltoztatná az
#: útvonal szerkezetét. Mérve (valódi QML-motor, négy útvonal):
#:
#: | a QML-nek átadva | amit a szolgáltató KAP |
#: |---|---|
#: | `C:\Users\…\Képek\AI` | **`C:%5CUsers%5C…%5CKépek%5CAI`** |
#: | `C:/Users/…/Képek/AI` | változatlanul ✅ |
#: | `/home/…/nyaralás 2024` | változatlanul ✅ (ékezet, szóköz rendben) |
#: | `/home/…/a#b` | változatlanul ✅ |
#:
#: Windowson az index NATÍV, visszaperes útvonalat tárol, tehát a kódolt
#: alakkal a keresés nem talál fájlt, a borító `None` lesz, és minden mappa
#: a mappaikonra esik vissza — pontosan ez volt a #2983.
#:
#: ⚠️ Csak a KÓDOLT ELVÁLASZTÓT oldjuk fel, nem az egész sztringet: a teljes
#: `fromPercentEncoding` egy `a%41b` nevű mappát `aAb`-vé rontana (a `%`-ot a
#: Qt már feloldotta `%25`-ből).
_KODOLT_ELVALASZTOK = (("%5C", "\\"), ("%5c", "\\"), ("%2F", "/"), ("%2f", "/"))


def normalizald_az_azonositot(id: str) -> str:
    """A szolgáltatónak átadott azonosító → a valódi útvonal (#2983)."""
    for kodolt, karakter in _KODOLT_ELVALASZTOK:
        id = id.replace(kodolt, karakter)
    return id
#: A kupacba kerülő fotók száma — a natív összeállító is az első
#: `min(N, 4)` fotót veszi (`0x004237ab`), névsorban.
BORITO_FOTOK_MAXIMUMA = 4


def borito_fajljai(index_db: Path, mappa: str) -> list[Path]:
    """A mappa első legfeljebb négy fotójának ÚTVONALA, névsorban.

    ⚠️ **#2984 — ez a függvény azért MODUL-SZINTŰ, hogy legyen mit
    tesztelni.** Korábban az `application.py` belsejében élő lezárás volt,
    és `rekord.path`-t olvasott — a `PhotoRecord`-nak viszont nincs ilyen
    mezője (`folder_path` + `name` van). MINDEN mappán `AttributeError`-t
    dobott, amit a szolgáltató „nincs borító"-vá nyelt, tehát a bal hasáb
    bekapcsolt kapcsolóval is mappaikont mutatott. A meglévő őrök
    `lambda`-val hívták a szolgáltatót, ezért a hibás lezárás **zölden
    átcsúszott**. Ugyanez a hiba volt a #1589 (Earth-export) — a közös
    segéd (`export.earth.record_path`) onnan származik.
    """
    from picasapy.export.earth import record_path
    from picasapy.index import open_index
    from picasapy.index.queries import photos_in_folder

    with open_index(index_db) as conn:
        rekordok = photos_in_folder(conn, mappa)[:BORITO_FOTOK_MAXIMUMA]
    return [record_path(rekord) for rekord in rekordok]


#: A kupacba kerülő egyes lapok leghosszabb oldala képpontban. Az élő
#: mintákban a KÉSZ borító leghosszabb oldala 72–119 px; egy lap ennél
#: kisebb, mert a kupac szétterül. A 60 px ebbe a sávba viszi a
#: végeredményt, és a fasor magasságára még bőven van mit kicsinyíteni.
LAP_MERET = 60


def _olvasd_be(utvonal: Path):
    import cv2

    # #1991: ékezetes néven a `cv2.imread(str(...))` Windowson némán
    # `None`-t ad — a bájtokat magunk olvassuk be.
    nyers = np.fromfile(str(utvonal), dtype=np.uint8)
    if nyers.size == 0:
        return None
    kep = cv2.imdecode(nyers, cv2.IMREAD_COLOR)
    if kep is None:
        return None
    magassag, szelesseg = kep.shape[:2]
    arany = LAP_MERET / max(magassag, szelesseg)
    if arany < 1.0:
        kep = cv2.resize(
            kep,
            (max(1, round(szelesseg * arany)), max(1, round(magassag * arany))),
            interpolation=cv2.INTER_AREA,
        )
    return kep


def keszits_mappa_boritot(mappa: str, fajlok: Sequence[Path]):
    """A mappa borítója RGBA tömbként, vagy `None`, ha nem áll össze.

    A kupacba a kapott lista **első** legfeljebb négy olvasható fájlja
    kerül — az eredeti is a lista elejét veszi (`0x004237ab`), nem a
    legrégebbit vagy a csillagozottat.
    """
    lapok = []
    for fajl in fajlok:
        if len(lapok) >= LAPOK_MAXIMUMA:
            break
        try:
            kep = _olvasd_be(Path(fajl))
        except OSError as hiba:
            _log.warning("a borító lapja nem olvasható: %s (%s)", fajl, hiba)
            continue
        if kep is not None:
            lapok.append(kep)
    if not lapok:
        return None
    return keszits_boritot(lapok, mappa_magja(mappa))


class FolderCoverProvider(QQuickImageProvider):
    """`image://foldercover/<mappa útvonala>`."""

    def __init__(self, fajlok_lekerdezo: Callable[[str], Sequence[Path]]) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._fajlok_lekerdezo = fajlok_lekerdezo
        self._gyorstar: dict[str, QImage] = {}

    def uritsd_a_gyorstarat(self) -> None:
        """Az indexelés után a borítók elavulhatnak."""
        self._gyorstar = {}

    def requestImage(self, id: str, size, requestedSize) -> QImage:  # noqa: A002
        mappa = normalizald_az_azonositot(id)
        kesz = self._gyorstar.get(mappa)
        if kesz is None:
            kesz = self._rajzold(mappa)
            self._gyorstar[mappa] = kesz
        if size is not None:
            size.setWidth(kesz.width())
            size.setHeight(kesz.height())
        if requestedSize is not None and requestedSize.isValid():
            return kesz.scaled(
                requestedSize,
                aspectMode=1,  # Qt.KeepAspectRatio
                mode=1,  # Qt.SmoothTransformation
            )
        return kesz

    def _rajzold(self, mappa: str) -> QImage:
        try:
            fajlok = list(self._fajlok_lekerdezo(mappa))
            borito = keszits_mappa_boritot(mappa, fajlok)
        except Exception:  # noqa: BLE001 — a providerből kivétel nem szökhet ki
            _log.exception("a mappa-borító előállítása elszállt: %s", mappa)
            borito = None
        if borito is None:
            # #2215: ÜRES (null) kép — NEM 1×1 átlátszó. A különbség a
            # felületen dől el: az 1×1-es kép sikeresen betöltődik, ezért a
            # QML `Image.status`-a `Ready` lesz, a fasor `boritoLatszik`
            # feltétele igaz, és a mappaikon ELREJTŐZIK — a sor teljesen
            # üresen marad. A null kép `Error` státuszt ad, tehát a sor
            # visszaesik a mappaikonra, ahogy a `FolderPane.qml` ígéri.
            return QImage()
        magassag, szelesseg = borito.shape[:2]
        # A tömb BGRA sorrendű (OpenCV); a Qt `Format_ARGB32` little-endian
        # gépen ugyanezt a bájtsorrendet várja.
        kep = QImage(
            borito.tobytes(),
            szelesseg,
            magassag,
            szelesseg * 4,
            QImage.Format.Format_ARGB32,
        )
        # A `QImage` nem másol: a puffert magunknak kell életben tartani.
        return kep.copy()
