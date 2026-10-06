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

import io
import logging
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np
from PIL import Image, ImageDraw, UnidentifiedImageError

from picasapy.cvimage import dekodolj_forrast, scale_down
from picasapy.ini import (
    IniConflictError,
    IniDocument,
    IniSaveError,
    load_or_empty,
    update_document,
)
from picasapy.ini.photo_crop import log_unreadable_ini_once
from picasapy.ini.filters import FilterOp, parse_filters_prefix
from picasapy.ioutil import write_atomic
from picasapy.metadata.export_metadata import bajtmasolas, frissitett_metaadat
from picasapy.render import apply_filters, normalize_crop_ops
from picasapy.render.flip import FLIP_MASK, apply_flip
from picasapy.render.text_fonts import DEFAULT_FAMILY, load_font
from picasapy.scanner import PICASA_INI_NAME
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS

_LOG = logging.getLogger(__name__)

# #1611: FÜGGVÉNY, nem modulszintű konstans — modulszinten a `cv2.ROTATE_*`
# olvasása a BETÖLTÉSKOR behozná az OpenCV-t, és az `export` az indulási
# láncban van (`app/controller` → `app/export_controller` → `export`).
def _rotations() -> dict[int, int]:
    return {
        1: cv2.ROTATE_90_CLOCKWISE,
        2: cv2.ROTATE_180,
        3: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }

# A bájthű (no-op) másolás csak valódi JPEG-forrásra alkalmazható — más
# formátumot mindenképp JPEG-be kell kódolni (meglévő viselkedés).
_JPEG_EXTENSIONS = frozenset({".jpg", ".jpeg"})



@dataclass(frozen=True)
class ExportSettings:
    """Export-beállítások: leghosszabb oldal (None = eredeti), JPEG-minőség,
    sorszámozás (#369: „Add numbers to file names to preserve order") és
    opcionális vízjel-szöveg (#369)."""

    max_dimension: int | None = None
    jpeg_quality: int = 85
    # #369 (export.fen): a fájlnevek elé "001-", "002-", ... kerül, a
    # bemeneti (kijelölés-)sorrendet őrizve — mert a célmappában a fájlrendszer
    # ábécésorrendje egyébként felülírná azt.
    add_numbers: bool = False
    # #369 (export.fen): jobb alsó sarokba égetett szöveg, fehér, félig
    # átlátszó — a Picasa mintáját közelítve (ld. _apply_watermark).
    watermark_text: str | None = None
    # #1166 (export.fen `radiogroup name="movies"`): „Teljes film (nincs
    # átméretezés)" = a videó bájthű másolása (alapértelmezés), „Első
    # képkocka" = az első kocka képként. Az eredeti alapértéke a
    # `Preferences\FileExportMovie`-ból jön (`0x00738c88`–`0x00738cb3`):
    # nem nulla → teljes film, nulla/hiányzó → első képkocka.
    movie_full: bool = True
    # #1138 (spec 3.3 és 7.1): az „Automatikus" fokozat az eredetiben NEM
    # szám, hanem KÜLÖN LOGIKAI JELZŐ (`[objektum+0xa40] = 1`,
    # `0x00739c4d`), és a kimenet a FORRÁS JPEG-kvantálási tábláit veszi át
    # — mérve: a forrás és a Picasa exportjának DQT-je bájtra azonos,
    # miközben a fájlméret más (tehát tényleg újrakódolt). Bekapcsolva a
    # `jpeg_quality` már csak VISSZAESÉS: nem JPEG forrásnál vagy
    # olvashatatlan táblánál.
    quality_automatic: bool = False
    # #4017: a rögzített Picasa-leképezésben csak a Maximális használ
    # 4:4:4-et; a többi választás 4:2:0. Az Automatikus JPEG-forrásnál ezt
    # a forrás JPEG mintája felülírja.
    jpeg_subsampling: int = 2

    def __post_init__(self) -> None:
        if self.max_dimension is not None and self.max_dimension < 1:
            raise ValueError(f"Érvénytelen max_dimension: {self.max_dimension}")
        if not 1 <= self.jpeg_quality <= 100:
            raise ValueError(f"Érvénytelen jpeg_quality: {self.jpeg_quality}")
        if self.jpeg_subsampling not in (0, 1, 2):
            raise ValueError(f"Érvénytelen jpeg_subsampling: {self.jpeg_subsampling}")


