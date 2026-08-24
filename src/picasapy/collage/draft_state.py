"""A kollázs PISZKOZAT-állapota — fájl-létezésből (#1072).

A #1072 lelete az volt, hogy a piszkozatnak nálunk **nincs fogalma**: a
`.cxf` írása (#431), az automentés életciklusa (#1051) és a látható
helykitöltő kép (#1072 első köre) mind megvolt, de sehol nem lehetett
megkérdezni egy képről, hogy „ez most piszkozat vagy kész kollázs?" —
tehát következményt (tiltás, külön befejező lépés) sem lehetett rákötni.

## A megkülönböztetés — a spec NORMATÍV táblájából

`docs/specs/kollazs-eletciklus.md` 1. szakasz:

| állapot | fájlok a Kollázsok mappában |
|---|---|
| **PISZKOZAT** | `<név>.jpg` (640 hosszú él) + `autosave.cxf` |
| **kész** | `<név>.jpg` (5120 hosszú él) + `<név>.cxf` |

Két kérdés, mindkettő fájl-létezés:

1. van-e a képnek **SAJÁT `.cxf` párja**? → akkor KÉSZ (ezen az egy jelen
   áll a #1002 „Kollázs szerkesztése" gombja is);
2. áll-e mellette **`autosave.cxf`**? → akkor PISZKOZAT.

## Miért nem az `index/album_collage.py`

A #1168 `folder_has_collage()`-e MÁS kérdésre felel: van-e a mappában
`PicasaCollage.cxf`, vagyis a PMP `albumdata_hascollage` album-jelzője.
Az ALBUMRÓL szól, nem egy konkrét képről, és nem a piszkozat/kész
különbségről. Ide nem használható; a két függvény nem is fedi egymást.

## ⚠️ Amit ez a szabály NEM tud

Ha a felhasználó egy IDEGEN JPEG-et tesz a Kollázsok mappába, miközben
ott egy piszkozat áll, azt is piszkozatnak látjuk. Ez tudatos: a kérdés
csak OLVASÁS (tiltás és egy gomb megjelenése), nem írás — a #1125
felülírás-védelme ezért továbbra is a nyilvántartott helykitöltő-útvonalon
áll, nem ezen. A rossz irányban tévedni itt olcsóbb: egy felesleges
„fejezze be előbb" üzenet bosszantó, egy PISZKOZAT-feliratos kép
kinyomtatása viszont pont az, amit a jegy meg akar akadályozni.

A modulban nincs Qt és nincs beállítás — tiszta útvonal-kérdések, hogy a
vezérlő, a nyomtatás és az e-mail ugyanazt a választ kapja.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.collage.autosave import AUTOSAVE_NAME


def _image_path(image_path: Path | str) -> Path | None:
    """A bemenet létező fájlként, vagy `None`.

    Üres/értelmezhetetlen útvonalra `None`: a felület null-őrei (a néző sor
    nélkül, a lebontás közbeni kötések) üres szöveget adnak, és abból nem
    szabad kivétel."""
    if not image_path:
        return None
    try:
        ut = Path(str(image_path))
        return ut if ut.is_file() else None
    except (OSError, ValueError):  # pragma: no cover - platformfüggő
        return None


def draft_project_path(image_path: Path | str) -> Path | None:
    """A kép mögötti PISZKOZAT-projekt (`autosave.cxf`), vagy `None`.

    A befejező lépésnek erre van szüksége: a piszkozat projektje nem a kép
    melletti `<név>.cxf` (az épp nincs is), hanem a mappa `autosave.cxf`-je.
    Kész kollázsra és sima fényképre `None`."""
    ut = _image_path(image_path)
    if ut is None:
        return None
    try:
        if ut.with_suffix(".cxf").exists():
            return None
    except (OSError, ValueError):  # pragma: no cover - platformfüggő
        return None
    autosave = ut.parent / AUTOSAVE_NAME
    return autosave if autosave.is_file() else None


def is_draft_image(image_path: Path | str) -> bool:
    """Piszkozat-e a megadott kép (ld. a modul docstringje)."""
    return draft_project_path(image_path) is not None


__all__ = ["draft_project_path", "is_draft_image"]
