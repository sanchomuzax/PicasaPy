"""OpenCV-alapú thumbnail-generálás lemez-gyorsítótárral (ADR: rpi5-image-libs).

A cache-kulcs a forrásfájl útvonalából + mtime-jából + méretéből képzett
hash: fájlváltozáskor automatikusan új bejegyzés készül, a régit a későbbi
takarító dolga eltüntetni. Az OpenCV imdecode alapból alkalmazza az
EXIF-orientációt, ezért a thumbnail már helyesen forgatott.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from picasapy.ini.filters import FilterOp, serialize_filters
from picasapy.ioutil import write_atomic
from picasapy.render import apply_filters
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS

_JPEG_QUALITY = 85

# #163: a szerkesztett (filters=) bélyegkép bázisa a célméret többszöröse —
# a lánc (jellemzően crop64) a nagy bázison fut, és csak a VÉGEREDMÉNYT
# kicsinyítjük a célméretre. Így az erős vágás után is éles marad a kép
# (nem a kész kis thumbnailt vágjuk tovább, amit a rács homályosan
# felnagyítana). A faktor 4: 25%-os vágás után a kimenet még pont a teljes
# célméret; ennél erősebb vágásnál is jóval élesebb a naiv útnál.
_EDIT_BASE_FACTOR = 4

# Nagy forrásképnél redukált JPEG-dekódolás kíméli az RPi memóriáját;
# a cél a thumbnail-méret legalább kétszerese, hogy az INTER_AREA
# kicsinyítésnek maradjon mintavételi tartaléka.
_REDUCED_FLAGS = (
    (8, cv2.IMREAD_REDUCED_COLOR_8),
    (4, cv2.IMREAD_REDUCED_COLOR_4),
    (2, cv2.IMREAD_REDUCED_COLOR_2),
)


class ThumbnailCache:
    def __init__(self, root: str | Path, size: int = 256):
        self._root = Path(root)
        self._size = size

    def thumbnail_path(self, photo_path: Path, mtime_ns: int, size_bytes: int) -> Path:
        key = f"{photo_path}\x00{mtime_ns}\x00{size_bytes}\x00{self._size}"
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return self._root / digest[:2] / f"{digest}.jpg"

    def get_or_create(
        self, photo_path: str | Path, mtime_ns: int, size_bytes: int
    ) -> Path | None:
        """A kész thumbnail útvonala; None, ha a forrás nem dekódolható."""
        source = Path(photo_path)
        target = self.thumbnail_path(source, mtime_ns, size_bytes)
        if target.exists():
            return target
        image = self._decode_source(source)
        if image is None:
            return None
        thumb = self._scale_down(image)
        ok, encoded = cv2.imencode(
            ".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY]
        )
        if not ok:
            return None
        try:
            self._write_atomic(target, encoded.tobytes())
        except OSError:
            return None  # tele lemez / NAS-hiba — a hívó placeholderre esik
        return target

    def get_or_create_edited(
        self,
        photo_path: str | Path,
        mtime_ns: int,
        size_bytes: int,
        ops: tuple[FilterOp, ...],
    ) -> Path | None:
        """Szerkesztett bélyegkép: a `filters=` láncot nagy felbontású
        bázison alkalmazza, majd a végeredményt kicsinyíti a célméretre (#163).

        Lánc nélkül a szűretlen thumbnailra esik vissza. A forgatás nem itt
        történik (a hívó a kész — kicsi — bélyegképen forgat, ami veszteség-
        mentes). A cache-kulcs tartalmazza a láncot, így a szerkesztett
        bélyegkép külön fájlba kerül és görgetéskor nem kell újraszámolni."""
        if not ops:
            return self.get_or_create(photo_path, mtime_ns, size_bytes)
        source = Path(photo_path)
        target = self.edited_thumbnail_path(
            source, mtime_ns, size_bytes, serialize_filters(ops)
        )
        if target.exists():
            return target
        base = self._decode_source(source, self._size * _EDIT_BASE_FACTOR)
        if base is None:
            return None
        rgb = cv2.cvtColor(self._scale_down(base, self._size * _EDIT_BASE_FACTOR),
                           cv2.COLOR_BGR2RGB)
        try:
            rendered, _skipped = apply_filters(rgb, ops)
        except Exception:  # noqa: BLE001
            # #73-elv: hibás/idegen lánc-bejegyzésnél a szűretlen kép a helyes
            # visszaesés (részleges előnézet), nem a placeholder.
            rendered = rgb
        thumb = cv2.cvtColor(self._scale_down(rendered, self._size),
                             cv2.COLOR_RGB2BGR)
        ok, encoded = cv2.imencode(
            ".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY]
        )
        if not ok:
            return None
        try:
            self._write_atomic(target, encoded.tobytes())
        except OSError:
            return None
        return target

    def edited_thumbnail_path(
        self, photo_path: Path, mtime_ns: int, size_bytes: int, chain: str
    ) -> Path:
        key = f"{photo_path}\x00{mtime_ns}\x00{size_bytes}\x00{self._size}\x00e\x00{chain}"
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return self._root / digest[:2] / f"{digest}.jpg"

    def _decode_source(self, source: Path, target: int | None = None):
        """Forrás → BGR numpy kép: videónál egy képkocka, képnél imdecode.

        `target`: a redukált beolvasás célmérete (a szerkesztő-bázis
        nagyobb, mint a sima thumbnailé). Alapból a cache saját mérete."""
        if source.suffix.lower() in VIDEO_EXTENSIONS:
            return _decode_video_frame(source)
        return _decode_image(source, self._read_flag(source, target))

    def _read_flag(self, source: Path, target: int | None = None) -> int:
        """Dekódolási flag: nagy képre redukált beolvasás (memóriakímélés)."""
        goal = self._size if target is None else target
        try:
            with Image.open(source) as probe:
                longest = max(probe.size)
        except (OSError, UnidentifiedImageError, ValueError):
            return cv2.IMREAD_COLOR
        for factor, flag in _REDUCED_FLAGS:
            if longest // factor >= goal * 2:
                return flag
        return cv2.IMREAD_COLOR

    @staticmethod
    def _write_atomic(target: Path, payload: bytes) -> None:
        """Közös helper (#129), egyedi temp-névvel: a provider több szálról
        is kérheti ugyanazt a thumbnailt. A cache tartalma újragenerálható,
        ezért fsync nem kell (durable=False); a replace sharing violationje
        (#66) lenyelhető, ha a thumbnail közben a párhuzamos írótól
        létrejött (ignore_replace_race)."""
        write_atomic(
            target,
            payload,
            durable=False,
            make_parents=True,
            ignore_replace_race=True,
        )

    def _scale_down(self, image, target: int | None = None):
        goal = self._size if target is None else target
        height, width = image.shape[:2]
        longest = max(width, height)
        if longest <= goal:
            return image
        scale = goal / longest
        new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)


def _decode_video_frame(source: Path):
    """Az első dekódolható képkocka a videóból, vagy None.

    Szándékosan NEM bájt-alapú (np.fromfile) út: egy mp4 több száz MB is
    lehet, hálózati mappán a teljes beolvasás percekre akasztaná a
    thumbnail-szálat — a VideoCapture streamelve csak a képkockához
    szükséges részt olvassa.
    """
    capture = cv2.VideoCapture(str(source))
    try:
        if not capture.isOpened():
            return None
        ok, frame = capture.read()
        if not ok or frame is None:
            return None
        return frame
    except cv2.error:
        return None
    finally:
        capture.release()


def _decode_image(source: Path, flag: int):
    """Bájt-alapú dekódolás a cv2.imread helyett (#65): az imread Windows-on
    az ANSI fájl-API-val nyit, ékezetes útvonalon (pl. „Képek") némán None-t
    ad. A np.fromfile a Python unicode-biztos fájlkezelésével olvas, az
    imdecode pedig az imread-del azonosan dekódol (EXIF-forgatással)."""
    try:
        payload = np.fromfile(source, dtype=np.uint8)
    except OSError:
        return None  # időközben törölt/elérhetetlen forrás (NAS)
    if payload.size == 0:
        return None
    return cv2.imdecode(payload, flag)