# #4017 (kontrollált Picasa-export, picasa-colab-jobs #87–#91): a tényleges
# kimeneti JPEG alapján a Maximum IJG q=93 és 4:4:4; a Normal q=85, a
# Minimum q=65. Az Automatic a forrás DQT-jét és JPEG-mintáját viszi tovább,
# a Custom a csúszkán kapott minőséget használja. Ez felülírja a korábbi,
# bináris 193-as választási értékből levezetett „szándékosan 100” közelítést.
# A presetválasztás nyers értékei továbbra is a binárisból ismertek:
# a választás (0…4) a `0x00739c3f`-nél kezdődő ágon dől el, az ugrótábla
# `0x00739ef4`-en áll (levezetés: docs/specs/export-parbeszed.md 7. szakasz):
#
#   Normál     = 85  (`0x55`, `0x00739caf`)
#   Maximális  = 193 (`0xC1`, `0x00739ca1`; a kontrollált kimenet q=93)
#   Minimális  = 65  (`0x41`, `0x00739ca8`)
#
# #1138: az "automatic" SZÁMA is a binárisból való: az ugrótábla 0. ága
# ugyanoda fut, mint a "normal" — 85 (`0x00739caf`). A kettőt a `+0xa40`
# jelző különbözteti meg, és a jelző hatása az, hogy a kimenet a FORRÁS
# kvantálótábláit kapja (`ExportSettings.quality_automatic`). A 85 tehát
# itt már nem „közelítés", hanem a mért visszaesési érték arra az esetre,
# amikor nincs honnan táblát venni (nem JPEG forrás).
_AUTOMATIC_QUALITY = 85
_QUALITY_PRESETS: dict[str, int] = {
    "automatic": _AUTOMATIC_QUALITY,
    "normal": 85,
    "maximum": 93,
    "minimum": 65,
}

#: #1138 (spec 3.3): az „Automatikus" fokozat kulcsa — nem szám, hanem
#: külön logikai jelző az eredetiben is.
_AUTOMATIC_KEY = "automatic"


def is_automatic_quality(preset: str) -> bool:
    """Az „Automatikus" fokozatot választották-e (#1138).

    Külön kérdés a `resolve_export_quality`-tól, mert az eredetiben is
    külön logikai jelző (`[objektum+0xa40] = 1`, `0x00739c4d`), nem a
    minőségszám hordozza: a szám ugyanaz a 85, mint a „Normál"-nál."""
    return (preset or "").strip().lower() == _AUTOMATIC_KEY


def resolve_export_subsampling(preset: str) -> int:
    """A mért leképezés: Maximum 4:4:4, a többi fokozat 4:2:0 (#4017).

    Az Automatikus JPEG-forrás esetén a kódoló a forrás mintáját olvassa ki;
    ez az érték csak annak a visszaesési módja, ha nincs átvehető forrás.
    Pillow-kódolásnál a 0 = 4:4:4, 1 = 4:2:2, 2 = 4:2:0.
    """
    return 0 if (preset or "").strip().lower() == "maximum" else 2


