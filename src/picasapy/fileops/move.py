"""Fotó áthelyezése másik mappába — a .picasa.ini szekció átvándorol (#15).

A forrás szekció (star/caption/rotate/filters/… és minden ismeretlen sor)
bitre pontosan átkerül a cél mappa `.picasa.ini`-jébe.

Mindkét ini-írás az ütközésbiztos `update_document`-en megy (#295): a
NAS-mappát a párhuzamosan futó eredeti Picasa is írhatja, a sima
`load → save` pedig némán felülírná, amit közben írt (lost update).

A műveletek sorrendje adatvesztés-kerülő (#295): fájlmozgatás → cél-ini
írása → forrás-ini takarítása. Ha a cél-ini írása bukik, a metaadat még a
forrásmappában van (visszakereshető); ha a forrás takarítása bukik, a
bejegyzés legfeljebb duplán marad meg — mindkettő helyreállítható, az
elvesztése nem lenne az.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from picasapy.ini import (
    IniConflictError,
    IniSaveError,
    load_or_empty,
    update_document,
)
from picasapy.scanner import PICASA_INI_NAME

# Az ini-írás kezelt hibái: a fájlrendszeré (`OSError`), a kódolásé
# (`IniSaveError`) és a tartós párhuzamos-írás-ütközésé (`IniConflictError`).
_INI_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError)


def move_photo(path: Path, dest_folder: Path) -> Path:
    """A `path` fájl áthelyezése a `dest_folder` mappába.

    Args:
        path: Az áthelyezendő fájl jelenlegi elérési útja.
        dest_folder: A célmappa (léteznie kell, könyvtárnak kell lennie).

    Returns:
        Az új elérési út.

    Raises:
        FileNotFoundError: Ha `path` vagy `dest_folder` nem létezik.
        NotADirectoryError: Ha `dest_folder` nem könyvtár.
        FileExistsError: Ha a célmappában már van azonos nevű fájl vagy
            ini-szekció — nem írjuk felül csendben.
        OSError | IniSaveError | IniConflictError: Ha a fájl már átkerült, de
            valamelyik ini-írás nem sikerült. A hiba TÍPUSA az eredetivel
            azonos marad (a hívók így tudják osztályozni), az üzenete pedig
            megmondja, hol a fájl és hol maradt a metaadat.
    """
    path = Path(path)
    dest_folder = Path(dest_folder)
    if not path.exists():
        raise FileNotFoundError(f"A fájl nem létezik: {path}")
    if not dest_folder.exists():
        raise FileNotFoundError(f"A célmappa nem létezik: {dest_folder}")
    if not dest_folder.is_dir():
        raise NotADirectoryError(f"A cél nem könyvtár: {dest_folder}")
    target = dest_folder / path.name
    if target.exists():
        raise FileExistsError(f"A célfájl már létezik: {target}")

    name = path.name
    source_ini = path.parent / PICASA_INI_NAME
    dest_ini = dest_folder / PICASA_INI_NAME
    has_section = (
        source_ini.exists() and load_or_empty(source_ini).section(name) is not None
    )
    if has_section and load_or_empty(dest_ini).section(name) is not None:
        raise FileExistsError(
            f"A célmappa ini-jében már van ilyen nevű szekció: {name}"
        )

    shutil.move(str(path), str(target))

    if not has_section:
        return target

    def _carry(document):
        # A forrás szekciót MINDEN próbálkozásnál frissen olvassuk ki: ha az
        # ütközés miatt újrajátszás történik, a párhuzamos író (futó Picasa)
        # időközben bekerült módosítása is átkerüljön a célba.
        section = load_or_empty(source_ini).section(name)
        return document if section is None else document.with_section(section)

    try:
        update_document(dest_ini, _carry, backup=True)
    except _INI_WRITE_ERRORS as error:
        raise _with_context(
            error,
            f"A fájl átkerült ide: {target}, de a hozzá tartozó .picasa.ini "
            f"bejegyzést nem sikerült a célmappába írni ({dest_ini}): {error}. "
            f"A kép beállításai (csillag, felirat, szerkesztések) egyelőre itt "
            f"maradtak: {source_ini} — az áthelyezés megismételhető.",
        ) from error

    try:
        update_document(
            source_ini,
            lambda document: document.without_section(name),
            backup=True,
        )
    except _INI_WRITE_ERRORS as error:
        raise _with_context(
            error,
            f"A fájl átkerült ide: {target}, és a .picasa.ini bejegyzése is, "
            f"de a régi bejegyzést nem sikerült törölni innen: {source_ini} "
            f"({error}). A kép beállításai most mindkét mappa ini-fájljában "
            f"szerepelnek; a forrásmappából a(z) [{name}] szakasz kézzel "
            f"törölhető.",
        ) from error

    return target


def _with_context(error: Exception, message: str) -> Exception:
    """Ugyanolyan TÍPUSÚ hiba, cselekvésre fordítható magyar üzenettel.

    A típus megőrzése azért kell, mert a hívók (pl. a `FileOpsController`)
    kivételosztály szerint szűrnek: egy saját, új osztály némán kicsúszna a
    szűrőjükön, és a részleges hiba a felhasználó felé láthatatlan maradna."""
    return type(error)(message)
