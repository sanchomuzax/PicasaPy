"""A keresősáv szűrő-ikonjainak SÚGÓJA — a #839 őre.

## A mérés, ami ezt kiváltotta

A jegy táblája szerint nálunk **négy** szűrő van (★ · arc · geo · méret), az
eredetiben **öt**. A mai kódon megmérve ez **elavult**: öt szűrőnk van, és a
sorrend is majdnem az eredeti —

| # | eredeti | nálunk |
|---:|---|---|
| 1 | `starsearch` | ★ |
| 2 | `facesearch` | `faceFilter` |
| 3 | `moviesearch` | `movieFilter` |
| 4 | `webview` | **`dupeFilter`** (saját funkció, ld. a döntés-lapot) |
| 5 | `geotagsearch` | `geoFilter` |

Ami TÉNYLEG hiányzott: a **geo-szűrő súgója** — az öt ikonból egyedül ezen
nem volt, pedig a tű a legkevésbé magától értetődő közülük. És hiányzott a
keresés-törlő gomb súgója is.

⚠️ Ez a lap **nem** a sorrendet és nem a be/ki állapot rajzát méri (azok a
jegyben nyitva maradt pontok), hanem azt, hogy **minden szűrő-ikonnak van
súgója** — mert egy súgó nélküli ikon néma.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

_SAV = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "MainToolbar.qml"
)

#: A sávon egymás után álló, TOP-SZINTŰ elemek — a blokk-határhoz.
FELSO_SZINTU = (
    "faceFilter", "movieFilter", "dupeFilter", "geoFilter",
    "searchClear", "toolbarFiltersLabel",
)

#: A szűrő-ikonok objectName-je + a súgó angol szövege (a `searchcontainer.tre`
#: `hottip` sorai szerint).
SZUROK = {
    "faceFilter": "Show only photos with faces",
    "movieFilter": "Show movies only",
    "dupeFilter": "Show duplicate files only",
    "geoFilter": "Show only photos with geotag",
}


def _blokk(nev: str) -> str:
    """Egy elem forrásrészlete az `objectName`-jétől a KÖVETKEZŐ elemig.

    ⚠️ Két zsákutca, hogy a következő olvasó ne fussa újra:

    * **fix karakterablak** (pl. 1800): az elemek hossza a kommentekkel
      együtt erősen szór, és a `faceFilter` súgóját már nem érte el — úgy
      nézett ki, mintha hiányozna;
    * **a következő `objectName:`**: a beágyazott elemeknek (pl.
      `geoFilterIcon`) SAJÁT `objectName`-jük van, tehát a határ a saját
      elemen belülre esett.

    A határ ezért a következő TOP-SZINTŰ elem neve, névsorból."""
    forras = _SAV.read_text(encoding="utf-8")
    kezd = forras.index(f'objectName: "{nev}"')
    hatarok = [
        forras.find(f'objectName: "{mas}"', kezd + 20)
        for mas in FELSO_SZINTU
        if mas != nev
    ]
    hatarok = [h for h in hatarok if h > 0]
    return forras[kezd:] if not hatarok else forras[kezd : min(hatarok)]


#: #839: a súgó HELYE mérve — a `searchcontainer.tre` HAT elemre adja
#: ugyanezt a sort (az öt szűrő + a `timecontainer_label`):
#:
#:     SharedHandler searchcontainer/tip hottip searchcontainer/filter_label
#:
#: A `hottip` célja a `filter_label`, tehát a súgó NEM lebegő buborékban,
#: hanem a „Szűrők" felirat helyén jelenik meg.
HOTTIP_SZOVEGEK = (
    "Show starred photos only",
    "Show only photos with faces",
    "Show movies only",
    "Show duplicate files only",
    "Show only photos with geotag",
    "Filter by date range",
)


def _hoveredtip_lanc() -> str:
    forras = _SAV.read_text(encoding="utf-8")
    kezd = forras.index("readonly property string hoveredTip:")
    return forras[kezd : forras.index("text: filtersLabel.hoveredTip", kezd)]


class TestMindenSzuronekVanSugoja:
    def test_MIND_A_HAT_sugo_szovege_megvan(self) -> None:
        """Egy súgó nélküli ikon néma — a felhasználó nem tudja, mit csinál."""
        lanc = _hoveredtip_lanc()
        for szoveg in HOTTIP_SZOVEGEK:
            assert f'qsTr("{szoveg}")' in lanc, (
                f"hiányzik a súgó szövege a felirat láncából: {szoveg}"
            )

    def test_mindegyik_a_SAJAT_mutatojahoz_van_kotve(self) -> None:
        """A szöveg jelenléte nem elég: a saját hover-kezelőjéhez kell
        kötődnie, különben minden ikonon ugyanaz jelenne meg."""
        lanc = _hoveredtip_lanc()
        for kezelo in (
            "starFilter.hovered",
            "faceFilterHover.hovered",
            "movieFilterHover.hovered",
            "dupeFilterHover.hovered",
            "geoFilterHover.hovered",
            "dateRangeHover.hovered",
        ):
            assert kezelo in lanc, f"nincs a láncban: {kezelo}"

    def test_a_sugo_a_FELIRAT_helyen_jelenik_meg_nem_lebegve(self) -> None:
        """#839, mérve: a hat `hottip`-es elemen NINCS lebegő `ToolTip`."""
        for nev in SZUROK:
            blokk = _blokk(nev)
            assert "ToolTip.text" not in blokk, (
                f"{nev}: lebegő buboréksúgója van, pedig a `.tre` szerint a "
                "súgó a szűrő-felirat helyén jelenik meg (`hottip`)"
            )

    def test_a_felirat_visszaall_mutato_nelkul(self) -> None:
        forras = _SAV.read_text(encoding="utf-8")
        assert 'filtersLabel.hoveredTip : qsTr("Filters")' in forras.replace(
            "\n", " "
        ) or 'qsTr("Filters")' in forras, (
            'a felirat mutatóelvétel után nem áll vissza a „Szűrők” szóra'
        )

    def test_a_felirat_a_MERT_betumeretet_viszi(self) -> None:
        """`m_displayfont12` (`fontmacros_win.tre` 43–47.: `fontsize 12`)."""
        forras = _SAV.read_text(encoding="utf-8")
        kezd = forras.index('objectName: "toolbarFiltersLabel"')
        blokk = forras[kezd : kezd + 1600]
        assert "font.pixelSize: 12" in blokk, (
            'a „Szűrők” felirat nem a mért 12 képpontos betűt viszi'
        )


