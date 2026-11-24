"""#7414: Fájltípus kikapcsolásakor az elem azonnal eltűnik a felületről,

de az index photos táblájában a sora megmarad, és visszakapcsoláskor
újraolvasás nélkül megjelenik.
"""

from __future__ import annotations

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


def _fajltipus_ful(window, qt_app, magassag_elteres: int = 0):
    options = _beallitasok_megnyit(window, qt_app)
    if magassag_elteres:
        options.setHeight(options.height() + magassag_elteres)
    _fulre_kattint(qt_app, options, "optionsTabFileTypes", 2)
    return options


@pytest.mark.parametrize("magassag_elteres", _MAGASSAG_ELTOLASOK)
def test_kikapcsolaskor_eltunik_racsbol_de_megmarad_indexben(
    filetype_retention_app, qt_app, magassag_elteres: int
):
    window, controller, _engine = filetype_retention_app
    window.show()
    window.requestActivate()
    assert _varj(qt_app, lambda: _nevek(controller) == {_JPEG, _BMP})

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
