"""A Picasa `.tpl` parancsnyelve: parszolás + `<%var%>`/`<%if%>` motor.

Teljes nyelvi spec: `docs/specs/picasa-program-resources.md` 2.3–2.4.
alfejezet. A `.tpl` fájlok egyszerű, soronkénti, `#`-tel kommentezhető
parancsnyelvet használnak (`define`/`include`/`loop`/`targetloop`/`copy`);
a beillesztett HTML/XML-fájlokban pedig `<%valtozoNev%>` behelyettesítés és
`<%if [!]valtozoNev%>...<%endif%>` feltétel működik.

Ez a modul KIZÁRÓLAG a nyelvet (parszolás + kiértékelés) adja — a tényleges
fájl-beillesztést, hurkolást és a változó-táblák feltöltését az `engine`/
`context` modulok végzik."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

# ---------------------------------------------------------------------------
# 1. `.tpl` parancsok — soronkénti parszolás
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DefineCommand:
    """`define variableName variableValue` — csak az utolsó `define` érvényes
    egy adott névre (a hívó/engine dolga felülírni a korábbit)."""

    name: str
    value: str


@dataclass(frozen=True)
class IncludeCommand:
    """`include fileName` — HTML/sablonfájl beillesztése a beillesztés
    pillanatában érvényes változó-táblával."""

    file_name: str


@dataclass(frozen=True)
class LoopCommand:
    """`loop perImageFile [columnCount rowStartInclude rowEndInclude]` —
    a `columnCount`/`rowStartInclude`/`rowEndInclude` a hivatalos Picasa-
    dokumentáció szerint sosem lett megvalósítva (`notImplemented`), ezért
    itt is figyelmen kívül maradnak, csak eltároljuk a nyers extra
    argumentumokat (kerekasztal-kompatibilitás, hibaüzenetekhez)."""

    per_image_file: str
    extra_args: tuple[str, ...] = ()


@dataclass(frozen=True)
class TargetLoopCommand:
    """`targetloop targetTemplateFile targetIncludeFile [...]` — képenként
    külön fájlt exportál (`targetTemplateFile` alapján), és a jelenlegi
    fájlba `targetIncludeFile`-t illeszti be képenként."""

    target_template_file: str
    target_include_file: str


@dataclass(frozen=True)
class CopyCommand:
    """`copy source [destination]` — statikus erőforrás (rekurzív) másolása."""

    source: str
    destination: str | None = None


@dataclass(frozen=True)
class TemplateHeader:
    """`#templatefile -v "verzió" -n "név" -d "leírás"` — a sablonválasztó
    UI-hoz szükséges metaadat; a tényleges futtatást nem befolyásolja."""

    version: str = ""
    name: str = ""
    description: str = ""


Command = DefineCommand | IncludeCommand | LoopCommand | TargetLoopCommand | CopyCommand


class TplSyntaxError(ValueError):
    """Érvénytelen/ismeretlen `.tpl` parancssor — emberi olvasásra szánt
    üzenettel (fájlnév + sorszám a hívó felelőssége, itt csak a sor tartalma)."""


_TOKEN_PATTERN = re.compile(r'"([^"]*)"|(\S+)')


def _tokenize(line: str) -> list[str]:
    """Whitespace-alapú tokenizálás, `"idézett string"` támogatással —
    SZÁNDÉKOSAN nem `shlex`: a `.tpl` sorokban a `copy assets\\` alakú,
    záró fordított perjeles (Windows-könyvtár-) jelölés a `shlex` escape-
    kezelésébe ütközne (backslash a sor VÉGÉN → "No escaped character").
    Itt a backslash mindig egyszerű, literális karakter."""
    return [quoted if quoted else bare for quoted, bare in _TOKEN_PATTERN.findall(line)]


def parse_header(text: str) -> TemplateHeader:
    """A `#templatefile -v ... -n ... -d ...` fejléc sor kiolvasása —
    bárhol a fájl elején lehet, a többi sortól függetlenül keressük."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#templatefile"):
            tokens = _tokenize(stripped[len("#templatefile") :])
            values = {"v": "", "n": "", "d": ""}
            it = iter(tokens)
            for token in it:
                if token in ("-v", "-n", "-d"):
                    values[token[1]] = next(it, "")
            return TemplateHeader(
                version=values["v"], name=values["n"], description=values["d"]
            )
    return TemplateHeader()


def parse_tpl(text: str) -> tuple[Command, ...]:
    """Egy `.tpl` fájl parancssorainak feldolgozása parancs-objektumok
    listájává. Üres sorok és `#`-tel kezdődő (megjegyzés/fejléc) sorok
    kimaradnak. Ismeretlen parancsnál `TplSyntaxError`."""
    commands: list[Command] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        tokens = _tokenize(line)
        if not tokens:
            continue
        keyword, *args = tokens
        commands.append(_parse_command(keyword, args, raw_line))
    return tuple(commands)


