"""#3645: a mentés-gomb TERVE (`terv`) is háttérszálon készül.

A `BackupDialog.qml`-t a #3504 óta a kiadás-panel MENTÉS-üzemmódja váltja
(`BackupHost.qml` + `PublishPanel.qml`), de az `onMentesFuttatasKert` a
`terv()`-et továbbra is szinkron, a hívó (GUI-)szálon hívta — ugyanaz a
gyökér-bejárás (fájlonkénti `stat`, fényképezőgép-szűrőnél EXIF-olvasás),
ami a #3643-ban a mappalistát fagyasztotta. A `tervezdHattereben` a
`mentetlenMappakLekerese` mintáját követi: azonnal visszatér a lekérdezés
sorszámával, az eredmény a `tervKeszult` jelzésen érkezik.
"""

from __future__ import annotations

import threading
import time

import pytest

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre


@pytest.fixture
def gyujtemeny(tmp_path):
    gyoker = tmp_path / "kepek"
    (gyoker / "nyaralas").mkdir(parents=True)
    make_jpeg(gyoker / "nyaralas" / "a.jpg")
    make_jpeg(gyoker / "nyaralas" / "b.jpg")
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
    ctl = BackupController(db, (str(gyujtemeny),))
    ctl.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")
    return ctl


class TestNemBlokkolja:
    """[MAGAS] a terv lekérdezése nem fut a GUI-szálon."""

    def test_a_lassu_terv_alatt_a_hivas_azonnal_visszater(
        self, qt_app, vezerlo, monkeypatch
    ):
        import picasapy.app.backup_controller as modul

        azonosito = vezerlo.keszletek()[0]["id"]
        engedd = threading.Event()
        eredeti = modul.tervezd_meg

        def _lassu(*args, **kwargs):
            # egy lassú NAS / EXIF-szűrő utánzata: amíg a teszt el nem
            # engedi, a számítás áll (vészfék: 5 mp)
            engedd.wait(5.0)
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(modul, "tervezd_meg", _lassu)
        kapott: list[tuple] = []
        vezerlo.tervKeszult.connect(
            lambda keres, kid, terv, media: kapott.append((keres, kid, terv, media))
        )

        indul = time.monotonic()
        keres = vezerlo.tervezdHattereben(azonosito, None, "")
        eltelt = time.monotonic() - indul
        assert eltelt < 1.0, f"a hívás {eltelt:.1f} mp-ig blokkolt"
        assert kapott == []

        engedd.set()
        assert varj_feltetelre(qt_app, lambda: bool(kapott)), (
            "a lassú terv eredménye nem jött meg"
        )
        kesz_keres, kid, terv, media = kapott[-1]
        assert kesz_keres == keres
        assert kid == azonosito
        assert media == ""
        assert terv["darab"] == 2

    def test_az_elavult_valasz_nem_jon_meg(self, qt_app, vezerlo, monkeypatch):
        import picasapy.app.backup_controller as modul

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
        vezerlo.tervKeszult.connect(lambda keres, kid, terv, media: kapott.append(keres))

        regi = vezerlo.tervezdHattereben(azonosito, [], "")
        uj = vezerlo.tervezdHattereben(azonosito, [], "")
        assert uj != regi
        assert varj_feltetelre(qt_app, lambda: uj in kapott), (
            "az új lekérdezés eredménye nem jött meg"
        )
        elso_engedd.set()
        assert vezerlo.waitForBackgroundWorkers(20.0)
        qt_app.processEvents()
        assert kapott == [uj], "az elavult válasz is kiment"


