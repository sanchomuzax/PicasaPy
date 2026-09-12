"""#819: a `slow` sáv-jelző a FELÜLET szálát védi.

## A lelet

A szűrő-regiszter **13 szűrőre** `slow` jelzőt ad. Ezek drága műveletek —
az eredeti külön szálon futtatja őket, jelzéssel. Nálunk a csúszka-húzás
útja (`_register_preview`) SZINKRON, tehát egy lassú effekt a felület
szálán számolt, és az ablak akadozott.

## Amit ez a próba mér

Melyik ÚTON megy a renderelés: a szinkron vagy a háttérszálas. A jelző
puszta értéke semmit nem bizonyít — a #819 első fele épp arról szólt, hogy
az adat megvolt, és nem történt tőle semmi.

⚠️ A háttér-út nem ingyen van: a kép csak a renderelés VÉGÉN frissül.
Ezért csak a `slow` láncoknál választjuk — a gyorsaknál a szinkron út ad
azonnali visszajelzést a csúszka alatt.
"""

from __future__ import annotations

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
    """Igaz, ha a hívás HÁTTÉRSZÁLAT indított."""
    elotte = len(ctl._bg_worker_set())
    hivas()
    return len(ctl._bg_worker_set()) > elotte


class TestASlowLanc:
    def test_a_lassu_szuro_HATTERBE_megy(self, vezerlo):
        """A `glow2` a 13 `slow` szűrő egyike (a `glow` NEM az)."""
        from dataclasses import replace

        vezerlo._session = replace(
            vezerlo._session, ops=(FilterOp("glow2", ("1", "0.5", "0.5")),)
        )

        assert _hatterben_futott(vezerlo, vezerlo._register_preview), (
            "a lassú lánc a felület szálán renderelt — az ablak akadozna"
        )

    def test_a_GYORS_lanc_szinkron_marad(self, vezerlo):
        """A csúszka alatt azonnali visszajelzés kell; a háttér-út csak a
        renderelés végén frissít."""
        from dataclasses import replace

        vezerlo._session = replace(
            vezerlo._session, ops=(FilterOp("sepia", ("1",)),)
        )

        assert not _hatterben_futott(vezerlo, vezerlo._register_preview)

    def test_URES_lanc_szinkron(self, vezerlo):
        assert not _hatterben_futott(vezerlo, vezerlo._register_preview)
