"""#6581: a filters= keret- és árnyék-kimenete nem lépheti túl a pixelkeretet."""
# rontás-kontroll: picasapy.render.glimmer_frame_ops._KERET_KIMENET_ABSZOLUT_PIXELPLAFON = 1_000_000_000 → 1 failed
# rontás-kontroll: picasapy.render.glimmer_frame_ops._KERET_KIMENET_FORRAS_SZORZO = 256 → 1 failed

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render import chain_glimmer_handlers as handlers
from picasapy.render import glimmer_frame_ops
from picasapy.render.chain import apply_filters

_MAX_FORRAS_SZORZO = 128
_MAX_KIMENETI_PIXEL = 256_000_000
_NAGY_FORRAS_SZORZO = 4


class _TulmeretesFoglalas(RuntimeError):
    pass


def _figyel_foglalasokat(monkeypatch, forras: np.ndarray) -> list[tuple[str, int]]:
    """A javítás nélküli próba se kérjen valódi gigabájtos memóriát."""
    forras_pixelek = forras.shape[0] * forras.shape[1]
    maximum = min(
        forras_pixelek * _MAX_FORRAS_SZORZO,
        max(_MAX_KIMENETI_PIXEL, forras_pixelek * _NAGY_FORRAS_SZORZO),
    )
    tulmeretes: list[tuple[str, int]] = []

    def meret_alaku(shape) -> int | None:
        try:
            if len(shape) < 2:
                return None
            return int(shape[0]) * int(shape[1])
        except (TypeError, ValueError, OverflowError):
            return None

    for nev in ("empty", "zeros"):
        eredeti = getattr(np, nev)

        def figyelo(shape, *args, _eredeti=eredeti, _nev=nev, **kwargs):
            pixelek = meret_alaku(shape)
            if pixelek is not None and pixelek > maximum:
                tulmeretes.append((_nev, pixelek))
                raise _TulmeretesFoglalas(_nev)
            return _eredeti(shape, *args, **kwargs)

        monkeypatch.setattr(np, nev, figyelo)

    eredeti_border = glimmer_frame_ops.cv2.copyMakeBorder

    def figyelo_border(image, top, bottom, left, right, *args, **kwargs):
        pixelek = (image.shape[0] + top + bottom) * (image.shape[1] + left + right)
        if pixelek > maximum:
            tulmeretes.append(("copyMakeBorder", pixelek))
            raise _TulmeretesFoglalas("copyMakeBorder")
        return eredeti_border(image, top, bottom, left, right, *args, **kwargs)

    monkeypatch.setattr(glimmer_frame_ops.cv2, "copyMakeBorder", figyelo_border)
    return tulmeretes


@pytest.mark.parametrize(
    ("filters", "name"),
    [
        ("Border=1,5000;", "Border"),
        ("Border=1,20000;", "Border"),
        ("MuseumMatte=1,20000;", "MuseumMatte"),
        ("DropShadow=1,1e9,90,10,00000000,00ffffff,30;", "DropShadow"),
    ],
)
def test_a_ini_nagy_keret_es_arnyek_meretellenorzes_elott_nem_foglal(
    monkeypatch, filters, name
):
    image = np.zeros((48, 64, 3), dtype=np.uint8)
    tulmeretes = _figyel_foglalasokat(monkeypatch, image)

    report = apply_filters(image, parse_filters(filters))

    assert report.skipped == (name,)
    assert report.image is image
    assert tulmeretes == []


def test_az_abszolut_pixelplafon_a_forras_szorzoja_felett_is_ervenyes(monkeypatch):
    image = np.zeros((2000, 2000, 3), dtype=np.uint8)
    tulmeretes = _figyel_foglalasokat(monkeypatch, image)

    report = apply_filters(image, parse_filters("Border=1,9000;"))

    assert report.skipped == ("Border",)
    assert report.image is image
    assert tulmeretes == []


def test_a_forrasszorzo_korlatozza_az_abszolut_plafon_alatti_meretet(monkeypatch):
    image = np.zeros((300, 300, 3), dtype=np.uint8)
    tulmeretes = _figyel_foglalasokat(monkeypatch, image)

    report = apply_filters(image, parse_filters("Border=1,1600;"))

    assert report.skipped == ("Border",)
    assert report.image is image
    assert tulmeretes == []


@pytest.mark.parametrize(
    ("filters", "expected_shape"),
    [
        ("Border=1,100,100;", (448, 464, 3)),
        ("MuseumMatte=1,100,100;", (448, 464, 3)),
        ("DropShadow=1,30,90,100,00000000,00ffffff,30;", (320, 336, 3)),
    ],
)
def test_a_filterdesc_csuszkak_felso_ertekeivel_a_keret_elfer(filters, expected_shape):
    image = np.zeros((48, 64, 3), dtype=np.uint8)

    report = apply_filters(image, parse_filters(filters))

    assert report.skipped == ()
    assert report.image.shape == expected_shape


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_nem_veges_float_parameterek_az_alapertekre_esnek(value):
    image = np.zeros((48, 64, 3), dtype=np.uint8)
    op = parse_filters(f"Border=1,{value};")[0]

    assert handlers._float_at(op, 0, 20.0) == 20.0
    report = apply_filters(image, (op,))

    assert report.skipped == ()
    assert report.image.shape == (98, 114, 3)


class _CsakMeret:
    """Foglalás nélküli képhelyettes: az őr csak a `shape`-et olvassa."""

    def __init__(self, height: int, width: int) -> None:
        self.shape = (height, width, 3)


@pytest.mark.parametrize(
    ("height", "width"),
    [(5477, 7303), (6000, 8000), (9000, 12000)],
)
def test_nagy_foto_szokasos_kerettel_nem_esik_ki(height, width):
    # 40, 48 és 108 megapixeles fotó a csúszka legnagyobb keretével
    # (2 × 100 px oldalanként) és a legnagyobb árnyékmargóval.
    for tobblet in (400, 2 * 30 + 2 * 100):
        glimmer_frame_ops._ellenoriz_keret_kimenetet(
            _CsakMeret(height, width), width + tobblet, height + tobblet
        )


def test_nagy_foto_abszurd_kerete_kiesik():
    with pytest.raises(ValueError):
        glimmer_frame_ops._ellenoriz_keret_kimenetet(
            _CsakMeret(5477, 7303), 7303 + 40000, 5477 + 40000
        )
