"""EXIF-adatok, fényképezőgép-összefoglaló és tulajdonságsorok."""

from __future__ import annotations

import itertools
from pathlib import Path

from PySide6.QtCore import QDateTime, QLocale

from picasapy.metadata import read_exif_details

from .crt_g_format import picasa_szam
from .formatting_info import _dimensions_text
from .formatting_sizes import _EXIF_LOCALE, format_exposure, format_size
from .tulajdonsag_sorok import file_date_text, person_tags_text

#: A `Flash` EXIF-mező és a többi felsorolt érték Picasa-kulcsszavai →
#: angol felirat. A magyar a `picasapy_hu.ts`-ben él, a
#: `Picasa3i18n.dll`-ből kinyert szótár szerint (#529,
#: `referencia/exif-cimkek-en-hu.tsv`) — így a nyers EXIF-kulcs SOSEM
#: kerül a felületre.
_ENUM_LABELS = {
    "Unknown": "Unknown",
    "Average": "Average",
    "CenterWeight": "Center Weight",
    "Spot": "Spot",
    "MultiSpot": "Multi-spot",
    "Pattern": "Pattern",
    "Partial": "Partial",
    "Other": "Other",
    "NotDefined": "Not Defined",
    "Manual": "Manual",
    "NormalProgram": "Normal Program",
    "AperturePriority": "Aperture Priority",
    "ShutterPriority": "Shutter Priority",
    "Creative": "Creative",
    "Action": "Action Program",
    "Portrait": "Portrait",
    "Landscape": "Landscape",
    "sRGB": "sRGB",
    "Uncalibrated": "Uncalibrated",
}

#: #3535: a Tömörítés sor `EXIF::…` azonosítói → az eredeti alapszövege
#: (spec `picasa-metaadat-tulajdonsagok.md` 14.). A magyar a `stringres`
#: szerint a `picasapy_hu.ts`-ben; a `JBIG B&W`-nek nincs magyar szövege.
_COMPRESSION_LABELS = {
    "Uncompressed": "Uncompressed",
    "CCITT1D": "CCITT 1D",
    "T4/Group3Fax": "T4/Group 3 Fax",
    "T6/Group4Fax": "T6/Group 4 Fax",
    "LZW": "LZW",
    "JPEGOldStyle": "JPEG (old-style)",
    "JPEG": "JPEG",
    "AdobeDeflate": "Adobe Deflate",
    "JBIGB&W": "JBIG B&W",
    "JBIGColor": "JBIG Color",
    "Kodak262": "Kodak 262",
    "Next": "Next",
    "SonyARWCompressed": "Sony ARW Compressed",
    "EpsonERFCompressed": "Epson ERF Compressed",
    "PackBits": "PackBits",
    "Thunderscan": "Thunderscan",
    "KodakKDCCompressed": "Kodak KDC Compressed",
    "IT8CTPAD": "IT8CTPAD",
    "IT8LW": "IT8LW",
    "IT8MP": "IT8MP",
    "IT8BL": "IT8BL",
    "PixarFilm": "PixarFilm",
    "PixarLog": "PixarLog",
    "Deflate": "Deflate",
    "DCS": "DCS",
    "JBIG": "JBIG",
    "SGILog": "SGILog",
    "SGILog24": "SGILog24",
    "JPEG2000": "JPEG 2000",
    "NikonNEFCompressed": "Nikon NEF Compressed",
    "MDIBinaryLevelCodec": "MDI Binary Level Codec",
    "MDIProgressiveTransformCodec": "MDI Progressive Transform Codec",
    "MDIVector": "MDI Vector",
    "KodakDCRCompressed": "Kodak DCR Compressed",
    "PentaxPEFCompressed": "Pentax PEF Compressed",
}

#: Az EXIF-tájolás nyolc értéke — a Picasa is szöveggel írja ki.
_ORIENTATION_LABELS = {
    1: "Normal",
    2: "Mirrored",
    3: "Rotated 180°",
    4: "Mirrored and rotated 180°",
    5: "Mirrored and rotated 90° CCW",
    6: "Rotated 90° CW",
    7: "Mirrored and rotated 90° CW",
    8: "Rotated 90° CCW",
}


def properties_entries(photo, locale: QLocale, tr, contacts_xml=None) -> list:
    """A Tulajdonságok-panel (#13/#529) sorai: (címke, érték) párok.

    A sorrend a Picasa saját `runtime/properties.xml`-jét követi (#529) — a
    38 LÁTHATÓ mezőt, abban a sorrendben. Az adat nélküli mezők KIMARADNAK
    (nem üres sorként jelennek meg), ahogy az eredetiben is.

    Az alap-adatok az indexből jönnek; az EXIF-mezők igény szerinti
    fájl-olvasással (csak a panel megnyitásakor fut, griden sosem).
    """
    entries: list = [
        (tr("File Path"), str(Path(photo.folder_path) / photo.name)),
        (tr("File Size"), format_size(photo.size, locale, tr)),
    ]
    if photo.width and photo.height:
        entries.append((tr("Dimensions"), _dimensions_text(photo, tr)))
    if photo.kind != "photo":
        entries.extend(_movie_entries(photo, locale, tr))
        return entries
    entries.extend(exif_entries(photo, locale, tr, contacts_xml))
    return entries


