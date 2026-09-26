"""#3594: a mentés vezérlője MAPPÁNKÉNT listázza a még el nem mentettet.

`backuptext2` (`biztonsagi-mentes.md` 10.3): „A Picasa most azokat a
fájlokat jeleníti meg, amelyekről korábban nem készült biztonsági
másolat." A `mentetlenMappak` ezt a nézetet adja a felületnek, a futás
(`futtasdMost`, `futtasdLemezkepbe`, `terv`) pedig a bepipált mappákra
szűkíthető.

Az átnézés (#3643) után a lekérdezés HÁTTÉRSZÁLON fut: a gyökerek
bejárása, a `stat()` és a fényképezőgép-szűrő EXIF-olvasása nagy
gyűjteménynél percekig tartana, és a GUI-szálon megfagyasztaná az ablakot
— pont ezt szüntette meg a #3009 a futásnál. Az eredmény a
`mentetlenMappakKeszek` jelzésen érkezik, és egy elavult (régebbi
kérésből jövő) válasz nem írja felül az újabbat.
"""

from __future__ import annotations

import threading
import time

import pytest

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre, wait_for_signal


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


def _sorok(vezerlo, keszlet_id: int) -> list[dict]:
    """A `mentetlenMappakLekerese` eredménye a jelzésről."""
    kapott: list[tuple] = []

    def _gyujt(keres, azonosito, sorok):
        kapott.append((keres, azonosito, sorok))

    vezerlo.mentetlenMappakKeszek.connect(_gyujt)
    try:
        keresek: list[int] = []
        wait_for_signal(
            vezerlo.mentetlenMappakKeszek,
            lambda: keresek.append(vezerlo.mentetlenMappakLekerese(keszlet_id)),
            description="a mentetlen mappák lekérdezése",
        )
    finally:
        vezerlo.mentetlenMappakKeszek.disconnect(_gyujt)
    assert kapott, "nem jött eredmény"
    keres, azonosito, sorok = kapott[-1]
    assert keres == keresek[0]
    assert azonosito == keszlet_id
    return list(sorok)


class TestAMentetlenMappak:
    def test_mappankent_a_mentetlen_fajlok(self, vezerlo, tmp_path, gyujtemeny):
        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")
        sorok = _sorok(vezerlo, vezerlo.keszletek()[0]["id"])
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

        sorok = _sorok(vezerlo, azonosito)
        assert [s["nev"] for s in sorok] == ["szulinap"]
        assert all("a.jpg" not in s["fajlok"] for s in sorok)

    def test_ismeretlen_keszletre_ures(self, vezerlo):
        assert _sorok(vezerlo, 9999) == []


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
        sorok = _sorok(vezerlo, azonosito)
        assert [s["nev"] for s in sorok] == ["szulinap"]


class TestNemBlokkolja:
    """[MAGAS] a lekérdezés nem fut a GUI-szálon."""

    def test_a_lassu_szamitas_alatt_a_hivas_azonnal_visszater(
        self, qt_app, vezerlo, tmp_path, monkeypatch
    ):
        import picasapy.app.backup_controller as modul

        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")
        azonosito = vezerlo.keszletek()[0]["id"]
        engedd = threading.Event()
        eredeti = modul.tervezd_meg

        def _lassu(*args, **kwargs):
            # egy lassú NAS / EXIF-szűrő utánzata: amíg a teszt el nem
            # engedi, a számítás áll (vészfék: 5 mp)
            engedd.wait(5.0)
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(modul, "tervezd_meg", _lassu)
        kapott: list = []
        vezerlo.mentetlenMappakKeszek.connect(
            lambda k, a, s: kapott.append(s))
        indul = time.monotonic()
        vezerlo.mentetlenMappakLekerese(azonosito)
        eltelt = time.monotonic() - indul
        assert eltelt < 1.0, f"a hívás {eltelt:.1f} mp-ig blokkolt"
        assert kapott == []

        engedd.set()
        assert varj_feltetelre(qt_app, lambda: bool(kapott)), (
            "a lassú lekérdezés eredménye nem jött meg")
        assert [s["nev"] for s in kapott[-1]] == ["nyaralas", "szulinap"]

    def test_az_elavult_valasz_nem_jon_meg(
        self, qt_app, vezerlo, tmp_path, monkeypatch
    ):
        import picasapy.app.backup_controller as modul

        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")
        azonosito = vezerlo.keszletek()[0]["id"]
        elso_engedd = threading.Event()
        hivasok: list[int] = []
        eredeti = modul.tervezd_meg

        def _elso_lassu(*args, **kwargs):
            hivasok.append(1)
            if len(hivasok) == 1:
                elso_engedd.wait(5.0)
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(modul, "tervezd_meg", _elso_lassu)
        kapott: list[int] = []
        vezerlo.mentetlenMappakKeszek.connect(
            lambda k, a, s: kapott.append(k))

        regi = vezerlo.mentetlenMappakLekerese(azonosito)
        uj = vezerlo.mentetlenMappakLekerese(azonosito)
        assert uj != regi
        assert varj_feltetelre(qt_app, lambda: uj in kapott), (
            "az új lekérdezés eredménye nem jött meg")
        elso_engedd.set()
        _vard_be(vezerlo, qt_app)
        assert kapott == [uj], "az elavult válasz is kiment"


class TestAFajlnevekKorlatja:
    """[KÖZEPES] a `fajlok` csak az első néhány nevet viszi a felületre."""

    def test_sok_fajlnal_csak_az_elso_husz_nev_megy(
        self, qt_app, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(
            "picasapy.app.backup_controller._kepek_mappaja",
            lambda: str(tmp_path / "Kepek"),
        )
        from picasapy.app.backup_controller import BackupController
        from picasapy.index import open_index, sync_tree

        gyoker = tmp_path / "sok"
        (gyoker / "tele").mkdir(parents=True)
        for i in range(25):
            make_jpeg(gyoker / "tele" / f"k{i:02d}.jpg")
        db = tmp_path / "sok.db"
        with open_index(db) as conn:
            sync_tree(conn, gyoker)
        vezerlo = BackupController(db, (str(gyoker),))
        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")

        sorok = _sorok(vezerlo, vezerlo.keszletek()[0]["id"])
        assert sorok[0]["darab"] == 25
        assert sorok[0]["fajlok"] == [f"k{i:02d}.jpg" for i in range(20)]
        _vard_be(vezerlo, qt_app)
