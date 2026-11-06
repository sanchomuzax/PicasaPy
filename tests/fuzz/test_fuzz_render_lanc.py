"""A renderlánc szerkezeti fuzz-próbái és a #6581 regressziós magjai."""
# ruff: noqa: E402

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import example, given, strategies as st

from picasapy.ini.filter_registry import canonical_filter_name
from picasapy.ini.filters import FilterOp, parse_filters
from picasapy.render.chain import apply_filters, can_render_filter
from picasapy.render.glimmer_frame_ops import (
    _KERET_KIMENET_ABSZOLUT_PIXELPLAFON,
    _KERET_KIMENET_FORRAS_SZORZO,
    _KERET_KIMENET_NAGY_FORRAS_SZORZO,
)
from picasapy.render.registry import FILTER_REGISTRY

_RENDERELHETO = tuple(
    nev
    for kulcs in FILTER_REGISTRY
    if (nev := canonical_filter_name(kulcs)) is not None and can_render_filter(nev)
)
_ERTEKEK = (
    "0",
    "nan",
    "inf",
    "-inf",
    "1e9",
    "-1e9",
    "00000000",
    "00ffffff",
    "#ff00ff",
    "",
    "1",
    "-1",
)
# (magasság, szélesség); így a 2×3 és 64×48 a feladatban megadott szélesség×magasság.
_KEPMERETEK = ((1, 1), (3, 2), (5, 7), (48, 64))
_KORPUSZ = (Path(__file__).parent / "korpusz" / "render" / "6581.txt").read_text(
    encoding="utf-8"
).splitlines()


@dataclass(frozen=True)
class _RenderEset:
    nev: str
    parameterek: tuple[str, ...]
    magassag: int
    szelesseg: int
    csatornak: int


def _pixelplafon(forras: int) -> int:
    """A #6581 által használt plafon; a konstansokat a forrásból importáljuk."""
    return min(
        forras * _KERET_KIMENET_FORRAS_SZORZO,
        max(
            _KERET_KIMENET_ABSZOLUT_PIXELPLAFON,
            forras * _KERET_KIMENET_NAGY_FORRAS_SZORZO,
        ),
    )


@st.composite
def _render_esetek(draw):
    nev = draw(st.sampled_from(_RENDERELHETO))
    alak = draw(st.sampled_from(_KEPMERETEK))
    csatornak = draw(st.sampled_from((3, 4)))
    parameterek = draw(
        st.one_of(
            st.just(()),
            st.lists(
                st.one_of(
                    st.sampled_from(_ERTEKEK),
                    st.floats(
                        allow_nan=False,
                        allow_infinity=False,
                        width=32,
                    ).map(lambda ertek: format(ertek, ".7g")),
                ),
                min_size=0,
                max_size=8,
            ).map(lambda ertekek: ("1", *ertekek)),
        )
    )
    return _RenderEset(nev, parameterek, alak[0], alak[1], csatornak)


class _TulmeretesFoglalas(RuntimeError):
    pass


def _elemszam(alak) -> int | None:
    try:
        if isinstance(alak, int):
            return alak
        szamok = tuple(int(elem) for elem in alak)
        return int(np.prod(szamok, dtype=object))
    except (TypeError, ValueError, OverflowError):
        return None


@contextmanager
def _figyel_tultermeseket(monkeypatch, plafon: int):
    tulmeretes: list[tuple[str, int]] = []
    with monkeypatch.context() as csere:
        for nev in ("empty", "zeros", "ones", "full"):
            eredeti = getattr(np, nev)

            def figyelo(alak, *args, _eredeti=eredeti, _nev=nev, **kwargs):
                elemszam = _elemszam(alak)
                if elemszam is not None and elemszam > plafon:
                    tulmeretes.append((_nev, elemszam))
                    raise _TulmeretesFoglalas(_nev)
                return _eredeti(alak, *args, **kwargs)

            csere.setattr(np, nev, figyelo)

        import picasapy.render.glimmer_frame_ops as frame_ops

        eredeti_border = frame_ops.cv2.copyMakeBorder

        def figyelo_border(image, top, bottom, left, right, *args, **kwargs):
            pixelek = (image.shape[0] + int(top) + int(bottom)) * (
                image.shape[1] + int(left) + int(right)
            )
            if pixelek > plafon:
                tulmeretes.append(("copyMakeBorder", pixelek))
                raise _TulmeretesFoglalas("copyMakeBorder")
            return eredeti_border(image, top, bottom, left, right, *args, **kwargs)

        csere.setattr(frame_ops.cv2, "copyMakeBorder", figyelo_border)
        yield tulmeretes


