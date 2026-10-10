"""A mellőzött arc a `.picasa.ini`-ben (#3670) — a saját detektálásunk és a
`faces=…,ffffffffffffffff` régiók összevetése.

Élőben mérve (`docs/specs/picasa-arcfelismeres.md` 15.3/b.1): az eredeti
Picasa a mellőzött arcot a `faces=` sor személy-mezőjébe írt
`ffffffffffffffff`-fel jelöli. A régiót a SAJÁT detektora jelölte ki, tehát
a keret sosem bitre azonos a miénkkel (YuNet).

**Az egyeztetés mértéke: a metszet a KISEBBIK keret területéhez mérve.**
Mérve 2026-09-27-én, a tulajdonos könyvtárán (400 Picasa-keret, hat mappa,
a YuNet-találatokkal a termék saját dekódolásán): a Picasa kerete
területben a medián szerint ~2,3× NAGYOBB a miénknél (a homlokot és az
állat is befoglalja). Emiatt a sima IoU mediánja 0,43, és a 0,5-ös
IoU-küszöb a keretek 77%-át nem párosítaná. A kisebbik keretre vetített
átfedés ≥ 0,5 a keretek 88%-át párosítja.

**A küszöb 0,5:** az arc legalább fele a másik keretbe esik. Ugyanabban
a mérésben egy Picasa-keret és egy MÁSIK saját találat (a második
legjobb) átfedése 400-ból 6 esetben érte el a 0,5-öt (a keret két
találatot is lefedett). Ezt a páronkénti hozzárendelés (`match_regions`)
oldja fel: egy keret egyetlen találatot visz, a jobban illeszkedőt (a
sima IoU dönt a döntetlenben). A 400-ból 47 keretnek nem volt 0,5 fölötti
párja; a 400 keret legalább tizedénél (alsó decilis) a mi detektorunk
egyáltalán nem talált arcot a helyen (a legjobb átfedés 0). Az ilyen arc a „Mellőzött emberek"
albumban az ini-régiójával jelenik meg (`ignoredGroups`).
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Sequence
from pathlib import Path
from typing import TypeVar

from picasapy.ini import (
    UNIDENTIFIED_CONTACT,
    Rect64,
    decode_rect64,
    encode_rect64,
    load_existing,
    parse_faces,
)
from picasapy.ini.faces import Face
from picasapy.scanner import PICASA_INI_NAME

#: relatív (rect64-stílusú) keret: bal, felső, jobb, alsó
RelRect = tuple[float, float, float, float]

#: a kisebbik keretre vetített átfedés küszöbe (indoklás: modul-docstring)
IGNORE_MATCH_OVERLAP = 0.5

#: az ini-ből jövő (saját indexsor nélküli) mellőzött arc kulcsa a QML-ben
_INI_KEY_PREFIX = "ini:"

K = TypeVar("K", bound=Hashable)


def clamp_rect(rect: Sequence[float]) -> RelRect:
    """A keret a [0..1] tartományra vágva (J1). A YuNet a képszélen
    túllógó arcra negatív vagy 1-nél nagyobb koordinátát ad, amit az
    `encode_rect64` `ValueError`-ral elutasít."""
    left, top, right, bottom = (min(1.0, max(0.0, float(v))) for v in rect)
    return (left, top, right, bottom)


def quantize_rect(rect: Sequence[float]) -> RelRect:
    """A vágott keret a rect64 1/65536-os rácsán — pontosan az az érték,
    amit a `.picasa.ini` visszaolvasva ad. A pontos párt kereső `ini/`
    függvények (`with_face` idempotenciája, `without_face`) csak így
    találnak rá."""
    quantized = decode_rect64(encode_rect64(Rect64(*clamp_rect(rect))))
    return (quantized.left, quantized.top, quantized.right, quantized.bottom)


def _area(rect: Sequence[float]) -> float:
    return max(0.0, rect[2] - rect[0]) * max(0.0, rect[3] - rect[1])


def _intersection(a: Sequence[float], b: Sequence[float]) -> float:
    width = min(a[2], b[2]) - max(a[0], b[0])
    height = min(a[3], b[3]) - max(a[1], b[1])
    return max(0.0, width) * max(0.0, height)


def region_overlap(a: Sequence[float], b: Sequence[float]) -> float:
    """A metszet a kisebbik keret területéhez mérve, [0..1]."""
    smaller = min(_area(a), _area(b))
    return _intersection(a, b) / smaller if smaller > 0 else 0.0


def rect_iou(a: Sequence[float], b: Sequence[float]) -> float:
    """A szokásos metszet/unió — itt csak a döntetlen feloldására."""
    intersection = _intersection(a, b)
    union = _area(a) + _area(b) - intersection
    return intersection / union if union > 0 else 0.0


def match_regions(
    items: Iterable[tuple[K, Sequence[float]]], regions: Iterable[RelRect]
) -> dict[K, RelRect]:
    """Páronkénti hozzárendelés: minden régió legfeljebb EGY elemhez, és
    minden elem legfeljebb EGY régióhoz — a legjobban illeszkedő párok
    előbb (átfedés, azon belül IoU). Csak a küszöböt elérő pár számít."""
    region_list = list(regions)
    candidates = []
    for key, rect in items:
        for index, region in enumerate(region_list):
            overlap = region_overlap(rect, region)
            if overlap >= IGNORE_MATCH_OVERLAP:
                candidates.append((overlap, rect_iou(rect, region), key, index))
    candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)
    matched: dict[K, RelRect] = {}
    used: set[int] = set()
    for _overlap, _iou, key, index in candidates:
        if key in matched or index in used:
            continue
        matched[key] = region_list[index]
        used.add(index)
    return matched


def best_region(rect: Sequence[float], regions: Iterable[RelRect]) -> RelRect | None:
    """Az egyetlen `rect`-hez legjobban illeszkedő régió, vagy `None`."""
    return match_regions([(0, rect)], regions).get(0)


def ini_faces_of(photo_path: Path) -> tuple[Face, ...]:
    """A fotó `faces=` bejegyzései a mappa `.picasa.ini`-jéből. Hiányzó
    vagy olvashatatlan ini, hiányzó szakasz, hibás érték: üres."""
    ini_path = photo_path.parent / PICASA_INI_NAME
    try:
        document = load_existing(ini_path)
    except (OSError, ValueError):
        return ()
    section = document.section(photo_path.name)
    raw_faces = section.get("faces") if section is not None else None
    if not raw_faces:
        return ()
    try:
        return parse_faces(raw_faces)
    except ValueError:
        return ()


def ignored_regions(faces: Iterable[Face]) -> tuple[RelRect, ...]:
    """A mellőzött (`ffffffffffffffff`) bejegyzések keretei."""
    return tuple(
        (face.rect.left, face.rect.top, face.rect.right, face.rect.bottom)
        for face in faces
        if face.contact_id.casefold() == UNIDENTIFIED_CONTACT
    )


def ini_face_key(photo_id: int, rect: Sequence[float]) -> str:
    """Saját indexsor nélküli (csak az ini-ben mellőzött) arc kulcsa."""
    return f"{_INI_KEY_PREFIX}{int(photo_id)}:{encode_rect64(Rect64(*rect))}"


def parse_ini_face_key(key: object) -> tuple[int, RelRect] | None:
    """Az `ini_face_key` visszafejtése; más alakra `None`."""
    if not isinstance(key, str) or not key.startswith(_INI_KEY_PREFIX):
        return None
    photo_part, _sep, rect_part = key[len(_INI_KEY_PREFIX):].partition(":")
    try:
        rect = decode_rect64(rect_part)
        return int(photo_part), (rect.left, rect.top, rect.right, rect.bottom)
    except ValueError:
        return None
