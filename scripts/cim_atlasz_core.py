"""A cím-atlasz determinisztikus, publikus kimeneti magja (#3342).

A parancssori generátor a privát `picasapy-agent/eszkozok/cim_atlasz.py` fájlban
él. Ez a modul azért publikus, mert a CI regenerálási őrének ugyanazt a
bájtszerializálási szerződést kell futtatnia a privát repó nélkül is.

A modul kizárólag a saját `docs/specs/*.md` szövegét dolgozza fel: nem olvas
binárist, nem másol utasításbájtokat, és nem tartalmaz kézzel karbantartott
cím-listát.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

SOURCE_SUFFIX = ".md"
GENERATED_NAMES = frozenset({"cim-atlasz.md", "cim-atlasz.tsv"})
ADDRESS_CANDIDATE_RE = re.compile(r"(?i)0x[0-9a-f]+\b")
HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
INSTRUCTION_RE = re.compile(
    r"\b(?:mov|fld|fstp|fst|call|jmp|push|lea|cmp|test|ret|add|sub|xor|or|and|fild|fistp)"
    r"\s+(?=(?:eax|ebx|ecx|edx|esi|edi|esp|ebp|eip|0x[0-9a-f]+|dword|word|byte)\b)",
    re.IGNORECASE,
)
DATA_WORDS = re.compile(
    r"(?i)\b(?:adat|tábla|tömb|mező|kulcs|érték|szöveg|sztring|literal|data|rdata|"
    r"offset|eltolás|sorszám|darabszám|rekord|string|table|array|const)\b"
)


@dataclass(frozen=True)
class Record:
    address: str
    address_value: int
    kind: str
    page: str
    section: str
    section_line: int
    line: int
    description: str


def normalize_address(token: str) -> str | None:
    """Normalizál egy 6–8 jegyű VA-jelöltet, vagy elutasítja."""
    raw = token.strip()
    if not raw.lower().startswith("0x"):
        return None
    digits = raw[2:]
    if not 6 <= len(digits) <= 8 or not re.fullmatch(r"[0-9a-fA-F]+", digits):
        return None
    value = int(digits, 16)
    if not 0x400000 <= value <= 0x1000000:
        return None
    return f"0x{value:08x}"


def classify_line(line: str) -> str:
    """A jegyben rögzített, sorrendfüggő környezeti osztályozás."""
    folded = line.casefold()
    if "vtbl" in folded or "vtábla" in folded:
        return "vtábla"
    if ".?av" in folded:
        return "RTTI"
    if "fun_" in folded or "függvény" in folded or "hívó" in folded:
        return "függvény"
    if (
        re.search(r"=\s*(?:-?\d+(?:[.,]\d+)?|0x[0-9a-f]+)", folded)
        or "konstans" in folded
        or re.search(r"\bfld\b", folded)
    ):
        return "konstans"
    if DATA_WORDS.search(line):
        return "adat"
    return "?"


def _safe_description(line: str) -> str:
    """Egy sor első tagmondata, assembly-kódminta nélkül, legfeljebb 120 jel."""
    text = re.sub(r"\s+", " ", line.strip())
    text = INSTRUCTION_RE.sub("utasítás ", text)
    # A Markdown-kódhatárok és táblázat-jelek nem maradhatnak ki a sorból.
    text = text.replace("|", "\\|").replace("`", "\\`")
    first = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0]
    if len(first) > 120:
        return first[:117].rstrip() + "…"
    return first


def _section_for_heading(heading: str, ordinal: int) -> str:
    return f"{ordinal}. {heading.strip()}"


def _records_for_page(path: Path) -> tuple[list[Record], int]:
    records: list[Record] = []
    section = "(dokumentum eleje)"
    section_line = 1
    ordinal = 0
    candidates = 0
    lines = path.read_text(encoding="utf-8").splitlines()
    for line_no, line in enumerate(lines, 1):
        heading = HEADING_RE.match(line)
        if heading:
            ordinal += 1
            section = _section_for_heading(heading.group(2), ordinal)
            section_line = line_no
        for match in ADDRESS_CANDIDATE_RE.finditer(line):
            candidates += 1
            normalized = normalize_address(match.group(0))
            if normalized is None:
                continue
            value = int(normalized[2:], 16)
            records.append(
                Record(
                    address=normalized,
                    address_value=value,
                    kind=classify_line(line),
                    page=path.name,
                    section=section,
                    section_line=section_line,
                    line=line_no,
                    description=_safe_description(line),
                )
            )
    return records, candidates


def collect_records(spec_dir: Path) -> tuple[list[Record], dict[str, int]]:
    """Összegyűjti és stabil sorrendbe rendezi a spec-lapok rekordjait."""
    all_records: list[Record] = []
    pages = 0
    candidates = 0
    filtered = 0
    for path in sorted(spec_dir.glob(f"*{SOURCE_SUFFIX}")):
        if path.name in GENERATED_NAMES:
            continue
        pages += 1
        records, page_candidates = _records_for_page(path)
        all_records.extend(records)
        candidates += page_candidates
    valid_candidates = len(all_records)
    filtered = candidates - valid_candidates
    all_records.sort(key=lambda r: (r.address_value, r.page, r.line, r.kind, r.description))
    unique_addresses = len({r.address_value for r in all_records})
    kinds = Counter(r.kind for r in all_records)
    stats = {
        "lapok": pages,
        "jeloltek": candidates,
        "hivatkozasok": valid_candidates,
        "kiszurt": filtered,
        "kulonbozo_cimek": unique_addresses,
        "ismeretlen_fajta": kinds.get("?", 0),
    }
    return all_records, stats


def _tsv_cell(value: object) -> str:
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")


def render_tsv(records: Iterable[Record], stats: dict[str, int]) -> str:
    del stats  # A TSV-ben a rekordok mellett nincs ismételt, kézzel írt mérőszám.
    lines = ["cim\tfajta\tlap\tszakasz\tsor\tmit"]
    for record in records:
        lines.append(
            "\t".join(
                _tsv_cell(value)
                for value in (
                    record.address,
                    record.kind,
                    record.page,
                    record.section,
                    record.line,
                    record.description,
                )
            )
        )
    return "\n".join(lines) + "\n"


def _md(value: object) -> str:
    return _tsv_cell(value)


def render_markdown(records: list[Record], stats: dict[str, int]) -> str:
    """Olvasható, címblokkokra bontott kimenet."""
    addresses = sorted({r.address_value for r in records})
    by_address: dict[int, list[Record]] = {}
    for record in records:
        by_address.setdefault(record.address_value, []).append(record)
    rows: list[str] = [
        "# Cím-atlasz — GENERÁLT, ne szerkeszd kézzel",
        "",
        "> Ezt a lapot a privát `picasapy-agent/eszkozok/cim_atlasz.py` írja a",
        "> publikus, determinisztikus feldolgozó magon keresztül. A generálási",
        "> időbélyeg szándékosan nincs benne: az őrnek bájtra egyező kimenetet",
        "> kell tudnia összevetni.",
        "",
        f"- Bemeneti lapok: **{stats['lapok']}**",
        f"- Elfogadott hivatkozások: **{stats['hivatkozasok']}**",
        f"- Különböző címek: **{stats['kulonbozo_cimek']}**",
        f"- Kiszűrt címjelölések: **{stats['kiszurt']}**",
        f"- Ismeretlen fajta (`?`): **{stats['ismeretlen_fajta']}**",
        "",
        "A címek csak a `0x400000`–`0x1000000` tartomány 6–8 jegyű",
        "jelöléseiből kerülnek be. A rekord a saját spec-lapunk hivatkozását, a",
        "legközelebbi `##`/`###` szakaszt, a forrássort és annak rövid leírását adja.",
        "",
    ]
    for block_start in range(0, len(addresses), 4096):
        block = addresses[block_start : block_start + 4096]
        block_end = block_start + len(block)
        rows.extend(
            [
                f"## Címblokk {block_start + 1}–{block_end}",
                "",
                "| cím | fajta | lap / szakasz | sor | mit |",
                "|---|---|---|---:|---|",
            ]
        )
        for value in block:
            for record in by_address[value]:
                source = f"{record.page}#L{record.section_line}"
                rows.append(
                    f"| `{record.address}` | {record.kind} | "
                    f"[{_md(record.page)} § {_md(record.section)}]({source}) | "
                    f"{record.line} | {_md(record.description)} |"
                )
        rows.append("")
    return "\n".join(rows)
