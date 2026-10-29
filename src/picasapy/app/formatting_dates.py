"""A felvételek dátumainak és az infósáv dátumrészének formázói."""

from __future__ import annotations

import re

from PySide6.QtCore import QDate, QDateTime, QLocale

from .photo_sort import photo_date

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


#: #2565: a kék sáv IDŐZÓNA-JELÖLŐJE. A `timeFormat(LongFormat)` a
#: másodpercet is kiírja (`H:mm:ss tttt`), de a zónanevet is — az
#: összehasonlító felvételen (`141421.jpg`) viszont `2023. 05. 10. 16:30:05`
#: áll, zóna nélkül. A záró zóna-tokent ezért vágjuk le; a formátum maga
#: marad a NYELVTERÜLETÉ, nem égetünk be magyar alakot.
_ZONA_TOKEN = re.compile(r"[\s,]*t+\Z")


def _info_datum(photo, locale: QLocale) -> str:
    """A kék sáv dátuma: EXIF felvételi idő, ennek híján a BEFAGYASZTOTT
    fájlidő (#2486).

    A #2565 nyitott kérdése az volt, honnan ír dátumot az eredeti egy EXIF
    nélküli PNG-hez. A válasz a `docs/specs/pmp-database.md` 10.1/10.3–10.4:
    a Picasa a BEOLVASÁSKORI fájlidőt tartja a saját katalógusában, és a
    pásztázó nem frissíti. Nálunk ez a `PhotoRecord.sort_mtime_ns` — az
    ÉLŐ `mtime`-ot szándékosan NEM használjuk, mert azt minden mentés
    elmozdítja (ez volt a #2486 hibája).

    A formátum a felvételről: rövid dátum + MÁSODPERCES idő, zóna nélkül.
    """
    if photo.taken_at:
        stamp = QDateTime.fromString(photo.taken_at, "yyyy-MM-ddTHH:mm:ss")
    else:
        nanos = getattr(photo, "sort_mtime_ns", 0) or 0
        if nanos <= 0:
            return ""
        stamp = QDateTime.fromMSecsSinceEpoch(nanos // 1_000_000)
    if not stamp.isValid():
        return ""
    alak = (
        locale.dateFormat(QLocale.FormatType.ShortFormat)
        + " "
        + _ZONA_TOKEN.sub("", locale.timeFormat(QLocale.FormatType.LongFormat))
    )
    return locale.toString(stamp, alak)

