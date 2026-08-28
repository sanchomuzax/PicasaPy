"""A lap mutassa meg, MI TÖRTÉNT — nem csak azt, hol tartunk. #1695

A tulajdonos szava (2026-08-28): *„Az artifact egyik fő célja, hogy az ember
(én) lássam, mi történt az éjszaka. Kiment pár release, és semmit sem látok
ebből olvasható módon, a githubot kell böngésszem."*

A lap addig kizárólag ÁLLAPOTOT mutatott (nyitott jegyek, lefedettség,
rothadás). Négy kiadás és tizenhét lezárt jegy után is ugyanúgy nézett ki —
tehát a munka nem látszott rajta. Ez a szakasz ezt pótolja.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GYOKER / "scripts"))

from allapotlap import epits  # noqa: E402
from kutatas_elszamolas import _osszesit  # noqa: E402

KIADASOK = [
    {"verzio": "v0.8.132", "mikor": "2026-08-28 04:36"},
    {"verzio": "v0.8.131", "mikor": "2026-08-28 03:39"},
]
LEZART = [
    {"number": 1667, "title": "Az exportcélok visszavétele 8,4 másodpercet visz el",
     "labels": {"bug", "P0"}, "closed": "2026-08-28T01:30:00Z"},
    {"number": 1654, "title": "Tesztüzem mód",
     "labels": {"enhancement"}, "closed": "2026-08-28T00:10:00Z"},
]


def _adat(kiadasok=None, lezart=None) -> dict:
    return {
        "menu": {"viselkedes": [], "erdemi": [], "csak_nev": [], "sehol": []},
        "kovetkezo": [], "jegyek": [], "ossz": _osszesit([]), "erintetlen": [],
        "spec": {"lapok": 0, "sorok": 0}, "spec_kerdesek": [],
        "kiadasok": KIADASOK if kiadasok is None else kiadasok,
        "frissen_lezart": LEZART if lezart is None else lezart,
        "ideje": datetime(2026, 8, 28, tzinfo=timezone.utc),
    }


class TestASzakaszMegjelenik:
    def test_a_kiadasok_lathatok_verzioval_es_idoponttal(self):
        lap = epits(_adat())
        assert "Mi történt" in lap
        assert "v0.8.132" in lap
        assert "2026-08-28 04:36" in lap

    def test_a_lezart_jegyek_szammal_es_cimmel_lathatok(self):
        lap = epits(_adat())
        assert "#1667" in lap
        assert "8,4 másodpercet visz el" in lap

    def test_a_szakasz_a_lap_ELEJEN_van(self):
        """A történés fontosabb, mint a rothadás-mutató — ne kelljen görgetni."""
        lap = epits(_adat())
        assert lap.index("Mi történt") < lap.index("A rothadás")


class TestUresAllapot:
    def test_adat_nelkul_a_szakasz_KIMARAD(self):
        """Üres szakasz rosszabb, mint semmi: azt sugallná, hogy nem történt
        semmi, holott csak a lekérdezés hiúsult meg."""
        lap = epits(_adat(kiadasok=[], lezart=[]))
        assert "Mi történt" not in lap

    def test_csak_kiadas_eseten_is_megjelenik(self):
        lap = epits(_adat(lezart=[]))
        assert "Mi történt" in lap
        assert "Az elmúlt napban egy sem." in lap