def _futtat(
    eset: _RenderEset, monkeypatch, fuzz_keret, kihagyas_meres, caplog
):
    kep = np.zeros(
        (eset.magassag, eset.szelesseg, eset.csatornak), dtype=np.uint8
    )
    plafon = _pixelplafon(eset.magassag * eset.szelesseg)
    with _figyel_tultermeseket(monkeypatch, plafon) as tulmeretes:
        with fuzz_keret():
            jelent = apply_filters(kep, (FilterOp(eset.nev, eset.parameterek),))
    kihagyas_meres(jelent.skipped)
    assert not tulmeretes, f"túlméretes foglalási kérés: {tulmeretes}"
    for rekord in caplog.records:
        if rekord.exc_info:
            kivetel = rekord.exc_info[1]
            assert not isinstance(kivetel, MemoryError), "a renderlánc memóriahiányba futott"
            assert "alloc" not in str(kivetel).casefold()
            assert "memory" not in str(kivetel).casefold()
    assert isinstance(jelent.image, np.ndarray)
    assert jelent.image.dtype == np.uint8
    assert jelent.image.ndim in (2, 3)
    assert jelent.image.shape[0] * jelent.image.shape[1] <= plafon
    return jelent


@example(_RenderEset("Border", (), 1, 1, 3))
@example(_RenderEset("Border", ("1",), 1, 1, 4))
@example(_RenderEset("Border", ("1", "nan"), 3, 2, 3))
@example(_RenderEset("Border", ("1", "inf"), 5, 7, 4))
@example(_RenderEset("Border", ("1", "1e9"), 48, 64, 3))
@example(_RenderEset("Border", ("1", "5000"), 48, 64, 3))
@example(_RenderEset("Border", ("1", "20000"), 48, 64, 3))
@example(_RenderEset("MuseumMatte", ("1", "20000"), 48, 64, 3))
@example(
    _RenderEset(
        "DropShadow",
        ("1", "1e9", "90", "10", "00000000", "00ffffff", "30"),
        48,
        64,
        3,
    )
)
@given(eset=_render_esetek())
def test_apply_filters_hibas_parameterekkel_es_kepalakkal_is_korlatozott(
    eset, monkeypatch, fuzz_keret, fuzz_kihagyas_merese, caplog
):
    _futtat(eset, monkeypatch, fuzz_keret, fuzz_kihagyas_merese, caplog)


def test_minden_renderelheto_regiszterszuro_lefut_kis_rgb_es_rgba_kepen(
    monkeypatch, fuzz_keret, fuzz_kihagyas_merese, caplog
):
    for nev in _RENDERELHETO:
        for csatornak in (3, 4):
            _futtat(
                _RenderEset(nev, ("1",), 2, 3, csatornak),
                monkeypatch,
                fuzz_keret,
                fuzz_kihagyas_merese,
                caplog,
            )


def test_a_6581_korpusz_minden_sorat_keretor_vizsgalja(
    monkeypatch, fuzz_keret, fuzz_kihagyas_merese, caplog
):
    for sor in _KORPUSZ:
        op = parse_filters(sor)[0]
        _futtat(
            _RenderEset(op.name, op.params, 48, 64, 3),
            monkeypatch,
            fuzz_keret,
            fuzz_kihagyas_merese,
            caplog,
        )


@pytest.mark.parametrize("ertek", ("nan", "inf", "-inf"))
def test_border_nem_veges_parametere_nem_kerul_ki_a_float_feldolgozas_elott(
    ertek, monkeypatch, fuzz_keret, fuzz_kihagyas_merese, caplog
):
    jelent = _futtat(
        _RenderEset("Border", ("1", ertek), 48, 64, 3),
        monkeypatch,
        fuzz_keret,
        fuzz_kihagyas_merese,
        caplog,
    )
    assert jelent.skipped == ()


def test_a_foglalasfigyelo_a_6581_rontaskontrolljanal_megallitja_a_memoriakerest(
    monkeypatch, fuzz_keret
):
    import picasapy.render.glimmer_frame_ops as frame_ops

    kep = np.zeros((48, 64, 3), dtype=np.uint8)
    plafon = _pixelplafon(48 * 64)
    monkeypatch.setattr(frame_ops, "_ellenoriz_keret_kimenetet", lambda *_args: None)
    with _figyel_tultermeseket(monkeypatch, plafon) as tulmeretes:
        with fuzz_keret(), pytest.raises(_TulmeretesFoglalas):
            frame_ops.add_ring(kep, 20_000, (0, 0, 0))
    assert tulmeretes and tulmeretes[0][0] == "copyMakeBorder"
