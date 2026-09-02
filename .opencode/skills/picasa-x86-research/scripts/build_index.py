#!/usr/bin/env python3
"""A BinaryIndex.java CSV-kimenetéből determinisztikus SQLite-indexet épít."""

from __future__ import annotations

import argparse
from contextlib import closing
import csv
import json
from pathlib import Path
import re
import sqlite3
from typing import Iterable


EXPECTED_REGISTRY = {
    "debug": "0x008f8360", "autobacklight": "0x008f7cc0",
    "finetune": "0x008f7cf0", "finetune2": "0x008f7ee0",
    "autolight": "0x008f80c0", "autocolor": "0x008f82a0",
    "triple": "0x008f8a60", "triple2": "0x008f8b90",
    "triple3": "0x008f8ce0", "colorfix": "0x008f9190",
    "ansel": "0x008f8410", "bw": "0x008f84c0",
    "whitept": "0x008f9270", "enhance": "0x008f8840",
    "warm": "0x008f8930", "blur": "0x008f89a0",
    "tilt": "0x008f8810", "glow": "0x008f8f70",
    "glow2": "0x008f8f70", "colortemp": "0x008f8ea0",
    "unsharp": "0x008f8f30", "unsharp2": "0x008f8f30",
    "tint": "0x008f9630", "dir_tint": "0x008f9880",
    "radtint": "0x008f8730", "sat": "0x008f8ff0",
    "grain": "0x008f88e0", "grain2": "0x008f88e0",
    "sepia": "0x008f8950", "rainbow": "0x008f92d0",
    "backlight": "0x008f8970", "fill": "0x008f8970",
    "autocontrast": "0x008f89d0", "radblur": "0x008f8520",
    "radsat": "0x008f8680", "linblur": "0x008f99c0",
    "dir_sat": "0x008f8fb0", "dir_brite": "0x008f9050",
    "dir_sharp": "0x008f9090", "gamma": "0x008f8e30",
    "contrast": "0x008f8a20", "shadow": "0x008f8ee0",
}

EXPECTED_WORKER_EDGES = {
    ("backlight", "0x0090ac20"), ("fill", "0x0090ac20"),
    ("autobacklight", "0x0090ac20"), ("finetune", "0x0090ac20"),
    ("finetune2", "0x0090ac20"), ("triple", "0x0090ac20"),
    ("triple2", "0x0090ac20"), ("triple3", "0x0090ac20"),
    ("autolight", "0x0090c3b0"), ("autocolor", "0x0090eda0"),
    ("colorfix", "0x0090eda0"), ("whitept", "0x0090eda0"),
    ("colortemp", "0x0090ea10"), ("contrast", "0x0090c2c0"),
    ("enhance", "0x009db610"), ("autocontrast", "0x009db610"),
    ("shadow", "0x0090d3e0"), ("blur", "0x0090cf60"),
    ("glow", "0x0090d4b0"), ("glow2", "0x0090d4b0"),
    ("unsharp", "0x0090c4a0"), ("unsharp2", "0x0090c4a0"),
    ("warm", "0x0090c040"), ("grain", "0x0090a2e0"),
    ("grain2", "0x0090a2e0"), ("dir_sat", "0x0090dbb0"),
    ("dir_brite", "0x0090d8b0"), ("linblur", "0x0090de10"),
}

CSV_FILES = {
    "functions": "functions.csv",
    "xrefs": "xrefs.csv",
    "string_xrefs": "string_xrefs.csv",
    "imports": "imports.csv",
    "rtti": "rtti.csv",
    "data_symbols": "data_symbols.csv",
}

ALIASES = {
    "functions": {"addr": "address"},
    "xrefs": {
        "from_addr": "from_address", "from_func_addr": "from_function_address",
        "to_addr": "to_address", "type": "kind",
    },
    "string_xrefs": {
        "func_addr": "function_address", "str_addr": "string_address", "text": "string",
    },
    "imports": {
        "addr": "address", "dll": "library", "symbol": "name",
        "func_addr": "function_address",
    },
    "rtti": {"vtable_addr": "address", "class_name": "name", "method_addrs": "kind"},
    "data_symbols": {"addr": "address", "type": "data_type"},
}


