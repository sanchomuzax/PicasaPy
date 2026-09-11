"""#1935 — a webalbum-feltöltő gombok SZÁNDÉKOSAN nincsenek meg.

Az eredeti szerkesztő-fejlécben két, egymást kizáró gomb ül ugyanazon a
helyen (`editpanel/quickupload` és `editpanel/uploadchanges`, mindkettő
34 × 22, `m_hidden`). A mögöttük álló szolgáltatás — a Google Web Albums és
annak „Drop Box" mappája — **megszűnt**.

**A tulajdonos döntése (2026-09-10, #1935, képernyőképpel):**

> „Ez egy nem működő, hibás funkcióra vezető gomb. Jelenleg ne
> implementáljuk, csak dokumentáljuk, ha majd lesz újra bármiféle »Feltöltés a
> Webalbumok Főalbum mappájába« szerű funkció."

⚠️ Ez FELÜLÍRJA a 2026-09-05-i korábbi döntést („legyenek ott szürkén"). A
szürke gomb is ígéret: ott áll a felületen egy vezérlő, ami nem működő
funkcióra vezet.

Ez az őr azt tartja fenn, hogy egy későbbi kör **ne építse meg** — sem élőn,
sem tiltva —, és hogy a döntés dokumentuma a helyén legyen. A mérés maga a
specben él (`docs/specs/szerkeszto-felso-sav.md` 2. és 4. szakasz), azt ez a
próba nem duplikálja.

Döntés: `docs/decisions/nincs-webalbum-feltoltes-gomb.md` (ADR-012).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import picasapy.app

_QML_DIR = Path(picasapy.app.__file__).parent / "qml"
_DONTES = (
    Path(picasapy.app.__file__).parents[2].parent
    / "docs" / "decisions" / "nincs-webalbum-feltoltes-gomb.md"
)

#: a két MÉRT elemnév — ezekre nem születhet vezérlő
TILTOTT_NEVEK = ("quickupload", "uploadchanges")


def _minden_qml() -> list[Path]:
    return sorted(_QML_DIR.rglob("*.qml"))


class TestNincsVezerlo:
    @pytest.mark.parametrize("nev", TILTOTT_NEVEK)
    def test_a_forrasban_nincs_ilyen_vezerlo(self, nev):
        """A puszta szó előfordulhat KOMMENTBEN (a döntés magyarázata), de
        `objectName`-ként nem: az már vezérlő volna."""
        talalatok = [
            f"{ut.name}"
            for ut in _minden_qml()
            if f'objectName: "{nev}' in ut.read_text(encoding="utf-8")
        ]
        assert talalatok == [], (
            f"megépült egy `{nev}` vezérlő: {talalatok} — a #1935 tulajdonosi "
            "döntése szerint ez a gomb NEM készül el, se élőn, se szürkén"
        )

    def test_a_dontes_lapja_a_helyen_van(self):
        """A hiány kimondott döntés — ha a lap eltűnik, a hiány elmaradásnak
        látszik, és egy következő kör megépíti."""
        assert _DONTES.exists(), f"nincs meg a döntés lapja: {_DONTES}"
        szoveg = _DONTES.read_text(encoding="utf-8")
        assert "ADR-012" in szoveg
        assert "quickupload" in szoveg
        assert "2026-09-10" in szoveg, "a döntés dátuma nem szerepel"

    def test_a_dontes_KIMONDJA_hogy_a_szurke_gomb_sem_jo(self):
        """A korábbi döntés („legyenek ott szürkén") felülírása maga is
        bizonyíték: enélkül egy következő kör a régi sort követné."""
        szoveg = _DONTES.read_text(encoding="utf-8")
        assert "felülírja" in szoveg
        assert "szürkén" in szoveg
