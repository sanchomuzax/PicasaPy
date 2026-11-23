"""A Vágás panel mentett kiegyenesítésű képen is figyelmeztető sor nélkül nyílik (#7392).

## A mérés (a jegy felvételei, `docs/specs/paritas-folyamat-7327.md` (I))

- `job-912 __16`: a `tilt=1,0.391249,0.000000;` láncú képen a Vágás csempe
  után a „Crop Photo" panelen NINCS figyelmeztető sor, és az `allapot.json`
  ablaklistája végig csak „Picasa 3" (nincs külön ablak).
- A panel a tilt nélküli `job-911 __10`-től csak a bélyegképek (a három
  vágás-előnézet) és a hisztogram tartalmában tér el: a cím, az útmutató, a
  legördülő és a gombok képpontra azonosak (a két kocka különbségterülete
  mérve: bélyegképek y 267..287, hisztogram y 825..847, a többi üres).
- `job-912 __18`: az Escape Cancelként zárja az eszközt, a kiegyenesítés
  megmarad (a panelen az „Undo Straighten" gomb ott áll).

## Amit a teszt mér, és amit NEM

- VALÓDI egérkattintás a Vágás csempén és valódi Escape-billentyű.
- Renderelt összevetés: a tilt-es kép Vágás panelje képpontra egyezik a tilt
  nélküli képével (a bélyegképek sávja kivételével) - ugyanaz a reláció, mint
  `__16` és `job-911 __10` között.
- NEM mér: az eredeti Picasa betűképét (a betűrajzolás különbözik, ezért a
  PicasaPy-panel és `__16` között nincs képpont-egyezés, csak elrendezés).
- NEM része: hogy az eredeti a figyelmeztetést a megnyitás UTÁN (húzáskor,
  Alkalmazáskor) kiírja-e (`7327-9c`).
- A Vörösszem „Info" ablakát (`straightenActive` másik fogyasztója) nem érinti
  a változás; azt a `test_redeye_straighten_warning_4542.py` őrzi.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest
from tests.support.varakozas import var_feltetelre

TILT = 0.391249
FIGYELMEZTETES = (
    "This image's orientation has been modified by the Straighten tool and "
    "might not crop accurately.\nIf you encounter difficulty cropping this "
    "image, try undoing the Straighten fix, then recrop, and Straighten "
    "again if necessary."
)


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _elem(window, nev: str) -> QObject:
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a kirajzolt ablakban"
    return elem


def _kattints(window, qt_app, nev: str) -> None:
    """Valódi egérkattintás a vezérlő közepére (jelenet-koordinátán)."""
    elem = _elem(window, nev)
    assert elem.width() > 0 and elem.height() > 0, f"{nev} nem látható"
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _doboz(window, elem: QObject) -> QRectF:
    """Az elem téglalapja a jelenet (ablak) koordinátáiban."""
    bal_felso = elem.mapToScene(QPointF(0, 0))
    return QRectF(bal_felso.x(), bal_felso.y(), elem.width(), elem.height())


def _kepkocka(window, qt_app) -> QImage:
    """A QML-állapotot valóban megrajzoló képkocka elkészültéig vár."""
    kepkockak = QSignalSpy(window.frameSwapped)
    window.update()
    assert _varj(
        qt_app, lambda: kepkockak.count() > 0
    ), "a Vágás panel friss QML-képkockája nem készült el"
    kep = window.grabWindow()
    assert not kep.isNull(), "a QML-képkocka üres"
    return kep


def _ini_ir(tmp_path, tartalom: str) -> None:
    ini = tmp_path / "kepek" / ".picasa.ini"
    ini.write_text(tartalom, encoding="utf-8")


def _nezot_nyit(window, qt_app, index: int):
    window.setProperty("viewerOpen", True)
    viewer = _elem(window, "photoViewer")
    viewer.setProperty("currentIndex", index)
    qt_app.processEvents()
    return viewer


def _vagast_nyit(window, qt_app, panel) -> None:
    panel.setProperty("activeTab", 0)
    qt_app.processEvents()
    _kattints(window, qt_app, "editToolCrop")
    assert _varj(
        qt_app, lambda: panel.property("cropActive") is True
    ), "a Vágás csempe kattintása nem nyitotta meg az eszközt"


def _vagast_zar_escape(window, qt_app, panel) -> None:
    QTest.keyClick(window, Qt.Key.Key_Escape)
    qt_app.processEvents()
    assert _varj(
        qt_app, lambda: panel.property("cropActive") is False
    ), "az Escape nem zárta a Vágás eszközt"


def _kulonbseg_pixelek(egyik: QImage, masik: QImage, doboz: QRectF, kihagy) -> int:
    """A `doboz`-ban eltérő képpontok száma, a `kihagy` téglalapok nélkül."""
    bal, felso = int(doboz.left()), int(doboz.top())
    jobb, also = int(doboz.right()), int(doboz.bottom())
    eltero = 0
    for y in range(felso, also):
        for x in range(bal, jobb):
            if any(k.contains(x, y) for k in kihagy):
                continue
            if egyik.pixel(x, y) != masik.pixel(x, y):
                eltero += 1
    return eltero


class TestVagasPanelKiegyenesitve7392:
    def _kiegyenesitett_es_sima(self, qml_app, qt_app, tmp_path):
        """a.jpg: mentett kiegyenesítés; b.jpg: nincs. A panel és a vezérlő."""
        _ini_ir(
            tmp_path,
            "[a.jpg]\nfilters=tilt=1,0.391249,0.000000;\n[b.jpg]\n",
        )
        window, _controller, engine = qml_app
        assert isinstance(window, QQuickWindow)
        edit = engine.rootContext().contextProperty("editController")
        return window, edit

    def test_a_panel_figyelmeztetes_nelkul_nyilik_kiegyenesitett_kepen(
        self, qml_app, qt_app, tmp_path
    ):
        window, edit = self._kiegyenesitett_es_sima(qml_app, qt_app, tmp_path)
        _nezot_nyit(window, qt_app, 0)
        assert _varj(
            qt_app, lambda: abs(edit.property("tiltParam") - TILT) < 1e-6
        ), "a mentett kiegyenesítés nem töltődött be"
        panel = _elem(window, "viewerEditorPanel")

        _vagast_nyit(window, qt_app, panel)

        # Előfeltétel: a kiegyenesítés TÉNYLEG aktív (különben a teszt
        # üres lenne), és a Vörösszem panel ugyanezt az állapotot használja.
        assert panel.property("straightenActive") is True
        figyelmeztetes = _elem(window, "cropStraightenWarning")
        assert figyelmeztetes.property("visible") is False, (
            "kiegyenesített képen a Vágás panel megnyitáskor figyelmeztet, "
            "az eredetiben (job-912 __16) nincs figyelmeztető sor"
        )
        # A szöveg a forrásban marad (7327-9c kérdése, hogy az eredeti
        # húzáskor/Alkalmazáskor kiírja-e): nem töröltük, csak nem látszik.
        assert figyelmeztetes.property("text") == FIGYELMEZTETES

    def test_a_legordulo_kozvetlenul_az_utmutato_alatt_all(
        self, qml_app, qt_app, tmp_path
    ):
        """A #7394 szerinti, 1 px-es rés marad az útmutató és a legördülő között."""
        window, edit = self._kiegyenesitett_es_sima(qml_app, qt_app, tmp_path)
        _nezot_nyit(window, qt_app, 0)
        assert _varj(qt_app, lambda: edit.property("tiltParam") != 0)
        panel = _elem(window, "viewerEditorPanel")
        _vagast_nyit(window, qt_app, panel)

        utmutato = _doboz(window, _elem(window, "cropGuideText"))
        legordulo = _doboz(window, _elem(window, "cropAspectComboRow"))
        oszlop = _elem(window, "cropColumn")

        res = legordulo.top() - utmutato.bottom()
        assert abs(res - 1) <= 0.5, (
            "az útmutató és a legördülő közötti mért rés nem 1 px: "
            f"{res:.1f} px (ColumnLayout spacing={oszlop.property('spacing')})"
        )

    def test_a_panel_kepponra_egyezik_a_tilt_nelkuli_kepevel(
        self, qml_app, qt_app, tmp_path
    ):
        """`__16` és `job-911 __10` viszonya: a bélyegképek sávján kívül a
        panel képpontra azonos a kiegyenesített és a sima képen."""
        window, edit = self._kiegyenesitett_es_sima(qml_app, qt_app, tmp_path)
        panel = _elem(window, "viewerEditorPanel")

        _nezot_nyit(window, qt_app, 1)
        assert _varj(qt_app, lambda: edit.property("tiltParam") == 0)
        _vagast_nyit(window, qt_app, panel)
        sima = _kepkocka(window, qt_app)
        oszlop = _doboz(window, _elem(window, "cropColumn"))
        belyegkepek = _doboz(window, _elem(window, "cropSuggestionRow"))
        _vagast_zar_escape(window, qt_app, panel)

        _nezot_nyit(window, qt_app, 0)
        assert _varj(
            qt_app, lambda: abs(edit.property("tiltParam") - TILT) < 1e-6
        )
        _vagast_nyit(window, qt_app, panel)
        kiegyenesitett = _kepkocka(window, qt_app)
        oszlop_tilt = _doboz(window, _elem(window, "cropColumn"))
        belyegkepek_tilt = _doboz(window, _elem(window, "cropSuggestionRow"))

        assert oszlop_tilt == oszlop, "a panel oszlopa elmozdult a tilt miatt"
        assert belyegkepek_tilt == belyegkepek
        assert _kulonbseg_pixelek(
            sima, kiegyenesitett, oszlop, [belyegkepek]
        ) == 0, (
            "a kiegyenesített kép Vágás panelje a bélyegképek sávján kívül "
            "eltér a tilt nélküliétől"
        )

    def test_az_escape_zar_es_a_kiegyenesites_megmarad(
        self, qml_app, qt_app, tmp_path
    ):
        """`__18`: az Escape Cancelként zárja az eszközt, a kiegyenesítés
        marad (a lánc és a csúszkaérték is)."""
        window, edit = self._kiegyenesitett_es_sima(qml_app, qt_app, tmp_path)
        _nezot_nyit(window, qt_app, 0)
        assert _varj(
            qt_app, lambda: abs(edit.property("tiltParam") - TILT) < 1e-6
        )
        panel = _elem(window, "viewerEditorPanel")
        _vagast_nyit(window, qt_app, panel)

        _vagast_zar_escape(window, qt_app, panel)

        assert abs(edit.property("tiltParam") - TILT) < 1e-6
        assert panel.property("straightenActive") is True
        szoveg = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "tilt=1,0.391249,0.000000;" in szoveg
        assert "crop64" not in szoveg
