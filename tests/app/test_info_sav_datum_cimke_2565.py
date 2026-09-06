"""#2565 — a kék infó-sáv: DÁTUM és CÍMKÉK, számláló nélkül.

A mérés az A/B felvételről (`141421.jpg`, 2026-09-06 14:14 — bal: Picasa 3,
jobb: PicasaPy, ugyanaz a kép ugyanabban a nézetben):

    Picasa 3:  JonasBen_he_sits_…0a71328.png   2023. 05. 10. 16:30:05
               896x1344 képpont   807 KB   Címkék: AI image
    PicasaPy:  AI > JonasBen_…_0291672e-…png   896x1344 képpont   807 KB
               (427 / 82)

Három eltérés, három állítás ebben a fájlban:

1. **dátum** — EXIF felvételi idő híján a BEFAGYASZTOTT fájlidő
   (`PhotoRecord.sort_mtime_ns`, #2486). Ez volt a jegy nyitott kérdése; a
   `docs/specs/pmp-database.md` 10.1/10.3–10.4 válaszolta meg: a Picasa a
   beolvasáskori fájlidőt tartja a saját katalógusában, tehát EXIF nélkül is
   tud dátumot írni. A formátum a felvételről: `2023. 05. 10. 16:30:05` —
   rövid dátum + MÁSODPERCES idő, időzóna nélkül.
2. **címkék** — `Címkék: AI image`. Az előtag MÉRT szöveg:
   `CThumbUI::GetTagInfo::format` (`referencia/stringres-en-hu.tsv:691`),
   `Tags: ` → `Címkék: `.
3. **számláló** — ⚠️ HELYESBÍTVE a #2587-ben: MÉGIS ott van, a fájlméret
   UTÁN és a címkék ELŐTT. Ez a fájl eredetileg az ellenkezőjét állította,
   mert a `141421.jpg` FÉL SZÉLESSÉGŰ Picasa-ablakot mutatott, ahol a sáv
   szövege le volt vágva — a levágást olvastuk hiánynak. A teljes
   szélességű felvétel (`research/felirat-ki-bekapcsolva/`) megcáfolta.

⚠️ A fájlnév alakját (mappa-előtag nélkül, középen rövidítve) ez a kör
SZÁNDÉKOSAN nem bántja: a rövidítés szabálya egyetlen mintából nem
dönthető el — külön jegy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from PySide6.QtCore import QLocale

from picasapy.app import formatting


@dataclass
class _Foto:
    """A `PhotoRecord` infó-sávhoz szükséges felülete."""

    name: str = "kep.png"
    taken_at: str | None = None
    width: int = 896
    height: int = 1344
    size: int = 826368
    keywords: str | None = None
    mtime_ns: int = 0
    first_seen_mtime_ns: int | None = None

    @property
    def sort_mtime_ns(self) -> int:
        if self.first_seen_mtime_ns is None:
            return self.mtime_ns
        return self.first_seen_mtime_ns


#: 2023-05-10 16:30:05 helyi idő — a felvételen ez áll
_MINTA_NS = int(
    __import__("datetime").datetime(2023, 5, 10, 16, 30, 5).timestamp() * 1e9
)


def _szoveg(foto) -> str:
    return formatting.photo_info_text(foto, QLocale("hu_HU"), lambda s: s)


class TestADatum:
    def test_EXIF_nelkul_is_van_datum(self):
        foto = _Foto(first_seen_mtime_ns=_MINTA_NS)
        assert "2023. 05. 10. 16:30:05" in _szoveg(foto), (
            "EXIF felvételi idő nélkül a sávból hiányzik a dátum — az "
            "eredeti a befagyasztott fájlidőt írja ki"
        )

    def test_a_BEFAGYASZTOTT_idot_hasznalja_nem_az_elot(self):
        """#2486: az élő `mtime` bármely mentéstől elmozdul."""
        foto = _Foto(
            mtime_ns=_MINTA_NS + 86_400 * 10**9,  # egy nappal későbbi
            first_seen_mtime_ns=_MINTA_NS,
        )
        assert "2023. 05. 10." in _szoveg(foto)
        assert "2023. 05. 11." not in _szoveg(foto)

    def test_az_EXIF_datum_marad_az_elsodleges(self):
        foto = _Foto(taken_at="2019-01-02T03:04:05", first_seen_mtime_ns=_MINTA_NS)
        assert "2019. 01. 02." in _szoveg(foto)
        assert "2023." not in _szoveg(foto)

    def test_a_masodperc_is_kiirodik(self):
        """A felvételen `16:30:05` áll, nem `16:30`."""
        assert re.search(r"\d{2}:\d{2}:\d{2}", _szoveg(_Foto(first_seen_mtime_ns=_MINTA_NS)))

    def test_idozona_NEM_kerul_bele(self):
        assert "CEST" not in _szoveg(_Foto(first_seen_mtime_ns=_MINTA_NS))
        assert "idő" not in _szoveg(_Foto(first_seen_mtime_ns=_MINTA_NS)).replace(
            "képpont", ""
        )


