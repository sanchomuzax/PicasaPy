#!/usr/bin/env python3
"""SQLite index + inotify skálázás benchmark (research-plan #3 lezárása).

1) SQLite: a valódi Picasa thumbindex útvonalaival (140k kép) épít indexet,
   méri a bulk-insertet, a tipikus lekérdezéseket és az FTS5 keresést.
2) inotify/watchdog: sok-mappás rekurzív figyelés felállási ideje és
   esemény-latenciája.

Használat: bench_sqlite_inotify.py <thumbindex.db> <scratch_dir>
"""
import shutil
import sqlite3
import struct
import sys
import tempfile
import time
from pathlib import Path

THUMBINDEX = Path(sys.argv[1])
SCRATCH = Path(sys.argv[2])


def load_paths():
    """Valódi fájl-útvonalak a Picasa thumbindexből."""
    data = THUMBINDEX.read_bytes()
    entries = struct.unpack_from("<I", data, 4)[0]
    pos, names, parents = 8, [], []
    while pos < len(data) and len(names) < entries:
        end = data.index(b"\x00", pos)
        names.append(data[pos:end].decode("utf-8", errors="replace"))
        pos = end + 1 + 26
        parents.append(struct.unpack_from("<I", data, pos)[0])
        pos += 4
    files = []
    for i, (n, p) in enumerate(zip(names, parents)):
        if n and p != 0xFFFFFFFF and p < len(names):
            files.append((names[p] + n, n))
    return files


def bench_sqlite(files):
    db_path = SCRATCH / "bench.sqlite"
    db_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        CREATE TABLE images(
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL,
            folder TEXT NOT NULL,
            name TEXT NOT NULL,
            star INTEGER DEFAULT 0,
            caption TEXT,
            keywords TEXT,
            mtime REAL,
            width INT, height INT
        );
        CREATE INDEX idx_folder ON images(folder);
        CREATE INDEX idx_star ON images(star) WHERE star=1;
        CREATE VIRTUAL TABLE search USING fts5(
            name, caption, keywords, content=images, content_rowid=id);
    """)

    rows = []
    for i, (full, name) in enumerate(files):
        folder = full[: -len(name)]
        star = 1 if i % 47 == 0 else 0
        caption = f"nyaralás {i} tenger napfény" if i % 11 == 0 else None
        keywords = "család,nyár,strand" if i % 13 == 0 else None
        rows.append((full, folder, name, star, caption, keywords,
                     1700000000.0 + i, 4624, 2601))

    t0 = time.perf_counter()
    con.executemany(
        "INSERT INTO images(path,folder,name,star,caption,keywords,mtime,"
        "width,height) VALUES(?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    t_insert = time.perf_counter() - t0

    t0 = time.perf_counter()
    con.execute("INSERT INTO search(rowid,name,caption,keywords) "
                "SELECT id,name,caption,keywords FROM images")
    con.commit()
    t_fts = time.perf_counter() - t0

    def q(sql, *args):
        t0 = time.perf_counter()
        n = len(con.execute(sql, args).fetchall())
        return (time.perf_counter() - t0) * 1000, n

    folder = rows[len(rows) // 2][1]
    t_folder, n1 = q("SELECT id,name FROM images WHERE folder=? "
                     "ORDER BY name", folder)
    t_star, n2 = q("SELECT id,path FROM images WHERE star=1")
    t_like, n3 = q("SELECT id FROM images WHERE caption LIKE '%tenger%'")
    t_match, n4 = q("SELECT rowid FROM search WHERE search MATCH 'tenger'")
    t_page, n5 = q("SELECT id,name FROM images WHERE folder=? "
                   "ORDER BY mtime LIMIT 200 OFFSET 1000", folder)

    size_mb = db_path.stat().st_size / 1e6
    print(f"  insert {len(rows)} sor:      {t_insert:6.2f} s "
          f"({len(rows)/t_insert:,.0f} sor/s)")
    print(f"  FTS5 index építés:      {t_fts:6.2f} s")
    print(f"  mappa-lista ({n1} kép):  {t_folder:6.1f} ms")
    print(f"  csillagozottak ({n2}):  {t_star:6.1f} ms")
    print(f"  LIKE keresés ({n3}):  {t_like:6.1f} ms")
    print(f"  FTS MATCH ({n4}):     {t_match:6.1f} ms")
    print(f"  lapozás (200/oldal):    {t_page:6.1f} ms")
    print(f"  db méret:               {size_mb:6.1f} MB")
    con.close()


def bench_inotify(n_dirs=2400):
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    root = Path(tempfile.mkdtemp(dir=SCRATCH, prefix="watch_"))
    for i in range(n_dirs):
        (root / f"y{i//200:02d}/d{i:04d}").mkdir(parents=True)

    events = []

    class H(FileSystemEventHandler):
        def on_created(self, e):
            events.append((e.src_path, time.perf_counter()))

    obs = Observer()
    t0 = time.perf_counter()
    obs.schedule(H(), str(root), recursive=True)
    obs.start()
    t_setup = time.perf_counter() - t0

    time.sleep(0.5)
    lat = []
    for i in range(20):
        di = (i * 113) % n_dirs
        target = root / f"y{di//200:02d}" / f"d{di:04d}" / "uj.jpg"
        t0 = time.perf_counter()
        target.write_bytes(b"x")
        while not any(str(target) == p for p, _ in events):
            time.sleep(0.001)
            if time.perf_counter() - t0 > 2:
                break
        lat.append((time.perf_counter() - t0) * 1000)
    obs.stop()
    obs.join()
    shutil.rmtree(root)

    lat.sort()
    print(f"  {n_dirs} mappa rekurzív watch felállás: {t_setup*1000:.0f} ms")
    print(f"  esemény-latencia: medián {lat[len(lat)//2]:.1f} ms, "
          f"max {lat[-1]:.1f} ms ({len(lat)} próba)")


def main():
    files = load_paths()
    print(f"=== SQLite ({len(files)} valódi útvonal) ===")
    bench_sqlite(files)
    print("\n=== inotify/watchdog ===")
    bench_inotify()


if __name__ == "__main__":
    main()
