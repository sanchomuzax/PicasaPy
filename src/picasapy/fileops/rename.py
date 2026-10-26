"""Fájl átnevezése a lemezen — a .picasa.ini szekció követi (#15).

Round-trip elv: a szekció tartalma (star/caption/rotate/filters/… és minden
ismeretlen sor) bitre pontosan megmarad, csak a `[fájlnév]` fejléc változik.

Az ini-írás az útvonalanként szerializált, best-effort konkurenciakezelésű
`update_document`-en megy (#295): a betöltés és az előzetes ujjlenyomat-
ellenőrzés között észlelt Picasa-változás újratöltést vált ki. A sikeres
ellenőrzés és fájlcsere közti külső írás elveszhet.

#366/#5941: `rename_photos_many` a `rename.fen` tömeges módja: alapnév +
opcionális dátum-/felbontás-utótag; csak foglalt cél esetén keres `-001`,
`-002`… neveket. Fájlonként az EGYFÁJLOS `rename_photo`-t hívja, így az
ini-átvitel (és annak ütközés-/hibakezelése) ugyanazon az úton megy, mint
az F2-átnevezésnél — nincs duplikált logika."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QDate, QDateTime, QLocale, Qt

from picasapy.fileops.originals import originals_follow
from picasapy.ini import has_ini_source, load_or_empty, update_document
from picasapy.scanner import PICASA_INI_NAME

def _rename(path: Path, target: Path) -> None:
    """A tényleges átnevezés — külön függvény, hogy a teszt
    helyettesíthesse (#1375).

    A `monkeypatch.setattr(Path, "rename", boom)` alak a `pathlib.Path`
    OSZTÁLYT írja át, tehát a teszt idejére a folyamat MINDEN átnevezése
    dob — az `ini`-mentés atomikus cseréje és a takarítás is."""
    path.rename(target)


def rename_photo(path: Path, new_name: str) -> Path:
    """A `path` fájl átnevezése `new_name`-re, ugyanabban a mappában.

    Args:
        path: Az átnevezendő fájl jelenlegi elérési útja.
        new_name: Az új fájlnév (csak név, elérési út elem nélkül).

    Returns:
        Az új elérési út.

    Raises:
        ValueError: Ha `new_name` üres vagy elérési út elemet tartalmaz.
        FileNotFoundError: Ha `path` nem létezik.
        FileExistsError: Ha a célnév (fájl, ini-szekció vagy a megőrzött
            eredeti helye) már foglalt — akkor is, ha az ini-szekciót csak az
            átnevezés közben foglalta el egy párhuzamos író.
        OSError: Ha a megőrzött eredeti költöztetése bukott el (#1430) —
            ilyenkor sem a kép, sem az eredetije nem mozdult el.
        IniConflictError: Ha az ini-t egy párhuzamos író miatt tartósan nem
            sikerült ütközésmentesen menteni (a fájl ekkor már át van
            nevezve; az üzenet megmondja, hol maradt a metaadat).
    """
    path = Path(path)
    _validate_name(new_name)
    if not path.exists():
        raise FileNotFoundError(f"A fájl nem létezik: {path}")
    target = path.with_name(new_name)
    if target.exists():
        raise FileExistsError(f"A célnév már foglalt: {target}")

    ini_path = path.parent / PICASA_INI_NAME
    has_ini = has_ini_source(ini_path)  # #4819: a régi Picasa.ini is forrás
    if has_ini and load_or_empty(ini_path).section(new_name) is not None:
        raise FileExistsError(f"A célnév ini-szekciója már foglalt: {new_name}")

    # #1430: a megőrzött eredeti (és a sorszámozott pillanatképek) a képpel
    # együtt mennek. Előbb ők költöznek, utána a kép — ha a kísérők
    # költöztetése bukik, a kép el sem indul; ha a kép átnevezése bukik, a
    # `originals_follow` visszateszi őket.
    with originals_follow(path, target):
        _rename(path, target)

    if has_ini:
        try:
            update_document(
                ini_path,
                lambda document: document.with_renamed_section(path.name, new_name),
                backup=True,
            )
        except ValueError as error:
            # A `with_renamed_section` ütközést jelez: a célnév szekcióját a
            # fenti előellenőrzés óta (az újrajátszás friss dokumentumában)
            # elfoglalta valaki. Kifelé a szerződés szerinti FileExistsError
            # marad, de a fájl EKKOR MÁR át van nevezve — ezt az üzenetnek
            # meg kell mondania, különben a felhasználó nem tudja, mit tegyen.
            raise FileExistsError(
                f"A fájl átnevezése megtörtént ({target}), de a .picasa.ini "
                f"bejegyzése nem követte: a(z) {new_name!r} szekciónevet egy "
                f"párhuzamos író (pl. a futó Picasa) időközben elfoglalta itt: "
                f"{ini_path}. A kép beállításai a(z) {path.name!r} szekcióban "
                f"maradtak — onnan kézzel átmásolhatók."
            ) from error

    return target


def _validate_name(name: str) -> None:
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        raise ValueError(f"Érvénytelen fájlnév: {name!r}")


class PartialRenameError(RuntimeError):
    """A köteg valamely fájlnál végrehajtási hiba miatt megállt.

    A ``completed_paths`` a hiba előtt sikeresen feldolgozott fájlok kimeneti
    útvonalait tartalmazza; a ``renamed_paths`` ezek közül a ténylegesen
    átnevezetteket. A hibás fájl útvonala a ``failed_source`` és
    ``failed_target`` mezőben van. Ennél az utolsó fájlnál az állapot
    ellenőrzendő, mert például ini-mentési hiba már a képfájl mozgatása után
    is keletkezhet.
    """

    def __init__(
        self,
        *,
        completed_paths: Sequence[Path],
        renamed_paths: Sequence[Path],
        failed_source: Path,
        failed_target: Path,
        cause: Exception,
    ) -> None:
        self.completed_paths = tuple(completed_paths)
        self.renamed_paths = tuple(renamed_paths)
        self.failed_source = failed_source
        self.failed_target = failed_target
        self.cause = cause

        if self.renamed_paths:
            changed = ", ".join(str(path) for path in self.renamed_paths)
            changed_text = f"Sikeresen átnevezve: {changed}. "
        else:
            changed_text = "A hiba előtt fájl nem lett átnevezve. "
        super().__init__(
            "A kötegelt átnevezés hiba miatt megállt. "
            f"{changed_text}A(z) {failed_source} feldolgozásakor állt le; "
            f"ellenőrizze ennek és a {failed_target} célfájlnak az "
            f"állapotát. Hiba: {cause}"
        )


@dataclass(frozen=True)
class RenameItem:
    """Egy tömegesen átnevezendő fájl bemenete (#366): az útvonal mellett a
    dátum-/felbontás-utótaghoz szükséges, MÁR ISMERT (indexelt) metaadat —
    a hívó (a controller) tölti a `PhotoRecord`-ból, nincs újra lemez-/
    EXIF-olvasás itt."""

    path: Path
    date: str | None = None  # ISO dátum(-idő), pl. a `taken_at`
    width: int | None = None
    height: int | None = None


# A fájlnévben tiltott karakterek (a névmező `filter="filename"` párja, #4879).
_FORBIDDEN_RE = re.compile('[\\\\/:*?"<>|]')
_TWO_DIGIT_YEAR_RE = re.compile(r"(?<!y)yy(?!y)")
_MINUTES_RE = re.compile(r"(?<!m)(\W?)(m{1,2})(?!m)")
_NUMBERED_SUFFIX_RE = re.compile(r"^(.*)-([0-9]+)$")
# kétirányú szövegjelzők és formázó jelek: a fájlnévbe nem kerülnek
_BIDI_MARKS = dict.fromkeys(
    map(ord, "\u200e\u200f\u061c\u202a\u202b\u202c\u202d\u202e"
             "\u2066\u2067\u2068\u2069")
)


def _date_pattern(locale: QLocale) -> str:
    """A területi beállítás rövid dátumhelye, a 2 jegyű év 4 jegyűre bővítve."""
    return _TWO_DIGIT_YEAR_RE.sub("yyyy", locale.dateFormat(QLocale.FormatType.ShortFormat))


def _time_pattern(locale: QLocale) -> str:
    """A területi beállítás rövid időmintája, a perc után másodperccel."""
    pattern = locale.timeFormat(QLocale.FormatType.ShortFormat)
    return _MINUTES_RE.sub(r"\1\2\1ss", pattern, count=1)


def _safe_filename_text(text: str) -> str:
    """Tiltott fájlnév-karakterek `-`-re; a szűk/nem törhető szóköz sima szóköz."""
    text = text.translate(_BIDI_MARKS)
    text = "".join(
        str(unicodedata.decimal(c)) if c.isdecimal() and not c.isascii() else c
        for c in text
    )
    text = text.replace("\u202f", " ").replace("\u00a0", " ")
    return _FORBIDDEN_RE.sub("-", text)


def format_taken_at(iso: str, locale: QLocale | None = None) -> str:
    """A felvétel dátuma + ideje fájlnév-utótagnak (#4879, `rename.fen`).

    A rendszer (`QLocale.system()`) rövid dátumformája 4 jegyű évvel, mögötte
    a rövid időforma másodperccel; a tiltott fájlnév-karakterek (`:`, `/`, …)
    `-`-re cserélve, így en_US-en `8-1-2004 2-30-45 PM`. Idő nélküli értéknél
    csak a dátum; értelmezhetetlen szövegnél az első 10 karakter."""
    locale = locale if locale is not None else QLocale.system()
    text = iso.strip()
    moment = QDateTime.fromString(text, Qt.DateFormat.ISODate) if len(text) > 10 else QDateTime()
    if moment.isValid():
        rendered = locale.toString(moment, f"{_date_pattern(locale)} {_time_pattern(locale)}")
    else:
        day = QDate.fromString(text[:10], Qt.DateFormat.ISODate)
        if not day.isValid():
            return _safe_filename_text(text[:10]).strip()
        rendered = locale.toString(day, _date_pattern(locale))
    return _safe_filename_text(rendered).strip()


def _build_stem(
    base_name: str,
    item: RenameItem,
    *,
    include_date: bool,
    include_size: bool,
    locale: QLocale | None = None,
) -> str:
    """Az alapnév + opcionális dátum-/felbontás-utótag — a `rename.fen`
    "Include in filename: Date / Image resolution" jelölőnégyzetei.
    Sorszám NÉLKÜL (azt a `preview_name` teszi hozzá) — hiányzó metaadatnál
    (nincs dátum/felbontás) a megfelelő utótag néma kihagyással marad el."""
    parts = [base_name]
    if include_date and item.date:
        parts.append(format_taken_at(item.date, locale))
    if include_size and item.width and item.height:
        parts.append(f"{item.width}x{item.height}")
    return " ".join(parts)


def preview_name(
    base_name: str,
    item: RenameItem,
    *,
    include_date: bool = False,
    include_size: bool = False,
    sequence: int = 0,
    ext: str | None = None,
    locale: QLocale | None = None,
) -> str:
    """A végleges fájlnév — élő előnézethez és a tényleges átnevezéshez is
    ez számolja ki. `sequence=0` az első fájl (nincs sorszám-utótag), `1`,
    `2`, … a Picasa-mintájú `név-001`, `név-002`, … folytatás. `ext` hiányában
    (élő előnévet-híváskor) `item.path.suffix`-ot használ."""
    stem = _build_stem(
        base_name, item, include_date=include_date, include_size=include_size,
        locale=locale,
    )
    if sequence > 0:
        stem = f"{stem}-{sequence:03d}"
    extension = ext if ext is not None else item.path.suffix
    return f"{stem}{extension}"


def _available_name(path: Path, stem: str) -> str:
    """Szabad célnevet ad vissza, a kiterjesztést változatlanul megtartva.

    A sorszám nélküli cél az első jelölt. Csak annak foglaltságakor vizsgálja
    a `-001`…`-4095` neveket; meglévő `-szám` végződésből a következő számmal
    folytatja. A korábbi kötegelemek fájljai a lemezen vannak, ezért ezek is
    foglaltnak számítanak.
    """
    path = Path(path)
    extension = path.suffix
    target_name = f"{stem}{extension}"
    target = path.with_name(target_name)
    if target == path or not _path_is_occupied(target):
        return target_name

    match = _NUMBERED_SUFFIX_RE.fullmatch(stem)
    if match:
        stem_root, previous_number = match.groups()
        first_number = int(previous_number) + 1
    else:
        stem_root = stem
        first_number = 1

    last_candidate = target_name
    for number in range(first_number, 4096):
        last_candidate = f"{stem_root}-{number:03d}{extension}"
        candidate = path.with_name(last_candidate)
        if candidate != path and not _path_is_occupied(candidate):
            return last_candidate

    raise FileExistsError(
        "A névkeresés kimerítette a 4096 próbálkozásos keretet; "
        f"utolsó jelölt: {path.with_name(last_candidate)}"
    )


def _path_is_occupied(path: Path) -> bool:
    """A törött symlink is foglalja a cél útvonalát, bár az `exists()` hamis."""
    return path.exists() or path.is_symlink()


def rename_photos_many(
    items: Sequence[RenameItem],
    base_name: str,
    *,
    include_date: bool = False,
    include_size: bool = False,
    locale: QLocale | None = None,
) -> list[Path]:
    """Tömeges átnevezés a `rename.fen` szerint (#366): a kijelölt fájlok
    egyetlen alapnevet kapnak (+ opcionális dátum-/felbontás-utótag).
    Szabad cél esetén nincs sorszám; foglaltságnál `-001`-től keres, meglévő
    `-szám` végződésnél pedig a következővel folytatja. A korábbi kötegelemek
    fájljai a lemezen vannak, ezért foglaltnak számítanak. Ezután fájlonként,
    sorrendben az egyfájlos `rename_photo`-t hívja (ini- és kísérőfájl-átvitel
    ugyanazon az úton).
    Futás közbeni hiba esetén a már sikeres átnevezések a helyükön maradnak,
    nincs köteg-szintű visszagörgetés. A `PartialRenameError` strukturáltan
    megadja a sikeres és az elakadt fájlokat; az elakadt fájl állapota ini- vagy
    fájlrendszer-hibánál ellenőrzendő.

    Raises:
        ValueError: érvénytelen alapnév.
        FileExistsError: ha 4096 céljelölt foglalt.
        PartialRenameError: fájlonkénti végrehajtási hiba; tartalmazza a már
            sikeresen feldolgozott útvonalakat, a hibás forrást és célnevet,
            valamint az eredeti kivételt.
    """
    if not items:
        return []
    _validate_name(base_name)
    results: list[Path] = []
    renamed: list[Path] = []
    for item in items:
        stem = _build_stem(
            base_name, item, include_date=include_date,
            include_size=include_size, locale=locale,
        )
        try:
            name = _available_name(item.path, stem)
        except Exception as error:
            if not renamed:
                raise
            raise PartialRenameError(
                completed_paths=results,
                renamed_paths=renamed,
                failed_source=item.path,
                failed_target=item.path.with_name(f"{stem}{item.path.suffix}"),
                cause=error,
            ) from error
        if name == item.path.name:
            results.append(item.path)  # no-op: a név ténylegesen nem változik
        else:
            target = item.path.with_name(name)
            try:
                result = rename_photo(item.path, name)
            except Exception as error:
                raise PartialRenameError(
                    completed_paths=results,
                    renamed_paths=renamed,
                    failed_source=item.path,
                    failed_target=target,
                    cause=error,
                ) from error
            results.append(result)
            renamed.append(result)
    return results
