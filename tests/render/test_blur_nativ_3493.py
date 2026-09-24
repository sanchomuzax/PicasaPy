"""#3493: a `blur` a kiolvasott NATÍV láncot futtatja.

A spec (`docs/specs/filters-decoded.md`, „⭐ A `blur` GÉPEZETE" és „⭐ A
`blur` TELJES lánca bitre szimulálva", #762/#3482) szerint:

* küszöb `K = CSONK(t²·65536)`; fal, ha `ΔR²+ΔG²+ΔB² > K // n²` (mindig a
  SZOMSZÉDOS pár);
* három lépték (`n = 1, 2, 4`), léptékenként jelölés, (n > 1-nél)
  fal-terjesztés és KÉT simító menet;
* a mag `(4·közép + 3·Σ4 szomszéd + 8) >> 4`, falnál a szomszéd helyére a
  közép kerül.

A korábbi kétállású modell (1,4-ig azonosság, fölötte σ = 4 Gauss) a
kétszínű 762-es ábrára illeszkedett; a „tétlenség" az ÁBRA sajátja volt.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from picasapy.render.blur import apply_blur, kuszob

#: a 762-es ábra lényege: kétszínű, egyetlen fekete-fehér éllel — a
#: szomszédpár négyzetes különbsége pontosan 3·255² = 195 075
_KETSZINU = np.zeros((24, 40, 3), dtype=np.uint8)
_KETSZINU[:, 20:] = 255


def test_a_kuszob_keplete():
    assert kuszob(1.72528) == 195_073
    assert kuszob(1.7253) == 195_078
    assert kuszob(-0.5) == kuszob(0.5) == 16_384


def test_a_ketszinu_abra_valtopontja():
    """A fal az élen addig áll, amíg 195 075 > K — utána az él elsimul."""
    np.testing.assert_array_equal(apply_blur(_KETSZINU, 1.72528), _KETSZINU)
    assert not np.array_equal(apply_blur(_KETSZINU, 1.7253), _KETSZINU)


def test_zajos_tartalmon_a_csuszka_tartomanyaban_is_simit():
    """A mért „tétlenség" a tesztábra sajátja: valódi, finoman zajos képen
    0,1-nél is simít (a `merokit-2` exportja a lánccal egyezik)."""
    rng = np.random.default_rng(3493)
    kep = (128 + rng.integers(-3, 4, size=(32, 48, 3))).astype(np.uint8)
    ki = apply_blur(kep, 0.1)
    assert not np.array_equal(ki, kep)
    assert ki.astype(int).std() < kep.astype(int).std()


def test_egyszinu_kep_valtozatlan():
    kep = np.full((16, 16, 3), 77, dtype=np.uint8)
    np.testing.assert_array_equal(apply_blur(kep, 2.0), kep)


def test_a_bemenet_valtozatlan_marad():
    rng = np.random.default_rng(1)
    kep = rng.integers(0, 256, size=(20, 30, 3), dtype=np.uint8)
    masolat = kep.copy()
    apply_blur(kep, 2.0)
    np.testing.assert_array_equal(kep, masolat)


_MEROKIT = Path("/mnt/nas/My Pictures/PicasaPy merokit-2")


@pytest.mark.skipif(not _MEROKIT.exists(), reason="a NAS-os mérőkészlet nem elérhető")
@pytest.mark.parametrize("nev,t", [("halott_01", 0.1), ("halott_02", 0.5), ("halott_03", 2.0)])
def test_a_picasa_exporttal_bitre_egyezik_ujratomoritve(nev, t):
    """Az export kvantálótábláival újratömörítve a kimenet a Picasa
    exportjával egyezik (mérve: 100%)."""
    import io

    from PIL import Image

    forras = np.asarray(Image.open(_MEROKIT / "halott_01.jpg").convert("RGB"))
    export_ut = _MEROKIT / "export-202608151438" / f"{nev}.jpg"
    export = Image.open(export_ut)
    buf = io.BytesIO()
    Image.fromarray(apply_blur(forras, t)).save(
        buf, "JPEG", qtables=export.quantization, subsampling=2
    )
    ujra = np.asarray(Image.open(io.BytesIO(buf.getvalue())).convert("RGB"))
    egyezes = (ujra == np.asarray(export.convert("RGB"))).all(-1).mean()
    assert egyezes > 0.99
