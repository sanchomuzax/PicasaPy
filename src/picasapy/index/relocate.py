"""Az index-SQLite + a thumbnail-cache áthelyezése új mappába (#368,
`move_database.fen`/`moving_database.fen`).

ELLENŐRZÖTT sorrend — ez a modul legfontosabb invariánsa: HIBA (vagy
megszakítás) esetén a RÉGI állapot MINDIG érintetlen marad.

    1. cél-hely validálása (írható, van elég szabad hely, nem a forrás
       alkönyvtára)
    2. másolás a cél alá — az SQLite-index a beépített `sqlite3` backup
       API-val (nem igényli a hívó éppen nyitva tartott kapcsolatának
       lezárását: a forrás egy KÜLÖN, csak-olvasásra nyitott kapcsolatból
       másolódik), a cache egyszerű fájlmásolással
    3. integritás-ellenőrzés (`PRAGMA integrity_check`) a MÁSOLT példányon
    4. csak SIKERES ellenőrzés UTÁN: az `on_verified` hívása (itt írja át a
       hívó az útvonal-beállítást — pl. a legközelebbi induláskor
       használandó adatgyökeret), majd a régi törlése

Ha bármelyik lépés hibázik vagy a hívó megszakítja (`should_cancel`), a
célon keletkezett FÉLKÉSZ másolat törlődik, a forrás pedig egyáltalán nem
nyúlunk hozzá — sem törlés, sem módosítás.

Qt-mentes, önállóan tesztelhető mag; a Qt-hidat az
`app/relocate_controller.py` adja (haladás-jelzés, megszakítás-gomb).
"""

from __future__ import annotations

import shutil
import sqlite3
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

#: A `shutil.disk_usage` MODULSZINTŰ fogantyúja (#1375) — a teszt EZT
#: cserélje, ne a `monkeypatch.setattr(relocate.shutil, "disk_usage", …)`
#: alakot: az a GLOBÁLIS `shutil`-t írja át.
_disk_usage = shutil.disk_usage

def _probe_iras(probe: Path) -> None:
    """A cél írhatóságát próbáló üres kiírás — külön függvény, hogy a teszt
    helyettesíthesse (#1375).

    A teszt korábban a `pathlib.Path.write_bytes`-t írta át GLOBÁLISAN: az
    OSZTÁLYON végzett csere a folyamat minden `write_bytes` hívására hat,
    tehát a „nem írható a cél" szimuláció az ini-mentést és a pytest saját
    kiírásait is elvitte volna."""
    probe.write_bytes(b"")


# a backup API ennyi oldalanként ad haladás-visszahívást — elég sűrű a
# folyamatjelzőhöz, de nem terheli túl a hívást nagy indexnél sem
_BACKUP_PAGES_PER_STEP = 64

# a szabad hely ellenőrzésénél ennyi RÁHAGYÁS kell a másolat mérete fölött,
# hogy a másolás közben (pl. WAL-checkpoint) se fogyhasson el a hely
_FREE_SPACE_MARGIN_RATIO = 0.05
_FREE_SPACE_MARGIN_MIN_BYTES = 1024 * 1024


class RelocationError(Exception):
    """Az áthelyezés nem végezhető el — a forrás érintetlen maradt."""


class RelocationCancelled(Exception):
    """A hívó (`should_cancel`) megszakította — a forrás érintetlen
    maradt, a célon keletkezett félkész másolat eltávolítva."""


@dataclass(frozen=True)
class RelocationProgress:
    """Egy haladás-jelzés. `phase`: "database"/"cache"/"done" — ember-
    olvasható fázisnév a UI-nak nem itt, hanem a controller oldalán
    fordítandó. `done`/`total` bájtban; `total == 0` esetén határozatlan
    (nem volt mit másolni ebben a fázisban)."""

    phase: str
    done: int
    total: int


@dataclass(frozen=True)
class RelocationResult:
    """A sikeres áthelyezés eredménye. `old_cleanup_error`: a régi adatok
    törlése közben történt (nem végzetes) hiba szövege, vagy `None` — az
    áthelyezés maga ekkor is sikeresnek számít, hiszen az új hely már
    ellenőrzötten él és a beállítás átíródott."""

    new_root: Path
    old_cleanup_error: str | None


ProgressCallback = Callable[[RelocationProgress], None]
CancelPredicate = Callable[[], bool]


def _check_cancelled(should_cancel: CancelPredicate | None) -> None:
    if should_cancel is not None and should_cancel():
        raise RelocationCancelled("Az áthelyezést a felhasználó megszakította.")


