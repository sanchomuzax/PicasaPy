"""#4224: a Vámpírszem bélyegének alfa-profilja ecsetkeménység szerint."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.app.paint_mask import Vonas, maszk_vonasokbol
from picasapy.ini.filters import parse_filters


PROFILOK = {
    0.0: (
        (
            0,
            0.029239766,
            0.048274282,
            0.067308798,
            0.124412335,
            0.181515887,
            0.219584912,
            0.257653952,
            0.40993005,
            0.4860681,
            0.543171644,
            0.600275218,
            0.695447743,
            0.866758406,
            1,
        ),
        (0, 0, 0, 2, 12, 32, 50, 69, 155, 189, 208, 223, 240, 252, 255),
    ),
    0.15: (
        (
            0,
            0.171069175,
            0.187322721,
            0.203576267,
            0.25233689,
            0.301097542,
            0.333604634,
            0.366111726,
            0.496140063,
            0.561154246,
            0.609914899,
            0.658675551,
            0.739943266,
            0.886225164,
            1,
        ),
        (0, 0, 0, 2, 12, 32, 50, 69, 155, 189, 208, 223, 240, 252, 255),
    ),
    0.5: (
        (
            0,
            0.48120302,
            0.491375506,
            0.501547992,
            0.532065451,
            0.56258291,
            0.582927942,
            0.603272915,
            0.684652805,
            0.725342751,
            0.755860269,
            0.786377728,
            0.83724016,
            0.928792596,
            1,
        ),
        (0, 0, 0, 2, 12, 32, 50, 69, 155, 189, 208, 223, 240, 252, 255),
    ),
}

HARD_ROWS = {
    20: (241, *(255 for _ in range(18)), 225, 0),
    40: (248, *(255 for _ in range(38)), 232, 0),
}


def _token(value: float) -> str:
    return format(value, ".9g")


def _ops(records: tuple[str, ...]):
    return parse_filters(
        "ReanimatedEyeColor=1,6,20," + ",".join(records) + ";"
    )


def _ini_rekord(kemenyseg: float = 0.5) -> str:
    return f"1.000000:0.5:0:0:20:{_token(kemenyseg)}:0.5|0.5"


def _ini_sor(kemenyseg: float = 0.5) -> str:
    return f"ReanimatedEyeColor=1,6,20,{_ini_rekord(kemenyseg)};"


@pytest.mark.parametrize("meret", (20, 40))
@pytest.mark.parametrize("kemenyseg", tuple(PROFILOK))
def test_az_ini_kemenysegprofilja_a_spec_15_mintapontjat_adja(
    meret: int, kemenyseg: float
):
    """A három mért interpolált profil 15 értéke mindkét ecsetméreten azonos."""
    u_ertekek, alfa_bajtok = PROFILOK[kemenyseg]
    magassag, szelesseg = 850, 100
    sugar = meret / 2
    cel_x = 50.5
    sorok = tuple(70 + index * 50 for index in range(len(u_ertekek)))
    rekordok = tuple(
        ":".join(
            (
                "1.000000",
                "0.5",
                "0",
                "0",
                str(meret),
                _token(kemenyseg),
                f"{_token((cel_x - sugar * (1 - u)) / szelesseg)}|"
                f"{_token((sor + 0.5) / magassag)}",
            )
        )
        for u, sor in zip(u_ertekek, sorok, strict=True)
    )
    maszk = maszk_vonasokbol(
        (), magassag, szelesseg, filters=_ops(rekordok)
    )

    assert maszk is not None
    kapott = tuple(
        int(round(float(maszk[sor, 50]) * 255)) for sor in sorok
    )
    assert kapott == alfa_bajtok


@pytest.mark.parametrize(("meret", "profil"), tuple(HARD_ROWS.items()))
def test_a_kemeny_ecset_teljes_kozepso_sora_a_spec_szerint(
    meret: int, profil: tuple[int, ...]
):
    """A külön h=1 ág mért teljes középső sora egyezzen 20/40 px-en."""
    rekord = "1.000000:0.5:0:0:" f"{meret}:1:0.5|0.5"
    maszk = maszk_vonasokbol(
        (), meret + 1, meret + 1, filters=_ops((rekord,))
    )

    assert maszk is not None
    kapott = tuple(
        int(round(float(alfa) * 255)) for alfa in maszk[meret // 2, :]
    )
    assert kapott == profil


def test_a_hianyzo_kemenyseg_alaperteke_015():
    vonas = Vonas(0.5, 0.5, 0.1)

    assert vonas.hardness == pytest.approx(0.15)


def test_a_fix_perem_rontas_kontrollja_elbukik_a_mert_015_profilon():
    u = 0.203576267
    tavolsag = 10 * (1 - u)
    vonas = Vonas((50.5 - tavolsag) / 100, 50.5 / 100, 0.1)

    maszk = maszk_vonasokbol((vonas,), 100, 100)

    assert maszk is not None
    assert int(round(float(maszk[50, 50]) * 255)) == 2


def test_az_elonezet_a_filters_sorbol_olvassa_a_vonasokat():
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.render.chain import apply_filters

    ys, xs = np.mgrid[0:60, 0:60]
    kep = np.stack(
        (
            (xs * 5 + ys * 3) % 256,
            (ys * 7 + 90) % 256,
            (200 - xs * 2) % 256,
        ),
        axis=-1,
    ).astype(np.uint8)
    ops = _ops((_ini_rekord(),))
    maszk = maszk_vonasokbol((), 60, 60, filters=ops)
    vart = apply_filters(kep, ops, paint_mask=maszk).image
    provider = EditPreviewProvider()

    kapott, _ = provider._futtasd_a_lancot("foto", kep, ops, False, ())

    np.testing.assert_array_equal(kapott, vart)


def test_a_mentes_a_filters_sorbol_olvassa_a_vonasokat(tmp_path):
    from picasapy.app.save_controller import _render_for_save
    from picasapy.lazy_cv2 import cv2
    from picasapy.render.chain import apply_filters

    kep = np.arange(60 * 90 * 3, dtype=np.uint8).reshape((60, 90, 3))
    ut = tmp_path / "foto.png"
    assert cv2.imwrite(str(ut), kep)
    sor = _ini_sor()
    ops = _ops((_ini_rekord(),))
    rgb = cv2.cvtColor(kep, cv2.COLOR_BGR2RGB)
    maszk = maszk_vonasokbol((), 60, 90, filters=ops)
    vart_rgb = apply_filters(rgb, ops, paint_mask=maszk).image
    vart = cv2.cvtColor(vart_rgb, cv2.COLOR_RGB2BGR)

    kapott = _render_for_save(ut, 0, sor)

    np.testing.assert_array_equal(kapott, vart)
