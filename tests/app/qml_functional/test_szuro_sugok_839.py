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


class TestMindenSzuronekVanSugoja:
    def test_a_negy_nevesitett_szuro_sugoja_megvan(self) -> None:
        for nev, szoveg in SZUROK.items():
            blokk = _blokk(nev)
            assert f'ToolTip.text: qsTr("{szoveg}")' in blokk, (
                f"{nev}: nincs (vagy más) buboréksúgója — a súgó nélküli "
                "ikon néma, a felhasználó nem tudja, mit csinál"
            )

    def test_a_sugo_a_LEBEGESRE_jelenik_meg(self) -> None:
        for nev in SZUROK:
            blokk = _blokk(nev)
            assert "ToolTip.visible:" in blokk and "hovered" in blokk
            assert "ToolTip.delay: Theme.tooltipDelay" in blokk, (
                f"{nev}: a súgó késleltetése nem a közös Theme-értékből jön"
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
