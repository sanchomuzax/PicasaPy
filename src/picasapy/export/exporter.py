"""Kijelölt képek exportja célmappába (Ctrl+Shift+S) — issue #16, #136.

A render-motor (V2) előtti első kör: a forgatás (rotate_steps) és a
`filters=` lánc beleégetése, opcionális átméretezés OpenCV-vel, állítható
JPEG-minőséggel. Ha egy elemen nincs mit beégetni, bájthű másolás történik
(mtime-őrző) — nincs felesleges generációs veszteség. A videók bitre pontos
másolással kerülnek át. Az újrakódolt JPEG-ekbe a forrás EXIF/IPTC-adata
(dátum, GPS, kameraadat, felirat, kulcsszavak) szegmens-szinten átkerül,
mert a `cv2.imencode` semmit nem visz át magától. Az UI-bekötés (hibaút,
QML) az integrátor lépése."""

from __future__ import annotations

import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from picasapy.ini.filters import FilterOp, parse_filters
from picasapy.ioutil import write_atomic
from picasapy.render import apply_filters
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS

_ROTATIONS = {
    1: cv2.ROTATE_90_CLOCKWISE,
    2: cv2.ROTATE_180,
    3: cv2.ROTATE_90_COUNTERCLOCKWISE,
}

# A bájthű (no-op) másolás csak valódi JPEG-forrásra alkalmazható — más
# formátumot mindenképp JPEG-be kell kódolni (meglévő viselkedés).
_JPEG_EXTENSIONS = frozenset({".jpg", ".jpeg"})

# JPEG-fejléc: SOI + a metaadatot hordozó APP-szegmensek markerei.
# 0xE0 = APP0 (JFIF, a cv2.imencode ezt írja — érintetlenül hagyjuk),
# 0xE1 = APP1 (EXIF és/vagy XMP), 0xED = APP13 (Photoshop/IPTC).
_SOI = b"\xff\xd8"
_SOS_MARKER = 0xDA
_METADATA_MARKERS = frozenset({0xE1, 0xED})


@dataclass(frozen=True)
class ExportSettings:
    """Export-beállítások: leghosszabb oldal (None = eredeti) és JPEG-minőség."""

    max_dimension: int | None = None
    jpeg_quality: int = 85

    def __post_init__(self) -> None:
        if self.max_dimension is not None and self.max_dimension < 1:
            raise ValueError(f"Érvénytelen max_dimension: {self.max_dimension}")
        if not 1 <= self.jpeg_quality <= 100:
            raise ValueError(f"Érvénytelen jpeg_quality: {self.jpeg_quality}")


@dataclass(frozen=True)
class ExportItem:
    """Egy exportálandó elem: forrásfájl + beégetendő forgatás (90°-os
    lépések) + opcionális `filters=` lánc (nyers, szerializált formában,
    ahogy a `.picasa.ini`-ben/indexben áll)."""

    source: Path
    rotate_steps: int = 0
    filters: str | None = None


@dataclass(frozen=True)
class ExportReport:
    """Az exportfutás eredménye: kész célfájlok és sikertelen források."""

    exported: tuple[Path, ...]
    failed: tuple[Path, ...]


def export_photos(
    items: Iterable[ExportItem],
    target_dir: Path,
    settings: ExportSettings = ExportSettings(),
) -> ExportReport:
    """Elemek exportja a célmappába; egy elem hibája nem állítja le a többit.

    Sosem hal el némán (#136): a célmappa létrehozásának hibája (pl. tele
    lemez, jogosultság) és bármely elem feldolgozási hibája is a strukturált
    `ExportReport.failed` listában landol — a hívó (worker-szál) mindig
    tud jelezni, sosem hal meg csendben kivétellel."""
    items = tuple(items)
    target_dir = Path(target_dir)
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # A célmappa nélkül egyetlen elem sem exportálható — mindet
        # hibásként jelezzük, ahelyett hogy a kivétel megölné a hívó szálat.
        return ExportReport(exported=(), failed=tuple(Path(item.source) for item in items))

    exported: list[Path] = []
    failed: list[Path] = []
    for item in items:
        source = Path(item.source)
        try:
            exported.append(_export_one(source, item, target_dir, settings))
        except Exception:  # noqa: BLE001 — egy rossz elem nem állíthatja le a köteget
            failed.append(source)
    return ExportReport(exported=tuple(exported), failed=tuple(failed))


def _export_one(
    source: Path, item: ExportItem, target_dir: Path, settings: ExportSettings
) -> Path:
    if source.suffix.lower() in VIDEO_EXTENSIONS:
        target = _unique_target(target_dir, source.stem, source.suffix)
        shutil.copy2(source, target)  # copy2: mtime is átkerül (#136)
        return target

    ops = parse_filters(item.filters) if item.filters else ()
    if _is_noop_copy(source, item, settings, ops):
        # Az érvényesség-ellenőrzéshez dekódolunk (a sérült/nem-kép forrás
        # így is a `failed` listára kerül), de az eredményt eldobjuk — a
        # célfájlba a forrás EREDETI bájtjai kerülnek, generációs veszteség
        # nélkül.
        _decode_image(source)
        target = _unique_target(target_dir, source.stem, source.suffix.lower())
        shutil.copy2(source, target)  # bájthű másolás, nincs generációs veszteség
        return target

    image = _decode_image(source)
    image = _apply_filter_chain(image, ops)
    image = _apply_rotation(image, item.rotate_steps)
    image = _scale_down(image, settings.max_dimension)
    ok, encoded = cv2.imencode(
        ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, settings.jpeg_quality]
    )
    if not ok:
        raise ValueError(f"JPEG-kódolás sikertelen: {source}")
    payload = _transfer_metadata(source, encoded.tobytes())
    target = _unique_target(target_dir, source.stem, ".jpg")
    # Közös helper (#129): fsync + atomikus csere — félkész célfájl sose
    # maradjon (NAS/tele lemez).
    write_atomic(target, payload)
    return target


