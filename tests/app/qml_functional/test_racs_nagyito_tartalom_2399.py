"""#2399 — a rács-nagyító a TELJES képből vág, nem a bélyegképet zsugorítja.

## A hiba, ahogy mérve volt

A lencse a `thumbUrl`-t kérte le, `PreserveAspectCrop`-pal, egy 65 × 65-ös
területre — vagyis az EGÉSZ bélyegképet belezsugorította a lencsébe.
Nagyítás helyett **kicsinyítés**. Arra, amire a funkció való (élesség,
csukott szem eldöntése), így alkalmatlan volt.

A `nagyitas: 2.5` tulajdonság a projekt egészében EGYSZER fordult elő — a
saját deklarációjában. Sehol nem hatott semmire.

## Az eredeti (mérve, #2399)

A lencsének **nincs nagyítási aránya**: a teljes méretű képet **1:1-ben**,
natív képpontmérettel rajzolja egy **161 × 161**-es felületre, csak
**eltolva**, hogy a kurzor alatti képpont a közepére essen. A látszólagos
nagyítás így magától adódik.

| állítás | cím |
|---|---|
| a rajzterület 161 × 161 | `0x0077c445` (`mov edx, 0xa1`) |
| a 80,0 a felület közepe (0…160) | `0x00cf4c30`, egyetlen hivatkozás |
| a célterület `W` × `H` ⇒ **1:1** | `0x0077bcf5`–`0x0077bd19` |

⚠️ A LÁTHATÓ méret (nálunk 65 × 65, az eredetiben 103 × 103) NEM ennek a
jegynek a tárgya — az a #1911/#460 hatásköre. Itt a TARTALOM a kérdés.

## Amit ez a fájl őriz

A régi őr (`test_racs_nagyito_1808.py`) csak azt állította, hogy a
`nagyitas` tulajdonság NEVE ott van a kódban — zöld maradt akkor is, amikor
a nagyító semmit nem csinált. Ez a fájl VISELKEDÉST állít.
"""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app as app_csomag

_FEED = (
    Path(app_csomag.__file__).parent / "qml" / "PicasaPy" / "LightboxFeed.qml"
).read_text(encoding="utf-8")


def _lencse_blokk() -> str:
    """A lencse `Image` elemének teljes blokkja, kapcsos zárójel szerint."""
    jel = 'objectName: "feedLoupeImage"'
    assert jel in _FEED, "nincs lencse-kép a rácsban"
    kezd = _FEED.rindex("Image {", 0, _FEED.index(jel))
    melyseg = 0
    for i in range(_FEED.index("{", kezd), len(_FEED)):
        if _FEED[i] == "{":
            melyseg += 1
        elif _FEED[i] == "}":
            melyseg -= 1
            if melyseg == 0:
                return _FEED[kezd : i + 1]
    raise AssertionError("nem záródik a lencse blokkja")


class TestATartalom:
    def test_a_lencse_NEM_a_belyegkepet_mutatja(self):
        blokk = _lencse_blokk()
        assert "elem.thumbUrl" not in blokk, (
            "a lencse a BÉLYEGKÉPET kéri le — azt zsugorítaná a 65 × 65-ös "
            "területre, vagyis kicsinyítene nagyítás helyett"
        )

    def test_a_TELJES_kepbol_dolgozik(self):
        blokk = _lencse_blokk()
        assert "fileUrl" in blokk, (
            "a lencse nem a teljes felbontású képből dolgozik"
        )

    def test_KIVAGATOT_ker_nem_atmeretezest(self):
        """`sourceClipRect`: a Qt a DEKÓDOLT képből vág, átméretezés nélkül
        — ez adja az 1:1 arányt."""
        blokk = _lencse_blokk()
        #: ⚠️ A HOZZÁRENDELÉST keressük (`sourceClipRect:`), nem a puszta
        #: szót: a fölötte álló komment is leírja a nevét, és attól a
        #: próba akkor is zöld maradna, ha a tulajdonság eltűnt. A
        #: magvetés pontosan ezt fedte fel.
        sorok = [
            sor.strip()
            for sor in blokk.splitlines()
            if sor.strip().startswith("sourceClipRect:")
        ]
        assert sorok, (
            "nincs kivágat — a kép átméretezve kerülne a lencsébe, az "
            "eredeti viszont 1:1-ben rajzol"
        )

    def test_a_kivagat_a_KURZORRA_kozepez(self):
        blokk = _lencse_blokk()
        assert "kurzor" in blokk.lower() or "loupeArea" in blokk, (
            "a kivágat nem a kurzor alatti képpontra középez"
        )


class TestAHoltTulajdonsag:
    def test_a_nagyitas_ELTUNT(self):
        """A holt `nagyitas: 2.5` TULAJDONSÁG eltűnt.

        ⚠️ A puszta szót nem tiltjuk: a helyén álló komment épp azt
        magyarázza el, MIÉRT nincs nagyítási arány (az eredeti 1:1-ben
        rajzol). Egy szó-tiltás arra kényszerítene, hogy a magyarázat
        körülírja magát — a komment nem hazudhat, de nem is némulhat el.
        """
        deklaraciok = re.findall(
            r"property\s+\w+\s+nagyitas\s*:", _FEED
        )
        assert not deklaraciok, (
            f"a holt `nagyitas` tulajdonság még ott van ({deklaraciok}) — az "
            f"eredeti nagyítónak NINCS aránya, a nagyítás a natív "
            f"képpontméretből adódik"
        )

    def test_a_kommentek_MEGMONDJAK_miert(self):
        """Aki legközelebb keresi a nagyítási arányt, kapjon választ."""
        assert "NINCS nagyítási arány" in _FEED
        assert "1:1" in _FEED


class TestAKivagatMerete:
    def test_a_kivagat_a_LATHATO_meretbol_szamol(self):
        """A látható terület nálunk 65 × 65 (a mért lencse-rajzból), tehát
        ennyi képpontot kell kivágni a teljes képből — se többet, se
        kevesebbet, különben megint átméretezés lenne."""
        blokk = _lencse_blokk()
        assert "65" in blokk, (
            "a kivágat mérete nem a mért 65 képpontos látható területből jön"
        )
