"""Recently Updated (#6851) adatréteg-tesztek: 7 napos láthatóság, 250-es korlát, fordított rekordsorrend."""

import time
import pytest

from picasapy.index import (
    open_index,
    sync_tree,
)
from picasapy.index.queries import (
    recently_updated_photos,
    count_recently_updated_photos,
)
from picasapy.index.albums import album_photos


@pytest.fixture
def conn(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    with open_index(tmp_path / "index.db") as connection:
        yield connection, root


def test_recently_updated_membership_7_days(conn):
    connection, root = conn
    now = time.time()
    now_ns = int(now * 1_000_000_000)
    day_ns = 86400 * 1_000_000_000

    # Három kép:
    # 1. 2 napja módosult -> tag (> now - 7 nap)
    # 2. 6 napja módosult -> tag (> now - 7 nap)
    # 3. 8 napja módosult -> NEM tag (<= now - 7 nap)
    f1 = root / "recent1.jpg"
    f2 = root / "recent2.jpg"
    f3 = root / "old.jpg"
    f1.write_bytes(b"1")
    f2.write_bytes(b"2")
    f3.write_bytes(b"3")

    sync_tree(connection, root)

    # Beállítjuk a fájlok mtime_ns-ét az indexben
    connection.execute("UPDATE photos SET mtime_ns = ? WHERE name = 'recent1.jpg'", (now_ns - 2 * day_ns,))
    connection.execute("UPDATE photos SET mtime_ns = ? WHERE name = 'recent2.jpg'", (now_ns - 6 * day_ns,))
    connection.execute("UPDATE photos SET mtime_ns = ? WHERE name = 'old.jpg'", (now_ns - 8 * day_ns,))
    connection.commit()

    photos = recently_updated_photos(connection, cutoff_ns=now_ns - 7 * day_ns)
    names = [p.name for p in photos]
    assert "old.jpg" not in names
    assert "recent1.jpg" in names
    assert "recent2.jpg" in names

    assert count_recently_updated_photos(connection, cutoff_ns=now_ns - 7 * day_ns) == 2


def test_recently_updated_order_reverse_record_order(conn):
    connection, root = conn
    now = time.time()
    now_ns = int(now * 1_000_000_000)

    # Sorrendben veszünk fel három képet (növekvő id):
    f1 = root / "img_a.jpg"
    f2 = root / "img_b.jpg"
    f3 = root / "img_c.jpg"
    f1.write_bytes(b"a")
    sync_tree(connection, root)

    f2.write_bytes(b"b")
    sync_tree(connection, root)

    f3.write_bytes(b"c")
    sync_tree(connection, root)

    connection.execute("UPDATE photos SET mtime_ns = ?", (now_ns,))
    connection.commit()

    photos = recently_updated_photos(connection, cutoff_ns=now_ns - 7 * 86400 * 1_000_000_000)
    # Fordított rekordsorrend: az utoljára felvett áll elöl
    names = [p.name for p in photos]
    assert names == ["img_c.jpg", "img_b.jpg", "img_a.jpg"]


def test_recently_updated_limit_250(conn):
    connection, root = conn
    now = time.time()
    now_ns = int(now * 1_000_000_000)

    # 5 képet készítünk, de a limit legyen 3
    for i in range(5):
        (root / f"pic_{i:02d}.jpg").write_bytes(b"x")
    sync_tree(connection, root)

    connection.execute("UPDATE photos SET mtime_ns = ?", (now_ns,))
    connection.commit()

    # Limit = 3: a legfrissebb 3 (pic_04, pic_03, pic_02) kell
    photos = recently_updated_photos(connection, cutoff_ns=now_ns - 7 * 86400 * 1_000_000_000, limit=3)
    assert len(photos) == 3
    assert [p.name for p in photos] == ["pic_04.jpg", "pic_03.jpg", "pic_02.jpg"]
    assert count_recently_updated_photos(connection, cutoff_ns=now_ns - 7 * 86400 * 1_000_000_000, limit=3) == 3


def test_album_photos_updated_token(conn):
    connection, root = conn
    now_ns = int(time.time() * 1_000_000_000)
    (root / "sample.jpg").write_bytes(b"sample")
    sync_tree(connection, root)
    connection.execute("UPDATE photos SET mtime_ns = ?", (now_ns,))
    connection.commit()

    res = album_photos(connection, "]updated")
    assert len(res) == 1
    assert res[0].name == "sample.jpg"
