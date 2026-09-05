"""#1672 — a képtálca műveletsorának hiányzó gombjai.

## A mért sorrend

```
print → email → export → shop → hello → blog → collage → movie → morebutton
```

Nálunk hat volt a kilencből: hiányzott a **Rendelés** (`shop`), a
**Blogger** (`blog`) és a **„További…"** (`morebutton`).

## `retired`, nem `placeholder`

A `PicasaMenuItem.qml` (#422) leírja a különbséget: a **`placeholder`
ígéret a jövőre**, a **`retired` nem ígér semmit**. A nyomat-rendelés és
a Blogger-integráció szolgáltatása **bizonyíthatóan megszűnt**, tehát
kivezetett gombként kerülnek be — a helyük az eredetié, de a
buboréksúgójuk kimondja, hogy a szolgáltatás nincs többé.

## A „További…" azóta BEKERÜLT (#2191)

A jegy külön feltétele az volt: *„a »További…« viselkedése kimérve,
mielőtt bekötjük — ne a feliratból következtessünk."* A #2191 kimérte (a
`respack.yt` `outputlayout/morebutton` gombja és a szövegtár két
felirata), ezért az itteni tiltó őr **leváltva**: mostantól azt kéri
számon, hogy a gomb a MÉRT tulajdonságaival legyen jelen. A viselkedését
a `test_kimeneti_tulcsordulas_2191.py` méri.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

_TRAY = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/TrayBar.qml"
)

#: A mért sorrend azon része, ami nálunk megvan (a `morebutton` nélkül).
MERT_SORREND = [
    "trayPrintButton",
    "trayEmailButton",
    "trayExportButton",
    "trayOrderButton",
    "trayShareButton",
    "trayBlogButton",
    "trayCollageButton",
    "trayMovieButton",
]


class TestASorrend:
    def test_a_gombok_a_MERT_sorrendben_allnak(self):
        """A sorrend a forrásbeli deklarációk sorrendje — a `Row`
        ugyanígy rakja ki őket."""
        forras = _TRAY.read_text(encoding="utf-8")
        helyek = [(forras.index(f'"{nev}"'), nev) for nev in MERT_SORREND]
        assert [nev for _hely, nev in sorted(helyek)] == MERT_SORREND, (
            "a tálca gombjai nem a mért sorrendben állnak (#1672)"
        )

    def test_a_ket_uj_gomb_letezik_az_elo_faban(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        for nev in ("trayOrderButton", "trayBlogButton"):
            assert window.findChild(QObject, nev) is not None, nev


class TestAKivezetesJelolese:
    def test_egyik_sem_kattinthato(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        for nev in ("trayOrderButton", "trayBlogButton"):
            gomb = window.findChild(QObject, nev)
            assert gomb.property("enabled") is False, (
                f"{nev} kattintható — kivezetett szolgáltatás mögé nem "
                "kínálunk működő gombot (#1672)"
            )

    def test_a_buborekusgo_KIMONDJA_hogy_megszunt(self):
        """A `retired` nem ígér semmit — de ezt meg is kell mondani,
        különben a szürke gomb „még nem kész"-nek látszik."""
        forras = _TRAY.read_text(encoding="utf-8")
        for szoveg in (
            "Order Prints (service discontinued)",
            "Publish to Blogger (service discontinued)",
        ):
            assert szoveg in forras, f"hiányzik a buboréksúgó: {szoveg!r}"


class TestASzukAblak:
    """A két kivezetett gomb szűk ablakban ELSŐKÉNT esik ki.

    A sávnak eddig is volt narrow-stratégiája (a csoportelválasztók
    elmaradnak); a kivezetett gombok a legjobb jelöltek a kiesésre, mert
    NEM KATTINTHATÓK — semmit nem vesznek el a felhasználótól. Az
    eredetiben erre a `morebutton`/`overflow` való, ami nálunk nincs meg."""

    def test_a_kivezetettek_kulon_kuszobot_kapnak(self):
        forras = _TRAY.read_text(encoding="utf-8")
        assert "retiredVisible" in forras, (
            "a kivezetett gombok nem tűnnek el szűk ablakban — a sáv "
            "kilógna (a #1345 elrendezés-őre ezt meg is fogja)"
        )

    def test_a_kuszobuk_MAGASABB_az_elvalasztokenal(self):
        """Ha nem lenne magasabb, a két 59 képpontos cella pont akkor
        maradna bent, amikor már a helye sincs meg."""
        forras = _TRAY.read_text(encoding="utf-8")
        assert (
            "windowWidthFor(actionCellCount + retiredCellCount + 2)"
            in forras
        )


class TestAMorebuttonMarBent:
    """A #1672 tiltó őrének utódja: a mérés megvan (#2191), tehát a gomb
    a helyén kell legyen — de csak a MÉRT feliratokkal."""

    def test_a_morebutton_BE_van_kotve(self):
        forras = _TRAY.read_text(encoding="utf-8")
        assert 'objectName: "trayMoreButton"' in forras, (
            "eltűnt a „További…” — a #2191 kimérte és bekötötte"
        )

    def test_a_MERT_forrasszoveget_hasznalja(self):
        """A szövegtárból: `More...` és `Click here for more options` —
        szabadon fordított alak itt nem elfogadható."""
        forras = _TRAY.read_text(encoding="utf-8")
        kezd = forras.index('objectName: "trayMoreButton"')
        blokk = forras[kezd:kezd + 900]
        assert 'text: qsTr("More...")' in blokk
        assert 'qsTr("Click here for more options")' in blokk
