"""Kijelölt képek exportja célmappába (Ctrl+Shift+S) — issue #16, #136.

A render-motor (V2) előtti első kör: a forgatás (rotate_steps), a
`filters=` lánc és a külön `crop=` kulcs beleégetése, opcionális
átméretezés OpenCV-vel, állítható JPEG-minőséggel. Ha egy elemen nincs mit
beégetni, bájthű másolás történik
(mtime-őrző) — nincs felesleges generációs veszteség. A videók bitre pontos
másolással kerülnek át. Az újrakódolt JPEG-ekbe a forrás EXIF/IPTC-adata
(dátum, GPS, kameraadat, felirat, kulcsszavak) szegmens-szinten átkerül,
mert a JPEG-kódolók nem visznek át maguktól metaadatot. Az UI-bekötés (hibaút,
QML) az integrátor lépése."""

from __future__ import annotations

import logging
import shutil
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

import numpy as np

from picasapy.cvimage import scale_down
from picasapy.ini import IniDocument, load_or_empty
from picasapy.ini.filters import parse_filters_prefix
from picasapy.ini.photo_crop import log_unreadable_ini_once
from picasapy.ioutil import write_atomic
from picasapy.metadata.export_metadata import bajtmasolas, frissitett_metaadat
from picasapy.render.text_fonts import DEFAULT_FAMILY as DEFAULT_FAMILY
from picasapy.render.text_fonts import load_font
from picasapy.scanner import PICASA_INI_NAME
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS

from .export_jpeg import (
    _JPEG_EXTENSIONS as _JPEG_EXTENSIONS,
    _WATERMARK_COLOR as _WATERMARK_COLOR,
    _WATERMARK_FONT_DIVISOR as _WATERMARK_FONT_DIVISOR,
    _WATERMARK_MIN_FONT_SIZE as _WATERMARK_MIN_FONT_SIZE,
    _WATERMARK_MIN_HEIGHT as _WATERMARK_MIN_HEIGHT,
    _apply_watermark as _apply_watermark_impl,
    _encode_jpeg as _encode_jpeg,
    _encode_with_source_qtables as _encode_with_source_qtables,
    _first_frame as _first_frame,
    _is_noop_copy as _is_noop_copy,
    _source_jpeg_parameters as _source_jpeg_parameters,
    _subsampling_from_layer as _subsampling_from_layer,
    _watermark_font_size_px as _watermark_font_size_px,
)
from .export_metadata import _write_ini_metadata as _write_ini_metadata
from .export_models import ExportItem, ExportReport
from .export_paths import (
    _PurgeError as _PurgeError,
    _purge_target as _purge_target,
    _unique_target as _unique_target,
)
from .export_pixels import (
    _apply_filter_chain as _apply_filter_chain,
    _apply_rotation as _apply_rotation,
    _decode_image as _decode_image,
    _export_filter_ops as _export_filter_ops,
    _rotations as _rotations,
    render_photo_pixels,
)
from .export_settings import (
    _AUTOMATIC_KEY as _AUTOMATIC_KEY,
    _AUTOMATIC_QUALITY as _AUTOMATIC_QUALITY,
    _QUALITY_PRESETS as _QUALITY_PRESETS,
    ExportSettings,
    is_automatic_quality as is_automatic_quality,
    resolve_export_quality as resolve_export_quality,
    resolve_export_subsampling as resolve_export_subsampling,
)

_LOG = logging.getLogger(__name__)

# Az `ExportSettings` immutábilis (frozen dataclass), ezért egyetlen
# modul-szintű példány biztonságosan megosztható alapértékként — elkerüli a
# B008-at (function-call a default argumentumban) viselkedésváltozás nélkül.
_DEFAULT_EXPORT_SETTINGS = ExportSettings()