class TestAMegszakitasTervezesKozben:
    """[MAGAS, #3645 átnézés] a Stop tervezés KÖZBEN a `terv()` maga nem
    néz a `_megszakitas`-ra, tehát enélkül a terv elkészülte UTÁN is
    elindulna a futtatás (a `futtasdMost` elején a `_megszakitas.clear()`
    a jelzést is törölné). A `szakitsdMeg()` ezért a folyamatban lévő
    tervkérést is érvényteleníti — ugyanaz a sorszám-minta, mint a
    `mentetlenMappakLekerese`-nél.

    A VALÓDI kattintásos verzió (Go → Stop → a terv elengedése → semmi
    nem másolódik) a `qml_functional/test_mentes_terv_klikk_3645.py`-ban."""

    def test_szakitasmeg_utan_a_folyamatban_levo_terv_nem_jon_meg(
        self, qt_app, vezerlo, monkeypatch
    ):
        import picasapy.app.backup_controller as modul

        azonosito = vezerlo.keszletek()[0]["id"]
        engedd = threading.Event()
        eredeti = modul.tervezd_meg

        def _lassu(*args, **kwargs):
            engedd.wait(5.0)
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(modul, "tervezd_meg", _lassu)
        kapott: list[tuple] = []
        vezerlo.tervKeszult.connect(
            lambda keres, kid, terv, media: kapott.append((keres, kid, terv, media))
        )

        vezerlo.tervezdHattereben(azonosito, None, "")
        vezerlo.szakitsdMeg()
        engedd.set()

        assert vezerlo.waitForBackgroundWorkers(5.0)
        qt_app.processEvents()
        assert kapott == [], (
            "a megszakított tervkérés válasza mégis kiment — a QML ezt "
            "továbbra is futtatásnak nézné"
        )


class TestATervezesiHiba:
    """[KÖZEPES, #3645 átnézés] tervezési hiba (kivétel, vagy közben
    törölt készlet) esetén a válasz `hiba: True`-t hordoz, nem hamis
    `{"darab": 0}`-t — enélkül a QML ezt a "nincs mit menteni" esettel
    azonosan kezelte: hamis „Backup Complete" ÉS a futtatás mégis
    elindult volna egy sikertelen terv felett."""

    def test_kivetel_eseten_hiba_flaggel_es_hibauzenettel_jon_a_valasz(
        self, qt_app, vezerlo, monkeypatch
    ):
        import picasapy.app.backup_controller as modul

        azonosito = vezerlo.keszletek()[0]["id"]

        def _hibas(*args, **kwargs):
            raise RuntimeError("teszt-hiba")

        monkeypatch.setattr(modul, "tervezd_meg", _hibas)

        hibak: list[str] = []
        vezerlo.hibatJelez.connect(hibak.append)
        kapott: list[tuple] = []
        vezerlo.tervKeszult.connect(
            lambda keres, kid, terv, media: kapott.append((keres, kid, terv, media))
        )

        vezerlo.tervezdHattereben(azonosito, None, "")
        assert varj_feltetelre(qt_app, lambda: bool(kapott))

        assert hibak, "kivétel esetén sem ment ki hibaüzenet"
        terv = kapott[-1][2]
        assert terv.get("hiba") is True
        assert terv["darab"] == 0

    def test_kozben_torolt_keszletnel_is_hiba_flaggel_jon_a_valasz(
        self, qt_app, vezerlo
    ):
        azonosito = vezerlo.keszletek()[0]["id"]
        vezerlo.torisdAKeszletet(azonosito)

        kapott: list[tuple] = []
        vezerlo.tervKeszult.connect(
            lambda keres, kid, terv, media: kapott.append((keres, kid, terv, media))
        )
        vezerlo.tervezdHattereben(azonosito, None, "")
        assert varj_feltetelre(qt_app, lambda: bool(kapott))
        terv = kapott[-1][2]
        assert terv.get("hiba") is True

# A korábbi, forrás-grep alapú `TestAFelulet` (csak azt nézte, hogy a
# `backupController.terv(` szöveg nem szerepel az `onMentesFuttatasKert`
# szakaszban) helyét a VALÓDI kattintásos felületi teszt vette át:
# `qml_functional/test_mentes_terv_klikk_3645.py` — az valós Go/Stop/Mégse
# kattintással, magyar `.qm`-mel ellenőrzi ugyanezt, plusz a Stop/Mégse
# hatását és a dupla kattintást is (#3645 átnézés).
