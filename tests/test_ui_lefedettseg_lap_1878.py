"""A lap és az olvasója NE csúszhasson el egymástól (#1878).

Az UI-lefedettségi mérő a **privát** `picasapy-agent` repóban él, a lapot
viszont ez a repó tárolja (`docs/specs/ui-lefedettseg.md`), és a
`scripts/ui_lefedettseg_lap.py` olvassa vissza az állapotlaphoz. A kettő
külön repóban lévő, **szövegen keresztül összekötött** pár — pontosan az a
felállás, ahol a törés néma marad.

⚠️ MÉRT eset: amikor a generátor az összesítő tábla „hiányzik" sorát
„hiányzik — **feltáratlan** (kutatói kör kell)"-re bővítette, az olvasó
pontos kulcsegyezése **0-t** adott. Az állapotlapon ez „nincs több hiány"
formában, HAMIS JAVULÁSKÉNT jelent volna meg. A teszt ezt fogja meg.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GYOKER / "scripts"))

import ui_lefedettseg_lap as lap  # noqa: E402


class LapEsOlvasoOsszhangTeszt(unittest.TestCase):
    def setUp(self):
        if not lap.LAP_UT.is_file():
            self.skipTest(f"nincs commitolt lap: {lap.LAP_UT}")
        self.szoveg = lap.LAP_UT.read_text(encoding="utf-8")

    def test_minden_kotelezo_kulcs_megvan_a_lapon(self):
        """Ez bukik, ha a generátor átnevez egy összesítő-sort."""
        hianyzo = lap.hianyzo_kulcsok(self.szoveg)
        self.assertEqual(
            hianyzo, (),
            "A lap összesítő táblájából hiányzó kulcs(ok): "
            f"{hianyzo}. Az olvasó ilyenkor NÉMÁN 0-t adna, és az "
            "állapotlapon hamis javulás látszana. Vagy a generátort "
            "állítsd vissza, vagy a KOTELEZO_KULCSOK prefixeit igazítsd.",
        )

    def test_a_szamok_nem_nemak(self):
        """A kiolvasott számok ne legyenek mind nullák.

        Egy elrontott minta minden mezőre 0-t adna — a lap ilyenkor
        „minden kész”-t mutatna. A párosítva és a bizonytalan a mai
        mérésben biztosan pozitív.
        """
        meres = lap.olvas()
        self.assertIsNotNone(meres)
        self.assertGreater(meres.parositva, 0, "a párosítva 0 — gyanús")
        self.assertGreater(
            meres.hianyzik + meres.lekutatva + meres.bizonytalan, 0,
            "minden hiány-szám 0 — a lap vagy az olvasó elromlott",
        )

    def test_a_ket_hiany_kulon_szam(self):
        """#1878 lényege: a feltáratlan és a lekutatva NEM ugyanaz a mező."""
        meres = lap.olvas()
        self.assertTrue(hasattr(meres, "lekutatva"))
        self.assertIsInstance(meres.lekutatva, int)


if __name__ == "__main__":
    unittest.main()
