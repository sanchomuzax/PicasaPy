"""Fájl-vágólap hasznos teher: `text/uri-list` + `x-special/gnome-copied-files`
(#1526).

## Mit csinál az eredeti, és miért ez a linuxos megfelelője

A Picasa **indításkor nyolc vágólap-formátumot regisztrál** (`0x005378e0`,
hívó `0x0040cd10`): `Shell IDList Array`, `Net Resource`,
`FileGroupDescriptor`, `UniformResourceLocator`, `FileContents`, `FileName`,
**`Preferred DropEffect`**, `Embedded Object`. Mind a nyolc **fájlátviteli**
formátum — egy sem képformátum. Ebből két dolog következik:

1. a Másolás/Kivágás **fájlokat** tesz a vágólapra (ezért lehet a Picasából
   közvetlenül a Fájlkezelőbe beilleszteni), nem képadatot;
2. a Kivágás és a Másolás **ugyanazt az adatot** teszi fel, és csak a
   `Preferred DropEffect` különbözteti meg őket (mozgatás vs. másolás).

A nyolc windowsos formátum reprodukálása hatókörön kívül (#1526): nincs
Linux-megfelelőjük. A LÉNYEG viszont pontosan visszaadható a linuxos
szabvánnyal:

| eredeti | nálunk |
|---|---|
| `FileName` / `Shell IDList Array` | `text/uri-list` |
| **`Preferred DropEffect`** | **`x-special/gnome-copied-files` első sora** |

## A két formátum alakja

`text/uri-list` (RFC 2483): `file://` URI-k, **CRLF**-fel elválasztva; a
`#`-kezdetű sor megjegyzés. Olvasáskor az LF-fel elválasztott listát is
elfogadjuk — a fájlkezelők nem mind tartják magukat a CRLF-hez.

`x-special/gnome-copied-files` (a Nautilus formátuma, amit a Dolphin, a
Thunar, a Nemo és a PCManFM is olvas): az **első sor** `copy` vagy `cut`,
utána soronként egy-egy URI, LF-fel elválasztva, záró újsor nélkül.

## Miért olvasáskor `copy` a biztonságos alapértelmezés

Az első sort idegen alkalmazás írja. Ha nem ismerjük fel, **másolásnak**
vesszük: az legrosszabb esetben egy fölösleges másolat, míg a téves
mozgatás fájlt visz el a forrásmappából. Íráskor viszont szigorúak vagyunk
(`ValueError`): a saját kódunk elgépelt művelet-neve hiba, nem bemenet.

Ez a modul SZÁNDÉKOSAN Qt-mentes — a formátum önmagában mérhető, a
`QMimeData`-ba töltés a `app/fileops_controller.py` dolga.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

#: A `Preferred DropEffect` két értékének megfelelője.
COPY = "copy"
CUT = "cut"

#: MIME-nevek. A `text/uri-list` a szabvány fájllista; a másik a
#: mozgatás/másolás megkülönböztetése.
URI_LIST = "text/uri-list"
GNOME_COPIED_FILES = "x-special/gnome-copied-files"

_EFFECTS = (COPY, CUT)


def path_to_uri(path: Path) -> str:
    """Abszolút útvonal `file://` URI-ként, százalékkódolva.

    A `Path.as_uri()` nem elég: az a nem-abszolút úton kivételt dob, itt
    viszont a hívó a rács útvonalait adja át — legyen kiszámítható.
    """
    text = str(Path(path))
    return "file://" + quote(text, safe="/")


def uri_from_text(text: str) -> Path | None:
    """Egy URI-sor útvonallá alakítása; `None`, ha nem helyi fájl.

    A megjegyzés-sor (`#`) és a nem `file:` sémájú URI (pl. `http://`)
    egyaránt `None` — azokkal nem tudunk fájlműveletet végezni.
    """
    text = text.strip()
    if not text or text.startswith("#"):
        return None
    parts = urlsplit(text)
    if parts.scheme != "file":
        return None
    # a `netloc` üres vagy `localhost` lehet; bármi más távoli hely
    if parts.netloc not in ("", "localhost"):
        return None
    return Path(unquote(parts.path))


def uri_list_payload(paths: Iterable[Path]) -> bytes:
    """`text/uri-list` hasznos teher — CRLF-fel elválasztva (RFC 2483)."""
    return "\r\n".join(path_to_uri(path) for path in paths).encode("utf-8")


def paths_from_uri_list(data: bytes | str) -> list[Path]:
    """`text/uri-list` visszaolvasása. CRLF-et és LF-et is elfogad."""
    text = data.decode("utf-8") if isinstance(data, bytes) else data
    found = (uri_from_text(line) for line in text.replace("\r\n", "\n").split("\n"))
    return [path for path in found if path is not None]


def gnome_payload(paths: Iterable[Path], effect: str) -> bytes:
    """`x-special/gnome-copied-files` hasznos teher.

    `effect` csak `COPY` vagy `CUT` lehet — a saját hívónk elgépelése hiba,
    nem bemenet (olvasáskor viszont elnézőek vagyunk, ld. modul-docstring).
    """
    if effect not in _EFFECTS:
        raise ValueError(
            f"ismeretlen vágólap-művelet: {effect!r} (várt: {COPY!r} vagy {CUT!r})"
        )
    lines = [effect, *(path_to_uri(path) for path in paths)]
    return "\n".join(lines).encode("utf-8")


def parse_gnome_payload(data: bytes | str) -> tuple[str, list[Path]]:
    """`(művelet, útvonalak)` a hasznos teherből.

    Ismeretlen vagy hiányzó művelet esetén `COPY` — ld. a modul
    docstringjének „miért a másolás a biztonságos alapértelmezés" részét.
    """
    text = data.decode("utf-8") if isinstance(data, bytes) else data
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or not lines[0].strip():
        return COPY, []
    head = lines[0].strip().lower()
    effect = head if head in _EFFECTS else COPY
    found = (uri_from_text(line) for line in lines[1:])
    return effect, [path for path in found if path is not None]


__all__ = [
    "COPY",
    "CUT",
    "GNOME_COPIED_FILES",
    "URI_LIST",
    "gnome_payload",
    "parse_gnome_payload",
    "path_to_uri",
    "paths_from_uri_list",
    "uri_from_text",
    "uri_list_payload",
]
