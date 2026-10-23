"""#5674: az effekt-színmező pipettája.

Két réteg. Az egységteszt a `pickEffectColor`-t ismert színű próbaképpel
méri. A QML-teszt VALÓDI egérkattintással viszi végig a pipettát: a
pipettagombra, majd a képre kattint, és a színmező a kattintott pixel színét
kell mutassa. Slotot vagy jelet a QML-tesztben nem hívunk közvetlenül.

Kiadáskép: ha a `PICASAPY_5674_KIADASKEP_MAPPA` be van állítva, a pipetta
utáni ablak ide kerül `effekt_pipetta_5674.png` néven.
"""

import os
import re
from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.jpeg_factory import make_minta_jpeg
from tests.app.qml_functional.conftest import _build_qml_app

PIROS_BAL = (200, 40, 90)
KEK_JOBB = (30, 160, 220)
HEX_MINTA = re.compile(r"#[0-9a-f]{6}")
# a Színes árnyalás (PicnikTint) katalógus-alapszíne: a pipetta előtt ez áll
TINT_ALAP = "#80cfff"


def _ketszinu_kep(path: Path) -> Path:
    """40×20-as próbakép: a bal fele `PIROS_BAL`, a jobb `KEK_JOBB`.

    A határ a közepén van, a mintavételi pontok (x = 4 és x = 35) a sávok
    belsejébe esnek, ahol a JPEG-torzítás nem ér el.
    """
    kep = Image.new("RGB", (40, 20), PIROS_BAL)
    kep.paste(KEK_JOBB, (20, 0, 40, 20))
    kep.save(path, "JPEG", quality=100)
    return path


def _kozel(hex_szin: str, rgb: tuple[int, int, int], tures: int = 3) -> bool:
    """A `#rrggbb` szín csatornánként `tures` tűrésen belül van-e `rgb`-hez."""
    csatornak = (int(hex_szin[i:i + 2], 16) for i in (1, 3, 5))
    return all(abs(c - t) <= tures for c, t in zip(csatornak, rgb, strict=True))


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def controller(qt_app, provider):
    from picasapy.app.edit_controller import EditController

    return EditController(provider)


class TestPickEffectColor:
    """`pickEffectColor`: a kattintott pont színe `#rrggbb` alakban."""

    def test_a_kattintott_pont_szinet_hex_alakban_adja(self, controller, tmp_path):
        foto = _ketszinu_kep(tmp_path / "IMG_0001.jpg")
        controller.beginEdit("1", str(foto))

        bal = controller.pickEffectColor(0.1, 0.5)
        jobb = controller.pickEffectColor(0.9, 0.5)

        assert HEX_MINTA.fullmatch(bal) and HEX_MINTA.fullmatch(jobb), (bal, jobb)
        assert _kozel(bal, PIROS_BAL), bal
        assert _kozel(jobb, KEK_JOBB), jobb

    def test_a_kepen_kivuli_pont_ures_sztring(self, controller, tmp_path):
        foto = _ketszinu_kep(tmp_path / "IMG_0001.jpg")
        controller.beginEdit("1", str(foto))

        assert controller.pickEffectColor(5.0, 5.0) == ""

    def test_aktiv_szerkesztes_nelkul_ures_sztring(self, controller):
        assert controller.pickEffectColor(0.5, 0.5) == ""

    def test_csak_a_szint_adja_vissza_nem_ir_lancot(self, controller, tmp_path):
        foto = _ketszinu_kep(tmp_path / "IMG_0001.jpg")
        ini = foto.parent / ".picasa.ini"
        controller.beginEdit("1", str(foto))
        lanc_elott = controller.effectChainCounts
        ini_elott = ini.read_text(encoding="utf-8") if ini.exists() else None

        controller.pickEffectColor(0.1, 0.5)

        assert controller.effectChainCounts == lanc_elott
        ini_utana = ini.read_text(encoding="utf-8") if ini.exists() else None
        assert ini_utana == ini_elott


def _mintakepek(lib: Path) -> None:
    """Mintázatos próbaképek: a kiadáskép valódi képet mutat, nem csempét."""
    make_minta_jpeg(lib / "a.jpg", size=(640, 480), seed=1)
    make_minta_jpeg(lib / "b.jpg", size=(320, 240), seed=2)


@pytest.fixture
def mintakepes_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_mintakepek)


def _find_item(root, name):
    if root.objectName() == name:
        return root
    for child in root.childItems():
        found = _find_item(child, name)
        if found is not None:
            return found
    return None


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _kattints(window, qt_app, elem, fx: float = 0.5, fy: float = 0.5) -> QPoint:
    """Valódi egérkattintás az `elem` (fx, fy) arányú pontjára.

    Visszaadja a kattintás pontját a szcénában, hogy a hívó ugyanazt a
    helyet számolhassa vissza a saját koordinátáiba.
    """
    assert elem is not None and elem.isVisible(), "a célelem nem látszik"
    pont = elem.mapToScene(QPointF(elem.width() * fx, elem.height() * fy))
    egesz = QPoint(round(pont.x()), round(pont.y()))
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, egesz
    )
    qt_app.processEvents()
    return egesz


def _elonezet_kepe(engine):
    """A pillanatnyi előnézet képe: ugyanaz, amit a néző kirajzol."""
    szerkeszto = engine.rootContext().contextProperty("editController")
    azonosito = str(szerkeszto.previewSource).split(
        "image://editpreview/", 1
    )[1].split("?", 1)[0]
    return szerkeszto, szerkeszto._provider.requestImage(azonosito, None, None)


def _varhato_szin(kep, terulet, egesz: QPoint) -> str:
    """A kattintás pixelének színe, a pipetta mintavételi szabálya szerint.

    A QML `mouse.x / width` normált koordinátát ad, a Python ebből
    `round(nx * (szélesség - 1))` pixelt vesz. Ugyanezt számoljuk itt.
    """
    helyi = terulet.mapFromScene(QPointF(egesz))
    x = round(helyi.x() / max(1.0, terulet.width()) * (kep.width() - 1))
    y = round(helyi.y() / max(1.0, terulet.height()) * (kep.height() - 1))
    return kep.pixelColor(x, y).name()


def _nyisd_a_tint_panelt(window, qt_app):
    """A Színes árnyalás effekt paraméter-panelje, valódi kattintással."""
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = window.findChild(QObject, "viewerEditorPanel")
    panel.setProperty("activeTab", 2)
    qt_app.processEvents()
    _kattints(window, qt_app, panel.findChild(QObject, "effectTint"))
    assert panel.property("paramPanelActive") is True
    return panel


def _pipettaz_a_kepen(window, qt_app, engine, panel, fx=0.35, fy=0.6) -> str:
    """Valódi kattintás a pipettagombra, majd a képre. Visszaadja a várt színt."""
    _kattints(window, qt_app, _find_item(panel, "effectParamPipette1"))
    terulet = window.findChild(QObject, "effectColorPickArea")
    assert terulet is not None and terulet.property("visible") is True, (
        "a pipetta gombra kattintás nem indította a pipettamódot"
    )
    pont = terulet.mapToScene(QPointF(terulet.width() * fx, terulet.height() * fy))
    egesz = QPoint(round(pont.x()), round(pont.y()))
    _, kep = _elonezet_kepe(engine)
    varhato = _varhato_szin(kep, terulet, egesz)
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, egesz
    )
    qt_app.processEvents()
    return varhato


def _kiadaskep_mentese(window) -> None:
    """A pipetta utáni ablak mentése, ha a kiadáskép mappája meg van adva."""
    mappa = os.environ.get("PICASAPY_5674_KIADASKEP_MAPPA")
    if not mappa:
        return
    kep = window.grabWindow()
    assert kep.save(str(Path(mappa) / "effekt_pipetta_5674.png")), (
        "a kiadáskép nem menthető"
    )


def test_pipetta_valodi_kattintassal_a_kep_szinet_veszi_at(
    mintakepes_app, qt_app
):
    window, _controller, engine = mintakepes_app
    panel = _nyisd_a_tint_panelt(window, qt_app)
    szin_mezo = _find_item(panel, "effectParamColor1")
    assert szin_mezo is not None and szin_mezo.isVisible()

    varhato = _pipettaz_a_kepen(window, qt_app, engine, panel)

    assert varhato != TINT_ALAP, "a próba értelmetlen: a minta a katalógus színe"
    assert _variant(panel.property("paramEffectValues"))[1] == varhato
    assert szin_mezo.property("currentColor") == varhato
    assert panel.property("effectColorPickerTarget") == -1
    szerkeszto, _ = _elonezet_kepe(engine)
    assert szerkeszto.recentPickerColors[0] == varhato
    _kiadaskep_mentese(window)


def test_megse_utan_a_regi_szin_marad(mintakepes_app, qt_app, tmp_path):
    window, _controller, engine = mintakepes_app
    panel = _nyisd_a_tint_panelt(window, qt_app)
    varhato = _pipettaz_a_kepen(window, qt_app, engine, panel)
    assert varhato != TINT_ALAP, "a próba értelmetlen: a minta a katalógus színe"

    _kattints(window, qt_app, panel.findChild(QObject, "effectParamCancelButton"))

    assert panel.property("paramPanelActive") is False
    ini = tmp_path / "kepek" / ".picasa.ini"
    assert not ini.exists() or "PicnikTint" not in ini.read_text(encoding="utf-8")
    _kattints(window, qt_app, panel.findChild(QObject, "effectTint"))
    assert _variant(panel.property("paramEffectValues"))[1] == TINT_ALAP
    assert _find_item(panel, "effectParamColor1").property("currentColor") == TINT_ALAP


def test_alkalmazas_menti_a_pipettaval_valasztott_szint(
    mintakepes_app, qt_app, tmp_path
):
    window, _controller, engine = mintakepes_app
    panel = _nyisd_a_tint_panelt(window, qt_app)
    varhato = _pipettaz_a_kepen(window, qt_app, engine, panel)
    assert varhato != TINT_ALAP, "a próba értelmetlen: a minta a katalógus színe"

    _kattints(window, qt_app, panel.findChild(QObject, "effectParamApplyButton"))

    ini_szoveg = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
    assert f"PicnikTint=1,0.000000,00{varhato[1:]}" in ini_szoveg