def canonical_address(value: object) -> str:
    """Egységes, 32 bites, nulla-kitöltött hex címet ad vissza."""
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and re.fullmatch(r"(?:0x)?[0-9a-fA-F]{1,8}", value.strip()):
        text = value.strip()
        number = int(text, 16)
    else:
        raise ValueError(f"Érvénytelen 32 bites cím: {value!r}")
    if not 0 <= number <= 0xFFFFFFFF:
        raise ValueError(f"A cím kívül esik a 32 bites tartományon: {value!r}")
    return f"0x{number:08x}"


def _read_registry(path: Path) -> dict[str, str]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        items = raw.items()
    elif isinstance(raw, list):
        items = ((row[0], row[1]) for row in raw)
    else:
        raise ValueError("A callback-jegyzék csak objektum vagy sorlista lehet.")
    return {str(name): canonical_address(address) for name, address in items}


def validate_invariants(registry_json: Path, worker_edges_json: Path) -> None:
    """Igazolja, hogy a kézzel ellenőrzött 42 callback és 28 él nem változott."""
    registry = _read_registry(Path(registry_json))
    if registry != EXPECTED_REGISTRY:
        missing = sorted(set(EXPECTED_REGISTRY.items()) - set(registry.items()))
        extra = sorted(set(registry.items()) - set(EXPECTED_REGISTRY.items()))
        raise ValueError(f"A 42 callback invariánsa sérült; hiány/eltérés={missing}; extra={extra}")

    worker_raw = json.loads(Path(worker_edges_json).read_text(encoding="utf-8"))
    workers = {(str(name), canonical_address(address)) for name, address in worker_raw}
    if workers != EXPECTED_WORKER_EDGES:
        missing = sorted(EXPECTED_WORKER_EDGES - workers)
        extra = sorted(workers - EXPECTED_WORKER_EDGES)
        raise ValueError(f"A munkafüggvény-élek invariánsa sérült; hiány={missing}; extra={extra}")


def _validate_meta(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    digest = raw.get("binary_sha256", "")
    version = raw.get("ghidra_version", "")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        raise ValueError("A meta binary_sha256 mezője nem 64 jegyű SHA-256.")
    if version != "12.1.2":
        raise ValueError(f"Nem támogatott Ghidra-verzió: {version!r}")
    image_base = canonical_address(raw.get("image_base"))
    result = {str(key): str(value) for key, value in raw.items()}
    result["binary_sha256"] = digest.lower()
    result["ghidra_version"] = version.strip()
    result["image_base"] = image_base
    return result


def _read_csv(path: Path, table: str) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"Nincs CSV-fejléc: {path}")
        aliases = ALIASES[table]
        columns = [aliases.get(name, name) for name in reader.fieldnames]
        if len(set(columns)) != len(columns):
            raise ValueError(f"Ütköző CSV-oszlopok: {path}")
        rows = []
        for source in reader:
            row = {aliases.get(key, key): value for key, value in source.items()}
            rows.append(row)
    return columns, rows


def _normalize_addresses(table: str, rows: list[dict[str, str]]) -> None:
    address_columns = {
        "functions": ("address",),
        "xrefs": ("from_address", "from_function_address", "to_address"),
        "string_xrefs": ("function_address", "string_address"),
        "imports": ("address", "function_address"),
        "rtti": ("address",),
        "data_symbols": ("address",),
    }[table]
    for row in rows:
        for column in address_columns:
            if column in row and row[column] not in (None, ""):
                row[column] = canonical_address(row[column])


def _quoted(identifier: str) -> str:
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", identifier):
        raise ValueError(f"Nem biztonságos oszlopnév: {identifier!r}")
    return f'"{identifier}"'


def _create_table(connection: sqlite3.Connection, table: str, columns: list[str]) -> None:
    definitions = [f"{_quoted(column)} TEXT NOT NULL DEFAULT ''" for column in columns]
    if table == "functions" and "address" in columns:
        definitions[columns.index("address")] = '"address" TEXT PRIMARY KEY'
    connection.execute(f'CREATE TABLE "{table}" ({", ".join(definitions)})')


