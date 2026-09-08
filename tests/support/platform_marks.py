"""Platform-kapuk teszt-jelölésekhez (#1864).

## Miért közös modul

A `chmod`-dal előállított hibahelyzetek **Windowson nem állnak elő**: ott az
`os.chmod` csak a „csak olvasható" attribútumot állítja, azt pedig a rendszer
a MAPPÁKRA nézve figyelmen kívül hagyja (fájlokra érvényesíti). Az ilyen
tesztek Windowson vagy elbuknak, vagy — rosszabb esetben — más okból lesznek
zöldek.

2026-09-01-ig négy export-hibaág minden PR-en elbukott a windows-lábon, és
nem tűnt fel, mert az a láb `continue-on-error` (#1864). Ez a modul azért van,
hogy a jelölés EGY helyen legyen kimondva, ne fájlonként újra megfogalmazva —
és hogy a `tests/test_chmod_platform_kapu_1864.py` kapuja fel tudja ismerni.
"""

from __future__ import annotations

import os

import pytest

#: A `chmod`-ra épülő próbák kapuja: Windowson a POSIX-bitek nem
#: érvényesülnek, rendszergazdaként pedig nem korlátoznak.
csak_posix_jogosultsag = pytest.mark.skipif(
    os.name != "posix" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason=(
        "#1864: a chmod Windowson a POSIX-biteket nem érvényesíti (mappára a "
        "csak-olvasható attribútum sem hat), rendszergazdaként pedig a bitek "
        "nem korlátoznak — a hibahelyzet nem áll elő"
    ),
)

__all__ = ["csak_posix_jogosultsag"]
