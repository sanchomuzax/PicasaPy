#!/usr/bin/env python3
"""Folyamatszintű képernyőkép-felvevő a PicasaPy-hoz (#6845).

Ugyanazt a felhasználói lépéssort futtatja a PicasaPy-on, amit az eredeti
Picasán a Colab-végrehajtó (kattintás, ctrl-kattintás, jobb klikk, menüpont,
gépelés, billentyű, várakozás), és MINDEN lépés után ablakképet, a végén a
lemezállapotot rögzíti. Ebből vethető össze a két program viselkedése
parancsonként. A felvevő csak MÉR: a termékhibát nem javítja.

Az alkalmazás offscreen platformon, egy tesztkönyvtárral indul: a `PicasaTeszt`
mappában 24 szintetikus JPEG van, rögzített mtime-mal, elszigetelt
beállításokkal (a gép valódi beállításaihoz és mappáihoz nem nyúl). A kurzor
villogását kikapcsoljuk, hogy két futás képe összevethető legyen; a felületi
animációkat a `setUITransitionsEnabled(False)` állítja le.

Lépésfajták (részletesen: `paritas_lepesek.py`):

    {"kijelol": 3}  {"kijelol_mod": [4, "ctrl"]}  {"jobbklikk": 4}
    {"jobbklikk_mappa": "PicasaTeszt"}  {"menupont": "contextMenuMove"}
    {"fomenu": "View", "menupont": "menuViewLibraryView"}
    {"gepel": "UjMappa"}  {"billentyu": "ctrl+a"}  {"var": 2}

Kimenet a `--kimenet` mappában: `kepernyo__00.png` (kezdőállapot),
`kepernyo__NN.png` (az NN. lépés után), `manifest.json` (lépésenként a kép,
a kivonat és az esetleges hiba), `allapot.json` (lemezfa, bal hasáb, rács,
kijelölés, nyitott rétegek).

Használat:
    python scripts/paritas_folyamat.py futtat --lepesek '[{"kijelol": 3}]' \\
        --kimenet /tmp/paritas
    python scripts/paritas_folyamat.py futtat --lepesek lepesek.json \\
        --kimenet /tmp/paritas

Kilépési kód: 0 siker, 1 az alkalmazás nem indult el vagy a kép nem menthető,
2 érvénytelen bemenet, 3 egy lépés nem hajtható végre (a kimenet addig
tartalmaz mindent, a hibás lépés képével együtt).

Figyelem: a felvevő valódi menüpontokra kattint, tehát a termék valódi
műveleteit végzi a tesztkönyvtáron (áthelyezés, törlés, mentés). A külső
programot indító tételek (Locate on Disk, Open File) nem érik el a gép
asztalát, mert a futás idejére a `DISPLAY` és a `WAYLAND_DISPLAY` hiányzik.
Az új mappa alapértelmezett dátuma a futás napja, ezért a `.picasa.ini`
`date=` értéke napról napra változik.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import paritas_lepesek as lepesek_modul
else:
    from . import paritas_lepesek as lepesek_modul

GYOKER = Path(__file__).resolve().parents[1]
TESZT_MAPPA = "PicasaTeszt"
KONYVTAR_NEV = "kepek"  # a `_build_qml_app` rögzített könyvtárneve
KEPSZAM = 24
MINTA_MTIME = 1_577_836_800
MINTA_MTIME_LEPES = 3600
_MINTA_MERETEK = ((320, 240), (240, 320), (400, 300))
_INDULAS_HATARIDO_MP = 15.0
_KEPERNYO_VALTOZOK = ("DISPLAY", "WAYLAND_DISPLAY")


def _modul(nev: str) -> Any:
    """A Qt-t betöltő testvérmodul; csak a környezet beállítása után hívható."""
    if __package__ in (None, ""):
        return importlib.import_module(nev)
    return importlib.import_module(f".{nev}", __package__)


def teszt_mappa_keszitese(lib: Path) -> None:
    """A `PicasaTeszt` mappa 24 mintázatos JPEG-gel, névsorrendben növő, rögzített mtime-mal."""
    from support.jpeg_factory import make_minta_jpeg

    mappa = lib / TESZT_MAPPA
    mappa.mkdir()
    for index in range(KEPSZAM):
        ut = mappa / f"kep_{index + 1:02d}.jpg"
        make_minta_jpeg(ut, size=_MINTA_MERETEK[index % len(_MINTA_MERETEK)], seed=index)
        ido = MINTA_MTIME + index * MINTA_MTIME_LEPES
        os.utime(ut, (ido, ido))


def _kornyezet_beallitasa() -> None:
    """Valódi képernyőt nem érinthetünk: a Qt offscreen platformon és szoftveres háttérrel fut."""
    for utvonal in (GYOKER / "src", GYOKER / "tests"):
        if str(utvonal) not in sys.path:
            sys.path.insert(0, str(utvonal))
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ.setdefault("QT_QUICK_BACKEND", "software")


@contextmanager
def _kepernyo_nelkul() -> Iterator[None]:
    """A futás idejére a valódi képernyő nem látszik a folyamatnak.

    A felvevő valódi menüpontokra kattint; ami külső programot indít (pl. a
    "Locate on Disk" fájlkezelőt, az "Open File" képnézőt), az így nem érheti el
    a gép asztalát."""
    korabbi = {nev: os.environ.pop(nev) for nev in _KEPERNYO_VALTOZOK if nev in os.environ}
    try:
        yield
    finally:
        os.environ.update(korabbi)


@contextmanager
def _munkamappaban(mappa: Path) -> Iterator[None]:
    """A futás idejére a tesztkönyvtárba lép.

    A mappaválasztó párbeszéd a folyamat munkamappájából indul; így a képe
    nem a gép vagy a checkout tartalmát mutatja, és két futás képe egyező."""
    korabbi = Path.cwd()
    os.chdir(mappa)
    try:
        yield
    finally:
        os.chdir(korabbi)


@contextmanager
def _munka(munkakonyvtar: Path | None) -> Iterator[Path]:
    """A megadott mappa megmarad; megadás nélkül ideiglenes, a végén törölt mappa."""
    if munkakonyvtar is not None:
        abszolut = munkakonyvtar.resolve()
        if abszolut.exists() and any(abszolut.iterdir()):
            raise ValueError(
                f"A munkakönyvtár nem üres: {munkakonyvtar}. Adj meg új vagy üres mappát."
            )
        abszolut.mkdir(parents=True, exist_ok=True)
        yield abszolut
        return
    with tempfile.TemporaryDirectory(prefix="picasapy-paritas-6845-") as ideiglenes:
        yield Path(ideiglenes)


def _alkalmazas(qt_app: Any) -> Any:
    from PySide6.QtGui import QGuiApplication

    alkalmazas = qt_app or QGuiApplication.instance() or QGuiApplication(["picasapy-paritas"])
    if alkalmazas.platformName() != "offscreen":
        raise RuntimeError(
            f"A felvevő csak offscreen platformon fut, nem a(z) {alkalmazas.platformName()!r} "
            "platformon: valódi képernyőt nem érinthet."
        )
    return alkalmazas


@contextmanager
def alkalmazas_inditasa(
    *,
    qt_app: Any = None,
    szelesseg: int = 1280,
    magassag: int = 800,
    munkakonyvtar: Path | None = None,
) -> Iterator[Any]:
    """Elindítja a tesztkönyvtáras alkalmazást, és a lépések `Kontextus`-át adja.

    Kilépéskor rendezetten lebont, és visszaállítja a környezetet, a munkamappát
    és az ideiglenes mappát. A `futtat` és a tesztek közös belépési pontja."""
    if szelesseg <= 0 or magassag <= 0:
        raise ValueError("Az ablakméretnek pozitívnak kell lennie.")
    _kornyezet_beallitasa()
    alkalmazas = _alkalmazas(qt_app)
    with _kepernyo_nelkul(), _munka(munkakonyvtar) as munka:
        from app.qml_functional.conftest import _build_qml_app

        generator = _build_qml_app(
            alkalmazas,
            munka,
            kepeket_keszit=teszt_mappa_keszitese,
            belyegkep_meret=256,
            valodi_belyegkep=True,
        )
        ablak, vezerlo, _motor = next(generator)
        try:
            konyvtar = munka / KONYVTAR_NEV
            with _munkamappaban(konyvtar):
                kon = _modul("paritas_vegrehajt").Kontextus(
                    alkalmazas, ablak, vezerlo, konyvtar, munka
                )
                _felkeszit(kon, szelesseg, magassag)
                yield kon
        finally:
            _lebontas(generator)


def futtat(
    lepesek: Sequence[Any],
    kimenet: Path,
    *,
    qt_app: Any = None,
    szelesseg: int = 1280,
    magassag: int = 800,
    munkakonyvtar: Path | None = None,
) -> dict[str, Any]:
    """Lefuttatja a lépéssort; a kimenet mappába ír, és a manifestet adja vissza."""
    # A munkamappába lépés előtt, különben a relatív útvonal a tesztkönyvtárra mutatna.
    kimenet = kimenet.resolve()
    with alkalmazas_inditasa(
        qt_app=qt_app,
        szelesseg=szelesseg,
        magassag=magassag,
        munkakonyvtar=munkakonyvtar,
    ) as kon:
        kimenet.mkdir(parents=True, exist_ok=True)
        return _felvetel(lepesek, kimenet, kon)


def _lebontas(generator: Iterator[Any]) -> None:
    try:
        next(generator)
    except StopIteration:
        pass
    except AssertionError as hiba:
        print(f"Figyelmeztetés: a lebontás hibát jelzett: {hiba}", file=sys.stderr)


def _felvetel(lepesek: Sequence[Any], kimenet: Path, kon: Any) -> dict[str, Any]:
    allapot = _modul("paritas_allapot")
    manifest: dict[str, Any] = {
        "program": "PicasaPy",
        "ablak": {"szelesseg": kon.ablak.width(), "magassag": kon.ablak.height()},
        "teszt_mappa": TESZT_MAPPA,
        "kepszam": KEPSZAM,
        "kezdo": _kep_rekord(0, None, kon, kimenet),
        "lepesek": [],
        "siker": True,
    }
    for sorszam, lepes in enumerate(lepesek, start=1):
        hiba = _lepes_vegrehajtasa(sorszam, lepes, kon)
        rekord = _kep_rekord(sorszam, lepes, kon, kimenet)
        manifest["lepesek"].append({**rekord, "hiba": hiba})
        if hiba:
            manifest["siker"] = False
            break
    _json_ir(
        kimenet / "allapot.json",
        allapot.teljes(kon.munka, kon.konyvtar, kon.vezerlo, kon.ablak),
    )
    _json_ir(kimenet / "manifest.json", manifest)
    return manifest


def _felkeszit(kon: Any, szelesseg: int, magassag: int) -> None:
    qt = _modul("paritas_qt")

    kon.alkalmazas.styleHints().setCursorFlashTime(0)
    kon.vezerlo.setUITransitionsEnabled(False)
    kon.ablak.resize(szelesseg, magassag)
    kon.ablak.show()
    kon.ablak.requestActivate()
    cel = str(kon.konyvtar / TESZT_MAPPA)
    kon.vezerlo.selectFolder(cel)
    kesz = qt.var_feltetelre(
        kon.alkalmazas,
        lambda: kon.ablak.isVisible()
        and Path(str(kon.vezerlo.currentFolder)) == Path(cel)
        and int(kon.vezerlo.photos.rowCount()) == KEPSZAM,
        _INDULAS_HATARIDO_MP,
    )
    if not kesz:
        raise RuntimeError(
            f"A {TESZT_MAPPA} mappa {KEPSZAM} képe nem jelent meg a rácson "
            f"{_INDULAS_HATARIDO_MP:g} másodpercen belül."
        )
    qt.var(kon.alkalmazas, 0.5)


def _lepes_vegrehajtasa(sorszam: int, lepes: Any, kon: Any) -> str | None:
    """A lépés hibaüzenete, vagy `None`; a váratlan Qt-hibát is a lépés hibájaként rögzíti."""
    qt = _modul("paritas_qt")
    try:
        _modul("paritas_vegrehajt").vegrehajt(kon, lepes)
    except qt.FuttatasiHiba as hiba:
        return f"A {sorszam}. lépés ({lepes.eredeti}) nem hajtható végre: {hiba}"
    except Exception as hiba:  # noqa: BLE001 - a felvevő a megfigyelést a hibánál sem dobja el
        return (
            f"A {sorszam}. lépés ({lepes.eredeti}) váratlan hibával állt le: "
            f"{type(hiba).__name__}: {hiba}"
        )
    return None


def _kep_rekord(
    sorszam: int, lepes: Any, kon: Any, kimenet: Path
) -> dict[str, Any]:
    qt = _modul("paritas_qt")

    kep, stabil = qt.stabil_ablakkep(kon.alkalmazas, kon.ablak)
    fajl = f"kepernyo__{sorszam:02d}.png"
    if not kep.save(str(kimenet / fajl), "PNG"):
        raise OSError(f"Nem sikerült elmenteni: {kimenet / fajl}")
    rekord: dict[str, Any] = {
        "sorszam": sorszam,
        "kep": fajl,
        "stabil": stabil,
        "meret": {"szelesseg": kep.width(), "magassag": kep.height()},
        "allapot": _modul("paritas_allapot").pillanatkep(kon.konyvtar, kon.vezerlo, kon.ablak),
    }
    if lepes is not None:
        rekord["fajta"] = lepes.fajta
        rekord["lepes"] = json.loads(lepes.eredeti)
    return rekord


def _json_ir(ut: Path, adat: dict[str, Any]) -> None:
    ut.write_text(json.dumps(adat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parancsok = parser.add_subparsers(dest="parancs", required=True)
    futtat_parser = parancsok.add_parser(
        "futtat", help="Egy lépéssor lefuttatása, lépésenkénti ablakképpel"
    )
    futtat_parser.add_argument(
        "--lepesek", required=True, help="a lépések JSON-listája, vagy JSON-fájl útja"
    )
    futtat_parser.add_argument("--kimenet", type=Path, required=True)
    futtat_parser.add_argument("--szelesseg", type=int, default=1280)
    futtat_parser.add_argument("--magassag", type=int, default=800)
    futtat_parser.add_argument(
        "--munkakonyvtar",
        type=Path,
        default=None,
        help="a tesztkönyvtár helye (megmarad); megadás nélkül ideiglenes, törölt mappa",
    )
    return parser


def _utf8_kimenet() -> None:
    """Windowson a konzol cp1252: az ékezetes kimenet nélküle elhasal."""
    for folyam in (sys.stdout, sys.stderr):
        try:
            folyam.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _utf8_kimenet()
    args = _parser().parse_args(argv)
    try:
        lepesek = lepesek_modul.betolt(args.lepesek)
        if args.szelesseg <= 0 or args.magassag <= 0:
            raise ValueError("Az ablakméretnek pozitívnak kell lennie.")
        manifest = futtat(
            lepesek,
            args.kimenet,
            szelesseg=args.szelesseg,
            magassag=args.magassag,
            munkakonyvtar=args.munkakonyvtar,
        )
    except (lepesek_modul.LepesHiba, ValueError) as hiba:
        print(f"Hiba: {hiba}", file=sys.stderr)
        return 2
    except (OSError, RuntimeError) as hiba:
        print(f"Hiba: {hiba}", file=sys.stderr)
        return 1
    if not manifest["siker"]:
        elso_hiba = next(lepes["hiba"] for lepes in manifest["lepesek"] if lepes["hiba"])
        print(f"Hiba: {elso_hiba}", file=sys.stderr)
        return 3
    print(
        f"{len(manifest['lepesek'])} lépés képe és az állapot elmentve ide: {args.kimenet}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
