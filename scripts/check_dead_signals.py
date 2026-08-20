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

#: A deklaráló osztály neve. A QML `Connections.target` gyakran ennek
#: camelCase alakja (pl. `DedupController` → `dedupController`).
_CLASS_DECL = re.compile(r"^[ \t]*class\s+(\w+)", re.M)

#: ``Property(..., notify=jelzesNev)`` — a property-értesítő jelzések.
_NOTIFY = re.compile(r"notify\s*=\s*(\w+)")

#: Az alapállapot FELSŐ korlátja — a legutóbbi teljes audit tételszáma.
#:
#: Az „új néma jelzés = piros CI" szabályt egy sor beírásával ki lehetne
#: kerülni. Ez a plafon ezt teszi TUDATOS lépéssé: új tételhez a számot is
#: emelni kell, azt pedig a felülvizsgálat látja. Ahogy a lista fogy, ezt a
#: számot ÉRDEMES lejjebb vinni — csökkenteni szabad, emelni csak indoklással.
# A plafon a célhoz kötött QML-fogadóellenőrzés utáni mai lista hossza.
# Csak LEFELÉ szabad módosítani: ez akadályozza meg, hogy valaki egy új
# néma jelzést a listába írva kerülje meg az őrt.
MAX_BASELINE_ENTRIES = 27


@dataclass(frozen=True)
class SignalDecl:
    """Egy deklarált jelzés: neve, fájlja és deklaráló osztálya."""

    name: str
    path: str  # a vizsgált gyökérhez képest, POSIX alakban
    owner: str | None

    @property
    def key(self) -> str:
        """Az alapállapot-lista kulcsa — fájl és név együtt.

        Azért nem csak a név: nyolc jelzésnév KÉTSZER szerepel a fában
        (pl. `scanStarted` a dedup- és az arc-vezérlőben is), és a puszta
        névre kulcsolt lista az egyiket némán elnyelné.
        """
        return f"{self.path}::{self.name}"

    @property
    def target_names(self) -> set[str]:
        """A QML/Python oldali, erre a deklarálóra utaló azonosítók.

        A QML context-property neve rendszerint a modul vagy az osztály
        camelCase alakja. A mixinek az `AppController` részei, ezért ott a
        közös `controller` név is érvényes cél.
        """
        module = Path(self.path).stem
        names = {_camel_name(module), module.replace("_controller", "")}
        if self.owner:
            names.add(_lower_camel(self.owner))
            if self.owner.endswith("Mixin"):
                names.add("controller")
            if self.owner.endswith("Provider"):
                names.add("provider")
        return names


def _handler_name(signal_name: str) -> str:
    """A jelzéshez tartozó QML-kezelő neve (`fooBar` → `onFooBar`)."""
    return "on" + signal_name[:1].upper() + signal_name[1:]


def _lower_camel(name: str) -> str:
    """`DedupController` → `dedupController`."""
    return name[:1].lower() + name[1:]


def _camel_name(name: str) -> str:
    """`dedup_controller` → `dedupController`."""
    head, *tail = name.split("_")
    return head + "".join(part.capitalize() for part in tail)


def _read_text(path: Path) -> str:
    """Fájl beolvasása; a nem UTF-8 bájtokat elnyeli, nem áll meg tőlük."""
    return path.read_text(encoding="utf-8", errors="replace")


def collect_declarations(root: Path) -> list[SignalDecl]:
    """A gyökér alatti `*.py` fájlok összes `Signal(...)` deklarációja."""
    found: list[SignalDecl] = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        text = _read_text(path)
        classes = [(match.start(), match.group(1)) for match in _CLASS_DECL.finditer(text)]
        for match in _SIGNAL_DECL.finditer(text):
            owner = next(
                (name for offset, name in reversed(classes) if offset < match.start()),
                None,
            )
            found.append(SignalDecl(name=match.group(1), path=relative, owner=owner))
    return found


def _joined_text(root: Path, pattern: str) -> str:
    """A gyökér alatti, mintára illeszkedő fájlok szövege egyben."""
    return "\n".join(_read_text(path) for path in sorted(root.rglob(pattern)))


def collect_notify_signals(root: Path) -> set[tuple[str, str | None, str]]:
    """A property-értesítők fájl-, osztály- és jelzésazonosítója.

    Azonos nevű jelzés több vezérlőben is lehet. Egy `A.done`-ra írt
    `notify=done` ezért nem teheti property-értesítővé a `B.done`-ot.
    """
    found: set[tuple[str, str | None, str]] = set()
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        text = _read_text(path)
        classes = [(match.start(), match.group(1)) for match in _CLASS_DECL.finditer(text)]
        for match in _NOTIFY.finditer(text):
            owner = next(
                (name for offset, name in reversed(classes) if offset < match.start()),
                None,
            )
            found.add((relative, owner, match.group(1)))
    return found