def resolve_export_quality(preset: str, custom: int) -> int:
    """Minőség-preset névből (a QML popup elemeiből) konkrét JPEG-minőség.

    `preset`: "normal" | "maximum" | "minimum" | "custom" | "automatic"
    (kis-nagybetűtől független); ismeretlen/üres preset — és maga
    "automatic" is — a mért 85-re esik vissza (ld. `_AUTOMATIC_QUALITY`).
    `custom` csak `preset == "custom"` esetén számít, és 0–100 közé kell
    essen: a 21 fogásos egyéni csúszka 0-s állása 0×5 = 0-t adna, amit az
    IJG-kódoló maga emel 1-re (`if (quality <= 0) quality = 1`) — ezt itt
    tesszük meg, hogy a felület legalsó fogása se dobjon kivételt."""
    key = (preset or "").strip().lower()
    if key == "custom":
        if custom == 0:
            custom = 1
        if not 1 <= custom <= 100:
            raise ValueError(f"Érvénytelen egyéni minőség: {custom}")
        return custom
    return _QUALITY_PRESETS.get(key, _AUTOMATIC_QUALITY)


@dataclass(frozen=True)
class ExportItem:
    """Egy exportálandó elem: forrásfájl + beégetendő forgatás (90°-os
    lépések) + opcionális `filters=` lánc (nyers, szerializált formában,
    ahogy a `.picasa.ini`-ben/indexben áll). Az aktuális cropot külön,
    a forrás képszekciójának `crop=` kulcsából olvassuk."""

    source: Path
    rotate_steps: int = 0
    #: #2902: tükrözés-jelző (`1` = függőleges, `2` = vízszintes) — a
    #: forgatás párja, ugyanúgy beégetendő, hogy az exportált fájl a rácsban
    #: látott képpel egyezzen.
    flip_flags: int = 0
    filters: str | None = None
    # #1166: a `.picasa.ini` `caption`/`keywords` mezője ÁTKERÜL a
    # célmappába — az eredetiben ezt a közös kimeneti mag (`CImageOutput`,
    # `0x0073f320`) végzi. Üresen hagyva nem születik ini a célban.
    caption: str | None = None
    keywords: str | None = None
    # #4332: az indexben tárolt dátumfelülírás kerül az export EXIF-jébe.
    taken_at_override: str | None = None


@dataclass(frozen=True)
class ExportReport:
    """Az exportfutás eredménye: kész célfájlok és sikertelen források.

    A `reasons` a `failed`-del párhuzamos, azonos hosszúságú, emberi
    olvasásra szánt hibaüzenet-lista (#136) — a UI-hibajelzéshez, hogy a
    felhasználó lássa, MELYIK fájl és MIÉRT hiúsult meg, ne csak a számot."""

    exported: tuple[Path, ...]
    failed: tuple[Path, ...]
    reasons: tuple[str, ...] = ()
    # #1166: a KÖTEG szintű hiba fajtája — a hívó ebből választja ki az
    # eredeti Picasa saját üzenetét (`IDS_DESTDIRCANNOCREATE`,
    # `CExportPrefsPage::deleteerror` stb.), ahelyett hogy nyers OS-hibát
    # mutatna. Üres sztring = nincs köteg-szintű hiba.
    error_kind: str = ""


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


class _PurgeError(Exception):
    """Az ürítés hibája — a fajtáját (`delete`/`remove`/`scan`) a
    `_purge_target` adja, hogy a hívó az eredeti üzenetet válassza."""


def _purge_target(target_dir: Path) -> str:
    """A célmappa KIÜRÍTÉSE — az eredeti „igen, felülírom" ága (#1166).

    `CExportPrefsPage::destexists` („A cél már létezik. Felülírja az új
    albummal?") — igen esetén a program az ELŐZŐ albumot törli, nem
    mellé exportál.

    ⚠️ Csak a célmappa TARTALMÁT törli, magát a mappát nem, és sosem lép
    ki belőle. Nem létező mappánál nem csinál semmit; ha a cél egy fájl,
    érintetlenül hagyja — a hívó a `mkdir` hibáján át kap jelzést
    (`IDS_DESTDIRCANNOCREATE`)."""
    if not target_dir.is_dir():
        return ""
    try:
        entries = tuple(target_dir.iterdir())
    except OSError:
        # a cél LETAPOGATÁSA bukott — `CExportPrefsPage::scanerror`
        return "scan"
    for entry in entries:
        try:
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)      # `::removeerror` tartománya
            else:
                entry.unlink()            # `::deleteerror` tartománya
        except OSError:
            return "remove" if entry.is_dir() else "delete"
    return ""