def export_photos(
    items: Iterable[ExportItem],
    target_dir: Path,
    settings: ExportSettings = _DEFAULT_EXPORT_SETTINGS,
    *,
    purge_existing: bool = False,
) -> ExportReport:
    """Elemek exportja a célmappába; egy elem hibája nem állítja le a többit.

    Sosem hal el némán (#136): a célmappa létrehozásának hibája (pl. tele
    lemez, jogosultság) és bármely elem feldolgozási hibája is a strukturált
    `ExportReport.failed` listában landol — a hívó (worker-szál) mindig
    tud jelezni, sosem hal meg csendben kivétellel."""
    items = tuple(items)
    target_dir = Path(target_dir)
    error_kind = ""
    try:
        if purge_existing:
            error_kind = _purge_target(target_dir)
            if error_kind:
                raise _PurgeError(error_kind)
        target_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, _PurgeError) as error:
        # A célmappa nélkül egyetlen elem sem exportálható — mindet
        # hibásként jelezzük, ahelyett hogy a kivétel megölné a hívó szálat.
        failed_sources = tuple(Path(item.source) for item in items)
        reason = f"célmappa nem hozható létre: {error}"
        return ExportReport(
            exported=(),
            failed=failed_sources,
            reasons=(reason,) * len(failed_sources),
            error_kind=error_kind or "destdir",
        )

    exported: list[Path] = []
    failed: list[Path] = []
    reasons: list[str] = []
    source_ini_cache: dict[Path, IniDocument] = {}
    # #369: a sorszám-szélesség a teljes kötegméretből számol, hogy a
    # fájlrendszer ábécésorrendje 1000+ elemnél se törje meg a sorrendet
    # ("0999-..." < "1000-..." csak azonos szélesség mellett igaz).
    number_width = max(3, len(str(len(items))))
    for index, item in enumerate(items, start=1):
        source = Path(item.source)
        prefix = f"{index:0{number_width}d}-" if settings.add_numbers else ""
        try:
            crop_ini_readable = True
            crop = None
            if source.suffix.lower() not in VIDEO_EXTENSIONS:
                try:
                    crop = _source_crop(source, source_ini_cache)
                except OSError as error:
                    crop_ini_readable = False
                    log_unreadable_ini_once(
                        source.parent / PICASA_INI_NAME, error
                    )
            exported.append(
                _export_one(
                    source,
                    item,
                    target_dir,
                    settings,
                    prefix,
                    crop,
                    crop_ini_readable,
                )
            )
        except Exception as error:  # noqa: BLE001 — egy rossz elem nem állíthatja le a köteget
            failed.append(source)
            reasons.append(str(error))
    _write_ini_metadata(target_dir, tuple(zip(items, exported, strict=False)))
    return ExportReport(
        exported=tuple(exported),
        failed=tuple(failed),
        reasons=tuple(reasons),
        # #1166: ha bármelyik fájl írása elbukott, a köteg üzenete az
        # eredeti lemezhiba-szövege (`CImageOutput::filewriteerr`)
        error_kind="write" if failed else "",
    )


def _export_one(
    source: Path, item: ExportItem, target_dir: Path, settings: ExportSettings,
    number_prefix: str = "", crop: str | None = None,
    crop_ini_readable: bool = True,
) -> Path:
    if source.suffix.lower() in VIDEO_EXTENSIONS:
        if not settings.movie_full:
            # #1166: „Első képkocka" — a videóból egyetlen JPEG lesz. Ha a
            # kocka nem olvasható, NEM veszítjük el a felvételt: a teljes
            # film másolására esünk vissza (az eredeti is fájlt ad, nem
            # semmit).
            frame = _first_frame(source)
            if frame is not None:
                target = _unique_target(
                    target_dir, number_prefix + source.stem, ".jpg"
                )
                _write_jpeg(frame, target, settings)
                return target
        target = _unique_target(target_dir, number_prefix + source.stem, source.suffix)
        shutil.copy2(source, target)  # copy2: mtime is átkerül (#136)
        return target

    # #1140: az OLVASÓ ág elvágja a láncot a hibás tagnál, és soha nem
    # dob — egy idegen `.picasa.ini` hibás lánca nem hiúsíthatja meg az
    # exportot. A felhasználó ettől kapott KEVESEBB képet, mint amennyit
    # kijelölt.
    ops = parse_filters_prefix(item.filters) if item.filters else ()
    ops = _export_filter_ops(
        ops,
        crop,
        crop_ini_readable=crop_ini_readable,
        warning_key=str(source),
    )
    if _is_noop_copy(source, item, settings):
        # Az érvényesség-ellenőrzéshez dekódolunk (a sérült/nem-kép forrás
        # így is a `failed` listára kerül), de az eredményt eldobjuk — a
        # célfájlba a forrás EREDETI bájtjai kerülnek, generációs veszteség
        # nélkül.
        _decode_image(source)
        target = _unique_target(
            target_dir, number_prefix + source.stem, source.suffix.lower()
        )
        shutil.copy2(source, target)  # bájthű másolás, nincs generációs veszteség
        return target

    image = render_photo_pixels(
        source,
        ops,
        rotate_steps=item.rotate_steps,
        flip_flags=item.flip_flags,
    )
    image = scale_down(image, settings.max_dimension)
    image = _apply_watermark(image, settings.watermark_text)
    height, width = image.shape[:2]
    taken_at_override = (
        datetime.fromisoformat(item.taken_at_override)
        if item.taken_at_override
        else None
    )
    payload = _transfer_metadata(
        source,
        _encode_jpeg(image, settings, source),
        (width, height),
        taken_at_override=taken_at_override,
    )
    target = _unique_target(target_dir, number_prefix + source.stem, ".jpg")
    # Közös helper (#129): fsync + atomikus csere — félkész célfájl sose
    # maradjon (NAS/tele lemez).
    write_atomic(target, payload)
    return target

