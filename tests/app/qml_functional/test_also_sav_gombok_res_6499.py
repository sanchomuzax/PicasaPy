"""#6499: az alsó sáv gombjai összeértek, és a zöld gomb alacsonyabb.

A tulajdonos képernyőképe szerint a főablak alsó sávjában a műveletgombok
(Feltöltés a Google Fotókba, Nyomtatás, E-mail, Exportálás, a három
megosztás-gomb, Kollázs, Film) KÖZVETLENÜL egymás mellett állnak, és a zöld
gomb alacsonyabb a többinél.

A kirajzolt képből mért okok (1280 px-es ablak, a teszt előtti állapot):

- Vízszintesen a cella és a gomb ugyanakkora (55 képpont), a margó 0
  (`TrayActionCell`, #1504). A szomszédos gombok KERETE ezért összeér: a
  bal gomb jobb kerete és a jobb gomb bal kerete egymás mellett áll, rés
  nélkül.
- Függőlegesen a zöld gomb 35 képpont magas, a szürkék 36. A felső él
  egyezik (755), az alsó tér el: a zöld 789-nél, a szürkék 790-nél zárnak.

Ez a teszt a KIRAJZOLT képpontokat méri, nem a QML-tulajdonságokat: a rést
a két keret közötti háttérszínű oszlopok számolják, a magasságot a keret
felső és alsó sora. A geometria csak arra kell, hogy a vizsgálat sávját
kijelölje.

Ha a `PICASAPY_6499_KEP` környezeti változó meg van adva, a teszt az alsó
sáv 1:1-es kivágását menti oda (a kiadáskép-előtte/utána képhez).
"""

from __future__ import annotations

import os
from collections import namedtuple
from itertools import pairwise
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from support.google_fiok import PROBA_EMAIL, PROBA_REFRESH
from support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre

import picasapy.google_photos as google_photos

ABLAK_SZELESSEG = 1280
#: A sor gombjai balról jobbra (a cella-sorban; a zöld gomb külön sor).
SOR_GOMBOK = (
    "trayPrintButton",
    "trayEmailButton",
    "trayExportButton",
    "trayOrderButton",
    "trayShareButton",
    "trayBlogButton",
    "trayCollageButton",
    "trayMovieButton",
)
ZOLD_GOMB = "trayUploadButton"
#: A feliratos gombok felirata: ezek nem lóghatnak ki, és nem vághatók le.
FELIRATOK = (
    ("trayPrintButton", "trayPrintLabel"),
    ("trayEmailButton", "trayEmailLabel"),
    ("trayExportButton", "trayExportLabel"),
    ("trayCollageButton", "trayCollageLabel"),
    ("trayUploadButton", "trayUploadLabel"),
)
#: Két szomszédos gomb között legalább ennyi háttérképpont kell (a jegy
#: kívánsága: „legalább 2 képpont háttérszín a két gomb kerete között").
MIN_RES_KEPPONT = 2
#: A zöld és a szürke gomb felső/alsó éle legfeljebb ennyit térhet el.
MAX_EL_ELTERES = 1

Doboz = namedtuple("Doboz", "x y w h")


def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _elem(window, nev: str) -> QQuickItem | None:
    elem = window.findChild(QObject, nev)
    return elem if isinstance(elem, QQuickItem) else None


def _doboz(window, nev: str) -> Doboz:
    elem = _elem(window, nev)
    assert elem is not None, f"{nev} nem található a kirajzolt fában"
    pont = elem.mapToScene(QPointF(0, 0))
    return Doboz(pont.x(), pont.y(), elem.width(), elem.height())


def _kepadat(kep: QImage) -> np.ndarray:
    rgba = kep.convertToFormat(QImage.Format.Format_RGBA8888)
    sorhossz = rgba.bytesPerLine()
    adat = np.frombuffer(rgba.constBits(), dtype=np.uint8)
    return (
        adat.reshape(rgba.height(), sorhossz)[:, : rgba.width() * 4]
        .reshape(rgba.height(), rgba.width(), 4)
        .copy()
    )


