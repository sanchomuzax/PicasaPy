"""#6103: a toolbar komponensei kezelhetők, a kirajzolt állapot változatlan."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import sys
import time

import pytest
from PySide6.QtCore import (
    Q_ARG,
    QEventLoop,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QRect,
    Qt,
)
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest
from tests.support.qml_blokk import blokk_horgonyra
from support.render_test_helpers import is_text_item

_KOMPONENS = "ToolbarFilterControls"
_ALLAPOTOK = ("default", "selection", "filter", "narrow")
_MAGASSAG_ELTERESEK = (-5, 0, 5)
_KEPEK = tuple(
    (allapot, elteres)
    for allapot in _ALLAPOTOK
    for elteres in _MAGASSAG_ELTERESEK
)


@pytest.fixture
def qml_app(qt_app, tmp_path, request, rogzitett_betu):
    """A dátummezők és fájl-időbélyegek minden futásban azonosak legyenek."""
    from tests.app.qml_functional.conftest import _build_qml_app
    from support.jpeg_factory import make_jpeg

    def _kepeket_keszit(konyvtar: Path) -> None:
        rogzitett_datum = "2020:01:01 12:00:00"
        rogzitett_mtime_ns = 1_577_880_000_000_000_000
        for nev, meret in (("a.jpg", (320, 160)), ("b.jpg", (100, 100))):
            kep = make_jpeg(
                konyvtar / nev,
                size=meret,
                taken_at=rogzitett_datum,
                datetime_0th=rogzitett_datum,
            )
            os.utime(kep, ns=(rogzitett_mtime_ns, rogzitett_mtime_ns))

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_kepeket_keszit,
        keep_modul=request.module,
    )


def _qml_mappa() -> Path:
    import picasapy.app

    return Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"


def _toolbar_kep(window, toolbar) -> QImage:
    teljes_kep = window.grabWindow()
    if teljes_kep.isNull():
        return QImage()
    dpr = teljes_kep.devicePixelRatio()
    eredet = toolbar.mapToScene(QPointF(0, 0))
    teglalap = QRect(
        round(eredet.x() * dpr),
        round(eredet.y() * dpr),
        round(toolbar.width() * dpr),
        round(toolbar.height() * dpr),
    )
    return teljes_kep.copy(teglalap).convertToFormat(QImage.Format.Format_ARGB32)


def _futo_slider_animacio(slider) -> bool:
    return any(
        "Animation" in objektum.metaObject().className()
        and objektum.property("running") is True
        for objektum in slider.findChildren(QObject)
    )


def _varj_feltetelre_hataridovel(qt_app, feltetel, hatarido: float) -> bool:
    """Az eseményhurkot legfeljebb 50 ms-os lépésekben hajtja a határidőig."""
    while True:
        if feltetel():
            return True
        maradek = hatarido - time.monotonic()
        if maradek <= 0:
            return False
        qt_app.processEvents(
            QEventLoop.ProcessEventsFlag.AllEvents,
            max(1, min(50, math.ceil(maradek * 1000))),
        )
        if not feltetel():
            maradek = hatarido - time.monotonic()
            if maradek <= 0:
                return False
            time.sleep(min(0.01, maradek))


def _ket_stabil_fogantyukocka(window, qt_app, toolbar, slider):
    """Három azonos képkockával igazolja a fogantyú raszterének stabilitását."""
    fogantyu = slider.property("handle")
    assert isinstance(fogantyu, QQuickItem), "a dátumcsúszka fogantyúja hiányzik"
    hatarido = time.monotonic() + 3.0
    elozo_allapot = None
    elozo_kep = QImage()
    egymas_utan_azonos = 0

    while True:
        maradek = hatarido - time.monotonic()
        assert maradek > 0, "a dátumcsúszka fogantyúja nem stabilizálódott 3 s alatt"

        kirajzult = QSignalSpy(window.frameSwapped)
        window.requestUpdate()
        assert _varj_feltetelre_hataridovel(
            qt_app, kirajzult.count, hatarido
        ), "az eszköztár nem rajzolt új képkockát 3 s alatt"

        animacio_fut = _futo_slider_animacio(slider)
        hely = fogantyu.mapToItem(toolbar, QPointF(0, 0))
        allapot = (
            float(hely.x()),
            float(hely.y()),
            float(fogantyu.x()),
            float(fogantyu.y()),
            float(slider.property("visualPosition")),
            bool(slider.property("pressed")),
            bool(slider.property("hovered")),
        )
        aktualis_kep = _toolbar_kep(window, toolbar)
        assert not aktualis_kep.isNull(), "üres eszköztár-képkocka"

        if animacio_fut:
            elozo_allapot = None
            elozo_kep = QImage()
            egymas_utan_azonos = 0
            continue
        if (
            allapot == elozo_allapot
            and bytes(elozo_kep.constBits()) == bytes(aktualis_kep.constBits())
        ):
            egymas_utan_azonos += 1
            if egymas_utan_azonos >= 2:
                return elozo_kep, aktualis_kep
        else:
            egymas_utan_azonos = 0

        elozo_allapot = allapot
        elozo_kep = aktualis_kep


def _toolbar_elrendezes(toolbar) -> dict[str, object]:
    """A szöveget nem rögzíti képpontként; az objektumneveket és középpontokat igen."""
    objektumok = [toolbar, *toolbar.findChildren(QObject)]
    nevesitett: dict[str, list[float]] = {}
    szovegek: dict[str, dict[str, object]] = {}
    szoveg_dobozok: list[list[int]] = []
    nevesitett_darabok: dict[str, int] = {}
    szoveg_darabok: dict[str, int] = {}

    for objektum in objektumok:
        if not isinstance(objektum, QQuickItem) or not objektum.isVisible():
            continue
        nev = objektum.objectName()
        szoveg_eleme = is_text_item(objektum)
        eredet = objektum.mapToItem(toolbar, QPointF(0, 0))
        if nev and not szoveg_eleme:
            darab = nevesitett_darabok.get(nev, 0)
            nevesitett_darabok[nev] = darab + 1
            kulcs = f"{nev}#{darab}"
            nevesitett[kulcs] = [
                round(eredet.x(), 3),
                round(eredet.y(), 3),
                round(objektum.width(), 3),
                round(objektum.height(), 3),
            ]

        if not szoveg_eleme:
            continue
        szoveg_ertek = objektum.property("text")
        if not szoveg_ertek:
            szoveg_ertek = objektum.property("placeholderText")
        if szoveg_ertek is None:
            continue
        szoveg = str(szoveg_ertek)
        if not szoveg.strip():
            continue
        alapkulcs = nev or szoveg
        darab = szoveg_darabok.get(alapkulcs, 0)
        szoveg_darabok[alapkulcs] = darab + 1
        kulcs = f"{alapkulcs}#{darab}"
        szovegek[kulcs] = {
            "text": szoveg,
            "center": [
                round(
                    objektum.mapToItem(
                        toolbar,
                        QPointF(objektum.width() / 2, objektum.height() / 2),
                    ).x(),
                    3,
                ),
                round(
                    objektum.mapToItem(
                        toolbar,
                        QPointF(objektum.width() / 2, objektum.height() / 2),
                    ).y(),
                    3,
                ),
            ],
        }

        # A Qt privát Text-alignment enumja nem alakítható át Pythonból
        # minden platformon. A teljes szöveg-item dobozát maszkoljuk; a doboz
        # méretét nem hasonlítjuk, csak a középpontját.
        szoveg_dobozok.append(
            [
                round(eredet.x()) - 2,
                round(eredet.y()) - 2,
                round(objektum.width()) + 4,
                round(objektum.height()) + 4,
            ]
        )

    return {
        "named_items": nevesitett,
        "text_items": szovegek,
        "text_boxes": szoveg_dobozok,
    }


def _nem_szoveg_elteresek(
    elotte: QImage,
    utana: QImage,
    szovegdobozok: list[list[int]],
    *,
    kizarando_teglalapok: list[list[int]] | None = None,
) -> tuple[int, list[tuple[int, int]]]:
    szelesseg = min(elotte.width(), utana.width())
    magassag = min(elotte.height(), utana.height())
    a = elotte.convertToFormat(QImage.Format.Format_ARGB32).copy(
        0, 0, szelesseg, magassag
    )
    b = utana.convertToFormat(QImage.Format.Format_ARGB32).copy(
        0, 0, szelesseg, magassag
    )
    maszkolt = [bytearray(szelesseg) for _ in range(magassag)]
    for x, y, w, h in [*szovegdobozok, *(kizarando_teglalapok or [])]:
        bal = max(0, x)
        felso = max(0, y)
        jobb = min(szelesseg, x + w)
        also = min(magassag, y + h)
        for sor in range(felso, also):
            maszkolt[sor][bal:jobb] = b"\x01" * max(0, jobb - bal)

    pixelek_a = bytes(a.constBits())
    pixelek_b = bytes(b.constBits())
    leptek_a = a.bytesPerLine()
    leptek_b = b.bytesPerLine()
    elteresek: list[tuple[int, int]] = []
    darab = 0
    for y in range(magassag):
        if all(maszkolt[y]):
            continue
        for x in range(szelesseg):
            if maszkolt[y][x]:
                continue
            poz_a = y * leptek_a + x * 4
            poz_b = y * leptek_b + x * 4
            if pixelek_a[poz_a : poz_a + 4] != pixelek_b[poz_b : poz_b + 4]:
                darab += 1
                if len(elteresek) < 24:
                    elteresek.append((x, y))
    return darab, elteresek


def test_pixel_osszehasonlito_kihagyja_a_megadott_dobozt_es_semmi_mast():
    alap = QImage(5, 5, QImage.Format.Format_ARGB32)
    alap.fill(0xFF000000)
    fogantyuval = QImage(alap)
    fogantyuval.setPixel(2, 2, 0xFFFFFFFF)

    assert _nem_szoveg_elteresek(
        alap,
        fogantyuval,
        [],
        kizarando_teglalapok=[[2, 2, 1, 1]],
    )[0] == 0

    masik_pixellel = QImage(fogantyuval)
    masik_pixellel.setPixel(1, 1, 0xFFFFFFFF)
    assert _nem_szoveg_elteresek(
        alap,
        masik_pixellel,
        [],
        kizarando_teglalapok=[[2, 2, 1, 1]],
    )[0] == 1


def _save_failure_images(
    captured: QImage,
    reference: QImage,
    allapot: str,
    magassag_elteres: int,
) -> None:
    """A CI által mért képet, goldent és piros differenciaképet menti."""
    kimeneti_mappa = os.environ.get("PICASAPY_RENDER_FAILURE_DIR")
    if not kimeneti_mappa:
        return
    kimenet = Path(kimeneti_mappa) / "main-toolbar-6103"
    kimenet.mkdir(parents=True, exist_ok=True)
    alapnev = f"{allapot}_{magassag_elteres:+d}"
    assert captured.save(str(kimenet / f"{alapnev}_captured.png"), "PNG")
    if reference.isNull():
        return
    assert reference.save(str(kimenet / f"{alapnev}_reference.png"), "PNG")

    diff = QImage(
        max(captured.width(), reference.width()),
        max(captured.height(), reference.height()),
        QImage.Format.Format_ARGB32,
    )
    diff.fill(0x00000000)
    for y in range(diff.height()):
        for x in range(diff.width()):
            if (
                x >= captured.width()
                or y >= captured.height()
                or x >= reference.width()
                or y >= reference.height()
                or captured.pixel(x, y) != reference.pixel(x, y)
            ):
                diff.setPixel(x, y, 0xFFFF2020)
    assert diff.save(str(kimenet / f"{alapnev}_diff.png"), "PNG")


def test_save_failure_images_writes_capture_reference_and_diff(tmp_path, monkeypatch):
    monkeypatch.setenv("PICASAPY_RENDER_FAILURE_DIR", str(tmp_path))
    captured = QImage(2, 2, QImage.Format.Format_ARGB32)
    captured.fill(0xFF000000)
    reference = QImage(2, 2, QImage.Format.Format_ARGB32)
    reference.fill(0xFFFFFFFF)

    _save_failure_images(captured, reference, "default", 0)

    kimenet = tmp_path / "main-toolbar-6103"
    assert (kimenet / "default_+0_captured.png").is_file()
    assert (kimenet / "default_+0_reference.png").is_file()
    diff = QImage(str(kimenet / "default_+0_diff.png"))
    assert not diff.isNull()
    assert diff.pixelColor(0, 0).name() == "#ff2020"


def _assert_toolbar_referenciaegyezes_belso(
    kep: QImage,
    elrendezes: dict[str, object],
    allapot: str,
    magassag_elteres: int,
) -> None:
    referencia = Path(__file__).parent / "golden" / "main_toolbar_6103"
    fajlnev = f"{allapot}_{magassag_elteres:+d}.png"
    elotte = QImage(str(referencia / fajlnev))
    assert not elotte.isNull(), f"hiányzó 6103 referencia: {fajlnev}"
    elotte_elrendezes = json.loads(
        (referencia / f"{fajlnev}.json").read_text(encoding="utf-8")
    )

    vart_szovegek = {
        kulcs.split(":", 1)[-1]: ertek
        for kulcs, ertek in elotte_elrendezes["text_items"].items()
    }
    szoveg_nevek = {kulcs.rsplit("#", 1)[0] for kulcs in vart_szovegek}
    vart_nevek = {
        nev: geometria
        for nev, geometria in elotte_elrendezes["named_items"].items()
        if nev.rsplit("#", 1)[0] not in szoveg_nevek | {"searchField"}
    }
    mostani_nevek = elrendezes["named_items"]
    assert set(mostani_nevek) == set(vart_nevek), (
        f"megváltozott toolbar objectName-készlet: {fajlnev}"
    )
    for nev, vart in vart_nevek.items():
        mostani = mostani_nevek[nev]
        assert all(abs(a - b) <= 3 for a, b in zip(vart, mostani, strict=True)), (
            f"{nev} geometriája 3 px-nél jobban eltér: {vart} → {mostani}"
        )

    mostani_szovegek = elrendezes["text_items"]
    assert set(mostani_szovegek) == set(vart_szovegek), (
        f"megváltozott toolbar feliratkészlet: {fajlnev}"
    )
    for nev, vart in vart_szovegek.items():
        mostani = mostani_szovegek[nev]
        verzio = nev.split(":", 1)[-1].rsplit("#", 1)[0] == "versionLabel"
        if not verzio:
            assert mostani["text"] == vart["text"], (
                f"megváltozott felirat ({nev}): "
                f"{vart['text']!r} → {mostani['text']!r}"
            )
        # #6315: a jobbra igazított verziófelirat vízszintes közepe a
        # verziószám hosszával mozog, ezért ott csak a függőleges helyzet mért.
        tengelyek = slice(1, 2) if verzio else slice(0, 2)
        assert all(
            abs(a - b) <= 2
            for a, b in zip(
                vart["center"][tengelyek], mostani["center"][tengelyek], strict=True
            )
        ), f"{nev} feliratközepe 2 px-nél jobban eltolódott"

    assert abs(kep.width() - elotte.width()) <= 3
    assert abs(kep.height() - elotte.height()) <= 3
    dobozok = [
        *elotte_elrendezes["text_boxes"],
        *elrendezes["text_boxes"],
    ]
    eltero_pontok, elteres_helyei = _nem_szoveg_elteresek(
        elotte,
        kep,
        dobozok,
    )
    assert eltero_pontok == 0, (
        f"{fajlnev}: {eltero_pontok} eltérő nem-szöveg képpont; "
        f"első helyek: {elteres_helyei}"
    )


def _assert_toolbar_referenciaegyezes(
    kep: QImage,
    elrendezes: dict[str, object],
    allapot: str,
    magassag_elteres: int,
) -> None:
    try:
        _assert_toolbar_referenciaegyezes_belso(
            kep, elrendezes, allapot, magassag_elteres
        )
    except AssertionError:
        referencia = (
            Path(__file__).parent
            / "golden" / "main_toolbar_6103"
            / f"{allapot}_{magassag_elteres:+d}.png"
        )
        _save_failure_images(
            kep,
            QImage(str(referencia)),
            allapot,
            magassag_elteres,
        )
        raise


def test_toolbar_qml_components_stay_below_800_lines():
    qml_dir = _qml_mappa()
    main_toolbar = qml_dir / "MainToolbar.qml"
    assert len(main_toolbar.read_text(encoding="utf-8").splitlines()) <= 800

    komponens = qml_dir / f"{_KOMPONENS}.qml"
    assert komponens.is_file(), f"hiányzik a {_KOMPONENS}.qml komponens"
    assert len(komponens.read_text(encoding="utf-8").splitlines()) <= 800
    assert "Dialog" not in komponens.stem
    assert f"{_KOMPONENS} 1.0 {_KOMPONENS}.qml" in (
        qml_dir.joinpath("qmldir").read_text(encoding="utf-8")
    )


def test_geo_icon_vertical_position_snaps_to_scene_device_pixel():
    source = (
        _qml_mappa() / "ToolbarFilterControls.qml"
    ).read_text(encoding="utf-8")
    geo_icon = blokk_horgonyra(source, 'objectName: "geoFilterIcon"')
    assert "anchors.topMargin:" in geo_icon
    assert "mapToItem(null, 0, 0)" in geo_icon
    assert "devicePixelRatio" in geo_icon
    assert "Math.round" in geo_icon


def test_pixel_guard_stays_active_in_ci(monkeypatch):
    monkeypatch.setenv("CI", "true")
    referencia = Path(__file__).parent / "golden" / "main_toolbar_6103"
    kep = QImage(str(referencia / "default_+0.png"))
    elrendezes = json.loads(
        (referencia / "default_+0.png.json").read_text(encoding="utf-8")
    )
    assert not kep.isNull()
    eltero_kep = QImage(kep)
    x, y = 0, 0
    eltero_kep.setPixel(
        x,
        y,
        0xFFFF00FF if kep.pixel(x, y) != 0xFFFF00FF else 0xFF00FFFF,
    )

    with pytest.raises(AssertionError, match="eltérő nem-szöveg képpont"):
        _assert_toolbar_referenciaegyezes_belso(
            eltero_kep, elrendezes, "default", 0
        )


def test_toolbar_uses_fixed_raster_assets_for_variable_renderers():
    qml_dir = _qml_mappa()
    toolbar = (qml_dir / "ToolbarFilterControls.qml").read_text(encoding="utf-8")
    slider = (qml_dir / "PicasaSlider.qml").read_text(encoding="utf-8")
    assert 'source: "icons/geo-pin-toolbar.png"' in toolbar
    assert 'source: "icons/toolbar-slider-shadow-14x14.png"' in slider
    assert "_rogzitettAlapArnyek" in slider
    assert (qml_dir / "icons" / "geo-pin-toolbar.png").is_file()
    assert (qml_dir / "icons" / "toolbar-slider-shadow-14x14.png").is_file()


@pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason=(
        "a pixel-referencia az Ubuntu Linux CI-n készül; más platformon a Qt "
        "raszterezése eltér"
    ),
)
@pytest.mark.parametrize(("allapot", "magassag_elteres"), _KEPEK)
def test_toolbar_allapot_kepe_rogzitheto(
    qml_app, qt_app, tmp_path, allapot: str, magassag_elteres: int
):
    window, controller, _engine = qml_app
    kezdo_magassag = window.height()
    cel_magassag = kezdo_magassag + magassag_elteres
    window.setHeight(cel_magassag)
    if allapot != "narrow":
        window.setWidth(1024)
    if allapot == "selection":
        QMetaObject.invokeMethod(
            window,
            "handleThumbClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
            Q_ARG("QVariant", 0),
        )
        def allapot_kesz() -> bool:
            return window.property("selectedIndex") == 0
    elif allapot == "filter":
        controller.showStarred()
        szuro = window.findChild(QObject, "starFilterButton")
        assert szuro is not None

        def allapot_kesz() -> bool:
            return (
                controller.viewModeName == "starred"
                and szuro.property("ctlFilterActive") is True
            )
    elif allapot == "narrow":
        window.setWidth(650)
        zona = window.findChild(QObject, "toolbarFilterZone")
        assert zona is not None

        def allapot_kesz() -> bool:
            return window.width() == 650 and zona.property("visible") is False
    else:
        def allapot_kesz() -> bool:
            return window.width() > 0

    def kesz() -> bool:
        vart_szelesseg = 650 if allapot == "narrow" else 1024
        return (
            window.width() == vart_szelesseg
            and window.height() == cel_magassag
            and allapot_kesz()
        )

    assert _varj_feltetelre_hataridovel(
        qt_app, kesz, time.monotonic() + 3.0
    ), (
        f"az eszköztár állapota nem állt be: {allapot}, {magassag_elteres:+d}px"
    )
    toolbar = window.findChild(QObject, "mainToolbar")
    assert toolbar is not None, "a mainToolbar nem található"
    datumcsuszka = toolbar.findChild(QObject, "dateRangeFilterSlider")
    assert datumcsuszka is not None, "a dátumcsúszka nem található"
    assert datumcsuszka.property("value") == 0.0
    assert datumcsuszka.property("visualPosition") == 0.0
    QTest.mouseMove(
        window,
        QPoint(max(0, window.width() - 2), max(0, window.height() - 2)),
    )
    qt_app.processEvents()
    toolbar_kep, masodik_toolbar_kep = _ket_stabil_fogantyukocka(
        window, qt_app, toolbar, datumcsuszka
    )
    assert not toolbar_kep.isNull(), f"üres toolbar-kép: {allapot}"
    assert not masodik_toolbar_kep.isNull(), f"üres második toolbar-kép: {allapot}"
    geo_icon = toolbar.findChild(QObject, "geoFilterIcon")
    assert isinstance(geo_icon, QQuickItem), "a geoFilterIcon nem található"
    geo_origin = geo_icon.mapToScene(QPointF(0, 0))
    dpr = window.devicePixelRatio()
    fizikai_y = geo_origin.y() * dpr
    if not math.isclose(fizikai_y, round(fizikai_y), abs_tol=1e-6):
        referencia = (
            Path(__file__).parent
            / "golden" / "main_toolbar_6103"
            / f"{allapot}_{magassag_elteres:+d}.png"
        )
        _save_failure_images(
            toolbar_kep,
            QImage(str(referencia)),
            allapot,
            magassag_elteres,
        )
    assert math.isclose(fizikai_y, round(fizikai_y), abs_tol=1e-6), (
        "a geoFilterIcon függőleges jelenetkoordinátája részpixeles: "
        f"({geo_origin.x():.3f}, {geo_origin.y():.3f}), DPR={dpr}"
    )

    elrendezes = _toolbar_elrendezes(toolbar)
    eltero_kockapontok, elteres_helyei = _nem_szoveg_elteresek(
        toolbar_kep,
        masodik_toolbar_kep,
        [*elrendezes["text_boxes"], *elrendezes["text_boxes"]],
    )
    if eltero_kockapontok:
        referencia = (
            Path(__file__).parent
            / "golden" / "main_toolbar_6103"
            / f"{allapot}_{magassag_elteres:+d}.png"
        )
        _save_failure_images(
            toolbar_kep,
            QImage(str(referencia)),
            allapot,
            magassag_elteres,
        )
    assert eltero_kockapontok == 0, (
        f"a két egymás utáni {allapot} kép eltér: "
        f"{eltero_kockapontok} nem-szöveg képpont, első helyek: {elteres_helyei}"
    )

    fajlnev = f"{allapot}_{magassag_elteres:+d}.png"
    mentesi_mappa = Path(os.environ.get("PICASAPY_6103_CAPTURE_DIR", tmp_path))
    mentesi_mappa.mkdir(parents=True, exist_ok=True)
    assert toolbar_kep.save(str(mentesi_mappa / fajlnev), "PNG")
    (mentesi_mappa / f"{fajlnev}.json").write_text(
        json.dumps(elrendezes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _assert_toolbar_referenciaegyezes(
        toolbar_kep, elrendezes, allapot, magassag_elteres
    )
    _assert_toolbar_referenciaegyezes(
        masodik_toolbar_kep,
        elrendezes,
        allapot,
        magassag_elteres,
    )
