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
import logging
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.cvimage import (
    hosszabb_el,
    read_image_bytes,
    reduced_color_flag,
    scale_down,
    scale_down_picasa_mag,
)
from picasapy.ini.filters import FilterOp, serialize_filters
from picasapy.ioutil import write_atomic
from picasapy.rawdecode import dekodol_nyerset, nyers_hosszabb_el, nyers_utvonal
from picasapy.render import apply_filters, normalize_crop_ops
from picasapy.render.elonezeti_arany import elonezeti_arany
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS
from picasapy.thumbs.prune import prune_cache_dir, prune_in_background
from picasapy.thumbs.szintek import szint_cellahoz, szintek
from picasapy.thumbs.cache_generation import _CacheGenerationMixin
from picasapy.thumbs.cache_storage import _CacheStorageMixin
from picasapy.thumbs.cache_policy import (
    _EDIT_BASE_CAP,
    _EDIT_BASE_FACTOR,
    _EDIT_BASE_MIN,
    _EDIT_CACHE_VERSION,
    _VIDEO_DECODE_TIMEOUT_S,
    _VIDEO_FALLBACK_LOCK,
    _ffmpeg_allapot,
    _futtato,
)

__all__ = [
    "FilterOp",
    "Path",
    "ThumbnailCache",
    "VIDEO_EXTENSIONS",
    "apply_filters",
    "cv2",
    "dekodol_nyerset",
    "elonezeti_arany",
    "hashlib",
    "hosszabb_el",
    "logging",
    "normalize_crop_ops",
    "np",
    "nyers_hosszabb_el",
    "nyers_utvonal",
    "open_video",
    "os",
    "prune_cache_dir",
    "prune_in_background",
    "read_image_bytes",
    "reduced_color_flag",
    "scale_down",
    "scale_down_picasa_mag",
    "serialize_filters",
    "subprocess",
    "sys",
    "szint_cellahoz",
    "szintek",
    "tempfile",
    "threading",
    "write_atomic",
]

_log = logging.getLogger(__name__)

_JPEG_QUALITY = 85

def _ffmpeg_elerheto() -> bool:
    """Van-e FFMPEG-háttér az OpenCV-ben (egyszer kiszámolva, gyorstárazva)."""
    global _ffmpeg_allapot
    if _ffmpeg_allapot is None:
        _ffmpeg_allapot = (
            cv2.CAP_FFMPEG in cv2.videoio_registry.getStreamBackends()
        )
    return _ffmpeg_allapot


def _video_decode_worker_command(source: Path, output: Path) -> list[str]:
    """A videóképkockát dekódoló alfolyamat parancsa.

    A PyInstalleres windowsos program a saját belépőjén át indítja a rejtett
    worker-módot; normál Python-telepítésnél a modult indítjuk.
    """
    if getattr(_futtato, "frozen", False):
        return [
            _futtato.executable,
            "--picasapy-video-decode",
            str(source),
            str(output),
        ]
    return [
        _futtato.executable,
        "-m",
        "picasapy.thumbs.video_decode_worker",
        str(source),
        str(output),
    ]


def _decode_video_frame_isolated(
    source: Path, *, timeout_s: float | None = None
):
    """Az első képkockát elszigetelt dekóderből kéri le, határidővel.

    A natív OpenCV-hívás gyermekfolyamatban fut. A határidő lejártakor a
    gyermek leáll, így a beragadt dekóder és a natív összeomlás sem ragadja
    magával a főfolyamatot vagy a rácsot. `timeout_s` csak célzott tesztnek
    adható meg; a termékút a rögzített `_VIDEO_DECODE_TIMEOUT_S` értéket
    használja.
    """
    hatarido = _VIDEO_DECODE_TIMEOUT_S if timeout_s is None else timeout_s
    try:
        with tempfile.TemporaryDirectory(prefix="picasapy-video-decode-") as tmp:
            kepfajl = Path(tmp) / "frame.png"
            worker_env = None
            if not getattr(sys, "frozen", False):
                worker_env = os.environ.copy()
                package_root = str(Path(__file__).resolve().parents[2])
                pythonpath = worker_env.get("PYTHONPATH")
                worker_env["PYTHONPATH"] = os.pathsep.join(
                    [package_root, *([pythonpath] if pythonpath else [])]
                )
            eredmeny = subprocess.run(
                _video_decode_worker_command(source, kepfajl),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=hatarido,
                check=False,
                env=worker_env,
            )
            if eredmeny.returncode != 0:
                reszlet = eredmeny.stderr.decode(
                    "utf-8", errors="replace"
                ).strip()
                _log.warning(
                    "a videóból nem készült képkocka, bélyegkép nélkül "
                    "marad: %s%s",
                    source,
                    f" ({reszlet[-1000:]})" if reszlet else "",
                )
                return None
            try:
                payload = kepfajl.read_bytes()
            except OSError:
                _log.warning(
                    "a videódekóder nem adta vissza a képkockát, "
                    "bélyegkép nélkül marad: %s",
                    source,
                    exc_info=True,
                )
                return None
    except subprocess.TimeoutExpired:
        _log.warning(
            "a videó képkockájának dekódolása túllépte a %.1f másodperces "
            "időkorlátot, bélyegkép nélkül marad: %s",
            hatarido,
            source,
        )
        return None
    except OSError:
        _log.warning(
            "a videó dekódoló alfolyamata nem indítható el, bélyegkép "
            "nélkül marad: %s",
            source,
            exc_info=True,
        )
        return None

    if not payload:
        _log.warning(
            "a videódekóder üres képkockát adott vissza, bélyegkép nélkül "
            "marad: %s",
            source,
        )
        return None
    try:
        frame = cv2.imdecode(
            np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR
        )
    except cv2.error:
        _log.warning(
            "a videó alfolyamatának képkockája nem olvasható, bélyegkép "
            "nélkül marad: %s",
            source,
            exc_info=True,
        )
        return None
    if frame is None:
        _log.warning(
            "a videó alfolyamata érvénytelen képkockát adott vissza, "
            "bélyegkép nélkül marad: %s",
            source,
        )
    return frame


