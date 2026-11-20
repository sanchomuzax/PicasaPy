"""#7294 - a mentés-panel megnyitása a vezérlőben: alapkészlet és az utoljára
használt készlet megjegyzése.

Az eredeti (`0x006706d0`, `docs/specs/paritas-folyamat-7290.md` 4.3):

* üres készletlistánál a panel MAGA hoz létre egy „My Backup Set"
  (`il_BurnPanel::bksetname`) nevű, CD/DVD típusú készletet
  (`0x00670ae6-0x00670ca8`);
* van készlet: az utoljára használtat (`Preferences\\LastBkSet`) választja
  NÉV szerint (`0x00670cb3`, `0x00670d63`), és ha a név nincs a listában, a
  0. indexűt (`0x00670dd5`).

A felület a lokalizált alapnevet adja át (`qsTr("My Backup Set")` - a
meglévő, minden nyelven lefordított szöveg); a döntés itt, Pythonban él.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def vezerlo(qt_app, tmp_path, monkeypatch):
    # a lemezkép-alaphely a tmp alá - SOHA ne a fejlesztő Képek mappájába
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController

    return BackupController(tmp_path / "index.db", ())


def _uj_vezerlo(tmp_path):
    """Ugyanazon az adatbázison új vezérlő - az alkalmazás újraindulása."""
    from picasapy.app.backup_controller import BackupController

    return BackupController(tmp_path / "index.db", ())


def _id(vezerlo, nev: str) -> int:
    return next(k["id"] for k in vezerlo.keszletek() if k["nev"] == nev)


class TestUresListanalAlapkeszlet:
    def test_a_megnyitas_pontosan_egy_keszletet_hoz_letre(self, vezerlo):
        assert vezerlo.keszletek() == []

        keszlet_id = vezerlo.megnyitasiKeszlet("My Backup Set")

        keszletek = vezerlo.keszletek()
        assert [k["nev"] for k in keszletek] == ["My Backup Set"]
        assert keszletek[0]["id"] == keszlet_id

    def test_az_alapkeszlet_cd_dvd_tipusu_es_a_lemezkep_alaphelyre_mutat(
        self, vezerlo
    ):
        vezerlo.megnyitasiKeszlet("My Backup Set")

        keszlet = vezerlo.keszletek()[0]
        assert keszlet["tipus"] == "cddvd"
        assert keszlet["cel"] == vezerlo.lemezkepAlapHely()
        assert keszlet["szuro"] == "minden"

    def test_a_lokalizalt_nev_kerul_a_keszletbe(self, vezerlo):
        vezerlo.megnyitasiKeszlet("Saját mentési készlet")

        assert [k["nev"] for k in vezerlo.keszletek()] == [
            "Saját mentési készlet"
        ]

    def test_ketszeri_megnyitas_nem_hoz_letre_ujat(self, vezerlo):
        elso = vezerlo.megnyitasiKeszlet("My Backup Set")
        masodik = vezerlo.megnyitasiKeszlet("My Backup Set")

        assert len(vezerlo.keszletek()) == 1
        assert masodik == elso

    def test_a_letrehozas_jelzi_a_keszlet_valtozast(self, vezerlo):
        jelzesek = []
        vezerlo.keszletekValtoztak.connect(lambda: jelzesek.append(1))

        vezerlo.megnyitasiKeszlet("My Backup Set")

        assert jelzesek, "a felület nem tud az új készletről"

    def test_ures_alapnevnel_nincs_keszlet_es_nincs_valasztas(self, vezerlo):
        hibak = []
        vezerlo.hibatJelez.connect(hibak.append)

        assert vezerlo.megnyitasiKeszlet("") == -1

        assert vezerlo.keszletek() == []
        assert hibak, "az elutasítás néma maradt"


class TestMeglevoListanalAzUtolsoHasznalt:
    @pytest.fixture
    def harom(self, vezerlo, tmp_path):
        for nev in ("Béta", "Alfa", "Gamma"):
            assert vezerlo.ujKeszlet(nev, str(tmp_path / nev), "minden")
        return vezerlo

    def test_megjegyzes_nelkul_az_elso_a_nev_szerinti_sorrendben(self, harom):
        keszlet_id = harom.megnyitasiKeszlet("My Backup Set")

        assert keszlet_id == harom.keszletek()[0]["id"]
        assert harom.keszletek()[0]["nev"] == "Alfa"

    def test_meglevo_listanal_nem_jon_letre_alapkeszlet(self, harom):
        harom.megnyitasiKeszlet("My Backup Set")

        assert sorted(k["nev"] for k in harom.keszletek()) == [
            "Alfa", "Béta", "Gamma",
        ]

    def test_a_megjegyzett_keszletet_valasztja_nev_szerint(self, harom):
        harom.utolsoKeszletMegjegyzese(_id(harom, "Gamma"))

        assert harom.megnyitasiKeszlet("My Backup Set") == _id(harom, "Gamma")

    def test_a_megjegyzes_ujrainditas_utan_is_megmarad(self, harom, tmp_path):
        harom.utolsoKeszletMegjegyzese(_id(harom, "Béta"))

        uj = _uj_vezerlo(tmp_path)

        assert uj.megnyitasiKeszlet("My Backup Set") == _id(uj, "Béta")

    def test_az_utolso_valasztas_felulirja_a_korabbit(self, harom):
        harom.utolsoKeszletMegjegyzese(_id(harom, "Gamma"))
        harom.utolsoKeszletMegjegyzese(_id(harom, "Béta"))

        assert harom.megnyitasiKeszlet("My Backup Set") == _id(harom, "Béta")

    def test_eltunt_keszletnel_az_elso(self, harom):
        gamma = _id(harom, "Gamma")
        harom.utolsoKeszletMegjegyzese(gamma)
        harom.torisdAKeszletet(gamma)

        assert harom.megnyitasiKeszlet("My Backup Set") == _id(harom, "Alfa")

    def test_az_atnevezett_keszlet_megmarad_az_utolsonak(self, harom):
        """A név a kulcs, tehát az „Edit Set" átnevezése nem veszítheti el
        a megjegyzést: a felhasználó ugyanazt a készletet választotta."""
        gamma = _id(harom, "Gamma")
        harom.utolsoKeszletMegjegyzese(gamma)

        assert harom.modositsdAKeszletet(gamma, "Delta", "", "")

        assert harom.megnyitasiKeszlet("My Backup Set") == gamma

    def test_ismeretlen_azonositonal_nem_ir_semmit(self, harom):
        harom.utolsoKeszletMegjegyzese(_id(harom, "Gamma"))

        harom.utolsoKeszletMegjegyzese(987654)

        assert harom.megnyitasiKeszlet("My Backup Set") == _id(harom, "Gamma")
