"""#7414: Fájltípus kikapcsolásakor az elem azonnal eltűnik a felületről,

de az index photos táblájában a sora megmarad, és visszakapcsoláskor
újraolvasás nélkül megjelenik.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PIL import Image

from conftest import _build_qml_app
from support.jpeg_factory import make_minta_jpeg
from picasapy.index import open_index
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _gyerek,
    _klikk_ablakban,
    _varj,
)
from tests.app.qml_functional.test_parbeszedek_valodi_5150_b import (
    _beallitasok_megnyit,
    _fulre_kattint,
)

_BMP = "masodik.bmp"
_JPEG = "elso.jpg"
_MAGASSAG_ELTOLASOK = (-5, 0, 5)


def _keszits_kepeket(lib: Path) -> None:
    make_minta_jpeg(lib / _JPEG, size=(120, 90), seed=7414)
    Image.new("RGB", (80, 60), (30, 120, 210)).save(lib / _BMP, format="BMP")


@pytest.fixture
def filetype_retention_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_kepeket,
    )


def _nevek(controller) -> set[str]:
    return {photo.name for photo in controller.photos.photos}


def _kep_mentese(window, qt_app, tmp_path: Path, nev: str, magassag_elteres: int):
    """Az ablak renderelt képét elmenti (a látás a mérce), és visszaadja a bájtjait."""
    qt_app.processEvents()
    kep = window.grabWindow()
    cel = tmp_path / f"{nev}-{magassag_elteres:+d}.png"
    assert kep.save(str(cel)), f"nem sikerült elmenteni: {cel}"
    return kep.constBits().tobytes()


def _talca_token_darabok(controller) -> list[int]:
    """A képtálcán kint álló album-tokenek darabszámai."""
    from picasapy import tray

    return [token.photo_count for token in tray.album_tokens(controller._tray)]


def _fajltipus_ful(window, qt_app, magassag_elteres: int = 0):
    options = _beallitasok_megnyit(window, qt_app)
    if magassag_elteres:
        options.setHeight(options.height() + magassag_elteres)
    _fulre_kattint(qt_app, options, "optionsTabFileTypes", 2)
    return options


@pytest.mark.parametrize("magassag_elteres", _MAGASSAG_ELTOLASOK)
def test_kikapcsolaskor_eltunik_racsbol_de_megmarad_indexben(
    filetype_retention_app, qt_app, tmp_path, magassag_elteres: int
):
    window, controller, _engine = filetype_retention_app
    window.show()
    window.requestActivate()
    assert _varj(qt_app, lambda: _nevek(controller) == {_JPEG, _BMP})
    assert controller.recentlyUpdatedCount == 2
    elotte = _kep_mentese(window, qt_app, tmp_path, "7414-1-elotte", magassag_elteres)

    # Ellenőrizzük, hogy mindkét kép az indexben van
    with open_index(controller._db_path) as conn:
        db_nevek = {row["name"] for row in conn.execute("SELECT name FROM photos")}
    assert db_nevek == {_JPEG, _BMP}

    # Megnyitjuk a Beállítások ablakot és kikapcsoljuk a BMP-t
    options = _fajltipus_ful(window, qt_app, magassag_elteres)
    bmp = _gyerek(options, "optionsFileTypeBmpCheck")
    assert bmp.property("checked") is True
    _klikk_ablakban(qt_app, options, bmp)
    assert bmp.property("checked") is False
    _klikk_ablakban(qt_app, options, _gyerek(options, "optionsOkButton"))

    # 1. Ellenőrzés: a rácsból eltűnik a BMP, csak a JPEG marad
    assert _varj(
        qt_app,
        lambda: not controller._sync_running and _nevek(controller) == {_JPEG},
    )

    # A bal hasáb számlálója is a látható halmazt számolja, nem az indexben
    # megmaradt kikapcsolt sort.
    assert controller.recentlyUpdatedCount == 1
    # A rács ténylegesen újrarajzolt képe is más: az eltűnt elem helye üres.
    kikapcsolva = _kep_mentese(
        window, qt_app, tmp_path, "7414-2-kikapcsolva", magassag_elteres
    )
    assert kikapcsolva != elotte, "a kikapcsolás után a rács képe nem változott"

    # 2. Ellenőrzés: a photos táblában a sora MEGMARAD
    with open_index(controller._db_path) as conn:
        db_nevek_kikapcsolva = {
            row["name"] for row in conn.execute("SELECT name FROM photos")
        }
    assert db_nevek_kikapcsolva == {_JPEG, _BMP}

    # 3. Visszakapcsoláskor a BMP újra megjelenik a felületen
    options = _fajltipus_ful(window, qt_app, 0)
    bmp = _gyerek(options, "optionsFileTypeBmpCheck")
    assert bmp.property("checked") is False
    _klikk_ablakban(qt_app, options, bmp)
    _klikk_ablakban(qt_app, options, _gyerek(options, "optionsOkButton"))

    assert _varj(
        qt_app,
        lambda: not controller._sync_running and _nevek(controller) == {_JPEG, _BMP},
    )
    assert controller.recentlyUpdatedCount == 2
    visszakapcsolva = _kep_mentese(
        window, qt_app, tmp_path, "7414-3-visszakapcsolva", magassag_elteres
    )
    assert visszakapcsolva != kikapcsolva


def test_kikapcsolt_tipus_a_szurt_nezetbol_es_a_zold_savbol_is_kimarad(
    filetype_retention_app, qt_app, tmp_path
):
    """A szűrt nézetek (itt: Recently Updated) rácsa és a zöld eredménysáv
    darabszáma is a látható halmazt mutatja, az index sora viszont megmarad."""
    window, controller, _engine = filetype_retention_app
    window.show()
    window.requestActivate()
    assert _varj(qt_app, lambda: _nevek(controller) == {_JPEG, _BMP})

    controller.showRecentlyUpdatedAlbum()
    assert _varj(qt_app, lambda: _nevek(controller) == {_JPEG, _BMP})
    assert _varj(qt_app, lambda: _talca_token_darabok(controller) == [2])
    assert re.search(r"\b2 pictures visible", controller.filterStatusText)

    controller.setFileTypeEnabled("bmp", False)
    assert _varj(qt_app, lambda: _nevek(controller) == {_JPEG})
    assert controller.recentlyUpdatedCount == 1
    assert re.search(r"\b1 pictures visible", controller.filterStatusText)
    # a tálca „Album Selected - N photos” tokenje is a látható halmazt számolja
    assert _talca_token_darabok(controller) == [1]
    _kep_mentese(window, qt_app, tmp_path, "7414-4-szurt-nezet", 0)

    with open_index(controller._db_path) as conn:
        assert {r["name"] for r in conn.execute("SELECT name FROM photos")} == {
            _JPEG,
            _BMP,
        }

    controller.setFileTypeEnabled("bmp", True)
    assert _varj(qt_app, lambda: _nevek(controller) == {_JPEG, _BMP})
    assert controller.recentlyUpdatedCount == 2
    assert _talca_token_darabok(controller) == [2]
