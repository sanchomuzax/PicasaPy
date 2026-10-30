"""A thumbnail-gyorsítótár lemezútvonalai és takarítása."""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path

from picasapy.ioutil import write_atomic
from picasapy.thumbs.prune import prune_cache_dir, prune_in_background
from picasapy.thumbs.szintek import szint_cellahoz, szintek


class _CacheStorageMixin:
    def __init__(
        self,
        root: str | Path,
        size: int = 256,
        max_bytes: int | None = None,
    ):
        """`max_bytes`: a lemez-cache méretkorlátja (#144) — ha meg van
        adva, induláskor háttérszálon lefut az LRU-takarító, hogy a
        `~/.cache` alatti tár ne nőjön korlátlanul."""
        self._root = Path(root)
        self._size = size
        #: #598: a tár SZINTJEI (72 · 144 · a rács maximuma). A felső szint
        #: útvonala szándékosan VÁLTOZATLAN (`root/<2 hex>/…`): így a már
        #: meglévő — százezres könyvtárnál órákba kerülő — gyorsítótár
        #: érvényes marad, és csak a két új kis szint épül fel menet közben.
        self._szintek = szintek(size)
        self._max_bytes = max_bytes
        # A szál referenciáját eltároljuk, hogy a hívó (pl. teszt) be
        # tudja várni — enélkül a takarítás versenyezne a mappa-törléssel.
        self._prune_thread: threading.Thread | None = None
        if max_bytes is not None:
            self._prune_thread = prune_in_background(self._root, max_bytes)

    def prune(self) -> int:
        """Szinkron LRU-takarítás a beállított korlátig; a törölt bájtok
        száma. Korlát nélkül nem csinál semmit (0)."""
        if self._max_bytes is None:
            return 0
        return prune_cache_dir(self._root, self._max_bytes)

    @property
    def levels(self) -> tuple[int, ...]:
        """A tár szintjei növő sorrendben (#598) — a legnagyobb a saját mérete."""
        return self._szintek

    def level_for(self, cella_px: int) -> int:
        """A `cella_px` oldalú megjelenítéshez tartozó szint (#598)."""
        return szint_cellahoz(cella_px, self._size)

    def clear(self) -> int:
        """A LEMEZES bélyegkép-tár ürítése; a felszabadult bájtok száma (#598).

        Az eredeti Beállítások `disposepreviews` kapcsolójának kért
        kilépéskori takarítója (#5897). Minden szintet töröl, a
        mappaszerkezetet meghagyja - a bélyegképek kérésre újraépülnek,
        tehát ez nem adatvesztés, csak lemezhely-visszanyerés.

        Best-effort, mint a takarító: az időközben eltűnt vagy zárolt fájlt
        kihagyja. Egy sikertelen törlés nem hibaüzenet, hanem kevesebb
        visszanyert hely."""
        import contextlib

        freed = 0
        if not self._root.is_dir():
            return 0
        try:
            fajlok = list(self._root.rglob("*.jpg"))
        except OSError:
            return 0
        for path in fajlok:
            try:
                meret = path.stat().st_size
            except OSError:
                continue
            with contextlib.suppress(OSError):
                path.unlink()
                freed += meret
        return freed

    def thumbnail_path(
        self,
        photo_path: Path,
        mtime_ns: int,
        size_bytes: int,
        level: int | None = None,
    ) -> Path:
        """A bélyegkép helye. `level` nélkül a legnagyobb (régi) szint.

        A kulcsban a szint SZÁMA áll — ugyanaz a séma, mint korábban a
        `self._size`-zal —, a kis szintek pedig külön alkönyvtárba mennek,
        hogy a takarító szintenként is dolgozni tudjon."""
        px = self._size if level is None else level
        key = f"{photo_path}\x00{mtime_ns}\x00{size_bytes}\x00{px}"
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        gyoker = self._root if px == self._size else self._root / f"sz{px}"
        return gyoker / digest[:2] / f"{digest}.jpg"


    @staticmethod
    def _write_atomic(target: Path, payload: bytes) -> None:
        """Közös helper (#129), egyedi temp-névvel: a provider több szálról
        is kérheti ugyanazt a thumbnailt. A cache tartalma újragenerálható,
        ezért fsync nem kell (durable=False); a replace sharing violationje
        (#66) lenyelhető, ha a thumbnail közben a párhuzamos írótól
        létrejött (ignore_replace_race)."""
        write_atomic(
            target,
            payload,
            durable=False,
            make_parents=True,
            ignore_replace_race=True,
        )
