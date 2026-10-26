#!/usr/bin/env python3
"""A PhotoViewer főállapotainak képpontos mérője (#5952).

Állapotok: alapnézet (bal fiók csukva); bal fiók nyitva; filmszalag;
szerkesztőpanel mind a hét füle (Gyakori javítások, Finomhangolás, Effektek,
Kreatív, Művészi, További effektek, Régi effektek); arcréteg; teljes képernyő.
Az állapotokat a `tests/app/qml_functional/conftest.py` közös
`_build_qml_app` építője hozza létre. Animációt nem veszünk mintának: a
képrögzítés határidőig várja, hogy három egymást követő ablakkép azonos legyen.
Kihagyott állapot nincs.

Használat:
    python scripts/photo_viewer_screenshots.py capture --output /tmp/nezokep
    python scripts/photo_viewer_screenshots.py compare --before /tmp/elotte \
        --after /tmp/utana --diff-dir /tmp/elteresek
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any

import numpy as np


GYOKER = Path(__file__).resolve().parents[1]
ALLAPOT_NEVEK = (
    "alapnezet",
    "bal-fiok-nyitva",
    "filmcsik",
    "szerkeszto-0",
    "szerkeszto-1",
    "szerkeszto-2",
    "szerkeszto-3",
    "szerkeszto-4",
    "szerkeszto-5",
    "szerkeszto-6",
    "arcreteg",
    "teljes-kepernyo",
)
_AKTIV_FUL_OBJEKTUMOK = (
    "editTabFixes",
    "editTabFinetune",
    "editTabEffects",
    "editTabEffects2",
    "editTabEffects3",
    "editTabEffects4",
    "editTabLegacy",
)
_KERET_SZIN = (255, 0, 255, 255)
_STABIL_KOCKAK = 3
_STABIL_HATARIDO_MP = 8.0
_ALLAPOT_HATARIDO_MP = 8.0


@dataclass(frozen=True)
class Allapot:
    nev: str
    nyitott_fiok: bool
    aktiv_ful: int | None = None
    arc_reteg: bool = False
    teljes_kepernyo: bool = False


ALLAPOTOK = (
    Allapot("alapnezet", nyitott_fiok=False),
    Allapot("bal-fiok-nyitva", nyitott_fiok=True),
    Allapot("filmcsik", nyitott_fiok=False),
    *(Allapot(f"szerkeszto-{index}", nyitott_fiok=True, aktiv_ful=index)
      for index in range(7)),
    Allapot("arcreteg", nyitott_fiok=False, arc_reteg=True),
    Allapot("teljes-kepernyo", nyitott_fiok=False, teljes_kepernyo=True),
)


def _elem(ablak: Any, nev: str) -> Any:
    from PySide6.QtCore import QObject

    elem = ablak.findChild(QObject, nev)
    if elem is None:
        raise RuntimeError(f"A QML-ablakból hiányzik a(z) {nev!r} objektum.")
    return elem


def _var_feltetelre(alkalmazas: Any, feltetel, leiras: str, hatarido: float) -> None:
    vege = time.monotonic() + hatarido
    while time.monotonic() < vege:
        alkalmazas.processEvents()
        if feltetel():
            return
        time.sleep(0.02)
    raise RuntimeError(f"Időtúllépés: {leiras}.")


def _minta_kepek(lib: Path) -> None:
    """A tesztkészlet mintázatos JPEG-jeivel fix bemenetet készít."""
    from support.jpeg_factory import make_minta_jpeg

    fajlok = (
        (lib / "a.jpg", (640, 400), 0),
        (lib / "b.jpg", (480, 360), 1),
    )
    for ut, meret, seed in fajlok:
        make_minta_jpeg(ut, size=meret, seed=seed)
        # A néző alsó adatsora a fájl módosítási idejét is kiírja.
        # Rögzített mtime nélkül két egymás utáni mérés képpontjai eltérnének.
        os.utime(ut, (1_577_836_800, 1_577_836_800))


def _adj_minta_arcot(ini_ut: Path) -> None:
    """A tesztfotón egy ismert, mentett arc legyen az arcréteghez."""
    from picasapy.ini import update_document
    from picasapy.ini.faces import Face, with_face
    from picasapy.ini.rect64 import Rect64

    arc = Face(Rect64(0.18, 0.16, 0.62, 0.69), "8e62b2035b74b477")
    update_document(
        ini_ut,
        lambda dokumentum: with_face(dokumentum, "a.jpg", arc),
        backup=False,
    )


def _kep_bajtok(kep: Any) -> bytes:
    from PySide6.QtGui import QImage

    rgba = kep.convertToFormat(QImage.Format.Format_RGBA8888)
    return bytes(rgba.constBits())


def _stabil_ablakkepernyo(ablak: Any, alkalmazas: Any, allapot: str) -> Any:
    """Határidővel vár három változatlan QImage-kockára, fix alvás nélkül."""
    elozo: bytes | None = None
    azonos = 0
    vege = time.monotonic() + _STABIL_HATARIDO_MP
    while time.monotonic() < vege:
        alkalmazas.processEvents()
        kep = ablak.grabWindow()
        if kep.isNull():
            azonos = 0
        else:
            bajtok = _kep_bajtok(kep)
            azonos = azonos + 1 if bajtok == elozo else 1
            if azonos >= _STABIL_KOCKAK:
                return kep.copy()
            elozo = bajtok
        time.sleep(0.05)
    raise RuntimeError(
        f"A(z) {allapot!r} állapot képe nem stabilizálódott "
        f"{_STABIL_HATARIDO_MP:g} másodpercen belül."
    )


def _lathato_objektumok(ablak: Any, nevek: tuple[str, ...]) -> list[str]:
    from PySide6.QtCore import QObject

    lathatok = []
    hianyzok = []
    for nev in nevek:
        elem = ablak.findChild(QObject, nev)
        if elem is not None and elem.isVisible():
            lathatok.append(nev)
        else:
            hianyzok.append(nev)
    if hianyzok:
        raise RuntimeError(
            "A képkockában nem látható kulcsobjektum(ok): "
            + ", ".join(hianyzok)
        )
    return lathatok


def _allapot_beallitasa(
    allapot: Allapot,
    *,
    ablak: Any,
    alkalmazas: Any,
    vezerlo: Any,
    viewer: Any,
    panel: Any,
) -> None:
    from PySide6.QtCore import QMetaObject
    from PySide6.QtGui import QWindow

    if ablak.visibility() == QWindow.Visibility.FullScreen:
        ablak.setProperty("visibility", QWindow.Visibility.Windowed)
    viewer.setProperty("facesEditMode", False)
    viewer.setProperty("facesVisible", False)
    vezerlo.setEditorControlsVisible(allapot.nyitott_fiok)
    if allapot.aktiv_ful is not None:
        panel.setProperty("activeTab", allapot.aktiv_ful)
    viewer.setProperty("facesVisible", allapot.arc_reteg)
    if allapot.arc_reteg:
        viewer.setProperty(
            "facesEditRevision", int(viewer.property("facesEditRevision")) + 1
        )
    if allapot.teljes_kepernyo:
        if not QMetaObject.invokeMethod(ablak, "toggleViewerFullscreen"):
            raise RuntimeError("A főablak teljes képernyős kapcsolója nem hívható.")
    _var_feltetelre(
        alkalmazas,
        lambda: ablak.isVisible()
        and viewer.isVisible()
        and _teljes_kepernyo(ablak) == allapot.teljes_kepernyo
        and bool(_elem(ablak, "viewerPhotoArea").isVisible())
        and float(_elem(ablak, "viewerImage").property("paintedWidth")) > 0,
        f"a(z) {allapot.nev} állapot megjelenése",
        _ALLAPOT_HATARIDO_MP,
    )
    if allapot.aktiv_ful is not None:
        _var_feltetelre(
            alkalmazas,
            lambda: int(panel.property("activeTab")) == allapot.aktiv_ful,
            f"a(z) {allapot.nev} fülváltása",
            _ALLAPOT_HATARIDO_MP,
        )
    if allapot.arc_reteg:
        overlay = _elem(ablak, "facesOverlay")
        _var_feltetelre(
            alkalmazas,
            lambda: overlay.isVisible() and len(overlay.property("faces")) > 0,
            "a mentett arcréteg megjelenése",
            _ALLAPOT_HATARIDO_MP,
        )


def _teljes_kepernyo(ablak: Any) -> bool:
    from PySide6.QtGui import QWindow

    return ablak.visibility() == QWindow.Visibility.FullScreen


def _kulcsobjektumok(allapot: Allapot) -> tuple[str, ...]:
    nevek = ["photoViewer", "viewerPhotoArea", "viewerImage"]
    if allapot.nyitott_fiok:
        nevek.extend(("viewerLeftDrawer", "viewerEditorPanel"))
    if allapot.aktiv_ful is not None:
        nevek.append(_AKTIV_FUL_OBJEKTUMOK[allapot.aktiv_ful])
    if allapot.nev == "filmcsik":
        nevek.append("viewerFilmstrip")
    if allapot.arc_reteg:
        nevek.append("facesOverlay")
    return tuple(nevek)


def _felvetel(ablak: Any, alkalmazas: Any, vezerlo: Any, output: Path,
              keresett_szel: int, keresett_mag: int) -> dict[str, Any]:
    viewer = _elem(ablak, "photoViewer")
    panel = _elem(ablak, "viewerEditorPanel")
    ablakmeret = {"width": ablak.width(), "height": ablak.height()}
    records: list[dict[str, Any]] = []
    for allapot in ALLAPOTOK:
        _allapot_beallitasa(
            allapot,
            ablak=ablak,
            alkalmazas=alkalmazas,
            vezerlo=vezerlo,
            viewer=viewer,
            panel=panel,
        )
        lathato = _lathato_objektumok(ablak, _kulcsobjektumok(allapot))
        kep = _stabil_ablakkepernyo(ablak, alkalmazas, allapot.nev)
        fajl = f"{allapot.nev}.png"
        cel = output / fajl
        if not kep.save(str(cel), "PNG"):
            raise RuntimeError(f"Nem sikerült elmenteni: {cel}")
        overlay = _elem(ablak, "facesOverlay")
        records.append(
            {
                "name": allapot.nev,
                "file": fajl,
                "width": kep.width(),
                "height": kep.height(),
                "window_size": {"width": ablak.width(), "height": ablak.height()},
                "visible_object_names": lathato,
                "active_tab": int(panel.property("activeTab"))
                if allapot.aktiv_ful is not None
                else None,
                "left_drawer_width": float(
                    _elem(ablak, "viewerLeftDrawer").property("width")
                ),
                "filmstrip_count": int(
                    _elem(ablak, "viewerFilmstrip").property("count")
                ),
                "face_count": len(overlay.property("faces"))
                if allapot.arc_reteg
                else 0,
                "fullscreen": _teljes_kepernyo(ablak),
            }
        )
    return {
        "requested_size": {"width": keresett_szel, "height": keresett_mag},
        "actual_window_size": ablakmeret,
        "states": records,
    }


def capture(output: Path, width: int, height: int) -> dict[str, Any]:
    """Felépíti a teszt-fixture appját, beállítja a nézőt, majd képeket ment."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["QT_QUICK_BACKEND"] = "software"
    if str(GYOKER / "src") not in sys.path:
        sys.path.insert(0, str(GYOKER / "src"))
    if str(GYOKER / "tests") not in sys.path:
        sys.path.insert(0, str(GYOKER / "tests"))

    from PySide6.QtGui import QGuiApplication
    from app.qml_functional.conftest import _build_qml_app

    alkalmazas = QGuiApplication.instance() or QGuiApplication(["picasapy-screenshot"])
    with tempfile.TemporaryDirectory(prefix="picasapy-viewer-5952-") as ideiglenes:
        gyoker = Path(ideiglenes)
        generator = _build_qml_app(
            alkalmazas, gyoker, kepeket_keszit=_minta_kepek
        )
        ablak, vezerlo, _engine = next(generator)
        try:
            vezerlo.setUITransitionsEnabled(False)
            ini_ut = gyoker / "kepek" / ".picasa.ini"
            _adj_minta_arcot(ini_ut)
            ablak.resize(width, height)
            ablak.show()
            ablak.requestActivate()
            ablak.setProperty("viewerOpen", True)
            alkalmazas.processEvents()
            viewer = _elem(ablak, "photoViewer")
            viewer.setProperty("currentIndex", 0)
            _var_feltetelre(
                alkalmazas,
                lambda: viewer.isVisible()
                and float(_elem(ablak, "viewerImage").property("paintedWidth")) > 0,
                "a szintetikus fotó betöltése",
                _ALLAPOT_HATARIDO_MP,
            )
            output.mkdir(parents=True, exist_ok=True)
            manifest = _felvetel(ablak, alkalmazas, vezerlo, output, width, height)
            manifest["states"] = list(manifest["states"])
            (output / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return manifest
        finally:
            try:
                next(generator)
            except StopIteration:
                pass


def _rgba_adatok(kep: Any) -> tuple[np.ndarray, int, int]:
    from PySide6.QtGui import QImage

    rgba = kep.convertToFormat(QImage.Format.Format_RGBA8888)
    sor_bajtok = bytes(rgba.constBits())
    sorhossz = rgba.bytesPerLine()
    adat = np.frombuffer(sor_bajtok, dtype=np.uint8).reshape(
        rgba.height(), sorhossz
    )[:, : rgba.width() * 4]
    return adat.reshape(rgba.height(), rgba.width(), 4), rgba.width(), rgba.height()


def _osszehasonlitott_kep(elotte: Any, utana: Any) -> tuple[int, tuple[int, int, int, int] | None, Any]:
    from PySide6.QtGui import QImage

    a, a_szel, a_mag = _rgba_adatok(elotte)
    b, b_szel, b_mag = _rgba_adatok(utana)
    szel, mag = max(a_szel, b_szel), max(a_mag, b_mag)
    elter = np.ones((mag, szel), dtype=bool)
    kozos_szel, kozos_mag = min(a_szel, b_szel), min(a_mag, b_mag)
    elter[:kozos_mag, :kozos_szel] = np.any(
        a[:kozos_mag, :kozos_szel] != b[:kozos_mag, :kozos_szel], axis=2
    )
    darab = int(np.count_nonzero(elter))
    if darab:
        sorok, oszlopok = np.nonzero(elter)
        bal, fent = int(oszlopok.min()), int(sorok.min())
        jobb, lent = int(oszlopok.max()) + 1, int(sorok.max()) + 1
        befoglalo = (bal, fent, jobb - bal, lent - fent)
    else:
        befoglalo = None
    pixels = np.zeros((mag, szel, 4), dtype=np.uint8)
    pixels[elter] = _KERET_SZIN
    diff = QImage(pixels.data, szel, mag, szel * 4, QImage.Format.Format_RGBA8888).copy()
    return darab, befoglalo, diff


def compare(before: Path, after: Path, diff_dir: Path) -> int:
    """Két PNG-mappát pontosan összevet, és a változó pixeleket kiemeli."""
    from PySide6.QtGui import QImage

    if not before.is_dir() or not after.is_dir():
        raise ValueError("Az összevetés mindkét bemenete létező mappa legyen.")
    png_a = {p.relative_to(before) for p in before.rglob("*.png") if not p.name.endswith(".diff.png")}
    png_b = {p.relative_to(after) for p in after.rglob("*.png") if not p.name.endswith(".diff.png")}
    if png_a != png_b:
        csak_a = sorted(p.as_posix() for p in png_a - png_b)
        csak_b = sorted(p.as_posix() for p in png_b - png_a)
        raise ValueError(
            "A két mappa PNG-listája eltér; csak előtte: "
            f"{csak_a}; csak utána: {csak_b}"
        )
    diff_dir.mkdir(parents=True, exist_ok=True)
    hibak = 0
    for relative in sorted(png_a):
        image_a, image_b = QImage(str(before / relative)), QImage(str(after / relative))
        if image_a.isNull() or image_b.isNull():
            raise ValueError(f"Nem olvasható PNG: {relative}")
        darab, bbox, diff = _osszehasonlitott_kep(image_a, image_b)
        diff_path = diff_dir / relative.parent / f"{relative.stem}.diff.png"
        if diff_path.exists():
            diff_path.unlink()
        if darab:
            diff_path.parent.mkdir(parents=True, exist_ok=True)
            if not diff.save(str(diff_path), "PNG"):
                raise OSError(f"Nem menthető a különbségkép: {diff_path}")
            assert bbox is not None
            x, y, bbox_szel, bbox_mag = bbox
            print(
                f"{relative.as_posix()}: {darab} eltérő képpont; "
                f"befoglaló téglalap: x={x}, y={y}, "
                f"szélesség={bbox_szel}, magasság={bbox_mag}; "
                f"különbségkép: {diff_path}"
            )
            hibak += darab
        else:
            print(f"{relative.as_posix()}: 0 eltérő képpont")
    return 1 if hibak else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture_parser = commands.add_parser("capture", help="A PhotoViewer állapotképeinek mentése")
    capture_parser.add_argument("--output", type=Path, required=True)
    capture_parser.add_argument("--width", type=int, default=1280)
    capture_parser.add_argument("--height", type=int, default=800)
    compare_parser = commands.add_parser("compare", help="Két PNG-mappa képpontos összevetése")
    compare_parser.add_argument("--before", type=Path, required=True)
    compare_parser.add_argument("--after", type=Path, required=True)
    compare_parser.add_argument("--diff-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "capture":
            if args.width <= 0 or args.height <= 0:
                raise ValueError("Az ablakméretnek pozitívnak kell lennie.")
            result = capture(args.output, args.width, args.height)
            print(
                f"{len(result['states'])} állapot képe elmentve ide: {args.output} "
                f"(ablak: {result['actual_window_size']['width']}×"
                f"{result['actual_window_size']['height']})."
            )
            return 0
        return compare(args.before, args.after, args.diff_dir)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Hiba: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
