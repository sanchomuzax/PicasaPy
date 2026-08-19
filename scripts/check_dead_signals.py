#!/usr/bin/env python3
"""A néma akció-jelzések őre — #1003.

**A hibaosztály.** Egy Qt-jelzés kibocsátása és a fogadása két külön hely a
kódban. Ha a kibocsátó elkészül és a fogadó nem, a program **nem hibázik**:
a jelzés elmegy a semmibe, a felhasználó nem lát semmit. A teszt is zöld
marad, mert a szokásos teszt a KIBOCSÁTÁST állítja, nem a HATÁST.

Ez a PicasaPy-ben 2026-08-19-ig **háromszor** ment ki kiadásba, egyre kisebb
léptékben: #985 (a kollázs-panel nem volt bekötve), #989 (a téma-választó
nem adta át a témát), #1001 (a „Megjelenítés és szerkesztés" gomb jelzésének
nincs fogadója). A szkript az egész osztályt egyszerre méri.

**Mit tekint fogadónak.** A jelzés akkor NEM néma, ha bármelyik igaz:

* QML-kezelő a neve alapján: ``onJelzesNev`` — ez fedi a deklaratív
  ``onJelzesNev:`` alakot, a ``Connections { function onJelzesNev() }``
  blokkot és a ``Connections { target: x; onJelzesNev: ... }`` alakot is;
* imperatív kötés bárhonnan: ``valami.jelzesNev.connect(...)`` — akár
  Pythonból, akár QML-ből (pl. ``Component.onCompleted``-ben).

**Mit hagy ki szándékosan.** A property-értesítőket (amikre valahol
``notify=`` hivatkozik): azokat a QML-kötések némán fogyasztják, ott a
hiányzó kezelő a normális állapot.

**Amit NEM ismer fel** (ha ilyen kerül a kódba, hamis riasztást ad, és a
felismerést ide kell felvenni): a `getattr(obj, "jelzesNev").connect(...)`
alakú, névből összerakott kötés, és a Qt4-es `QObject.connect(sender,
SIGNAL(...))` alak. A tesztekből érkező kötés SZÁNDÉKOSAN nem számít
fogadónak: attól a felhasználó még nem lát semmit.

**Az alapállapot.** A bevezetéskor 26 néma jelzés volt a fában; azokra
azonnal pirosra váltani a main-t nem lehet. Ezért a mai állapot egy
tételes, INDOKLÁSSAL ellátott listában áll (``dead_signals_baseline.txt``).
A szkript akkor bukik, ha

* **ÚJ** néma jelzés keletkezik (nincs a listán), vagy
* a listán olyan tétel van, ami már nem néma (**elavult** bejegyzés), vagy
* a lista hosszabb a bevezetéskori méretnél (``MAX_BASELINE_ENTRIES``) —
  egy sor beírásával az őr különben kikerülhető lenne.

Így a lista rövidülhet, de nem hízhat észrevétlenül.

Használat::

    python scripts/check_dead_signals.py          # ellenőrzés (CI)
    python scripts/check_dead_signals.py --list   # a mai néma jelzések

Kilépési kód: 0 ha nincs eltérés az alapállapottól, 1 ha van, 2 ha a
bemenet hibás (nincs ilyen könyvtár, rossz alapállapot-fájl).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_ROOT = _REPO_ROOT / "src" / "picasapy"
_DEFAULT_BASELINE = Path(__file__).resolve().parent / "dead_signals_baseline.txt"

#: ``jelzesNev = Signal(...)`` osztályszinten. A fában minden jelzés ilyen
#: alakban áll (ast-tal ellenőrizve: 174 találat, mindkét módszerrel ugyanaz).
_SIGNAL_DECL = re.compile(r"^[ \t]*(\w+)\s*=\s*Signal\(", re.M)

#: ``Property(..., notify=jelzesNev)`` — a property-értesítő jelzések.
_NOTIFY = re.compile(r"notify\s*=\s*(\w+)")

#: Az alapállapot FELSŐ korlátja — a bevezetéskori 26 tétel.
#:
#: Az „új néma jelzés = piros CI" szabályt egy sor beírásával ki lehetne
#: kerülni. Ez a plafon ezt teszi TUDATOS lépéssé: a 27. tételhez a számot is
#: emelni kell, azt pedig a felülvizsgálat látja. Ahogy a lista fogy, ezt a
#: számot ÉRDEMES lejjebb vinni — csökkenteni szabad, emelni csak indoklással.
# A plafon a lista MAI hossza — a #1001 lezárásával 26-ról 25-re csökkent.
# Csak LEFELÉ szabad módosítani: ez akadályozza meg, hogy valaki egy új
# néma jelzést a listába írva kerülje meg az őrt.
MAX_BASELINE_ENTRIES = 25


@dataclass(frozen=True)
class SignalDecl:
    """Egy deklarált jelzés: a neve és a fájl, ahol áll."""

    name: str
    path: str  # a vizsgált gyökérhez képest, POSIX alakban

    @property
    def key(self) -> str:
        """Az alapállapot-lista kulcsa — fájl és név együtt.

        Azért nem csak a név: nyolc jelzésnév KÉTSZER szerepel a fában
        (pl. `scanStarted` a dedup- és az arc-vezérlőben is), és a puszta
        névre kulcsolt lista az egyiket némán elnyelné.
        """
        return f"{self.path}::{self.name}"


def _handler_name(signal_name: str) -> str:
    """A jelzéshez tartozó QML-kezelő neve (`fooBar` → `onFooBar`)."""
    return "on" + signal_name[:1].upper() + signal_name[1:]


def _read_text(path: Path) -> str:
    """Fájl beolvasása; a nem UTF-8 bájtokat elnyeli, nem áll meg tőlük."""
    return path.read_text(encoding="utf-8", errors="replace")


def collect_declarations(root: Path) -> list[SignalDecl]:
    """A gyökér alatti `*.py` fájlok összes `Signal(...)` deklarációja."""
    found: list[SignalDecl] = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        for match in _SIGNAL_DECL.finditer(_read_text(path)):
            found.append(SignalDecl(name=match.group(1), path=relative))
    return found


def _joined_text(root: Path, pattern: str) -> str:
    """A gyökér alatti, mintára illeszkedő fájlok szövege egyben."""
    return "\n".join(_read_text(path) for path in sorted(root.rglob(pattern)))


def notify_signals(python_text: str) -> set[str]:
    """A `notify=` hivatkozással property-értesítővé tett jelzések nevei."""
    return set(_NOTIFY.findall(python_text))


def has_receiver(name: str, python_text: str, qml_text: str) -> bool:
    """Van-e a jelzésnek fogadója — QML-kezelő vagy imperatív kötés."""
    if re.search(rf"\b{re.escape(_handler_name(name))}\b", qml_text):
        return True
    connect = rf"\b{re.escape(name)}\s*\.\s*connect\s*\("
    return bool(re.search(connect, python_text) or re.search(connect, qml_text))


@dataclass(frozen=True)
class Report:
    """Egy futás nyers eredménye — a számokkal együtt, hogy kiírható legyen."""

    total: int
    notify: int
    silent: tuple[SignalDecl, ...]

    @property
    def action(self) -> int:
        """Az akció-jelzések száma (az összesből a property-értesítők nélkül)."""
        return self.total - self.notify


def scan(root: Path) -> Report:
    """A teljes vizsgálat egy forrásfán."""
    python_text = _joined_text(root, "*.py")
    qml_text = _joined_text(root, "*.qml")
    notify = notify_signals(python_text)
    declarations = collect_declarations(root)
    silent = tuple(
        declaration
        for declaration in declarations
        if declaration.name not in notify
        and not has_receiver(declaration.name, python_text, qml_text)
    )
    notify_count = sum(1 for d in declarations if d.name in notify)
    return Report(total=len(declarations), notify=notify_count, silent=silent)


def load_baseline(path: Path) -> dict[str, str]:
    """Az alapállapot beolvasása: kulcs → indoklás.

    Formátum soronként: a kulcs (`fájl::jelzésNév`), szóköz, majd az
    indoklás — jegyszám vagy mondat arról, miért él még a tétel. A `#`-cal
    kezdődő és az üres sorok megjegyzések. Indoklás nélküli tétel HIBA: a
    néma engedély pontosan az, ami ide nem kell.
    """
    if not path.is_file():
        raise FileNotFoundError(f"nincs alapállapot-fájl: {path}")
    entries: dict[str, str] = {}
    for number, raw in enumerate(_read_text(path).splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, _, reason = line.partition(" ")
        reason = reason.strip()
        if not reason:
            raise ValueError(f"{path}:{number}: a tételhez INDOKLÁS kell — {key!r}")
        if key in entries:
            raise ValueError(f"{path}:{number}: kétszer szereplő tétel — {key!r}")
        entries[key] = reason
    if len(entries) > MAX_BASELINE_ENTRIES:
        raise ValueError(
            f"{path}: {len(entries)} tétel, a felső korlát "
            f"{MAX_BASELINE_ENTRIES} — a lista csak rövidülhet "
            "(ld. MAX_BASELINE_ENTRIES a check_dead_signals.py-ban)"
        )
    return entries


def _print_report(report: Report) -> None:
    """A számok kiírása — ugyanaz a fejléc az ellenőrzésnél és a listánál."""
    print(
        f"{report.total} jelzés, {report.notify} property-értesítő, "
        f"{report.action} akció-jelzés, {len(report.silent)} néma"
    )


def check(root: Path, baseline_path: Path) -> int:
    """Ellenőrzés az alapállapothoz mérve. 0 = nincs eltérés."""
    report = scan(root)
    baseline = load_baseline(baseline_path)
    found = {declaration.key: declaration for declaration in report.silent}
    new = sorted(set(found) - set(baseline))
    stale = sorted(set(baseline) - set(found))

    _print_report(report)
    if not new and not stale:
        print(f"Rendben: mind a {len(found)} néma jelzés szerepel az alapállapotban.")
        return 0

    if new:
        print(f"\nÚJ néma jelzés ({len(new)}) — kibocsátjuk, de senki nem fogadja:")
        for key in new:
            print(f"  {key}")
        print(
            "\n  Kösd be (QML-kezelő vagy .connect), vagy töröld a jelzést.\n"
            "  Ha tényleg tartalék: vedd fel a listára INDOKLÁSSAL — "
            f"{baseline_path.name}"
        )
    if stale:
        print(f"\nELAVULT bejegyzés ({len(stale)}) — a lista tétele már nem néma:")
        for key in stale:
            print(f"  {key}  ({baseline[key]})")
        print(f"\n  Töröld a sorát: {baseline_path.name} — a lista csak rövidülhet.")
    return 1


def main(argv: list[str] | None = None) -> int:
    """Parancssori belépési pont."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=_DEFAULT_ROOT,
        help="a vizsgált forrásfa (alapértelmezés: src/picasapy)",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=_DEFAULT_BASELINE,
        help="az alapállapot-fájl útvonala",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="listing",
        help="csak a mai néma jelzések kiírása, alapállapot nélkül",
    )
    args = parser.parse_args(argv)

    if not args.root.is_dir():
        print(f"nincs ilyen könyvtár: {args.root}", file=sys.stderr)
        return 2

    if args.listing:
        report = scan(args.root)
        _print_report(report)
        for declaration in sorted(report.silent, key=lambda d: d.key):
            print(f"  {declaration.key}")
        return 0

    try:
        return check(args.root, args.baseline)
    except (FileNotFoundError, ValueError) as error:
        print(f"hibás alapállapot: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
