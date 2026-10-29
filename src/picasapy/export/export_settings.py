"""Az exportálás beállításai és JPEG-minőség-leképezése."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportSettings:
    """Export-beállítások: leghosszabb oldal (None = eredeti), JPEG-minőség,
    sorszámozás (#369: „Add numbers to file names to preserve order") és
    opcionális vízjel-szöveg (#369)."""

    max_dimension: int | None = None
    jpeg_quality: int = 85
    # #369 (export.fen): a fájlnevek elé "001-", "002-", ... kerül, a
    # bemeneti (kijelölés-)sorrendet őrizve — mert a célmappában a fájlrendszer
    # ábécésorrendje egyébként felülírná azt.
    add_numbers: bool = False
    # #369 (export.fen): jobb alsó sarokba égetett szöveg, fehér, félig
    # átlátszó — a Picasa mintáját közelítve (ld. _apply_watermark).
    watermark_text: str | None = None
    # #1166 (export.fen `radiogroup name="movies"`): „Teljes film (nincs
    # átméretezés)" = a videó bájthű másolása (alapértelmezés), „Első
    # képkocka" = az első kocka képként. Az eredeti alapértéke a
    # `Preferences\FileExportMovie`-ból jön (`0x00738c88`–`0x00738cb3`):
    # nem nulla → teljes film, nulla/hiányzó → első képkocka.
    movie_full: bool = True
    # #1138 (spec 3.3 és 7.1): az „Automatikus" fokozat az eredetiben NEM
    # szám, hanem KÜLÖN LOGIKAI JELZŐ (`[objektum+0xa40] = 1`,
    # `0x00739c4d`), és a kimenet a FORRÁS JPEG-kvantálási tábláit veszi át
    # — mérve: a forrás és a Picasa exportjának DQT-je bájtra azonos,
    # miközben a fájlméret más (tehát tényleg újrakódolt). Bekapcsolva a
    # `jpeg_quality` már csak VISSZAESÉS: nem JPEG forrásnál vagy
    # olvashatatlan táblánál.
    quality_automatic: bool = False
    # #4017: a rögzített Picasa-leképezésben csak a Maximális használ
    # 4:4:4-et; a többi választás 4:2:0. Az Automatikus JPEG-forrásnál ezt
    # a forrás JPEG mintája felülírja.
    jpeg_subsampling: int = 2

    def __post_init__(self) -> None:
        if self.max_dimension is not None and self.max_dimension < 1:
            raise ValueError(f"Érvénytelen max_dimension: {self.max_dimension}")
        if not 1 <= self.jpeg_quality <= 100:
            raise ValueError(f"Érvénytelen jpeg_quality: {self.jpeg_quality}")
        if self.jpeg_subsampling not in (0, 1, 2):
            raise ValueError(f"Érvénytelen jpeg_subsampling: {self.jpeg_subsampling}")


# #4017 (kontrollált Picasa-export, picasa-colab-jobs #87–#91): a tényleges
# kimeneti JPEG alapján a Maximum IJG q=93 és 4:4:4; a Normal q=85, a
# Minimum q=65. Az Automatic a forrás DQT-jét és JPEG-mintáját viszi tovább,
# a Custom a csúszkán kapott minőséget használja. Ez felülírja a korábbi,
# bináris 193-as választási értékből levezetett „szándékosan 100” közelítést.
# A presetválasztás nyers értékei továbbra is a binárisból ismertek:
# a választás (0…4) a `0x00739c3f`-nél kezdődő ágon dől el, az ugrótábla
# `0x00739ef4`-en áll (levezetés: docs/specs/export-parbeszed.md 7. szakasz):
#
#   Normál     = 85  (`0x55`, `0x00739caf`)
#   Maximális  = 193 (`0xC1`, `0x00739ca1`; a kontrollált kimenet q=93)
#   Minimális  = 65  (`0x41`, `0x00739ca8`)
#
# #1138: az "automatic" SZÁMA is a binárisból való: az ugrótábla 0. ága
# ugyanoda fut, mint a "normal" — 85 (`0x00739caf`). A kettőt a `+0xa40`
# jelző különbözteti meg, és a jelző hatása az, hogy a kimenet a FORRÁS
# kvantálótábláit kapja (`ExportSettings.quality_automatic`). A 85 tehát
# itt már nem „közelítés", hanem a mért visszaesési érték arra az esetre,
# amikor nincs honnan táblát venni (nem JPEG forrás).
_AUTOMATIC_QUALITY = 85
_QUALITY_PRESETS: dict[str, int] = {
    "automatic": _AUTOMATIC_QUALITY,
    "normal": 85,
    "maximum": 93,
    "minimum": 65,
}

#: #1138 (spec 3.3): az „Automatikus" fokozat kulcsa — nem szám, hanem
#: külön logikai jelző az eredetiben is.
_AUTOMATIC_KEY = "automatic"


def is_automatic_quality(preset: str) -> bool:
    """Az „Automatikus" fokozatot választották-e (#1138).

    Külön kérdés a `resolve_export_quality`-tól, mert az eredetiben is
    külön logikai jelző (`[objektum+0xa40] = 1`, `0x00739c4d`), nem a
    minőségszám hordozza: a szám ugyanaz a 85, mint a „Normál"-nál."""
    return (preset or "").strip().lower() == _AUTOMATIC_KEY


def resolve_export_subsampling(preset: str) -> int:
    """A mért leképezés: Maximum 4:4:4, a többi fokozat 4:2:0 (#4017).

    Az Automatikus JPEG-forrás esetén a kódoló a forrás mintáját olvassa ki;
    ez az érték csak annak a visszaesési módja, ha nincs átvehető forrás.
    Pillow-kódolásnál a 0 = 4:4:4, 1 = 4:2:2, 2 = 4:2:0.
    """
    return 0 if (preset or "").strip().lower() == "maximum" else 2


def resolve_export_quality(preset: str, custom: int) -> int:
    """Minőség-preset névből (a QML popup elemeiből) konkrét JPEG-minőség.

    `preset`: "normal" | "maximum" | "minimum" | "custom" | "automatic"
    (kis-nagybetűtől független); ismeretlen/üres preset — és maga
    "automatic" is — a mért 85-re esik vissza (ld. `_AUTOMATIC_QUALITY`).
    `custom` csak `preset == "custom"` esetén számít, és 0–100 közé kell
    essen: a 21 fogásos egyéni csúszka 0-s állása 0×5 = 0-t adna, amit az
    IJG-kódoló maga emel 1-re (`if (quality <= 0) quality = 1`) — ezt itt
    tesszük meg, hogy a felület legalsó fogása se dobjon kivételt."""
    key = (preset or "").strip().lower()
    if key == "custom":
        if custom == 0:
            custom = 1
        if not 1 <= custom <= 100:
            raise ValueError(f"Érvénytelen egyéni minőség: {custom}")
        return custom
    return _QUALITY_PRESETS.get(key, _AUTOMATIC_QUALITY)

