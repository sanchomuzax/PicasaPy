#!/usr/bin/env python3
"""`respack.yt` kicsomagoló — a Picasa 3.9 bináris erőforráscsomagja.

A formátum visszafejtve 2026-08-06-án a `research/copy_Picasa_3_7/Picasa3`
telepítés `runtime/respack.yt` (3,7 MB) és `runtime/slingshot/respack.yt`
(372 KB) fájljaiból. A teljes formátumleírás:
`docs/specs/picasa-respack-format.md`.

Röviden:

* fejléc: `uint32 LE` = a NÉVINDEX bájt-eltolása a fájl végén;
* névindex: `uint32 darabszám`, majd darabszámszor `név\\0` + `uint32 offset`;
* minden rekord 13 bájtos fejléccel indul
  (`int16 x0,y0,x1,y1` + `uint8 ?` + `uint8 látható` + `uint16 ?` +
  `uint8 kódolás`), utána a hasznos adat:
  - kódolás `2` = tömör kitöltés, 4 bájt BGRA;
  - kódolás `1` = RLE: `(uint8 darab, B, G, R, A)` ötösök **egyetlen,
    sorhatároktól FÜGGETLEN képpont-folyamként**, összesen
    `(x1-x0) * (y1-y0)` képpont (a futamok átlógnak a sorok között);
  - kódolás `0` = üres réteg (csak fejléc, nincs képpontadat);
  - a `tre:` nevű bejegyzések nyers ASCII szövegek (UI-elrendezés-forrás),
    nincs 13 bájtos fejlécük.

Használat:

    python3 tools/picasa/respack.py list  <respack.yt>
    python3 tools/picasa/respack.py tre   <respack.yt> <kimenet_dir>
    python3 tools/picasa/respack.py png   <respack.yt> <kimenet_dir> [szűrő]

**Jogi megjegyzés:** a kicsomagolt képek és szövegek a Google Inc.
szerzői jogvédett anyagai. Ez az eszköz KUTATÁSI célú: a formátum
dokumentálásához és a saját, legális Picasa-telepítés vizsgálatához
készült. A kinyert grafikát a PicasaPy NEM tartalmazza és nem terjeszti.
"""

from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

HEADER_SIZE = 13
ENC_EMPTY = 0
ENC_RLE = 1
ENC_SOLID = 2


@dataclass(frozen=True)
class Entry:
    """Egy bejegyzés a csomagban (név + a nyers adatblokk határai)."""

    name: str
    offset: int
    end: int

    @property
    def is_tre(self) -> bool:
        return self.name.startswith("tre:")


@dataclass(frozen=True)
class Layer:
    """Dekódolt rajzi réteg."""

    name: str
    x0: int
    y0: int
    x1: int
    y1: int
    encoding: int
    pixels: bytes  # BGRA, soronként; tömör kitöltésnél is kifejtve

    @property
    def width(self) -> int:
        return self.x1 - self.x0

    @property
    def height(self) -> int:
        return self.y1 - self.y0


class RespackError(Exception):
    """A csomag nem a várt formátumú."""


def read_index(data: bytes) -> list[Entry]:
    """Beolvassa a névindexet, offset szerint rendezve adja vissza.

    A rekordhatárt a KÖVETKEZŐ bejegyzés offsetje adja (az utolsóét maga
    az index kezdete) — a formátumban nincs explicit hosszmező.
    """
    if len(data) < 8:
        raise RespackError("A fájl túl rövid ahhoz, hogy respack legyen.")
    (index_off,) = struct.unpack_from("<I", data, 0)
    if not 8 <= index_off < len(data):
        raise RespackError(f"Érvénytelen indexeltolás: {index_off}")

    pos = index_off
    (count,) = struct.unpack_from("<I", data, pos)
    pos += 4
    raw: list[tuple[str, int]] = []
    for _ in range(count):
        nul = data.find(b"\0", pos)
        if nul < 0:
            raise RespackError("Lezáratlan név az indexben.")
        name = data[pos:nul].decode("latin1")
        pos = nul + 1
        if pos + 4 > len(data):
            raise RespackError("Csonka index.")
        (off,) = struct.unpack_from("<I", data, pos)
        pos += 4
        raw.append((name, off))

    raw.sort(key=lambda t: t[1])
    entries: list[Entry] = []
    for i, (name, off) in enumerate(raw):
        end = raw[i + 1][1] if i + 1 < len(raw) else index_off
        entries.append(Entry(name=name, offset=off, end=end))
    return entries


