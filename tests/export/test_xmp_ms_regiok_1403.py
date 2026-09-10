"""A Microsoft Photo 1.2 arcrégió-blokk az XMP-ben (#1403).

## Miért kell a MÁSODIK séma

A Picasa mindkét arcrégió-szabványt kiírja: az `mwg-rs`-t (ezt a #1798 köre
már megépítette) és a `MicrosoftPhoto` 1.2-t. A kettő nem váltja ki egymást —
az olvasók egyik vagy másik ágat ismerik (a Windows Fotógaléria és a
Photoshop Elements a Microsoft-félét, a digiKam/Lightroom az mwg-rs-t).

## A csapda: MÁSHOL van a téglalap origója

| | `mwg-rs` (`stArea`) | `MicrosoftPhoto` (`MPReg:Rectangle`) |
|---|---|---|
| x, y | a régió **KÖZÉPPONTJA** | a régió **BAL FELSŐ** sarka |
| alak | négy attribútum | EGY szöveg, `x, y, w, h` |

Ezért `bal = x − w/2`, `felső = y − h/2`. Ha valaki a középpontot írja a
Microsoft-blokkba, a Windows Fotógaléria a NÉGYSZERES területű, elcsúszott
régiót mutatná — és a mi mwg-rs blokkunk mellett ez fel sem tűnne.
"""

from __future__ import annotations

from picasapy.export.xmp import XmpImageMetadata, XmpRegion, build_xmp


def _xmp(regiok, meret=(1000, 800)) -> str:
    return build_xmp(
        XmpImageMetadata(regions=tuple(regiok), dimensions=meret)
    )


class TestAMicrosoftBlokk:
    def test_a_blokk_es_a_nevterek_ott_vannak(self):
        szoveg = _xmp([XmpRegion(name="Anna", x=0.5, y=0.5, w=0.2, h=0.2)])

        assert "<MP:RegionInfo" in szoveg
        assert 'xmlns:MPReg="http://ns.microsoft.com/photo/1.2/t/Region#"' in szoveg
        assert "<MPReg:PersonDisplayName>Anna</MPReg:PersonDisplayName>" in szoveg

    def test_a_teglalap_a_BAL_FELSO_sarokbol_indul(self):
        """A középpont (0,5; 0,5) és a 0,2×0,2 méret bal felső sarka 0,4/0,4."""
        szoveg = _xmp([XmpRegion(name="Anna", x=0.5, y=0.5, w=0.2, h=0.2)])

        assert "<MPReg:Rectangle>0.4, 0.4, 0.2, 0.2</MPReg:Rectangle>" in szoveg, (
            "a Microsoft-blokkba a BAL FELSŐ sarok megy, nem a középpont — "
            "különben a Windows Fotógaléria elcsúszott régiót mutat"
        )

    def test_a_kep_szelere_csuszo_regio_nem_megy_negativba(self):
        szoveg = _xmp([XmpRegion(name="Bori", x=0.05, y=0.05, w=0.2, h=0.2)])

        assert "<MPReg:Rectangle>0, 0, 0.2, 0.2</MPReg:Rectangle>" in szoveg

    def test_az_mwg_blokk_VALTOZATLAN_marad(self):
        """A második séma nem nyúl az elsőhöz: ott továbbra is a KÖZÉPPONT áll."""
        szoveg = _xmp([XmpRegion(name="Anna", x=0.5, y=0.5, w=0.2, h=0.2)])

        assert 'stArea:x="0.5" stArea:y="0.5"' in szoveg
        assert 'stArea:unit="normalized"' in szoveg

    def test_regio_nelkul_egyik_blokk_sem_epul_fel(self):
        szoveg = build_xmp(XmpImageMetadata(keywords=("nyár",)))

        assert "MP:RegionInfo" not in szoveg
        assert "mwg-rs:Regions" not in szoveg

    def test_ket_regio_ket_teteld(self):
        szoveg = _xmp(
            [
                XmpRegion(name="Anna", x=0.25, y=0.25, w=0.1, h=0.1),
                XmpRegion(name="Bori", x=0.75, y=0.75, w=0.1, h=0.1),
            ]
        )

        assert szoveg.count("<MPReg:PersonDisplayName>") == 2
        assert "<MPReg:Rectangle>0.2, 0.2, 0.1, 0.1</MPReg:Rectangle>" in szoveg
        assert "<MPReg:Rectangle>0.7, 0.7, 0.1, 0.1</MPReg:Rectangle>" in szoveg
