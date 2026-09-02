#!/usr/bin/env python3
"""A `cv2` FÁJLÚTVONALAS olvasó/író őre — #1991.

**A hibaosztály.** A `cv2.imread` és a `cv2.imwrite` fájlútvonalas alakja
Windowson az ANSI kódlapon megy át, ezért **ékezetes néven némán** nem
olvas / nem ír: nincs kivétel, nincs hibakód, csak `None`, illetve
nincs fájl. A projekt ezt a **#65** és a **#190** óta tudja, és négy modul
(`collage/render.py`, `edit/save.py`, `thumbs/cache.py`,
`export/exporter.py`) bájt-alapon megy miatta.

**Miért kell gépi őr.** A tanulság négy fájl KOMMENTJÉBEN élt — pontosan
azokban, ahol be is tartottuk. Ahol megszegtük, ott értelemszerűen nem
volt komment. 2026-09-02-én egy nap alatt kétszer bukott ki: a #979
helykitöltője fájlútvonalasan írt (a windows-CI fogta meg), és a
`webexport/images.py` **évek óta** így olvasott, valódi felhasználói úton.
A próza nem fut le.

**A bevált út.** Olvasás: `cvimage.read_image_bytes()` + `cv2.imdecode`.
Írás: `cv2.imencode` + `Path.write_bytes`.

⚠️ **Csak KÓDSOROKAT néz.** A meglévő fájlok kommentjei és docstringjei
név szerint említik mindkét hívást (ez a szkript is), tehát a naiv
szövegkeresés azonnal hamis pozitív lenne. Az elemzés `ast`-tel megy: a
komment és a sztring-literál így fogalmilag sem tud beleszólni.
"""

from __future__ import annotations

import ast
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
FORRAS = REPO / "src" / "picasapy"

#: A tiltott `cv2.<név>(...)` hívások.
TILTOTT = ("imread", "imwrite")

#: Nevesített kivételek: `"csomag/modul.py"` → miért szabad ott.
#: ÜRES — ha ide valaha kerül tétel, az indoklás kötelező, hogy a
#: következő kör ne találgasson.
KIVETELEK: dict[str, str] = {}


def _talalatok(fa: ast.AST) -> list[tuple[int, str]]:
    """A `cv2.imread(...)` / `cv2.imwrite(...)` hívások (sor, név)."""
    ki: list[tuple[int, str]] = []
    for csomopont in ast.walk(fa):
        if not isinstance(csomopont, ast.Call):
            continue
        fv = csomopont.func
        if (
            isinstance(fv, ast.Attribute)
            and fv.attr in TILTOTT
            and isinstance(fv.value, ast.Name)
            and fv.value.id == "cv2"
        ):
            ki.append((csomopont.lineno, fv.attr))
    return ki


def main() -> int:
    leletek: list[str] = []
    for utvonal in sorted(FORRAS.rglob("*.py")):
        rel = utvonal.relative_to(REPO / "src").as_posix()
        if rel in KIVETELEK:
            continue
        try:
            fa = ast.parse(utvonal.read_text(encoding="utf-8"))
        except SyntaxError as hiba:  # pragma: no cover - a lint úgyis fogja
            print(f"⚠️  nem elemezhető: {rel} ({hiba})", file=sys.stderr)
            continue
        for sor, nev in _talalatok(fa):
            leletek.append(f"  {rel}:{sor} — cv2.{nev}(...)")

    if not leletek:
        print("✅ nincs fájlútvonalas cv2.imread/imwrite a forrásban")
        return 0

    print(
        "⛔ FÁJLÚTVONALAS cv2-hívás a forrásban — ékezetes néven Windowson\n"
        "   NÉMÁN elbukik (#65, #190, #1991):",
        file=sys.stderr,
    )
    for lelet in leletek:
        print(lelet, file=sys.stderr)
    print(
        "\n   A bevált út: olvasás `cvimage.read_image_bytes()` + "
        "`cv2.imdecode`,\n   írás `cv2.imencode` + `Path.write_bytes`.\n"
        "   Ha egy hely INDOKOLTAN kivétel, vedd fel a szkript "
        "`KIVETELEK` szótárába — az indoklással együtt.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
