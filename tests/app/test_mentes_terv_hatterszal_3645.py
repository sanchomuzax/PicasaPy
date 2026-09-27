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
from pathlib import Path

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


class TestAFelulet:
    """Forrás-szintű állítás: a gomb NEM hívhatja szinkron a `terv`-et."""

    def test_a_gomb_a_hatterszalas_tervet_hivja(self):
        gazda = (
            Path(__file__).parents[2]
            / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "BackupHost.qml"
        ).read_text(encoding="utf-8")
        szakasz = gazda[gazda.index("onMentesFuttatasKert"):]
        szakasz = szakasz[: szakasz.index("function fogadjATervet")]
        assert "backupController.terv(" not in szakasz, (
            "a szinkron terv() a GUI-szálon fagyasztaná az ablakot"
        )
        assert "tervezdHattereben" in szakasz
        assert "Calculating" in szakasz, "nincs busy-állapot a hivatalos felirattal"
        assert "function onTervKeszult(" in gazda
        assert "function fogadjATervet(" in gazda
