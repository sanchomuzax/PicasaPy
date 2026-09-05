"""Megjelenítési formázók: méret, dátum, infó-sáv és Tulajdonságok-panel
szövegépítése (#150 — az AppControllerből kiemelve).

Tiszta függvények: nincs Qt-objektum-állapotuk, a lokalizációt a hívó adja
át (`locale` + a fordítási kontextust őrző, kötött `tr`). Így a fordítások
kontextusa változatlanul az `AppController` marad."""

from __future__ import annotations

import itertools
import re
import sys
from pathlib import Path

from PySide6.QtCore import QDate, QDateTime, QLocale, QUrl

from picasapy.metadata import read_exif_details

from .photo_sort import photo_date

# útvonal-vég leválasztása mappa-névhez (per- és backslash-tűrő)
PATH_TAIL = re.compile(r"[/\\]")

#: A FÉNYKÉPEZŐGÉP számainak locale-ja: C, azaz PONT a tizedesjel — akkor
#: is, ha a felhasználó rendszere magyar (#664, ADR-004:
#: `docs/decisions/tizedesjel.md`).
#:
#: Az eredeti Picasa két külön úton írt ki számokat. A gép adatai (rekesz,
#: fókusztávolság, záridő, tárgytávolság, GPS) nyers `printf`-fel készültek
#: a lefordított formátumsztringből — a hivatalos MAGYAR szövegkészletben
#: is `f/%3.1f` és `%2$3.1f mm` áll (ld. `docs/specs/histogram-reference.md`
#: H.3) —, tehát mindig ponttal. A KÖNYVTÁR adatai (fájlméret, darabszám,
#: dátum) ezzel szemben a Windows területi számformázóján mentek át, tehát
#: magyar rendszeren vesszővel jelentek meg; azok nálunk is a hívótól kapott
#: `locale`-t használják.
#:
#: NE cseréld vissza `QLocale()`-ra „következetességből": az `f/2,8` nem
#: hűségjavítás, hanem hűség-rontás.
_EXIF_LOCALE = QLocale.c()


def _platform() -> str:
    """Cserélhető platform-fogantyú (#1217).

    A `to_local_path` windowsos ága enélkül CSAK Windowson volna mérhető —
    a #1626 pontosan attól maradt észrevétlen, hogy a hiba a windows-lábon
    keletkezett, a fejlesztés viszont Linuxon folyt."""
    return sys.platform


#: Meghajtóbetűs útvonal elé tett per (`/C:/Users/...`) — a `file:///C:/...`
#: alakú URL-ek természetes maradéka.
_MEGHAJTOS_ELOTAG = re.compile(r"^/[A-Za-z]:(?:[/\\]|$)")


def to_local_path(path_or_url: str) -> str:
    """file:// URL vagy sima útvonal → OS-natív lokális útvonal.

    A QUrl.toLocalFile Windowson per-jeles utat ad (C:/...) — a Path-on
    átfuttatás normalizálja, különben ugyanaz a mappa két alakban
    szerepelhetne a figyeltek közt.

    ⚠️ #1626: a Qt a meghajtóbetű ELÉ tett perjelet (`file:///C:/x` →
    `/C:/x`) csak Windowson szedi le — a `QUrlPrivate::toLocalFile`
    megfelelő ága `#ifdef Q_OS_WIN` alatt áll. Ezt itt a `_platform()`
    fogantyún át magunk is elvégezzük: Windowson a Qt már megtette, tehát
    a minta nem is illeszkedik, Linuxon viszont a fogantyú átállításával a
    **windowsos ág mérhetővé válik**. A `\\C:\\...` alakon a `mkdir`
    `WinError 123`-mal elhasal — a #1626-ban emiatt nem készült el a KML.
    """
    text = path_or_url.strip()
    if text.startswith("file:"):
        text = QUrl(text).toLocalFile()
        if _platform().startswith("win") and _MEGHAJTOS_ELOTAG.match(text):
            text = text[1:]
    return str(Path(text)) if text else ""


def to_file_url(path: str) -> QUrl:
    """Lokális útvonal → `file:` URL a QML `Image.source`-ának (#1009).

    A `to_local_path` PÁRJA, az ellenkező irányban — és nem kényelmi
    függvény: **kézzel fűzött URL-t írni hibás**.

    | amit írni szoktak | windowsos útvonalra | ékezetes/`#`-es névre |
    |---|---|---|
    | `"file://" + út` | **érvénytelen** URL (a `C:` portnak látszik, a `QUrl` üresre normalizál) | a `#` levágja a nevet |
    | `"file:" + út` | véletlenül működik | a `#` levágja a nevet |
    | `QUrl.fromLocalFile(út)` | helyes | helyes (százalékos kódolás) |

    A `"file://"`-os alak a #1009-ben éles hibát okozott: a kollázs
    háttérkép-előnézete Windowson MINDEN útvonalra üres maradt — a
    windows-CI-láb fogta meg. Üres bemenetre üres (érvénytelen) URL jár,
    hogy a QML `source`-a törölhető legyen."""
    text = (path or "").strip()
    return QUrl.fromLocalFile(text) if text else QUrl()


