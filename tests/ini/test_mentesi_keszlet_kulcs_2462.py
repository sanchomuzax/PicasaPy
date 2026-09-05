"""#2462: a mentés-készletenkénti `.picasa.ini` kulcs round-trip-je.

Spec: `docs/specs/biztonsagi-mentes.md` 9.2.

A Picasa a biztonsági mentéskor a kép szakaszába egy **készletenkénti**
testvérkulcsot ír a sima `backuphash` mellé, és a kulcs NEVE tartalmazza a
készlet nevét:

```ini
[photo01__bw.jpg]
filters=bw=1;
backuphash=40037
BKTag Saját mentési készlet-backuphash=40037
```

⚠️ **Termékhiba nincs** — a `document.py` ezt ma is helyesen kezeli. Ez a
fájl ŐR: a kulcsalak három olyan tulajdonságot hoz be, amit a meglévő
tesztek nem gyakoroltak, és amelyek bármelyike könnyen elveszne egy jövőbeli
„rendrakásnál":

1. **szóköz a kulcsnévben** — egy `strip()`-elő vagy tokenizáló olvasó
   szétvágná;
2. **ékezet** (`Saját`) — kódolás-érzékeny;
3. **kötőjel és a `backuphash` utótag** — egy előtag-alapú szűrő
   összetéveszthetné a sima `backuphash`-sel.

A minta a tulajdonos valódi, a Picasa 3.9.141.259 által írt fájljából való.
"""

from __future__ import annotations

from picasapy.ini.document import parse_document

#: A KÉSZLETENKÉNTI kulcs pontos alakja — szóközzel, ékezettel, kötőjellel.
_KESZLET_KULCS = "BKTag Saját mentési készlet-backuphash"

#: CRLF-fel, ahogy a Picasa írja.
_MINTA = (
    "[foto.jpg]\r\n"
    "filters=bw=1;\r\n"
    "backuphash=40037\r\n"
    f"{_KESZLET_KULCS}=40037\r\n"
)


class TestRoundTrip:
    def test_a_szerializalas_BITRE_azonos(self):
        """A round-trip a `.picasa.ini` alapszabálya (igazságforrás)."""
        assert parse_document(_MINTA).serialize() == _MINTA

    def test_a_kulcs_KIOLVASHATO(self):
        szakasz = parse_document(_MINTA).sections[0]
        assert szakasz.get(_KESZLET_KULCS) == "40037"

    def test_a_kulcssorrend_megmarad(self):
        szakasz = parse_document(_MINTA).sections[0]
        assert [k for k, _ in szakasz.items()] == [
            "filters",
            "backuphash",
            _KESZLET_KULCS,
        ]


class TestSzerkesztesUtanIsMegmarad:
    def test_a_filters_atirasa_nem_viszi_el(self):
        doc = parse_document(_MINTA).with_value("foto.jpg", "filters", "sepia=1;")
        szoveg = doc.serialize()
        assert f"{_KESZLET_KULCS}=40037" in szoveg
        assert "filters=sepia=1;" in szoveg

    def test_uj_kulcs_felvetele_nem_viszi_el(self):
        doc = parse_document(_MINTA).with_value("foto.jpg", "star", "yes")
        assert f"{_KESZLET_KULCS}=40037" in doc.serialize()


class TestATorlesNEMTEVESZTI_OSSZE:
    """A két kulcs KÜLÖN él — az egyik törlése nem viheti a másikat."""

    def test_a_SIMA_backuphash_torlese_meghagyja_a_keszletest(self):
        doc = parse_document(_MINTA).with_removed("foto.jpg", "backuphash")
        szoveg = doc.serialize()
        assert f"{_KESZLET_KULCS}=40037" in szoveg, (
            "a készletenkénti kulcs a sima `backuphash` törlésekor eltűnt — "
            "egy előtag- vagy utótag-alapú egyezés tévedett"
        )
        assert "\r\nbackuphash=40037" not in szoveg

    def test_a_KESZLETES_torlese_meghagyja_a_simat(self):
        doc = parse_document(_MINTA).with_removed("foto.jpg", _KESZLET_KULCS)
        szoveg = doc.serialize()
        assert "backuphash=40037" in szoveg
        assert _KESZLET_KULCS not in szoveg


class TestAKulcsnevHarom_TULAJDONSAGA:
    """Külön-külön is állítjuk, amit a kulcsalak behoz — így a bukás
    MEGNEVEZI, melyik tulajdonság veszett el."""

    def test_a_SZOKOZ_megmarad_a_kulcsnevben(self):
        szakasz = parse_document(_MINTA).sections[0]
        kulcsok = [k for k, _ in szakasz.items()]
        assert any(" " in k for k in kulcsok), (
            "egyetlen kulcsnévben sincs szóköz — az olvasó levágta vagy "
            "szétvágta a kulcsot"
        )

    def test_az_EKEZET_megmarad(self):
        szakasz = parse_document(_MINTA).sections[0]
        assert any("Saját" in k for k in [k for k, _ in szakasz.items()])

    def test_a_ket_backuphash_KULON_kulcs(self):
        szakasz = parse_document(_MINTA).sections[0]
        kulcsok = [k for k, _ in szakasz.items()]
        assert "backuphash" in kulcsok
        assert _KESZLET_KULCS in kulcsok
        assert len({k for k in kulcsok if k.endswith("backuphash")}) == 2