def _edit_base_size(target_size: int) -> int:
    """A szerkesztett bélyegkép rendereléséhez használt bázisméret (#525):
    legalább `_EDIT_BASE_MIN`, legfeljebb `_EDIT_BASE_CAP`, a kettő között
    a célméret `_EDIT_BASE_FACTOR`-szorosa."""
    return min(_EDIT_BASE_CAP, max(target_size * _EDIT_BASE_FACTOR, _EDIT_BASE_MIN))


def _bazis_arany(source: Path, dekodolt: np.ndarray, bazis: np.ndarray) -> float:
    """A renderelt bázis és a TELJES felbontású forrás aránya (#3472).

    A teljes méret a fejlécből jön (nyers fájlnál a LibRaw méret-mezőiből);
    videónál és olvashatatlan fejlécnél a dekódolt képkocka a mérce. A
    dekód maga is kicsinyíthet (`IMREAD_REDUCED_*`), ezért nem elég a
    dekódolt kép méretét nézni."""
    if source.suffix.lower() in VIDEO_EXTENSIONS:
        teljes = None
    elif nyers_utvonal(source):
        teljes = nyers_hosszabb_el(source)
    else:
        teljes = hosszabb_el(source)
    if not teljes:
        teljes = max(dekodolt.shape[0], dekodolt.shape[1])
    return min(1.0, max(bazis.shape[0], bazis.shape[1]) / teljes)


