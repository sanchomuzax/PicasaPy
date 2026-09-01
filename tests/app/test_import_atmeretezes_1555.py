"""Az importálás öt átméretezési opciója — #1555.

A mért parancsazonosítók és feltételek (`0x00518b40`):

| azonosító | feltétel        | jelentés      |
|-----------|-----------------|---------------|
| `0x9dfe`  | `[+0x74c] == 0` | eredeti méret |
| `0x9e14`  | `== 0x800`      | 2048 képpont  |
| `0x9dfd`  | `== 0x640`      | 1600 képpont  |
| `0x9e0a`  | `== 0x400`      | 1024 képpont  |
| `0x9e13`  | `== 0x320`      | 800 képpont   |

⚠️ A jegy három szerződést köt ki, és mindhármat külön teszt őrzi:

1. **pontosan** ezek az értékek,
2. a `0` jelentése **„eredeti méret"**, nem „nincs beállítva",
3. a tárolt érték **képpont**, nem sorszám — így egy új méret felvétele
   nem töri el a meglévő beállításokat.

A leskálázás matematikáját NEM írjuk le újra: a `cvimage.scale_down` a
projekt egyetlen „hosszabbik oldal korlátozása, felskálázás soha"
megvalósítása. Ez a fájl a DÖNTÉST és a BEKÖTÉST méri.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QSettings

from picasapy.importsource import (
    ATMERETEZES_EREDETI,
    ATMERETEZES_OPCIOK,
    atmeretez_masolatot,
    atmeretezendo,
)
from support.jpeg_factory import make_jpeg

_CTL = (
    Path(picasapy.app.__file__).parent / "import_source_controller.py"
).read_text(encoding="utf-8")
_DIALOG = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "ImportSourceDialog.qml"
).read_text(encoding="utf-8")


class TestAzOtOpcio:
    def test_pontosan_a_mert_ertekek(self):
        assert ATMERETEZES_OPCIOK == (0, 2048, 1600, 1024, 800)

    def test_a_nulla_az_EREDETI_meret(self):
        assert ATMERETEZES_EREDETI == 0
        assert atmeretezendo(4000, 3000, 0) is False

    def test_a_nagy_kepet_atmeretezi(self):
        assert atmeretezendo(4000, 3000, 2048) is True

    def test_a_KISEBB_kepet_nem_nagyitja_fel(self):
        """Az importálás nem javíthat a felbontáson."""
        assert atmeretezendo(800, 600, 2048) is False

    def test_a_hosszabbik_oldal_dont_allo_kepnel_is(self):
        assert atmeretezendo(600, 4000, 2048) is True


class TestAMasolatLeskalazasa:
    def test_a_masolat_kisebb_lesz(self, tmp_path):
        forras = make_jpeg(tmp_path / "nagy.jpg", size=(3000, 2000))
        masolat = tmp_path / "masolat.jpg"
        masolat.write_bytes(forras.read_bytes())

        assert atmeretez_masolatot(masolat, 1024) is True

        #: ⚠️ A `read_image_bytes` NYERS BÁJTOKAT ad, nem dekódolt képet —
        #: a mérethez dekódolni kell (a `thumbs/cache.py` mintája). Az első
        #: változatom ezt elnézte, és a bájttömb hosszát mérte volna.
        import cv2

        from picasapy.cvimage import read_image_bytes

        kep = cv2.imdecode(read_image_bytes(masolat), cv2.IMREAD_COLOR)
        assert max(kep.shape[0], kep.shape[1]) == 1024

    def test_a_FORRAS_erintetlen(self, tmp_path):
        """A kártyán lévő eredetihez az importálás nem nyúlhat."""
        forras = make_jpeg(tmp_path / "nagy.jpg", size=(3000, 2000))
        elotte = forras.read_bytes()
        masolat = tmp_path / "masolat.jpg"
        masolat.write_bytes(elotte)

        atmeretez_masolatot(masolat, 800)

        assert forras.read_bytes() == elotte

    def test_eredeti_meretnel_NEM_ir(self, tmp_path):
        kep = make_jpeg(tmp_path / "a.jpg", size=(3000, 2000))
        elotte = kep.read_bytes()
        assert atmeretez_masolatot(kep, 0) is False
        assert kep.read_bytes() == elotte

    def test_mar_kicsi_kepet_NEM_ir_ujra(self, tmp_path):
        """Fölösleges újrakódolás minőségromlás, nem nyereség."""
        kep = make_jpeg(tmp_path / "kicsi.jpg", size=(400, 300))
        elotte = kep.read_bytes()
        assert atmeretez_masolatot(kep, 2048) is False
        assert kep.read_bytes() == elotte

    def test_nem_dekodolhato_fajl_ERINTETLEN(self, tmp_path):
        """Videó/RAW/sérült: a másolat nem sérülhet meg."""
        film = tmp_path / "film.mp4"
        film.write_bytes(b"\x00" * 64)
        assert atmeretez_masolatot(film, 800) is False
        assert film.read_bytes() == b"\x00" * 64


class TestABeallitas:
    @pytest.fixture
    def ctl(self, qt_app, tmp_path):
        from picasapy.app.import_source_controller import ImportSourceController

        settings = QSettings(
            str(tmp_path / "s.ini"), QSettings.Format.IniFormat
        )
        return ImportSourceController(
            provider=None,
            add_folder=lambda _p: None,
            index_path=tmp_path / "index.db",
            settings=settings,
        )

    def test_alapbol_eredeti_meret(self, ctl):
        assert ctl.resizeLimit == 0

    def test_az_opciolista_a_mert_otos(self, ctl):
        assert list(ctl.resizeOptions) == [0, 2048, 1600, 1024, 800]

    def test_a_valasztas_megmarad(self, ctl):
        ctl.setResizeLimit(1600)
        assert ctl.resizeLimit == 1600

    def test_ISMERETLEN_ertekre_nem_ir(self, ctl):
        ctl.setResizeLimit(1600)
        ctl.setResizeLimit(1234)
        assert ctl.resizeLimit == 1600

    def test_ismeretlen_TAROLT_ertek_az_eredetire_esik_vissza(
        self, qt_app, tmp_path
    ):
        """Kézzel írt beállításfájl vagy jövőbeli verzió: inkább ne
        méretezzünk át, mint hogy félreértett számra vágjunk."""
        from picasapy.app.import_source_controller import (
            RESIZE_SETTINGS_KEY,
            ImportSourceController,
        )

        settings = QSettings(
            str(tmp_path / "s.ini"), QSettings.Format.IniFormat
        )
        settings.setValue(RESIZE_SETTINGS_KEY, 999)
        settings.sync()
        ctl = ImportSourceController(
            provider=None,
            add_folder=lambda _p: None,
            index_path=tmp_path / "index.db",
            settings=settings,
        )
        assert ctl.resizeLimit == 0

    def test_a_tarolt_ertek_KEPPONT_nem_sorszam(self, qt_app, tmp_path):
        """A jegy kulcs-szerződése: a beállításfájlban a képpont áll."""
        from picasapy.app.import_source_controller import (
            RESIZE_SETTINGS_KEY,
            ImportSourceController,
        )

        settings = QSettings(
            str(tmp_path / "s.ini"), QSettings.Format.IniFormat
        )
        ctl = ImportSourceController(
            provider=None,
            add_folder=lambda _p: None,
            index_path=tmp_path / "index.db",
            settings=settings,
        )
        ctl.setResizeLimit(800)
        settings.sync()
        assert int(settings.value(RESIZE_SETTINGS_KEY)) == 800


class TestABekotes:
    def test_a_masolasi_hurok_HASZNALJA(self):
        """A #1798 osztálya: a beállítás ne legyen néma."""
        kezd = _CTL.index("target = copy_photo(candidate.path, subdir)")
        blokk = _CTL[kezd : kezd + 700]
        assert "atmeretez_masolatot(target, resize_limit)" in blokk

    def test_a_hatart_a_szal_INDULASAKOR_olvassuk(self):
        """A `QSettings` a GUI-szálé; a fél feladat két méretben már nem
        visszakövethető."""
        assert "resize_limit = self.resizeLimit" in _CTL
        assert _CTL.index("resize_limit = self.resizeLimit") < _CTL.index(
            "atmeretez_masolatot(target, resize_limit)"
        )

    def test_van_valaszto_a_parbeszedben(self):
        assert 'objectName: "importSourceResizeBox"' in _DIALOG
        assert "importSourceController.setResizeLimit(" in _DIALOG

    def test_a_valaszto_a_VEZERLOTOL_kapja_az_opciokat(self):
        """Beégetett lista két igazságforrás lenne."""
        assert "importSourceController.resizeOptions" in _DIALOG
        assert "2048" not in _DIALOG
