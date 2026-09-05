"""#2148 — a 7. (örökölt) fül bevezetője nem állíthat valótlant.

A régi mondat azt állította, hogy ezek a szűrők „nem érhetők el a mai
Picasában". A binárisból mérve ez **három elemre nem igaz**:

| örökölt kulcs   | hol érhető el a mai Picasában | bizonyíték |
|---|---|---|
| `radtint`       | 1. effekt-fül, 12. csempe (`dir_tint`), **Shifttel** | `0x00c7e5a0` tábla 12. rekordja |
| `autobacklight` | Alapvető javítások fül, egykattintásos gomb | `editpanel/autobacklight` → `call 0x6021d0` (`0x005d6848`) |
| `rainbow`       | Kiegyenesítés gomb + **ALT**                 | `push 0x12` (VK_MENU) → `push "rainbow"` (`0x005d6733`) |

A maradék 18-ra a mondat igaz: azokat a `0x008fc690` név-átfordító csak a
LÁNC BETÖLTÉSEKOR ismeri fel (`colorfix`/`triple*` → `finetune`/`finetune2`),
felületi vezérlőjük nincs.

Az őr a bevezető mondatot nézi — angolul és magyarul egyaránt.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

GYOKER = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app"
QML = GYOKER / "qml" / "PicasaPy" / "EditorLegacyTab.qml"
TS = GYOKER / "i18n" / "picasapy_hu.ts"


def _bevezeto_angol() -> str:
    """A `legacyEffectsIntro` `qsTr(...)` szövege a QML-ből.

    Az elemnévtől indulunk, és a hozzá tartozó blokk `text:` sorát vesszük —
    így a fájl bővülése (új elem elé vagy mögé) nem viszi ki az ablakból.
    """
    forras = QML.read_text(encoding="utf-8")
    kezdet = forras.index('objectName: "legacyEffectsIntro"')
    blokk = forras[kezdet : forras.index("}", kezdet)]
    talalat = re.search(r'text:\s*qsTr\("(.+?)"\)', blokk, re.S)
    assert talalat, "a legacyEffectsIntro blokkjában nincs qsTr() szöveg"
    return talalat.group(1)


def _bevezeto_magyar(angol: str) -> str:
    """Az angol mondathoz tartozó magyar fordítás a `.ts`-ből."""
    xml = TS.read_text(encoding="utf-8")
    keresett = angol.replace("'", "&apos;")
    kezdet = xml.index(keresett)
    talalat = re.search(r"<translation>(.*?)</translation>", xml[kezdet:], re.S)
    assert talalat, "a bevezetőhöz nincs <translation> a .ts-ben"
    return talalat.group(1)


#: Fordulatok, amelyek a mondatot valótlanná teszik: kizárólagos tagadás.
TILTOTT_ANGOL = ("not available in today", "are not available")
TILTOTT_MAGYAR = ("nem érhetők el", "nem érhetőek el", "nem elérhetők")


class TestABevezetoNemAllitValotlant:
    def test_az_angol_mondat_nem_zar_ki_mindent(self):
        mondat = _bevezeto_angol()
        for tiltott in TILTOTT_ANGOL:
            assert tiltott.lower() not in mondat.lower(), (
                f"a bevezető megint kizárólagosan tagad ({tiltott!r}), pedig a "
                "radtint, az autobacklight és a rainbow ma is elérhető"
            )

    def test_a_magyar_mondat_nem_zar_ki_mindent(self):
        magyar = _bevezeto_magyar(_bevezeto_angol())
        for tiltott in TILTOTT_MAGYAR:
            assert tiltott not in magyar, (
                f"a magyar bevezető megint kizárólagosan tagad ({tiltott!r})"
            )

    def test_a_mondat_tovabbra_is_megmondja_honnan_valok(self):
        """A pontosítás nem törölheti a fül LÉNYEGÉT."""
        mondat = _bevezeto_angol().lower()
        assert "older versions of picasa" in mondat

    def test_van_magyar_forditas(self):
        magyar = _bevezeto_magyar(_bevezeto_angol())
        assert magyar.strip() and "Picasa" in magyar


class TestAHaromKivetelAListabanMarad:
    """A három elérhető szűrő NEM kerül ki a fülről.

    A #2148 (a) útját választottuk: a mondat pontosul, a lista marad. Ha
    valaki mégis a (b) utat vinné végig (kivétel a listából), az tudatos
    döntés legyen, ne mellékhatás — ezért az őr kimondja.
    """

    @pytest.mark.parametrize("kulcs", ["radtint", "autobacklight", "rainbow"])
    def test_a_kulcs_a_fulon_marad(self, kulcs):
        from picasapy.render.legacy_effects import LEGACY_EFFECT_KEYS

        assert kulcs in LEGACY_EFFECT_KEYS
