"""GPS-koordináták: `.picasa.ini` `geotag=` és EXIF GPS-IFD (#30).

Két forrás van, és a sorrendjük fontos:

1. a **`.picasa.ini` `geotag=`** kulcsa (`szélesség,hosszúság` tizedes
   fokban) — ez a felhasználó/Picasa által adott hely, ez az erősebb;
2. a fájl **EXIF GPS-IFD**-je (fok/perc/másodperc + féltekejelölő) — a
   fényképezőgép/telefon rögzítette hely.

A modul tiszta: nincs se Qt, se index-függés; a beolvasás hibatűrő —
sérült vagy értelmetlen adat `None`, sosem kivétel (a #301 elve: egy hibás
mező nem viheti el az egész beolvasást).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

# EXIF: a GPS-IFD mutatója és a benne használt címkék.
_GPS_IFD_TAG = 0x8825
_LAT_REF, _LAT, _LON_REF, _LON = 1, 2, 3, 4

_LAT_LIMIT = 90.0
_LON_LIMIT = 180.0
# a Picasa hat tizedesjegyet ír (kb. 10 cm felbontás)
_PRECISION = 6


@dataclass(frozen=True)
class GeoPoint:
    """Egy hely tizedes fokban; a létrehozáskor validál."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -_LAT_LIMIT <= self.latitude <= _LAT_LIMIT:
            raise ValueError(f"Érvénytelen földrajzi szélesség: {self.latitude}")
        if not -_LON_LIMIT <= self.longitude <= _LON_LIMIT:
            raise ValueError(f"Érvénytelen földrajzi hosszúság: {self.longitude}")

    def as_geotag(self) -> str:
        """A `.picasa.ini` `geotag=` értéke — a Picasa alakjában."""
        return format_geotag(self.latitude, self.longitude)


def format_geotag(latitude: float, longitude: float) -> str:
    """`szélesség,hosszúság` a Picasa formátumában — MINDIG hat tizedesjegy.

    ⚠️ **A záró nullákat NEM vágjuk le** (#2012). A régi változat
    `rstrip("0")`-t hívott, azzal az indokkal, hogy „a kerek koordináta ne
    `33.770556000` alakban íródjon vissza" — ez az indok téves volt: a
    `%.6f` sosem ad hatnál több tizedest, tehát a levágás kizárólag olyan
    jegyeket vett el, amiket a Picasa megtart. Nem volt olyan eset, amiben
    segített volna.

    Mért bizonyíték a hat tizedesjegyre:

    - a `Picasa3.exe` a `geotag` kulcsot (`0x00c81874`, írás `0x007d582e`)
      `%lf,%lf` formátummal írja (`0x00c8187c`, a `sprintf` `0x007d57fb`);
      MSVC-ben a `printf`-beli `%lf` azonos a `%f`-fel, tehát hat tizedes;
    - a tulajdonos 859 fájlos `.picasa.ini`-korpuszában mind a **84** valós
      `geotag=` érték 6/6 tizedesjeggyel áll.

    A BEOLVASÁS (`parse_geotag`) változatlanul tűrő marad: a korábbi
    verzióink írta rövid alakot is el kell tudni olvasni.
    """
    point = GeoPoint(float(latitude), float(longitude))
    return ",".join(
        f"{value:.{_PRECISION}f}" for value in (point.latitude, point.longitude)
    )


def parse_geotag(text: str | None) -> GeoPoint | None:
    """A `geotag=` érték értelmezése; hibás/üres érték `None`.

    Tűrő: a záró mezőket (magasság stb.) figyelmen kívül hagyja, a
    szóközöket megeszi — a round-trip elv miatt az EREDETI szöveget úgyis
    az ini-réteg őrzi, ide csak a megjelenítéshez kell a szám."""
    if not text:
        return None
    parts = [part.strip() for part in str(text).split(",")]
    if len(parts) < 2:
        return None
    try:
        latitude = float(parts[0])
        longitude = float(parts[1])
    except ValueError:
        return None
    try:
        return GeoPoint(latitude, longitude)
    except ValueError:
        return None


def _rational(value) -> float | None:
    """EXIF-racionális (vagy sima szám) → float; nullosztás esetén None."""
    try:
        numerator, denominator = value.numerator, value.denominator
    except AttributeError:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if not denominator:
        return None
    return numerator / denominator


def _degrees(values) -> float | None:
    """(fok, perc, másodperc) → tizedes fok; hiányos adat esetén None."""
    try:
        parts = list(values)
    except TypeError:
        return None
    if len(parts) < 2:
        return None
    numbers = [_rational(part) for part in parts[:3]]
    if any(number is None for number in numbers):
        return None
    degrees = numbers[0] + numbers[1] / 60.0
    if len(numbers) > 2:
        degrees += numbers[2] / 3600.0
    return degrees


def _signed(degrees: float | None, reference) -> float | None:
    """Déli/nyugati féltekén a koordináta negatív."""
    if degrees is None:
        return None
    marker = str(reference or "").strip().upper()[:1]
    return -degrees if marker in ("S", "W") else degrees


def gps_from_exif(exif) -> GeoPoint | None:
    """Egy MÁR beolvasott EXIF-blokk GPS-koordinátája (`Image.getexif()`).

    A `metadata.reader` ezt hívja, hogy a fájl egyetlen megnyitásból adja
    az összes metaadatot — a hely nem kerül külön fájlolvasásba."""
    try:
        gps = exif.get_ifd(_GPS_IFD_TAG)
    except (AttributeError, OSError, ValueError):
        return None
    if not gps:
        return None
    latitude = _signed(_degrees(gps.get(_LAT)), gps.get(_LAT_REF))
    longitude = _signed(_degrees(gps.get(_LON)), gps.get(_LON_REF))
    if latitude is None or longitude is None:
        return None
    try:
        return GeoPoint(latitude, longitude)
    except ValueError:
        return None


def read_exif_gps(path: str | Path) -> GeoPoint | None:
    """A fájl EXIF GPS-koordinátája; hiány/hiba esetén `None`.

    Nem dob: a nem kép, a sérült EXIF és a hiányos GPS-blokk is `None`."""
    try:
        with Image.open(Path(path)) as image:
            return gps_from_exif(image.getexif())
    except (
        OSError,
        UnidentifiedImageError,
        ValueError,
        AttributeError,
        Image.DecompressionBombError,
    ):
        return None


def photo_location(geotag: str | None, path: str | Path | None) -> GeoPoint | None:
    """A kép helye: az ini `geotag=` az erősebb, utána az EXIF GPS.

    Ez az egyetlen igazságforrás a sorrendre — az indexelő és a
    tulajdonságok-panel is ezt hívja, hogy sose térjenek el."""
    point = parse_geotag(geotag)
    if point is not None:
        return point
    if path is None:
        return None
    return read_exif_gps(path)
