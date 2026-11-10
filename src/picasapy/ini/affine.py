"""2x3-as affin leképezés típusa és az azonossági mátrix (#6688).

A szerkesztő vezérlője a vörösszem-panel állapotában az azonossági mátrixszal
indul, és ezt az indulás kritikus útján olvassa. A `picasapy.render.
chain_geometry` (ahonnan a nevek eredetileg jöttek) importja a teljes
`picasapy.render` csomagot behúzná, ami az első ablakkép előtt nem fér bele,
ezért a két név itt, a könnyű `ini` rétegben él; a `chain_geometry` innen
veszi át és újraexportálja őket.
"""

from __future__ import annotations

#: 2×3-as affin mátrix: `((a, b, c), (d, e, f))`, azaz
#: `x' = a·x + b·y + c`, `y' = d·x + e·y + f`.
Matrix = tuple[tuple[float, float, float], tuple[float, float, float]]

AZONOSSAG: Matrix = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
