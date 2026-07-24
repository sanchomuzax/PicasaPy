"""Fájl átnevezése a lemezen — a .picasa.ini szekció követi (#15).

Round-trip elv: a szekció tartalma (star/caption/rotate/filters/… és minden
ismeretlen sor) bitre pontosan megmarad, csak a `[fájlnév]` fejléc változik.

Az ini-írás az ütközésbiztos `update_document`-en megy (#295): a NAS-mappát
a párhuzamosan futó eredeti Picasa is írhatja, a sima `load → save` pedig
némán felülírná, amit közben írt (lost update).
"""

from __future__ import annotations

from pathlib import Path

from picasapy.ini import load_or_empty, update_document
from picasapy.scanner import PICASA_INI_NAME


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
        FileExistsError: Ha a célnév (fájl vagy ini-szekció) már foglalt —
            akkor is, ha az ini-szekciót csak az átnevezés közben foglalta
            el egy párhuzamos író.
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
    has_ini = ini_path.exists()
    if has_ini and load_or_empty(ini_path).section(new_name) is not None:
        raise FileExistsError(f"A célnév ini-szekciója már foglalt: {new_name}")

    path.rename(target)

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
