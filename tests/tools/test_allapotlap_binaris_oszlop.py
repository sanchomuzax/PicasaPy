"""A blokkolt jegyek harmadik oszlopa: amit bináris kutatás old fel.

A tulajdonos kérdése az állapotlapon (2026-08-27): „Ezek közül melyikre
érdemes bináris kutatást indítani? Az lehetne egy 3. oszlop?"

A besorolás NEM vélemény és nem szövegelemzés, hanem a jegyen rögzített
`bináris-kutatható` CÍMKE — ugyanúgy, ahogy a `blocked` és a
`felhasználóra-vár` is az. A lap változatlanul csak mér.
"""

from __future__ import annotations

import sys
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GYOKER / "scripts"))

from allapotlap import epits  # noqa: E402
from kutatas_elszamolas import _osszesit  # noqa: E402


def _jegy(szam: int, cim: str, *cimkek: str) -> dict:
    return {"number": szam, "title": cim, "labels": list(cimkek), "createdAt": "",
            "updatedAt": "", "comments": 0}


BLOKKOLT_KUTATHATO = _jegy(1153, "A Klipek fül feltárása", "blocked", "bináris-kutatható")
BLOKKOLT_FELHASZNALOS = _jegy(684, "Golden-mappa exportja", "blocked")
NEM_BLOKKOLT_KUTATHATO = _jegy(999, "Nyitott kutatás", "ready", "bináris-kutatható")


class TestOsszesites:
    def test_a_cimkezett_blokkolt_bekerul(self):
        ossz = _osszesit([BLOKKOLT_KUTATHATO, BLOKKOLT_FELHASZNALOS])
        assert [i["number"] for i in ossz["binaris_kutathato"]] == [1153]

    def test_a_cimke_nelkuli_blokkolt_kimarad(self):
        ossz = _osszesit([BLOKKOLT_FELHASZNALOS])
        assert ossz["binaris_kutathato"] == []

    def test_a_nem_blokkolt_kutathato_kimarad(self):
        """A harmadik oszlop a BLOKKOLTAK részhalmaza — a nyitott, dolgozható
        jegyek nem tartoznak az „Ez vár rád" szakaszba."""
        ossz = _osszesit([NEM_BLOKKOLT_KUTATHATO])
        assert ossz["binaris_kutathato"] == []
        assert ossz["blokkolt"] == []


class TestLap:
    def _adat(self, jegyek: list[dict]) -> dict:
        from datetime import datetime, timezone
        return {"menu": {"viselkedes": [], "erdemi": [], "csak_nev": [], "sehol": []},
                "kovetkezo": [], "jegyek": jegyek,
                "ossz": _osszesit(jegyek), "erintetlen": [],
                "spec": {"lapok": 0, "sorok": 0}, "spec_kerdesek": [],
                "ideje": datetime(2026, 8, 27, tzinfo=timezone.utc)}

    def test_a_lapon_megjelenik_a_harmadik_oszlop(self):
        # ⚠️ #1664/#1681: a szakasz címei megváltoztak, mert a régi
        # „Ez vár rád" cím ellentmondott a tartalmának, és a két csoport
        # DUPLÁN sorolta ugyanazt a jegyet. A csoport itt már particionált:
        # „Ebből bináris kutatás…" → „Bináris kutatás oldja fel".
        lap = epits(self._adat([BLOKKOLT_KUTATHATO, BLOKKOLT_FELHASZNALOS]))
        assert "Bináris kutatás oldja fel" in lap
        assert "#1153" in lap

    def test_a_cimke_nelkuli_nem_kerul_a_harmadik_oszlopba(self):
        """A #684-et a felhasználó exportja oldja fel, nem visszafejtés —
        a „Külső akadályon áll" csoportban ott van, a harmadikban nem."""
        lap = epits(self._adat([BLOKKOLT_FELHASZNALOS]))
        harmadik = lap.split("Bináris kutatás oldja fel", 1)[1]
        assert "#684" not in harmadik.split("</div>", 2)[0]
        assert "#684" in lap

    def test_egy_jegy_CSAK_EGY_csoportban_szerepel(self):
        """#1664: a duplázás volt a jelentett hiba — ez őrzi, hogy ne térjen
        vissza. A `bináris-kutatható` jegy a harmadik csoportba tartozik, a
        „Külső akadályon áll" listából KI kell maradnia."""
        lap = epits(self._adat([BLOKKOLT_KUTATHATO, BLOKKOLT_FELHASZNALOS]))
        szakasz = lap.split("Mi áll, és kin múlik", 1)[1].split("</section>", 1)[0]
        assert szakasz.count("#1153") == 1, (
            "a bináris-kutatható jegy KÉTSZER szerepel a szakaszban (#1664)"
        )
        assert szakasz.count("#684") == 1
