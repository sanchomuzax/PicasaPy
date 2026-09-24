"""#3353 — az XMP-névterek: mit ír ki az eredeti, és mit írunk MI.

## A mérés (bájtszintű pásztázás a szállított `Picasa3.exe`-n)

| minta | találat |
|---|---:|
| `ns.adobe.com/lightroom` | **0** |
| `Iptc4xmpExt` | 2 |

A két `Iptc4xmpExt`-találat helye dönti el a jelentését:

⚠️ **HELYESBÍTÉS a kör közben:** az első olvasatom az volt, hogy az
`Iptc4xmpExt` az Adobe XMP-SDK szokásos névtér-készletének része. A spec 12/B
szakasza (#3348) ezt megdönti: az eredeti a SAJÁT NÉGY regisztrációja közé
veszi fel, és a teljes IPTC Extension sémát is bejegyzi (21 tulajdonság,
`0xbafe00`–`0xbb0300`). A regisztráció tehát szándékos.

A döntést nem a bináris, hanem a **saját exportja** hozta meg: a
`684-merokeszlet/export` 40 és a `3229-lanc-sorrend/export` 4 képében a kiírt
XMP-csomag PONTOSAN három névteret tartalmaz (`xmp`, `exif`, `dc`), és
`Iptc4xmpExt`/`PersonInImage`/`mwg-rs`/`MicrosoftPhoto` egyikben sem szerepel.

A mért exportokon nem volt nevesített arc — az `mwg-rs` hiánya ezért NEM
jelenti, hogy arcos képnél is hiányozna (#1403 épp azt mérte, hogy arcokhoz az
`mwg-rs`/`MP` megy). A `PersonInImage` viszont a megnevezett arc mellett SEM
íródik: a binárisból eldöntve (#3424, spec 12/E) a név a régió `Name`
mezőjébe kerül, a `PersonInImage`-et a Picasa csak olvassa.

## A két döntés, amit ez a fájl őriz

* **`lr:` MARAD** — tudatos, az eredetiben nem létező kiegészítés, mert a
  hierarchikus címke csak így jut el egy digiKam/Lightroom-olvasóhoz. A kód
  ezt ki is mondja; ez a próba azt őrzi, hogy a kimondás ott is maradjon.
* **`Iptc4xmpExt` NEM kerül a kimenetbe** — nincs mit pótolni.

⚠️ Amit ez a fájl NEM mér: hogy egy valódi Picasa-export tartalmaz-e
IPTC-tulajdonságot. A bizonyíték a binárisból való; egy ellenkező irányú
export-lelet új mérés és új jegy.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.export.xmp as xmp_modul
from picasapy.export.xmp import XmpImageMetadata, XmpRegion, build_xmp

_FORRAS = Path(xmp_modul.__file__).read_text(encoding="utf-8")


def _csomag() -> str:
    return build_xmp(
        XmpImageMetadata(
            keywords=("Nyár", "Anna"),
            hierarchical=("People|Anna",),
            caption="Egy felirat",
            regions=(XmpRegion(name="Anna", x=0.5, y=0.4, w=0.2, h=0.25),),
        )
    )


class TestAmitKIIRUNK:
    def test_a_lr_nevter_BENNE_van(self):
        """A döntés: marad — a hierarchikus címke máshogy nem jut el."""
        csomag = _csomag()
        assert "http://ns.adobe.com/lightroom/1.0/" in csomag
        assert "lr:hierarchicalSubject" in csomag

    def test_az_Iptc4xmpExt_NEM_kerul_a_kimenetbe(self):
        csomag = _csomag()
        assert "Iptc4xmpExt" not in csomag
        assert "iptc.org/std" not in csomag

    def test_a_MERT_nevterek_benne_vannak(self):
        """Amit az eredeti tényleg ÍR: mwg-rs és MP (#1403)."""
        csomag = _csomag()
        assert "http://www.metadataworkinggroup.com/schemas/regions/" in csomag
        assert "http://ns.microsoft.com/photo/1.2/" in csomag


class TestADontesAKODBANisLATSZIK:
    """#3353 elfogadási feltétele: a döntés ne csak a jegyben álljon.

    ⚠️ Ez FORRÁS-szintű állítás — azt őrzi, hogy a magyarázat ott maradjon,
    nem azt, hogy igaz. A mérés maga a jegyben és a specben van.
    """

    def test_a_lr_mellett_ott_all_hogy_nem_eredeti(self):
        assert "_NS_LR" in _FORRAS
        # a döntés kimondva: tudatos, az eredetiben nem létező kiegészítés
        assert "nulla" in _FORRAS and "lightroom" in _FORRAS
        assert "#3353" in _FORRAS

    def test_az_Iptc4xmpExt_hianya_INDOKOLVA_van(self):
        assert "Iptc4xmpExt" in _FORRAS, (
            "a hiányt nem elég megtenni, ki is kell mondani — különben a "
            "következő kör újra felveti"
        )
        # a kimondás lényege: a regisztráció nem írás, ÉS a megnevezett arc
        # sem kerül `PersonInImage` alá — a #3424 óta binárisból eldöntve,
        # tehát a negatív állítás hatókör nélkül igaz
        assert "NEM írás" in _FORRAS or "nem írás" in _FORRAS
        assert "megnevezett arc SEM" in _FORRAS
        assert "0x00bb17e0" in _FORRAS

    def test_a_MERES_hivatkozasa_ott_van_a_nevterek_mellett(self):
        assert "picasa-metaadat-tulajdonsagok.md" in _FORRAS