def validate_destination(new_root: Path, sources: Iterable[Path]) -> None:
    """`RelocationError`, ha `new_root` nem alkalmas célnak: a forrás(ok)
    valamelyikével egyezik/alattuk van, nem hozható létre, vagy nem
    írható. Mellékhatásként létrehozza `new_root`-ot, ha még nem létezik."""
    resolved_new = new_root.resolve()
    for source in sources:
        resolved_source = Path(source).resolve()
        if resolved_new == resolved_source or resolved_new.is_relative_to(
            resolved_source
        ):
            raise RelocationError(
                f"A kiválasztott cél ({new_root}) a jelenlegi adatok "
                f"mappáján ({source}) belül van — ez nem megengedett."
            )
    try:
        new_root.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise RelocationError(
            f"A cél mappa nem hozható létre: {error}"
        ) from error
    probe = new_root / f".picasapy-write-test-{id(new_root):x}"
    try:
        _probe_iras(probe)
    except OSError as error:
        raise RelocationError(f"A cél mappa nem írható: {error}") from error
    finally:
        probe.unlink(missing_ok=True)


def _cache_total_bytes(cache_dir: Path) -> int:
    if not cache_dir.exists():
        return 0
    return sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())


def _database_total_bytes(index_db: Path) -> int:
    if not index_db.exists():
        return 0
    total = index_db.stat().st_size
    for suffix in ("-wal", "-shm"):
        sidecar = index_db.with_name(index_db.name + suffix)
        if sidecar.exists():
            total += sidecar.stat().st_size
    return total


def _check_free_space(new_root: Path, required_bytes: int) -> None:
    usage = _disk_usage(new_root)
    margin = max(
        int(required_bytes * _FREE_SPACE_MARGIN_RATIO), _FREE_SPACE_MARGIN_MIN_BYTES
    )
    needed = required_bytes + margin
    if usage.free < needed:
        raise RelocationError(
            "Nincs elég szabad hely a cél mappában: "
            f"{usage.free} bájt szabad, {needed} bájt szükséges."
        )


def _copy_database(
    old_index_db: Path,
    new_index_db: Path,
    progress: ProgressCallback | None,
    should_cancel: CancelPredicate | None,
) -> None:
    """A forrás-adatbázis másolása a sqlite3 backup API-val — a forrás
    kapcsolatot lezárás nélkül, konzisztens pillanatképként olvassa (a
    WAL-t is figyelembe véve), a cél mindig egy TELJES, önálló fájl lesz
    (nincs -wal/-shm sidecar-másolás)."""
    if not old_index_db.exists():
        return  # még nincs index — nincs mit másolni, a cél üresen indul
    new_index_db.parent.mkdir(parents=True, exist_ok=True)
    source_conn = sqlite3.connect(str(old_index_db))
    try:
        target_conn = sqlite3.connect(str(new_index_db))
        try:

            def _on_backup_progress(status: int, remaining: int, total: int) -> None:
                del status  # nem használt — a `remaining`/`total` elég
                if progress is not None and total > 0:
                    progress(RelocationProgress("database", total - remaining, total))
                _check_cancelled(should_cancel)

            source_conn.backup(
                target_conn,
                pages=_BACKUP_PAGES_PER_STEP,
                progress=_on_backup_progress,
            )
        finally:
            target_conn.close()
    except sqlite3.Error as error:
        raise RelocationError(
            f"Az adatbázis másolása nem sikerült: {error}"
        ) from error
    finally:
        source_conn.close()


def _copy_cache(
    old_cache_dir: Path,
    new_cache_dir: Path,
    total_bytes: int,
    progress: ProgressCallback | None,
    should_cancel: CancelPredicate | None,
) -> None:
    if not old_cache_dir.exists():
        return
    done = 0
    for file in old_cache_dir.rglob("*"):
        if not file.is_file():
            continue
        _check_cancelled(should_cancel)
        relative = file.relative_to(old_cache_dir)
        target = new_cache_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(file, target)
        except OSError as error:
            raise RelocationError(
                f"A gyorsítótár másolása nem sikerült ({file}): {error}"
            ) from error
        done += file.stat().st_size
        if progress is not None:
            progress(RelocationProgress("cache", done, total_bytes))


def _integrity_check(new_index_db: Path) -> None:
    if not new_index_db.exists():
        return  # nem volt forrás-adatbázis — nincs mit ellenőrizni
    conn = sqlite3.connect(str(new_index_db))
    try:
        rows = conn.execute("PRAGMA integrity_check").fetchall()
    finally:
        conn.close()
    values = [str(row[0]) for row in rows]
    if values != ["ok"]:
        raise RelocationError(
            "Az áthelyezett adatbázis integritás-ellenőrzése nem sikerült: "
            + "; ".join(values)
        )