def _write_jpeg(image: np.ndarray, target: Path, settings: ExportSettings) -> None:
    """Kép JPEG-be, a köteg minőségével és méretkorlátjával (#1166) —
    a kép-ág utolsó lépéseinek megfelelője a videó első kockájához.

    Forrás nincs (a kocka egy videóból jön), ezért az „Automatikus"
    itt mindig a visszaesési értékkel kódol — filmnek nincs DQT-je."""
    image = scale_down(image, settings.max_dimension)
    image = _apply_watermark(image, settings.watermark_text)
    write_atomic(target, _encode_jpeg(image, settings, None))


def _source_crop(source: Path, cache: dict[Path, IniDocument]) -> str | None:
    """A Picasa aktuális kivágása a képszekció `crop=` kulcsában áll (#4008).

    A forrásmappánkénti dokumentum-cache elkerüli, hogy egy tömeges export
    ugyanazt a `.picasa.ini`-t minden képnél újraolvassa. Olvasási hibát a
    hívó naplóz és az eredeti filters-lánccal esik vissza.
    """
    ini_path = source.parent / PICASA_INI_NAME
    document = cache.get(ini_path)
    if document is None:
        document = load_or_empty(ini_path)
        cache[ini_path] = document
    section = document.section(source.name)
    return section.get("crop") if section is not None else None


def _apply_watermark(image: np.ndarray, text: str | None) -> np.ndarray:
    """Vízjel az exportáló modul régi, monkeypatch-elhető belépési pontján."""
    return _apply_watermark_impl(image, text, font_loader=load_font)


def _transfer_metadata(
    source: Path,
    encoded: bytes,
    size: tuple[int, int],
    *,
    taken_at_override: datetime | None = None,
) -> bytes:
    """Az újrakódolt JPEG metaadatai az eredeti Picasa szerint (#136, #3961).

    A JPEG-kódoló a metaadatot elhagyja. A forrás EXIF-je és XMP-je NEM
    bájtra kerül át: az export ideje, a kimeneti méret és a hiányzó mezők
    a `metadata/export_metadata.py` leírása szerint frissülnek; az IPTC
    (APP13) változatlanul megy. `size` a kimeneti kép (szélesség, magasság).

    A kép exportja SOHA nem bukhat el a metaadat miatt: bármely hibánál a
    régi, bájtra másoló út (#136) a kimenet; ha az is dob (ugyanazt a
    szegmens-kódot használja), a kép metaadat nélkül megy ki."""
    try:
        return frissitett_metaadat(
            source, encoded, size=size, taken_at_override=taken_at_override
        )
    except Exception:  # noqa: BLE001 — a metaadat soha nem buktathat exportot
        _LOG.warning("export: a metaadat-frissítés hibázott, bájtmásolás", exc_info=True)
    try:
        return bajtmasolas(source, encoded)
    except Exception:  # noqa: BLE001 — a kép SOHA nem eshet ki az exportból
        _LOG.warning("export: %s metaadat nélkül exportálva", source, exc_info=True)
        return encoded
