"""A szerkesztési előnézet forrásképének dekódolása és képkonverziói."""

from __future__ import annotations

import functools
from pathlib import Path

import numpy as np
from PySide6.QtCore import QSize
from PySide6.QtGui import QColorSpace, QImage, QImageReader

from picasapy.cvimage import scale_down
from picasapy.lazy_cv2 import cv2
from picasapy.rawdecode import dekodol_nyerset, nyers_hosszabb_el, nyers_utvonal

_MAX_PREVIEW_EDGE = 2560


@functools.lru_cache(maxsize=64)
def _teljes_hosszabb_el(path: str, mtime: float | None) -> int | None:
    """A forrás TELJES felbontású hosszabb éle — csak a fejlécből (#3377).

    Az `mtime` a gyorsítótár-kulcs része: a lecserélt fájl új méretét adja.
    `None`, ha a méret nem olvasható."""
    if nyers_utvonal(path):
        return nyers_hosszabb_el(Path(path))
    meret = QImageReader(path).size()
    if not meret.isValid():
        return None
    return max(meret.width(), meret.height()) or None


def _elonezeti_arany(
    path: Path, mtime: float | None, source: np.ndarray | None, teljes_felbontas: bool
) -> float:
    """A munkavászon és a teljes felbontású kép aránya (#3377).

    Az eredeti a keret két vastagságát ezzel szorozza (`imageWidth /
    fullResImageWidth`). Teljes felbontású dekódnál, és ha a méret nem
    állapítható meg, 1 — ilyenkor a keret a mai, teljes felbontású
    viselkedést adja."""
    if teljes_felbontas or source is None:
        return 1.0
    teljes = _teljes_hosszabb_el(str(path), mtime)
    if not teljes:
        return 1.0
    return min(1.0, max(source.shape[0], source.shape[1]) / teljes)


def _decode_source(
    path: Path, *, full_res: bool = False, color_managed: bool = False
) -> np.ndarray | None:
    """A forráskép dekódolása RGB numpy tömbbé, előnézet-felbontásra korlátozva.

    QImageReader + autoTransform: az EXIF-orientációt a betöltés alkalmazza —
    a néző natív Image-e is így tesz (autoTransform: true). A dekód mérete
    korlátozott: az előnézethez elég, és a GUI-szálon futó renderelés így
    nagy képnél is gyors marad. `None`, ha a kép nem olvasható be.

    #819: `full_res=True` esetén a korlát ELMARAD. A szűrő-regiszter 19
    szűrőre `fullres` jelzőt ad — ezek csak teljes felbontáson adnak helyes
    eredményt, tehát a kicsinyített forráson futtatva a felhasználó MÁST
    látna, mint amit a mentett kép tartalmaz. A megjelenített előnézet
    ettől függetlenül a korlátra kicsinyül (`_kicsinyitsd_a_megjelenitendot`).

    #1725: `color_managed=True` esetén a képbe **beágyazott ICC-profil**
    érvényesül — a kép sRGB-be alakul (`QImage.convertToColorSpace`). Ez az
    eredeti `Színkezelés használata` kapcsolójának mért jelentése: littleCMS
    szabványos ICC-átalakítása, nem saját színtan (spec 5.12). Profil nélküli
    vagy már sRGB képen ez no-op, a kikapcsolt állapot pedig — ahogy a
    binárisban is — semmit nem tesz."""
    if nyers_utvonal(path):
        return _nyers_forras(path, full_res=full_res)
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    native = reader.size()
    if native.isValid() and not full_res:
        longest = max(native.width(), native.height())
        if longest > _MAX_PREVIEW_EDGE:
            scale = _MAX_PREVIEW_EDGE / longest
            reader.setScaledSize(
                QSize(round(native.width() * scale), round(native.height() * scale))
            )
    source = reader.read()
    if source.isNull():
        return None
    if color_managed:
        source = _srgb_be(source)
    return _qimage_to_rgb_array(source)


