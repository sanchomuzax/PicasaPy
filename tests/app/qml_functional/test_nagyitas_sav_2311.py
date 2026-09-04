"""#2311 — a szerkesztő nagyítás-sávja: ikonok és mért méretek.

## A mérés (a #2305 kutatói köréből)

| elem | hely (`respack.yt`) | méret | smink |
|---|---|---|---|
| `editpanel/fit` | x 286…323, y 449…471 | **37 × 22** | `globalbuttons/b38l_*` (**bal** szegmens) |
| `editpanel/1to1` | x 323…360, y 449…471 | **37 × 22** | `globalbuttons/b38r_*` (**jobb** szegmens) |
| `editpanel/fit_icon` | x 298…312 | 14 × 12 | — |
| `editpanel/1to1_icon` | x 332…349 | 17 × 12 | — |
| `editpanel/zoomslider_container` | x 399…526 | **127** széles | — |

A két gomb **érintkezik** (323 = 323), és a `b38l` / `b38r` sminkpár
összeragasztott **szegmenspárt** jelöl. Mindkettőn `Property mousedown 1`
⇒ **lenyomásra** sülnek el, nem felengedésre.

Hivatalos magyar súgó (`panel-feliratok-hu.tsv:4919–4920`):
**„Beillesztheti a fotót a megjelenítési területbe"** ·
**„Fotó megjelenítése tényleges méretben"**. Az angol forrásszövegeink
pontosan az eredetiéi — csak a fordítás tért el.

⚠️ **Ami NEM ez a jegy:** a csúszka értékkészlete (nálunk 0,25…8 közvetlen
szorzó, az eredetiben normalizált 0…1). A köztes leképezés nincs kimérve —
csak a szélesség változik itt.

⛔ Az `inbetweenzoom` harmadik állapot `m_hidden` az eredetiben: **nem
készül hozzá vezérlő**.
"""

from __future__ import annotations

import time
from pathlib import Path

import picasapy.app as app_csomag
from PySide6.QtCore import QObject

_QML = (
    Path(app_csomag.__file__).parent / "qml" / "PicasaPy" / "PhotoViewer.qml"
).read_text(encoding="utf-8")
_TS = (
    Path(app_csomag.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")

GOMB_SZELES = 37
GOMB_MAGAS = 22
CSUSZKA_SZELES = 127


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AssertionError, AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.01)
    return False


def _elem(window, nev: str):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"nincs ilyen elem: {nev}"
    return obj


class TestAMertMeretek:
    def test_a_fit_gomb_37x22(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "zoomFitButton"))
        gomb = _elem(window, "zoomFitButton")
        assert (gomb.property("width"), gomb.property("height")) == (
            GOMB_SZELES,
            GOMB_MAGAS,
        )

    def test_az_1to1_gomb_37x22(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "zoomActualButton"))
        gomb = _elem(window, "zoomActualButton")
        assert (gomb.property("width"), gomb.property("height")) == (
            GOMB_SZELES,
            GOMB_MAGAS,
        )

    def test_a_csuszka_127_szeles(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "zoomSlider"))
        assert _elem(window, "zoomSlider").property("width") == CSUSZKA_SZELES


class TestIkonNemGlifa:
    def test_a_fit_gomb_NEM_szoveget_mutat(self, qml_app, qt_app):
        """A `⛶` glifa platformfüggő és nem az eredeti rajza."""
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "zoomFitButton"))
        assert not _elem(window, "zoomFitButton").property("text"), (
            "a fit gomb szöveg-glifát mutat ikon helyett"
        )

    def test_az_1to1_gomb_NEM_szoveget_mutat(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "zoomActualButton"))
        assert not _elem(window, "zoomActualButton").property("text"), (
            "az 1:1 gomb szöveget mutat ikon helyett"
        )

    def test_MINDKETTONEK_van_ikonfajlja(self):
        ikonok = Path(app_csomag.__file__).parent / "qml" / "PicasaPy" / "icons"
        for nev in ("zoom-fit.svg", "zoom-actual.svg"):
            assert (ikonok / nev).exists(), f"hiányzik az ikon: {nev}"


class TestSzegmensPar:
    def test_a_ket_gomb_ERINTKEZIK(self, qml_app, qt_app):
        """A mérésben 286…323 és 323…360 — nincs rés köztük."""
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "zoomFitButton"))
        fit = _elem(window, "zoomFitButton")
        egy = _elem(window, "zoomActualButton")
        tav = egy.x() - (fit.x() + fit.width())
        assert abs(tav) < 0.5, (
            f"a két gomb között {tav:.1f} képpont rés van — az eredetiben "
            f"összeragasztott szegmenspár"
        )


class TestLenyomasraSul:
    def test_mindketto_mousedown(self):
        """`Property mousedown 1` mindkettőn — a felengedés késői."""
        for nev in ("zoomFitButton", "zoomActualButton"):
            kezd = _QML.index(f'objectName: "{nev}"')
            blokk = _QML[kezd:kezd + 700]
            assert "onPressed:" in blokk, (
                f"a(z) {nev} felengedésre sül el, nem lenyomásra"
            )
            assert "onClicked:" not in blokk, (
                f"a(z) {nev} még mindig `onClicked`-et használ"
            )


class TestAHivatalosMagyarSugo:
    def test_a_ket_forditas_a_MERT_szoveg(self):
        for forras, magyar in (
            (
                "Fit Photo inside viewing area",
                "Beillesztheti a fotót a megjelenítési területbe",
            ),
            (
                "Display Photo at actual size",
                "Fotó megjelenítése tényleges méretben",
            ),
        ):
            assert f"<source>{forras}</source>" in _TS
            assert f"<translation>{magyar}</translation>" in _TS, (
                f"nem a hivatalos magyar alak: {magyar}"
            )


class TestAmiNEMkeszul:
    def test_nincs_inbetweenzoom_vezerlo(self):
        """Az eredetiben `m_hidden` — nem építünk hozzá gombot."""
        assert "inbetweenzoom" not in _QML.lower()