def _insert_rows(
    connection: sqlite3.Connection,
    table: str,
    columns: list[str],
    rows: Iterable[dict[str, str]],
) -> None:
    ordered = sorted(rows, key=lambda row: tuple(row.get(column, "") for column in columns))
    placeholders = ",".join("?" for _ in columns)
    names = ",".join(_quoted(column) for column in columns)
    connection.executemany(
        f'INSERT INTO "{table}" ({names}) VALUES ({placeholders})',
        [[row.get(column, "") or "" for column in columns] for row in ordered],
    )


def _validate_database_invariants(
    connection: sqlite3.Connection,
    registry_json: Path | None,
    worker_edges_json: Path | None,
) -> None:
    functions = {row[0] for row in connection.execute("SELECT address FROM functions")}
    xref_columns = {row[1] for row in connection.execute("PRAGMA table_info(xrefs)")}
    if {"from_address", "to_address", "kind"} <= xref_columns:
        dangling = connection.execute(
            "SELECT from_address, to_address FROM xrefs "
            "WHERE lower(kind) = 'call' AND to_address NOT IN (SELECT address FROM functions) LIMIT 1"
        ).fetchone()
        if dangling:
            raise ValueError(f"Függvény nélküli CALL cél: {dangling[0]} -> {dangling[1]}")

    # A teljes exportnál az elfogadási invariánsoknak magából az indexből is
    # vissza kell jönniük. A kis unit-fixture csak a gráf általános épségét méri.
    if (
        registry_json is not None
        and worker_edges_json is not None
        and len(functions) >= len(EXPECTED_REGISTRY)
    ):
        registry = _read_registry(Path(registry_json))
        missing_callbacks = sorted(
            (name, address)
            for name, address in registry.items()
            if address not in functions
        )
        source_column = (
            "from_function_address"
            if "from_function_address" in xref_columns
            else "from_address"
        )
        edges = {
            (row[0], row[1])
            for row in connection.execute(
                f"SELECT {source_column}, to_address FROM xrefs WHERE lower(kind) = 'call'"
            )
        }
        missing_edges = []
        for name, target in json.loads(Path(worker_edges_json).read_text(encoding="utf-8")):
            edge = (registry[name], canonical_address(target))
            if edge not in edges:
                missing_edges.append((name, *edge))
        if missing_callbacks or missing_edges:
            raise ValueError(
                f"Az index elfogadási invariánsa sérült; callback={missing_callbacks}; élek={missing_edges}"
            )


def build_index(
    input_dir: Path,
    output_db: Path,
    *,
    registry_json: Path | None = None,
    worker_edges_json: Path | None = None,
) -> None:
    """Ellenőrzött, byte-determinisztikus SQLite-adatbázist épít."""
    input_dir = Path(input_dir)
    output_db = Path(output_db)
    if (registry_json is None) != (worker_edges_json is None):
        raise ValueError("A registry és a worker-élek csak együtt adhatók meg.")
    if registry_json is not None and worker_edges_json is not None:
        registry_json = Path(registry_json)
        worker_edges_json = Path(worker_edges_json)
        validate_invariants(registry_json, worker_edges_json)
    meta = _validate_meta(input_dir / "meta.json")
    loaded = {}
    for table, filename in CSV_FILES.items():
        columns, rows = _read_csv(input_dir / filename, table)
        _normalize_addresses(table, rows)
        loaded[table] = (columns, rows)

    output_db.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_db.with_suffix(output_db.suffix + ".part")
    temporary.unlink(missing_ok=True)
    try:
        with closing(sqlite3.connect(temporary)) as connection:
            connection.execute("PRAGMA page_size=4096")
            connection.execute("PRAGMA journal_mode=DELETE")
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            connection.executemany("INSERT INTO meta VALUES (?, ?)", sorted(meta.items()))
            for table in CSV_FILES:
                columns, rows = loaded[table]
                _create_table(connection, table, columns)
                _insert_rows(connection, table, columns, rows)
            _validate_database_invariants(connection, registry_json, worker_edges_json)
            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise ValueError(f"SQLite idegenkulcs-hiba: {violations}")
            connection.execute("PRAGMA user_version=1")
            connection.commit()
            connection.execute("VACUUM")
        temporary.replace(output_db)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_db", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--worker-edges", type=Path)
    args = parser.parse_args()
    build_index(
        args.input_dir,
        args.output_db,
        registry_json=args.registry,
        worker_edges_json=args.worker_edges,
    )


if __name__ == "__main__":
    main()
