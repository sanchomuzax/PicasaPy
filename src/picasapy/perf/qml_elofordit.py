"""#1719 — a QML-fa ELŐREFORDÍTÁSA telepítéskor (`qmlcachegen` bájtkód).

**A baj.** A Qt a QML-t *induláskor* fordítja bájtkóddá. A lemezes
gyorsítótára (`~/.cache/PicasaPy/PicasaPy/qmlcache/`) ezt megspórolná, de
az érvényessége a forrásfájl **időbélyegéhez** van kötve — a
`pip install --upgrade` pedig MINDEN fájlt friss időbélyeggel ír ki, tehát
minden telepítés/frissítés után az első indulás újrafordítja a teljes,
141 fájlos QML-fát.

**A megoldás.** A `qmlcachegen` ugyanazt a bájtkódot állítja elő *előre*,
és **nulla forrás-időbélyeget** ír a fejlécébe. A Qt a `Foo.qml`
betöltésekor ELŐSZÖR a mellette fekvő `Foo.qmlc`-t próbálja
(`QV4::CompiledData::CompilationUnit::loadFromDisk`: `cachePaths[0] =
sourcePath + 'c'`), és nulla időbélyegnél **nem hasonlít dátumot**
(`Unit::verifyHeader`). Az így elhelyezett egység tehát a telepítés
időbélyegeitől függetlenül érvényes marad.

**Miért TELEPÍTÉSKOR és nem a wheel építésekor.** A fejléc tartalmazza a
Qt verzióját is; eltérésnél a Qt CSENDBEN eldobja a bájtkódot és
visszaesik a forrásfordításra. A `picasapy` wheel `py3-none-any`, a
célgép PySide6-ja pedig más verziójú lehet, mint az építőgépé — ezért az
előrefordítás a `postinst` / `install.bat` dolga, a célgép SAJÁT
PySide6-jával.

⚠️ **Fejlesztői munkafolyamat.** Épp az időbélyeg-függetlenség miatt egy
ottfelejtett `.qmlc` **némán elnyomná** a frissen szerkesztett `.qml`-t.
Ezért a `.qmlc`/`.jsc` a `.gitignore`-ban van, a `MANIFEST.in` kizárja a
csomagból, a fejlesztői indítás (`./picasapy`, tesztek) pedig SOHA nem
hívja ezt a modult. Ha kézzel mégis lefuttattad a forrásfán, a
`--takarit` állítja vissza a fejlesztői állapotot.

Használat (telepített csomagon a saját QML-fáját találja meg magától)::

    python -m picasapy.perf.qml_elofordit
    python -m picasapy.perf.qml_elofordit --ellenoriz
    python -m picasapy.perf.qml_elofordit --takarit

Kilépőkód: 0 = rendben, 1 = hiba (hiányzó `qmlcachegen`, fordítási hiba,
vagy `--ellenoriz` mellett hiányzó/elavult/időbélyeghez kötött egység).
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

#: A `qv4cdata` fejléc eleje: magic[8] + quint32 version + quint32 qtVersion
#: + qint64 sourceTimeStamp. A Qt is ezeket nézi (`Unit::verifyHeader`),
#: mielőtt elfogadná az egységet — az `--ellenoriz` ugyanezt kérdezi.
_MAGIC = b"qv4cdata"
_FEJLEC = struct.Struct("<8sIIq")

#: Amit előrefordítunk. A `qmlcachegen` a `.js`/`.mjs`-t is fordítja; a
#: kimenet neve mindig a forrásé + „c" — ezt az utat próbálja a Qt először.
_FORRAS_KITERJESZTESEK = (".qml", ".js", ".mjs")

#: Egy fordító-hívás felső időkorlátja. Egy QML-fájl fordítása
#: ezredmásodperces nagyságrendű; ha percekig tart, az beragadás.
_FORDITO_IDOKORLAT_MP = 300


@dataclass(frozen=True)
class Eredmeny:
    """Egy futás összegzése — a hívó ebből dönt a kilépőkódról."""

    forras_szam: int
    keszult: int
    hibas: tuple[tuple[Path, str], ...]

    @property
    def rendben(self) -> bool:
        """Minden forráshoz van kész egység, és nem volt hiba."""
        return not self.hibas and self.keszult == self.forras_szam


#: A `qmlcachegen` helye a PySide6 csomagon belül, platformonként MÁS.
#: Ellenőrizve a PyPI 6.11.2-es wheeljeiben (a zip-névlistából):
#: `manylinux_2_34_x86_64` → `PySide6/Qt/libexec/qmlcachegen`,
#: `win_amd64` → `PySide6/qmlcachegen.exe`. A Debian-csomagolt PySide6
#: 6.8.2 szintén a `Qt/libexec/` alá teszi.
_QMLCACHEGEN_JELOLTEK = (
    ("Qt", "libexec", "qmlcachegen"),
    ("Qt", "libexec", "qmlcachegen.exe"),
    ("qmlcachegen.exe",),
    ("qmlcachegen",),
)


def qmlcachegen_utvonal() -> Path | None:
    """A `qmlcachegen` elérési útja, vagy None ha nincs telepítve.

    Először a PATH-on lévő `pyside6-qmlcachegen` burkolót keressük — ez
    mindig ahhoz a PySide6-hoz tartozik, amelyikkel a program futni fog —,
    utána a PySide6 csomagon belüli, platformfüggő helyeket."""
    burkolo = shutil.which("pyside6-qmlcachegen")
    if burkolo:
        return Path(burkolo)
    try:
        import PySide6
    except ImportError:
        return None
    csomag = Path(PySide6.__file__).parent
    for reszek in _QMLCACHEGEN_JELOLTEK:
        jelolt = csomag.joinpath(*reszek)
        if jelolt.is_file():
            return jelolt
    return None


def qt_verzio() -> int | None:
    """A futó PySide6 Qt-verziója a fejléc `qtVersion` alakjában (0xMMmmpp).

    Ha ez nem egyezik a bájtkódéval, a Qt eldobja az egységet — az
    `--ellenoriz` ezért ezt is összeveti."""
    try:
        from PySide6.QtCore import __version_info__
    except ImportError:
        return None
    fo, kis, javit = __version_info__[:3]
    return (fo << 16) | (kis << 8) | javit


def alap_gyoker() -> Path:
    """A futó telepítés QML-gyökere (`picasapy/app/qml`).

    Forrásból futtatva a repó `src/picasapy/app/qml`-jét adja, telepítve a
    `site-packages` alattit — így a `postinst` és a fejlesztői futtatás
    ugyanazt a hívást használhatja."""
    return Path(__file__).resolve().parent.parent / "app" / "qml"


def forrasok(gyoker: Path) -> list[Path]:
    """A `gyoker` alatti összes fordítható QML/JS forrás, rendezetten."""
    return sorted(
        p
        for p in gyoker.rglob("*")
        if p.is_file() and p.suffix in _FORRAS_KITERJESZTESEK
    )


def cel_utvonal(forras: Path) -> Path:
    """A forráshoz tartozó bájtkód-fájl (`Foo.qml` → `Foo.qmlc`)."""
    return forras.with_name(forras.name + "c")


def fejlec(egyseg: Path) -> tuple[int, int] | None:
    """`(qtVersion, sourceTimeStamp)` a bájtkódból, vagy None ha nem az."""
    try:
        with egyseg.open("rb") as f:
            nyers = f.read(_FEJLEC.size)
    except OSError:
        return None
    if len(nyers) < _FEJLEC.size:
        return None
    magic, _verzio, qtverzio, idobelyeg = _FEJLEC.unpack(nyers)
    if magic != _MAGIC:
        return None
    return qtverzio, idobelyeg


def _fordit(eszkoz: Path, gyoker: Path, forras: Path) -> tuple[Path, str | None]:
    """Egyetlen forrás lefordítása; visszaad: (forrás, hibaszöveg vagy None).

    A `--only-bytecode` szándékos: C++ AOT-kódot a CMake-es
    `qt_add_qml_module` projektekhez lehet generálni, nekünk pontosan az a
    bájtkód kell, amit a motor egyébként induláskor állítana elő."""
    cel = cel_utvonal(forras)
    parancs = [
        str(eszkoz),
        "--only-bytecode",
        "-I",
        str(gyoker),
        "-o",
        str(cel),
        str(forras),
    ]
    try:
        kesz = subprocess.run(
            parancs,
            capture_output=True,
            text=True,
            timeout=_FORDITO_IDOKORLAT_MP,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as hiba:
        return forras, f"a fordító indítása nem sikerült: {hiba}"
    if kesz.returncode != 0:
        uzenet = (kesz.stderr or kesz.stdout or "").strip()
        return forras, uzenet or f"kilépőkód {kesz.returncode}"
    # A qmlcachegen egy `.aotstats` melléktermékét is leteszi — a futáshoz
    # nem kell, és csak zajt vinne a telepített csomagba.
    stats = cel.with_name(cel.name + ".aotstats")
    if stats.exists():
        stats.unlink()
    if not cel.is_file():
        return forras, "a fordító nem írt kimenetet"
    return forras, None


def elofordit(gyoker: Path, szalak: int = 0) -> Eredmeny:
    """A teljes fa előrefordítása, a magok számával párhuzamosan.

    ⚠️ **Először MINDIG kitakarít.** Egy fordított egység a hozzá tartozó
    forrás dátumától függetlenül érvényes, ezért egy RÉGI verzióból
    ottmaradt `.qmlc` némán elnyomná az új `.qml`-t — a felhasználó a
    régi felületet kapná az új programmal. A `pip install --upgrade` nem
    törli ezeket (nem szerepelnek a csomag RECORD-jában), tehát a
    takarítás a mi dolgunk. Így a futás legrosszabb kimenetele is csak
    HIÁNYZÓ egység (= a mai, lassabb viselkedés), soha nem ELAVULT."""
    eszkoz = qmlcachegen_utvonal()
    takarit(gyoker)
    lista = forrasok(gyoker)
    if eszkoz is None:
        return Eredmeny(
            len(lista), 0, ((gyoker, "nincs `qmlcachegen` a PySide6 mellett"),)
        )
    szalak = szalak or (os.cpu_count() or 1)
    hibas: list[tuple[Path, str]] = []
    keszult = 0
    with ThreadPoolExecutor(max_workers=szalak) as pool:
        for _forras, hiba in pool.map(
            lambda f: _fordit(eszkoz, gyoker, f), lista
        ):
            if hiba is None:
                keszult += 1
            else:
                hibas.append((_forras, hiba))
    return Eredmeny(len(lista), keszult, tuple(hibas))


def ellenoriz(gyoker: Path) -> Eredmeny:
    """Van-e MINDEN forráshoz érvényes, időbélyeg-független bájtkód?

    Ez az őr magja (`tests/perf/test_qml_elofordit.py`): **munkamennyiséget**
    mér — hány forráshoz van használható fordított egység —, nem időt
    (#1653, #1689)."""
    lista = forrasok(gyoker)
    vart_qt = qt_verzio()
    hibas: list[tuple[Path, str]] = []
    rendben = 0
    for forras in lista:
        cel = cel_utvonal(forras)
        if not cel.is_file():
            hibas.append((forras, "hiányzik a fordított egység"))
            continue
        fej = fejlec(cel)
        if fej is None:
            hibas.append((cel, "nem `qv4cdata` bájtkód"))
            continue
        qtverzio, idobelyeg = fej
        if idobelyeg != 0:
            hibas.append(
                (cel, "időbélyeghez kötött egység — nem előrefordított")
            )
            continue
        if vart_qt is not None and qtverzio != vart_qt:
            hibas.append(
                (
                    cel,
                    f"más Qt-verzióhoz készült (0x{qtverzio:06x} "
                    f"≠ 0x{vart_qt:06x})",
                )
            )
            continue
        rendben += 1
    return Eredmeny(len(lista), rendben, tuple(hibas))


def takarit(gyoker: Path) -> int:
    """Minden fordított egység törlése — vissza a fejlesztői állapotba.

    Nem a forrásokból indul, hanem a kimenetekből: így az ÁRVA egységek is
    eltűnnek (olyan `.qmlc`, amelynek a `.qml`-jét egy újabb verzió már
    nem tartalmazza)."""
    torolt = 0
    for minta in ("*.qmlc", "*.jsc", "*.mjsc", "*.aotstats"):
        for jelolt in gyoker.rglob(minta):
            if jelolt.is_file():
                jelolt.unlink()
                torolt += 1
    return torolt


def main(argv: list[str] | None = None) -> int:
    """Parancssori belépési pont (`picasapy-qml-elofordit`)."""
    ertelmezo = argparse.ArgumentParser(
        prog="picasapy-qml-elofordit",
        description="A PicasaPy QML-fájljainak előrefordítása (#1719).",
    )
    ertelmezo.add_argument(
        "--gyoker",
        type=Path,
        default=None,
        help="a QML-fa gyökere (alapértelmezés: a futó telepítésé)",
    )
    ertelmezo.add_argument(
        "--szalak", type=int, default=0, help="párhuzamos fordítók száma"
    )
    ertelmezo.add_argument(
        "--ellenoriz", action="store_true", help="csak ellenőrzés, nem fordít"
    )
    ertelmezo.add_argument(
        "--takarit", action="store_true", help="a fordított egységek törlése"
    )
    ertelmezo.add_argument(
        "--legalabb",
        type=int,
        default=0,
        help=(
            "ennyi forrást várunk a fában (munkamennyiség-mérce: egy üres "
            "vagy csonka QML-fa különben CSENDBEN zöld lenne)"
        ),
    )
    args = ertelmezo.parse_args(argv)

    gyoker = (args.gyoker or alap_gyoker()).resolve()
    if not gyoker.is_dir():
        sys.stderr.write(f"HIBA: nincs ilyen könyvtár: {gyoker}\n")
        return 1

    if args.takarit:
        sys.stdout.write(f"Törölt fordított egység: {takarit(gyoker)}\n")
        return 0

    eredmeny = (
        ellenoriz(gyoker) if args.ellenoriz else elofordit(gyoker, args.szalak)
    )
    for hol, hiba in eredmeny.hibas[:20]:
        sys.stderr.write(f"  {hol}: {hiba}\n")
    tobbi = len(eredmeny.hibas) - 20
    if tobbi > 0:
        sys.stderr.write(f"  … és további {tobbi} hiba\n")
    sys.stdout.write(
        f"QML-előrefordítás: {eredmeny.keszult}/{eredmeny.forras_szam} "
        f"rendben ({gyoker})\n"
    )
    if eredmeny.forras_szam < args.legalabb:
        sys.stderr.write(
            f"HIBA: csak {eredmeny.forras_szam} QML-forrást találtam, "
            f"legalább {args.legalabb} volt a várt — a fa csonka.\n"
        )
        return 1
    return 0 if eredmeny.rendben else 1


if __name__ == "__main__":
    raise SystemExit(main())
