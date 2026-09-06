"""#2564 — a nagyítás-hármas HELYE: az alsó eszközsáv, nem a fotó sarka.

## A mérés

Forrás: `docs/specs/ui-audit-editor.md` („A szerkesztő NAGYÍTÁS-HÁRMASA"),
a geometria a `respack.yt` rétegfejléceiből, a horgonyzás az
`editpanel.tre:1288–1324`-ből.

| elem | horgony | x-tartomány |
|---|---|---|
| `editpanel/zoombuttcontainer` (fit + 1to1) | `m_offsetRB` az `editbase`-en | 286…360 |
| `editpanel/zoomup_icon` (a nagyító) | `m_offsetLB` a `zoomsliderrect`-en | 368…392 |
| `editpanel/zoomslider_container` | `m_offsetLB` a `zoomsliderrect`-en | 399…526 |

A könyvtár ALSÓ SÁVJÁNAK mért tartományai (#2305) ugyanezek a rések:
`thumbui/loupehit` **366…391**, `thumbui/scalecontainer` **398…525**,
`thumbui/metadata_group` 545…785. Vagyis a szerkesztő nagyítás-hármasa a
könyvtár nagyító + bélyegkép-csúszka párjának a HELYÉT foglalja el —
egyetlen sáv, módonként cserélt tartalommal, nem két külön hely.

⇒ A hármas az alsó eszközsáv gyereke (a csillag és a két forgatás után, a
négy panelkapcsoló előtt), NEM a fotó-területé, és nincs körülötte lebegő
sötét doboz.

## Amit ez az őr NEM állít

- a gombok MÉRETÉT (37 × 22, 127) a #2311 őre méri, a csúszka
  ÉRTÉKKÉSZLETÉT a #2492-é — ez a fájl kizárólag a HELYRŐL szól;
- az `editpanel/zoomup_icon` MAGASSÁGA nincs kimérve (csak a 24 képpontos
  szélessége), és a `.tre` nem ad neki `Property mousedown`-t: ezért nálunk
  díszítő ikon, nem gomb. Ha egyszer kiderül, hogy vezérlő, az külön jegy.
"""

from __future__ import annotations

import time
from pathlib import Path

import picasapy.app as app_csomag
from PySide6.QtCore import QObject

_QML_MAPPA = Path(app_csomag.__file__).parent / "qml" / "PicasaPy"
_TALCA = (_QML_MAPPA / "TrayBar.qml").read_text(encoding="utf-8")
_NEZO = (_QML_MAPPA / "PhotoViewer.qml").read_text(encoding="utf-8")

#: a hármas: a két szegmensgomb és a csúszka
HARMAS = ("zoomFitButton", "zoomActualButton", "zoomSlider")


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


def _osok(elem) -> list[str]:
    """Az elem szülőláncának elemnevei, a legközelebbivel kezdve."""
    nevek: list[str] = []
    szulo = elem.parent()
    while szulo is not None:
        nev = szulo.objectName()
        if nev:
            nevek.append(nev)
        szulo = szulo.parent()
    return nevek


