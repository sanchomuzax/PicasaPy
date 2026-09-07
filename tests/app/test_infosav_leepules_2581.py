"""#2581 — a kék infó-sáv KÉTLÉPCSŐS leépülése, a MÉRT szabály szerint.

## A mérés (a teljes levezetés: `docs/specs/kek-info-sav.md` 9.)

Két Picasa 3 felvétel, UGYANAZ a fájl, UGYANAZ a nézet, más ablakszélesség:

| felvétel | ablak | a név mezője |
|---|---|---|
| `picasa3-felirat-bekapcsolva. 223224.jpg` | 1920 | `AI > JonasBen_…0a71328.png` **teljesen**, 544 px |
| `141421.jpg` (A/B, bal fél) | ≈960 | `JonasBen_he_sits_...0a71328.png`, **149 px** |

Hogy a betű azonos, a SZOMSZÉD mezők bizonyítják (dátum 98, felbontás 85,
méret 31 képpont — mindkét felvételen ugyanannyi). Ebből:

1. a szabály **képpont**-alapú (karakterszabály mellett ugyanúgy csonkulna
   mindkettő);
2. a leépülés **kétlépcsős**: előbb a `mappa > ` előtag marad el, és csak
   utána vág a névbe — a vágott alak NEM az előtaggal kezdődik;
3. a vágás a név **közepén**, három ASCII ponttal (`…` U+2026 literál a
   binárisban NINCS).

## Miért QJSEngine, és miért SZINTETIKUS betű

A szabály a `infosav.js`-ben él, mert a `TrayBar.qml`-ből nem lehetne
külön mérni. A szélesség-mérést a hívó adja be függvényként — itt egy
determinisztikus, karakterenként fix szélességű „betűt" adunk. Így a
próba nem függ attól, milyen betű van a futtató gépen, és pontosan azt
állítja, amit a mérés kimondott: a szabály a SZÉLESSÉGET nézi.

⚠️ Amit ez a fájl NEM állít: a fej/far arányt szerződésként. A mért
84 / 142 = 59,2 % a 60/40-be fér bele, miközben az 50/50 és a 2/3–1/3
kizárva — a próba ezt a KIZÁRÁST méri, nem a pontos arányt.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtQml import QJSEngine

_JS = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "infosav.js"
).read_text(encoding="utf-8")

#: A felvételen mért valódi név és előtag.
NEV = (
    "JonasBen_he_sits_on_a_ladder_above_the_clouds_with_a_fishing-ro"
    "_0291672e-b6c3-4582-8195-fdadc0a71328.png"
)
ELOTAG = "AI > "
MEZOK = "   2023. 05. 10. 16:30:05   896x1344 képpont   807 KB"
TELJES = ELOTAG + NEV + MEZOK

#: A szintetikus betű: minden karakter ennyi képpont.
KARAKTER_SZELESSEG = 5


@pytest.fixture
def js(qt_app):
    """A `infosav.js` egy JS-motorban, szintetikus szélesség-mérővel.

    ⚠️ A `qt_app` KELL: `QCoreApplication` nélkül a `QJSEngine` SIGSEGV-vel
    áll meg (a projekt visszatérő csapdája).
    """
    engine = QJSEngine()
    engine.installExtensions(QJSEngine.Extension.AllExtensions)
    # a `.pragma library` sor a modul-alakhoz kell, a sima kiértékeléshez nem
    forras = _JS.replace(".pragma library", "")
    engine.evaluate("var InfoSav = (function () {\n" + forras + """
        return {lecsokkentve: lecsokkentve, elotagNelkul: elotagNelkul,
                nevKozepenVagva: nevKozepenVagva, HAROMPONT: HAROMPONT,
                FEJ_ARANY: FEJ_ARANY}
    })()""")
    engine.evaluate(
        "var szelesseg = function (s) { return s.length * %d }"
        % KARAKTER_SZELESSEG
    )
    return engine


def _hivd(engine, szoveg: str, hely: float) -> str:
    engine.globalObject().setProperty("_sz", szoveg)
    engine.globalObject().setProperty("_h", hely)
    ertek = engine.evaluate("InfoSav.lecsokkentve(_sz, _h, szelesseg)")
    assert not ertek.isError(), ertek.toString()
    return ertek.toString()


class TestElfer:
    """Ha kifér, semmi nem történik — az előtag is marad."""

    def test_a_bo_helyen_valtozatlan(self, js):
        hely = len(TELJES) * KARAKTER_SZELESSEG + 100
        assert _hivd(js, TELJES, hely) == TELJES

    def test_a_pontosan_elfero_szoveg_is_valtozatlan(self, js):
        hely = len(TELJES) * KARAKTER_SZELESSEG
        assert _hivd(js, TELJES, hely) == TELJES

    def test_az_ures_szoveg_ures_marad(self, js):
        assert _hivd(js, "", 10) == ""


class TestElsoLepcso:
    """Ha nem fér ki, ELŐBB a `mappa > ` előtag marad el."""

    def test_az_eloteg_elmarad_a_nev_erintese_nelkul(self, js):
        elotag_nelkul = NEV + MEZOK
        hely = len(elotag_nelkul) * KARAKTER_SZELESSEG
        kapott = _hivd(js, TELJES, hely)
        assert kapott == elotag_nelkul, (
            "az előtag elhagyása az ELSŐ lépcső — a névbe csak utána szabad "
            f"vágni (kapott: {kapott!r})"
        )
        assert InfoSav_harompont(js) not in kapott

    def test_a_datumban_levo_jel_nem_teveszti_meg(self, js):
        """A `>` szerepelhet más mezőben is — csak az ELSŐ mező számít."""
        szoveg = "kep.png   2023 > 2024   807 KB"
        hely = (len(szoveg) - 1) * KARAKTER_SZELESSEG
        kapott = _hivd(js, szoveg, hely)
        assert "2023 > 2024" in kapott, (
            f"a második mező `>` jelét is előtagnak vette: {kapott!r}"
        )


def InfoSav_harompont(engine) -> str:
    return engine.evaluate("InfoSav.HAROMPONT").toString()


class TestMasodikLepcso:
    """Ha az előtag elhagyása sem elég, a NÉV KÖZEPÉN vág."""

    def _vagott(self, js, hely: float) -> str:
        return _hivd(js, TELJES, hely)

    def test_a_harompont_a_NEV_kozepere_kerul(self, js):
        kapott = self._vagott(js, 149 + len(MEZOK) * KARAKTER_SZELESSEG)
        nev_mezo = kapott.split("   ")[0]
        assert "..." in nev_mezo, f"nincs vágás a névben: {kapott!r}"
        fej, far = nev_mezo.split("...", 1)
        assert fej and far, (
            f"a vágás a név SZÉLÉN történt, nem a közepén: {nev_mezo!r}"
        )

    def test_a_kiterjesztes_megmarad(self, js):
        """A felvételen `…0a71328.png` áll — a far a név VÉGE."""
        nev_mezo = self._vagott(
            js, 149 + len(MEZOK) * KARAKTER_SZELESSEG
        ).split("   ")[0]
        assert nev_mezo.endswith(".png"), (
            f"a kiterjesztés lemaradt: {nev_mezo!r}"
        )

    def test_a_fej_a_nev_ELEJE(self, js):
        nev_mezo = self._vagott(
            js, 149 + len(MEZOK) * KARAKTER_SZELESSEG
        ).split("   ")[0]
        fej = nev_mezo.split("...")[0]
        assert NEV.startswith(fej), (
            f"a fej nem a név eleje: {fej!r}"
        )

    def test_a_TOBBI_mezo_erintetlen(self, js):
        """A vágás CSAK a nevet éri — a dátum és a méret nem csonkulhat."""
        kapott = self._vagott(js, 149 + len(MEZOK) * KARAKTER_SZELESSEG)
        assert kapott.endswith(MEZOK.strip()), (
            f"a többi mező is sérült: {kapott!r}"
        )

    def test_a_vegeredmeny_BEFER(self, js):
        """Minden olyan szélességen, ahol a TÖBBI mező még kifér."""
        legkisebb = (len(MEZOK) + 4) * KARAKTER_SZELESSEG
        for hely in (legkisebb, legkisebb + 60, legkisebb + 200, 900):
            kapott = self._vagott(js, hely)
            assert len(kapott) * KARAKTER_SZELESSEG <= hely + 1e-6, (
                f"{hely} képpontra {len(kapott) * KARAKTER_SZELESSEG} "
                f"képpontnyi szöveg jött vissza: {kapott!r}"
            )

    def test_a_VEGLETESEN_szuk_helyen_a_nev_puszta_harompont(self, js):
        """A többi mezőhöz nem nyúlunk — ott a sáv clipje vág (#1934).

        Az eredeti sem rövidíti a dátumot vagy a méretet: a `.tre`
        `infotext_clip`-je vágja le, ami nem fér ki. A név viszont ilyenkor
        sem tarthat meg semmit — marad a puszta jel.
        """
        kapott = self._vagott(js, 40)
        assert kapott.split("   ")[0] == "...", (
            f"a név nem csökkent a minimumra: {kapott!r}"
        )
        assert kapott.endswith(MEZOK.strip()), (
            f"a többi mezőt is bántotta: {kapott!r}"
        )


class TestAzAranyKizarasa:
    """A mérés két kerek arányt KIZÁR — a próba ezt a kizárást őrzi.

    A felvételen a fej 84, a far 58 képpont (a hárompont nélkül 142).
    Ha az arány 50/50 volna, a fej 71 lenne; ha 2/3–1/3, akkor 94,7. A
    mért 84 egyikkel sem fér össze, a 60/40-gyel (85,2) igen.
    """

    def test_a_fej_HOSSZABB_a_farnal(self, js):
        nev_mezo = _hivd(
            js, TELJES, 149 + len(MEZOK) * KARAKTER_SZELESSEG
        ).split("   ")[0]
        fej, far = nev_mezo.split("...", 1)
        assert len(fej) > len(far), (
            f"a fej ({len(fej)}) nem hosszabb a farnál ({len(far)}) — "
            "az 50/50 arányt a mérés kizárta"
        )

    def test_az_arany_a_MERT_savban_van(self, js):
        nev_mezo = _hivd(
            js, TELJES, 149 + len(MEZOK) * KARAKTER_SZELESSEG
        ).split("   ")[0]
        fej, far = nev_mezo.split("...", 1)
        arany = len(fej) / (len(fej) + len(far))
        assert 0.55 <= arany <= 0.65, (
            f"a fej aránya {arany:.2f}; a mért 0,59 (a felvételen 84/142), "
            "az 50/50 és a 2/3–1/3 kizárva"
        )