def _write_ini_metadata(
    target_dir: Path, parok: tuple[tuple[ExportItem, Path], ...]
) -> None:
    """A `caption`/`keywords` átvitele a célmappa `.picasa.ini`-jébe (#1166).

    Egyetlen `update_document` hívással, a köteg végén: a párhuzamosan
    futó eredeti Picasa közbeírása így sem veszhet el (#295), és nem
    nyitjuk-zárjuk fájlonként. Adat nélküli kötegnél nem keletkezik ini.

    A szekció fejléce a CÉLFÁJL neve (sorszámozásnál `001-a.jpg`),
    különben az adatnak nem lenne gazdája."""
    ujak = {
        cel.name: {
            kulcs: ertek
            for kulcs, ertek in (("caption", item.caption), ("keywords", item.keywords))
            if ertek
        }
        for item, cel in parok
    }
    ujak = {nev: mezok for nev, mezok in ujak.items() if mezok}
    if not ujak:
        return
    ini_path = target_dir / PICASA_INI_NAME

    def modosit(document):
        for nev, mezok in ujak.items():
            for kulcs, ertek in mezok.items():
                # a `with_value` a hiányzó szekciót maga hozza létre, és ez
                # a `.picasa.ini` minden kulcsírásának közös kapuja (#643)
                document = document.with_value(nev, kulcs, ertek)
        return document

    try:
        update_document(ini_path, modosit)
    except (OSError, IniSaveError, IniConflictError):
        # Az ini-írás hibája NEM hiúsíthatja meg a kész exportot: a képek
        # a helyükön vannak, csak a felirat/címke marad el.
        pass


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

    image = _decode_image(source)
    image = _apply_filter_chain(image, ops)
    # #3065: ELŐBB a tükrözés, UTÁNA a forgatás — a mért sorrend (három
    # független összeállító, `docs/specs/picasa-ini-format.md` „⛳ MEGVAN A
    # SORREND”). A kettő nem kommutál: fölcserélve 90°/270° mellett a MÁSIK
    # tengelyre tükröz.
    image = apply_flip(image, item.flip_flags)
    image = _apply_rotation(image, item.rotate_steps)
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


def _first_frame(source: Path) -> np.ndarray | None:
    """A videó ELSŐ olvasható képkockája BGR tömbként, vagy `None` (#1166).

    Az eredeti „Első képkocka" választása ezt teszi a mappába a film
    helyett. Sosem dob: olvashatatlan felvételnél a hívó a teljes film
    másolására esik vissza."""
    capture = None
    try:
        capture = cv2.VideoCapture(str(source))
        if not capture.isOpened():
            return None
        ok, frame = capture.read()
        return frame if ok and frame is not None and frame.size else None
    except cv2.error:
        return None
    finally:
        if capture is not None:
            capture.release()


def _write_jpeg(image: np.ndarray, target: Path, settings: ExportSettings) -> None:
    """Kép JPEG-be, a köteg minőségével és méretkorlátjával (#1166) —
    a kép-ág utolsó lépéseinek megfelelője a videó első kockájához.

    Forrás nincs (a kocka egy videóból jön), ezért az „Automatikus"
    itt mindig a visszaesési értékkel kódol — filmnek nincs DQT-je."""
    image = scale_down(image, settings.max_dimension)
    image = _apply_watermark(image, settings.watermark_text)
    write_atomic(target, _encode_jpeg(image, settings, None))


