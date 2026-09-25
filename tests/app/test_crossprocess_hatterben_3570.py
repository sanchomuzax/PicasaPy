"""#3570 — a Cross Process (Áttűnés) a felület szála helyett HÁTTÉRBEN fut.

## A mérés

A #22 mérőszkriptje a Raspberry Pi 5-ön, a szerkesztő előnézeti
felbontásán (2560 × 1707): **2399 ms** medián — a #3452 óta háromszor
lassabb. A lánc végi fényesség-tartó színezés (`tint_luma_preserving`)
maga ~1,8 s; a lánc minden lépése pontonkénti.

## Miért nem a regiszter `slow` jelzője

A regiszter (`render/registry_data.py`) az eredeti `filterdesc.xml`
MÁSA, és ott a `CrossProcess` nem lassú. A jelzőt átírva az eredeti
adatát hamisítanánk meg. A lassúság a MI megvalósításunk költsége,
ezért a döntés is a miénk: a szerkesztő saját, mért listája
(`EditController.SAJAT_LASSU_SZUROK`).

## Miért nem gyorsítás

A bitre azonos kimenet a jegy feltétele. A sávos párhuzamosítás (négy
magon) bitre azonos, de csak 1,7-szeres (2,3 s → 1,4 s — a memória-
sávszélesség a korlát), a 100 ms-os célt nem éri el.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from picasapy.ini.filters import FilterOp


@pytest.fixture
def vezerlo(qt_app, tmp_path):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from support.jpeg_factory import make_jpeg

    kep = make_jpeg(tmp_path / "IMG_1.jpg", size=(64, 48))
    ctl = EditController(EditPreviewProvider())
    ctl.beginEdit("1", str(kep))
    yield ctl
    ctl.cancelPendingPreview()
    ctl.waitForBackgroundWorkers(10.0)


def _hatterben_futott(ctl, hivas) -> bool:
    elotte = len(ctl._bg_worker_set())
    hivas()
    return len(ctl._bg_worker_set()) > elotte


def test_az_attunes_hatterbe_megy(vezerlo):
    vezerlo._session = replace(
        vezerlo._session, ops=(FilterOp("crossprocess", ("1", "0")),)
    )

    assert _hatterben_futott(vezerlo, vezerlo._register_preview), (
        "a Cross Process a felület szálán renderelt — ~2,4 s-ra megállna"
    )


def test_masik_szuro_utan_is_hatterbe_megy(vezerlo):
    """A lánc bármely pontján elég egy lassú szűrő."""
    vezerlo._session = replace(
        vezerlo._session,
        ops=(FilterOp("sepia", ("1",)), FilterOp("crossprocess", ("1", "0"))),
    )

    assert _hatterben_futott(vezerlo, vezerlo._register_preview)


def test_a_regiszter_jelzoje_valtozatlan():
    """Az eredeti `filterdesc.xml` adata nem sérülhet: a regiszter szerint
    a Cross Process továbbra sem lassú."""
    from picasapy.render.registry import chain_flags

    _teljes, lassu, _ujrameretez = chain_flags(["crossprocess"])

    assert lassu is False