#: A Picasa MAGYAR méretformátumai (#526), a CD-diavetítő 37 nyelvű
#: szövegkészletéből (ugyanaz a séma, mint a `Picasa3i18n.dll`-é):
#:
#:     il_FormatBigB  = "%.0f bájt"   il_FormatBigKB = "%.0f KB"
#:     il_FormatBigMB = "%.1f MB"     il_FormatBigGB = "%.1f GB"
#:     il_FormatBigTB = "%.1f TB"
#:
#: Vagyis: „bájt" KISBETŰVEL, bájt és KB EGÉSZ számra, MB-tól EGY tizedes.
#: (küszöb, felirat, tizedesjegyek)
_SIZE_TIERS = (
    (1024, "%1 bytes", 0),
    (1024**2, "%1 KB", 0),
    (1024**3, "%1 MB", 1),
    (1024**4, "%1 GB", 1),
)


def format_size(size_bytes: int, locale: QLocale, tr) -> str:
    """Fájlméret a Picasa magyar formátumai szerint (#526).

    A korábbi változat 1 MB alatt MINDIG KB-ot írt (egy 300 bájtos fájl így
    „0 KB" volt) és a GB/TB fokozatot nem ismerte.
    """
    for limit, label, decimals in _SIZE_TIERS:
        if size_bytes < limit:
            unit = limit // 1024
            value = size_bytes / unit if unit > 1 else float(size_bytes)
            return tr(label).replace("%1", locale.toString(value, "f", decimals))
    return tr("%1 TB").replace(
        "%1", locale.toString(size_bytes / 1024**4, "f", 1)
    )


def long_date(iso: str, locale: QLocale) -> str:
    """Picasa-stílusú hosszú dátum: `2026. január 2., péntek`.

    #526 — TUDATOS ELTÉRÉS: az eredeti Picasa magyar szövegkészletében a
    dátum/idő formátumok LEFORDÍTATLANUL maradtak (`ytDateTime::Format1 =
    "%1$s %2$d, %3$d"`, azaz „hónap nap, év", és 12 órás AM/PM-es idő). Az
    a NEM magyar sorrend és óraformátum — egy fordítási hiányosság, nem
    szándékos alak. Nálunk a helyes magyar alak marad (`ÉÉÉÉ. hónap N.`,
    24 órás idő); ezt egy későbbi „hűségjavítás" NE rontsa vissza.
    """
    date = QDate.fromString(iso[:10], "yyyy-MM-dd")
    return locale.toString(date, QLocale.FormatType.LongFormat)


def photo_dates(records) -> list[str]:
    """Egy KÉPHALMAZ dátumai növekvő sorrendben, ISO-alakban (#2304).

    A mappa-fejléc (`first_date_text`), az állapotsor dátumtartománya
    (`status_text`) és — a `controller._show`-n át — a `folderDateText`
    property KÖZÖS forrása, hogy a három felirat ne mondhasson mást
    ugyanarról a mappáról.

    **Mindent vagy semmit tartalék.** Ha a halmazban akár EGYETLEN
    felvételi idő is van, kizárólag a felvételi idők számítanak; a
    fájlidőre csak akkor esünk vissza, ha EGYIK rekordnak sincs
    `taken_at`-je. Ez szándékosan szűkebb, mint a rekordonkénti
    visszaesés (`photo_sort.photo_date`): ott a cél egy teljes rendezés,
    itt egy szélsőérték, és a rekordonkénti tartalék mellett egyetlen
    romlott vagy régi `mtime`-ú fájl egy EXIF-fel bíró mappa dátumát is
    évekkel korábbra húzná. A mérés (#2304, a tulajdonos `AI` mappája: 82
    médiafájl, egyikben sincs EXIF felvételi idő) csak a „egyetlen képnek
    sincs EXIF-je" esetet fedi — a tartalék se tegyen többet annál.

    **A fájlidő dobhat.** A `photo_date` a `datetime.fromtimestamp`-en át
    megy, ami romlott indexsorra kivételt ad (mérve: `mtime_ns = 10**26`
    → `OSError: [Errno 75] Value too large for defined data type`). Az
    ilyen rekordot KIHAGYJUK: a fejléc-építés a rács `_show`-jának
    közepén fut, egyetlen hibás sor nem viheti ki az egész rácsot.
    """
    taken = sorted(record.taken_at for record in records if record.taken_at)
    if taken:
        return taken
    fallback: list[str] = []
    for record in records:
        try:
            fallback.append(photo_date(record))
        except (OSError, ValueError, OverflowError):
            continue
    return sorted(fallback)