class _HamisKulcstarto:
    """A bejelentkezett állapot kell a zöld gombhoz, kulcstár nélkül."""

    def __init__(self):
        self.values = {}

    def get_password(self, service, username):
        return self.values.get((service, username))

    def set_password(self, service, username, password):
        self.values[(service, username)] = password

    def delete_password(self, service, username):
        self.values.pop((service, username), None)


def _kattints(window, item: QQuickItem, qt_app) -> None:
    pont = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont.toPoint(),
    )
    qt_app.processEvents()


def _alsosav_kirajzolva(qml_app_valodi_belyegkep, qt_app, monkeypatch, tmp_path):
    """Engedélyezett alsó sáv: kijelölt és megtartott fotók, bejelentkezve.

    Így a műveletgombok (és a zöld gomb) azt az állapotot mutatják, amit a
    tulajdonos lát, nem a letiltottat.
    """
    window, controller, _engine = qml_app_valodi_belyegkep
    konyvtar = Path(controller.watchedFolders[0])
    for i in range(3):
        make_minta_jpeg(konyvtar / f"6499-{i}.jpg", size=(96, 72), seed=i + 3)
    controller.rescan()
    assert _var(qt_app, lambda: controller.photos.rowCount() >= 3, 10.0), (
        "a próbaképek nem kerültek az indexbe"
    )

    # a bejelentkezettség kliens-hitelesítést kér (ld. test_belepett_sor_6446)
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setattr(google_photos, "keyring", _HamisKulcstarto())
    controller._on_google_photos_auth_result(PROBA_REFRESH, "", PROBA_EMAIL)
    window.setProperty("selectedIndexes", [0, 1, 2])
    window.setProperty("selectedIndex", 0)
    window.show()
    assert _var(qt_app, lambda: window.isExposed(), 10.0), "a főablak nem jelent meg"
    window.setProperty("width", ABLAK_SZELESSEG)
    for _ in range(6):
        qt_app.processEvents()

    _kattints(window, _elem(window, "trayHoldButton"), qt_app)
    assert _var(qt_app, lambda: controller.heldCount == 3, 10.0), (
        "a kijelölt képek megtartása nem fejeződött be"
    )
    assert _var(
        qt_app,
        lambda: _elem(window, ZOLD_GOMB).property("enabled") is True,
        10.0,
    ), "a zöld gomb nem lett engedélyezett (bejelentkezés + megtartott kép)"
    assert _var(
        qt_app,
        lambda: _elem(window, "trayPrintButton").property("enabled") is True,
        10.0,
    ), "a Nyomtatás gomb nem lett engedélyezett (van kijelölés)"
    for _ in range(4):
        qt_app.processEvents()
    return window


class _Kep:
    """A kirajzolt főablak képe és a sáv háttérszíne, egy képkockából."""

    def __init__(self, window):
        self.window = window
        self.kep = window.grabWindow()
        assert not self.kep.isNull(), "a főablakról nem készült képkocka"
        self.s = self.kep.width() / window.width()
        self.adat = _kepadat(self.kep)
        self.sav = _doboz(window, "trayMainBar")
        # a sáv alatti üres sor: a gombok alja alatt, a háttér tiszta
        y = int(round((self.sav.y + self.sav.h) * self.s)) - 3
        x = int(round(self.sav.x * self.s)) + 5
        self.hatter = self.adat[y, x, :3].copy()

    def px(self, x: float, y: float) -> np.ndarray:
        return self.adat[int(round(y * self.s)), int(round(x * self.s)), :3]

    def hatter_e(self, rgb) -> bool:
        return bool(np.array_equal(rgb, self.hatter))

    def keret_sorai(self, doboz: Doboz) -> tuple[int, int]:
        """A gomb keretének felső és alsó sora a KÉPEN (inkluzív).

        A kereső a gomb 6 képpontos környezetében a háttértől eltérő
        sorokat keresi; így a felirat és az ikon (a gomb közepén) nem
        téveszti meg, a keret pedig a szélén áll.
        """
        x = int(round((doboz.x + 6) * self.s))
        y0 = int(round((doboz.y - 6) * self.s))
        y1 = int(round((doboz.y + doboz.h + 6) * self.s))
        oszlop = self.adat[y0:y1, x, :3]
        nem_hatter = np.flatnonzero(np.any(oszlop != self.hatter, axis=1))
        assert nem_hatter.size, f"a keret nem látszik a képen (x={x})"
        return y0 + int(nem_hatter[0]), y0 + int(nem_hatter[-1])

    def res_keppont(self, bal: Doboz, jobb: Doboz) -> int:
        """Háttérszínű oszlopok száma a két gomb keretei között.

        A bal gomb jobb keretének oszlopa és a jobb gomb bal keretének oszlopa
        között számol; a középső sorban, ahol a gombok feliratai nem érnek
        az élig.
        """
        sor = int(round((bal.y + bal.h / 2) * self.s))
        bal_vege = int(round((bal.x + bal.w) * self.s))
        jobb_eleje = int(round(jobb.x * self.s))
        sorpx = self.adat[sor, :, :3]
        assert not self.hatter_e(sorpx[bal_vege - 1]), "a bal gomb jobb kerete nem látszik a képen"
        assert not self.hatter_e(sorpx[jobb_eleje]), "a jobb gomb bal kerete nem látszik a képen"
        x = bal_vege
        while x < jobb_eleje and self.hatter_e(sorpx[x]):
            x += 1
        return x - bal_vege