def _cleanup_partial(new_index_db: Path, new_cache_dir: Path) -> None:
    """A célon keletkezett félkész másolat eltakarítása — mindig
    best-effort (a hívás egy már folyamatban lévő hibakezelésből jön, itt
    nem dobhatunk újabb kivételt)."""
    for name in (
        new_index_db.name,
        new_index_db.name + "-wal",
        new_index_db.name + "-shm",
    ):
        try:
            new_index_db.with_name(name).unlink(missing_ok=True)
        except OSError:
            pass
    if new_cache_dir.exists():
        shutil.rmtree(new_cache_dir, ignore_errors=True)


def _delete_old(old_index_db: Path, old_cache_dir: Path) -> str | None:
    """A régi adatok törlése — best-effort: a hiba szövegét adja vissza,
    de NEM dob kivételt (az áthelyezés eddigi pontig már sikeres és
    ellenőrzött, egy törlési hiba emiatt nem teheti "sikertelenné")."""
    errors: list[str] = []
    for name in (
        old_index_db.name,
        old_index_db.name + "-wal",
        old_index_db.name + "-shm",
    ):
        try:
            old_index_db.with_name(name).unlink(missing_ok=True)
        except OSError as error:
            errors.append(str(error))
    if old_cache_dir.exists():
        try:
            shutil.rmtree(old_cache_dir)
        except OSError as error:
            errors.append(str(error))
    return "; ".join(errors) if errors else None


def relocate_data_root(
    old_index_db: Path,
    old_cache_dir: Path,
    new_root: Path,
    *,
    index_db_name: str = "index.db",
    cache_subdir: str = "thumbs",
    progress: ProgressCallback | None = None,
    should_cancel: CancelPredicate | None = None,
    on_verified: Callable[[Path], None] | None = None,
) -> RelocationResult:
    """Az index-SQLite (`old_index_db`) + a thumbnail-cache
    (`old_cache_dir`) áthelyezése egyetlen ÚJ, egyesített `new_root`
    mappa alá (`new_root/index_db_name` + `new_root/cache_subdir`) — ez a
    Picasa "Move Database" viselkedésének felel meg (a db + a cache attól
    kezdve egy helyen élnek).

    `on_verified`: az integritás-ellenőrzés UTÁN, a régi törlése ELŐTT
    hívódik `new_root`-tal — itt írja át a hívó a "legközelebb induláskor
    innen olvasandó" beállítást. Ha ez a hívás kivételt dob, a célon
    keletkezett másolat törlődik és a kivétel továbbterjed — a régi
    adatokhoz és a beállításhoz emiatt nem nyúlunk.

    `RelocationError`/`RelocationCancelled` esetén a forrás MINDIG
    érintetlen marad — ez a modul legfontosabb invariánsa."""
    old_index_db = Path(old_index_db)
    old_cache_dir = Path(old_cache_dir)
    new_root = Path(new_root)

    validate_destination(new_root, (old_index_db.parent, old_cache_dir))
    _check_cancelled(should_cancel)

    required_bytes = _database_total_bytes(old_index_db) + _cache_total_bytes(
        old_cache_dir
    )
    _check_free_space(new_root, required_bytes)

    new_index_db = new_root / index_db_name
    new_cache_dir = new_root / cache_subdir

    try:
        _check_cancelled(should_cancel)
        _copy_database(old_index_db, new_index_db, progress, should_cancel)
        _check_cancelled(should_cancel)
        cache_total = _cache_total_bytes(old_cache_dir)
        _copy_cache(
            old_cache_dir, new_cache_dir, cache_total, progress, should_cancel
        )
        _check_cancelled(should_cancel)
        _integrity_check(new_index_db)
    except (RelocationError, RelocationCancelled):
        _cleanup_partial(new_index_db, new_cache_dir)
        raise
    except OSError as error:
        _cleanup_partial(new_index_db, new_cache_dir)
        raise RelocationError(f"Másolási hiba: {error}") from error

    if on_verified is not None:
        try:
            on_verified(new_root)
        except Exception:
            _cleanup_partial(new_index_db, new_cache_dir)
            raise

    old_cleanup_error = _delete_old(old_index_db, old_cache_dir)
    if progress is not None:
        progress(RelocationProgress("done", 1, 1))
    return RelocationResult(new_root=new_root, old_cleanup_error=old_cleanup_error)