class ThumbnailCache(_CacheGenerationMixin, _CacheStorageMixin):
    def get_or_create_edited(
        self,
        photo_path: str | Path,
        mtime_ns: int,
        size_bytes: int,
        ops: tuple[FilterOp, ...],
        level: int | None = None,
        *,
        crop: str | None,
        crop_ini_readable: bool = True,
    ) -> Path | None:
        """Szerkesztett bélyegkép: a `filters=` láncot nagy felbontású
        bázison alkalmazza, majd a végeredményt kicsinyíti a célméretre
        (#163, a bázisméret pontos meghatározása #525: `_edit_base_size`).

        Lánc nélkül a szűretlen thumbnailra esik vissza. A forgatás nem itt
        történik (a hívó a kész — kicsi — bélyegképen forgat, ami veszteség-
        mentes). A cache-kulcs tartalmazza a láncot, így a szerkesztett
        bélyegkép külön fájlba kerül és görgetéskor nem kell újraszámolni."""
        effective_ops = normalize_crop_ops(
            ops,
            crop,
            crop_ini_readable=crop_ini_readable,
            warning_key=str(photo_path),
        )
        if not effective_ops:
            return self.get_or_create(photo_path, mtime_ns, size_bytes, level)
        source = Path(photo_path)
        lanc = serialize_filters(effective_ops)
        px = self._size if level is None else self.level_for(level)
        target = self.edited_thumbnail_path(
            source, mtime_ns, size_bytes, lanc, px
        )
        if target.exists():
            return target
        #: #598: a kis szint a FELSŐ szint kész, szerkesztett bélyegképéből
        #: áll elő — a `filters=` láncot sosem futtatjuk kétszer ugyanarra a
        #: képre. A lánc drága (nagy bázison fut), a kicsinyítés nem.
        if px != self._size:
            nagy = self.get_or_create_edited(
                source,
                mtime_ns,
                size_bytes,
                ops,
                crop=crop,
                crop_ini_readable=crop_ini_readable,
            )
            if nagy is None:
                return None
            payload = read_image_bytes(nagy)
            if payload is None:
                return None
            kep = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_COLOR)
            if kep is None:
                return None
            ok, encoded = cv2.imencode(
                ".jpg",
                scale_down_picasa_mag(kep, px),
                [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY],
            )
            if not ok:
                return None
            try:
                self._write_atomic(target, encoded.tobytes())
            except OSError:
                return None
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
        # #3472: a bázis kisebb a teljes képnél — a keret két vastagsága
        # ezzel az aránnyal skálázódik, mint az eredetiben (`imageWidth /
        # fullResImageWidth`, ld. `render/elonezeti_arany.py`), különben a
        # bélyegképen sokszorosan vastagabb, mint a mentett képen.
        with elonezeti_arany(_bazis_arany(source, base, rgb)):
            rendered, _skipped = apply_filters(rgb, effective_ops)
        thumb = cv2.cvtColor(scale_down_picasa_mag(rendered, self._size),
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
        self,
        photo_path: Path,
        mtime_ns: int,
        size_bytes: int,
        chain: str,
        level: int | None = None,
    ) -> Path:
        # #525: a kulcsban az _EDIT_CACHE_VERSION is szerepel — ha a
        # bázisméret-képlet változik, a régi (esetleg hibásan sötét)
        # lemez-cache-bejegyzések automatikusan érvénytelenné válnak,
        # ahelyett hogy örökre beragadnának.
        px = self._size if level is None else level
        key = (
            f"{photo_path}\x00{mtime_ns}\x00{size_bytes}\x00{px}"
            f"\x00e{_EDIT_CACHE_VERSION}\x00{chain}"
        )
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        gyoker = self._root if px == self._size else self._root / f"sz{px}"
        return gyoker / digest[:2] / f"{digest}.jpg"

    def _decode_source(self, source: Path, target: int | None = None):
        """Forrás → BGR numpy kép: videónál egy képkocka, képnél imdecode.

        `target`: a redukált beolvasás célmérete (a szerkesztő-bázis
        nagyobb, mint a sima thumbnailé). Alapból a cache saját mérete."""
        if source.suffix.lower() in VIDEO_EXTENSIONS:
            return _decode_video_frame_isolated(source)
        if nyers_utvonal(source):
            # #528: a nyers (RAW) fájlnak nincs `cv2` dekódere — a LibRaw-ra
            # kell mennie. A célméretet átadjuk: ha a fájlban van beágyazott
            # JPEG-előnézet, abból nagyságrenddel gyorsabb a bélyegkép.
            return dekodol_nyerset(source, self._size if target is None else target)
        # #144: a forrást EGYSZER olvassuk be — a méret-próba és a dekódolás
        # ugyanabból a bájtpufferből dolgozik (korábban PIL Image.open +
        # np.fromfile kétszer nyitotta a fájlt, ami NAS-on drága).
        payload = read_image_bytes(source)
        if payload is None:
            return None
        return cv2.imdecode(payload, self._read_flag(payload, target))


def _open_video(source: Path) -> cv2.VideoCapture:
    """A videó megnyitása a #673 szerint rögzített háttérrel.

    FFMPEG-es OpenCV-n kényszerítetten `cv2.CAP_FFMPEG` (nincs visszaesés a
    GStreamerre); FFMPEG nélküli buildben marad az automatikus választás, de
    sorosítva — a részletes indoklás és a mérési számok a modul tetején."""
    if _ffmpeg_elerheto():
        return cv2.VideoCapture(str(source), cv2.CAP_FFMPEG)
    with _VIDEO_FALLBACK_LOCK:
        return cv2.VideoCapture(str(source))


#: #1838: a videó-megnyitás EGYETLEN útja a projektben. A képkocka-mentés
#: (`app/frame_capture_controller.py`) ugyanezt használja — külön
#: `VideoCapture`-hívás a #673 háttér-rögzítését kerülné meg.
open_video = _open_video


def _decode_video_frame(source: Path):
    """Az első dekódolható képkocka a videóból, vagy None.

    Szándékosan NEM bájt-alapú (np.fromfile) út: egy mp4 több száz MB is
    lehet, hálózati mappán a teljes beolvasás percekre akasztaná a
    thumbnail-szálat — a VideoCapture streamelve csak a képkockához
    szükséges részt olvassa.

    A sikertelenség SOHA nem néma: a hívó (`ThumbnailProvider`) a hiányzó
    bélyegképet placeholderrel és `brokenImageDetected` jelzéssel mutatja
    meg, itt pedig naplóba kerül a fájl neve és a bukás pontos oka is —
    enélkül a sérült videó csak egy megmagyarázhatatlan üres cella lenne.
    """
    capture = _open_video(source)
    try:
        if not capture.isOpened():
            _log.warning(
                "a videó nem nyitható meg (sérült vagy nem támogatott "
                "kódek), bélyegkép nélkül marad: %s",
                source,
            )
            return None
        ok, frame = capture.read()
        if not ok or frame is None:
            _log.warning(
                "a videóból nem olvasható képkocka, bélyegkép nélkül "
                "marad: %s",
                source,
            )
            return None
        return frame
    except cv2.error:
        _log.warning(
            "a videó dekódolása OpenCV-hibával elbukott, bélyegkép nélkül "
            "marad: %s",
            source,
            exc_info=True,
        )
        return None
    finally:
        capture.release()
