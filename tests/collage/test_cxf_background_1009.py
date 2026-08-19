"""A `.cxf` KÉPHÁTTERE — `<background type="image"><src>…</src></background>` (#1009).

A #431 csak az egyszínű hátteret ismerte
(`<background type="solid" color="FFFFFFFF"/>`), mert a spec 1.6-os mintája
olyan volt. A golden-anyag két képhátteres kollázsa (`AI2.cxf`, `AI5.cxf`,
privát repó `referencia/kollazs-golden/`) most megmutatta a MÁSIK alakot, és
az meglepetést tartogat:

```
 <background type="image">
  <src>$My Pictures\\AI\\2a655925-….png</src>
 </background>
```

**A `color` attribútum ilyenkor NINCS OTT** — nem üres, nem alapérték:
hiányzik. Aki „az egyszínű alakhoz hozzáír egy `<src>`-t", olyan fájlt ír,
amilyet az eredeti Picasa soha nem írt.

A két minta bájtra pontosan ezt az alakot tartalmazza (egy szóköz behúzás a
`<background>`-on, kettő a `<src>`-en, CRLF sorvégek).
"""

from __future__ import annotations

import pytest

from picasapy.collage.cxf import CxfBackground, CxfNode, CxfProject, dumps, loads

#: A golden `AI2.cxf` / `AI5.cxf` háttér-részlete, karakterre.
KEPHATTER_RESZLET = (
    ' <background type="image">\r\n'
    "  <src>$My Pictures\\AI\\2a655925-cb0c-4fc0-828c-6d0107a9ba20.png</src>\r\n"
    " </background>\r\n"
)

MINTA_SRC = "$My Pictures\\AI\\2a655925-cb0c-4fc0-828c-6d0107a9ba20.png"


def _projekt(hatter: CxfBackground) -> CxfProject:
    return CxfProject(
        background=hatter,
        nodes=(
            CxfNode(
                x=0.1, y=0.2, w=0.3, h=0.4, theta=0.0, scale=337.0, src=MINTA_SRC
            ),
        ),
    )


class TestIras:
    def test_a_kephatter_a_golden_alakjaban_megy_ki(self):
        szoveg = dumps(_projekt(CxfBackground(type="image", src=MINTA_SRC))).decode(
            "utf-8"
        )
        assert KEPHATTER_RESZLET in szoveg

    def test_a_kephatteren_NINCS_color_attributum(self):
        """A golden két mintája sem tartalmazza — ez a lényegi különbség."""
        szoveg = dumps(_projekt(CxfBackground(type="image", src=MINTA_SRC))).decode(
            "utf-8"
        )
        hatter_sor = next(s for s in szoveg.splitlines() if "<background" in s)
        assert "color" not in hatter_sor

    def test_az_egyszinu_hatter_alakja_valtozatlan(self):
        """A #431 szerződése nem sérülhet: `src` nélkül önzáró elem, színnel."""
        szoveg = dumps(_projekt(CxfBackground(type="solid", color="FFFFFFFF"))).decode(
            "utf-8"
        )
        assert ' <background type="solid" color="FFFFFFFF"/>\r\n' in szoveg

    def test_az_utvonal_XML_szerint_vedve_megy_ki(self):
        szoveg = dumps(
            _projekt(CxfBackground(type="image", src="C:\\a&b\\<x>.png"))
        ).decode("utf-8")
        assert "<src>C:\\a&amp;b\\&lt;x&gt;.png</src>" in szoveg


class TestOlvasas:
    def test_a_src_visszaolvasodik(self):
        projekt = loads(dumps(_projekt(CxfBackground(type="image", src=MINTA_SRC))))
        assert projekt.background.type == "image"
        assert projekt.background.src == MINTA_SRC

    def test_korjarat_bajtra_pontos(self):
        eredeti = _projekt(CxfBackground(type="image", src=MINTA_SRC))
        assert dumps(loads(dumps(eredeti))) == dumps(eredeti)

    def test_a_src_nelkuli_hatter_ures_marad(self):
        projekt = loads(dumps(_projekt(CxfBackground(type="solid", color="FF203040"))))
        assert projekt.background.src == ""
        assert projekt.background.color == "FF203040"

    def test_ekezetes_utvonal_is_atmegy(self):
        """A kimenet ékezetes mappába megy (#190) — a `.cxf` UTF-8."""
        eredeti = _projekt(CxfBackground(type="image", src="/képek/nyár őszi.png"))
        assert loads(dumps(eredeti)).background.src == "/képek/nyár őszi.png"


class TestErvenyesites:
    def test_ismeretlen_tipus_tovabbra_is_hibat_dob(self):
        with pytest.raises(ValueError):
            CxfBackground(type="csillamos")

    def test_a_kephatter_szin_nelkul_is_ervenyes(self):
        """A golden így írja; az alapértelmezett szín csak tartalék."""
        assert CxfBackground(type="image", src=MINTA_SRC).color == "FF000000"