class TestAKeresesTorlo:
    def test_csak_beirt_keresesnel_latszik(self) -> None:
        """A jegy feltétele — mérve: ez már korábban is teljesült."""
        blokk = _blokk("searchClear")
        assert "visible: searchField.text.length > 0" in blokk

    def test_van_sugoja(self) -> None:
        blokk = _blokk("searchClear")
        assert 'ToolTip.text: qsTr("Clear your search")' in blokk


class TestADontesRogzitve:
    """A jegy kikötése: a `webview` kihagyása döntés-lapon álljon."""

    def test_a_webview_dontes_lap_letezik(self) -> None:
        """⚠️ A `docs/` a REPÓ gyökere alatt van, nem a csomag alatt.

        Az első változatom `parents[2]`-t írt (az a `src/`), és a fájlt nem
        találva KIHAGYTA magát — egy kihagyott teszt pedig nem őr, csak
        zöld pipa. A tesztgyökérből számolva az útvonal egyértelmű."""
        lap = (
            Path(__file__).resolve().parents[3]
            / "docs" / "decisions" / "keresosav-webview-szuro-kimarad.md"
        )
        assert lap.is_file(), f"nincs döntés-lap: {lap}"
        szoveg = lap.read_text(encoding="utf-8")
        assert "webview" in szoveg and "dupeFilter" in szoveg
