"""#921 — a `snap_9` −90°-ot tárol, és a szögfelirat negált.

Két apró, de MÉRHETŐ eltérés, ami a windowsos Picasával való oda-vissza
olvasásban jelentkezik:

1. A `snap_9` nálunk `270.0` fokot tárolt, a binárisban **`−90.0f`**.
   Rajzban ugyanaz, tárolásban NEM: a `.cxf`-be `−1,570796` kerül
   `4,712389` helyett.
2. A húzás közben kiírt szöget a Picasa a megjelenítés előtt **negálja**
   (`fchs`); nálunk előjelhelyesen ment ki.

A helyi menü „270 fok" felirata a MEGJELENÍTETT szöveg, nem a tárolt
érték — a kettő összekeverése okozta az eredeti hibát.
"""

from __future__ import annotations

import math

import pytest

from picasapy.collage.canvas import SNAP_COMMANDS, angle_caption_degrees, snap_theta


class TestSnapSzogek:
    @pytest.mark.parametrize(
        ("parancs", "fok"),
        [("snap_12", 0.0), ("snap_3", 90.0), ("snap_6", 180.0), ("snap_9", -90.0)],
    )
    def test_a_negy_parancs_a_binaris_konstansaival(self, parancs, fok):
        """A címek: 0x0082e0e9 · 0xcf4370 · 0xcf409c · 0xcf50d0."""
        assert SNAP_COMMANDS[parancs] == fok
        assert snap_theta(parancs) == pytest.approx(math.radians(fok))

    def test_a_snap_9_NEGATIV_nem_270(self):
        """Ez a jegy lényege: rajzban ugyanaz, tárolásban nem."""
        assert snap_theta("snap_9") == pytest.approx(-1.5707964, abs=1e-6)
        assert snap_theta("snap_9") != pytest.approx(math.radians(270.0))

    def test_ismeretlen_parancs_hibat_dob(self):
        with pytest.raises(ValueError, match="Ismeretlen forgatás-igazító"):
            snap_theta("snap_7")


class TestSzogfelirat:
    @pytest.mark.parametrize(
        ("radian", "vart"),
        [(math.pi / 2, -90), (-math.pi / 2, 90), (0.0, 0), (math.pi, -180)],
    )
    def test_a_felirat_NEGALT(self, radian, vart):
        """A Picasa a kiírás előtt `fchs`-sel negál (0x00868944)."""
        assert angle_caption_degrees(radian) == vart

    def test_a_snap_9_felirata_270_kent_olvasodik(self):
        """A tárolt −90 fok feliratként +90-et ad; a menü „270 fok" szövege
        ettől független, rögzített felirat."""
        assert angle_caption_degrees(snap_theta("snap_9")) == 90