def _nyisd_a_nezot(window, qt_app):
    window.setProperty("viewerOpen", True)
    nezo = _elem(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    qt_app.processEvents()
    assert _var(qt_app, lambda: _elem(window, "zoomFitButton").property("visible"))
    return nezo


def _also_x(window, nev: str) -> float:
    """Egy elem x-e az ALSÓ SÁV koordinátáiban (a `trayBar`-ig felösszegezve)."""
    elem = _elem(window, nev)
    x = 0.0
    csomo = elem
    while csomo is not None and csomo.objectName() != "trayBar":
        ertek = csomo.property("x")
        if ertek is not None:
            x += float(ertek)
        csomo = csomo.parent()
    assert csomo is not None, f"a(z) {nev} nem a `trayBar` alatt van"
    return x


class TestAHelye:
    def test_a_harmas_az_ALSO_SAV_gyereke(self, qml_app, qt_app):
        """`editbase` jobb alsó sarka = a könyvtár alsó sávjának ugyanaz a rése."""
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        for nev in HARMAS:
            assert "trayBar" in _osok(_elem(window, nev)), (
                f"a(z) {nev} nem az alsó eszközsávban ül, hanem itt: "
                f"{_osok(_elem(window, nev))}"
            )

    def test_a_harmas_NEM_a_NEZO_gyereke(self, qml_app, qt_app):
        """A fotó fölötti réteg ELHAGYÁSA — nem elég, hogy a sávban is ott van.

        Szándékosan a `photoViewer`-re néz, nem a `viewerPhotoArea`-ra: a
        lebegő `zoomBar` a fotó-terület TESTVÉRE volt (közös átfedő réteg),
        tehát a `viewerPhotoArea` hiánya a régi állapotra is igaz volt
        volna — az az állítás a hibát RÖGZÍTETTE volna, nem fogja meg.
        """
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        for nev in HARMAS:
            osok = _osok(_elem(window, nev))
            assert "photoViewer" not in osok, (
                f"a(z) {nev} még mindig a nézőben lebeg: {osok}"
            )

    def test_nincs_korulotte_lebego_sotet_doboz(self, qml_app, qt_app):
        """A lebegő `viewerZoomBar` doboz megszűnt a hármas körül."""
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        for nev in HARMAS:
            assert "viewerZoomBar" not in _osok(_elem(window, nev))


class TestAMertSorrend:
    """csillag + forgatás → fit · 1:1 · nagyító · csúszka → panelkapcsolók."""

    def test_a_forgatas_gombok_UTAN_all(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        csillagcsoport = _elem(window, "trayStarGroup")
        csillag_jobb = _also_x(window, "trayStarGroup") + float(
            csillagcsoport.property("width")
        )
        assert _also_x(window, "zoomFitButton") >= csillag_jobb, (
            "a nagyítás-hármas a csillag/forgatás csoport ELÉ került"
        )

    def test_fit_majd_1to1_majd_csuszka(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        fit = _also_x(window, "zoomFitButton")
        egy = _also_x(window, "zoomActualButton")
        nagyito = _also_x(window, "viewerZoomUpIcon")
        csuszka = _also_x(window, "zoomSlider")
        assert fit < egy < nagyito < csuszka, (
            f"nem a mért sorrend: fit={fit} 1:1={egy} nagyító={nagyito} "
            f"csúszka={csuszka}"
        )

    def test_a_panelkapcsolok_ELE_kerul(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        assert _also_x(window, "zoomSlider") < _also_x(
            window, "trayMetadataGroup"
        ), "a hármas a négy panelkapcsoló MÖGÉ került"


class TestEgySavKetTartalom:
    """Ugyanaz a rés: könyvtárban a bélyegkép-csúszka, nézőben a nagyítás."""

    def test_a_konyvtarban_a_BELYEGKEP_csuszka_all_ott(self, qml_app, qt_app):
        window, _c, _e = qml_app
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        assert _elem(window, "trayLibraryZoomRow").property("visible") is True
        assert _elem(window, "trayViewerZoomRow").property("visible") is False

    def test_a_nezoben_a_NAGYITAS_all_ott(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        assert _elem(window, "trayViewerZoomRow").property("visible") is True
        assert _elem(window, "trayLibraryZoomRow").property("visible") is False


class TestAmiVALTOZATLAN:
    """A vágás és a videó ugyanúgy elrejti a hármast, mint a lebegő sávban."""

    def test_a_vagas_elrejti(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        panel = _elem(window, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        assert _elem(window, "trayViewerZoomRow").property("visible") is False
        panel.setProperty("cropActive", False)
        qt_app.processEvents()
        assert _elem(window, "trayViewerZoomRow").property("visible") is True

    def test_a_ket_arc_gomb_a_nezoben_MARAD(self, qml_app, qt_app):
        """Hatókörön kívül (a jegy kimondja): a `☺` és a `✎` a mienk."""
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        for nev in ("facesToggleButton", "facesEditToggleButton"):
            assert "trayBar" not in _osok(_elem(window, nev)), (
                f"a(z) {nev} átkerült az alsó sávba — a jegy hatókörén kívül"
            )


class TestAForras:
    def test_a_harmas_a_TALCA_fajlban_el(self):
        for nev in HARMAS:
            assert f'objectName: "{nev}"' in _TALCA, (
                f"a(z) {nev} nem a TrayBar.qml-ben van"
            )
            assert f'objectName: "{nev}"' not in _NEZO, (
                f"a(z) {nev} MÉG MINDIG a PhotoViewer.qml-ben van"
            )


class TestAModvaltasNemMozgatSemmit:
    """A tartalomcsere nem rendezheti át a felső sort.

    ⚠️ Ez egy MÁR MEGTÖRTÉNT hiba őre, nem elméleti aggály. Amíg a rés
    `Row` volt, a néző megnyitásakor a keskenyebb könyvtári tartalmat a
    szélesebb nézői váltotta, a felső sor átrendeződött, és az átrendeződés
    alatt érkező EGYETLEN kattintás elveszett: a #2566 őre azt mutatta,
    hogy a fiók bal szélső gombja („Emberek") a néző megnyitása után az
    első kattintásra nem nyílik ki. A rés azóta rögzített szélességű
    `Item`, a két sor pedig a jobb szélhez zár — ami a MÉRÉSSEL is egyezik:
    `thumbui/scalecontainer` 525 és `editpanel/zoomslider_container` 526,
    vagyis a két mód sávja ugyanott ér véget.
    """

    def _res(self, window):
        elem = _elem(window, "trayZoomGroup")
        kozep = elem.mapToScene(elem.boundingRect().center())
        return (round(float(elem.property("width"))), round(kozep.x()))

    def test_a_res_merete_es_helye_valtozatlan(self, qml_app, qt_app):
        window, _c, _e = qml_app
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        konyvtar = self._res(window)
        _nyisd_a_nezot(window, qt_app)
        assert self._res(window) == konyvtar, (
            f"a rés elmozdult a módváltáskor: {konyvtar} → "
            f"{self._res(window)}"
        )

    def test_a_panelkapcsolok_nem_mozdulnak(self, qml_app, qt_app):
        window, _c, _e = qml_app
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        gomb = _elem(window, "trayMetadataGroup")
        elotte = round(gomb.mapToScene(gomb.boundingRect().center()).x())
        _nyisd_a_nezot(window, qt_app)
        utana = round(gomb.mapToScene(gomb.boundingRect().center()).x())
        assert elotte == utana, (
            f"a négy panelkapcsoló elmozdult a módváltáskor: {elotte} → {utana}"
        )