def _connections_blocks(qml_text: str) -> list[str]:
    """A QML `Connections { … }` blokkjai, a belső függvénytörzsekkel együtt."""
    blocks: list[str] = []
    for match in re.finditer(r"\bConnections\s*\{", qml_text):
        depth = 1
        index = match.end()
        while index < len(qml_text) and depth:
            if qml_text[index] == "{":
                depth += 1
            elif qml_text[index] == "}":
                depth -= 1
            index += 1
        if depth == 0:
            blocks.append(qml_text[match.start():index])
    return blocks


def _property_rhs(qml_text: str, name: str) -> str | None:
    """Egy QML-property pontos, ugyanebben a fájlban álló jobb oldala."""
    match = re.search(
        rf"^(?P<indent>[ \t]*)(?:readonly\s+)?property\b[^\n]*\b"
        rf"{re.escape(name)}\s*:\s*(?P<rhs>[^\n]*)$",
        qml_text,
        re.M,
    )
    if match is None:
        return None
    parts = [match.group("rhs").split(";", 1)[0]]
    if ";" in match.group("rhs"):
        return parts[0]
    indent = len(match.group("indent"))
    tail = qml_text[match.end():].splitlines()
    for line in tail:
        if not line.strip() or len(line) - len(line.lstrip()) <= indent:
            break
        parts.append(line.strip().split(";", 1)[0])
        if ";" in line:
            break
    return "\n".join(parts)


def _connection_targets(block: str, qml_text: str) -> set[str]:
    """A `target:` kifejezés azonosítói, fájlhelyes alias-feloldással."""
    target = re.search(r"\btarget\s*:\s*([^\n;]+)", block)
    if target is None:
        return set()
    names = set(re.findall(r"\b[A-Za-z_]\w*\b", target.group(1)))
    pending = list(names)
    while pending:
        name = pending.pop()
        rhs = _property_rhs(qml_text, name)
        if rhs is None:
            continue
        for resolved in re.findall(r"\b[A-Za-z_]\w*\b", rhs):
            if resolved not in names:
                names.add(resolved)
                pending.append(resolved)
    return names


def _qml_receivers(qml_text: str) -> list[tuple[set[str], set[str]]]:
    """QML `Connections`-fogadók indexe a saját fájl targetjeivel."""
    blocks = _connections_blocks(qml_text)
    connected: list[tuple[set[str], set[str]]] = []
    for block in blocks:
        handlers = set(re.findall(r"\bon[A-Z]\w*\b", block))
        connected.append((_connection_targets(block, qml_text), handlers))
    return connected


def _has_connection_receiver(
    declaration: SignalDecl,
    qml_receivers: list[tuple[set[str], set[str]]],
) -> bool:
    handler = _handler_name(declaration.name)
    if any(
        handler in handlers and targets & declaration.target_names
        for targets, handlers in qml_receivers
    ):
        return True
    return False


def _has_imperative_receiver(
    declaration: SignalDecl, text: str, own_python_text: str = ""
) -> bool:
    """`target.signal.connect(...)` csak a deklaráló ismert targetjére számít."""
    self_connect = rf"\bself\s*\.\s*{re.escape(declaration.name)}\s*\.\s*connect\s*\("
    if re.search(self_connect, own_python_text):
        return True
    # A mixin jelzéseit az AppController a saját `self`-én köti be. Ez a
    # mixin és a végső osztály közti szándékos, ellenőrizhető kapcsolat.
    if declaration.owner and declaration.owner.endswith("Mixin") and re.search(
        self_connect, text
    ):
        return True
    pattern = re.compile(
        rf"\b(?:self\s*\.\s*)?([A-Za-z_]\w*)(?:\s*\(\s*\))?\s*"
        rf"\.\s*{re.escape(declaration.name)}\s*"
        r"\.\s*connect\s*\("
    )
    module = Path(declaration.path).stem
    for match in pattern.finditer(text):
        target = match.group(1).lstrip("_")
        if _camel_name(target) in declaration.target_names:
            return True
        if target.startswith("get_") and module in target:
            return True
    return False


def has_receiver(
    declaration: SignalDecl,
    python_text: str,
    qml_text: str,
    own_python_text: str,
    qml_receivers: list[tuple[set[str], set[str]]],
) -> bool:
    """Van-e a KONKRÉT deklaráció fogadója, nem csak névazonos jelzésé."""
    return _has_connection_receiver(declaration, qml_receivers) or _has_imperative_receiver(
        declaration, python_text, own_python_text
    ) or _has_imperative_receiver(declaration, qml_text)


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
    qml_receivers = [
        receiver
        for path in root.rglob("*.qml")
        for receiver in _qml_receivers(_read_text(path))
    ]
    python_by_path = {
        path.relative_to(root).as_posix(): _read_text(path)
        for path in root.rglob("*.py")
    }
    notify = collect_notify_signals(root)
    declarations = collect_declarations(root)
    silent = tuple(
        declaration
        for declaration in declarations
        if (declaration.path, declaration.owner, declaration.name) not in notify
        and not has_receiver(
            declaration,
            python_text,
            qml_text,
            python_by_path[declaration.path],
            qml_receivers,
        )
    )
    notify_count = sum(
        1 for d in declarations if (d.path, d.owner, d.name) in notify
    )
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
