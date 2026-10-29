"""Az export műveleti bemenetei és eredményei."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportItem:
    """Egy exportálandó elem: forrásfájl + beégetendő forgatás (90°-os
    lépések) + opcionális `filters=` lánc (nyers, szerializált formában,
    ahogy a `.picasa.ini`-ben/indexben áll). Az aktuális cropot külön,
    a forrás képszekciójának `crop=` kulcsából olvassuk."""

    source: Path
    rotate_steps: int = 0
    #: #2902: tükrözés-jelző (`1` = függőleges, `2` = vízszintes) — a
    #: forgatás párja, ugyanúgy beégetendő, hogy az exportált fájl a rácsban
    #: látott képpel egyezzen.
    flip_flags: int = 0
    filters: str | None = None
    # #1166: a `.picasa.ini` `caption`/`keywords` mezője ÁTKERÜL a
    # célmappába — az eredetiben ezt a közös kimeneti mag (`CImageOutput`,
    # `0x0073f320`) végzi. Üresen hagyva nem születik ini a célban.
    caption: str | None = None
    keywords: str | None = None
    # #4332: az indexben tárolt dátumfelülírás kerül az export EXIF-jébe.
    taken_at_override: str | None = None


@dataclass(frozen=True)
class ExportReport:
    """Az exportfutás eredménye: kész célfájlok és sikertelen források.

    A `reasons` a `failed`-del párhuzamos, azonos hosszúságú, emberi
    olvasásra szánt hibaüzenet-lista (#136) — a UI-hibajelzéshez, hogy a
    felhasználó lássa, MELYIK fájl és MIÉRT hiúsult meg, ne csak a számot."""

    exported: tuple[Path, ...]
    failed: tuple[Path, ...]
    reasons: tuple[str, ...] = ()
    # #1166: a KÖTEG szintű hiba fajtája — a hívó ebből választja ki az
    # eredeti Picasa saját üzenetét (`IDS_DESTDIRCANNOCREATE`,
    # `CExportPrefsPage::deleteerror` stb.), ahelyett hogy nyers OS-hibát
    # mutatna. Üres sztring = nincs köteg-szintű hiba.
    error_kind: str = ""