def _movie_entries(photo, locale: QLocale, tr) -> list:
    """A `properties.xml` videómezői, az eredeti panel-sorrendben (#4580)."""
    entries = []
    if photo.movie_format:
        entries.append((tr("Movie Info"), photo.movie_format))
    if photo.frame_rate is not None:
        rate = locale.toString(float(photo.frame_rate), "g", 6)
        entries.append((tr("Movie Rate"), f"{rate} fps"))
    if photo.duration_seconds is not None:
        entries.append(
            (tr("Movie Length"), _movie_duration_text(photo.duration_seconds))
        )
    return entries


def _movie_duration_text(seconds: float) -> str:
    """A videó hossza perc:másodperc vagy óra:perc:másodperc alakban."""
    total_seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def _enum_entry(value, tr) -> str | None:
    """Felsorolt EXIF-érték → lefordított felirat (ismeretlenre: None)."""
    label = _ENUM_LABELS.get(value)
    return tr(label) if label else None


def _compression_entry(value, tr) -> str | None:
    """Tömörítési azonosító → felirat; ismeretlen kódnál (az olvasó a
    számot adja) maga a szám, ahogy az eredeti `%ld`-je (#3535)."""
    if value is None:
        return None
    label = _COMPRESSION_LABELS.get(value)
    return tr(label) if label else value


def exif_entries(photo, locale: QLocale, tr, contacts_xml=None) -> list:
    """A `properties.xml` EXIF-eredetű mezői, EREDETI SORRENDBEN (#529).

    Az adat nélküli mező kimarad. A felsorolt értékek (fénymérés,
    expozíciós program, színtér…) a `Picasa3i18n.dll`-ből kinyert szótár
    szerinti feliratot kapják, nem a nyers EXIF-kulcsot.
    """
    details = read_exif_details(Path(photo.folder_path) / photo.name)
    entries: list = []

    def add(label: str, value) -> None:
        if value not in (None, "", False):
            entries.append((tr(label), value))

    def date(value) -> str | None:
        if not value:
            return None
        stamp = QDateTime.fromString(value, "yyyy-MM-ddTHH:mm:ss")
        return locale.toString(stamp, QLocale.FormatType.ShortFormat)

    add("Camera Make", details.make)
    add("Camera Model", details.model)
    # #4332: a Properties „Camera Date” sora a felhasználói felülírást
    # mutatja; a forrásfájl EXIF-jét a dátummódosító nem írja át.
    add(
        "Camera Date",
        date(getattr(photo, "taken_at_override", None) or details.datetime_original),
    )
    add("Digitized Date", date(details.datetime_digitized))
    add("Modified Date", date(details.datetime_modified))
    add("File Date", file_date_text(photo, locale))
    if details.orientation in _ORIENTATION_LABELS:
        add("Orientation", tr(_ORIENTATION_LABELS[details.orientation]))
    if details.flash_fired is not None:
        add("Flash", tr("Fired") if details.flash_fired else tr("Did not fire"))
    add("Lens", details.lens)
    # #664 / ADR-004: a gép saját számai C-locale-lal (PONT), a fájlé és a
    # dátumé a hívó `locale`-jával — ld. az _EXIF_LOCALE megjegyzését
    if details.focal_mm:
        add("Focal Length", _millimetres(details.focal_mm, _EXIF_LOCALE, tr))
    if details.focal_35mm:
        add(
            "Focal Length in 35mm Film",
            _millimetres(float(details.focal_35mm), _EXIF_LOCALE, tr),
        )
    if details.ccd_width:
        add("CCD Width", picasa_szam(details.ccd_width))
    if details.exposure_seconds:
        add(
            "Exposure Time",
            format_exposure(details.exposure_seconds, _EXIF_LOCALE),
        )
    # #4579: a NYERS APEX-érték, `%.3g`, előtag nélkül (spec 17. B)
    if details.aperture_apex is not None:
        add("Aperture", picasa_szam(details.aperture_apex))
    if details.f_number:
        add("F Number", f"f/{_EXIF_LOCALE.toString(details.f_number, 'g', 3)}")
    if details.subject_distance_m:
        add(
            "Subject Distance",
            tr("%1 m").replace(
                "%1", _EXIF_LOCALE.toString(details.subject_distance_m, "g", 3)
            ),
        )
    if details.iso:
        add("ISO", str(details.iso))
    if details.white_balance:
        # ismeretlen kódnál az olvasó a számot adja: az marad (#3558)
        add(
            "White Balance",
            {"auto": tr("Auto"), "manual": tr("Manual")}.get(
                details.white_balance, details.white_balance
            ),
        )
    add("Metering Mode", _enum_entry(details.metering_mode, tr))
    add("Exposure Program", _enum_entry(details.exposure_program, tr))
    add("Compression", _compression_entry(details.compression, tr))
    add("Color Space", _enum_entry(details.color_space, tr))
    if details.has_icc_profile:
        add("ICC Profile", tr("Embedded"))
    if details.has_embedded_thumbnail:
        add("Embedded Thumbnail", tr("Yes"))
    add("JPEG Quality", details.jpeg_quality)
    if photo.keywords:
        keywords = (
            keyword.strip()
            for keyword in (photo.keywords or "").split(",")
            if keyword.strip()
        )
        add("Keywords", ", ".join(keywords))
    add("People Tags", person_tags_text(photo, details.xmp_people, contacts_xml))
    # a koordináta a Picasában is mindig pontos (`.picasa.ini`
    # `geotag=33.770556,-84.293055`, KML `<longitude>%f`): vesszős
    # tizedesjellel egy koordinátapár olvashatatlan volna
    if details.latitude is not None:
        add("GPS Latitude", _EXIF_LOCALE.toString(details.latitude, "f", 6))
    if details.longitude is not None:
        add("GPS Longitude", _EXIF_LOCALE.toString(details.longitude, "f", 6))
    if details.altitude_m is not None:
        add(
            "GPS Altitude",
            tr("%1 m").replace(
                "%1", _EXIF_LOCALE.toString(details.altitude_m, "g", 5)
            ),
        )
    add("Unique ID", details.image_unique_id)
    return entries


