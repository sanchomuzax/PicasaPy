"""#4087 — az eszközsor abszolút, renderelt képernyő-helye."""

from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF

from tests.app.qml_functional.test_szerkeszto_sav_forgatott_kepen_4022 import (
    _ablak_kep_bounds,
    _app,
    _folyamat,
    _item,
    _kattint,
    _renderelt_rgb,
    _zar,
)


_ABLAKSZELESSEGEK = (1279, 1280, 1281, 1282, 1283)
_ABLAKMAGASSAGOK = (1019, 1029, 1039)
_VEZERLO_ELTOLASOK = ((0, 267), (278, 360), (365, 447))


def _js_round(ertek: float) -> int:
    """A pozitív QML `Math.round` egészre kerekítését adja."""
    return math.floor(ertek + 0.5)


def _pixelfutasok(maszk: np.ndarray, max_hezag: int = 2) -> list[tuple[int, int]]:
    """Renderelt vízszintes futások; a felirat körüli kis lyukakat átugorja."""
    xs = np.flatnonzero(maszk)
    if not len(xs):
        return []
    futasok = []
    kezdet = elozo = int(xs[0])
    for x in xs[1:]:
        x = int(x)
        if x > elozo + 1 + max_hezag:
            futasok.append((kezdet, elozo + 1))
            kezdet = x
        elozo = x
    futasok.append((kezdet, elozo + 1))
    return futasok


def _vart_vezerlok(sor_bal: int) -> list[tuple[int, int]]:
    return [(sor_bal + bal, sor_bal + jobb) for bal, jobb in _VEZERLO_ELTOLASOK]


def _egyezik_futasok(mert, vart, turelem: float) -> bool:
    return all(
        abs(mert_bal - vart_bal) <= turelem
        and abs(mert_jobb - vart_jobb) <= turelem
        for (mert_bal, mert_jobb), (vart_bal, vart_jobb)
        in zip(mert, vart, strict=True)
    )


def _rgb(kep) -> np.ndarray:
    """A Qt QImage fizikai képpontjait RGB-tömbbe alakítja."""
    return _renderelt_rgb(kep)


def _valtozasmaszk(window, toolbar, qt_app, dpr: float) -> np.ndarray:
    aktiv = window.grabWindow()
    assert not aktiv.isNull(), "a főablak grabWindow() képe üres"
    toolbar.setProperty("opacity", 0.0)
    _folyamat(qt_app)
    rejtett = window.grabWindow()
    toolbar.setProperty("opacity", 1.0)
    _folyamat(qt_app)
    assert not rejtett.isNull(), "az eszközsáv nélküli grabWindow() kép üres"
    aktiv_rgb = _rgb(aktiv)
    rejtett_rgb = _rgb(rejtett)
    assert aktiv.devicePixelRatio() == dpr
    return np.max(
        np.abs(aktiv_rgb.astype(np.int16) - rejtett_rgb.astype(np.int16)), axis=2
    ) > 4


