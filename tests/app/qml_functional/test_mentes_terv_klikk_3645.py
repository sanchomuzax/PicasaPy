"""#3645 átnézés — a mentés-gomb terve VALÓDI kattintással.

A `test_mentes_terv_hatterszal_3645.py` a `tervezdHattereben`-t közvetlenül,
a vezérlőn hívva ellenőrizte. Ez a fájl a TELJES láncot méri, a felhasználó
szemével: a „Burn Disc" gombtól (`publishBackupGo`) a Stop/Mégse hatásáig,
magyar `.qm`-mel — a korábbi, forrás-grep alapú `TestAFelulet`
(`test_mentes_terv_hatterszal_3645.py`) helyett, ami csak a forrásszöveget
nézte, nem a tényleges felületi viselkedést.

Három lelet:

1. [MAGAS] a Stop a TERVEZÉS alatt korábban semmit nem állított meg: a
   terv elkészülte után a `fogadjATervet` úgyis elindította a futtatást
   (`futtasdMost`), aminek elején a `_megszakitas.clear()` a Stop
   jelzését is törölte.
2. [KÖZEPES] a panel bezárása (Mégse) tervezés közben ugyanígy elindított
   egy láthatatlan futtatást.
3. [KÖZEPES] a Go gomb kattintása azonnal visszatér (a terv HÁTTÉRSZÁLON
   készül), a gomb a tervezés alatt le van tiltva — dupla kattintásra
   ezért csak EGY tervezés indul.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QCoreApplication, QMetaObject, QPoint, Qt, QTranslator
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.backup_host_harness import epits_ablakot
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre, wait_for_signal

_QML = Path(picasapy.app.__file__).parent / "qml"
_I18N = _QML.parent / "i18n"


def _elem(gyoker, nev: str):
    elem = gyoker.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(view, elem, qt_app):
    """Valódi kattintás a vezérlő KÖZEPÉRE (`test_mentes_tipus_ui_3593.py`
    mintája): előbb kikényszeríti az elrendezést az elem ősein, különben
    offscreen a vezérlő a RÉGI helyén állna."""
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


def _lassu_tervezes(monkeypatch, engedd: threading.Event) -> list[int]:
    """A `tervezd_meg`-et lecseréli egy olyanra, ami az `engedd` esemény
    beállításáig áll (egy lassú NAS/EXIF-bejárás utánzata). Visszaadja a
    hívások számlálóját, hogy a dupla kattintás tesztje ellenőrizhesse:
    valóban csak EGY tervezés indult."""
    import picasapy.app.backup_controller as modul

    eredeti = modul.tervezd_meg
    hivasok: list[int] = []

    def _lassu(*args, **kwargs):
        hivasok.append(1)
        engedd.wait(5.0)
        return eredeti(*args, **kwargs)

    monkeypatch.setattr(modul, "tervezd_meg", _lassu)
    return hivasok


@pytest.fixture
def gazda(qt_app, tmp_path, monkeypatch):
    # a hivatalos magyar feliratokkal mérünk (`il_BurnPanel::calculating`)
    fordito = QTranslator()
    assert fordito.load("picasapy_hu", str(_I18N))
    QCoreApplication.installTranslator(fordito)

    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index, sync_tree

    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "a.jpg")
    make_jpeg(gyoker / "b.jpg")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    cel = tmp_path / "cel"
    vezerlo = BackupController(db, (str(gyoker),))
    vezerlo.ujKeszlet("Külső", str(cel), "minden")
    view, ablak = epits_ablakot(_QML, {"backupController": vezerlo})
    QMetaObject.invokeMethod(ablak, "nyisd")
    ablak.setProperty("kivalasztott", 0)
    qt_app.processEvents()
    # #3594: a mappalista háttérszálon készül — a "Select All" csak
    # akkor pipál, ha már megvan
    assert varj_feltetelre(
        qt_app, lambda: ablak.property("mappakToltodnek") is False)
    qt_app.processEvents()
    _kattints(view, _elem(ablak, "publishBackupSelectAll"), qt_app)

    yield view, ablak, vezerlo, cel

    view.hide()
    QCoreApplication.removeTranslator(fordito)


class TestAMegszakitasValodiKattintassal:
    """[MAGAS] a Stop a tervezés ALATT is hat — nem indul másolás."""

    def test_stop_a_tervezes_alatt_nem_masol(self, gazda, qt_app, monkeypatch):
        view, ablak, vezerlo, cel = gazda
        engedd = threading.Event()
        _lassu_tervezes(monkeypatch, engedd)

        _kattints(view, _elem(ablak, "publishBackupGo"), qt_app)
        assert ablak.property("fut") is True
        assert ablak.property("uzenet") == "Számítás…"

        _kattints(view, _elem(ablak, "publishBackupStop"), qt_app)
        assert ablak.property("fut") is False, (
            "a Stop tervezés közben nem állította vissza a fut állapotot"
        )
        assert ablak.property("uzenet") == ""

        # a lassú terv csak MOST készül el — a megszakítás után érkező
        # válasz nem indíthat futtatást
        engedd.set()
        assert vezerlo.waitForBackgroundWorkers(5.0), (
            "a háttérszál nem állt le időben"
        )
        qt_app.processEvents()
        qt_app.processEvents()

        assert list(cel.rglob("*.jpg")) == [], (
            "a Stop utáni, megszakított terv mégis elindította a másolást"
        )
        assert ablak.property("fut") is False


class TestAMegseValodiKattintassal:
    """[KÖZEPES] a panel bezárása (Mégse) a tervezés alatt is
    érvényteleníti a folyamatban lévő tervkérést."""

    def test_megse_a_tervezes_alatt_nem_masol(self, gazda, qt_app, monkeypatch):
        view, ablak, vezerlo, cel = gazda
        engedd = threading.Event()
        _lassu_tervezes(monkeypatch, engedd)

        _kattints(view, _elem(ablak, "publishBackupGo"), qt_app)
        assert ablak.property("fut") is True

        _kattints(view, _elem(ablak, "publishBackupCancel"), qt_app)
        assert ablak.property("nyitva") is False
        assert ablak.property("fut") is False

        engedd.set()
        assert vezerlo.waitForBackgroundWorkers(5.0)
        qt_app.processEvents()
        qt_app.processEvents()

        assert list(cel.rglob("*.jpg")) == [], (
            "a bezárt panel mögött mégis elindult a másolás"
        )


class TestDuplaKattintas:
    """[KÖZEPES] a Go gomb kattintása 1 mp alatt visszatér, a tervezés
    alatt le van tiltva, és dupla kattintásra csak EGY tervezés indul."""

    def test_a_gomb_egy_masodperc_alatt_visszater_es_letiltodik(
        self, gazda, qt_app, monkeypatch
    ):
        view, ablak, vezerlo, cel = gazda
        engedd = threading.Event()
        hivasok = _lassu_tervezes(monkeypatch, engedd)

        gomb = _elem(ablak, "publishBackupGo")
        indul = time.monotonic()
        _kattints(view, gomb, qt_app)
        eltelt = time.monotonic() - indul
        assert eltelt < 1.0, f"a kattintás {eltelt:.1f} mp-ig blokkolta a felületet"

        assert ablak.property("uzenet") == "Számítás…"
        assert gomb.property("enabled") is False, (
            "a Go gomb a tervezés alatt is kattintható maradt"
        )

        # dupla kattintás: a gomb már le van tiltva, tehát a második
        # kattintás nem indíthat újabb tervezést
        _kattints(view, gomb, qt_app)

        # a tervezés HÁTTÉRSZÁLON indul — az első bejegyzés (a lassú
        # `tervezd_meg` hívása) néhány ezredmásodpercet késhet a klikk
        # után. Bevárjuk, majd rövid pihenőt adunk: ha a dupla kattintás
        # MÉGIS második tervezést indítana, annak is legyen ideje
        # bejegyezni magát, mielőtt véglegesen ellenőrzünk.
        assert varj_feltetelre(qt_app, lambda: len(hivasok) >= 1), (
            "az (első) tervezés nem indult el időben"
        )
        time.sleep(0.2)
        qt_app.processEvents()
        assert len(hivasok) == 1, (
            f"{len(hivasok)} tervezés indult egyetlen (dupla) kattintásra"
        )

        wait_for_signal(
            vezerlo.futasKesz,
            lambda: engedd.set(),
            description="a mentés befejezése",
            process_events_with=qt_app,
        )

        assert sorted(p.name for p in cel.rglob("*.jpg")) == ["a.jpg", "b.jpg"]

        # #3767 MÉRVE: a bukás NEM egyetlen képkockás kötés-késés (ahogy a
        # jegy feltételezte) — a `futasKesz` előtt kiadott
        # `keszletekValtoztak` jelzés a mentés UTÁN újra lekérdezi a
        # mentetlen mappákat (`mentetlenMappakLekerese`, külön
        # háttérszálon). Mivel MINDKÉT fájl elment, a válasz üres listát
        # ad, ez pedig kipipálatlanítja az addig bejelölt mappát
        # (`fogadjAMappakat`) — a Go gomb emiatt HELYESEN tiltódik le,
        # nincs több menteni való. A régi assert csak addig volt zöld, amíg
        # ez a második háttérlekérdezés még nem futott le; a BEÁLLT állapot
        # mindig `enabled=False`. Ezért a valódi feltételre várunk.
        assert varj_feltetelre(qt_app, lambda: gomb.property("enabled") is False), (
            "a Go gomb nem tiltódott le a mentés utáni mappalista-"
            "frissítésre, holott nincs több mentetlen mappa"
        )
        assert varj_feltetelre(
            qt_app, lambda: ablak.property("mappakToltodnek") is False
        ), "a mentés utáni mappalista-frissítés nem ért véget"
        assert ablak.property("fut") is False, (
            "a gomb a beragadt futás miatt tiltott"
        )
        assert ablak.property("pipaltMappak").property("length").toInt() == 0