def _encode_jpeg(
    image: np.ndarray, settings: ExportSettings, source: Path | None
) -> bytes:
    """A kirenderelt kép JPEG-bájtjai.

    Az „Automatikus" fokozatnál (#1138, #4017) a FORRÁS JPEG kvantálási
    tábláival és mintavételezésével kódolunk. Más fokozatoknál a mért
    minőséghez tartozó táblát és a fokozat saját mintavételezését használjuk."""
    if settings.quality_automatic and source is not None:
        payload = _encode_with_source_qtables(image, source)
        if payload is not None:
            return payload
    try:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        puffer = io.BytesIO()
        Image.fromarray(rgb).save(
            puffer,
            format="JPEG",
            quality=settings.jpeg_quality,
            subsampling=settings.jpeg_subsampling,
        )
    except (OSError, ValueError, TypeError, cv2.error) as exc:
        raise ValueError(f"JPEG-kódolás sikertelen: {source}") from exc
    return puffer.getvalue()


def _source_jpeg_parameters(source: Path) -> tuple[dict, int] | None:
    """A forrás JPEG kvantálási táblái és mintája, vagy `None`.

    Sosem dob: nem JPEG, sérült vagy olvashatatlan forrásnál `None` —
    a hívó ilyenkor a minőségszámos ágra esik vissza."""
    try:
        with Image.open(source) as kep:
            if kep.format != "JPEG":
                return None
            tablak = dict(kep.quantization)
            subsampling = _subsampling_from_layer(kep.layer)
    except (OSError, ValueError, UnidentifiedImageError):
        return None
    if not tablak or subsampling is None:
        return None
    return tablak, subsampling


def _encode_with_source_qtables(image: np.ndarray, source: Path) -> bytes | None:
    """Kódolás a forrás kvantálási tábláival (#1138), vagy `None`, ha nem
    megy — a hívó ilyenkor a szokásos úton kódol.

    A Pillow a beolvasott `quantization` szótárat `qtables=`-ként
    változtatás nélkül visszaveszi, tehát a kimenet DQT-je bájtra a
    forrásé lesz."""
    parameters = _source_jpeg_parameters(source)
    if parameters is None:
        return None
    tablak, subsampling = parameters
    try:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        puffer = io.BytesIO()
        Image.fromarray(rgb).save(
            puffer,
            format="JPEG",
            qtables=tablak,
            subsampling=subsampling,
        )
    except (OSError, ValueError, TypeError, cv2.error):
        return None
    return puffer.getvalue()


def _subsampling_from_layer(layer) -> int | None:
    """Pillow `Image.layer` komponensfaktoraiból JPEG-módot olvas ki."""
    try:
        components = tuple(layer)
        if len(components) not in (1, 3, 4):
            return None
        _y_id, y_h, y_v, _y_table = components[0]
        chroma_sampling = tuple(
            (h, v) for _id, h, v, _table in components[1:]
        )
        if any(factor != (1, 1) for factor in chroma_sampling):
            return None
    except (TypeError, ValueError):
        return None
    return {(1, 1): 0, (2, 1): 1, (2, 2): 2}.get((y_h, y_v))


def _is_noop_copy(
    source: Path,
    item: ExportItem,
    settings: ExportSettings,
) -> bool:
    """Nincs mit beégetni: se forgatás, se tükrözés (#3977), se átméretezés,
    se szerkesztés, se vízjel — és a forrás már JPEG. Ilyenkor a sima másolás a helyes (bájthű,
    mtime-őrző); a sorszámozás (#369) csak a fájlnevet érinti, a bájthű
    másolást nem zárja ki. A nem üres nyers `filters=` láncot akkor is
    újrakódoljuk, ha a renderelés egyes vagy összes tagot kihagy: az eredeti
    Picasa ilyenkor is új JPEG-et ír, és a metaadatoknak is le kell futniuk
    (#3997, #4017)."""
    return (
        source.suffix.lower() in _JPEG_EXTENSIONS
        and item.rotate_steps % 4 == 0
        and not int(item.flip_flags or 0) & FLIP_MASK
        and settings.max_dimension is None
        and not settings.watermark_text
        and not item.filters
        and not item.taken_at_override
    )


