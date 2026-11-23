"""#7380: a szöveg a megadott pont ALATT áll, a bal széle a ponton.

Az eredeti Picasa a `text=` pozícióját a SZÖVEGDOBOZ bal felső sarkának
veszi (job-839 `__26`: a kattintott (600,400) pontnál a betűk pixelei
x 601-651, y 402-407, vagyis a pont ALATT). A korábbi rajzolónk a pontot az
ALAPVONALNAK vette, ezért a betűk a pont FÖLÖTT álltak.

A próbák a három rajzolóúton futnak (Hershey, Pillow/TrueType, Qt), és nem
konkrét képpont-mintát, hanem a HELYZETET állítják: nincs festék a pont
fölött, a festék teteje a pont közelében kezdődik, a bal széle a ponton.
A betűkép gépenként eltér, ezért a hézag a betűmérethez mért tűréssel áll.
"""

from __future__ import annotations

import numpy as np
import pytest

import picasapy.render.text_overlay as text_overlay
from picasapy.render.text_overlay import apply_text_overlay

# a job-839 képe: 1024 x 256, a kattintás a képen (0,316406 ; 0,144531)
_MAGASSAG = 256
_SZELESSEG = 1024
_X = 0.316406
_Y = 0.144531
_PONT_X = round(_X * _SZELESSEG)
_PONT_Y = round(_Y * _MAGASSAG)
_TARTALOM = "PicasaPy7327"
_MERET_PT = 12  # 12 * 256 / 360 = 8,5 -> 9 képpont a képen


def _vaszon() -> np.ndarray:
    return np.zeros((_MAGASSAG, _SZELESSEG, 3), dtype=np.uint8)


def _festek(kep: np.ndarray) -> tuple[int, int, int, int]:
    """A festékes képpontok befoglalója: (felső sor, alsó sor, bal, jobb)."""
    maszk = kep.sum(axis=-1) > 0
    sorok = np.nonzero(maszk.any(axis=1))[0]
    oszlopok = np.nonzero(maszk.any(axis=0))[0]
    assert sorok.size > 0, "semmi nem rajzolódott ki"
    return (
        int(sorok.min()), int(sorok.max()),
        int(oszlopok.min()), int(oszlopok.max()),
    )


def _rajzol(**kwargs) -> np.ndarray:
    return apply_text_overlay(
        _vaszon(), _TARTALOM, _X, _Y,
        font_size_pt=_MERET_PT, color=(255, 255, 255), **kwargs,
    )


def _allitsd_pont_alatt(kep: np.ndarray) -> None:
    felso, also, bal, jobb = _festek(kep)
    meret_px = text_overlay.betumeret_keppontban(_MERET_PT, _MAGASSAG)
    assert felso >= _PONT_Y - 1, (
        f"a festék teteje ({felso}) a pont ({_PONT_Y}) FÖLÖTT van: "
        "a pont alapvonalként viselkedik"
    )
    assert felso <= _PONT_Y + meret_px // 2, (
        f"a festék teteje ({felso}) messze a pont ({_PONT_Y}) alatt kezdődik"
    )
    assert also <= _PONT_Y + 2 * meret_px, "a szöveg túl messzire nyúlik le"
    assert _PONT_X - 1 <= bal <= _PONT_X + 3, (
        f"a bal szél ({bal}) nem a ponton ({_PONT_X}) áll"
    )
    assert jobb > bal


class TestPontAlattiHorgony:
    def test_pillow_truetype_ut(self) -> None:
        """Qt nélkül a Pillow-út fut (ha van TrueType a gépen)."""
        if text_overlay.load_font(text_overlay.DEFAULT_FAMILY, 9) is None:
            pytest.skip("nincs használható TrueType betű: a Hershey-út próbája fedi")
        _allitsd_pont_alatt(_rajzol())

    def test_hershey_ut(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(text_overlay, "load_font", lambda *a, **k: None)
        _allitsd_pont_alatt(_rajzol())

    @pytest.mark.usefixtures("qt_app", "renderelo_betuk")
    def test_qt_ut(self) -> None:
        _allitsd_pont_alatt(_rajzol())

    @pytest.mark.usefixtures("qt_app", "renderelo_betuk")
    def test_qt_ut_nagyobb_meretnel_is_a_pont_alatt(self) -> None:
        """A méret nő, a festék teteje akkor is a pont közelében marad (nem
        a betűmérettel arányosan csúszik FEL, mint az alapvonalnál)."""
        kicsi = _rajzol()
        nagy = apply_text_overlay(
            _vaszon(), _TARTALOM, _X, _Y,
            font_size_pt=48, color=(255, 255, 255),
        )
        felso_kicsi = _festek(kicsi)[0]
        felso_nagy = _festek(nagy)[0]
        assert felso_nagy >= _PONT_Y - 1
        assert abs(felso_nagy - felso_kicsi) <= 12

    @pytest.mark.usefixtures("qt_app", "renderelo_betuk")
    def test_igazitas_kozepre_es_jobbra_is_pont_alatt(self) -> None:
        for igazitas in ("center", "right"):
            kep = _rajzol(align=igazitas)
            felso = _festek(kep)[0]
            assert felso >= _PONT_Y - 1, igazitas
