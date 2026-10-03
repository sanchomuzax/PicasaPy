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


def _nyers_x(photo, photo_area, toolbar) -> tuple[float, float]:
    """(a photoArea képernyő-x origója, a sáv nyers bal széle a szülő-koordinátán),
    a kirajzolt kép befoglalójának közepéből — a QML `szuloKozep − width/2` mása."""
    kep_bal, _, kep_jobb, _ = _ablak_kep_bounds(photo)
    origin = photo_area.mapToScene(QPointF(0, 0)).x()
    return origin, (kep_bal + kep_jobb) / 2 - origin - toolbar.width() / 2


def _sor_futasok(window, toolbar, qt_app, dpr: float, x: float) -> list[tuple[float, float]]:
    """A sáv x-ét beállítja, rendereli, és a vezérlőfutások (bal, jobb) élét adja."""
    toolbar.setProperty("x", x)
    _folyamat(qt_app)
    maszk = _valtozasmaszk(window, toolbar, qt_app, dpr)
    felso = toolbar.mapToScene(QPointF(0, 0)).y()
    sor = _js_round((felso + 8) * dpr)
    return [(bal / dpr, jobb / dpr) for bal, jobb in _pixelfutasok(maszk[sor])]


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

        # Rontás-kontroll: a Math.floor / Math.ceil kerekítés a sort egy képponttal
        # eltolná a Math.round-alapú elvárástól — de csak TÖRT nyers x-nél. A tört
        # rész platformfüggő (a CI-n a képközép 1 px-szel eltérhet), ezért a
        # kontroll kis pásztázással KERES olyan helyzetet, ahol a floor (törtrész
        # ≥ 0,5) illetve a ceil (0 < törtrész < 0,5) a round-tól eltér.
        window.setProperty("width", 1280)
        window.setProperty("height", 1029)
        _folyamat(qt_app)
        talalt: dict[str, float] = {}
        for dx in (0.0, 0.25, -0.25, 0.5, -0.5, 0.75, -0.75, 1.0, -1.0):
            viewer.setProperty("panX", dx)
            _folyamat(qt_app)
            _, nyers = _nyers_x(photo, photo_area, toolbar)
            tort = nyers - math.floor(nyers)
            if "floor" not in talalt and 0.5 <= tort <= 0.95:
                talalt["floor"] = dx
            if "ceil" not in talalt and 0.05 <= tort < 0.5:
                talalt["ceil"] = dx
        assert set(talalt) == {"floor", "ceil"}, (
            f"a pásztázás nem hozott létre a floor/ceil mutációhoz tört x-et: {talalt}"
        )
        for nev, dx in talalt.items():
            viewer.setProperty("panX", dx)
            _folyamat(qt_app)
            origin, nyers = _nyers_x(photo, photo_area, toolbar)
            round_x = _js_round(nyers)
            mutalt_x = math.floor(nyers) if nev == "floor" else math.ceil(nyers)
            assert mutalt_x != round_x, f"{nev}: a mutáns nem tér el a Math.round-tól ({nyers:.3f})"
            vart = _vart_vezerlok(origin + round_x)
            round_futasok = _sor_futasok(window, toolbar, qt_app, dpr, round_x)
            assert _egyezik_futasok(round_futasok, vart, 0.5), (
                f"{nev}-kontroll: a Math.round-alapú sor nem egyezik az elvárással: "
                f"{round_futasok} vs {vart}"
            )
            mutalt_futasok = _sor_futasok(window, toolbar, qt_app, dpr, mutalt_x)
            assert not _egyezik_futasok(mutalt_futasok, vart, 0.5), (
                f"{nev}-kontroll: a Math.{nev}-mutáns renderelt sora egyezik az "
                f"elvárással ({mutalt_futasok}), a pozícióőr nem fogná meg"
            )
        viewer.setProperty("panX", 0.0)
        _folyamat(qt_app)

        # Rontás-kontroll a kerekítés nélküli y-ra. A Qt a tört eltolást
        # ugyanarra a rasztersorra igazíthatja, ezért ezt a mutációt a valódi
        # QML-geometria (toolbar.y) őrzi; a képpontmaszk önmagában nem elég.
        # Olyan ablakmagasságot keresünk, ahol a nyers y törtrésze észlelhető.
        y_talalat = None
        # A #4063 óta a fit nézet egész képponton ül, ezért a tört y-t a
        # függőleges pásztázás tört eltolása adja (mint az x-kontrollnál).
        for magassag, pan_y in (
            (m, p) for m in range(1015, 1040) for p in (0.0, 0.25, 0.5, 0.75)
        ):
            window.setProperty("width", 1279)
            window.setProperty("height", magassag)
            viewer.setProperty("panY", pan_y)
            _folyamat(qt_app)
            kep_alja = _ablak_kep_bounds(photo)[3]
            skala = float(photo.property("scale"))
            nyers_y_global = kep_alja - skala * (toolbar.height() / 2 + 10)
            nyers_y_global -= toolbar.height() / 2
            area_origin_y = photo_area.mapToScene(QPointF(0, 0)).y()
            nyers_y = nyers_y_global - area_origin_y
            if abs(nyers_y - _js_round(nyers_y)) > 0.1:
                y_talalat = nyers_y
                break
        assert y_talalat is not None, "nincs olyan ablakmagasság, ahol a nyers y tört"
        viewer.setProperty("panY", 0.0)
        round_y = _js_round(y_talalat)
        toolbar.setProperty("y", round_y)
        _folyamat(qt_app)
        assert abs(float(toolbar.y()) - round_y) <= 1e-6
        toolbar.setProperty("y", y_talalat)
        _folyamat(qt_app)
        assert abs(float(toolbar.y()) - round_y) > 0.1, (
            "a geometriai y-őrnek észre kell vennie a kerekítés elhagyását"
        )
    finally:
        _zar(generator)
