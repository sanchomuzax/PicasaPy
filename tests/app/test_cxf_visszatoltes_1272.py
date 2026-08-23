"""A `.cxf` beállításai TELJESEN visszajönnek újranyitáskor (#1272, #1274).

## A tulajdonos jelentése (v0.8.51, Windows)

> „Az újra szerkesztésre megnyitott képkollázs esetén elállítódik a
> képarány az utolsó projektben használt négyzetesre. Mindig az utolsó
> használt képerányt erőlteti rá a korábbi szerkesztésére. A régi Picasa
> jól nyitja meg."

> „Sőt, más típusok esetén is elvesznek a kollázsképtípus beállítások,
> amiket a Picasa 3 állított be."

## A gyökér

Az `_apply_cxf_project()` a témát, a tájolást, az árnyékot, a feliratokat,
a címet, a csomópontokat és a hátteret visszaadta — a **lapformátumot** és
a **térközt** nem. Azok a MENTETT beállításból (az utoljára használtból)
éltek tovább, tehát a projekt saját értékét némán felülírták.

⚠️ A mérce a VALÓDI Picasa fájlja, nem a sajátunk: a saját mentés →
saját visszaolvasás kör akkor is konzisztens, ha mindkét oldal ugyanazt
hibázza.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.collage.cxf import loads
from picasapy.collage.page_formats import format_key_of, format_text
from support.jpeg_factory import make_jpeg

GOLDEN = "AI7.cxf"


class _Photo:
    def __init__(self, folder_path, name):
        self.folder_path = folder_path
        self.name = name
        self.caption = None
        self.width = 400
        self.height = 300


class _Photos:
    def __init__(self, photos):
        self.photos = list(photos)


@pytest.fixture
def host(qt_app, tmp_path):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "Kollázsok"))

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos([])

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

    peldany = _Host()
    yield peldany
    assert peldany.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


def _cxf_szoveggel(tmp_path, *, format_text_ertek: str, spacing: str) -> str:
    """Kézzel írt `.cxf` — a MEZŐK a fájlból jönnek, nem a mi írónkból."""
    mappa = tmp_path / "Kollázsok"
    mappa.mkdir(exist_ok=True)
    kep = mappa / "proba.jpg"
    make_jpeg(kep, size=(400, 300))
    (mappa / "proba.cxf").write_text(
        '<?xml version="1.0" encoding="utf-8" ?>\r\n'
        f'<collage version="2" format="{format_text_ertek}" '
        'orientation="landscape" theme="picturegrid" shadows="0" '
        'captions="0">\r\n'
        " <albumTitle>Próba</albumTitle>\r\n"
        ' <background type="solid" color="FFFFFFFF"/>\r\n'
        f' <spacing value="{spacing}"/>\r\n'
        "</collage>\r\n",
        encoding="utf-8",
    )
    return str(kep)


class TestFormatumNevKulcs:
    """A `.cxf` a formátum NEVÉT tárolja — kulccsá kell visszafordítani."""

    @pytest.mark.parametrize(
        "kulcs", ["Desktop4x3", "Square", "A4", "10x15m", "HDTV16x9"]
    )
    def test_a_nev_UGYANARRA_a_lapalakra_jon_vissza(self, kulcs):
        """A név → kulcs irány nem feltétlenül ugyanazt a kulcsot adja.

        ⚠️ Két menütétel viseli ugyanazt a nevet: az `A4` és az
        `A4PageCollage` egyaránt `297:210`. A fájlban csak a NÉV áll, tehát
        a kettő onnan megkülönböztethetetlen — a visszafordítás a menü
        SORRENDJÉBEN elsőt adja. Ami számít, az a lap ALAKJA: annak
        azonosnak kell lennie."""
        vissza = format_key_of(format_text(kulcs))
        assert vissza is not None
        assert format_text(vissza) == format_text(kulcs)

    def test_ismeretlen_nevre_None(self):
        assert format_key_of("nincs:ilyen") is None
        assert format_key_of("") is None

    def test_az_A4_neve_MILLIMETERBEN_van(self):
        """#1089: az A4 neve `297:210`, nem a képpontarány."""
        assert format_text("A4") == "297:210"
        assert format_key_of("297:210") == "A4"


