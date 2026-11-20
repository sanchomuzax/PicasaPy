"""#7143: a Kivágás és a Beillesztés kapui az eredeti szerint, a VALÓDI főablakon.

Az eredeti (`0x0056e1c0`, Szerkesztés-ág): nézőben és szerkesztőben a Kivágás és
a Beillesztés tiltott (`0x0056e95f-0x0056e98d`), a Beillesztés kezelő hatástalan
(`0x005fead4`); könyvtárban a Beillesztés akkor él, ha a belső lista nem üres,
a mappa eltér a forrástól (`0x0056ec92`), és a sikeres beillesztés a listát
kiüríti (`0x005feaeb-0x005feb05`). Azonos mappában nincs fájlművelet. A cél
nélküli üzenet modális Információ-ablak (`0x005791fb-0x0057921b`).

A próbák a kirajzolt menüt és a valódi billentyűeseményt használják: a Szerkesztés
menüt VALÓDI kattintással nyitjuk meg, és az ott látszó tételek állapotát,
valamint a kirajzolt Információ-ablakot olvassuk vissza, nem a forrást.

Mit őriz (a jegy „Kész, ha” és „Nem szabad” pontjai):
  * (1) nézőben a Kivágás és a Beillesztés szürke, a Ctrl+X és a Ctrl+V
    hatástalan, a Másolás él;
  * (2) azonos mappában a Beillesztés szürke, és a Ctrl+V nem készít fájlt;
  * (3) saját Másolás és sikeres beillesztés után a Beillesztés szürke, új
    Másolás után él; a Mégse megtartja a vágólapot;
  * (5) a külső (másik mappából való) fájl-vágólap beillesztése változatlanul
    működik, albumnézetben a #7142 útja él, a mappakapu nem érinti.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from support.jpeg_factory import make_jpeg
from tests.app.qml_functional._fomenu_4420_menu import _megnyit, _zarj_menuket
from tests.app.qml_functional._paste_megerosites_7112 import (
    jovahagy_a_beillesztest,
    megerosito_ablak,
    megerosito_zarva,
)
from tests.support.varakozas import var_feltetelre

from picasapy.app.fileops_controller import vagolap_fajlok
from picasapy.index import open_index, sync_tree

_KEPEK = (".jpg", ".jpeg", ".png")


def _gyerek(window, nev: str) -> QObject:
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kepek(mappa: Path) -> dict[str, bytes]:
    """A mappa képfájljai tartalommal: ebből látszik, ha bármi keletkezik/mozdul."""
    return {
        p.name: p.read_bytes()
        for p in sorted(mappa.iterdir())
        if p.suffix.lower() in _KEPEK
    }


def _engedelyezve(window, nev: str) -> bool:
    return _gyerek(window, nev).property("enabled") is True


def _kijelol(window, qt_app, sorok: list[int]) -> None:
    window.setProperty("selectedIndexes", sorok)
    window.setProperty("selectedIndex", sorok[-1] if sorok else -1)
    qt_app.processEvents()


def _beillesztes(window, qt_app) -> None:
    """A menü és a billentyű ugyanezt a főablak-függvényt hívja."""
    QMetaObject.invokeMethod(
        window, "beillesztAVagolaprol", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _vagolap(vezerlo) -> tuple[list[Path], str]:
    fajlok, muvelet = vagolap_fajlok(vezerlo._vagolap_adata())
    return [Path(f) for f in fajlok], muvelet


def _hibasav(window) -> tuple[str, bool]:
    szoveg = _gyerek(window, "errorBannerText").property("text")
    sav = _gyerek(window, "errorBanner")
    return szoveg, sav.property("visible") is True


def _info_ablak_latszik(window) -> bool:
    ablak = window.findChild(QObject, "operationInfoDialog")
    return ablak is not None and ablak.property("visible") is True


class _Kotegek:
    """Köteg-utak és megerősítések figyelője; a köteg SEMMIT nem futtat."""

    def __init__(self, vezerlo, monkeypatch):
        self.hivasok: list[tuple[str, tuple]] = []
        self.megerositesek: list[tuple] = []
        vezerlo.clipboardPasteConfirmationRequested.connect(
            lambda *args: self.megerositesek.append(args)
        )
        for nev in ("_copy_batch", "_move_batch"):
            monkeypatch.setattr(
                vezerlo, nev, lambda *a, _nev=nev, **k: self.hivasok.append((_nev, a))
            )

    @property
    def semmi(self) -> bool:
        return not self.hivasok and not self.megerositesek


@pytest.fixture
def helyzet(qml_app, qt_app, tmp_path):
    """`kepek` (a.jpg, b.jpg) a megnyitott mappa; `masik` (c.jpg) is indexelt."""
    window, controller, engine = qml_app
    vezerlo = engine.rootContext().contextProperty("fileOpsController")
    assert vezerlo is not None, "a fileOpsController nincs bekötve"
    kepek = tmp_path / "kepek"
    masik = tmp_path / "masik"
    masik.mkdir()
    make_jpeg(masik / "c.jpg", size=(64, 64))
    with open_index(controller._db_path) as conn:
        sync_tree(conn, masik)

    window.show()
    window.requestActivate()
    qt_app.processEvents()
    # az indulás már a `kepek` mappát mutatja (két kép); a `selectFolder`
    # egy gyökérmappánál a teljes fát is behozná, ezért itt nem hívjuk
    assert var_feltetelre(
        qt_app, lambda: controller.photos.rowCount() == 2
    ), "a megnyitott mappa képei nem töltődtek be"
    assert controller.viewModeName == "folder"
    assert Path(controller.currentFolder) == kepek
    _kijelol(window, qt_app, [0])
    vezerlo._vagolap_adat = None
    vezerlo.clipboardFilesChanged.emit()
    qt_app.processEvents()

    return {
        "window": window,
        # ⚠️ EGY példány, a teszt végéig tartva: a `window.property("menuBar")`
        # ideiglenes (azonnal eldobott) burka a főablak Python-burkát is
        # érvénytelenné teszi, és a következő `findChild` „already deleted”
        # hibával áll meg
        "menu_bar": window.property("menuBar"),
        "controller": controller,
        "vezerlo": vezerlo,
        "qt_app": qt_app,
        "kepek": kepek,
        "masik": masik,
        "gyoker": tmp_path,
    }


def _nezot_nyit(h) -> None:
    """Megnyitja a nézőt egy konkrét képen (a #4629 mintájára).

    A néző aktív képe (`currentIndex`) nélkül a fotóművelet célpontja üres,
    és a Kivágás azért is szürke volna, mert nincs mit kivágni, nem a néző
    miatt: a próba így a NÉZŐ tiltását méri, nem az üres célpontot."""
    _gyerek(h["window"], "photoViewer").setProperty("currentIndex", 1)
    h["window"].setProperty("viewerOpen", True)
    h["qt_app"].processEvents()


def _szerkesztes_menu(h):
    """A Szerkesztés menü VALÓDI kattintással megnyitva (kirajzolt állapot)."""
    return _megnyit(h["menu_bar"], h["qt_app"], "&Edit")


def _tetel_a_megnyitott_menuben(h, nev: str) -> QQuickItem:
    tetel = _gyerek(h["window"], nev)
    assert isinstance(tetel, QQuickItem)
    assert tetel.isVisible(), f"{nev} nem látszik a megnyitott menüben"
    return tetel


class TestNezoben:
    def test_nezoben_a_kivagas_es_a_beillesztes_szurke_a_masolas_el(self, helyzet):
        h = helyzet
        h["vezerlo"].copyFilesToClipboard([str(h["masik"] / "c.jpg")])
        assert h["vezerlo"].clipboardHasFiles is True

        # kontroll: a könyvtárban mind a három tétel él (másik mappa a forrás)
        _szerkesztes_menu(h)
        assert _engedelyezve(h["window"], "menuEditCut")
        assert _engedelyezve(h["window"], "menuEditCopy")
        assert _engedelyezve(h["window"], "menuEditPaste")
        _zarj_menuket(h["menu_bar"], h["qt_app"])

        _nezot_nyit(h)

        _szerkesztes_menu(h)
        for nev in ("menuEditCut", "menuEditCopy", "menuEditPaste"):
            _tetel_a_megnyitott_menuben(h, nev)
        assert not _engedelyezve(h["window"], "menuEditCut"), (
            "nézőben a Kivágás nem szürke"
        )
        assert not _engedelyezve(h["window"], "menuEditPaste"), (
            "nézőben a Beillesztés nem szürke"
        )
        assert _engedelyezve(h["window"], "menuEditCopy"), (
            "nézőben a Másolás nem élhet szürkén"
        )

    def test_a_ctrl_x_nezoben_nem_vag_ki_konyvtarban_igen(self, helyzet):
        h = helyzet
        h["vezerlo"].copyFilesToClipboard([str(h["masik"] / "c.jpg")])
        elotte = _vagolap(h["vezerlo"])
        h["window"].requestActivate()

        _nezot_nyit(h)
        assert _gyerek(h["window"], "shortcutCutFiles").property("enabled") is False
        QTest.keyClick(h["window"], Qt.Key.Key_X, Qt.KeyboardModifier.ControlModifier)
        h["qt_app"].processEvents()
        assert _vagolap(h["vezerlo"]) == elotte, (
            "a Ctrl+X nézőben átírta a vágólapot"
        )

        # kontroll: a könyvtárban ugyanez a billentyű kivágja a kijelölt képet
        h["window"].setProperty("viewerOpen", False)
        h["qt_app"].processEvents()
        assert _gyerek(h["window"], "shortcutCutFiles").property("enabled") is True
        QTest.keyClick(h["window"], Qt.Key.Key_X, Qt.KeyboardModifier.ControlModifier)
        h["qt_app"].processEvents()
        assert _vagolap(h["vezerlo"]) == ([h["kepek"] / "a.jpg"], "cut")

    def test_a_ctrl_v_es_a_beillesztes_fuggveny_nezoben_hatastalan(
        self, helyzet, monkeypatch
    ):
        h = helyzet
        kotegek = _Kotegek(h["vezerlo"], monkeypatch)
        h["vezerlo"].copyFilesToClipboard([str(h["masik"] / "c.jpg")])
        kepek_elotte = _kepek(h["kepek"])
        h["window"].requestActivate()
        _nezot_nyit(h)

        assert _gyerek(h["window"], "shortcutPasteFiles").property("enabled") is False
        QTest.keyClick(h["window"], Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        h["qt_app"].processEvents()
        _beillesztes(h["window"], h["qt_app"])

        assert kotegek.semmi, "nézőben a Beillesztés elindított valamit"
        assert _kepek(h["kepek"]) == kepek_elotte
        assert _hibasav(h["window"]) == ("", False)
        assert not _info_ablak_latszik(h["window"])
        assert h["vezerlo"].clipboardHasFiles is True


class TestAzonosMappa:
    @pytest.mark.parametrize("muvelet", ["copy", "cut"])
    def test_azonos_mappaban_a_beillesztes_szurke_es_a_ctrl_v_nem_keszit_fajlt(
        self, helyzet, monkeypatch, muvelet
    ):
        h = helyzet
        kotegek = _Kotegek(h["vezerlo"], monkeypatch)
        kep = h["kepek"] / "a.jpg"
        if muvelet == "copy":
            h["vezerlo"].copyFilesToClipboard([str(kep)])
        else:
            h["vezerlo"].cutFilesToClipboard([str(kep)])
        assert h["vezerlo"].clipboardHasFiles is True
        kepek_elotte = _kepek(h["kepek"])
        h["window"].requestActivate()
        h["qt_app"].processEvents()

        _szerkesztes_menu(h)
        _tetel_a_megnyitott_menuben(h, "menuEditPaste")
        assert not _engedelyezve(h["window"], "menuEditPaste"), (
            "azonos mappában a Beillesztés nem szürke"
        )
        _zarj_menuket(h["menu_bar"], h["qt_app"])

        assert _gyerek(h["window"], "shortcutPasteFiles").property("enabled") is False
        QTest.keyClick(h["window"], Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        h["qt_app"].processEvents()
        _beillesztes(h["window"], h["qt_app"])

        assert _kepek(h["kepek"]) == kepek_elotte, "azonos mappába fájl keletkezett"
        assert kotegek.semmi, "azonos mappában nincs megerősítés és nincs köteg"
        assert _hibasav(h["window"]) == ("", False)
        assert not _info_ablak_latszik(h["window"])

    def test_a_menu_a_mappavaltassal_egyutt_kovet(self, helyzet):
        h = helyzet
        h["vezerlo"].copyFilesToClipboard([str(h["kepek"] / "a.jpg")])
        assert not _engedelyezve(h["window"], "menuEditPaste")

        target = str(h["masik"])
        # A bal oldali mappasor ugyanígy törli a régi rácskijelölést,
        # mielőtt a vezérlő mappát vált. Enélkül a régi fókuszsor
        # visszaállíthatja a tesztben közvetlenül beállított mappát.
        h["window"].clearSelection()
        h["controller"].selectFolder(target)
        assert var_feltetelre(
            h["qt_app"], lambda: _engedelyezve(h["window"], "menuEditPaste")
        ), "másik mappába lépve a Beillesztés nem éledt fel"

        h["window"].clearSelection()
        h["controller"].selectFolder(str(h["kepek"]))
        assert var_feltetelre(
            h["qt_app"], lambda: not _engedelyezve(h["window"], "menuEditPaste")
        ), "a forrásmappába visszalépve a Beillesztés nem szürkült"

    def test_vegyes_vagolapnal_a_beillesztes_el_es_csak_a_masik_mappa_fajlja_kerdes(
        self, helyzet, monkeypatch
    ):
        h = helyzet
        kotegek = _Kotegek(h["vezerlo"], monkeypatch)
        h["vezerlo"].copyFilesToClipboard(
            [str(h["kepek"] / "a.jpg"), str(h["masik"] / "c.jpg")]
        )
        assert _engedelyezve(h["window"], "menuEditPaste")

        _beillesztes(h["window"], h["qt_app"])

        assert len(kotegek.megerositesek) == 1
        paths, dest, muvelet = kotegek.megerositesek[0]
        assert [Path(p) for p in paths] == [h["masik"] / "c.jpg"], (
            "a célmappában lévő fájl is felkerült a kérdésre"
        )
        assert Path(dest) == h["kepek"]
        assert muvelet == "copy"

    def test_albumnezetben_a_mappakapu_nem_tilt(self, helyzet):
        """#7142: album célnál a forrás lehet a nyitott mappában is."""
        h = helyzet
        token = h["controller"].createAlbum("Album 7143", [0])
        assert token, "a próba-album nem jött létre"
        h["controller"].showAlbum(token)
        h["qt_app"].processEvents()
        assert h["controller"].viewModeName == "album"
        h["controller"]._current_folder = str(h["kepek"])

        h["vezerlo"].copyFilesToClipboard([str(h["kepek"] / "b.jpg")])

        assert _engedelyezve(h["window"], "menuEditPaste"), (
            "albumnézetben a mappakapu tiltotta a Beillesztést"
        )
        assert _gyerek(h["window"], "shortcutPasteFiles").property("enabled") is True


class TestSikeresBeillesztesUtan:
    def _beilleszt_jovahagyassal(self, h) -> None:
        _beillesztes(h["window"], h["qt_app"])
        jovahagy_a_beillesztest(h["window"], h["qt_app"], "copy")

    def test_beillesztes_utan_szurke_uj_masolas_utan_el(self, helyzet):
        h = helyzet
        h["vezerlo"].copyFilesToClipboard([str(h["masik"] / "c.jpg")])
        assert _engedelyezve(h["window"], "menuEditPaste")

        self._beilleszt_jovahagyassal(h)

        assert var_feltetelre(
            h["qt_app"], lambda: (h["kepek"] / "c.jpg").exists()
        ), "a beillesztés nem másolta át a képet"
        assert var_feltetelre(
            h["qt_app"], lambda: not _engedelyezve(h["window"], "menuEditPaste")
        ), "a sikeres beillesztés után a Beillesztés nem szürke"
        assert h["vezerlo"].clipboardHasFiles is False
        _szerkesztes_menu(h)
        _tetel_a_megnyitott_menuben(h, "menuEditPaste")
        assert not _engedelyezve(h["window"], "menuEditPaste")
        _zarj_menuket(h["menu_bar"], h["qt_app"])

        # új Másolás: a tétel újra él
        h["vezerlo"].copyFilesToClipboard([str(h["masik"] / "c.jpg")])
        assert _engedelyezve(h["window"], "menuEditPaste"), (
            "új Másolás után a Beillesztés nem éledt fel"
        )

    def test_a_megse_megtartja_a_vagolapot(self, helyzet):
        h = helyzet
        h["vezerlo"].copyFilesToClipboard([str(h["masik"] / "c.jpg")])
        kepek_elotte = _kepek(h["kepek"])

        _beillesztes(h["window"], h["qt_app"])
        megerosito_ablak(h["window"], h["qt_app"])
        gomb = _gyerek(h["window"], "pasteConfirmCancelButton")
        kozep = gomb.mapToScene(
            QPointF(gomb.property("width") / 2, gomb.property("height") / 2)
        )
        QTest.mouseClick(
            h["window"],
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            kozep.toPoint(),
        )
        assert var_feltetelre(
            h["qt_app"], lambda: megerosito_zarva(h["window"])
        ), "a Mégse nem zárta be a kérdést"

        assert _kepek(h["kepek"]) == kepek_elotte
        assert h["vezerlo"].clipboardHasFiles is True, "a Mégse kiürítette a vágólapot"
        assert _engedelyezve(h["window"], "menuEditPaste"), (
            "a Mégse után a Beillesztés nem maradt élő"
        )
