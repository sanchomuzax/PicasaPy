"""A nyers (RAW) fájlok dekódolása — a #528 őre.

## Mit mér ez a lap

A `scanner/filetypes.py` 2026 óta **felismeri** a nyers fájlokat
(`media_kind_of` → `"raw"`), a képbetöltés viszont mindenhol
`cv2.imdecode`-dal ment, aminek **nincs nyers dekódere** — a nyers fájlok
bekerültek az indexbe, de nem jelent meg belőlük kép.

A tesztek egy **valódi**, 6,5 KB-os CFA DNG-n futnak
(`tests/support/raw_factory.py`) — tehát a LibRaw tényleg dekódol, nem
utánzatot mérünk. Amit ez a minta nem mér (színhelyesség,
gyártóspecifikus MakerNote, beágyazott előnézet), azt a fixture
docstringje mondja ki.

## Mért tény a jegy mintáján — a beágyazott előnézet NEM garantált

A jegy „gyors út" pontja azt írta, hogy „a legtöbb nyers fájl tartalmaz
beágyazott JPEG-előnézetet". A jegy saját Leica-mintáján
(`RAW_LEICA_DIGILUX2_SRGB.RAW`, 2568 × 1928) ez **megdőlt**:
`rawpy.extract_thumb()` → `LibRawNoThumbnailError: No thumbnail in file`.
A teljes demozaikolás 0,39 s volt (RPi5). ⇒ a beágyazott előnézet
**gyorsítás**, nem a működés feltétele; a dekódolónak enélkül is
működnie kell. Ezt a `test_beagyazott_elonezet_nelkul_is_dekodol` köti ki.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import numpy as np
import pytest

from picasapy.lazy_cv2 import cv2
from picasapy.scanner.filetypes import RAW_EXTENSIONS, media_kind_of

from picasapy import rawdecode
from tests.support.raw_factory import MAGASSAG, SZELESSEG, ir_dng

# ⛔ Itt SZÁNDÉKOSAN nincs `importorskip`: a `rawpy` a `pyproject.toml`
# futásidejű függősége, tehát ha hiányzik, ez a lap BUKJON — a kihagyott
# teszt nem őr, csak zöld pipa.


@pytest.fixture
def dng(tmp_path: Path) -> Path:
    return ir_dng(tmp_path / "minta.dng")


class TestAKiterjesztesFelismerese:
    def test_a_nyers_kiterjesztes_nyersnek_szamit(self, dng: Path):
        assert media_kind_of(dng.name) == "raw"
        assert rawdecode.nyers_utvonal(dng)

    def test_a_jpeg_nem_nyers(self, tmp_path: Path):
        assert not rawdecode.nyers_utvonal(tmp_path / "a.jpg")

    def test_a_felismert_es_a_dekodolhato_keszlet_EGYEZIK(self):
        """A jegy elfogadási feltétele: a `filetypes` listája és amit a
        dekóder vállal, ne csúszhasson el egymástól."""
        assert rawdecode.NYERS_KITERJESZTESEK == RAW_EXTENSIONS


class TestADekodolas:
    def test_a_cv2_NEM_birja_a_nyers_fajlt(self, dng: Path):
        """A kiinduló hiba rögzítése: emiatt kell külön ág."""
        bajtok = np.fromfile(dng, dtype=np.uint8)
        assert cv2.imdecode(bajtok, cv2.IMREAD_COLOR) is None

    def test_a_nyers_dekoder_BGR_kepet_ad(self, dng: Path):
        kep = rawdecode.dekodol_nyerset(dng)
        assert kep is not None
        assert kep.shape == (MAGASSAG, SZELESSEG, 3)
        assert kep.dtype == np.uint8

    def test_beagyazott_elonezet_nelkul_is_dekodol(self, dng: Path):
        """A generált DNG-ben NINCS beágyazott előnézet — ahogy a jegy
        Leica-mintájában sem. A teljes demozaikolásra kell esnie."""
        assert rawdecode.beagyazott_elonezet(dng) is None
        assert rawdecode.dekodol_nyerset(dng) is not None

    def test_a_serult_nyers_fajl_None_es_NAPLOZ(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ):
        """Néma üres kép TILOS: a hívó `None`-t kap (placeholder), és a
        napló megnevezi a fájlt."""
        rossz = tmp_path / "csonka.dng"
        rossz.write_bytes(b"II*\x00" + b"\x00" * 64)
        with caplog.at_level(logging.WARNING, logger="picasapy.rawdecode"):
            assert rawdecode.dekodol_nyerset(rossz) is None
        assert "csonka.dng" in caplog.text

    def test_a_hianyzo_rawpy_NAPLOZ_es_nem_dob(
        self, dng: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ):
        """Ha a `rawpy` nincs telepítve, a program nem eshet össze — de a
        napló mondja ki, MIÉRT nincs kép."""
        monkeypatch.setattr(rawdecode, "_rawpy", lambda: None)
        with caplog.at_level(logging.WARNING, logger="picasapy.rawdecode"):
            assert rawdecode.dekodol_nyerset(dng) is None
        assert "rawpy" in caplog.text


class TestABelyegkepUt:
    def test_a_racs_belyegkepe_elkeszul_nyers_fajlbol(self, tmp_path: Path):
        """Az elfogadási feltétel első pontja: megjelenik a bélyegkép."""
        from picasapy.thumbs.cache import ThumbnailCache

        forras = ir_dng(tmp_path / "kep.dng")
        cache = ThumbnailCache(tmp_path / "gyorstar", size=32)
        stat = forras.stat()
        eredmeny = cache.get_or_create(forras, stat.st_mtime_ns, stat.st_size)
        assert eredmeny is not None and eredmeny.exists()
        belyeg = cv2.imdecode(
            np.fromfile(eredmeny, dtype=np.uint8), cv2.IMREAD_COLOR
        )
        assert belyeg is not None
        assert max(belyeg.shape[:2]) == 32


class TestANagyNezet:
    """Az elfogadási feltétel második pontja: a nagy nézetben is megnyílik.

    A `QImageReader`-nek nincs nyers beolvasója, tehát a szerkesztő-előnézet
    útján is kell az elágazás — enélkül a nyers fájl a nézőben üres.
    """

    def test_a_QImageReader_NEM_birja_a_nyers_fajlt(self, dng: Path):
        from PySide6.QtGui import QImageReader

        olvaso = QImageReader(str(dng))
        assert olvaso.read().isNull()

    def test_az_elonezet_dekodolja_a_nyers_fajlt(self, dng: Path):
        from picasapy.app.edit_preview import _decode_source

        tomb = _decode_source(dng)
        assert tomb is not None
        assert tomb.shape == (MAGASSAG, SZELESSEG, 3)

    def test_az_elonezet_korlatozza_a_nyers_kep_meretet(self, tmp_path: Path):
        """A nagy nyers kép az előnézeten sem lehet nagyobb a korlátnál — a
        GUI-szálon futó renderelésnek ez a védelme (#819)."""
        from picasapy.app.edit_preview import _MAX_PREVIEW_EDGE, _decode_source

        nagy = ir_dng(tmp_path / "nagy.dng", _MAX_PREVIEW_EDGE + 400, 600)
        tomb = _decode_source(nagy)
        assert tomb is not None
        assert max(tomb.shape[:2]) == _MAX_PREVIEW_EDGE

    def test_teljes_felbontason_nincs_korlat(self, tmp_path: Path):
        from picasapy.app.edit_preview import _MAX_PREVIEW_EDGE, _decode_source

        nagy = ir_dng(tmp_path / "nagy.dng", _MAX_PREVIEW_EDGE + 400, 600)
        tomb = _decode_source(nagy, full_res=True)
        assert tomb is not None
        assert max(tomb.shape[:2]) == _MAX_PREVIEW_EDGE + 400


class TestAMappaBorito:
    def test_a_nyers_borito_ikonja_elkeszul(self, tmp_path: Path):
        from picasapy.app.folder_cover_provider import IKON_MERET, _olvasd_be

        forras = ir_dng(tmp_path / "borito.dng", 400, 300)
        kep = _olvasd_be(forras)
        assert kep is not None
        assert max(kep.shape[:2]) == IKON_MERET


#: A jegy valódi Leica-mintája. Nincs a repóban (9,9 MB), a privát
#: képleltárban él — az útvonalat környezeti változóval kapja a futtató.
MINTA_VALTOZO = "PICASAPY_NYERS_MINTA"


@pytest.mark.skipif(
    not os.environ.get(MINTA_VALTOZO),
    reason=f"a valódi nyers minta útvonala nincs megadva ({MINTA_VALTOZO})",
)
class TestAValodiKameraMinta:
    """A jegy Leica-mintája — ⚠️ **a CI-n EZ MINDIG KIMARAD.**

    Kimondva, hogy ne olvasódjon őrnek: a 9,9 MB-os kameragyártmány nem
    tehető a repóba, tehát ez a két teszt csak azon a gépen fut, ahol a
    `PICASAPY_NYERS_MINTA` a minta útvonalára mutat. A kódutakat a fenti,
    generált DNG-s lapok őrzik — ez itt a valódi fájl egyszeri, megismételhető
    ellenőrzése, nem a hálózat foga.

    A 2026-09-14-i helyi mérés (RPi5, LibRaw 0.21.4): 2568 × 1928,
    `postprocess` 0,39 s, beágyazott előnézet **nincs**.
    """

    @pytest.fixture
    def minta(self) -> Path:
        return Path(os.environ[MINTA_VALTOZO])

    def test_a_valodi_minta_dekodolodik(self, minta: Path):
        kep = rawdecode.dekodol_nyerset(minta)
        assert kep is not None
        assert (kep.shape[1], kep.shape[0]) == (2568, 1928)

    def test_a_valodi_mintaban_NINCS_beagyazott_elonezet(self, minta: Path):
        """A jegy „gyors út" feltevésének mért cáfolata."""
        assert rawdecode.beagyazott_elonezet(minta) is None
