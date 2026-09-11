"""Valós fényképek TULAJDONSÁGAIVAL bíró teszt-fixture-ök (#1620).

A tesztjeink döntő része apró, sima JPEG-en fut (`jpeg_factory.py`). A
valódi fényképek viszont olyan eseteket hoznak, amiket az soha: EXIF-
orientáció, progresszív kódolás, CMYK, beágyazott színprofil, 16 bites
PNG, nagy felbontás.

**Miért generálunk, és nem töltünk le.** A tulajdonos felvetésére adott
válasz (#1620 komment): egy letöltött korpusz vagy nagy, vagy bizonytalan
eredetű, és a CI-t is lassítja. Az itteni képek **kicsik,
determinisztikusak, jogtiszták**, és mindkét CI-lábon futnak.

⚠️ **Amit ez NEM ad:** valódi fényképezőgépek szokatlan vagy sérült
metaadatát. Ha az hiányzik, az külön jegy és a tulajdonos gépéről
származó minta — nem letöltés.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import piexif
from PIL import Image, ImageCms


#: Az EXIF `Orientation` mind a nyolc állása (1–8). A 2, 4, 5, 7 TÜKRÖZÖTT
#: — ezek a ritkák, és ezeken bukik a legtöbb feldolgozó.
ORIENTACIOK = (1, 2, 3, 4, 5, 6, 7, 8)

#: Az elforgatott állások: a 5–8 a kép SZÉLESSÉGÉT és MAGASSÁGÁT is
#: felcseréli, ha a megjelenítő alkalmazza az orientációt.
FEKVOBOL_ALLO = (5, 6, 7, 8)


def _alap_kep(meret: tuple[int, int]) -> Image.Image:
    """Determinisztikus, fotószerű színátmenet — nem egyszínű mező.

    Az egyszínű kép a kicsinyítést, a JPEG-tömörítést és a hasonlósági
    méréseket is hazuggá teszi: minden algoritmus átmegy rajta.
    """
    szelesseg, magassag = meret
    x = np.linspace(0, 255, szelesseg, dtype=np.float32)[None, :]
    y = np.linspace(0, 255, magassag, dtype=np.float32)[:, None]
    voros = np.broadcast_to(x, (magassag, szelesseg))
    zold = np.broadcast_to(y, (magassag, szelesseg))
    kek = (x + y) / 2
    rgb = np.stack([voros, zold, np.broadcast_to(kek, (magassag, szelesseg))], axis=2)
    return Image.fromarray(rgb.astype(np.uint8), mode="RGB")


def orientacios_jpeg(
    utvonal: Path, orientacio: int, meret: tuple[int, int] = (60, 40)
) -> Path:
    """Fekvő kép a megadott EXIF `Orientation` értékkel."""
    kep = _alap_kep(meret)
    exif = piexif.dump({"0th": {piexif.ImageIFD.Orientation: orientacio}})
    kep.save(utvonal, "JPEG", quality=92, exif=exif)
    return utvonal


def progressziv_jpeg(utvonal: Path, meret: tuple[int, int] = (120, 90)) -> Path:
    """Progresszív (többmenetes) JPEG — a fényképezőgépek és a webes
    feldolgozók gyakori kimenete."""
    _alap_kep(meret).save(utvonal, "JPEG", quality=90, progressive=True)
    return utvonal


def cmyk_jpeg(utvonal: Path, meret: tuple[int, int] = (120, 90)) -> Path:
    """CMYK JPEG — nyomdai anyagból származó kép."""
    _alap_kep(meret).convert("CMYK").save(utvonal, "JPEG", quality=90)
    return utvonal


def szinprofilos_jpeg(utvonal: Path, meret: tuple[int, int] = (120, 90)) -> Path:
    """Beágyazott ICC-profillal ellátott JPEG."""
    profil = ImageCms.createProfile("sRGB")
    _alap_kep(meret).save(
        utvonal, "JPEG", quality=90, icc_profile=ImageCms.ImageCmsProfile(profil).tobytes()
    )
    return utvonal


def tizenhat_bites_png(utvonal: Path, meret: tuple[int, int] = (60, 40)) -> Path:
    """16 bit/csatorna szürkeárnyalatos PNG — szkennelt és HDR forrás."""
    szelesseg, magassag = meret
    x = np.linspace(0, 65535, szelesseg, dtype=np.uint16)[None, :]
    adat = np.broadcast_to(x, (magassag, szelesseg)).astype(np.uint16)
    Image.fromarray(adat, mode="I;16").save(utvonal, "PNG")
    return utvonal


def nagy_jpeg(utvonal: Path, meret: tuple[int, int] = (2000, 1500)) -> Path:
    """Nagy felbontású JPEG — a redukált dekódolás ágát ez éri el."""
    _alap_kep(meret).save(utvonal, "JPEG", quality=85)
    return utvonal


def jpeg_bajtok(utvonal: Path) -> bytes:
    return Path(utvonal).read_bytes()


def kep_merete(bajtok: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(bajtok)) as kep:
        return kep.size
