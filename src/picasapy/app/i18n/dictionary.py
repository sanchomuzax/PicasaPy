"""Qt TS-szótárak eredetjelölése, biztonságos párosítása és bájtpontos köre."""

from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict

ORIGIN_PREFIX = "picasapy-origin:"
ORIGIN_KEY_PREFIX = "picasapy-origin-key:"
ORIGIN_PICASAPY = "picasapy"
ORIGIN_PICASA = "picasa"


def load_catalog(data: bytes) -> ET.Element:
    """Qt TS bájtok beolvasása; idegen gyökeret elutasít."""
    root = ET.fromstring(data)
    if root.tag != "TS":
        raise ValueError(f"nem Qt TS szótár: {root.tag!r}")
    return root


def dump_catalog(root: ET.Element) -> bytes:
    """A kanonikus UTF-8 Qt TS alak — ugyanaz a fa mindig ugyanazokat a bájtokat adja."""
    if root.tag != "TS":
        raise ValueError(f"nem Qt TS szótár: {root.tag!r}")
    ET.indent(root, space="    ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


def message_origin(message: ET.Element) -> str | None:
    """A gépileg olvasható eredetérték, ha a sor már meg van jelölve."""
    extra = message.findtext("extracomment") or ""
    for line in extra.splitlines():
        if line.startswith(ORIGIN_PREFIX):
            return line[len(ORIGIN_PREFIX) :].strip()
    return None


def set_message_origin(
    message: ET.Element, origin: str, reference_keys: tuple[str, ...] = ()
) -> None:
    """Egységes eredetjelölő hozzáadása a TS `extracomment` mezőjéhez."""
    if origin not in {ORIGIN_PICASAPY, ORIGIN_PICASA}:
        raise ValueError(f"ismeretlen szótáreredet: {origin!r}")

    extra = message.find("extracomment")
    if extra is None:
        extra = ET.Element("extracomment")
        translation = message.find("translation")
        index = list(message).index(translation) if translation is not None else len(message)
        message.insert(index, extra)

    lines = [
        line
        for line in (extra.text or "").splitlines()
        if not line.startswith((ORIGIN_PREFIX, ORIGIN_KEY_PREFIX))
    ]
    lines.append(f"{ORIGIN_PREFIX} {origin}")
    if reference_keys:
        lines.append(f"{ORIGIN_KEY_PREFIX} {';'.join(reference_keys)}")
    extra.text = "\n".join(lines)


def missing_count(root: ET.Element) -> int:
    """A hiányzó/unfinished fordítású aktív TS-sorok száma."""
    missing = 0
    for message in root.iter("message"):
        translation = message.find("translation")
        if translation is None:
            missing += 1
            continue
        state = translation.get("type")
        if state in {"obsolete", "vanished"}:
            continue
        if state == "unfinished":
            missing += 1
            continue
        if message.get("numerus") == "yes":
            forms = translation.findall("numerusform")
            if not forms or any(not (form.text or "").strip() for form in forms):
                missing += 1
        elif not (translation.text or "").strip():
            missing += 1
    return missing


def normalise_original_text(value: str) -> str:
    """A #2971 mérés szabálya: NFC, ampersand és záró írásjel nélkül, casefold."""
    cleaned = unicodedata.normalize("NFC", value).replace("&", "").strip()
    return re.sub(r"[.:…]+$", "", cleaned).casefold()


def index_original_texts(originals: dict[str, str]) -> dict[str, tuple[str, ...]]:
    """Normalizált szöveg → eredeti kulcsok; a nagy katalógushoz egyszer épül."""
    by_text: dict[str, list[str]] = defaultdict(list)
    for key, value in originals.items():
        by_text[normalise_original_text(value)].append(key)
    return {text: tuple(sorted(keys)) for text, keys in by_text.items()}


def match_original_translation(
    hungarian_translation: str,
    hungarian_originals: dict[str, str],
    target_originals: dict[str, str],
    *,
    hungarian_index: dict[str, tuple[str, ...]] | None = None,
) -> tuple[str, tuple[str, ...]] | None:
    """Egy saját HU-szöveg eredeti párját oldja fel, tippelés nélkül.

    A normalizált magyar szöveg lehet több eredeti kulcs értéke is. Ilyenkor
    csak akkor párosítunk, ha minden jelölt kulcs megvan a célnyelvben, és
    mindegyik ugyanazt a célnyelvi szöveget adja. Máskülönben `None` marad,
    hogy a hívó unfinished állapotot írjon.
    """
    normal = normalise_original_text(hungarian_translation)
    if hungarian_index is None:
        hungarian_index = index_original_texts(hungarian_originals)
    keys = hungarian_index.get(normal, ())
    if not keys or any(key not in target_originals for key in keys):
        return None
    target_values = {target_originals[key] for key in keys}
    if len(target_values) != 1:
        return None
    return next(iter(target_values)), keys
