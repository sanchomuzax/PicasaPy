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

## A „További…" NEM került be

A jegy külön feltétele: *„a »További…« viselkedése kimérve, mielőtt
bekötjük — ne a feliratból következtessünk."* Nincs mérve, tehát nem
építjük meg. A `TrayActionSeparator` kommentje már ma is megnevezi
(`morebutton`/`overflow`) mint a szűk ablak kezelésének eredeti
megoldását — ez önálló mérést kíván.
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


class TestAmiNEMkeszult:
    def test_a_morebutton_NINCS_bekotve(self):
        """A jegy előírja: előbb mérés, aztán bekötés. Ha valaki mégis
        felveszi, ez a teszt kérdezzen rá, hogy megmérte-e."""
        forras = _TRAY.read_text(encoding="utf-8")
        assert 'objectName: "trayMoreButton"' not in forras, (
            "a „További…” bekerült — a #1672 szerint a viselkedését ELŐBB "
            "ki kell mérni, nem a feliratából következtetni"
        )
