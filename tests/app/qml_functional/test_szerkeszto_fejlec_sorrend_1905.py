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

⚠️ #3663 pontosított mérés (`ui-audit-editor.md` 3/b.1, élő 1280×1024-es
felvétel): a hármas UTÁN két további segédgomb áll (a fókuszváltó és az
elrendezés-váltó) — a valódi utolsó elem tehát az elrendezés-váltó, nem az
`AA` szegmens. A lenti `SORREND` ezt a pontosabb mérést követi. A korábbi
kör tévesen a nézőben akkor még nem létező, letiltott
`compareButtonA/AB/AA` placeholdereket vonta be a próbába a valódi
`viewerLayoutOnly1up/Ab/Aa` szegmensek helyett — a #3663 törölte a
placeholdereket (nincs ilyen sor a referencián), a próba ezért a valódi
szegmensekre és a két segédgombra tér át.

⚠️⚠️ #3663 MÁSODIK átnézési kör (a fenti javítás után derült ki): „a sáv
JOBB SZÉLÉN" tévedés volt — a mért abszolút pozíció (ugyanott, 3/b.1: `▶`
vége 917, szegmens 933–1047, fókuszváltó 1057–1091, elrendezés-váltó
1096–1130, 1280 px-en) azt mutatja, hogy a teljes navigátor-csoport (Play …
elrendezés-váltó) a FOTÓTERÜLET vízszintes közepéhez igazodik — a
filmszalag középpontja esik egybe a fotóterület középpontjával —, NEM a
sáv jobb szeléhez. Az akkori „jobbszél"-próbát (`test_a_harmas_a_sav_JOBB_
szelen_all`) ez a kör lecserélte egy ellenpróbára (a csoport NEM simul a
szélhez); az abszolút pozíció és a fotóterület-közép szerinti igazodás
pontos, ±8 px tűrésű próbája a
`test_kettos_nezet_gombsor_helye_3663.py::TestANavigatorCsoportAbszolutHelye`
osztályban él, öt fotós próbamappával (a filmszalag szélessége a mérthez
közel essen).

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


def _valts_ket_kepre(window, qt_app):
    """#3663: a fókuszváltó/elrendezés-váltó CSAK 2-up módban látszik
    (`visible: viewer.layoutMode !== "1up"`) — a sorrend-teszthez ide kell
    kapcsolni, különben a Row kihagyja őket az elrendezésből."""
    nezo = _elem(window, "photoViewer")
    nezo.setProperty("layoutMode", "ab")
    qt_app.processEvents()


class TestAVezerlokSorrendje:
    #: balról jobbra, ahogy a felvételen az eredetiben állnak — #3663:
    #: a valódi `A`/`AB`/`AA` szegmensek és a két segédgomb (a korábbi kör
    #: letiltott `compareButtonA/AB/AA` placeholderei helyett, ld. a fenti
    #: figyelmeztetést).
    SORREND = (
        "viewerPlayButton",
        "viewerPrevButton",
        "viewerFilmstrip",
        "viewerNextButton",
        "viewerLayoutOnly1up",
        "viewerLayoutAb",
        "viewerLayoutAa",
        "viewerSwapFocus",
        "viewerSwapLayout",
    )

    def test_a_sorrend_az_eredetit_koveti(self, qml_app, qt_app):
        window = _nyisd_meg(qml_app, qt_app)
        _valts_ket_kepre(window, qt_app)
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
        for nev in ("viewerLayoutOnly1up", "viewerLayoutAb", "viewerLayoutAa"):
            assert _bal_x(_elem(window, nev)) > _jobb_x(szalag), (
                f"a(z) {nev} a filmszalag ELÉ került"
            )

    def test_a_harmas_UTAN_ket_segedgomb_all_es_NEM_a_sav_szelen(
        self, qml_app, qt_app
    ):
        """#3663 MÁSODIK átnézési kör: a korábbi próba tévesen a sáv jobb
        SZÉLÉHEZ simulást várta el — a mért abszolút pozíció szerint a
        csoport a FOTÓTERÜLET közepéhez igazodik, tehát jelentős rés marad
        a sáv jobb széléig (a pontos, ±8 px tűrésű abszolút próba:
        `test_kettos_nezet_gombsor_helye_3663.py::
        TestANavigatorCsoportAbszolutHelye`). Ez az ellenpróba csak azt
        védi, hogy a sorrend (hármas → fókuszváltó → elrendezés-váltó)
        megmaradjon, és a csoport NE csússzon vissza a szélre."""
        window = _nyisd_meg(qml_app, qt_app)
        _valts_ket_kepre(window, qt_app)
        sav = _elem(window, "viewerTopBar")
        assert sav is not None, "nincs objectName-je a felső sávnak"
        utolso = _elem(window, "viewerSwapLayout")
        hezag = _jobb_x(sav) - _jobb_x(utolso)
        assert hezag > 50, (
            f"az elrendezés-váltó csak {hezag:.0f} px-re áll a sáv jobb "
            "szélétől — úgy tűnik, a csoport megint a szélre tolódott, "
            "nem a fotóterület közepére igazodik"
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