class TestACimkek:
    def test_a_cimkek_a_sav_VEGEN_allnak(self):
        foto = _Foto(keywords="AI image", first_seen_mtime_ns=_MINTA_NS)
        szoveg = _szoveg(foto)
        assert szoveg.rstrip().endswith("Tags: AI image"), (
            f"a címkék nem a sáv végén állnak: {szoveg!r}"
        )

    def test_cimke_nelkul_nincs_ures_elotag(self):
        szoveg = _szoveg(_Foto(first_seen_mtime_ns=_MINTA_NS))
        assert "Tags" not in szoveg

    def test_a_MERT_magyar_elotag(self):
        """`CThumbUI::GetTagInfo::format` — `Tags: ` → `Címkék: `."""
        from pathlib import Path

        import picasapy.app as app_csomag

        ts = (
            Path(app_csomag.__file__).parent / "i18n" / "picasapy_hu.ts"
        ).read_text(encoding="utf-8")
        assert "<source>Tags: %1</source>" in ts
        assert "<translation>Címkék: %1</translation>" in ts


class TestASzamlaloAMERTHelyen:
    """#2587 — a #2565 itt TÉVEDETT, és a tévedés kiment a felhasználóhoz.

    Az akkori bizonyíték (`141421.jpg`) FÉL SZÉLESSÉGŰ Picasa-ablakot
    mutatott: a kék sáv szövege le volt vágva, és a levágást olvastuk
    hiánynak. A teljes szélességű felvétel
    (`research/felirat-ki-bekapcsolva/picasa3-felirat-bekapcsolva. 223224.jpg`)
    megcáfolta::

        … 896x1344 képpont   807 KB   (82 / 3)   Címkék: AI image

    A számláló tehát OTT VAN, a fájlméret UTÁN és a címkék ELŐTT.
    """

    def test_a_szamlalo_a_MERET_es_a_CIMKEK_kozott_all(self):
        foto = _Foto(keywords="AI image", first_seen_mtime_ns=_MINTA_NS)
        szoveg = formatting.photo_info_text(
            foto, QLocale("hu_HU"), lambda s: s, "(82 / 3)"
        )
        meret = szoveg.index("807") if "807" in szoveg else szoveg.index("KB")
        assert szoveg.index("(82 / 3)") > meret
        assert szoveg.index("(82 / 3)") < szoveg.index("Tags:")

    def test_szamlalo_nelkul_nem_marad_ures_hely(self):
        szoveg = formatting.photo_info_text(
            _Foto(first_seen_mtime_ns=_MINTA_NS), QLocale("hu_HU"), lambda s: s
        )
        assert "(" not in szoveg
        assert "    " not in szoveg  # nincs dupla elválasztó

    def test_a_nezo_savja_TARTALMAZZA_a_szamlalot(self):
        from picasapy.app.controller import AppController

        forras = __import__("inspect").getsource(AppController.viewerInfo)
        kod = "\n".join(
            sor for sor in forras.splitlines()
            if not sor.lstrip().startswith("#")
        )
        assert "szamlalo_szoveg" in kod, (
            "a néző kék sávjából hiányzik a lapszámláló — az eredetiben "
            "(teljes szélességű felvétel) ott van"
        )

    def test_a_FORMAZO_es_a_forditasa_MEGMARAD(self):
        """A #1960 mérése (fordított magyar sorrend) érvényben van."""
        from picasapy.app.controller import AppController

        assert AppController.szamlalo_szoveg(3, 5)
