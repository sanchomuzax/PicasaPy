"""#4022 — a szerkesztő eszközsávja forgatásnál és nagyításnál."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app


_ABLAKMAGASSAGOK = (1019, 1029, 1039)
_KEPSZINEK = {
    "00-negyzet.png": (31, 67, 103),
    "01-negyzet-90.png": (51, 87, 123),
    "02-negyzet-270.png": (71, 107, 143),
    "03-negyzet-180.png": (31, 67, 103),
    "04-fekvo.png": (111, 147, 183),
    "05-fekvo-90.png": (131, 167, 203),
    "06-fekvo-270.png": (151, 187, 223),
    "07-allo-90.png": (171, 207, 239),
}
_FORGATAS = {
    "00-negyzet.png": 0,
    "01-negyzet-90.png": 1,
    "02-negyzet-270.png": 3,
    "03-negyzet-180.png": 2,
    "04-fekvo.png": 0,
    "05-fekvo-90.png": 1,
    "06-fekvo-270.png": 3,
    "07-allo-90.png": 1,
}


def _probakepek(lib: Path) -> None:
    ini = []
    for nev, szin in _KEPSZINEK.items():
        if nev.startswith(("04-", "05-", "06-")):
            meret = (1600, 800)
        elif nev.startswith("07-"):
            meret = (800, 1600)
        else:
            meret = (600, 600)
        kep = QImage(*meret, QImage.Format.Format_RGB32)
        kep.fill(QColor(*szin))
        assert kep.save(str(lib / nev), "PNG"), f"nem írható a próbakép: {nev}"
        lepes = _FORGATAS[nev]
        if lepes:
            ini.extend((f"[{nev}]", f"rotate=rotate({lepes})"))
    (lib / ".picasa.ini").write_text("\n".join(ini), encoding="utf-8")


def _item(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a valódi főablakban"
    return elem


def _folyamat(qt_app) -> None:
    for _ in range(8):
        qt_app.processEvents()


def _kattint(window, elem, qt_app) -> None:
    assert elem.width() > 0 and elem.height() > 0, "a csempe nem látható"
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    _folyamat(qt_app)


def _ablak_kep_bounds(image_item) -> tuple[float, float, float, float]:
    """A kirajzolt képrész négy sarkát a képernyőre képezi le."""
    pw = float(image_item.property("paintedWidth"))
    ph = float(image_item.property("paintedHeight"))
    assert pw > 0 and ph > 0, "a próbakép nem rajzolódott ki"
    x0 = (float(image_item.width()) - pw) / 2
    y0 = (float(image_item.height()) - ph) / 2
    pontok = [
        image_item.mapToScene(QPointF(x, y))
        for x, y in ((x0, y0), (x0 + pw, y0), (x0, y0 + ph), (x0 + pw, y0 + ph))
    ]
    return (
        min(p.x() for p in pontok),
        min(p.y() for p in pontok),
        max(p.x() for p in pontok),
        max(p.y() for p in pontok),
    )


def _renderelt_rgb(image: QImage) -> np.ndarray:
    rgb = image.convertToFormat(QImage.Format.Format_RGB888)
    raw = np.frombuffer(
        rgb.constBits(), dtype=np.uint8, count=rgb.bytesPerLine() * rgb.height()
    )
    return raw.reshape(rgb.height(), rgb.bytesPerLine())[:, : rgb.width() * 3].reshape(
        rgb.height(), rgb.width(), 3
    ).copy()


def _szin_doboz(kep: np.ndarray, szin: tuple[int, int, int], dpr: float):
    """A próbakép képpontjainak doboza a főablak grabWindow() képén."""
    maszk = np.all(np.abs(kep.astype(np.int16) - np.asarray(szin)) <= 1, axis=2)
    ys, xs = np.nonzero(maszk)
    assert len(xs), f"a {szin} színű próbakép nem látszik a grabWindow() képen"
    return (
        xs.min() / dpr,
        ys.min() / dpr,
        (xs.max() + 1) / dpr,
        (ys.max() + 1) / dpr,
    )


def _elem_doboz(elem, dpr: float) -> tuple[float, float, float, float]:
    pontok = [
        elem.mapToScene(QPointF(x, y))
        for x, y in (
            (0, 0),
            (elem.width(), 0),
            (0, elem.height()),
            (elem.width(), elem.height()),
        )
    ]
    return (
        min(p.x() for p in pontok) / dpr,
        min(p.y() for p in pontok) / dpr,
        max(p.x() for p in pontok) / dpr,
        max(p.y() for p in pontok) / dpr,
    )


def _felirat_minta(renderelt: np.ndarray, elem, dpr: float):
    """A gomb fehér feliratának maszkja; a betűméretet nem rögzíti."""
    bal, fent, jobb, lent = _elem_doboz(elem, dpr)
    behuzas = 4 * dpr
    x0, y0 = max(0, int(np.ceil(bal * dpr + behuzas))), max(
        0, int(np.ceil(fent * dpr + behuzas))
    )
    x1 = min(renderelt.shape[1], int(np.floor(jobb * dpr - behuzas)))
    y1 = min(renderelt.shape[0], int(np.floor(lent * dpr - behuzas)))
    kivagas = renderelt[y0:y1, x0:x1].astype(np.int16)
    feher = (kivagas.min(axis=2) >= 250) & (
        kivagas.max(axis=2) - kivagas.min(axis=2) <= 16
    )
    ys, xs = np.nonzero(feher)
    assert len(xs) >= 4, f"a {elem.objectName()} felirata nem látszik a felvételen"
    bbox = (
        (x0 + int(xs.min())) / dpr,
        (y0 + int(ys.min())) / dpr,
        (x0 + int(xs.max()) + 1) / dpr,
        (y0 + int(ys.max()) + 1) / dpr,
    )
    minta = feher[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1].copy()
    return bbox, minta


def _meres(
    window,
    viewer,
    panel,
    controller,
    qt_app,
    fajlnev: str,
    dpr: float,
    *,
    skala: float = 1.0,
    feliratokat_merd: bool = True,
):
    if panel.property("tiltActive") is True:
        _kattint(window, _item(window, "tiltCancelButton"), qt_app)

    indexek = {
        Path(controller.photos.filePathAt(i)).name: i
        for i in range(controller.photos.rowCount())
    }
    assert fajlnev in indexek, f"a próbakép nincs az indexben: {fajlnev}"
    viewer.setProperty("currentIndex", indexek[fajlnev])
    _folyamat(qt_app)
    panel.setProperty("activeTab", 0)
    _folyamat(qt_app)
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    assert panel.property("tiltActive") is True, "a csempekattintás nem nyitotta meg az eszközt"

    foto = _item(window, "viewerImage")
    sav = _item(window, "editorToolBar")
    if skala != 1.0:
        foto.setProperty("scale", skala)
        _folyamat(qt_app)
    assert sav.property("visible") is True
    assert foto.property("rotation") == 90 * _FORGATAS[fajlnev]

    felvetel = window.grabWindow()
    assert not felvetel.isNull(), "a főablak grabWindow() képe üres"
    renderelt = _renderelt_rgb(felvetel)
    kep_doboz = _szin_doboz(renderelt, _KEPSZINEK[fajlnev], dpr)
    vart_doboz = _ablak_kep_bounds(foto)
    if skala == 1.0:
        assert all(abs(a - b) <= 2 for a, b in zip(kep_doboz, vart_doboz, strict=True)), (
            f"a {fajlnev} renderelt képdoboza {kep_doboz}, "
            f"a paintedWidth/Height transzformált doboza {vart_doboz}"
        )

    sav_doboz = _elem_doboz(sav, dpr)
    gombok = {
        nev: _item(window, nev)
        for nev in ("tiltApplyButton", "tiltCancelButton")
    }
    feliratok = (
        {
            nev: _felirat_minta(renderelt, gomb, dpr)
            for nev, gomb in gombok.items()
        }
        if feliratokat_merd
        else {}
    )
    painted = (
        float(foto.property("paintedWidth")),
        float(foto.property("paintedHeight")),
    )
    return {
        "sav": sav_doboz,
        "kep": kep_doboz,
        "feliratok": feliratok,
        "painted": painted,
    }


def _assert_vizszintes_es_igazit(meres, *, res: float, turelem: float = 1.5):
    sav = meres["sav"]
    kep = meres["kep"]
    sav_szel, sav_mag = sav[2] - sav[0], sav[3] - sav[1]
    assert sav_szel > sav_mag, f"a sáv függőleges: {sav_szel:.1f}×{sav_mag:.1f}"
    assert abs((kep[0] + kep[2] - sav[0] - sav[2]) / 2) <= 2, (
        f"a sáv közepe nem a kép közepe: sáv={sav}, kép={kep}"
    )
    mert_res = kep[3] - sav[3]
    assert abs(mert_res - res) <= turelem, (
        f"a sáv alja {mert_res:.1f} px-re van a képtől, várt rés={res:.1f}"
    )


def _app(qt_app, tmp_path):
    generator = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_probakepek)
    window, controller, _engine = next(generator)
    window.setProperty("viewerOpen", True)
    _folyamat(qt_app)
    viewer = _item(window, "photoViewer")
    panel = _item(window, "viewerEditorPanel")
    dpr = float(window.devicePixelRatio())
    assert dpr > 0
    return generator, window, viewer, panel, controller, dpr


def _zar(generator):
    try:
        next(generator)
    except StopIteration:
        pass


def test_a_kiegyenesites_savja_90_es_270_foknal_vizszintes_es_a_kephez_igazodik(
    qt_app, tmp_path
):
    generator, window, viewer, panel, controller, dpr = _app(qt_app, tmp_path)
    try:
        meresek_magassagonkent = {}
        for magassag in _ABLAKMAGASSAGOK:
            window.setProperty("width", 1280)
            window.setProperty("height", magassag)
            _folyamat(qt_app)
            meresek = {
                nev: _meres(
                    window, viewer, panel, controller, qt_app, nev, dpr
                )
                for nev in (
                    "00-negyzet.png",
                    "01-negyzet-90.png",
                    "02-negyzet-270.png",
                    "03-negyzet-180.png",
                    "04-fekvo.png",
                    "05-fekvo-90.png",
                    "06-fekvo-270.png",
                )
            }
            meresek_magassagonkent[magassag] = meresek

            alap = meresek["00-negyzet.png"]
            for nev, meres in meresek.items():
                _assert_vizszintes_es_igazit(meres, res=10)
                if nev in {"01-negyzet-90.png", "02-negyzet-270.png", "03-negyzet-180.png"}:
                    assert all(
                        abs(a - b) <= 2
                        for a, b in zip(alap["sav"], meres["sav"], strict=True)
                    ), f"{magassag}px-es ablakban {nev} sávja eltér a 0°-ostól"
    finally:
        _zar(generator)


def test_180_foknal_a_feliratok_allok_es_sorrendjuk_helyes(qt_app, tmp_path):
    generator, window, viewer, panel, controller, dpr = _app(qt_app, tmp_path)
    try:
        for magassag in _ABLAKMAGASSAGOK:
            window.setProperty("width", 1280)
            window.setProperty("height", magassag)
            _folyamat(qt_app)
            alap = _meres(
                window, viewer, panel, controller, qt_app, "00-negyzet.png", dpr
            )
            forgatott = _meres(
                window, viewer, panel, controller, qt_app, "03-negyzet-180.png", dpr
            )
            _assert_vizszintes_es_igazit(forgatott, res=10)

            alkalmaz = forgatott["feliratok"]["tiltApplyButton"]
            megse = forgatott["feliratok"]["tiltCancelButton"]
            alkalmaz_kozep = (alkalmaz[0][0] + alkalmaz[0][2]) / 2
            megse_kozep = (megse[0][0] + megse[0][2]) / 2
            assert alkalmaz_kozep < megse_kozep, (
                "180°-nál az Alkalmaz felirata nem a Mégse feliratától balra van"
            )

            for gomb in ("tiltApplyButton", "tiltCancelButton"):
                alap_minta = alap["feliratok"][gomb][1]
                forgatott_minta = forgatott["feliratok"][gomb][1]
                assert np.array_equal(alap_minta, forgatott_minta), (
                    f"180°-nál a {gomb} fehér képpont-mintája nem egyezik "
                    f"a 0°-os feliratéval (alak: {alap_minta.shape}/"
                    f"{forgatott_minta.shape}, eltérő pixelek: "
                    f"{np.count_nonzero(alap_minta != forgatott_minta)}, "
                    f"sáv: {alap['sav']}/{forgatott['sav']}, feliratdoboz: "
                    f"{alap['feliratok'][gomb][0]}/"
                    f"{forgatott['feliratok'][gomb][0]})"
                )
    finally:
        _zar(generator)


def test_rotate_1_es_13x_nagyitasnal_a_sav_merete_es_helye_skalaalapu(
    qt_app, tmp_path
):
    generator, window, viewer, panel, controller, dpr = _app(qt_app, tmp_path)
    try:
        for magassag in _ABLAKMAGASSAGOK:
            window.setProperty("width", 1280)
            window.setProperty("height", magassag)
            _folyamat(qt_app)
            meres = _meres(
                window,
                viewer,
                panel,
                controller,
                qt_app,
                "07-allo-90.png",
                dpr,
                skala=1.3,
                feliratokat_merd=False,
            )
            _assert_vizszintes_es_igazit(meres, res=13, turelem=1)
            sav = meres["sav"]
            meret = (sav[2] - sav[0], sav[3] - sav[1])
            assert abs(meret[0] - 441 * 1.3) <= 1, (
                f"1,3×-nál a sáv szélessége {meret[0]:.1f} px, "
                f"várt {441 * 1.3:.1f} px"
            )
            assert abs(meret[1] - 28 * 1.3) <= 1, (
                f"1,3×-nál a sáv magassága {meret[1]:.1f} px, "
                f"várt {28 * 1.3:.1f} px"
            )
    finally:
        _zar(generator)


def test_nem_forgatott_zoom_meret_es_res_megegyezik_a_regi_meressel(
    qt_app, tmp_path
):
    generator, window, viewer, panel, controller, dpr = _app(qt_app, tmp_path)
    vartak = (
        ("1,0×", 1.0, 441.0, 28.0, 10.0),
        ("1,29×", 1.293, 570.5, 36.2, 12.9),
        ("1,99×", 1.985, 875.5, 55.6, 19.9),
    )
    try:
        window.setProperty("width", 1280)
        window.setProperty("height", 1600)
        _folyamat(qt_app)
        for cimke, skala, vart_szel, vart_mag, vart_res in vartak:
            meres = _meres(
                window,
                viewer,
                panel,
                controller,
                qt_app,
                "04-fekvo.png",
                dpr,
                skala=skala,
                feliratokat_merd=False,
            )
            sav = meres["sav"]
            mert_szel = sav[2] - sav[0]
            mert_mag = sav[3] - sav[1]
            mert_res = meres["kep"][3] - sav[3]
            assert abs(mert_szel - vart_szel) <= 1, (
                f"{cimke}-nál a sáv szélessége {mert_szel:.1f} px, "
                f"régi mérés={vart_szel:.1f} px"
            )
            assert abs(mert_mag - vart_mag) <= 1, (
                f"{cimke}-nál a sáv magassága {mert_mag:.1f} px, "
                f"régi mérés={vart_mag:.1f} px"
            )
            # a kép alját képpontból mérjük (csak a teljesen fedett sort
            # számoljuk), ezért a rés 1 px-nél kevesebbel kisebbnek mérődik
            assert abs(mert_res - vart_res) <= 1.5, (
                f"{cimke}-nál a rés {mert_res:.1f} px, "
                f"régi mérés={vart_res:.1f} px"
            )
    finally:
        _zar(generator)


def test_csempekattintassal_nyilik_meg_a_forgatott_kiegyenesites(qt_app, tmp_path):
    generator, window, viewer, panel, controller, dpr = _app(qt_app, tmp_path)
    try:
        for magassag in _ABLAKMAGASSAGOK:
            window.setProperty("width", 1280)
            window.setProperty("height", magassag)
            _folyamat(qt_app)
            meres = _meres(
                window,
                viewer,
                panel,
                controller,
                qt_app,
                "01-negyzet-90.png",
                dpr,
            )
            _assert_vizszintes_es_igazit(meres, res=10)
            assert abs((meres["sav"][2] - meres["sav"][0]) - 441) <= 1
            assert abs((meres["sav"][3] - meres["sav"][1]) - 28) <= 1
    finally:
        _zar(generator)