# #1603: a vízjel geometriai szabályai a `0x0045c4b0` dekompilálásából
# (955 bájt; hívja: `CPreparedDBImage` a `0x007948c0`-n, a `0x0045c430`-on
# át). Az állítás, hogy ezek a paraméterek „nem rekonstruálhatók" — MEGDŐLT.
#: 32 képpontnál ALACSONYABB MAGASSÁGÚ (nem a szélesség — ld. `cmp ecx,
#: 0x20` az `[esi+0xc]` = magasság mezőn) képre nem kerül vízjel; az
#: eredeti ilyenkor a 4-es hibakóddal tér vissza.
_WATERMARK_MIN_HEIGHT = 32
#: A betűméret alsó korlátja (`mov ebx, 0xc`), hogy nagyon kis képen se
#: legyen a felirat olvashatatlanul apró.
_WATERMARK_MIN_FONT_SIZE = 12
#: A betűméretet a kép HOSSZABB oldalából adja, egész osztással
#: (`0x51eb851f`-es szorzó + `shr edx, 4` ≡ osztás 50-nel).
_WATERMARK_FONT_DIVISOR = 50
#: A mérés (#1603) átlátszatlan fehéret mutatott (`0xffffffff`,
#: `[esp+0x88]`) — ez a jegy leggyengébb (bár „erős") bizonyítékú
#: állítása, mert a `0xFFFFFFFF` elméletileg „nincs színkulcs" jelölő is
#: lehetne. Egy windowsos referencia-export döntené el megnyugtatóan
#: (a kérdés a jegyben BLOKKOLTKÉNT szerepel); addig a mért értéket
#: (átlátszatlan, nincs alfa-keverés) visszük át — ez a korábbi
#: `alpha = 0.6` közelítést váltja fel.
_WATERMARK_COLOR = (255, 255, 255)


def _watermark_font_size_px(width: int, height: int) -> int:
    """A vízjel betűmérete képpontban (#1603): a kép HOSSZABB oldalából,
    egész osztással 50-nel, de legalább 12 képpont."""
    return max(_WATERMARK_MIN_FONT_SIZE, max(width, height) // _WATERMARK_FONT_DIVISOR)


def _apply_watermark(image: np.ndarray, text: str | None) -> np.ndarray:
    """A vízjelszöveg beégetése a jobb alsó sarokba (#369, pontosítva #1603).

    A paraméterek a Picasa `0x0045c4b0` függvényéből visszafejtettek:
    Arial, 600-as vastagság (félkövér), méretezés 1.0; betűméret =
    `max(12, hosszabb oldal // 50)` képpont; a margó mind a négy oldalon a
    betűmérettel egyenlő, ezért a szöveg jobb éle és alsó (leszálló) éle a
    `(szélesség - betűméret, magasság - betűméret)` pontra esik. 32
    képpontnál alacsonyabb MAGASSÁGÚ képre nem kerül vízjel (az eredeti
    ilyenkor a 4-es hibakóddal tér vissza — itt a kép egyszerűen
    változatlan marad). Üres/`None` szöveg esetén szintén nincs változás.

    Ha a gépen nincs használható TrueType-betű (pl. csupasz CI-kép), a
    rajzolás Hershey-visszaesésre vált (ld. `render.text_fonts.load_font`)
    — a méret/elhelyezés szabályai ilyenkor is érvényben maradnak, csak a
    betű ALAKJA közelítő, nem az eredeti Arial."""
    if not text:
        return image
    height, width = image.shape[:2]
    if height < _WATERMARK_MIN_HEIGHT:
        return image
    size = _watermark_font_size_px(width, height)
    margin = size
    anchor = (width - margin, height - margin)
    font = load_font(DEFAULT_FAMILY, size, bold=True)
    if font is not None:
        pil_image = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_image)
        # "rd" = jobb (right) + leszálló (descender) horgony: a szöveg
        # jobb és alsó éle pontosan az `anchor`-ra esik, ahogy a
        # dekompilált margó-számítás (jobb = szélesség-betűméret, alsó =
        # magasság-betűméret) is mutatja.
        draw.text(anchor, text, font=font, fill=_WATERMARK_COLOR, anchor="rd")
        return np.asarray(pil_image)
    # Hershey-visszaesés: nincs TrueType a gépen. A DUPLEX vaskosabb
    # vonala közelebb áll a 600-as vastagsághoz, mint a vékony SIMPLEX; a
    # méretezés a betűméret cél-nagybetű-magasságára hangolt.
    font_face = cv2.FONT_HERSHEY_DUPLEX
    font_scale = size / 22
    thickness = max(1, round(font_scale * 2))
    (text_width, _text_height), baseline = cv2.getTextSize(
        text, font_face, font_scale, thickness
    )
    origin = (anchor[0] - text_width, anchor[1] - baseline)
    result = image.copy()
    cv2.putText(
        result, text, origin, font_face, font_scale, _WATERMARK_COLOR,
        thickness, cv2.LINE_AA,
    )
    return result