def _nyers_forras(path: Path, *, full_res: bool) -> np.ndarray | None:
    """Nyers (RAW) forrás → RGB tömb, az előnézet-korláttal (#528).

    A `QImageReader`-nek nincs nyers beolvasója, tehát a nyers fájl ezen az
    úton is külön dekódolót kíván (`picasapy.rawdecode`, LibRaw).

    Két dolog szándékosan MARAD EL itt:

    * **EXIF-orientáció** — a LibRaw a nyers fájl saját `flip` mezőjét már a
      demozaikolás közben alkalmazza, tehát a `setAutoTransform` megfelelője
      megvan; másodszor forgatni hiba lenne.
    * **ICC-átalakítás** (`color_managed`) — a LibRaw kimenete alapból sRGB,
      nincs mit átalakítani. A nyers fájlban nincs beégetett színtér, ezért a
      #1725 kapcsolójának itt nincs mit érvényesítenie.
    """
    bgr = dekodol_nyerset(path)
    if bgr is None:
        return None
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    if full_res:
        return rgb
    return scale_down(rgb, _MAX_PREVIEW_EDGE)


def _srgb_be(kep: QImage) -> QImage:
    """A beágyazott profillal jelölt kép sRGB-be alakítva (#1725).

    Profil nélküli vagy már sRGB képnél változatlanul adja vissza — az
    átalakítás így sosem „talál ki" színteret oda, ahol nincs.
    """
    szinter = kep.colorSpace()
    srgb = QColorSpace(QColorSpace.NamedColorSpace.SRgb)
    if not szinter.isValid() or szinter == srgb:
        return kep
    atalakitott = kep.copy()
    atalakitott.convertToColorSpace(srgb)
    return atalakitott


def _megjelenitendo(tomb: np.ndarray, teljes_felbontas: bool) -> np.ndarray:
    """A MEGJELENÍTENDŐ kép — a teljes felbontású render kicsinyítve (#819).

    A `fullres` szűrők a teljes felbontású forráson futnak, de a felületre
    kikerülő előnézet ettől nem lehet nagyobb: a néző úgyis kicsinyítve
    mutatja, a nagy `QImage` viszont a memóriát és a rajzolást terheli
    (egy 3200×2400-as RGB kép ~23 MB)."""
    if not teljes_felbontas:
        return tomb
    magas, szeles = tomb.shape[0], tomb.shape[1]
    leghosszabb = max(szeles, magas)
    if leghosszabb <= _MAX_PREVIEW_EDGE:
        return tomb
    arany = _MAX_PREVIEW_EDGE / leghosszabb
    from picasapy.render.glimmer_ops import resize_image

    return resize_image(tomb, max(1, round(szeles * arany)), max(1, round(magas * arany)))


def _qimage_to_rgb_array(image: QImage) -> np.ndarray:
    """QImage → RGB uint8 (H, W, 3) numpy tömb, a bufferre hivatkozás nélkül
    (a `.copy()` a QImage megszűnése után is biztonságos marad)."""
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = converted.width(), converted.height()
    stride = converted.bytesPerLine()
    buffer = bytes(converted.constBits())
    raw = np.frombuffer(buffer, dtype=np.uint8).reshape((height, stride))
    return raw[:, : width * 3].reshape((height, width, 3)).copy()


def _rgb_array_to_qimage(array: np.ndarray) -> QImage:
    """RGB uint8 (H, W, 3) numpy tömb → QImage (a numpy-puffer másolatával)."""
    contiguous = np.ascontiguousarray(array)
    height, width = contiguous.shape[:2]
    stride = width * 3
    image = QImage(contiguous.data, width, height, stride, QImage.Format.Format_RGB888)
    return image.copy()


def _lut_array_to_qimage(lut: np.ndarray) -> QImage:
    """`(256, 3)` uint8 finetune2-LUT → 256×1 RGB8 `QImage` (#22) — a
    `GpuPointFilterPreview.qml` ezt tölti be `lutItem`-ként és mintavételezi
    csatornánként a shaderben (ld. `gpu_point_pipeline` modul-docsztring)."""
    return _rgb_array_to_qimage(lut[np.newaxis, :, :])
