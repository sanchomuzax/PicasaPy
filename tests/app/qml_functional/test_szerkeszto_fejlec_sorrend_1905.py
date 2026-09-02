"""#1905/2–3: a szerkesztő fejlécének SORRENDJE és a hisztogram helye.

## A bizonyíték

Egymás mellé tett felvétel ugyanazon a mappán
(`research/Picasa3-vs-PicasaPy-fejlec-elteresek/`, a tulajdonos felvétele
— a projekt szabálya szerint ez a legerősebb bizonyíték).

### 2. A vezérlők sorrendje

| | Picasa 3 (balról jobbra) | PicasaPy (a jegy nyitásakor) |
|---|---|---|
| 1 | Vissza a könyvtárhoz | Vissza a könyvtárhoz |
| 2 | *(paletta-gomb — funkciója FELTÁRATLAN)* | – |
| 3 | ▶ Lejátszás | ▶ Lejátszás |
| 4 | ◀ léptető | `A` · `AB` · `AA` |
| 5 | a filmszalag | ◀ léptető |
| 6 | ▶ léptető | a filmszalag |
| 7 | `A` · `AB` · `AA` — a sáv JOBB SZÉLÉN | ▶ léptető |

⇒ Az `A`/`AB`/`AA` hármas nálunk a szalag ELÉ került; az eredetiben a
szalag UTÁN, a sáv jobb szélén áll.

### 3. A hisztogram-doboz helye — MÉRVE a felvételen

Mindkét ablak bal panelje ugyanott ér véget (a kék infósáv `y = 926`-nál
kezdődik, tehát a panel alja `y = 925`):

| | a doboz alsó szegélye | távolság a panel aljától |
|---|---|---|
| Picasa 3 | `y = 921` | **4 px** |
| PicasaPy | `y = 830` | **95 px** |

A 95 nem a semmiből jött: az `editpanel.tre` `nerdview_container`-e
`YConstraint 1, 1, -95`. Csakhogy annak a SZÜLŐJE `root`, nem a bal fiók
— a fiók alja fölött ez a −95 nagy üres sávot hagy. A felvétel dönt: a
doboz a panel aljához simul.

⚠️ A doboz MÉRETÉT (238 × 144) ez a kör NEM változtatja. A felvételen a
magasság 150 px-nek adódik, de a 144 korábbi körből származik, és 6 px
eltérésre JPEG-en mért szegélyekből nem mondunk ki új igazságot.
"""
from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem

from support.jpeg_factory import make_jpeg

#: A felvételen mért távolság a doboz alja és a panel alja között.
MERT_ALSO_HEZAG = 4
#: JPEG-en mért szegélyek: egy képpont tűrés mindkét irányba.
TURES = 2


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _elem(window, nev: str):
    for it in _walk(window.contentItem()):
        if it.objectName() == nev:
            return it
    return window.findChild(QObject, nev)


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


def _bal_x(elem) -> float:
    """Az elem bal éle JELENET-koordinátában (a szülők eltolásával)."""
    return elem.mapToScene(elem.boundingRect().topLeft()).x()


def _jobb_x(elem) -> float:
    return elem.mapToScene(elem.boundingRect().bottomRight()).x()


def _nyisd_meg(qml_app, qt_app):
    window, controller, _e = qml_app
    lib = Path(controller.watchedFolders[0])
    mappa = lib / "fejlec"
    mappa.mkdir(exist_ok=True)
    for i in range(3):
        make_jpeg(mappa / f"kep{i}.jpg", size=(60, 40))
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()

    sor = next(
        s for s in range(controller.photos.rowCount())
        if "fejlec" in controller.photos.filePathAt(s)
    )
    window.setProperty("selectedIndexes", [sor])
    window.setProperty("selectedIndex", sor)
    qt_app.processEvents()
    nezo = _elem(window, "photoViewer")
    nezo.setProperty("currentIndex", sor)
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()
    _var(qt_app, lambda: _elem(window, "viewerFilmstrip") is not None)
    return window


class TestAVezerlokSorrendje:
    #: balról jobbra, ahogy a felvételen az eredetiben állnak
    SORREND = (
        "viewerPlayButton",
        "viewerPrevButton",
        "viewerFilmstrip",
        "viewerNextButton",
        "compareButtonA",
        "compareButtonAB",
        "compareButtonAA",
    )

    def test_a_sorrend_az_eredetit_koveti(self, qml_app, qt_app):
        window = _nyisd_meg(qml_app, qt_app)
        elemek = [(nev, _elem(window, nev)) for nev in self.SORREND]
        hianyzo = [nev for nev, e in elemek if e is None]
        assert not hianyzo, f"nincs meg a fejlécben: {hianyzo}"

        helyek = [(nev, _bal_x(e)) for nev, e in elemek]
        rendezett = [nev for nev, _x in sorted(helyek, key=lambda p: p[1])]
        assert rendezett == list(self.SORREND), (
            "a fejléc-vezérlők sorrendje eltér az eredetitől.\n"
            f"  mért:  {helyek}\n"
            f"  várt:  {list(self.SORREND)}"
        )

    def test_az_osszehasonlito_harmas_a_szalag_UTAN_all(self, qml_app, qt_app):
        """A foga: a hármast a szalag elé visszatéve ez bukik."""
        window = _nyisd_meg(qml_app, qt_app)
        szalag = _elem(window, "viewerFilmstrip")
        for nev in ("compareButtonA", "compareButtonAB", "compareButtonAA"):
            assert _bal_x(_elem(window, nev)) > _jobb_x(szalag), (
                f"a(z) {nev} a filmszalag ELÉ került"
            )

    def test_a_harmas_a_sav_JOBB_szelen_all(self, qml_app, qt_app):
        """Nem elég a szalag után lennie: az eredetiben a sáv jobb szélén
        áll, nem közvetlenül a szalag mellett."""
        window = _nyisd_meg(qml_app, qt_app)
        sav = _elem(window, "viewerTopBar")
        assert sav is not None, "nincs objectName-je a felső sávnak"
        utolso = _elem(window, "compareButtonAA")
        hezag = _jobb_x(sav) - _jobb_x(utolso)
        assert 0 <= hezag <= 16, (
            f"az `AA` gomb {hezag:.0f} px-re áll a sáv jobb szélétől — "
            "az eredetiben a szélhez simul"
        )


class TestAHisztogramAPanelAljan:
    def test_a_doboz_a_panel_aljahoz_simul(self, qml_app, qt_app):
        window = _nyisd_meg(qml_app, qt_app)
        fiok = _elem(window, "viewerLeftDrawer")
        doboz = _elem(window, "viewerHistogramBox")
        assert fiok is not None and doboz is not None

        fiok_alja = fiok.mapToScene(fiok.boundingRect().bottomLeft()).y()
        doboz_alja = doboz.mapToScene(doboz.boundingRect().bottomLeft()).y()
        hezag = fiok_alja - doboz_alja
        assert abs(hezag - MERT_ALSO_HEZAG) <= TURES, (
            f"a hisztogram-doboz {hezag:.0f} px-re lebeg a panel alja fölött; "
            f"a felvételen mért érték {MERT_ALSO_HEZAG} px"
        )
