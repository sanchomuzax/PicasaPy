"""#3594: a mentés vezérlője MAPPÁNKÉNT listázza a még el nem mentettet.

`backuptext2` (`biztonsagi-mentes.md` 10.3): „A Picasa most azokat a
fájlokat jeleníti meg, amelyekről korábban nem készült biztonsági
másolat." A `mentetlenMappak` ezt a nézetet adja a felületnek, a futás
(`futtasdMost`, `futtasdLemezkepbe`, `terv`) pedig a bepipált mappákra
szűkíthető.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def gyujtemeny(tmp_path):
    gyoker = tmp_path / "kepek"
    for mappa in ("nyaralas", "szulinap"):
        (gyoker / mappa).mkdir(parents=True)
    make_jpeg(gyoker / "nyaralas" / "a.jpg")
    make_jpeg(gyoker / "nyaralas" / "b.jpg")
    make_jpeg(gyoker / "szulinap" / "c.jpg")
    return gyoker


@pytest.fixture
def vezerlo(qt_app, tmp_path, gyujtemeny, monkeypatch):
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index, sync_tree

    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyujtemeny)
    return BackupController(db, (str(gyujtemeny),))


def _vard_be(vezerlo, qt_app) -> None:
    assert vezerlo.waitForBackgroundWorkers(20.0), "a mentés szála nem állt le"
    qt_app.processEvents()


class TestAMentetlenMappak:
    def test_mappankent_a_mentetlen_fajlok(self, vezerlo, tmp_path, gyujtemeny):
        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")
        sorok = vezerlo.mentetlenMappak(vezerlo.keszletek()[0]["id"])
        assert [s["mappa"] for s in sorok] == [
            str(gyujtemeny / "nyaralas"), str(gyujtemeny / "szulinap")]
        assert [s["nev"] for s in sorok] == ["nyaralas", "szulinap"]
        assert sorok[0]["fajlok"] == ["a.jpg", "b.jpg"]
        assert sorok[0]["darab"] == 2
        assert sorok[0]["bajt"] > 0

    def test_a_mar_elmentett_fajl_nem_latszik(
        self, qt_app, vezerlo, tmp_path, gyujtemeny
    ):
        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")
        azonosito = vezerlo.keszletek()[0]["id"]
        vezerlo.futtasdMost(azonosito, [str(gyujtemeny / "nyaralas")])
        _vard_be(vezerlo, qt_app)

        sorok = vezerlo.mentetlenMappak(azonosito)
        assert [s["nev"] for s in sorok] == ["szulinap"]
        assert all("a.jpg" not in s["fajlok"] for s in sorok)

    def test_ismeretlen_keszletre_ures(self, vezerlo):
        assert vezerlo.mentetlenMappak(9999) == []


class TestAPipakSzukitik:
    def test_a_terv_a_pipalt_mappakra_szukul(
        self, vezerlo, tmp_path, gyujtemeny
    ):
        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")
        azonosito = vezerlo.keszletek()[0]["id"]
        assert vezerlo.terv(azonosito)["darab"] == 3
        assert vezerlo.terv(
            azonosito, [str(gyujtemeny / "szulinap")])["darab"] == 1
        assert vezerlo.terv(azonosito, [])["darab"] == 0

    def test_a_futas_csak_a_pipalt_mappat_viszi(
        self, qt_app, vezerlo, tmp_path, gyujtemeny
    ):
        cel = tmp_path / "cel"
        vezerlo.ujKeszlet("Külső", str(cel), "minden")
        vezerlo.futtasdMost(
            vezerlo.keszletek()[0]["id"], [str(gyujtemeny / "szulinap")])
        _vard_be(vezerlo, qt_app)
        assert sorted(p.name for p in cel.rglob("*.jpg")) == ["c.jpg"]

    def test_a_lemezkep_ag_is_szukul(
        self, qt_app, vezerlo, tmp_path, gyujtemeny
    ):
        vezerlo.ujKeszlet("Lemezre", "", "minden", "cddvd")
        azonosito = vezerlo.keszletek()[0]["id"]
        vezerlo.futtasdLemezkepbe(
            azonosito, "cd", [str(gyujtemeny / "nyaralas")])
        _vard_be(vezerlo, qt_app)
        # a lemezképbe került mappa elmentettnek számít, a másik nem
        sorok = vezerlo.mentetlenMappak(azonosito)
        assert [s["nev"] for s in sorok] == ["szulinap"]