class TestUjranyitas:
    def test_a_kepararany_a_FAJLBOL_jon_nem_a_legutobbibol(self, host, tmp_path):
        """A tulajdonos tünete: mindig az utolsó használtat erőlteti rá."""
        host.setCollageFormat("Square")
        assert host.collageFormatKey == "Square"
        ut = _cxf_szoveggel(tmp_path, format_text_ertek="4:3", spacing="0.000000")

        host.openCollageProject(ut)

        assert host.collageFormatKey == "Desktop4x3", (
            "az újranyitás a legutóbb használt formátumot hagyta a helyén"
        )

    def test_a_terkoz_is_visszajon(self, host, tmp_path):
        host.setCollageSpacing(0.0)
        ut = _cxf_szoveggel(tmp_path, format_text_ertek="4:3", spacing="0.250000")

        host.openCollageProject(ut)

        assert host.collageSpacing == pytest.approx(0.25)

    def test_ismeretlen_formatumnev_nem_ir_felul(self, host, tmp_path):
        """Idegen fájl nem teheti használhatatlanná a panelt."""
        host.setCollageFormat("Desktop4x3")
        ut = _cxf_szoveggel(tmp_path, format_text_ertek="nincs:ilyen", spacing="0")

        host.openCollageProject(ut)

        assert host.collageFormatKey == "Desktop4x3"


class TestValodiPicasaMinta:
    """A mérce a valódi Picasa fájlja, nem a sajátunk."""

    def test_az_AI7_formatuma_visszafordithato(self):
        from pathlib import Path

        minta = Path.home() / "picasapy-agent" / "referencia" / "kollazs-golden"
        if not (minta / GOLDEN).is_file():
            pytest.skip("a golden készlet nincs a gépen")
        projekt = loads((minta / GOLDEN).read_bytes())
        assert projekt.aspect_ratio == "4:3"
        assert format_key_of(projekt.aspect_ratio) == "Desktop4x3"


class TestKeretVisszatoltes:
    """A panel KERET-választója is a projektből jön (#1274).

    A `.cxf` a keretet **csomópontonként** tárolja (`<theme>polaroid</theme>`),
    a panelen viszont EGY keret-választó van. A csomópontok kerete eddig
    visszajött, a panelé nem — ezért az újranyitott polaroidos kollázs
    „nincs keret"-et mutatott, és a KÖVETKEZŐ felvett kép keret nélkül
    került be. A tulajdonos szava: „elvesznek a kollázsképtípus
    beállítások, amiket a Picasa 3 állított be."
    """

    @staticmethod
    def _cxf_kerettel(tmp_path, keretek: list[str]) -> str:
        mappa = tmp_path / "Kollázsok"
        mappa.mkdir(exist_ok=True)
        kep = mappa / "keretes.jpg"
        make_jpeg(kep, size=(400, 300))
        csomopontok = "".join(
            f' <node x="0.1" y="0.1" w="0.3" h="0.3" theta="0.0" scale="1.0">\r\n'
            f"  <theme>{keret}</theme>\r\n"
            f"  <src>kep{i}.jpg</src>\r\n"
            f" </node>\r\n"
            for i, keret in enumerate(keretek)
        )
        (mappa / "keretes.cxf").write_text(
            '<?xml version="1.0" encoding="utf-8" ?>\r\n'
            '<collage version="2" format="4:3" orientation="landscape" '
            'theme="picturepile" shadows="0" captions="0">\r\n'
            " <albumTitle>Keretes</albumTitle>\r\n"
            ' <background type="solid" color="FFFFFFFF"/>\r\n'
            ' <spacing value="0.000000"/>\r\n' + csomopontok + "</collage>\r\n",
            encoding="utf-8",
        )
        return str(kep)

    def test_az_egysegez_keret_visszajon(self, host, tmp_path):
        host.setCollageBorder("noborder")
        ut = self._cxf_kerettel(tmp_path, ["polaroid", "polaroid", "polaroid"])

        host.openCollageProject(ut)

        assert host.collageBorder == "polaroid", (
            "a panel keret-választója a legutóbbin maradt"
        )

    def test_vegyes_keretnel_a_panel_erteke_marad(self, host, tmp_path):
        """Vegyes keretet EGY választó nem tud megjeleníteni — ne hazudjunk."""
        host.setCollageBorder("whiteborder")
        ut = self._cxf_kerettel(tmp_path, ["polaroid", "noborder"])

        host.openCollageProject(ut)

        assert host.collageBorder == "whiteborder"

    def test_csomopont_nelkul_nem_valt(self, host, tmp_path):
        host.setCollageBorder("whiteborder")
        ut = self._cxf_kerettel(tmp_path, [])

        host.openCollageProject(ut)

        assert host.collageBorder == "whiteborder"
