"""A differenciális összevetés véletlenállapot-függő láncai."""

import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import differencialis_lanc_osszevet as osszevet  # noqa: E402


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        ("bw=1;GrAiN2=1;", "igen"),
        ("TRIPLE3=1,0.2;", "igen"),
        ("GrAiN=1;", "igen"),
        ("PicnikGrain=1,2;", "nem"),
        ("grain2extra=1;bw=1;", "nem"),
        ("tint=1,grain2;", "nem"),
    ],
)
def test_lanc_besorolasa_hianyzo_kimenetnel_is(tmp_path, filters, expected):
    record = {"azonosito": "a", "koteg": "k", "kep": "a.jpg", "filters": filters}
    row = osszevet.compare_record(record, tmp_path, tmp_path)
    assert row["veletlenfuggo"] == expected
    assert row["egyezes"] == "hiányzik"


def test_csv_es_osszesites_kulon_szamolja_a_merheto_lancokat(tmp_path, monkeypatch):
    records = [
        {"azonosito": str(i), "koteg": "k", "kep": "a.jpg", "filters": chain}
        for i, chain in enumerate(("grain2=1;", "triple3=1;", "bw=1;", "warm=1;", "grain=1;"))
    ]
    (tmp_path / "lancok.json").write_text(json.dumps(records), encoding="utf-8")
    outcomes = iter(("egyezik", "eltér", "egyezik", "hiányzik", "helyi hiba"))
    original = osszevet.compare_record

    def measured(record, own, reference):
        row = original(record, own, reference)
        row["egyezes"] = next(outcomes)
        return row

    monkeypatch.setattr(osszevet, "compare_record", measured)
    rows = osszevet.compare_all(tmp_path, tmp_path)
    with (tmp_path / "eredmeny.csv").open(encoding="utf-8", newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    assert [row["veletlenfuggo"] for row in csv_rows] == ["igen", "igen", "nem", "nem", "igen"]
    assert [row["egyezes"] for row in rows] == ["egyezik", "eltér", "egyezik", "hiányzik", "helyi hiba"]
    report = (tmp_path / "eredmeny.md").read_text(encoding="utf-8")
    assert "Véletlenállapot-függő: 3 | Egyezik: 1 | Eltér: 1" in report
    assert "Véletlenállapot-függők nélkül: 1/1 (100,0%)" in report


def test_ures_nevezo_nem_ad_felrevezeto_aranyt(tmp_path):
    record = {"azonosito": "a", "koteg": "k", "kep": "a.jpg", "filters": "grain2=1;"}
    (tmp_path / "lancok.json").write_text(json.dumps([record]), encoding="utf-8")
    osszevet.compare_all(tmp_path, tmp_path)
    report = (tmp_path / "eredmeny.md").read_text(encoding="utf-8")
    assert "Véletlenállapot-függők nélkül: nincs értékelhető mérés" in report


def test_markdown_tablazat_soronkent_jeloli_a_veletlenfuggeset(tmp_path):
    records = [
        {"azonosito": "a", "koteg": "k", "kep": "a.jpg", "filters": "grain2=1;"},
        {"azonosito": "b", "koteg": "k", "kep": "b.jpg", "filters": "bw=1;"},
    ]
    (tmp_path / "lancok.json").write_text(json.dumps(records), encoding="utf-8")
    osszevet.compare_all(tmp_path, tmp_path)
    report = (tmp_path / "eredmeny.md").read_text(encoding="utf-8")
    assert "| Véletlenállapot-függő |" in report
    assert "`grain2=1;` | igen |" in report
    assert "`bw=1;` | nem |" in report
