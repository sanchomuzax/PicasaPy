"""A Picasa-projekt album-mezői túlélik az újramentést (#1274).

## A tulajdonos jelentése

> „Sőt, más típusok esetén is elvesznek a kollázsképtípus beállítások,
> amiket a Picasa 3 állított be."

## A mérés — mi van a valódi Picasa-fájlokban

A 12 golden mintán (`referencia/kollazs-golden/`) végigmérve:

| mező | hány mintában |
|---|---|
| `albumUID` | **12 / 12** |
| `albumDate` | **12 / 12** |
| `albumID` | 0 / 12 |
| `spacing` | 3 (csak a rácsos témák) |

Az `albumUID` és az `albumDate` tehát az eredeti MINDEN kollázsában ott
van — nálunk viszont sem az írás, sem a visszatöltés nem ismerte őket.
Egy Picasával készült kollázs újramentése **eldobta** mindkettőt.

⚠️ Ezek a panelen nem SZERKESZTHETŐK, és nem is kell hogy azok legyenek:
a helyes viselkedés az, hogy **változatlanul mennek vissza**. Kitalálni
sem szabad őket — ha nincs a fájlban, marad üresen (a saját `.cxf`-jeink
albumUID-ja külön jegy: #1092).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.collage.cxf import loads
from support.jpeg_factory import make_jpeg

UID = "a4ef8e0fd2dbb152d25d79eb2bd2a28b"
DATUM = "2023. november"


class _Photos:
    def __init__(self):
        self.photos = []


@pytest.fixture
def host(qt_app, tmp_path):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "Kollázsok"))

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos()

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

    peldany = _Host()
    yield peldany
    assert peldany.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


def _picasa_kollazs(tmp_path, kepek) -> str:
    """Picasa-stílusú `.cxf` + a mellette álló kép — albumUID-dal."""
    mappa = tmp_path / "Kollázsok"
    mappa.mkdir(exist_ok=True)
    kep = mappa / "AI.jpg"
    make_jpeg(kep, size=(400, 300))
    csomopontok = "".join(
        f' <node x="0.1" y="0.1" w="0.3" h="0.3" theta="0.0" scale="1.0">\r\n'
        f"  <theme>noborder</theme>\r\n"
        f"  <src>{ut}</src>\r\n"
        f" </node>\r\n"
        for ut in kepek
    )
    (mappa / "AI.cxf").write_text(
        '<?xml version="1.0" encoding="utf-8" ?>\r\n'
        f'<collage version="2" format="4:3" orientation="landscape" '
        f'theme="picturepile" shadows="1" captions="1" albumUID="{UID}">\r\n'
        " <albumTitle>AI</albumTitle>\r\n"
        f" <albumDate>{DATUM}</albumDate>\r\n"
        ' <background type="solid" color="FFD5D9AB"/>\r\n'
        ' <spacing value="0.000000"/>\r\n' + csomopontok + "</collage>\r\n",
        encoding="utf-8",
    )
    return str(kep)


class TestAMegnyitasMegtartja:
    def test_az_albumUID_es_a_datum_a_panelre_kerul(self, host, tmp_path):
        ut = _picasa_kollazs(tmp_path, [])

        host.openCollageProject(ut)

        assert host._collage_panel_album_uid == UID
        assert host._collage_panel_album_date == DATUM

    def test_ures_fajlnal_ures_marad(self, host, tmp_path):
        """Kitalálni nem szabad: ami nincs a fájlban, az üres."""
        mappa = tmp_path / "Kollázsok"
        mappa.mkdir(exist_ok=True)
        kep = mappa / "sajat.jpg"
        make_jpeg(kep, size=(400, 300))
        (mappa / "sajat.cxf").write_text(
            '<?xml version="1.0" encoding="utf-8" ?>\r\n'
            '<collage version="2" format="4:3" orientation="landscape" '
            'theme="picturepile" shadows="0" captions="0">\r\n'
            ' <background type="solid" color="FFFFFFFF"/>\r\n'
            ' <spacing value="0.000000"/>\r\n'
            "</collage>\r\n",
            encoding="utf-8",
        )

        host.openCollageProject(str(kep))

        assert host._collage_panel_album_uid == ""
        assert host._collage_panel_album_date == ""


class TestAzUjramentesMegorzi:
    def test_a_piszkozat_visszairja_az_album_mezoket(self, host, tmp_path):
        """A piszkozat ugyanazon a `project_from_nodes`-on megy ki."""
        forras = tmp_path / "kepek"
        forras.mkdir()
        kepek = []
        for nev in ("a.jpg", "b.jpg"):
            make_jpeg(forras / nev, size=(80, 60))
            kepek.append(str(forras / nev))
        host.openCollageProject(_picasa_kollazs(tmp_path, kepek))

        host.saveCollageDraft()

        piszkozat = host._collage_panel_draft_dir() / "autosave.cxf"
        assert piszkozat.is_file(), "nem született piszkozat"
        projekt = loads(piszkozat.read_bytes())
        assert projekt.album_uid == UID, "az albumUID elveszett újramentéskor"
        assert projekt.album_date == DATUM, "az albumDate elveszett újramentéskor"
