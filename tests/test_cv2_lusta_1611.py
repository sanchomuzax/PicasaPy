"""#1611: az OpenCV NEM töltődik be az induláshoz.

## A mérés, ami miatt ez a jegy megnyílt

`import picasapy.app.application` — **2435 ms** valódi OpenCV-vel, **876
ms** kicserélt cv2-vel (#1601). A levehető költség ~1,5 másodperc MINDEN
induláskor, akkor is, ha a felhasználó egyetlen effektet vagy arckeresést
sem használ. Az eredeti Picasa 0–2 s alatt elindul, a miénk 5,2 s volt.

## Miért nem elég egy helyen javítani

A #1601 kipróbálta a kézenfekvő utat (egy lusta import az
`index/__init__.py`-ban), és **nulla nyereséget** kapott: az indulási
láncban több mint harminc modul importálja a cv2-t felső szinten, és elég
EGY, hogy a teljes költség beessen.

## Az őr foga

Két, egymást kiegészítő állítás — a második nélkül az első kijátszható
egyetlen új sorral:

1. **Viselkedés:** az `app.application` betöltése után a `cv2` nincs a
   `sys.modules`-ban. Ez a végeredmény, és bármelyik visszaeséstől bukik.
2. **Szerkezet:** egyetlen `src/picasapy/**` modul se importálja a cv2-t
   közvetlenül, és egyik se olvasson `cv2.X`-et MODULSZINTEN. Ez utóbbi a
   csendes visszaesés útja: egy `_FLAGS = cv2.IMREAD_...` konstans a
   betöltéskor behozza az egész OpenCV-t, miközben az import sora
   ártatlannak látszik.

Mindkettőt egyetlen sor visszaírásával elbuktattam, mielőtt bekerült
volna (a `render/text_overlay.py` `_FONT` konstansával).

## Az ÁRA — és miért nem fagy meg tőle a felület

Az első tényleges cv2-használat egyszeri ~1341 ms. **Ez nem a felület
szálán esik be:** a bélyegképeket a `ThumbnailProvider` állítja elő, ami
`QQuickAsyncImageProvider` — a Qt szálkészletén fut, nem a GUI-szálon.
Az első bélyegkép tehát valamivel később készül el, a felület közben
mozog.

⚠️ Egy KORÁBBI változat háttérszálon „előmelegítette" az OpenCV-t az
ablak első képkockája után. Két őr buktatta el, jogosan:

1. `test_hatterszal_nyilvantartas_988` — nyers `threading.Thread` az app
   rétegben (a `BackgroundWorkerMixin._start_background` a szabály);
2. `test_indulas_or_1601` — a blokkoló indulás növekménye túllépte a
   megengedett hányadot: a Python-import a GIL-t tartja, tehát az
   „előmelegítés" éppen a felület szálát akasztotta meg.

Az előmelegítés ezért KIKERÜLT. A lusta import a nyereség; a halasztott
költséget az viszi, akinek tényleg kell, és az egy háttérszál.
"""

from __future__ import annotations

import ast
import os
import pathlib
import subprocess
import sys

import picasapy

_FORRAS = pathlib.Path(picasapy.__file__).parent