def decode_layer(data: bytes, entry: Entry) -> Layer:
    """Egy `layer:` bejegyzés kibontása BGRA képponttömbbé."""
    if entry.is_tre:
        raise RespackError(f"{entry.name}: szöveges bejegyzés, nem réteg.")
    off = entry.offset
    if off + HEADER_SIZE > entry.end:
        raise RespackError(f"{entry.name}: csonka fejléc.")
    x0, y0, x1, y1 = struct.unpack_from("<4h", data, off)
    encoding = data[off + 12]
    body = data[off + HEADER_SIZE : entry.end]
    width, height = x1 - x0, y1 - y0
    count = max(width, 0) * max(height, 0)

    if encoding == ENC_EMPTY:
        pixels = b"\0\0\0\0" * count
    elif encoding == ENC_SOLID:
        if len(body) < 4:
            raise RespackError(f"{entry.name}: hiányzó kitöltőszín.")
        pixels = bytes(body[:4]) * count
    elif encoding == ENC_RLE:
        out = bytearray()
        pos = 0
        while pos + 5 <= len(body):
            run = body[pos]
            out += body[pos + 1 : pos + 5] * run
            pos += 5
        if len(out) != count * 4:
            raise RespackError(
                f"{entry.name}: RLE hossz nem stimmel "
                f"({len(out) // 4} képpont, várt {count})"
            )
        pixels = bytes(out)
    else:
        raise RespackError(f"{entry.name}: ismeretlen kódolás: {encoding}")

    return Layer(entry.name, x0, y0, x1, y1, encoding, pixels)


def encode_layer(layer: Layer) -> bytes:
    """A dekódolt rétegből VISSZAÁLLÍTJA a nyers adatblokkot (a 13 bájtos
    fejléc nélkül).

    Ez a formátum-értés legerősebb próbája: ha a visszakódolt bájtsor azonos az
    eredetivel, akkor a kódolást pontosan értjük, nem csak olvasni tudjuk. A
    valódi `respack.yt`-n mind az 1365 RLE-réteg bájtra egyezik.

    **Fontos:** a futamok NEM sorhatárra igazítottak — a kép egyetlen,
    folytonos képpont-folyam (ezt épp a visszakódolási próba mutatta ki, ld.
    `docs/specs/picasa-respack-format.md` 3.2).
    """
    if layer.encoding == ENC_EMPTY:
        return b""
    if layer.encoding == ENC_SOLID:
        return bytes(layer.pixels[:4])
    out = bytearray()
    px = layer.pixels
    total = layer.width * layer.height
    i = 0
    while i < total:
        color = px[i * 4 : i * 4 + 4]
        run = 1
        while (
            i + run < total
            and run < 255
            and px[(i + run) * 4 : (i + run) * 4 + 4] == color
        ):
            run += 1
        out.append(run)
        out += color
        i += run
    return bytes(out)


def extract_tre(data: bytes, entry: Entry) -> str:
    """Egy `tre:` bejegyzés szövegének kinyerése."""
    return data[entry.offset : entry.end].decode("latin1")


def _safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_.() " else "_" for c in name)


def _cmd_list(path: Path) -> int:
    data = path.read_bytes()
    entries = read_index(data)
    tre = sum(1 for e in entries if e.is_tre)
    print(f"{path}: {len(entries)} bejegyzés ({tre} .tre forrás)")
    for e in entries:
        print(f"  {e.offset:9d} {e.end - e.offset:8d}  {e.name}")
    return 0


def _cmd_tre(path: Path, outdir: Path) -> int:
    data = path.read_bytes()
    outdir.mkdir(parents=True, exist_ok=True)
    n = 0
    for e in read_index(data):
        if not e.is_tre:
            continue
        (outdir / f"{_safe_filename(e.name[4:])}.tre").write_text(
            extract_tre(data, e), encoding="latin1"
        )
        n += 1
    print(f"{n} .tre fájl kiírva ide: {outdir}")
    return 0


def _cmd_png(path: Path, outdir: Path, needle: str | None) -> int:
    try:
        from PIL import Image
    except ImportError:
        print("A PNG-kiírás Pillow-t igényel (pip install pillow).", file=sys.stderr)
        return 2
    data = path.read_bytes()
    outdir.mkdir(parents=True, exist_ok=True)
    written = skipped = 0
    for e in read_index(data):
        if e.is_tre or (needle and needle not in e.name):
            continue
        try:
            layer = decode_layer(data, e)
        except RespackError as err:
            print(f"  kihagyva: {err}", file=sys.stderr)
            skipped += 1
            continue
        if layer.width <= 0 or layer.height <= 0:
            skipped += 1
            continue
        img = Image.frombytes(
            "RGBA", (layer.width, layer.height), layer.pixels, "raw", "BGRA"
        )
        img.save(outdir / f"{_safe_filename(layer.name)}.png")
        written += 1
    print(f"{written} PNG kiírva ({skipped} kihagyva) ide: {outdir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="bejegyzések listázása")
    p_list.add_argument("respack", type=Path)

    p_tre = sub.add_parser("tre", help="UI-elrendezés-források kiírása")
    p_tre.add_argument("respack", type=Path)
    p_tre.add_argument("outdir", type=Path)

    p_png = sub.add_parser("png", help="rétegek PNG-be mentése")
    p_png.add_argument("respack", type=Path)
    p_png.add_argument("outdir", type=Path)
    p_png.add_argument("filter", nargs="?", default=None)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "list":
            return _cmd_list(args.respack)
        if args.cmd == "tre":
            return _cmd_tre(args.respack, args.outdir)
        return _cmd_png(args.respack, args.outdir, args.filter)
    except (RespackError, OSError) as err:
        print(f"Hiba: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