def first_date_text(records, locale: QLocale) -> str:
    """A csoport fejléc-dátuma: a legkorábbi felvétel hosszú dátuma.

    #2304 (1. eltérés): EXIF-felvételi idő híján a FÁJL ideje a tartalék
    (a részletek és a hatókör a `photo_dates`-nél). Enélkül egy csupa
    EXIF-nélküli mappa (letöltött vagy generált képek) fejléce dátum
    NÉLKÜL maradt, holott az eredeti Picasa ott is ír dátumot.

    **A tartalék hatóköre — mely `taken_at`-olvasók kapják meg és melyek
    nem.** Megkapja mind a négy hely, amely egy MAPPA (vagy képhalmaz)
    EGÉSZÉT datálja: a rács rendezőkulcsa (`photo_sort.photo_date`), az
    állapotsor dátumtartománya (`status_text`), a mappa indexelt dátuma
    (`index/sync._sync_folder_date`) és — ötödikként, a `photo_dates`-en
    át — a `controller._show` `folderDateText`-je. NEM kapja meg viszont
    egyetlen olyan olvasó sem, amely EGY KÉP saját felvételi idejét
    mutatja vagy írja: a kék infó-sáv (`photo_info_text`), a nyomtatás
    képfelirata (`print_controller`), a dátum-átállítás és az időbélyeg
    (`photo_ops_controller`), a keresés és a lekérdezések
    (`search_results`, `index/queries`, `models`). Ott a fájlidő nem
    tartalék, hanem hazugság lenne: a felhasználó azt látná, hogy a
    képnek van felvételi ideje, holott nincs.
    """
    dates = photo_dates(records)
    return long_date(dates[0], locale) if dates else ""


def format_exposure(seconds: float, locale: QLocale) -> str:
    """Záridő fotós alakban: 1 mp alatt `1/N s`, fölötte `N s`."""
    if 0 < seconds < 1:
        return f"1/{round(1 / seconds)} s"
    return f"{locale.toString(seconds, 'g', 3)} s"


def _dimensions_text(photo, tr) -> str:
    """`SZxM képpont` szöveg a felbontáshoz."""
    return (
        tr("%1x%2 pixels")
        .replace("%1", str(photo.width))
        .replace("%2", str(photo.height))
    )


def photo_info_text(photo, locale: QLocale, tr) -> str:
    """A kék infó-sáv kijelöléskori tartalma, Picasa-stílusban:
    `név   dátum   SZxM képpont   méret`."""
    parts = [photo.name]
    if photo.taken_at:
        taken = QDateTime.fromString(photo.taken_at, "yyyy-MM-ddTHH:mm:ss")
        parts.append(locale.toString(taken, QLocale.FormatType.ShortFormat))
    if photo.width and photo.height:
        parts.append(_dimensions_text(photo, tr))
    parts.append(format_size(photo.size, locale, tr))
    return "   ".join(parts)


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
    "Uncompressed": "Uncompressed",
    "JPEG": "JPEG",
    "AdobeDeflate": "Adobe Deflate",
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


def properties_entries(photo, locale: QLocale, tr) -> list:
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
    entries.extend(exif_entries(photo, locale, tr))
    return entries


def _movie_entries(photo, locale: QLocale, tr) -> list:
    """A `properties.xml` videó-mezői (`MovieLength`, `MovieRate`).

    ŐSZINTESÉG: az indexben ma NINCS videó-hossz/képsebesség (a
    `PhotoRecord`-ban nem szerepel), és a projektben nincs videó-dekóder,
    amiből kiolvashatnánk. Amíg ez nincs meg, a videó ugyanazt a három
    alapsort kapja, mint a kép — a mezők HELYE viszont rögzített, hogy az
    adat megjelenésekor csak az olvasót kelljen bekötni.
    """
    del locale, tr
    return []


def _enum_entry(value, tr) -> str | None:
    """Felsorolt EXIF-érték → lefordított felirat (ismeretlenre: None)."""
    label = _ENUM_LABELS.get(value)
    return tr(label) if label else None