def _kepet_menti(kep: _Kep) -> None:
    """Az alsó sáv 1:1-es kivágása (a kiadáskép-előtte/utána képhez)."""
    cel = os.environ.get("PICASAPY_6499_KEP")
    if not cel:
        return
    y = int(round(kep.sav.y * kep.s))
    magassag = int(round(kep.sav.h * kep.s))
    kivagas = kep.kep.copy(0, y, kep.kep.width(), magassag)
    assert kivagas.save(cel, "PNG"), f"nem menthető a kivágás: {cel}"


def _lathato_sor_gombok(window) -> list[tuple[str, Doboz]]:
    """A látható sor-gombok bal-jobb sorrendben, a nevükkel."""
    kesz = []
    for nev in SOR_GOMBOK:
        elem = _elem(window, nev)
        if elem is not None and elem.isVisible():
            kesz.append((nev, _doboz(window, nev)))
    return sorted(kesz, key=lambda p: p[1].x)


def _elvalaszto_x(window) -> list[float]:
    return [
        item.mapToScene(QPointF(0, 0)).x()
        for item in window.findChildren(QObject)
        if isinstance(item, QQuickItem)
        and item.objectName() == "trayActionSeparatorRule"
        and item.isVisible()
    ]


@pytest.fixture
def alsosav(qml_app_valodi_belyegkep, qt_app, monkeypatch, tmp_path):
    window = _alsosav_kirajzolva(qml_app_valodi_belyegkep, qt_app, monkeypatch, tmp_path)
    kep = _Kep(window)
    _kepet_menti(kep)
    return window, kep


class TestReSKetGomb:
    def test_a_szomszedos_gombok_kerete_kozott_legalabb_2_kepponton_hatter_van(self, alsosav):
        window, kep = alsosav
        sor = _lathato_sor_gombok(window)
        elvalaszto = _elvalaszto_x(window)
        assert len(sor) >= 6, f"túl kevés látható sor-gomb: {[n for n, _ in sor]}"

        hibak = []
        for (bal_nev, bal), (jobb_nev, jobb) in pairwise(sor):
            if any(bal.x + bal.w <= x <= jobb.x for x in elvalaszto):
                # csoportelválasztó a kettő között: más csoport, nem ez a rés
                continue
            res = kep.res_keppont(bal, jobb)
            if res < MIN_RES_KEPPONT:
                hibak.append(f"{bal_nev} → {jobb_nev}: {res} px")
        assert not hibak, (
            "a szomszédos gombok között kevesebb a háttér, mint "
            f"{MIN_RES_KEPPONT} képpont (a kirajzolt képen): " + "; ".join(hibak)
        )

    def test_a_rések_egyformak_a_gombsorban(self, alsosav):
        window, kep = alsosav
        sor = _lathato_sor_gombok(window)
        elvalaszto = _elvalaszto_x(window)
        resek = []
        for (bal_nev, bal), (jobb_nev, jobb) in pairwise(sor):
            if any(bal.x + bal.w <= x <= jobb.x for x in elvalaszto):
                continue
            resek.append((f"{bal_nev} → {jobb_nev}", kep.res_keppont(bal, jobb)))
        assert resek, "nincs mért gombpár"
        egyforma = {res for _, res in resek}
        assert len(egyforma) == 1, f"a rések nem egyformák a sorban: {resek}"

    def test_a_csoportelvalasztok_megmaradnak(self, alsosav):
        window, kep = alsosav
        elvalasztok = _elvalaszto_x(window)
        assert elvalasztok, "nincs csoportelválasztó a képen (2 db várt)"
        for x in elvalasztok:
            cy = _doboz(window, "trayMainBar").y + 60
            assert not kep.hatter_e(kep.px(x + 0.5, cy)), (
                f"az elválasztó (x={x:.0f}) nem látszik a háttérből kiemelkedve"
            )


