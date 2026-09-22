"""#3478: az effektcsempe a kanonikus ini-nevet használja.

A #1141 óta a lánc a nem kanonikus írásmódú nevet — az eredeti bejárójához
hűen — kihagyja. A csempe korábban a kisbetűs belső kulcsot adta
műveletnévnek (`border`), így a nagybetűs nevű effektek (`Border`,
`Vignette`, `DropShadow`…) csempéje a módosítatlan fotót mutatta.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.app.effect_thumbnails import _KNOWN_EFFECTS, _default_op
from picasapy.ini.filter_registry import is_exact_filter_name
from picasapy.render import apply_filters


@pytest.mark.parametrize("effekt", sorted(_KNOWN_EFFECTS))
def test_a_csempe_muveletneve_kanonikus_es_nem_marad_ki(effekt):
    op = _default_op(effekt)
    assert is_exact_filter_name(op.name), f"{effekt}: nem kanonikus név ({op.name!r})"
    kep = np.full((60, 80, 3), 128, dtype=np.uint8)
    kep[20:40, 30:50] = (200, 60, 40)
    jelentes = apply_filters(kep, (op,))
    assert op.name not in jelentes.skipped, f"{effekt}: a lánc kihagyta"


def test_a_szegely_csempe_tenyleg_keretet_rajzol():
    kep = np.full((150, 200, 3), 128, dtype=np.uint8)
    kimenet = apply_filters(kep, (_default_op("border"),)).image
    assert kimenet.shape[:2] != kep.shape[:2]
