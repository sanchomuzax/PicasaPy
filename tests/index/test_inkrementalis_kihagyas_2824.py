"""Az inkrementális kihagyás HATÁRA — a #2824 gyökéroka, reprodukálva.

## Mit mér ez a lap

A `sync_tree` alapból inkrementális (#143): kihagyja azt a mappát, amelynek
a **mappa-mtime-ja** egyezik a tárolt állapottal **és** 2 másodpercnél
(`_SKIP_SAFETY_NS`) régebbi.

Egy fájl **helyben átírása** viszont a mappa mtime-ját **nem mozdítja** (sem
POSIX-on, sem Windowson — a könyvtár bejegyzései nem változnak). ⇒ ha a
mappa túllépte a védőablakot, a változás **nem kerül be az indexbe**.

## Miért ez a #2824 gyökéroka

A `test_arc_ujraszkenneles_2519.py` a fotót helyben írta át, majd
`sync_tree(conn, root)`-ot hívott, és azt várta, hogy az index átvegye az új
(mtime, méret) párt. Amíg a próba a 2 másodperces ablakon belül futott
(linuxon jellemzően igen), a mappa nem lett kihagyva, és minden működött.
A lassabb windows-futáson viszont kimaradt — az index a RÉGI állapotot
tartotta, a detektor pedig joggal hagyta ki a fotót: `1 == 2`.

A `68792531` main-futásán a beszédes állítás ezt ki is írta:

```
index=[('a.jpg', 1789433180369050100, 633)]
fájl=(mtime_ns=1789433183748655700, size=709)
```

a két mtime **3,4 másodpercre** volt egymástól.

## ⚠️ Ez NEM termékhiba

A kihagyás **szándékos** (#143), és a védőablak épp azért van, hogy a friss
mappa sose maradjon ki. Aki a teljes állapotot akarja, `incremental=False`-t
kér. Ez a lap a HATÁRT rögzíti, hogy legközelebb ne „ingadozó tesztként"
találkozzunk vele.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg

#: A `sync.py` védőablaka — ennél régebbi mappa hagyható ki.
VEDOABLAK_NS = 2_000_000_000


def _kapcsolat(tmp_path: Path):
    """A projekt saját megnyitója — séma és sorgyár egy helyen."""
    return open_index(tmp_path / "index.db")


def _foto_allapot(conn) -> list[tuple[str, int, int]]:
    return [
        (sor["name"], sor["mtime_ns"], sor["size"])
        for sor in conn.execute("SELECT name, mtime_ns, size FROM photos")
    ]


def _regi_mappa_mtime(mappa: Path, mikor: int) -> None:
    """A mappa mtime-ja a védőablakon KÍVÜLRE — ez teszi kihagyhatóvá.

    ⚠️ A `mikor` KÖTELEZŐ és fix: a kihagyás feltétele, hogy a tárolt és a
    mostani mtime BITRE egyezzen. Az első változatom minden híváskor
    újraszámolta (`time.time_ns()`), tehát a két beállítás eltért — így
    sosem volt kihagyás, és a próba a saját hipotézisét cáfolta volna meg
    tévesen."""
    os.utime(mappa, ns=(mikor, mikor))


def _regen() -> int:
    """Egy időpont a védőablakon kívül — hívásonként EGYSZER kiszámolva."""
    return time.time_ns() - 3 * VEDOABLAK_NS


def test_a_HELYBEN_atirt_fajl_kimarad_az_inkrementalis_szinkronbol(tmp_path):
    """⛔ A #2824 gyökéroka, reprodukálva — linuxon is."""
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    kep = gyoker / "a.jpg"
    make_jpeg(kep, size=(40, 30))
    # ⚠️ A mappa mtime-ját az ELSŐ szinkron ELŐTT öregítjük: a kihagyás
    # feltétele, hogy a TÁROLT állapot EGYEZZEN a mostanival, ÉS régebbi
    # legyen a védőablaknál. (Az első változatom utólag öregített — akkor a
    # tárolt és a mostani mtime ELTÉRT, tehát nem is volt kihagyás, és a
    # próba a saját hipotézisét cáfolta volna meg tévesen.)
    regen = _regen()
    _regi_mappa_mtime(gyoker, regen)

    kapcsolat = _kapcsolat(tmp_path)
    conn = kapcsolat.__enter__()
    sync_tree(conn, gyoker)
    conn.commit()
    elso = _foto_allapot(conn)
    assert len(elso) == 1

    # a fájl HELYBEN változik (a mappa bejegyzései nem), a mappa mtime-ja
    # pedig változatlan marad — ezért lesz kihagyható
    make_jpeg(kep, size=(80, 60))
    uj = kep.stat()
    os.utime(kep, ns=(uj.st_mtime_ns + 1_000_000_000,) * 2)
    _regi_mappa_mtime(gyoker, regen)

    sync_tree(conn, gyoker)
    conn.commit()
    assert _foto_allapot(conn) == elso, (
        "az inkrementális szinkron ÁTVETTE a változást — akkor a #2824 "
        "magyarázata nem áll, és ezt a lapot újra kell gondolni"
    )


def test_a_TELJES_szinkron_atveszi(tmp_path):
    """A helyes eszköz: `incremental=False`. Ezzel a próba determinisztikus."""
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    kep = gyoker / "a.jpg"
    make_jpeg(kep, size=(40, 30))
    regen = _regen()
    _regi_mappa_mtime(gyoker, regen)

    kapcsolat = _kapcsolat(tmp_path)
    conn = kapcsolat.__enter__()
    sync_tree(conn, gyoker)
    conn.commit()
    elso = _foto_allapot(conn)

    make_jpeg(kep, size=(80, 60))
    uj = kep.stat()
    os.utime(kep, ns=(uj.st_mtime_ns + 1_000_000_000,) * 2)
    _regi_mappa_mtime(gyoker, regen)

    sync_tree(conn, gyoker, incremental=False)
    conn.commit()
    assert _foto_allapot(conn) != elso


def test_a_VEDOABLAKON_BELUL_az_inkrementalis_is_atveszi(tmp_path):
    """A védőablak dolgozik: a friss mappát sosem hagyjuk ki.

    Ez a kontroll — enélkül a fenti próba akkor is zöld lenne, ha a
    kihagyás MINDIG működne (és akkor a `#143` védőablaka volna törött)."""
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    kep = gyoker / "a.jpg"
    make_jpeg(kep, size=(40, 30))

    kapcsolat = _kapcsolat(tmp_path)
    conn = kapcsolat.__enter__()
    sync_tree(conn, gyoker)
    conn.commit()
    elso = _foto_allapot(conn)

    make_jpeg(kep, size=(80, 60))
    uj = kep.stat()
    os.utime(kep, ns=(uj.st_mtime_ns + 1_000_000_000,) * 2)
    # a mappa mtime-ját NEM toljuk vissza: friss marad, tehát nem hagyható ki

    sync_tree(conn, gyoker)
    conn.commit()
    assert _foto_allapot(conn) != elso