class TestZoldEsSzurkeGomb:
    def test_a_zold_es_a_szurke_gomb_keretenek_magassaga_azonos(self, alsosav):
        window, kep = alsosav
        zold = _doboz(window, ZOLD_GOMB)
        szurke = _doboz(window, "trayPrintButton")
        zold_felso, zold_also = kep.keret_sorai(zold)
        szurke_felso, szurke_also = kep.keret_sorai(szurke)
        zold_magas = zold_also - zold_felso + 1
        szurke_magas = szurke_also - szurke_felso + 1
        assert zold_magas == szurke_magas, (
            f"a zöld gomb keretének magassága {zold_magas} képpont, a "
            f"Nyomtatásé {szurke_magas} képpont (a kirajzolt képen)"
        )

    def test_a_zold_es_a_szurke_gomb_felso_es_also_ele_egy_vonalban_van(self, alsosav):
        window, kep = alsosav
        zold_felso, zold_also = kep.keret_sorai(_doboz(window, ZOLD_GOMB))
        for nev in ("trayPrintButton", "trayMovieButton"):
            felso, also = kep.keret_sorai(_doboz(window, nev))
            assert abs(zold_felso - felso) <= MAX_EL_ELTERES, (
                f"a zöld felső éle {zold_felso}, a {nev} felső éle {felso}"
            )
            assert abs(zold_also - also) <= MAX_EL_ELTERES, (
                f"a zöld alsó éle {zold_also}, a {nev} alsó éle {also}"
            )

    def test_a_sor_gombjainak_magassaga_egyforma(self, alsosav):
        window, kep = alsosav
        magassagok = {}
        for nev, doboz in _lathato_sor_gombok(window):
            felso, also = kep.keret_sorai(doboz)
            magassagok[nev] = also - felso + 1
        assert len(set(magassagok.values())) == 1, (
            f"a sor gombjainak keretmagassága eltér: {magassagok}"
        )


class TestFelirat:
    def test_a_felirat_nem_log_ki_a_gombbol_es_nem_vagodik_le(self, alsosav):
        window, _kep = alsosav
        hibak = []
        for gomb_nev, felirat_nev in FELIRATOK:
            gomb = _doboz(window, gomb_nev)
            felirat = _elem(window, felirat_nev)
            assert felirat is not None, f"{felirat_nev} nem található"
            if felirat.property("paintedWidth") > felirat.property("width") + 0.5:
                hibak.append(f"{felirat_nev}: a szöveg szélesebb a dobozánál")
            if felirat.property("paintedHeight") > felirat.property("height") + 0.5:
                hibak.append(f"{felirat_nev}: a szöveg magasabb a dobozánál")
            fp = felirat.mapToScene(QPointF(0, 0))
            if (
                fp.x() < gomb.x - 0.5
                or fp.x() + felirat.property("paintedWidth") > gomb.x + gomb.w + 0.5
            ):
                hibak.append(f"{felirat_nev}: kilóg a {gomb_nev} gombból")
        assert not hibak, "; ".join(hibak)
