"""#3593 — a készlet típusa a vezérlőben: létrehozás, módosítás, lista.

A CD/DVD-típusú készletnek az eredetiben NINCS célmappája (a „Choose…"
csak a lemez-lemez típusnál él, `newbackupset.fen`). Nálunk a lemezkép
fájlba kerül, tehát kell egy hely: üres célnál a vezérlő a honosított
`Képek/Picasa biztonsági másolat/ISO-k` mappát adja
(`il_BurnPanel::DefBkFolder` + `il_BurnPanel::ISOFolder`).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def vezerlo(qt_app, tmp_path, monkeypatch):
    # a lemezkép-alaphely a tmp alá — SOHA ne a fejlesztő Képek mappájába
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index, sync_tree

    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "a.jpg")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    return BackupController(db, (str(gyoker),))


def test_a_lista_mutatja_a_tipust(vezerlo, tmp_path):
    vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden", "lemez")

    assert vezerlo.keszletek()[0]["tipus"] == "lemez"


def test_a_regi_harom_argumentumos_hivas_lemez_lemez(vezerlo, tmp_path):
    """A meglévő hívók (és a mai párbeszéd) nem törhetnek el."""
    assert vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")

    assert vezerlo.keszletek()[0]["tipus"] == "lemez"


def test_cd_dvd_tipus_cel_nelkul_az_alaphelyre_ir(vezerlo):
    assert vezerlo.ujKeszlet("Lemezre", "", "minden", "cddvd")

    keszlet = vezerlo.keszletek()[0]
    assert keszlet["tipus"] == "cddvd"
    assert keszlet["cel"] == vezerlo.lemezkepAlapHely()
    assert Path(keszlet["cel"]).name == "ISOs"


def test_lemez_lemez_tipus_cel_nelkul_hibat_jelez(vezerlo):
    uzenetek = []
    vezerlo.hibatJelez.connect(uzenetek.append)

    assert vezerlo.ujKeszlet("Külső", "", "minden", "lemez") is False
    assert uzenetek


def test_ismeretlen_tipus_hibat_jelez(vezerlo, tmp_path):
    uzenetek = []
    vezerlo.hibatJelez.connect(uzenetek.append)

    assert vezerlo.ujKeszlet("X", str(tmp_path), "minden", "szalag") is False
    assert uzenetek
    assert vezerlo.keszletek() == []


def test_a_tipus_modosithato(vezerlo, tmp_path):
    vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden", "lemez")
    azonosito = vezerlo.keszletek()[0]["id"]

    assert vezerlo.modositsdAKeszletet(
        azonosito, "Külső", str(tmp_path / "cel"), "minden", "cddvd"
    )

    assert vezerlo.keszletek()[0]["tipus"] == "cddvd"


def test_a_regi_negy_argumentumos_modositas_a_tipust_nem_bantja(
    vezerlo, tmp_path
):
    vezerlo.ujKeszlet("Lemezre", "", "minden", "cddvd")
    azonosito = vezerlo.keszletek()[0]["id"]

    vezerlo.modositsdAKeszletet(azonosito, "Átnevezve", "", "kepek")

    keszlet = vezerlo.keszletek()[0]
    assert (keszlet["nev"], keszlet["tipus"]) == ("Átnevezve", "cddvd")


def test_cd_dvd_tipusra_valtva_az_alaphelyre_ir_nem_a_regi_mappaba(
    vezerlo, tmp_path
):
    """Az átnézés lelete: a lemez-lemez készletet CD/DVD-re váltva a felület
    az alaphelyet MUTATJA — a mentett helynek is annak kell lennie, nem a
    régi mappának (különben a lemezképek a régi mentés közé kerülnének)."""
    regi = str(tmp_path / "regi")
    vezerlo.ujKeszlet("Külső", regi, "minden", "lemez")
    azonosito = vezerlo.keszletek()[0]["id"]

    vezerlo.modositsdAKeszletet(azonosito, "Külső", regi, "minden", "cddvd")

    assert vezerlo.keszletek()[0]["cel"] == vezerlo.lemezkepAlapHely()


def test_uj_cd_dvd_keszlet_a_megadott_mappat_sem_hasznalja(vezerlo, tmp_path):
    vezerlo.ujKeszlet("Lemezre", str(tmp_path / "x"), "minden", "cddvd")

    assert vezerlo.keszletek()[0]["cel"] == vezerlo.lemezkepAlapHely()
