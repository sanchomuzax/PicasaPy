"""#440: a mentés-készlet FELÜLETI hídja — az Eszközök menü mögött.

A mentés magja a 0.8.410-ben landolt (`picasapy.backup`,
`picasapy.index.backup_sets`), de felület nélkül: a menüpont helyőrző
volt. Ez a fájl a hidat méri — a készletek listáját, a
létrehozás/módosítás/törlés útját, a terv előnézetét és a futtatást.

## Két szabály, amit az eredeti mond ki

1. **A törlés megerősítést kér** — a felület dolga, de a vezérlőnek
   külön művelete van rá, hogy a párbeszéd ne „véletlenül" hívja.
2. **Az újrafuttatás csak az újat viszi** — a terv előnézete ezt
   számokban mutatja meg („Picasa is now showing the files you have not
   previously backed up").
"""

from __future__ import annotations


import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def gyujtemeny(tmp_path):
    gyoker = tmp_path / "kepek"
    (gyoker / "nyaralas").mkdir(parents=True)
    make_jpeg(gyoker / "nyaralas" / "a.jpg")
    make_jpeg(gyoker / "nyaralas" / "b.jpg")
    return gyoker


@pytest.fixture
def vezerlo(qt_app, tmp_path, gyujtemeny):
    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index, sync_tree

    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyujtemeny)
    return BackupController(db, (str(gyujtemeny),))


def _vard_be(vezerlo, qt_app) -> None:
    """#3009: a másolás HÁTTÉRSZÁLON fut — a hívás után be kell várni.

    Enélkül a próba a még el sem indult másolás eredményét nézné. A
    `processEvents` a szálak közti jelzéseket (haladás, futasKesz) is
    kézbesíti, azok nélkül a jelzés-próbák üresen maradnának."""
    assert vezerlo.waitForBackgroundWorkers(20.0), "a mentés szála nem állt le"
    qt_app.processEvents()


class TestAKeszletek:
    def test_ures_indulaskor(self, vezerlo):
        assert vezerlo.keszletek() == []

    def test_letrehozas_utan_latszik(self, vezerlo, tmp_path):
        vezerlo.ujKeszlet("Külső lemez", str(tmp_path / "cel"), "minden")
        lista = vezerlo.keszletek()
        assert [k["nev"] for k in lista] == ["Külső lemez"]
        assert lista[0]["cel"] == str(tmp_path / "cel")
        assert lista[0]["szuro"] == "minden"

    def test_a_NEVTELEN_keszlet_hibat_jelez(self, vezerlo, tmp_path, qt_app):
        hibak = []
        vezerlo.hibatJelez.connect(hibak.append)
        assert vezerlo.ujKeszlet("  ", str(tmp_path / "cel"), "minden") is False
        assert hibak, "a névtelen készlet némán elveszett"

    def test_az_UGYANOLYAN_nev_hibat_jelez(self, vezerlo, tmp_path):
        hibak = []
        vezerlo.hibatJelez.connect(hibak.append)
        vezerlo.ujKeszlet("K", str(tmp_path / "cel"), "minden")
        assert vezerlo.ujKeszlet("K", str(tmp_path / "masik"), "minden") is False
        assert hibak

    def test_modositas(self, vezerlo, tmp_path):
        vezerlo.ujKeszlet("K", str(tmp_path / "cel"), "minden")
        azonosito = vezerlo.keszletek()[0]["id"]
        vezerlo.modositsdAKeszletet(azonosito, "Új", str(tmp_path / "uj"), "kepek")
        k = vezerlo.keszletek()[0]
        assert (k["nev"], k["cel"], k["szuro"]) == ("Új", str(tmp_path / "uj"), "kepek")

    def test_torles(self, vezerlo, tmp_path):
        vezerlo.ujKeszlet("K", str(tmp_path / "cel"), "minden")
        vezerlo.torisdAKeszletet(vezerlo.keszletek()[0]["id"])
        assert vezerlo.keszletek() == []


class TestATerv:
    def test_a_terv_MEGSZAMOLJA_az_uj_fajlokat(self, vezerlo, tmp_path):
        vezerlo.ujKeszlet("K", str(tmp_path / "cel"), "minden")
        terv = vezerlo.terv(vezerlo.keszletek()[0]["id"])
        assert terv["darab"] == 2
        assert terv["bajt"] > 0
        assert terv["kihagyott"] == 0

    def test_a_MASODIK_terv_ures(self, qt_app, vezerlo, tmp_path):
        vezerlo.ujKeszlet("K", str(tmp_path / "cel"), "minden")
        azonosito = vezerlo.keszletek()[0]["id"]
        vezerlo.futtasdMost(azonosito)
        _vard_be(vezerlo, qt_app)
        terv = vezerlo.terv(azonosito)
        assert terv["darab"] == 0, "másodszorra is mentene"
        assert terv["kihagyott"] == 2


class TestAFuttatas:
    def test_a_fajlok_atkerulnek(self, qt_app, vezerlo, tmp_path):
        cel = tmp_path / "cel"
        vezerlo.ujKeszlet("K", str(cel), "minden")
        vezerlo.futtasdMost(vezerlo.keszletek()[0]["id"])
        _vard_be(vezerlo, qt_app)
        assert (cel / "nyaralas" / "a.jpg").is_file()
        assert (cel / "files.txt").is_file()

    def test_a_futas_UTAN_van_idopont(self, qt_app, vezerlo, tmp_path):
        vezerlo.ujKeszlet("K", str(tmp_path / "cel"), "minden")
        azonosito = vezerlo.keszletek()[0]["id"]
        assert vezerlo.keszletek()[0]["utolsoFutas"] == ""
        vezerlo.futtasdMost(azonosito)
        _vard_be(vezerlo, qt_app)
        assert vezerlo.keszletek()[0]["utolsoFutas"] != ""

    def test_a_JELZES_megmondja_mennyi_ment_at(self, qt_app, vezerlo, tmp_path):
        kesz = []
        vezerlo.futasKesz.connect(lambda db, bajt: kesz.append((db, bajt)))
        vezerlo.ujKeszlet("K", str(tmp_path / "cel"), "minden")
        vezerlo.futtasdMost(vezerlo.keszletek()[0]["id"])
        _vard_be(vezerlo, qt_app)
        assert kesz and kesz[0][0] == 2

    def test_ISMERETLEN_keszletre_nem_omlik_ossze(self, qt_app, vezerlo):
        hibak = []
        vezerlo.hibatJelez.connect(hibak.append)
        vezerlo.futtasdMost(9999)
        _vard_be(vezerlo, qt_app)
        assert hibak
