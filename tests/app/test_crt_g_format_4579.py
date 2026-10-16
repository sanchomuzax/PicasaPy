"""#4579: az eredeti CRT `%.3g` / `%g` kerekítése (spec 17. szakasz, A).

A pontos fél érték a nullától ELKEREKEDIK (22.25 -> 22.3), a Python
`format(x, ".3g")` viszont párosra (22.2) — ezért saját formázó kell."""

import pytest

from picasapy.app.crt_g_format import crt_g, picasa_szam


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (22.25, "22.3"),
        (1.125, "1.13"),
        (0.03125, "0.0313"),
        (4.97, "4.97"),
        (5.0, "5"),
        (22.35, "22.4"),
        (998.6, "999"),
        (22.2504, "22.3"),
        (0.0, "0"),
    ],
)
def test_harom_ertekes_jegy_felertek_a_nullatol_el(value, expected):
    assert crt_g(value, 3) == expected


def test_negativ_ertek_szimmetrikus():
    assert crt_g(-1.125, 3) == "-1.13"


def test_kitevos_alak_haromjegyu_kitevovel():
    assert crt_g(1000.0, 1) == "1e+003"
    assert crt_g(1e6, 1) == "1e+006"
    assert crt_g(1e-5, 1) == "1e-005"


def test_g_hat_ertekes_jegy():
    assert crt_g(1234567.0, 6) == "1.23457e+006"
    assert crt_g(1000.0, 6) == "1000"
    assert crt_g(0.5, 6) == "0.5"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (4.97, "4.97"),
        (5.0, "5"),
        (1.125, "1.13"),
        (0.01, "0.01"),
        (999.0, "999"),
        (1000.0, "1000"),  # %g: 6 értékes jegy, nincs kitevő
        (0.005, "0.005"),
        (1234567.0, "1.23457e+006"),
    ],
)
def test_picasa_szam_kuszobok(value, expected):
    assert picasa_szam(value) == expected
