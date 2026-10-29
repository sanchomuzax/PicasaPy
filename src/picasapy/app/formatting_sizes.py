"""Fájlméret- és fényképezőgép-számok Picasa-formátumban."""

from __future__ import annotations

from PySide6.QtCore import QLocale

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
    „0 KB" volt) és a GB/TB fokozatot nem ismerte. A számot Python fixpontos
    formázása állítja elő, a területi beállítás szerinti tizedesjellel; így
    nem kerülnek bele a `printf` formátumában nem szereplő ezreselválasztók.
    """
    for limit, label, decimals in _SIZE_TIERS:
        if size_bytes < limit:
            unit = limit // 1024
            value = size_bytes / unit if unit > 1 else float(size_bytes)
            return tr(label).replace(
                "%1", _fixed_number(value, decimals, locale)
            )
    return tr("%1 TB").replace(
        "%1", _fixed_number(size_bytes / 1024**4, 1, locale)
    )


def _fixed_number(value: float, decimals: int, locale: QLocale) -> str:
    """Python `printf`-szerű fixpontos alak, csoportosítás nélkül."""
    result = f"{value:.{decimals}f}"
    decimal_point = locale.decimalPoint()
    return result.replace(".", decimal_point) if decimal_point != "." else result


def format_exposure(seconds: float, locale: QLocale) -> str:
    """Záridő fotós alakban a MÉRT formátumokkal (#866).

    Az eredeti két erőforrást tart rá: `1/%ds` az 1 másodperc alattira és
    `%2.1fs` a fölöttire (`il_NerdView::4` és `::5`,
    `docs/specs/picasa-hisztogram.md` 6.). A hosszú expozíció tehát MINDIG
    egy tizedesjeggyel jelenik meg — a korábbi `g`-formátum 4 értékes
    jegyre kerekített (`2.5` helyett `2.500`, `10` helyett `10.00`)."""
    if 0 < seconds < 1:
        return f"1/{round(1 / seconds)} s"
    return f"{locale.toString(seconds, 'f', 1)} s"

