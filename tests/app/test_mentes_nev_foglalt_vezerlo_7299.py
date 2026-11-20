"""#7299 - a `keszletNevFoglalt` slot: az Új/Módosítás űrlap névellenőrzése.

Az eredeti (`0x00679570`, `docs/specs/paritas-folyamat-7298.md` 4. szakasz):
a név FOGLALT, ha egy MÁSIK készlet neve ASCII A-Z kisbetűsítve egyezik a
szöveggel; a nem ASCII betűk kis/nagybetűs alakja KÜLÖN név, és a szóközök
számítanak (a szöveget az ellenőrzés előtt nem vágjuk le). Szerkesztéskor a
szerkesztett készlet saját neve nem ütközik (a jegy 4. pontja: a saját név
kis/nagybetűs átírása is engedett, ez tudatos eltérés az eredetitől).
"""

from __future__ import annotations

import pytest


@pytest.fixture
def vezerlo(qt_app, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController

    ujabb = BackupController(tmp_path / "index.db", ())
    assert ujabb.ujKeszlet("Saját mentési készlet", "", "minden", "cddvd")
    assert ujabb.ujKeszlet("Külső", str(tmp_path / "kulso"), "minden", "lemez")
    # a TÁROLT név nem ASCII nagybetűket is tartalmaz
    assert ujabb.ujKeszlet("ÁRVÍZ", "", "minden", "cddvd")
    return ujabb


def _id(vezerlo, nev: str) -> int:
    return next(k["id"] for k in vezerlo.keszletek() if k["nev"] == nev)


class TestUjKeszlet:
    """`szerkesztettId == -1`: nincs saját rekord, minden készlet ütközhet."""

    def test_a_baitra_azonos_nev_foglalt(self, vezerlo):
        assert vezerlo.keszletNevFoglalt("Külső", -1) is True

    def test_az_ascii_kis_nagybetu_elteres_foglalt(self, vezerlo):
        assert vezerlo.keszletNevFoglalt("küLső", -1) is True
        assert vezerlo.keszletNevFoglalt("KüLső", -1) is True

    def test_a_nem_ascii_kis_nagybetu_elteres_kulon_nev(self, vezerlo):
        # `Á` / `á`: nem ASCII, a kisbetűsítés nem egyesíti
        assert vezerlo.keszletNevFoglalt("SAJÁT mentési készlet", -1) is False
        assert vezerlo.keszletNevFoglalt("saját mentési készlet", -1) is True
        assert vezerlo.keszletNevFoglalt("Saját mentési készlet", -1) is True

    def test_a_nem_ascii_betu_a_kisbetusitesnel_nem_valtozik(self, vezerlo):
        # `KÜLSŐ`: az `Ü`/`Ő` nem ASCII, ezért különbözik a `Külső`-től
        assert vezerlo.keszletNevFoglalt("KÜLSŐ", -1) is False

    def test_a_tarolt_nev_nem_ascii_nagybetuje_sem_kisbetusodik(self, vezerlo):
        # tárolt `ÁRVÍZ`: az `Á`/`Í` nem ASCII, tehát az `árvíz` más név
        assert vezerlo.keszletNevFoglalt("árvíz", -1) is False
        assert vezerlo.keszletNevFoglalt("ÁRVÍZ", -1) is True
        # a nem ASCII betűk azonosak, csak az ASCII betűk alakja tér el
        assert vezerlo.keszletNevFoglalt("ÁrVÍz", -1) is True
        # `í` az `Í`-tól különbözik: ez már más név
        assert vezerlo.keszletNevFoglalt("Árvíz", -1) is False

    def test_a_szokoz_szamit_nincs_levagas(self, vezerlo):
        assert vezerlo.keszletNevFoglalt("Külső ", -1) is False
        assert vezerlo.keszletNevFoglalt(" Külső", -1) is False

    def test_az_uj_nev_szabad(self, vezerlo):
        assert vezerlo.keszletNevFoglalt("Nyaralás", -1) is False

    def test_az_ures_nev_nem_foglalt_a_tiltast_mas_szabaly_adja(self, vezerlo):
        assert vezerlo.keszletNevFoglalt("", -1) is False

    def test_ures_listan_semmi_nem_foglalt(self, qt_app, tmp_path):
        from picasapy.app.backup_controller import BackupController

        ures = BackupController(tmp_path / "ures.db", ())

        assert ures.keszletNevFoglalt("My Backup Set", -1) is False


class TestSzerkesztes:
    def test_a_sajat_nev_valtozatlanul_nem_foglalt(self, vezerlo):
        assert vezerlo.keszletNevFoglalt("Külső", _id(vezerlo, "Külső")) is False

    def test_a_sajat_nev_kisbetus_atirasa_tudatosan_nem_foglalt(self, vezerlo):
        assert vezerlo.keszletNevFoglalt("külső", _id(vezerlo, "Külső")) is False

    def test_masik_keszlet_neve_foglalt(self, vezerlo):
        kulso = _id(vezerlo, "Külső")

        assert vezerlo.keszletNevFoglalt("Saját mentési készlet", kulso) is True
        assert vezerlo.keszletNevFoglalt("saját mentési készlet", kulso) is True

    def test_masik_keszlet_nevenek_nem_ascii_valtozata_szabad(self, vezerlo):
        kulso = _id(vezerlo, "Külső")

        assert vezerlo.keszletNevFoglalt("SAJÁT mentési készlet", kulso) is False

    def test_ismeretlen_azonosito_nem_vedi_a_nevet(self, vezerlo):
        # nincs ilyen saját rekord: a név a többi készlettel ütközik
        assert vezerlo.keszletNevFoglalt("Külső", 99999) is True


class TestNemModositAdatot:
    def test_a_lekerdezes_nem_hoz_letre_es_nem_torol_keszletet(self, vezerlo):
        elotte = vezerlo.keszletek()

        vezerlo.keszletNevFoglalt("Külső", -1)
        vezerlo.keszletNevFoglalt("Új", -1)

        assert vezerlo.keszletek() == elotte
