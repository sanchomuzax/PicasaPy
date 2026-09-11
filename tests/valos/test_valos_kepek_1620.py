"""#1620: a lánc VALÓS fénykép-tulajdonságokon — mindkét CI-lábon.

A tesztjeink döntő része apró, sima JPEG-et lát (`tests/support/jpeg_factory.py`).
Ez a fájl a `tests/support/valos_kepek.py` készletével megy végig a
fogyasztókon: EXIF-orientáció mind a nyolc állása, progresszív JPEG, CMYK,
beágyazott ICC-profil, 16 bites PNG, nagy felbontás.

## Amit a készlet MÁR megtalált

Az EXIF-orientáció 5–8 állásában az index a fájlban TÁROLT méretet őrzi
(fekvő), a megjelenített kép viszont álló — a `cvimage` dekódolása
alkalmazza az orientációt. A két adat így ellentmond egymásnak; a
következményeit a #2996 rendezte (0.8.415): az index marad a fájl
igazságánál, a fogyasztók a `metadata.megjelenitett_meret`-et hívják.

## Amit NEM talált (mérve, hogy ne tűnjön hiánynak)

A bélyegkép-készítés, a metaadat-olvasás, a dHash és a szín-elemzés a
készlet MINDEN darabján lefut, kivétel nélkül. A CMYK és a 16 bites PNG
dekódolása képpontra egyezik a Pillow kimenetével.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from picasapy.dedup.phash import compute_dhash
from picasapy.index.colors import compute_photo_color
from picasapy.lazy_cv2 import cv2
from picasapy.metadata.reader import read_exif_details, read_file_metadata
from picasapy.thumbs.cache import ThumbnailCache
from support.valos_kepek import (
    FEKVOBOL_ALLO,
    ORIENTACIOK,
    cmyk_jpeg,
    nagy_jpeg,
    orientacios_jpeg,
    progressziv_jpeg,
    szinprofilos_jpeg,
    tizenhat_bites_png,
)


def _dekodolt(fajl: Path, flag=None):
    bajtok = np.frombuffer(Path(fajl).read_bytes(), np.uint8)
    return cv2.imdecode(bajtok, cv2.IMREAD_COLOR if flag is None else flag)


@pytest.fixture
def keszlet(tmp_path) -> dict[str, Path]:
    """A teljes készlet — nevekkel, hogy a bukás megnevezze a darabot."""
    mappa = tmp_path / "valos"
    mappa.mkdir()
    darabok = {
        f"orientacio-{o}": orientacios_jpeg(mappa / f"o{o}.jpg", o)
        for o in ORIENTACIOK
    }
    darabok["progressziv"] = progressziv_jpeg(mappa / "progressziv.jpg")
    darabok["cmyk"] = cmyk_jpeg(mappa / "cmyk.jpg")
    darabok["szinprofil"] = szinprofilos_jpeg(mappa / "icc.jpg")
    darabok["png16"] = tizenhat_bites_png(mappa / "melyseg.png")
    darabok["nagy"] = nagy_jpeg(mappa / "nagy.jpg", meret=(1200, 900))
    return darabok


class TestALancVegigfut:
    def test_belyegkep_keszul_MINDEN_darabra(self, keszlet, tmp_path):
        gyorstar = ThumbnailCache(tmp_path / "cache")
        hianyzo = []
        for nev, fajl in keszlet.items():
            allapot = fajl.stat()
            kesz = gyorstar.get_or_create(
                fajl, allapot.st_mtime_ns, allapot.st_size
            )
            if kesz is None or not kesz.exists():
                hianyzo.append(nev)
        assert not hianyzo, f"nem készült bélyegkép: {hianyzo}"

    def test_metaadat_olvasas_MINDEN_darabra(self, keszlet):
        rossz = []
        for nev, fajl in keszlet.items():
            meta = read_file_metadata(fajl)
            if not (meta.width and meta.height):
                rossz.append(nev)
            read_exif_details(fajl)
        assert not rossz, f"nincs méret a metaadatban: {rossz}"

    def test_dhash_es_szin_MINDEN_darabra(self, keszlet):
        nincs_hash = [n for n, f in keszlet.items() if compute_dhash(f) is None]
        nincs_szin = [
            n for n, f in keszlet.items() if compute_photo_color(f) is None
        ]
        assert not nincs_hash, f"nincs dHash: {nincs_hash}"
        assert not nincs_szin, f"nincs szín: {nincs_szin}"


class TestAzOrientacio:
    @pytest.mark.parametrize("orientacio", ORIENTACIOK)
    def test_a_dekodolas_alkalmazza_az_orientaciot(self, tmp_path, orientacio):
        """A `thumbs/cache.py` docstringje ezt ÁLLÍTJA — itt mérve."""
        fajl = orientacios_jpeg(
            tmp_path / f"o{orientacio}.jpg", orientacio, meret=(60, 40)
        )
        magassag, szelesseg = _dekodolt(fajl).shape[:2]
        allo_lett = magassag > szelesseg
        assert allo_lett is (orientacio in FEKVOBOL_ALLO), (
            f"a(z) {orientacio}. állás dekódolt alakja {szelesseg}×{magassag}"
        )

    @pytest.mark.parametrize("orientacio", FEKVOBOL_ALLO)
    def test_a_REDUKALT_dekodolas_is_alkalmazza(self, tmp_path, orientacio):
        """A nagy képek a felezett/negyedelt ágon jönnek be (`cvimage`), és
        ott is érvényesülnie kell az orientációnak — máskülönben a nagy és a
        kicsi kép MÁS tájolású lenne."""
        fajl = orientacios_jpeg(
            tmp_path / f"o{orientacio}.jpg", orientacio, meret=(400, 200)
        )
        magassag, szelesseg = _dekodolt(fajl, cv2.IMREAD_REDUCED_COLOR_2).shape[:2]
        assert magassag > szelesseg, "a redukált dekódolás elveszítette az állást"

    @pytest.mark.parametrize("orientacio", FEKVOBOL_ALLO)
    def test_az_orientacio_es_a_tarolt_meret_ELTER(self, tmp_path, orientacio):
        """⚠️ A MAI állapot mérése, nem helyeslése.

        Az index a fájlban tárolt (fekvő) méretet őrzi, miközben a
        megjelenített kép álló. Aki a `width`/`height` párból arányt számol
        — a kollázs-elrendezés és a néző 1:1 nagyítása —, forgatott képnél
        rossz arányt kapott. **A #2996 ezt eldöntötte** (0.8.415): a
        kanonikus adat MARAD a tárolt méret + az orientáció — az index a
        fájl igazságát tükrözi —, a fogyasztók viszont a
        `metadata.megjelenitett_meret` segéden át a megjelenített méretet
        kérik. Ez a próba ezért továbbra is a TÁROLT értéket állítja, és
        szándékosan marad zöld.
        """
        fajl = orientacios_jpeg(
            tmp_path / f"o{orientacio}.jpg", orientacio, meret=(60, 40)
        )
        meta = read_file_metadata(fajl)
        magassag, szelesseg = _dekodolt(fajl).shape[:2]
        assert (meta.width, meta.height) == (60, 40)
        assert (szelesseg, magassag) == (40, 60)


class TestAKulonlegesFormatumok:
    def test_a_CMYK_dekodolas_egyezik_a_Pillow_eval(self, tmp_path):
        fajl = cmyk_jpeg(tmp_path / "cmyk.jpg")
        cv_kep = _dekodolt(fajl)
        with Image.open(fajl) as kep:
            pil = np.array(kep.convert("RGB"))
        elteres = np.abs(cv_kep[:, :, ::-1].astype(int) - pil.astype(int)).max()
        assert elteres <= 8, f"a két dekóder eltér: {elteres} szint"

    def test_a_16_bites_PNG_felso_bajtja_marad_meg(self, tmp_path):
        fajl = tizenhat_bites_png(tmp_path / "melyseg.png", meret=(64, 8))
        cv_kep = _dekodolt(fajl)
        with Image.open(fajl) as kep:
            pil = np.array(kep)
        assert np.array_equal(cv_kep[4, :, 0], (pil[4] >> 8).astype(np.uint8))

    def test_a_progressziv_JPEG_dekodolhato(self, tmp_path):
        assert _dekodolt(progressziv_jpeg(tmp_path / "p.jpg")) is not None

    def test_a_szinprofil_nem_akasztja_meg_a_metaadatot(self, tmp_path):
        fajl = szinprofilos_jpeg(tmp_path / "icc.jpg")
        assert read_file_metadata(fajl).width == 120
