"""OpenCV-alapú thumbnail-generálás lemez-gyorsítótárral (ADR: rpi5-image-libs).

A cache-kulcs a forrásfájl útvonalából + mtime-jából + méretéből képzett
hash: fájlváltozáskor automatikusan új bejegyzés készül, az elárvult
régieket a méretkorlátos LRU-takarító (`prune.py`, #144) tünteti el —
induláskor háttérszálon fut, ha a cache méretkorláttal jött létre.
Az OpenCV imdecode alapból alkalmazza az
EXIF-orientációt, ezért a thumbnail már helyesen forgatott.
"""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path

import cv2
import numpy as np

from picasapy.cvimage import read_image_bytes, reduced_color_flag, scale_down
from picasapy.ini.filters import FilterOp, serialize_filters
from picasapy.ioutil import write_atomic
from picasapy.render import apply_filters
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS
from picasapy.thumbs.prune import prune_cache_dir, prune_in_background

_JPEG_QUALITY = 85

# #163: a szerkesztett (filters=) bélyegkép bázisa a célméret többszöröse —
# a lánc (jellemzően crop64) a nagy bázison fut, és csak a VÉGEREDMÉNYT
# kicsinyítjük a célméretre. Így az erős vágás után is éles marad a kép
# (nem a kész kis thumbnailt vágjuk tovább, amit a rács homályosan
# felnagyítana). A faktor 4: 25%-os vágás után a kimenet még pont a teljes
# célméret; ennél erősebb vágásnál is jóval élesebb a naiv útnál.
_EDIT_BASE_FACTOR = 4

# #525: a Glimmer-effektek (Holga, Lomo, Vignette, ...) sugár-/elmosás-
# képletei RÉSZBEN abszolút képpontszámban vannak megadva (a Flash
# `blurX`/`blurY` 255-ös korlátjának öröksége, ld. `glimmer_ops.
# clamp_glow_radius`) — ha a láncot a MÁR kicsinyített (pl. 96–256px-es)
# thumbnailra futtatjuk, ez a sugár relatíve sokszorosan szélesebb
# vignettát rajzol, mint amit Picasa nagy (2560px-es) exportján látni
# (mérve: #525 jegy, `referencia/holga` és `referencia/lomo`). A puszta
# `_EDIT_BASE_FACTOR` (kis thumbnail-méretnél 96×4=384, 256×4=1024) ezt
# NEM oldja meg — a mérés szerint a torzulás csak kb. 1500–2000px-es
# bázisnál kezd belapulni. Ezért a bázis egy ALSÓ KORLÁTOT is kap
# (`_EDIT_BASE_MIN`) a puszta szorzat mellé, felül pedig egy teljesítmény-
# korlátot (`_EDIT_BASE_CAP`) — 2560px-es (natív méretű) bázison a Holga
# ~1 mp/kép, ami a bélyegkép-gyorsítótár (egyszeri, háttérszálas) útjára
# nézve nagyságrendi lassulás lenne. A mért kompromisszum (2560×1702-es
# referenciafotón, Holga): bázis 1536px → átlagfény-eltérés a Picasa
# kimenetétől 33,2 (a "kicsinyít-majd-effektez" út 47,9-éhez képest),
# 0,57 mp/kép; bázis 2048px → 21,2, 1,08 mp/kép; teljes (2560px) → 14,1,
# 2,65 mp/kép. Az 1536–2048-as sáv adja a legjobb arányt — jelentős
# javulás, a lassulás pedig még mindig kevesebb, mint egy nagyságrend a
# korábbi (384–1024px-es) bázishoz képest.
_EDIT_BASE_MIN = 1536
_EDIT_BASE_CAP = 2048

# #525: a bázisméret-képlet fenti változása miatt a RÉGI (a bug miatt
# sötét) szerkesztett bélyegképeket el kell avultatni — a cache-kulcs a
# forrás/mtime/méret/lánc mellé ezt a verziószámot is beleszámítja, így a
# meglévő lemez-cache-ben ragadt sötét bejegyzések nem találatot adnak,
# hanem újragenerálódnak az új bázismérettel. Csak a #163 SZERKESZTETT
# (`filters=` láncos) bélyegképeket érinti — a sima `get_or_create` út
# (a könyvtár nagy része) változatlan, nem kell újragenerálódnia.
_EDIT_CACHE_VERSION = 2


