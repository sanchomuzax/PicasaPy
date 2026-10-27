"""A Kép ▸ Csoportos szerkesztés tételei VALÓDI egérkattintással (#5150, 3. rész).

Minden tétel a Kép fejlécére, majd a Csoportos szerkesztés almenüjének sorára
kattintva indul (`QTest.mouseClick`). A hatást a kijelölt képek `.picasa.ini`
láncán és a `rotate_steps` állapoton mérjük; a kijelöletlen kép érintetlenségét
is ellenőrizzük. A közös segédek a `_mappa_kep_menu_5150_helpers.py`-ban vannak.

Már lefedett tételek (ezeket itt nem ismételjük):
- `menuBatchRename`: test_batch_edit_menu_4701.py:68
- `menuBatchSepia`, `menuBatchBlackWhite`: test_photo_menu_commands.py:315
- `menuPictureBatchEdit` (almenü): test_photo_menu_commands.py:117

Setup-only: a `menuBatchWarmify` a test_szerkesztes_menu_valodi_5150_b.py
előkészítő lépése, de csak azt nézi, hogy a lánc nem üres. Itt a `warm=1;`
kulcsot ellenőrizzük, tételspecifikusan.
"""

from __future__ import annotations

import pytest

from support.qt_wait import wait_for_photo_op
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    kijelol,
    szures,
    tetel_kattintasa,
    varj,
)

_KIJELOLT_SOROK = [0, 1]
_KIJELOLETLEN_SOR = 2

#: a forgatás-tétel és a várt `rotate_steps` (óramutató szerint 1, ellenkezőleg 3)
_FORGATASOK = (
    ("menuBatchRotateRight", 1),
    ("menuBatchRotateLeft", 3),
)

#: az effekt-tétel és a lemezre írt `filters=` kulcs (a redeye értékét régió követi)
_EFFEKTEK = (
    ("menuBatchAutoContrast", "autolight=1;"),
    ("menuBatchAutoColor", "autocolor=1;"),
    ("menuBatchEnhance", "enhance=1;"),
    ("menuBatchSharpen", "unsharp2=1,0.600000;"),
    ("menuBatchWarmify", "warm=1;"),
    ("menuBatchFilmGrain", "grain2=1;"),
    ("menuBatchAutoRedeye", "redeye="),
)


@pytest.fixture
def kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _kotegelt_tetel(window, qt_app, controller, nev: str) -> None:
    """Kép ▸ Csoportos szerkesztés ▸ `nev` valódi kattintásokkal; a háttérmunka
    végét megvárjuk, mert a kötegelt effekt az ini-fájlba ír."""
    wait_for_photo_op(
        controller,
        lambda: tetel_kattintasa(
            window, qt_app, "&Picture", nev,
            almenu_utvonal=("menuPictureBatchEdit",),
        ),
        qt_app=qt_app,
    )


class TestKotegeltForgatas:
    @pytest.mark.parametrize(("nev", "lepes"), _FORGATASOK)
    def test_a_forgatas_valodi_kattintassal_a_kijelolt_kepeket_forgatja(
        self, kep_app, qt_app, nev, lepes
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, _KIJELOLT_SOROK)
        assert controller.photos.photos[0].rotate_steps == 0, (
            "a kiinduló forgatás nem nulla: a teszt nem bizonyít"
        )

        _kotegelt_tetel(window, qt_app, controller, nev)

        assert varj(
            qt_app, lambda: controller.photos.photos[0].rotate_steps == lepes
        ), f"a {nev} kattintás nem forgatta a kijelölt képet {lepes} lépéssel"
        assert controller.photos.photos[_KIJELOLETLEN_SOR].rotate_steps == 0, (
            "a kijelöletlen kép is elfordult"
        )


class TestKotegeltEffektek:
    @pytest.mark.parametrize(("nev", "kulcs"), _EFFEKTEK)
    def test_az_effekt_valodi_kattintassal_a_kijelolt_kepekre_kerul(
        self, kep_app, qt_app, nev, kulcs
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, _KIJELOLT_SOROK)
        assert all(kulcs not in szures(controller, sor) for sor in _KIJELOLT_SOROK), (
            f"a {kulcs} már a kiinduló láncban van: a teszt nem bizonyít"
        )

        _kotegelt_tetel(window, qt_app, controller, nev)

        assert varj(
            qt_app,
            lambda: all(kulcs in szures(controller, sor) for sor in _KIJELOLT_SOROK),
        ), (
            f"a {nev} kattintás nem írta a {kulcs} szűrőt a kijelölt képekre: "
            f"{[szures(controller, sor) for sor in _KIJELOLT_SOROK]}"
        )
        if nev == "menuBatchSharpen":
            assert all(szures(controller, sor) == kulcs for sor in _KIJELOLT_SOROK), (
                "a Sharpen nem a kért pontos filters= értéket írta: "
                f"{[szures(controller, sor) for sor in _KIJELOLT_SOROK]}"
            )
        assert kulcs not in szures(controller, _KIJELOLETLEN_SOR), (
            "a kijelöletlen kép is kapta az effektet"
        )
