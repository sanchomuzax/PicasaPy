"""#3342 — a spec-cím-atlasz négy gépi őre.

Az atlasz generátora a privát `picasapy-agent` repóban él, de a
regenerálási szerződés tiszta, publikus magon keresztül CI-ben is ellenőrizhető.
A commitolt kimenet nem kézi leltár: ugyanabból a `docs/specs/` fából minden
futásnak bájtra ugyanazt kell előállítania.
"""
from __future__ import annotations

import csv
import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
ATLASZ_TSV = REPO / "docs" / "specs" / "cim-atlasz.tsv"
ATLASZ_MD = REPO / "docs" / "specs" / "cim-atlasz.md"
CORE_PATH = REPO / "scripts" / "cim_atlasz_core.py"


def _core():
    spec = importlib.util.spec_from_file_location("cim_atlasz_core_3342", CORE_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - importlib guard
        raise ImportError(f"nem tölthető be: {CORE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def atlasz():
    return _core()


def test_a_cim_normalizalasa_es_tartomanya(atlasz):
    assert atlasz.normalize_address("0x4a2f10") == "0x004a2f10"
    assert atlasz.normalize_address("0X00A2F010") == "0x00a2f010"
    assert atlasz.normalize_address("0x003fffff") is None
    assert atlasz.normalize_address("0x01000001") is None
    assert atlasz.normalize_address("0x9d57") is None


def test_a_fajta_sorrendje_es_ismeretlenje(atlasz):
    assert atlasz.classify_line("0x00400000 vtábla FUN_00400000") == "vtábla"
    assert atlasz.classify_line("0x00400000 .?AVCThing@@") == "RTTI"
    assert atlasz.classify_line("0x00400000 FUN_00400000 függvény") == "függvény"
    assert atlasz.classify_line("0x00400000 fld [eax], konstans") == "konstans"
    assert atlasz.classify_line("0x00400000 adat-tábla") == "adat"
    assert atlasz.classify_line("0x00400000 megnevezett cím") == "?"


def test_a_regeneralt_kimenet_bajtra_egyezik(atlasz):
    records, stats = atlasz.collect_records(REPO / "docs" / "specs")
    assert records, "az atlasz üres — hibás bemenet mellett nem lehet zöld"
    assert ATLASZ_TSV.read_bytes() == atlasz.render_tsv(records, stats).encode("utf-8")
    assert ATLASZ_MD.read_bytes() == atlasz.render_markdown(records, stats).encode("utf-8")


def test_minden_rekord_feloldhato_es_a_forrassor_letezik(atlasz):
    with ATLASZ_TSV.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    assert rows, "a commitolt TSV üres"
    assert {"cim", "fajta", "lap", "szakasz", "sor", "mit"} <= set(rows[0])
    source_lines: dict[Path, list[str]] = {}
    for row in rows:
        source = REPO / "docs" / "specs" / row["lap"]
        assert source.is_file(), row
        assert row["szakasz"], row
        line_no = int(row["sor"])
        assert line_no >= 1
        lines = source_lines.setdefault(
            source, source.read_text(encoding="utf-8").splitlines()
        )
        assert line_no <= len(lines), row
        assert row["mit"].strip(), row


def test_a_kiszurt_es_ismeretlen_darabszam_lathato(atlasz):
    text = ATLASZ_MD.read_text(encoding="utf-8")
    records, stats = atlasz.collect_records(REPO / "docs" / "specs")
    assert f"Bemeneti lapok: **{stats['lapok']}**" in text
    assert f"Különböző címek: **{stats['kulonbozo_cimek']}**" in text
    assert f"Kiszűrt címjelölések: **{stats['kiszurt']}**" in text
    assert f"Ismeretlen fajta (`?`): **{stats['ismeretlen_fajta']}**" in text
    assert len(records) >= stats["kulonbozo_cimek"]


def test_nem_kerul_utasitasminta_a_kimenetbe():
    text = ATLASZ_TSV.read_text(encoding="utf-8") + ATLASZ_MD.read_text(encoding="utf-8")
    minta = re.compile(
        r"\b(?:mov|fld|fstp|call|jmp|push|lea|cmp|test|ret|add|sub|xor)[ \t]+"
        r"(?:eax|ebx|ecx|edx|esi|edi|esp|ebp|0x[0-9a-f]+|dword|byte)\b",
        re.IGNORECASE,
    )
    assert not minta.search(text), "x86 utasításminta került az atlaszba"


def test_a_00_index_belatasi_pontja_megvan():
    text = (REPO / "docs" / "specs" / "00-index.md").read_text(encoding="utf-8")
    assert "cim-atlasz.md" in text
    assert "cim-atlasz.tsv" in text
    assert "cim_atlasz.py" in text