def exif_entries(photo, locale: QLocale, tr) -> list:
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
    add("Camera Date", date(details.datetime_original))
    add("Digitized Date", date(details.datetime_digitized))
    add("Modified Date", date(details.datetime_modified))
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
    if details.exposure_seconds:
        add(
            "Exposure Time",
            format_exposure(details.exposure_seconds, _EXIF_LOCALE),
        )
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
        add(
            "White Balance",
            tr("Auto") if details.white_balance == "auto" else tr("Manual"),
        )
    add("Metering Mode", _enum_entry(details.metering_mode, tr))
    add("Exposure Program", _enum_entry(details.exposure_program, tr))
    add("Compression", _enum_entry(details.compression, tr))
    add("Color Space", _enum_entry(details.color_space, tr))
    if details.has_icc_profile:
        add("ICC Profile", tr("Embedded"))
    if details.has_embedded_thumbnail:
        add("Embedded Thumbnail", tr("Yes"))
    if photo.keywords:
        add("Keywords", ", ".join(photo.keywords))
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
        left.append(
            tr("Focal length: %1 mm").replace(
                "%1", _EXIF_LOCALE.toString(details.focal_mm, "g", 4)
            )
        )
    if details.focal_35mm:
        left.append(
            tr("(35 mm equivalent: %1 mm)").replace("%1", str(details.focal_35mm))
        )
    if details.exposure_seconds:
        right.append(format_exposure(details.exposure_seconds, _EXIF_LOCALE))
    if details.f_number:
        right.append(f"f/{_EXIF_LOCALE.toString(details.f_number, 'g', 3)}")
    if details.iso:
        right.append(tr("ISO: %1").replace("%1", str(details.iso)))
    if details.flash_fired is not None:
        right.append(tr("Flash: Fired") if details.flash_fired else tr("Flash: Off"))
    if not left and not right:
        return ""
    rows = itertools.zip_longest(left, right, fillvalue="")
    return "\n".join(f"{lcell}\t{rcell}" for lcell, rcell in rows)


def filter_status_text(records, elapsed: float, locale: QLocale, tr) -> str:
    """A zöld eredménysáv szövege (Picasa-minta)."""
    folders = len({r.folder_path for r in records})
    total_gb = sum(r.size for r in records) / (1024**3)
    return (
        tr("%1 folders / %2 pictures visible (%3 seconds) %4 GB")
        .replace("%1", str(folders))
        .replace("%2", str(len(records)))
        .replace("%3", locale.toString(elapsed, "f", 3))
        .replace("%4", locale.toString(total_gb, "f", 1))
    )


def status_text(records, locale: QLocale, tr, tr_n) -> str:
    """Az alsó állapotsor szövege: darabszám, dátumtartomány, összméret.

    A `tr_n` a többes számot kezelő fordító (`%n picture(s)` minta)."""
    if not records:
        return tr("0 pictures")
    total_mb = sum(r.size for r in records) / (1024 * 1024)
    # #2304: EXIF-felvételi idő híján a FÁJL ideje a tartalék. Enélkül egy
    # csupa EXIF-nélküli mappánál (letöltött vagy generált képek) a
    # dátumtartomány egyszerűen kimaradt az állapotsorból, holott az
    # eredeti Picasa ott is ír dátumot. A `photo_dates` KÖZÖS a
    # mappa-fejléccel, hogy a két felirat ne mondhasson mást ugyanarról a
    # halmazról; a „mindent vagy semmit" tartalék indoklása is ott áll.
    dates = photo_dates(records)
    date_part = ""
    if dates:
        first = long_date(dates[0], locale)
        last = long_date(dates[-1], locale)
        date_part = first if first == last else f"{first}-{last}"
    return tr_n("%n picture(s)", "", len(records)) + (
        f"   {date_part}   " if date_part else "   "
    ) + tr("%1 MB on disk").replace(
        "%1", locale.toString(total_mb, "f", 1)
    )


def build_feed_groups(records, locale: QLocale) -> tuple:
    """Mappa-csoportok a rács-feedhez (#64): az egymást követő azonos
    mappájú futamok, {path, name, start, count, dateText} alakban."""
    runs: list[list] = []
    for row, record in enumerate(records):
        if not runs or runs[-1][0] != record.folder_path:
            runs.append([record.folder_path, row, 0])
        runs[-1][2] += 1
    return tuple(
        {
            "path": path,
            "name": PATH_TAIL.split(path)[-1],
            "start": start,
            "count": count,
            "dateText": first_date_text(records[start : start + count], locale),
        }
        for path, start, count in runs
    )