def _kulon_folyamat(kod: str) -> subprocess.CompletedProcess:
    """Friss értelmezőben futtat — a tesztkészlet többi része már behozta
    az OpenCV-t, ezért ITT nem lehet mérni. A `sys.path` átadva, hogy a
    csomag a munkafából jöjjön, ne egy telepített példányból."""
    kornyezet = dict(os.environ)
    kornyezet["PYTHONPATH"] = os.pathsep.join(
        [p for p in sys.path if p] + [kornyezet.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    return subprocess.run(
        [sys.executable, "-c", kod],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        timeout=180,
        env=kornyezet,
    )


class TestAzIndulasNemToltiBe:
    def test_az_application_utan_nincs_cv2(self):
        """KÜLÖN folyamatban — a tesztkészlet többi része már behozta."""
        kod = (
            "import sys; import picasapy.app.application; "
            "sys.exit(1 if 'cv2' in sys.modules else 0)"
        )
        eredmeny = _kulon_folyamat(kod)
        assert eredmeny.returncode == 0, (
            "az `import picasapy.app.application` behozta az OpenCV-t — "
            "a ~1,5 másodperces indulási költség visszatért.\n"
            + eredmeny.stderr[-2000:]
        )


class TestSzerkezet:
    def test_nincs_MODULSZINTU_cv2_import(self):
        """A helyettesen kell átmenni (`from picasapy.lazy_cv2 import cv2`).

        A FÜGGVÉNYEN BELÜLI `import cv2` rendben van: az már eleve halasztott,
        és néhány helyen (`importsource`, `index/colors`) szándékosan így áll.
        """
        vetkesek = []
        for utvonal in sorted(_FORRAS.rglob("*.py")):
            try:
                fa = ast.parse(utvonal.read_text(encoding="utf-8"))
            except SyntaxError:  # pragma: no cover
                continue
            for csomopont in fa.body:  # CSAK modulszint (a `try` belsejével)
                if isinstance(
                    csomopont,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                ):
                    continue
                for al in ast.walk(csomopont):
                    if isinstance(al, ast.Import) and any(
                        nev.name == "cv2" for nev in al.names
                    ):
                        vetkesek.append(f"{utvonal.name}:{al.lineno}")
                    elif isinstance(al, ast.ImportFrom) and al.module == "cv2":
                        vetkesek.append(f"{utvonal.name}:{al.lineno}")
        assert not vetkesek, (
            "modulszintű, közvetlen cv2-import — használd a "
            f"`picasapy.lazy_cv2` helyettest: {vetkesek}"
        )

    def test_nincs_MODULSZINTU_cv2_hivatkozas(self):
        """A csendes visszaesés útja: egy konstans a betöltéskor behozza."""
        vetkesek = []
        for utvonal in sorted(_FORRAS.rglob("*.py")):
            try:
                fa = ast.parse(utvonal.read_text(encoding="utf-8"))
            except SyntaxError:  # pragma: no cover
                continue
            for csomopont in fa.body:  # CSAK modulszint
                if isinstance(
                    csomopont,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                ):
                    continue
                for al in ast.walk(csomopont):
                    if (
                        isinstance(al, ast.Attribute)
                        and isinstance(al.value, ast.Name)
                        and al.value.id == "cv2"
                    ):
                        vetkesek.append(
                            f"{utvonal.name}:{csomopont.lineno}: cv2.{al.attr}"
                        )
                        break
        assert not vetkesek, (
            "modulszintű `cv2.X` — a betöltéskor behozza az OpenCV-t; "
            f"tedd függvénybe: {vetkesek}"
        )


class TestAHelyettesHelyesenTovabbit:
    def test_ugyanazt_adja_mint_a_valodi(self):
        import cv2 as valodi

        from picasapy.lazy_cv2 import cv2 as helyettes

        assert helyettes.IMREAD_COLOR == valodi.IMREAD_COLOR
        assert helyettes.resize is valodi.resize

    def test_a_foltozas_ATLATSZIK_rajta(self):
        """A helyettes SZÁNDÉKOSAN nem gyorstáraz.

        Gyorstárral a valódi modul foltozása (`monkeypatch.setattr(cv2,
        …)`) nem látszana rajta át — a tesztjeink élnek ezzel
        (`tests/thumbs/test_cache.py`), és élesben is csendes, nehezen
        felderíthető eltérés lenne.
        """
        import cv2 as valodi

        from picasapy.lazy_cv2 import cv2 as helyettes

        eredeti = valodi.imencode
        try:
            valodi.imencode = lambda *a, **k: ("folt", None)
            assert helyettes.imencode(None, None)[0] == "folt"
        finally:
            valodi.imencode = eredeti
        assert helyettes.imencode is valodi.imencode

    def test_csak_hasznalatra_toltodik_be(self):
        kod = (
            "import sys\n"
            "from picasapy.lazy_cv2 import cv2, betoltve\n"
            "assert not betoltve() and 'cv2' not in sys.modules\n"
            "cv2.IMREAD_COLOR\n"
            "assert betoltve() and 'cv2' in sys.modules\n"
        )
        eredmeny = _kulon_folyamat(kod)
        assert eredmeny.returncode == 0, eredmeny.stderr[-2000:]