def _apply_filter_chain(image: np.ndarray, ops: tuple[FilterOp, ...]) -> np.ndarray:
    """A szűrőlánc és az aktuális crop kulcs beleégetése — a meglévő
    render-lánccal (RGB-térben, mint a bélyegkép-gyorsítótár,
    ld. `thumbs/cache.py`).

    A `_export_filter_ops` a forrás képszekciójának `crop=` mezőjét az
    utolsó `crop64` tételen érvényesíti, annak láncbeli helyét megtartva.

    Hibás/idegen lánc-bejegyzésnél (#73-elv) a szűretlen kép a helyes
    visszaesés, nem az export teljes meghiúsulása — ezt a #301 óta maga az
    apply_filters garantálja (a hibás op kimarad, kivétel nem szökik ki)."""
    if not ops:
        return image
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rendered, _skipped = apply_filters(rgb, ops)
    return cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR)


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


def _export_filter_ops(
    ops: tuple[FilterOp, ...],
    crop: str | None,
    *,
    crop_ini_readable: bool = True,
    warning_key: str | None = None,
) -> tuple[FilterOp, ...]:
    """Az export közös render-előkészítője (#4008, #4013)."""
    return normalize_crop_ops(
        ops,
        crop,
        crop_ini_readable=crop_ini_readable,
        warning_key=warning_key,
    )


def _decode_image(source: Path) -> np.ndarray:
    """Bájt-alapú dekódolás a közös helperrel (`picasapy.cvimage`, #151/7).
    EXIF-forgatással dekódol; hibánál emberi olvasásra szánt kivétel.

    #3120: a közös belépőn megy, tehát a **nyers (RAW)** fájlok is
    exportálhatók — korábban a puszta `cv2.imdecode` némán `None`-t adott
    rájuk, és az export „nem dekódolható kép" hibával állt meg."""
    image = dekodolj_forrast(source)
    if image is None:
        raise ValueError(f"Nem dekódolható kép: {source}")
    return image


def _apply_rotation(image: np.ndarray, rotate_steps: int) -> np.ndarray:
    """90°-os órairányú lépések beégetése (a Picasa/Qt konvenciója szerint)."""
    steps = rotate_steps % 4
    if steps == 0:
        return image
    return cv2.rotate(image, _rotations()[steps])


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


def _unique_target(target_dir: Path, stem: str, suffix: str) -> Path:
    """Ütközésmentes célnév: `név.jpg`, `név-1.jpg`, `név-2.jpg`, ..."""
    candidate = target_dir / f"{stem}{suffix}"
    counter = 1
    while candidate.exists():
        candidate = target_dir / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate
