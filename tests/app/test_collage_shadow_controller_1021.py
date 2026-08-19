"""#1021 — az árnyék paraméterei a VÁSZONNAK, lapegységben.

A #977 az árnyékot a magba tette; a mentett kép azóta jó. Az élő vászon
viszont nem kapott semmit, és a felhasználó a v0.8.4-en jelezte: a
jelölőnégyzet kapcsolgatása nem csinál semmit.

Ez a lap a HIDAT méri: a vezérlő `collageShadow` térképét, ami ugyanabból
a `render_settings()`-ből származik, mint a mentés — tehát a kettő
**nem tud elválni**. A rajzolást a
`qml_functional/test_collage_shadow_canvas_1021.py` méri kirajzolva.

## Miért lapegység és nem képpont

A vászon szélessége az ablaktól függ, a mentett képé 5120. Ha a vezérlő
képpontot adna, a vászon más lenne minden ablakméretnél. A lapegység
(1024, spec 6.1) MINDKÉT rendszerben ugyanaz — a képpontra váltás a
vászon egyetlen szorzója (`unit`).

⚠️ A váltás a mentés SAJÁT lapszélességével történik, nem 1024-gyel
számolva: az eltolás képlete additív tagot is tartalmaz (`+1`, `+2`), ami
nem arányos a lapmérettel. Aki 1024-re számolna, a `+1`-et ötszörösére
nagyítaná.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.collage.nodes import SHEET_UNITS
from picasapy.collage.shadow import shadow_params
from picasapy.collage.shadow_sprite import (
    DATA_URL_PREFIX,
    sprite_border,
    sprite_support,
)
from picasapy.collage.themes import (
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    PICTUREGRID,
    PICTUREPILE,
    REGULARGRID,
)

from support.jpeg_factory import make_jpeg


class _Photo:
    def __init__(self, folder_path, name, caption=None, width=400, height=300):
        self.folder_path = folder_path
        self.name = name
        self.caption = caption
        self.width = width
        self.height = height


class _Photos:
    def __init__(self, photos):
        self.photos = list(photos)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / name, size=(80, 60))
    return root


@pytest.fixture
def host(qt_app, tmp_path, library):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "kimenet"))

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos(
                [
                    _Photo(str(library), "a.jpg", "Alma"),
                    _Photo(str(library), "b.jpg"),
                    _Photo(str(library), "c.jpg", "Cica"),
                ]
            )

        def _get_settings(self):
            return self._settings

    peldany = _Host()
    peldany.openCollage([0, 1, 2])
    yield peldany
    assert peldany.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


def _bekapcsolva(host, theme):
    host.setCollageTheme(theme)
    host.setCollageShadows(True)
    return host.collageShadow


class TestAmikorNincsArnyek:
    def test_a_tobbszoros_exponalasnak_nincs_arnyeka(self, host):
        """A maszk 11. bitje tiltja — nem témanév-hasonlítás.

        A felhasználó be sem tudja kapcsolni; a vásznon sem szabad
        megjelennie."""
        host.setCollageTheme(MULTIEXP)
        host.setCollageShadows(True)
        assert host.collageShadow == {}

    def test_kikapcsolt_jelolonegyzetnel_ures(self, host):
        host.setCollageTheme(PICTUREPILE)
        host.setCollageShadows(False)
        assert host.collageShadow == {}

    def test_a_bekapcsolas_utan_megjelenik(self, host):
        """A jegy bejelentése szó szerint: a kapcsolgatásnak hatása van."""
        host.setCollageTheme(PICTUREPILE)
        host.setCollageShadows(False)
        assert host.collageShadow == {}
        host.setCollageShadows(True)
        assert host.collageShadow != {}


class TestAzErtekek:
    @pytest.mark.parametrize(
        "theme", (PICTUREPILE, PICTUREGRID, FRAMEGRID, REGULARGRID, CONTACTSHEET)
    )
    def test_a_terkep_a_MENTES_parametereit_hozza_lapegysegben(self, host, theme):
        """A vászon és a mentett kép EGY forrásból számol.

        Az elvárt értéket itt a mag `shadow_params`-ából vezetjük le,
        ugyanazzal a lapszélességgel, amit a mentés használ — így a teszt a
        vezérlő átváltását méri, nem a #977 képleteit ismétli meg."""
        terkep = _bekapcsolva(host, theme)
        beallitas = host._render_settings()
        varhato = shadow_params(
            theme,
            page_width=beallitas.width,
            page_height=beallitas.height,
            count=len(host.collageNodes.nodes),
        )
        keppont_per_egyseg = beallitas.width / SHEET_UNITS
        for kulcs, ertek in (
            ("offsetX", varhato.offset_x),
            ("offsetY", varhato.offset_y),
            ("blur", varhato.blur),
        ):
            assert terkep[kulcs] == pytest.approx(ertek / keppont_per_egyseg, rel=1e-9)
        assert terkep["alpha"] == varhato.alpha
        assert terkep["opacity"] == pytest.approx(varhato.opacity)

    @pytest.mark.parametrize("theme", (REGULARGRID, CONTACTSHEET))
    def test_a_racsos_temak_arnyeka_SOTETEBB(self, host, theme):
        """A #977 legkönnyebben elrontható száma, a vászon oldalán is.

        Aki a vásznat egyetlen közös átlátszatlansággal írja meg, négy
        témából kettőt elront — és ez csak a képen látszik."""
        eros = _bekapcsolva(host, theme)["alpha"]
        gyenge = _bekapcsolva(host, PICTUREPILE)["alpha"]
        assert eros == 153 and gyenge == 102, f"{eros} vs {gyenge}"

    def test_az_eltolas_jobbra_le_mutat(self, host):
        """Az árnyék iránya: mindkét eltolás pozitív, az y a nagyobb."""
        terkep = _bekapcsolva(host, PICTUREPILE)
        assert terkep["offsetX"] > 0 and terkep["offsetY"] > terkep["offsetX"]

    def test_az_additiv_tagot_NEM_1024_re_szamolja(self, host):
        """Az eltolás nem arányos a lapmérettel — `+1` / `+2` additív tag.

        Aki a képletet 1024-es lappal futtatná, az additív tagot ötszörösére
        nagyítaná. A különbség mérhető: a Képkupacnál a `+1` a mentés
        léptékén 0,2 lapegység, 1024-es lapon 1,0 volna."""
        terkep = _bekapcsolva(host, PICTUREPILE)
        rossz = shadow_params(
            PICTUREPILE,
            page_width=int(SHEET_UNITS),
            page_height=int(SHEET_UNITS * host.collagePageRatio),
            count=len(host.collageNodes.nodes),
        )
        assert terkep["offsetX"] != pytest.approx(rossz.offset_x, rel=1e-3)


class TestAJelzes:
    def test_a_kapcsolo_ertesit_a_valtozasrol(self, host):
        """Kötés-értesítő nélkül a vászon nem rajzolna újra."""
        host.setCollageTheme(PICTUREPILE)
        host.setCollageShadows(True)
        erkezett = []
        host.collageShadowChanged.connect(lambda: erkezett.append(1))
        host.setCollageShadows(False)
        assert erkezett, "az árnyék kikapcsolása nem értesítette a vásznat"

    def test_a_temavaltas_is_ertesit(self, host):
        host.setCollageTheme(PICTUREPILE)
        erkezett = []
        host.collageShadowChanged.connect(lambda: erkezett.append(1))
        host.setCollageTheme(REGULARGRID)
        assert erkezett, "a témaváltás nem értesítette a vásznat"


class TestACsempe:
    def test_a_csempe_URL_es_meretek(self, host):
        """A vászon egyetlen hívásból kapja a képet ÉS a geometriát.

        Két külön forrás (kép itt, méret ott) előbb-utóbb elválna, és az
        árnyék elcsúszna a csempéjétől."""
        _bekapcsolva(host, PICTUREPILE)
        csempe = host.collageShadowSprite(6.0, 102)
        assert csempe["url"].startswith(DATA_URL_PREFIX)
        assert csempe["support"] == sprite_support(6.0)
        assert csempe["border"] == sprite_border(6.0)

    def test_nulla_elmosasnal_sincs_ervenytelen_meret(self, host):
        """Nagyon kicsi vásznon az elmosás nullához tart; a csempe akkor is
        érvényes marad (a haló legalább 1)."""
        csempe = host.collageShadowSprite(0.0, 102)
        assert csempe["support"] >= 1
        assert csempe["url"].startswith(DATA_URL_PREFIX)
