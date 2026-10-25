"""A tálca csillag- és forgatógombjainak lemezre írt eredménye (#5396)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw
from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.ini import KeyValueLine, load_document
from support.jpeg_factory import make_minta_jpeg
from support.qt_wait import wait_for_photo_op
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app


@pytest.fixture
def csillag_forgatas_app(qt_app, tmp_path):
    # A valódi bélyegkép-szolgáltató és mintázatos képek: a teszt képe a
    # kiadásba kerül, és ott a csempéken látható képnek kell lennie
    # (picasapy-agent #225).
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


@pytest.fixture
def csillag_forgatas_valodi_app(qt_app, tmp_path):
    """A forgatási próbához mintázatos képet és a valódi render-magot adja."""
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_mintakepet,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _keszits_kepeket(mappa: Path) -> None:
    for sorszam in range(1, 8):
        make_minta_jpeg(mappa / f"{sorszam}.jpg", size=(320, 240), seed=sorszam)


def _negyedes_kep(path: Path) -> None:
    """Négy eltérő színű negyed: a 90°-os elfordulás a képpontokból látszik."""
    szelesseg, magassag = 320, 240
    kep = Image.new("RGB", (szelesseg, magassag))
    festo = ImageDraw.Draw(kep)
    kozep_x, kozep_y = szelesseg // 2, magassag // 2
    festo.rectangle((0, 0, kozep_x - 1, kozep_y - 1), fill=(240, 20, 20))
    festo.rectangle((kozep_x, 0, szelesseg - 1, kozep_y - 1), fill=(20, 210, 20))
    festo.rectangle((0, kozep_y, kozep_x - 1, magassag - 1), fill=(20, 40, 240))
    festo.rectangle(
        (kozep_x, kozep_y, szelesseg - 1, magassag - 1), fill=(240, 220, 20)
    )
    kep.save(path, "JPEG", quality=95, subsampling=0)


def _keszits_mintakepet(mappa: Path) -> None:
    _negyedes_kep(mappa / "1.jpg")


def _qml_bejaras(gyoker):
    for elem in gyoker.childItems():
        yield elem
        yield from _qml_bejaras(elem)


def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _kattint(window, elem: QQuickItem, qt_app) -> None:
    assert elem.isVisible() and elem.isEnabled(), (
        f"a kattintandó elem nem látható vagy tiltott: {elem.objectName()}"
    )
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont.toPoint(),
    )
    qt_app.processEvents()


def _foto_kijelolese(window, controller, qt_app, fajlnev: str) -> int:
    sor = next(
        i for i, photo in enumerate(controller.photos.photos)
        if photo.name == fajlnev
    )
    mouse_areas = [
        item
        for item in _qml_bejaras(window.contentItem())
        if item.objectName() == "thumbMouseArea"
        and item.parentItem() is not None
        and item.parentItem().property("index") == sor
    ]
    assert len(mouse_areas) == 1, (
        f"a {fajlnev} kép rácsbeli kattintási területe nem egyértelmű"
    )
    _kattint(window, mouse_areas[0], qt_app)
    assert _var(qt_app, lambda: window.property("selectedIndex") == sor), (
        f"a valódi rácskattintás nem a {fajlnev} képet jelölte ki"
    )
    return sor


def _talca_gomb(window, object_name: str) -> QQuickItem:
    elem = window.findChild(QQuickItem, object_name)
    assert elem is not None, f"hiányzó tálcagomb: {object_name}"
    return elem


def _kep_elemek(window, object_name: str) -> list[QQuickItem]:
    return [
        item
        for item in _qml_bejaras(window.contentItem())
        if item.objectName() == object_name
    ]


def _qml_url(elem: QQuickItem) -> str:
    source = elem.property("source")
    return source.toString() if hasattr(source, "toString") else str(source)


def _delegate_index(elem: QQuickItem) -> int | None:
    """A ThumbDelegate indexe a belső Image ősein található."""
    while elem is not None:
        index = elem.property("index")
        if index is not None:
            try:
                return int(index)
            except (TypeError, ValueError):
                pass
        elem = elem.parentItem()
    return None


def _csempe_koordinatak(window, elem: QQuickItem, kep: QImage) -> list[tuple[int, int]]:
    """A kirajzolt kép négy belső negyedének ablak-képpontbeli helye."""
    szeles = float(elem.property("paintedWidth"))
    magas = float(elem.property("paintedHeight"))
    doboz_szel = float(elem.property("width"))
    doboz_mag = float(elem.property("height"))
    bal_felso = elem.mapToScene(
        QPointF((doboz_szel - szeles) / 2, (doboz_mag - magas) / 2)
    )
    dpr_x = kep.width() / window.width()
    dpr_y = kep.height() / window.height()
    return [
        (
            round((bal_felso.x() + szeles * x) * dpr_x),
            round((bal_felso.y() + magas * y) * dpr_y),
        )
        for x, y in ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75))
    ]


def _negyedszinek(window, elem: QQuickItem, kep: QImage) -> list[tuple[int, int, int]]:
    return [
        tuple(kep.pixelColor(x, y).getRgb()[:3])
        for x, y in _csempe_koordinatak(window, elem, kep)
    ]


def _szin_egyezik(tenyleges: tuple[int, int, int], vart: tuple[int, int, int]) -> bool:
    return sum((a - b) ** 2 for a, b in zip(tenyleges, vart, strict=True)) ** 0.5 < 85


def _kattints_es_varj(window, controller, qt_app, gombnev: str) -> None:
    gomb = _talca_gomb(window, gombnev)
    wait_for_photo_op(
        controller,
        lambda: _kattint(window, gomb, qt_app),
        qt_app=qt_app,
    )


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_talca_csillag_es_forgatas_az_eredeti_ini_kimenetet_irja(
    csillag_forgatas_app, qt_app, magassag_eltolas, tmp_path
):
    window, controller, _engine = csillag_forgatas_app
    eredeti_magassag = window.height()
    celmagassag = eredeti_magassag + magassag_eltolas
    window.setHeight(celmagassag)
    assert _var(qt_app, lambda: window.height() == celmagassag), (
        f"az ablakmagasság nem állt be ({magassag_eltolas:+} px)"
    )
    assert [photo.name for photo in controller.photos.photos] == [
        f"{sorszam}.jpg" for sorszam in range(1, 8)
    ]
    assert all(
        not photo.star and photo.rotate_steps == 0
        for photo in controller.photos.photos
    )

    _foto_kijelolese(window, controller, qt_app, "4.jpg")
    _kattints_es_varj(window, controller, qt_app, "trayStarButton")
    assert _var(qt_app, lambda: controller.photos.starAt(3))

    _foto_kijelolese(window, controller, qt_app, "7.jpg")
    _kattints_es_varj(window, controller, qt_app, "trayStarButton")
    assert _var(qt_app, lambda: controller.photos.starAt(6))
    _kattints_es_varj(window, controller, qt_app, "trayStarButton")
    assert _var(qt_app, lambda: not controller.photos.starAt(6))

    _foto_kijelolese(window, controller, qt_app, "5.jpg")
    _kattints_es_varj(window, controller, qt_app, "trayRotateRight")
    assert _var(qt_app, lambda: controller.photos.rotateAt(4) == 1)

    _foto_kijelolese(window, controller, qt_app, "6.jpg")
    _kattints_es_varj(window, controller, qt_app, "trayRotateLeft")
    assert _var(qt_app, lambda: controller.photos.rotateAt(5) == 3)

    ini_path = Path(controller.photos.photos[0].folder_path) / ".picasa.ini"
    assert ini_path.is_file(), "a műveletek nem írtak .picasa.ini-t"
    document = load_document(ini_path)
    actual = [
        (
            section.name,
            {
                line.key: line.value
                for line in section.lines
                if isinstance(line, KeyValueLine)
            },
        )
        for section in document.file_sections()
    ]
    # A job-231 szerint a forgatás után az eredeti backuphash-t is ír (#5810);
    # az értéke az írás pillanatától függ, ezért csak a meglétét és alakját mérjük.
    for nev, kulcsok in actual:
        hash_ertek = kulcsok.get("backuphash")
        if nev in ("5.jpg", "6.jpg"):
            assert hash_ertek is not None and hash_ertek.isdecimal(), (
                f"[{nev}] forgatás után hiányzik a backuphash: {kulcsok!r}"
            )
            assert 0 <= int(hash_ertek) <= 0xFFFF
        else:
            assert hash_ertek is None, f"[{nev}] csillagnál nem kell backuphash"
    kulcsok_hash_nelkul = [
        (nev, {k: v for k, v in kulcsok.items() if k != "backuphash"})
        for nev, kulcsok in actual
    ]
    assert kulcsok_hash_nelkul == [
        ("4.jpg", {"star": "yes"}),
        ("7.jpg", {}),
        ("5.jpg", {"rotate": "rotate(1)"}),
        ("6.jpg", {"rotate": "rotate(3)"}),
    ], f"a lemezre írt .picasa.ini eltér az eredeti viselkedésétől: {actual!r}"
    assert window.grabWindow().save(str(tmp_path / "csillag_forgatas_5396.png"))


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
@pytest.mark.parametrize(
    ("gombnev", "vart_lepes", "vart_negyedszinek"),
    (
        ("trayRotateRight", 1, [(20, 40, 240), (240, 20, 20), (240, 220, 20), (20, 210, 20)]),
        ("trayRotateLeft", 3, [(20, 210, 20), (240, 220, 20), (240, 20, 20), (20, 40, 240)]),
    ),
)
def test_a_talca_forgatasa_a_valodi_racs_es_talca_belyegkepet_elforditja(
    csillag_forgatas_valodi_app,
    qt_app,
    tmp_path,
    magassag_eltolas,
    gombnev,
    vart_lepes,
    vart_negyedszinek,
):
    window, controller, _engine = csillag_forgatas_valodi_app
    celmagassag = window.height() + magassag_eltolas
    window.setHeight(celmagassag)
    assert _var(qt_app, lambda: window.height() == celmagassag), (
        f"az ablakmagasság nem állt be ({magassag_eltolas:+} px)"
    )

    sor = _foto_kijelolese(window, controller, qt_app, "1.jpg")
    racs_kepek = [
        item
        for item in _kep_elemek(window, "thumbImage")
        if _delegate_index(item) == sor
    ]
    assert len(racs_kepek) == 1, "a mintakép rács-bélyegképe nem egyértelmű"
    racs_kep = racs_kepek[0]
    assert _var(
        qt_app,
        lambda: racs_kep.property("paintedWidth") > 0
        and racs_kep.property("paintedHeight") > 0,
    ), "a rács valódi bélyegképe nem töltődött be"
    assert float(racs_kep.property("paintedWidth")) > float(
        racs_kep.property("paintedHeight")
    ), "a mintakép kiinduló csempéjének fekvőnek kell lennie"

    talca_kepek = _kep_elemek(window, "trayPreviewThumb")
    assert len(talca_kepek) == 1, "a kijelölt kép tálca-bélyegképe hiányzik"
    talca_kep = talca_kepek[0]
    assert _var(
        qt_app,
        lambda: talca_kep.property("paintedWidth") > 0
        and talca_kep.property("paintedHeight") > 0,
    ), "a tálca valódi bélyegképe nem töltődött be"
    talca_url_forgatas_elott = _qml_url(talca_kep)

    foto = controller.photos.photos[sor]
    url_forgatas_elott = controller.photos.thumbUrlAt(sor)
    assert foto.rotate_steps == 0
    assert controller._provider.photo_record(str(foto.id)).rotate_steps == 0

    _kattints_es_varj(window, controller, qt_app, gombnev)
    assert _var(qt_app, lambda: controller.photos.photos[sor].rotate_steps == vart_lepes), (
        f"a {gombnev} nem frissítette a modell forgatását"
    )
    foto = controller.photos.photos[sor]
    assert controller.photos.thumbUrlAt(sor) != url_forgatas_elott, (
        "a forgatás után nem változott a rács bélyegképének cache-buster URL-je"
    )
    url_forgatas_utan = controller.photos.thumbUrlAt(sor)
    assert controller._provider.photo_record(str(foto.id)).rotate_steps == vart_lepes, (
        "a ThumbnailProvider nem kapta meg a friss rotate_steps rekordot"
    )
    provider_id = url_forgatas_utan.removeprefix("image://thumbs/")
    provider_kep = controller._provider.requestImage(provider_id, QSize(), QSize())
    assert provider_kep.height() > provider_kep.width(), (
        "a friss provider rekord sem ad álló képet: "
        f"{provider_kep.width()}x{provider_kep.height()}"
    )

    # A rajzolt rácskép a termék providerének válaszából származik; a várakozás
    # a tényleges QML-geometrián történik, az állítást a képpontok végzik.
    vart_allo = _var(
        qt_app,
        lambda: float(racs_kep.property("paintedHeight"))
        > float(racs_kep.property("paintedWidth")),
    )
    screenshot = window.grabWindow()
    felvetel = tmp_path / f"forgatas_utani_racs_5396_{gombnev}_{magassag_eltolas}.png"
    assert screenshot.save(str(felvetel)), f"nem menthető a rács képe: {felvetel}"
    assert _qml_url(racs_kep) == url_forgatas_utan, (
        "a rács QML Image.source nem követte a modell friss URL-jét: "
        f"QML={_qml_url(racs_kep)!r}, modell={url_forgatas_utan!r}"
    )
    assert vart_allo, (
        "a forgatás után a valódi bélyegképből rajzolt rácscsempe nem álló: "
        f"{racs_kep.property('paintedWidth')}x{racs_kep.property('paintedHeight')}"
    )

    szinek = _negyedszinek(window, racs_kep, screenshot)
    assert all(
        _szin_egyezik(tenyleges, vart)
        for tenyleges, vart in zip(szinek, vart_negyedszinek, strict=True)
    ), f"a rácson nem fordult el a mintázat a {gombnev} után: {szinek!r}"

    talca_url_frissult = _var(
        qt_app,
        lambda: _qml_url(talca_kep) != talca_url_forgatas_elott
        and f"?r={vart_lepes}" in _qml_url(talca_kep),
    )
    assert talca_url_frissult, (
        "a tálca bélyegképe nem kérte újra a forgatott URL-t "
        f"(előtte: {talca_url_forgatas_elott!r}, utána: {_qml_url(talca_kep)!r})"
    )
    talca_szinek = _negyedszinek(window, talca_kep, screenshot)
    assert len(talca_szinek) == 4 and all(
        _szin_egyezik(tenyleges, vart)
        for tenyleges, vart in zip(talca_szinek, vart_negyedszinek, strict=True)
    ), f"a tálca bélyegképe nem a forgatott mintázatot mutatja: {talca_szinek!r}"
