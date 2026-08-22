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

from picasapy.cvimage import read_image_bytes, scale_down
from picasapy.ini import IniConflictError, IniSaveError, update_document
from picasapy.ini.filters import FilterOp, parse_filters_prefix
from picasapy.ioutil import write_atomic
from picasapy.render import apply_filters
from picasapy.scanner import PICASA_INI_NAME
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

    def __post_init__(self) -> None:
        if self.max_dimension is not None and self.max_dimension < 1:
            raise ValueError(f"Érvénytelen max_dimension: {self.max_dimension}")
        if not 1 <= self.jpeg_quality <= 100:
            raise ValueError(f"Érvénytelen jpeg_quality: {self.jpeg_quality}")


# #369 (export.fen "Image quality" popup): a Picasa pontos preset-értékei
# nem dokumentáltak (a UI csak "Automatic/Normal/Maximum/Minimum/Custom"
# feliratokat mutat, számot nem) — ez egy jóhiszemű, dokumentáltan közelítő
# leképezés ésszerű JPEG-minőségekre. "Automatic" nem 100%-ig hű "forrás-
# minőség": ha nincs mit beégetni (ld. _is_noop_copy), a bájthű másolás
# amúgy is megőrzi az eredeti fájlt változtatás nélkül; ha viszont muszáj
# újrakódolni (forgatás/átméretezés/szűrő/vízjel), egy közelítő, majdnem
# veszteségmentes értéket használunk, mert az eredeti kódoló minőségének
# megbízható visszafejtése (kvantálási táblákból) külön kutatást igényelne.
_QUALITY_PRESETS: dict[str, int] = {
    "normal": 85,
    "maximum": 100,
    "minimum": 70,
}
_AUTOMATIC_QUALITY_APPROXIMATION = 92


def resolve_export_quality(preset: str, custom: int) -> int:
    """Minőség-preset névből (a QML popup elemeiből) konkrét JPEG-minőség.

    `preset`: "normal" | "maximum" | "minimum" | "custom" | "automatic"
    (kis-nagybetűtől független); ismeretlen/üres preset — és maga
    "automatic" is — a közelítő automatikus értékre esik vissza.
    `custom` csak `preset == "custom"` esetén számít, és 1–100 közé kell
    essen (ugyanaz a korlát, mint az `ExportSettings.jpeg_quality`-é)."""
    key = (preset or "").strip().lower()
    if key == "custom":
        if not 1 <= custom <= 100:
            raise ValueError(f"Érvénytelen egyéni minőség: {custom}")
        return custom
    return _QUALITY_PRESETS.get(key, _AUTOMATIC_QUALITY_APPROXIMATION)


@dataclass(frozen=True)
class ExportItem:
    """Egy exportálandó elem: forrásfájl + beégetendő forgatás (90°-os
    lépések) + opcionális `filters=` lánc (nyers, szerializált formában,
    ahogy a `.picasa.ini`-ben/indexben áll)."""

    source: Path
    rotate_steps: int = 0
    filters: str | None = None
    # #1166: a `.picasa.ini` `caption`/`keywords` mezője ÁTKERÜL a
    # célmappába — az eredetiben ezt a közös kimeneti mag (`CImageOutput`,
    # `0x0073f320`) végzi. Üresen hagyva nem születik ini a célban.
    caption: str | None = None
    keywords: str | None = None


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
    # #369: a sorszám-szélesség a teljes kötegméretből számol, hogy a
    # fájlrendszer ábécésorrendje 1000+ elemnél se törje meg a sorrendet
    # ("0999-..." < "1000-..." csak azonos szélesség mellett igaz).
    number_width = max(3, len(str(len(items))))
    for index, item in enumerate(items, start=1):
        source = Path(item.source)
        prefix = f"{index:0{number_width}d}-" if settings.add_numbers else ""
        try:
            exported.append(_export_one(source, item, target_dir, settings, prefix))
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
    number_prefix: str = "",
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
    if _is_noop_copy(source, item, settings, ops):
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
    image = _apply_rotation(image, item.rotate_steps)
    image = scale_down(image, settings.max_dimension)
    image = _apply_watermark(image, settings.watermark_text)
    ok, encoded = cv2.imencode(
        ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, settings.jpeg_quality]
    )
    if not ok:
        raise ValueError(f"JPEG-kódolás sikertelen: {source}")
    payload = _transfer_metadata(source, encoded.tobytes())
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
    a kép-ág utolsó lépéseinek megfelelője a videó első kockájához."""
    image = scale_down(image, settings.max_dimension)
    image = _apply_watermark(image, settings.watermark_text)
    ok, encoded = cv2.imencode(
        ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, settings.jpeg_quality]
    )
    if not ok:
        raise ValueError(f"JPEG-kódolás sikertelen: {target}")
    write_atomic(target, encoded.tobytes())


def _is_noop_copy(
    source: Path, item: ExportItem, settings: ExportSettings, ops: tuple[FilterOp, ...]
) -> bool:
    """Nincs mit beégetni: se forgatás, se átméretezés, se szerkesztés, se
    vízjel — és a forrás már JPEG. Ilyenkor a sima másolás a helyes (bájthű,
    mtime-őrző); a sorszámozás (#369) csak a fájlnevet érinti, a bájthű
    másolást nem zárja ki."""
    return (
        source.suffix.lower() in _JPEG_EXTENSIONS
        and item.rotate_steps % 4 == 0
        and settings.max_dimension is None
        and not settings.watermark_text
        and not ops
    )


def _apply_watermark(image: np.ndarray, text: str | None) -> np.ndarray:
    """A vízjelszöveg beégetése a jobb alsó sarokba, fehér, félig átlátszó
    (#369, a Picasa mintáját közelítve — a pontos betűtípus/méret a Picasa
    forráskódja nélkül nem rekonstruálható, ez egy olvasható, arányos
    közelítés). Üres/`None` szöveg esetén a kép változatlan."""
    if not text:
        return image
    height, width = image.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.5, min(width, height) / 500)
    thickness = max(1, round(font_scale * 2))
    (text_width, text_height), _baseline = cv2.getTextSize(
        text, font, font_scale, thickness
    )
    margin = max(6, round(min(width, height) * 0.02))
    x = max(0, width - text_width - margin)
    y = max(text_height, height - margin)
    overlay = image.copy()
    cv2.putText(
        overlay, text, (x, y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA
    )
    alpha = 0.6  # félig átlátszó, a Picasa alapértelmezett mintájához hasonlóan
    return cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)


def _apply_filter_chain(image: np.ndarray, ops: tuple[FilterOp, ...]) -> np.ndarray:
    """A `filters=` lánc beleégetése — a meglévő render-lánccal (RGB-térben,
    mint a bélyegkép-gyorsítótár, ld. `thumbs/cache.py`).

    Hibás/idegen lánc-bejegyzésnél (#73-elv) a szűretlen kép a helyes
    visszaesés, nem az export teljes meghiúsulása — ezt a #301 óta maga az
    apply_filters garantálja (a hibás op kimarad, kivétel nem szökik ki)."""
    if not ops:
        return image
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rendered, _skipped = apply_filters(rgb, ops)
    return cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR)


def _decode_image(source: Path) -> np.ndarray:
    """Bájt-alapú dekódolás a közös helperrel (`picasapy.cvimage`, #151/7).
    EXIF-forgatással dekódol; hibánál emberi olvasásra szánt kivétel."""
    payload = read_image_bytes(source)
    if payload is None:
        raise ValueError(f"Üres vagy nem olvasható forrásfájl: {source}")
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
