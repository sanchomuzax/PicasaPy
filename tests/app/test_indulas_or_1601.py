"""#1601 ŐR: az indulás blokkoló ideje NEM nőhet az ini-söpréssel arányosan.

A tulajdonos panasza nem „lassú", hanem **„egyre lassabb"** volt: nem egy
konstans költség a baj, hanem egy szakasz, ami a gyűjtemény méretével
skálázódik. Ez az őr pontosan ezt méri.

## A mérés szerkezete

Két könyvtárral indítjuk a vezérlőt (`_KICSI` és `_NAGY` ini-vel bíró
mappa), és megnézzük, mennyivel lassabb a nagyobbnál a `start()`
BLOKKOLÓ ideje. Ezt a NÖVEKMÉNYT egy ugyanezen a gépen, ugyanezen az
adaton mért **referenciához** viszonyítjuk: egyetlen teljes
`.picasa.ini`-söprés idejéhez (`load_side_pane_collections`) — pontosan
ahhoz a munkához, amit a #1601 levett a felület száláról.

## Miért nem abszolút ezredmásodperc a küszöb

Egy abszolút határ („az indulás legyen 300 ms alatt") gépfüggő, és a
négymagos fejlesztőgépen párhuzamos tesztfutás mellett flaky. Itt a
küszöb **önkalibráló**: a gép sebessége a növekményt és a referenciát
egyformán szorozza, tehát az arányuk stabil marad.

## A küszöb honnan jön — MÉRVE (RPi5, tmpfs, 2026-08-27)

| kód | 20 mappa | 400 mappa | növekmény | söprés | hányad |
|---|---|---|---|---|---|
| **javított** (1. futás) | 17 ms | 89 ms | 72 ms | ~264 ms | **27%** |
| **javított** (2. futás) | 73 ms | 94 ms | 22 ms | 536 ms | **4%** |
| a halasztás nélkül (mutáció) | 53 ms | 845 ms | 792 ms | 443 ms | **179%** |

A küszöb **50%**: a mért 4–27% fölött kényelmesen, a hibás 179% alatt
bőven. A megmaradó néhány százalék nem hiba — az induláskori SQL-munka
(`merge_duplicate_folders`, a mappalista betöltése) jogosan lineáris, és
mérve nagyságrenddel olcsóbb az ini-söprésnél.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QSettings

from picasapy.index import open_index, sync_tree
from picasapy.index.side_pane import load_side_pane_collections
from support.jpeg_factory import make_jpeg

#: A két mért könyvtárméret (ini-vel bíró mappák száma).
_KICSI = 20
_NAGY = 400

#: Szekció ini-nként — a valódi korpusz aránya (18 801 szekció / 859 ini).
#: Enélkül az ini-k olyan könnyűek lennének, hogy az őrnek nem volna foga.
_SZEKCIO_PER_INI = 22

#: A megengedett növekmény EGY teljes ini-söprés idejéhez mérve.
_MEGENGEDETT_HANYAD = 0.5

_ROY = "b8e4117cf1d6615b"
_ANNA = "a1a2a3a4a5a6a7a8"
_RECT = "3f840000c3509f84"


def _konyvtar(root, mappa_szam: int) -> None:
    """`mappa_szam` mappa, mindegyikben egy kép és egy valósághű súlyú ini.

    A képet EGYSZER állítjuk elő, utána bájtmásolat — a fixture felépítése
    így nem viszi el a mérés idejét."""
    root.mkdir(parents=True, exist_ok=True)
    minta = root / "minta.jpg"
    make_jpeg(minta, size=(32, 24))
    blob = minta.read_bytes()
    minta.unlink()
    szekciok = "".join(
        f"[IMG_{n:04d}.JPG]\n"
        f"faces=rect64({_RECT}),{_ROY};rect64({_RECT}),{_ANNA};\n"
        f"filters=enhance=1;\n"
        for n in range(_SZEKCIO_PER_INI)
    )
    ini = (
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n{_ANNA}=Anna Kis;;\n"
        f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY};\n" + szekciok
    )
    for i in range(mappa_szam):
        folder = root / f"{2000 + i % 20}" / f"{i:04d}"
        folder.mkdir(parents=True)
        (folder / "a.jpg").write_bytes(blob)
        (folder / ".picasa.ini").write_text(ini, encoding="utf-8")


def _konyvtar_es_index(tmp_path, nev: str, mappa_szam: int):
    """Felépített könyvtár + kész index — a mérésbe ez már nem számít bele."""
    base = tmp_path / nev
    lib = base / "kepek"
    _konyvtar(lib, mappa_szam)
    db = base / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)
    return base, lib, db


def _indulas_blokkolo_ms(base, lib, db) -> float:
    """A `start()` VISSZATÉRÉSÉIG eltelt idő — ennyit áll a felület."""
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    settings = QSettings(str(base / "settings.ini"), QSettings.Format.IniFormat)
    controller = AppController(
        db,
        (str(lib),),
        ThumbnailProvider(ThumbnailCache(base / "thumbs", size=32)),
        settings=settings,
        watched_file=base / "WatchedFolders.txt",
    )
    try:
        started = time.perf_counter()
        controller.start()
        return (time.perf_counter() - started) * 1000.0
    finally:
        controller.shutdown()
        controller.waitForBackgroundWorkers(120.0)


def _sopres_ms(db) -> float:
    """A referencia: EGY teljes `.picasa.ini`-söprés ugyanezen a gépen."""
    with open_index(db) as conn:
        load_side_pane_collections(conn)  # bemelegítés (lemez-gyorstár)
        started = time.perf_counter()
        load_side_pane_collections(conn)
        return (time.perf_counter() - started) * 1000.0


class TestIndulasNemSkalazodikAzIniSopressel:
    def test_a_blokkolo_indulas_novekmenye_a_sopres_tort_resze(
        self, qt_app, tmp_path
    ):
        kicsi = _konyvtar_es_index(tmp_path, "kicsi", _KICSI)
        nagy = _konyvtar_es_index(tmp_path, "nagy", _NAGY)

        kicsi_ms = _indulas_blokkolo_ms(*kicsi)
        nagy_ms = _indulas_blokkolo_ms(*nagy)
        novekmeny_ms = nagy_ms - kicsi_ms
        sopres_ms = _sopres_ms(nagy[2])

        assert novekmeny_ms <= sopres_ms * _MEGENGEDETT_HANYAD, (
            f"az indulás blokkoló ideje az ini-söpréssel arányosan nő: "
            f"{_KICSI} mappa → {kicsi_ms:.0f} ms, {_NAGY} mappa → "
            f"{nagy_ms:.0f} ms (növekmény {novekmeny_ms:.0f} ms), miközben "
            f"egy teljes söprés {sopres_ms:.0f} ms. A #1601 óta a "
            f"`.picasa.ini`-söprésnek a háttér-szinkron szálán kell futnia, "
            f"nem a felület szálán."
        )