def test_a_kiegyenesites_sor_abszolut_szeleit_a_kirajzolt_kep_kozepehez_meri(
    qt_app, tmp_path
):
    generator, window, viewer, panel, _controller, dpr = _app(qt_app, tmp_path)
    try:
        window.setProperty("viewerOpen", True)
        _folyamat(qt_app)
        viewer.setProperty("currentIndex", 7)
        _folyamat(qt_app)
        panel.setProperty("activeTab", 0)
        _folyamat(qt_app)
        _kattint(window, _item(window, "editToolTilt"), qt_app)

        photo_area = _item(window, "viewerPhotoArea")
        left_drawer = _item(window, "viewerLeftDrawer")
        toolbar = _item(window, "editorToolBar")
        photo = _item(window, "viewerImage")
        assert toolbar.property("visible") is True
        assert dpr > 0

        # A képterület széleit a tényleges jelenetgeometriából mérjük. A #4082
        # balfiók-változása nem része az abszolút referencia-ellenőrzésnek.
        area_left = photo_area.mapToScene(QPointF(0, 0)).x()
        area_right = photo_area.mapToScene(
            QPointF(photo_area.width(), 0)
        ).x()
        drawer_right = left_drawer.mapToScene(
            QPointF(left_drawer.width(), 0)
        ).x()
        assert abs(area_left - (drawer_right + 14)) <= 0.05
        assert abs(area_right - (window.width() - 14)) <= 0.05
        assert abs(
            photo_area.width() - (window.width() - left_drawer.width() - 28)
        ) <= 0.05

        floor_y_kulonbozne = False
        ceil_y_kulonbozne = False
        for magassag in _ABLAKMAGASSAGOK:
            for szelesseg in _ABLAKSZELESSEGEK:
                window.setProperty("width", szelesseg)
                window.setProperty("height", magassag)
                _folyamat(qt_app)
                if (
                    szelesseg == 1280
                    and abs(left_drawer.width() - 280) <= 0.05
                ):
                    assert abs(photo_area.width() - (szelesseg - 308)) <= 0.05

                valtozott = _valtozasmaszk(window, toolbar, qt_app, dpr)

                toolbar_felso = toolbar.mapToScene(QPointF(0, 0)).y()
                # A lekerekített sáv a magasság felénél éri el teljes szélességét.
                # Ez a sor 8 px-re van a tetejétől, a felirat fölött és már
                # a lekerekített sarkok teljes szélességű szakaszán.
                sor = _js_round((toolbar_felso + 8) * dpr)
                futasok_pixel = _pixelfutasok(valtozott[sor])
                assert len(futasok_pixel) == 3, (
                    f"{szelesseg}×{magassag} ablakban a szöveg nélküli sorban "
                    f"három vezérlőfutást vártunk, mért futások: {futasok_pixel}"
                )
                futasok = [(bal / dpr, jobb / dpr) for bal, jobb in futasok_pixel]

                area_origin_x = photo_area.mapToScene(QPointF(0, 0)).x()
                kep_bal, _, kep_jobb, _ = _ablak_kep_bounds(photo)
                foto_kozepe = (kep_bal + kep_jobb) / 2
                foto_kozepe_szulo = foto_kozepe - area_origin_x
                toolbar_pozicio = toolbar.mapToScene(QPointF(0, 0)).x()
                toolbar_szelesseg = float(toolbar.width())
                assert toolbar_szelesseg == 447
                # Az elvárás a kirajzolt kép forgatás utáni dobozából indul,
                # a toolbar x-étől függetlenül. A QML a szülő-koordinátán
                # kerekít, ezért az abszolút bal szélhez visszatérünk a
                # photoArea jelenetbeli kezdőpontjához.
                nyers_x = foto_kozepe_szulo - toolbar_szelesseg / 2
                vart_toolbar_x = _js_round(nyers_x)
                assert abs(float(toolbar.x()) - vart_toolbar_x) <= 1e-6, (
                    f"{szelesseg}×{magassag}: QML-szülő-x={toolbar.x():.3f}, "
                    f"kép-közép és Math.round alapján {vart_toolbar_x}; "
                    "ez a geometriai őr a képpontra igazító raszterezéstől független"
                )
                sor_bal = area_origin_x + vart_toolbar_x
                vart = _vart_vezerlok(sor_bal)
                assert _egyezik_futasok(futasok, vart, 0.5), (
                    f"{szelesseg}×{magassag} ablakban a sáv/gomb élek "
                    f"{futasok}, a kirajzolt kép közepéből számított "
                    f"elvárás {vart}; fotóközép={foto_kozepe:.2f}, "
                    f"QML-sáv-x={toolbar_pozicio:.2f}, "
                    f"nyers szülő-x={nyers_x:.2f}"
                )

                # A függőleges helyet a forgatás utáni paintedHeight-doboz
                # alsó éle adja; a szöveg helyett a csúszka belső oszlopán
                # mérünk, ahol csak a keret/kitöltés rajzolódik.
                kep_alja = _ablak_kep_bounds(photo)[3]
                skala = float(photo.property("scale"))
                y_nyers_global = kep_alja - skala * (toolbar.height() / 2 + 10)
                y_nyers_global -= toolbar.height() / 2
                area_origin_y = photo_area.mapToScene(QPointF(0, 0)).y()
                y_nyers = y_nyers_global - area_origin_y
                vart_toolbar_y = _js_round(y_nyers)
                vart_felso = area_origin_y + vart_toolbar_y
                floor_y_kulonbozne |= math.floor(y_nyers) != vart_toolbar_y
                ceil_y_kulonbozne |= math.ceil(y_nyers) != vart_toolbar_y
                assert abs(float(toolbar.y()) - vart_toolbar_y) <= 1e-6, (
                    f"{szelesseg}×{magassag}: QML-szülő-y={toolbar.y():.3f}, "
                    f"a kép alja alapján Math.round={vart_toolbar_y}; "
                    "a pixeles raszter önmagában elrejtheti a tört y-eltérést"
                )
                bal = _js_round((sor_bal + 30) * dpr)
                jobb = _js_round((sor_bal + 50) * dpr)
                vez_sor = np.any(valtozott[:, bal:jobb], axis=1)
                y_pontok = np.flatnonzero(vez_sor)
                assert len(y_pontok), "a sáv kitöltése nem látszik a rögzített oszlopban"
                mert_felso = y_pontok[0] / dpr
                assert abs(mert_felso - vart_felso) <= 0.5, (
                    f"{szelesseg}×{magassag} ablakban a renderelt felső y={mert_felso:.2f}, "
                    f"Math.round-alapú elvárás={vart_felso:.2f}; nyers y={y_nyers:.2f}"
                )

                # A job-69 referencia (1280 széles ablakon: sáv 557–823, Alkalmaz
                # 835–916, Mégse 922–1003) a kirajzolt kép közepéhez kötött, ez
                # pedig platformfüggő (a CI-n a fit-méret és a képközép 1 px-szel
                # eltér, ld. a #4036 805/800 tanulságát): ezért abszolút számot
                # NEM állítunk, az elvárás a renderelt kép saját közepéből jön.

        assert floor_y_kulonbozne, (
            "az ablakmagasság-sweep nem fogja meg a Math.floor(y) eltérést"
        )
        assert ceil_y_kulonbozne, (
            "az ablakmagasság-sweep nem fogja meg a Math.ceil(y) eltérést"
        )

        # Rontás-kontroll: 1280×1029-en a képközép-alapú x 262,5; a
        # Math.floor-mutáns ezért a teljes renderelt sort egy képponttal balra viszi.
        window.setProperty("width", 1280)
        window.setProperty("height", 1029)
        _folyamat(qt_app)
        area_origin_x = photo_area.mapToScene(QPointF(0, 0)).x()
        kep_bal, _, kep_jobb, _ = _ablak_kep_bounds(photo)
        foto_kozepe_szulo = (kep_bal + kep_jobb) / 2 - area_origin_x
        nyers_x = foto_kozepe_szulo - toolbar.width() / 2
        round_x = _js_round(nyers_x)
        floor_x = math.floor(nyers_x)
        assert round_x == 263 and floor_x == 262
        toolbar.setProperty("x", floor_x)
        _folyamat(qt_app)
        floor_maszk = _valtozasmaszk(window, toolbar, qt_app, dpr)
        floor_felso = toolbar.mapToScene(QPointF(0, 0)).y()
        floor_sor = _js_round((floor_felso + 8) * dpr)
        floor_futasok = [
            (bal / dpr, jobb / dpr)
            for bal, jobb in _pixelfutasok(floor_maszk[floor_sor])
        ]
        floor_vart = _vart_vezerlok(area_origin_x + round_x)
        assert abs(floor_futasok[0][0] - (area_origin_x + floor_x)) <= 0.5, (
            f"floor kontroll: x={toolbar.x():.2f}, globális x="
            f"{toolbar.mapToScene(QPointF(0, 0)).x():.2f}, y-sor={floor_sor}, "
            f"mért={floor_futasok}, várt x={floor_x}"
        )
        assert not _egyezik_futasok(floor_futasok, floor_vart, 0.5)

        # A kerekítés ceil-mutánsa csak félpixelestől eltérő x-nél látható.
        # A kis pásztázás csak a ceil-rontáskontrollhoz hoz létre tört
        # koordinátát; az elvárás ezúttal is a kirajzolt kép közepéből indul.
        viewer.setProperty("panX", -0.25)
        _folyamat(qt_app)
        kep_bal, _, kep_jobb, _ = _ablak_kep_bounds(photo)
        foto_kozepe_szulo = (kep_bal + kep_jobb) / 2 - area_origin_x
        ceil_nyers_x = foto_kozepe_szulo - toolbar.width() / 2
        ceil_round_x = _js_round(ceil_nyers_x)
        ceil_x = math.ceil(ceil_nyers_x)
        assert ceil_x != ceil_round_x, (
            f"a ceil-mutációhoz nem félpixelestől eltérő koordinátát kaptunk: "
            f"{ceil_nyers_x:.2f}"
        )
        # A tört x kerekítésének elhagyását a QML-geometria fogja meg akkor
        # is, ha a Qt ugyanarra a pixelre raszterezi a két változatot.
        toolbar.setProperty("x", ceil_nyers_x)
        _folyamat(qt_app)
        assert abs(float(toolbar.x()) - ceil_round_x) > 0.1
        toolbar.setProperty("x", ceil_round_x)
        _folyamat(qt_app)
        ceil_round_maszk = _valtozasmaszk(window, toolbar, qt_app, dpr)
        ceil_round_felso = toolbar.mapToScene(QPointF(0, 0)).y()
        ceil_round_sor = _js_round((ceil_round_felso + 8) * dpr)
        ceil_round_futasok = [
            (bal / dpr, jobb / dpr)
            for bal, jobb in _pixelfutasok(ceil_round_maszk[ceil_round_sor])
        ]
        assert abs(
            ceil_round_futasok[0][0] - (area_origin_x + ceil_round_x)
        ) <= 0.5
        ceil_vart = _vart_vezerlok(area_origin_x + ceil_round_x)
        toolbar.setProperty("x", ceil_x)
        _folyamat(qt_app)
        ceil_maszk = _valtozasmaszk(window, toolbar, qt_app, dpr)
        ceil_felso = toolbar.mapToScene(QPointF(0, 0)).y()
        ceil_sor = _js_round((ceil_felso + 8) * dpr)
        ceil_futasok = [
            (bal / dpr, jobb / dpr)
            for bal, jobb in _pixelfutasok(ceil_maszk[ceil_sor])
        ]
        assert abs(ceil_futasok[0][0] - (area_origin_x + ceil_x)) <= 0.5
        assert not _egyezik_futasok(ceil_futasok, ceil_vart, 0.5)

        # Rontás-kontroll a kerekítés nélküli y-ra. A Qt a tört eltolást
        # ugyanarra a rasztersorra igazíthatja, ezért ezt a mutációt a valódi
        # QML-geometria (toolbar.y) őrzi; a képpontmaszk önmagában nem elég.
        window.setProperty("width", 1279)
        window.setProperty("height", 1019)
        _folyamat(qt_app)
        kep_alja = _ablak_kep_bounds(photo)[3]
        skala = float(photo.property("scale"))
        nyers_y_global = kep_alja - skala * (toolbar.height() / 2 + 10)
        nyers_y_global -= toolbar.height() / 2
        area_origin_y = photo_area.mapToScene(QPointF(0, 0)).y()
        nyers_y = nyers_y_global - area_origin_y
        round_y = _js_round(nyers_y)
        toolbar.setProperty("y", round_y)
        _folyamat(qt_app)
        assert abs(float(toolbar.y()) - round_y) <= 1e-6
        assert abs(nyers_y - round_y) > 0.1, (
            f"a tört y mutációhoz egész koordinátát kaptunk: {nyers_y:.3f}"
        )
        toolbar.setProperty("y", nyers_y)
        _folyamat(qt_app)
        assert abs(float(toolbar.y()) - round_y) > 0.1, (
            "a geometriai y-őrnek észre kell vennie a kerekítés elhagyását"
        )
    finally:
        _zar(generator)
