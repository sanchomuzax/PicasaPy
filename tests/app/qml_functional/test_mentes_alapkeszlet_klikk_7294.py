"""#7294 - a mentés-panel első megnyitása létrehozza a „My Backup Set"
készletet, és a következő megnyitások az utoljára használtat választják,
VALÓDI egérkattintással.

Az eredeti (`0x006706d0`, `docs/specs/paritas-folyamat-7290.md` 4.3): üres
készletlistánál a panel maga hoz létre egy CD/DVD típusú „My Backup Set"
készletet, és kiválasztja; létező listánál az utoljára használtat
(`LastBkSet`) választja név szerint, ha eltűnt, az elsőt.

A megnyitást a menü is a `nyisd()`-del végzi (`MainMenuBar.qml`); a készlet-
választás a `publishBackupSetMenu` legördülőn, a bezárás a Mégse gombon
VALÓDI kattintás. Az „újraindítás" új vezérlő + új gazda ugyanazon az
adatbázison: a folyamaton belüli állapot (`kivalasztott`) így nem
segíthet, a megjegyzésnek valóban tárolódnia kell.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QMetaObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.backup_host_harness import epits_ablakot
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre

_QML = Path(picasapy.app.__file__).parent / "qml"


def _elem(gyoker, nev: str):
    elem = gyoker.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(view, elem, qt_app):
    qt_app.processEvents()
    os_ = elem
    while os_ is not None:
        os_.ensurePolished()
        os_ = os_.parentItem()
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _lathato_sorok(view):
    sorok = []
    verem = [view.contentItem()]
    while verem:
        elem = verem.pop()
        cn = elem.metaObject().className()
        if elem.isVisible() and ("ItemDelegate" in cn or "MenuItem" in cn):
            sorok.append(elem)
        verem.extend(elem.childItems())
    return sorted(sorok, key=lambda e: e.mapToScene(QPointF(0, 0)).y())


def _valassz_keszletet(view, qt_app, kombo, index):
    """A legördülő lenyitása és az `index`. sor kiválasztása - VALÓDI kattintás."""
    modell = kombo.property("model")
    _kattints(view, kombo, qt_app)
    assert varj_feltetelre(
        qt_app, lambda: len(_lathato_sorok(view)) == len(modell)
    ), "a legördülő lista nem nyílt le"
    _kattints(view, _lathato_sorok(view)[index], qt_app)


@pytest.fixture
def kornyezet(qt_app, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.index import open_index, sync_tree

    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "a.jpg")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    nezetek = []
    yield db, gyoker, nezetek
    for view in nezetek:
        view.hide()


def _inditsd_az_alkalmazast(kornyezet, qt_app):
    """Új vezérlő + új gazda ugyanazon az adatbázison, a menü `nyisd()`-jével."""
    from picasapy.app.backup_controller import BackupController

    db, gyoker, nezetek = kornyezet
    vezerlo = BackupController(db, (str(gyoker),))
    view, ablak = epits_ablakot(_QML, {"backupController": vezerlo})
    nezetek.append(view)
    QMetaObject.invokeMethod(ablak, "nyisd")
    qt_app.processEvents()
    return view, ablak, vezerlo


def _kivalasztott_nev(ablak) -> str:
    """A gazda TÉNYLEGES választása (nem a legördülő felirata: a ComboBox
    -1 index mellett is az első elemre állhat, és az hamis zöldet adna)."""
    index = ablak.property("kivalasztott")
    assert index >= 0, "a gazdán nincs kiválasztott készlet"
    lista = ablak.property("keszletek")
    lista = lista.toVariant() if hasattr(lista, "toVariant") else lista
    return lista[index]["nev"]


def _varj_a_mappalistara(ablak, qt_app):
    assert varj_feltetelre(
        qt_app, lambda: ablak.property("mappakToltodnek") is False)


class TestUresAdatbazisElsoMegnyitasa:
    def test_pontosan_egy_cd_dvd_keszlet_van_es_ki_van_valasztva(
        self, kornyezet, qt_app
    ):
        _, ablak, vezerlo = _inditsd_az_alkalmazast(kornyezet, qt_app)

        keszletek = vezerlo.keszletek()
        assert [(k["nev"], k["tipus"]) for k in keszletek] == [
            ("My Backup Set", "cddvd")
        ]
        assert keszletek[0]["cel"] == vezerlo.lemezkepAlapHely()
        assert ablak.property("kivalasztott") == 0

    def test_a_legordulo_latszik_es_az_alapkeszletet_mutatja(
        self, kornyezet, qt_app
    ):
        _, ablak, _ = _inditsd_az_alkalmazast(kornyezet, qt_app)

        kombo = _elem(ablak, "publishBackupSetMenu")
        assert kombo.property("visible") is True
        assert _kivalasztott_nev(ablak) == "My Backup Set"
        assert kombo.property("currentText") == "My Backup Set"

    def test_a_cd_dvd_tipus_kimeneti_valasztoja_latszik(
        self, kornyezet, qt_app
    ):
        _, ablak, _ = _inditsd_az_alkalmazast(kornyezet, qt_app)

        assert _elem(ablak, "publishBackupOutputMode").property("visible") is True

    def test_ketszeri_megnyitas_kozott_is_egy_keszlet_marad(
        self, kornyezet, qt_app
    ):
        view, ablak, vezerlo = _inditsd_az_alkalmazast(kornyezet, qt_app)

        _kattints(view, _elem(ablak, "publishBackupCancel"), qt_app)
        assert ablak.property("nyitva") is False
        QMetaObject.invokeMethod(ablak, "nyisd")
        qt_app.processEvents()

        assert ablak.property("nyitva") is True
        assert len(vezerlo.keszletek()) == 1
        assert ablak.property("kivalasztott") == 0

    def test_ujraindulas_utan_sem_jon_letre_masodik_alapkeszlet(
        self, kornyezet, qt_app
    ):
        _inditsd_az_alkalmazast(kornyezet, qt_app)

        _, ablak, vezerlo = _inditsd_az_alkalmazast(kornyezet, qt_app)

        assert [k["nev"] for k in vezerlo.keszletek()] == ["My Backup Set"]
        assert ablak.property("kivalasztott") == 0


class TestAzUtolsoHasznaltKeszlet:
    @pytest.fixture
    def ketto(self, kornyezet, qt_app, tmp_path):
        """Két készlet; az első indítás után a nyitott gazdával."""
        from picasapy.app.backup_controller import BackupController

        db, gyoker, _ = kornyezet
        elo = BackupController(db, (str(gyoker),))
        assert elo.ujKeszlet("Alfa", str(tmp_path / "alfa"), "minden")
        assert elo.ujKeszlet("Béta", str(tmp_path / "beta"), "minden")
        return _inditsd_az_alkalmazast(kornyezet, qt_app)

    def test_megjegyzes_nelkul_az_elso_van_kivalasztva(self, ketto):
        _, ablak, _ = ketto

        assert _kivalasztott_nev(ablak) == "Alfa"

    def test_a_legordulon_valasztott_keszlet_az_ujraindulas_utan_is_az(
        self, ketto, kornyezet, qt_app
    ):
        view, ablak, _ = ketto
        _valassz_keszletet(
            view, qt_app, _elem(ablak, "publishBackupSetMenu"), 1)
        assert _kivalasztott_nev(ablak) == "Béta"

        _kattints(view, _elem(ablak, "publishBackupCancel"), qt_app)
        _, uj_ablak, vezerlo = _inditsd_az_alkalmazast(kornyezet, qt_app)

        assert _kivalasztott_nev(uj_ablak) == "Béta"
        assert _elem(uj_ablak, "publishBackupSetMenu").property(
            "currentText") == "Béta"
        assert len(vezerlo.keszletek()) == 2, "nem szabad új készletet felvenni"

    def test_a_visszavalasztott_keszlet_a_legutolso_valasztas(
        self, ketto, kornyezet, qt_app
    ):
        view, ablak, _ = ketto
        kombo = _elem(ablak, "publishBackupSetMenu")
        _valassz_keszletet(view, qt_app, kombo, 1)
        _valassz_keszletet(view, qt_app, kombo, 0)

        _, uj_ablak, _ = _inditsd_az_alkalmazast(kornyezet, qt_app)

        assert _kivalasztott_nev(uj_ablak) == "Alfa"

    def test_a_megjegyzett_keszlet_mappalistaja_toltodik(
        self, ketto, kornyezet, qt_app
    ):
        view, ablak, _ = ketto
        _valassz_keszletet(
            view, qt_app, _elem(ablak, "publishBackupSetMenu"), 1)

        _, uj_ablak, _ = _inditsd_az_alkalmazast(kornyezet, qt_app)

        _varj_a_mappalistara(uj_ablak, qt_app)
        assert uj_ablak.property("kivalasztott") == 1

    def test_az_eltunt_megjegyzett_keszletnel_az_elso_van_kivalasztva(
        self, ketto, kornyezet, qt_app
    ):
        view, ablak, vezerlo = ketto
        _valassz_keszletet(
            view, qt_app, _elem(ablak, "publishBackupSetMenu"), 1)
        beta = next(k["id"] for k in vezerlo.keszletek() if k["nev"] == "Béta")
        vezerlo.torisdAKeszletet(beta)

        _, uj_ablak, _ = _inditsd_az_alkalmazast(kornyezet, qt_app)

        assert _kivalasztott_nev(uj_ablak) == "Alfa"
