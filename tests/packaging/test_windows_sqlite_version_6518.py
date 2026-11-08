"""#6518: a Windows-csomag SQLite-verziója legyen nyomon követhető."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import yaml


def test_indulasi_verziojelentes_tartalmazza_a_betoltott_sqlite_verziot():
    from picasapy.app.startup_diagnostics import runtime_version_messages

    messages = runtime_version_messages("6.11.3", "6.11.3")

    assert any(f"SQLite {sqlite3.sqlite_version}" in message for message in messages)


def test_a_wal_resetet_nem_javitott_sqlite_figyelmeztet_a_hibanaploban(caplog):
    from picasapy.app.startup_diagnostics import warn_if_sqlite_wal_reset_vulnerable

    with caplog.at_level(logging.WARNING, logger="picasapy.startup"):
        warned = warn_if_sqlite_wal_reset_vulnerable(
            sqlite_version="3.49.1",
            sqlite_version_info=(3, 49, 1),
        )

    assert warned
    assert any("3.49.1" in record.message for record in caplog.records)
    assert any("3.51.3" in record.message for record in caplog.records)


def test_a_wal_reset_javitasa_nem_ad_felesleges_figyelmeztetest(caplog):
    from picasapy.app.startup_diagnostics import warn_if_sqlite_wal_reset_vulnerable

    with caplog.at_level(logging.WARNING, logger="picasapy.startup"):
        warned = warn_if_sqlite_wal_reset_vulnerable(
            sqlite_version="3.51.3",
            sqlite_version_info=(3, 51, 3),
        )

    assert not warned
    assert not caplog.records


def test_a_windows_csomagolas_elott_naplozza_a_hasznalt_sqlite_verziot():
    repo = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load(
        (repo / ".github/workflows/package.yml").read_text(encoding="utf-8")
    )
    steps = workflow["jobs"]["windows-telepito"]["steps"]
    names = [step.get("name") for step in steps]
    sqlite_step = next(
        step for step in steps if step.get("name") == "SQLite-verzió a Windows-csomagban"
    )

    assert names.index("Set up Python 3.12") < names.index(sqlite_step["name"])
    assert names.index(sqlite_step["name"]) < names.index("PyInstaller-csomagolás")
    assert "sqlite3.sqlite_version" in sqlite_step["run"]

    smoke_step = next(
        step
        for step in steps
        if step.get("name") == "Telepítő telepítése és valós indulási füstpróba"
    )
    assert 'if "SQLite " not in log:' in smoke_step["run"]
    assert "print(log)" in smoke_step["run"]

    startup_prepare = (
        repo / "src/picasapy/app/application_startup_prepare.py"
    ).read_text(encoding="utf-8")
    assert "warn_if_sqlite_wal_reset_vulnerable()" in startup_prepare