def _millimetres(value: float, locale: QLocale, tr) -> str:
    return tr("%1 mm").replace("%1", locale.toString(value, "g", 4))

def camera_summary_text(details, locale: QLocale, tr) -> str:
    """Picasa-mintájú, KÉToszlopos fényképezőgép-összefoglaló a hisztogram-
    doboz alá (#25, #235). Formátum: soronként `bal\\tjobb` cellapár, a sorok
    `\\n`-nel — a HistogramBox.qml ebből rendereli a két címkézett oszlopot,
    az eredeti Picasa 3 elrendezését követve:

        Xiaomi Mi Note 10            1/125 s
        Fókusztávolság: 6,7 mm       f/1.7
        (35 mm-egyenérték: 24 mm)    ISO: 3200

    Csak a kitöltött mezők kerülnek be; üres string, ha egy sincs (pl. EXIF
    nélküli fájl). `details` egy `ExifDetails` (ld. `metadata.reader`)."""
    # #664 / ADR-004: itt MINDEN szám a gépé, tehát végig C-locale (PONT) —
    # a `locale` paraméter a hívási lánc egységessége miatt marad meg
    left: list[str] = []
    right: list[str] = []
    if details.camera:
        left.append(details.camera)
    if details.focal_mm:
        #: #866: `%3.1f` — EGY tizedesjegy (`il_NerdView::2`). A korábbi
        #: `g`/4 értékes jegy `6.700`-at adott a mért `6.7` helyett.
        left.append(
            tr("Focal length: %1 mm").replace(
                "%1", _EXIF_LOCALE.toString(details.focal_mm, "f", 1)
            )
        )
    if details.focal_35mm:
        left.append(
            tr("(35 mm equivalent: %1 mm)").replace("%1", str(details.focal_35mm))
        )
    if details.exposure_seconds:
        right.append(format_exposure(details.exposure_seconds, _EXIF_LOCALE))
    if details.f_number:
        #: #866: `f/%3.1f` — egy tizedes (`il_NerdView::6`); a `g`/3
        #: `f/1.70`-et adott a mért `f/1.7` helyett.
        right.append(f"f/{_EXIF_LOCALE.toString(details.f_number, 'f', 1)}")
    if details.iso:
        #: #866: `ISO: %2d` — a szám LEGALÁBB két karakter széles, szóközzel
        #: kitöltve (`il_NerdView::7`), és ez az utolsó sor: `\n` nélkül.
        right.append(tr("ISO: %1").replace("%1", f"{int(details.iso):2d}"))
    #: ⛔ #866: VAKU-SOR NINCS. Az eredeti hisztogram-blokkja pontosan hét
    #: formátum-sztringet ismer (`il_NerdView::1..7`, és a `0x00567e10`
    #: másoló is hét mezőt mozgat) — vaku nem szerepel köztük. A vaku-adat
    #: NEM tűnt el: a Tulajdonságok-panel `exif_entries` sora hozza, ahol az
    #: eredetiben is ott van.
    if not left and not right:
        return ""
    rows = itertools.zip_longest(left, right, fillvalue="")
    return "\n".join(f"{lcell}\t{rcell}" for lcell, rcell in rows)