def _is_noop_copy(
    source: Path, item: ExportItem, settings: ExportSettings, ops: tuple[FilterOp, ...]
) -> bool:
    """Nincs mit beégetni: se forgatás, se átméretezés, se szerkesztés — és a
    forrás már JPEG. Ilyenkor a sima másolás a helyes (bájthű, mtime-őrző)."""
    return (
        source.suffix.lower() in _JPEG_EXTENSIONS
        and item.rotate_steps % 4 == 0
        and settings.max_dimension is None
        and not ops
    )


def _apply_filter_chain(image: np.ndarray, ops: tuple[FilterOp, ...]) -> np.ndarray:
    """A `filters=` lánc beleégetése — a meglévő render-lánccal (RGB-térben,
    mint a bélyegkép-gyorsítótár, ld. `thumbs/cache.py`).

    Hibás/idegen lánc-bejegyzésnél (#73-elv) a szűretlen kép a helyes
    visszaesés, nem az export teljes meghiúsulása."""
    if not ops:
        return image
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    try:
        rendered, _skipped = apply_filters(rgb, ops)
    except Exception:  # noqa: BLE001
        return image
    return cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR)


def _decode_image(source: Path) -> np.ndarray:
    """Bájt-alapú dekódolás a cv2.imread helyett (#65 tanulság: az imread
    Windowson ékezetes útvonalon némán None-t ad). EXIF-forgatással dekódol."""
    payload = np.fromfile(source, dtype=np.uint8)
    if payload.size == 0:
        raise ValueError(f"Üres forrásfájl: {source}")
    image = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Nem dekódolható kép: {source}")
    return image


def _apply_rotation(image: np.ndarray, rotate_steps: int) -> np.ndarray:
    """90°-os órairányú lépések beégetése (a Picasa/Qt konvenciója szerint)."""
    steps = rotate_steps % 4
    if steps == 0:
        return image
    return cv2.rotate(image, _ROTATIONS[steps])


def _scale_down(image: np.ndarray, max_dimension: int | None) -> np.ndarray:
    """A leghosszabb oldal korlátozása; felskálázás soha nincs."""
    if max_dimension is None:
        return image
    height, width = image.shape[:2]
    longest = max(width, height)
    if longest <= max_dimension:
        return image
    scale = max_dimension / longest
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)


def _transfer_metadata(source: Path, encoded: bytes) -> bytes:
    """A forrás EXIF (APP1) és IPTC/Photoshop (APP13) szegmenseinek átvitele
    az újrakódolt JPEG-bájtokba (#136) — a `cv2.imencode` ezeket elhagyja,
    a Picasa exportja viszont megőrzi a dátumot, GPS-t, kameraadatot,
    feliratot és kulcsszavakat.

    Szegmens-szintű, nyers másolás: nem kell értelmezni a tartalmat, a
    forrás bájtjai kerülnek át változatlanul, a cv2 által írt JFIF (APP0)
    UTÁN beszúrva (szabványos sorrend). Sérült/nem-JPEG forrásnál, vagy ha
    nincs átvihető szegmens, a bemenet változatlanul visszaadva."""
    try:
        source_bytes = source.read_bytes()
    except OSError:
        return encoded
    if not source_bytes.startswith(_SOI) or not encoded.startswith(_SOI):
        return encoded
    segments = _extract_app_segments(source_bytes, _METADATA_MARKERS)
    if not segments:
        return encoded
    insert_at = _after_app0(encoded)
    return encoded[:insert_at] + b"".join(segments) + encoded[insert_at:]


def _extract_app_segments(data: bytes, markers: frozenset[int]) -> list[bytes]:
    """A SOI utáni, kért markerű APP-szegmensek nyers bájtjai, sorrendben."""
    segments: list[bytes] = []
    pos = 2
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            break
        marker = data[pos + 1]
        if marker == 0xFF:  # kitöltő bájt
            pos += 1
            continue
        if marker == _SOS_MARKER:
            break
        length = int.from_bytes(data[pos + 2 : pos + 4], "big")
        if length < 2 or pos + 2 + length > len(data):
            break
        if marker in markers:
            segments.append(data[pos : pos + 2 + length])
        pos += 2 + length
    return segments


def _after_app0(data: bytes) -> int:
    """A beszúrási pont: a vezető APP0 (JFIF) szegmens után, vagy az SOI
    után, ha nincs APP0."""
    if len(data) >= 4 and data[2] == 0xFF and data[3] == 0xE0:
        length = int.from_bytes(data[4:6], "big")
        return 4 + length
    return 2


def _unique_target(target_dir: Path, stem: str, suffix: str) -> Path:
    """Ütközésmentes célnév: `név.jpg`, `név-1.jpg`, `név-2.jpg`, ..."""
    candidate = target_dir / f"{stem}{suffix}"
    counter = 1
    while candidate.exists():
        candidate = target_dir / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate
