"""Determinisztikus referencia-képgenerátor a hisztogram-összevetéshez (#236).

A modul ~9-10 apró, előre ismert hisztogramú képet állít elő numpy-val. A
képek `uint8` (H, W, 3) RGB-tömbök — pontosan az a formátum, amit a
`picasapy.app.histogram_helper.compute_rgb_histogram` vár. A generálás
tisztán determinisztikus (nincs véletlen), így a hisztogram-csúcsok
pozíciója bitre kiszámítható és tesztelhető.

Minden képhez egy `ReferenceImage` tartozik, amely leírja a VÁRT
hisztogram-alakot (mely bin(ek)ben van csúcs csatornánként, illetve hogy a
csatorna lapos/egyenletes-e). Ezt használja a `test_histogram_reference.py`
az automatikus ellenőrzéshez, és a `tools/histogram/render_reference.py` a
render-golden előállításához.

A `write_reference_pngs()` PNG-be is kimenti a képeket (opcionális,
OpenCV-vel), hogy a felhasználó ugyanezeket a fájlokat a Windows-os Picasa
3-ban megnyithassa és golden-screenshotot készíthessen — ld.
`docs/specs/histogram-reference.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# A referencia-képek kanonikus mérete. A rámpánál a szélesség 256, hogy
# minden 0..255 intenzitás PONTOSAN egyszer forduljon elő oszloponként —
# így a szürke rámpa hisztogramja tökéletesen egyenletes.
_HEIGHT = 32
_WIDTH = 256


@dataclass(frozen=True)
class ReferenceImage:
    """Egy referencia-kép a hozzá tartozó várt hisztogram-leírással.

    Attribútumok:
        name: rövid, fájlnév-barát azonosító (pl. ``"pure_red"``).
        title: emberi cím (a doksihoz / golden-fájlnévhez).
        shape_doc: a várt hisztogram-alak szöveges leírása (magyarul).
        array: a kép mint ``uint8`` (H, W, 3) RGB-tömb.
        expected_peaks: csatornánként (``"r"``/``"g"``/``"b"``) azok a
            bin-indexek, ahol a NORMALIZÁLT érték 1.0 (a csúcs). Üres lista =
            a csatorna teljesen üres (csupa nulla) VAGY lapos-egyenletes;
            ezt a ``flat_channels`` különbözteti meg.
        flat_channels: azok a csatornák, amelyek hisztogramja közel
            egyenletes (nincs kiugró csúcs — pl. szürke rámpa). Ezekre a
            teszt nem egyetlen csúcsot, hanem laposságot ellenőriz.
    """

    name: str
    title: str
    shape_doc: str
    array: np.ndarray
    expected_peaks: dict[str, list[int]] = field(default_factory=dict)
    flat_channels: tuple[str, ...] = ()


def _solid(r: int, g: int, b: int) -> np.ndarray:
    """Egyszínű (H, W, 3) uint8 tömb a megadott RGB-értékkel."""
    img = np.empty((_HEIGHT, _WIDTH, 3), dtype=np.uint8)
    img[:, :, 0] = r
    img[:, :, 1] = g
    img[:, :, 2] = b
    return img


def _gray_ramp() -> np.ndarray:
    """Vízszintes szürke rámpa 0→255 (oszloponként egy-egy intenzitás)."""
    row = np.arange(_WIDTH, dtype=np.uint8)  # 0..255
    img = np.repeat(row[np.newaxis, :, np.newaxis], _HEIGHT, axis=0)
    return np.repeat(img, 3, axis=2)  # mindhárom csatorna azonos → szürke


def _two_tone(low: int, high: int) -> np.ndarray:
    """Két-tónusú 50/50 szürke kép: bal fél ``low``, jobb fél ``high``."""
    img = _solid(low, low, low)
    half = _WIDTH // 2
    img[:, half:, :] = high
    return img


def _rgb_gradient() -> np.ndarray:
    """Vízszintes piros→zöld→kék átmenet.

    Az első felében piros→zöld lineárisan keveredik (R csökken, G nő), a
    második felében zöld→kék (G csökken, B nő). Így mindhárom csatorna a
    teljes 0..255 tartományt bejárja, de eltérő eloszlással.
    """
    img = np.zeros((_HEIGHT, _WIDTH, 3), dtype=np.uint8)
    half = _WIDTH // 2
    left = np.linspace(0, 255, half, dtype=np.float64)
    # bal fél: piros → zöld
    img[:, :half, 0] = (255 - left).astype(np.uint8)  # R: 255 → 0
    img[:, :half, 1] = left.astype(np.uint8)  # G: 0 → 255
    # jobb fél: zöld → kék
    right = np.linspace(0, 255, _WIDTH - half, dtype=np.float64)
    img[:, half:, 1] = (255 - right).astype(np.uint8)  # G: 255 → 0
    img[:, half:, 2] = right.astype(np.uint8)  # B: 0 → 255
    return img


def reference_images() -> list[ReferenceImage]:
    """A teljes referencia-készlet (9 kép), determinisztikusan generálva."""
    return [
        ReferenceImage(
            name="pure_red",
            title="Tiszta piros (255,0,0)",
            shape_doc=(
                "Az R-csatorna egyetlen csúcsa a legfelső binben (255); a G "
                "és B csatorna teljesen üres (csak a 0-s binben van érték)."
            ),
            array=_solid(255, 0, 0),
            expected_peaks={"r": [255], "g": [0], "b": [0]},
        ),
        ReferenceImage(
            name="pure_green",
            title="Tiszta zöld (0,255,0)",
            shape_doc=(
                "A G-csatorna egyetlen csúcsa a 255-ös binben; R és B a 0-s "
                "binben."
            ),
            array=_solid(0, 255, 0),
            expected_peaks={"r": [0], "g": [255], "b": [0]},
        ),
        ReferenceImage(
            name="pure_blue",
            title="Tiszta kék (0,0,255)",
            shape_doc=(
                "A B-csatorna egyetlen csúcsa a 255-ös binben; R és G a 0-s "
                "binben."
            ),
            array=_solid(0, 0, 255),
            expected_peaks={"r": [0], "g": [0], "b": [255]},
        ),
        ReferenceImage(
            name="white",
            title="Fehér (255,255,255)",
            shape_doc=(
                "Mindhárom csatorna egyetlen csúcsa a legfelső binben (255); "
                "sehol máshol nincs érték."
            ),
            array=_solid(255, 255, 255),
            expected_peaks={"r": [255], "g": [255], "b": [255]},
        ),
        ReferenceImage(
            name="black",
            title="Fekete (0,0,0)",
            shape_doc=(
                "Mindhárom csatorna egyetlen csúcsa a legalsó binben (0). A "
                "compute_rgb_histogram a normalizálás után is helyes csúcsot "
                "ad a 0-s binben (minden pixel oda esik)."
            ),
            array=_solid(0, 0, 0),
            expected_peaks={"r": [0], "g": [0], "b": [0]},
        ),
        ReferenceImage(
            name="mid_gray",
            title="Középszürke (128,128,128)",
            shape_doc=(
                "Mindhárom csatorna egyetlen csúcsa a középső binben (128); "
                "sehol máshol nincs érték. A három görbe pontosan fedésben."
            ),
            array=_solid(128, 128, 128),
            expected_peaks={"r": [128], "g": [128], "b": [128]},
        ),
        ReferenceImage(
            name="gray_ramp",
            title="Vízszintes szürke rámpa 0→255",
            shape_doc=(
                "Tökéletesen egyenletes (lapos) hisztogram mindhárom "
                "csatornán: minden 0..255 intenzitás pontosan ugyanannyiszor "
                "fordul elő, így normalizálás után minden bin értéke ~1.0. "
                "Nincs kiugró csúcs."
            ),
            array=_gray_ramp(),
            flat_channels=("r", "g", "b"),
        ),
        ReferenceImage(
            name="two_tone_64_192",
            title="Két-tónusú 50/50 (64 és 192 szürke)",
            shape_doc=(
                "Két, egyforma magas csúcs mindhárom csatornán: a 64-es és a "
                "192-es binben (fej-fej mellett, mindkettő normalizálva 1.0). "
                "Minden más bin üres."
            ),
            array=_two_tone(64, 192),
            expected_peaks={"r": [64, 192], "g": [64, 192], "b": [64, 192]},
        ),
        ReferenceImage(
            name="rgb_gradient",
            title="RGB-átmenet (piros→zöld→kék, vízszintesen)",
            shape_doc=(
                "Mindhárom csatorna a teljes 0..255 tartományt bejárja, de "
                "eltérő eloszlással: a G-csatorna kétszer fut végig a "
                "tartományon (fel, majd le), az R csak lefelé, a B csak "
                "felfelé. A hisztogram szélesen szórt, nincs egyetlen éles "
                "csúcs — a 0-s és 255-ös bin környéke a legdúsabb (a végpontok "
                "telített színei miatt)."
            ),
            array=_rgb_gradient(),
            flat_channels=("r", "g", "b"),
        ),
    ]


# Modul-szintű, egyszer legenerált készlet (a képek immutábilisek, a tömbök
# csak olvasásra kellenek).
REFERENCES: list[ReferenceImage] = reference_images()


def reference_by_name(name: str) -> ReferenceImage:
    """A megadott nevű referencia-kép, vagy ``KeyError``, ha nincs ilyen."""
    for ref in REFERENCES:
        if ref.name == name:
            return ref
    raise KeyError(f"Ismeretlen referencia-kép: {name!r}")


def write_reference_pngs(out_dir: Path) -> list[Path]:
    """A referencia-képeket PNG-be írja (OpenCV-vel), és visszaadja az utakat.

    A PNG-ket a felhasználó a Windows-os Picasa 3-ban megnyithatja a
    golden-screenshotokhoz (ld. docs/specs/histogram-reference.md). Az
    OpenCV BGR-sorrendet vár, ezért a mentés előtt megfordítjuk a
    csatornákat. Az OpenCV importja lusta (csak itt kell), hogy a
    tesztek/generátor OpenCV nélkül is működjenek.
    """
    import cv2

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for ref in REFERENCES:
        path = out_dir / f"{ref.name}.png"
        bgr = ref.array[:, :, ::-1]  # RGB → BGR az OpenCV-nek
        if not cv2.imwrite(str(path), bgr):
            raise RuntimeError(f"PNG-írás sikertelen: {path}")
        written.append(path)
    return written