def _parse_command(keyword: str, args: list[str], raw_line: str) -> Command:
    if keyword == "define":
        if len(args) < 2:
            raise TplSyntaxError(f"define legalább 2 argumentumot vár: {raw_line!r}")
        # a spec szerint a define egyetlen szóértékű változót vár, de a
        # robusztusság kedvéért az esetleges további tokeneket (idézőjel
        # nélküli, szóközös érték) összefűzzük — hű az eredeti sorhoz.
        return DefineCommand(name=args[0], value=" ".join(args[1:]))
    if keyword == "include":
        if len(args) != 1:
            raise TplSyntaxError(f"include pontosan 1 fájlnevet vár: {raw_line!r}")
        return IncludeCommand(file_name=args[0])
    if keyword == "loop":
        if not args:
            raise TplSyntaxError(f"loop legalább 1 argumentumot vár: {raw_line!r}")
        return LoopCommand(per_image_file=args[0], extra_args=tuple(args[1:]))
    if keyword == "targetloop":
        if len(args) < 2:
            raise TplSyntaxError(f"targetloop legalább 2 argumentumot vár: {raw_line!r}")
        return TargetLoopCommand(
            target_template_file=args[0], target_include_file=args[1]
        )
    if keyword == "copy":
        if not args:
            raise TplSyntaxError(f"copy legalább 1 argumentumot vár: {raw_line!r}")
        destination = args[1] if len(args) > 1 else None
        return CopyCommand(source=args[0], destination=destination)
    raise TplSyntaxError(f"ismeretlen .tpl parancs: {keyword!r} ({raw_line!r})")


# ---------------------------------------------------------------------------
# 2. `<%var%>` behelyettesítés és `<%if%>` feltétel a HTML/XML tartalomban
# ---------------------------------------------------------------------------

_VAR_PATTERN = re.compile(r"<%(\w+)%>")
_IF_OPEN_PATTERN = re.compile(r"<%if\s+(!?)(\w+)%>")
_IF_ANY_PATTERN = re.compile(r"<%if\s+!?\w+%>|<%endif%>")
_ENDIF_TOKEN = "<%endif%>"

# "hamis" karakterláncok: hiányzó/üres, vagy explicit "0"/"false" —
# a Picasa sablonokban a logikai változók "true"/""/"0" alakban fordulnak
# elő (a doksi nem rögzíti pontosan, ez egy megengedő, józan olvasat).
_FALSY_VALUES = frozenset({"", "0", "false"})


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() not in _FALSY_VALUES


def eval_conditionals(text: str, variables: Mapping[str, str]) -> str:
    """`<%if [!]name%>...<%endif%>` feltételek kiértékelése — beágyazott
    `<%if%>`-eket is helyesen kezel (a legkülső párra illesztünk, majd a
    megtartott tartalmat rekurzívan újra feldolgozzuk)."""
    result: list[str] = []
    pos = 0
    while True:
        open_match = _IF_OPEN_PATTERN.search(text, pos)
        if open_match is None:
            result.append(text[pos:])
            break
        result.append(text[pos : open_match.start()])
        negate = open_match.group(1) == "!"
        name = open_match.group(2)
        inner_start = open_match.end()
        end_pos = _find_matching_endif(text, inner_start)
        if end_pos is None:
            # nincs záró <%endif%> — hű maradunk a nyers szöveghez, nem
            # dobunk kivételt (a robusztus round-trip elve, CLAUDE.md)
            result.append(text[open_match.start() :])
            break
        inner = text[inner_start:end_pos]
        condition_holds = _is_truthy(variables.get(name)) != negate
        if condition_holds:
            result.append(eval_conditionals(inner, variables))
        pos = end_pos + len(_ENDIF_TOKEN)
    return "".join(result)


def _find_matching_endif(text: str, start: int) -> int | None:
    """A `start`-tól keresett, a nyitó `<%if%>`-hez tartozó `<%endif%>`
    kezdőpozíciója — beágyazott `<%if%>...<%endif%>` párokat átugorva."""
    depth = 1
    for match in _IF_ANY_PATTERN.finditer(text, start):
        if match.group(0) == _ENDIF_TOKEN:
            depth -= 1
            if depth == 0:
                return match.start()
        else:
            depth += 1
    return None


def _substitute_one(match: re.Match[str], variables: Mapping[str, str]) -> str:
    name = match.group(1)
    if name == "endif":
        # egy pórul maradt (pár nélküli) <%endif%> jelölő NEM változó — az
        # eval_conditionals mindig előbb fut, ez csak védőháló hibás/
        # befejezetlen sablonra (ld. eval_conditionals unterminated-if ága)
        return match.group(0)
    return variables.get(name, "")


def substitute_vars(text: str, variables: Mapping[str, str]) -> str:
    """`<%name%>` → `variables[name]`; ismeretlen változó üres sztringre
    cserélődik (megengedő viselkedés — a hiányzó változó nem hibás sablon,
    csak üres kimenetet ad, ahogy egy egyszerű makrónyelvtől elvárható)."""
    return _VAR_PATTERN.sub(lambda m: _substitute_one(m, variables), text)


def render(text: str, variables: Mapping[str, str]) -> str:
    """Egy beillesztett fájl (HTML/XML) teljes feldolgozása: előbb a
    feltételek, utána a változó-behelyettesítés — ebben a sorrendben, mert
    a feltétel a NÉV alapján dönt (a `variables`-ből), nem a már
    behelyettesített szövegből."""
    return substitute_vars(eval_conditionals(text, variables), variables)