def _edit_base_size(target_size: int) -> int:
    """A szerkesztett bélyegkép rendereléséhez használt bázisméret (#525):
    legalább `_EDIT_BASE_MIN`, legfeljebb `_EDIT_BASE_CAP`, a kettő között
    a célméret `_EDIT_BASE_FACTOR`-szorosa."""
    return min(_EDIT_BASE_CAP, max(target_size * _EDIT_BASE_FACTOR, _EDIT_BASE_MIN))


class ThumbnailCache:
    def __init__(
        self,
        root: str | Path,
        size: int = 256,
        max_bytes: int | None = None,
    ):
        """`max_bytes`: a lemez-cache méretkorlátja (#144) — ha meg van
        adva, induláskor háttérszálon lefut az LRU-takarító, hogy a
        `~/.cache` alatti tár ne nőjön korlátlanul."""
        self._root = Path(root)
        self._size = size
        self._max_bytes = max_bytes
        # A szál referenciáját eltároljuk, hogy a hívó (pl. teszt) be
        # tudja várni — enélkül a takarítás versenyezne a mappa-törléssel.
        self._prune_thread: threading.Thread | None = None
        if max_bytes is not None:
            self._prune_thread = prune_in_background(self._root, max_bytes)

    def prune(self) -> int:
        """Szinkron LRU-takarítás a beállított korlátig; a törölt bájtok
        száma. Korlát nélkül nem csinál semmit (0)."""
        if self._max_bytes is None:
            return 0
        return prune_cache_dir(self._root, self._max_bytes)

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
        thumb = scale_down(image, self._size)
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
        bázison alkalmazza, majd a végeredményt kicsinyíti a célméretre
        (#163, a bázisméret pontos meghatározása #525: `_edit_base_size`).

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
        base_size = _edit_base_size(self._size)
        base = self._decode_source(source, base_size)
        if base is None:
            return None
        rgb = cv2.cvtColor(scale_down(base, base_size),
                           cv2.COLOR_BGR2RGB)
        # #301: a hibás/idegen lánc-bejegyzést az apply_filters saját maga
        # hagyja ki (kivétel nem szökik ki innen) — a lánc többi tagja lefut,
        # a #73-elv (szűretlen kép a placeholder helyett) így is teljesül.
        rendered, _skipped = apply_filters(rgb, ops)
        thumb = cv2.cvtColor(scale_down(rendered, self._size),
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
        # #525: a kulcsban az _EDIT_CACHE_VERSION is szerepel — ha a
        # bázisméret-képlet változik, a régi (esetleg hibásan sötét)
        # lemez-cache-bejegyzések automatikusan érvénytelenné válnak,
        # ahelyett hogy örökre beragadnának.
        key = (
            f"{photo_path}\x00{mtime_ns}\x00{size_bytes}\x00{self._size}"
            f"\x00e{_EDIT_CACHE_VERSION}\x00{chain}"
        )
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return self._root / digest[:2] / f"{digest}.jpg"

    def _decode_source(self, source: Path, target: int | None = None):
        """Forrás → BGR numpy kép: videónál egy képkocka, képnél imdecode.

        `target`: a redukált beolvasás célmérete (a szerkesztő-bázis
        nagyobb, mint a sima thumbnailé). Alapból a cache saját mérete."""
        if source.suffix.lower() in VIDEO_EXTENSIONS:
            return _decode_video_frame(source)
        # #144: a forrást EGYSZER olvassuk be — a méret-próba és a dekódolás
        # ugyanabból a bájtpufferből dolgozik (korábban PIL Image.open +
        # np.fromfile kétszer nyitotta a fájlt, ami NAS-on drága).
        payload = read_image_bytes(source)
        if payload is None:
            return None
        return cv2.imdecode(payload, self._read_flag(payload, target))

    def _read_flag(self, payload: np.ndarray, target: int | None = None) -> int:
        """Dekódolási flag a MÁR beolvasott bájtokból: nagy képre redukált
        beolvasás (memóriakímélés). A döntés a közös `picasapy.cvimage.
        reduced_color_flag`-ben él (#294) — ugyanazt hívja a dedup dHash-e is."""
        return reduced_color_flag(payload, self._size if target is None else target)

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
