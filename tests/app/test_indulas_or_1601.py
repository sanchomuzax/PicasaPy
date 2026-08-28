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

from PySide6.QtCore import QCoreApplication, QSettings

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
#:
#: ⚠️ #1689: 0,5 → 1,0. A 0,5 a CI terhelése alatt **51%-on** megbukott
#: (120 ms növekmény, 235 ms söprés), pedig a termék jó volt. Az arány
#: önkalibráló ugyan, de a két mérés NEM egyszerre készül: egy közben
#: beérkező terhelés az egyiket jobban torzítja, mint a másikat.
#:
#: A szűk küszöb szerepét átvette a fölötte álló, DETERMINISZTIKUS
#: munkamennyiség-őr (nulla főszáli ini-olvasás). Ez az időarányos mérce
#: durva hálóként marad: a mért regresszió 179% volt, tehát az 1,0 azt
#: bőven megfogja, flaky-ség nélkül.
_MEGENGEDETT_HANYAD = 1.0

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


def _fosz_ali_ini_olvasasok(base, lib, db) -> int:
    """Hány `.picasa.ini`-t olvas a FŐSZÁL a `start()` alatt? — #1689.

    Ez a MUNKAMENNYISÉG-mérce. Az időarányos őr (lentebb) a CI terhelése
    alatt megbukott 51%-on az 50%-os küszöbnél, pedig a termék jó volt:
    az arány önkalibráló ugyan, de a két mérés NEM egyszerre készül,
    tehát egy közben beérkező terhelés az egyiket jobban torzítja.

    A munkamennyiség ezzel szemben determinisztikus: a #1601 óta az
    ini-söprésnek a háttérszálon kell futnia, tehát a főszálon NULLA
    ini-olvasásnak kell történnie — a könyvtár méretétől függetlenül.
    """
    import threading

    from picasapy.index import folder_ini
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    fosz = threading.get_ident()
    szamlalo = {"fosz": 0, "hatter": 0}
    eredeti = folder_ini.load_document

    def merve(*args, **kwargs):
        kulcs = "fosz" if threading.get_ident() == fosz else "hatter"
        szamlalo[kulcs] += 1
        return eredeti(*args, **kwargs)

    folder_ini.load_document = merve
    try:
        settings = QSettings(
            str(base / "settings.ini"), QSettings.Format.IniFormat
        )
        controller = AppController(
            db,
            (str(lib),),
            ThumbnailProvider(ThumbnailCache(base / "thumbs", size=32)),
            settings=settings,
            watched_file=base / "WatchedFolders.txt",
        )
        try:
            controller.start()
            # ⚠️ A `start()` VISSZATÉRÉSE nem elég mérési ablak: a hasáb
            # frissítése a felület szálán a `syncFinished` UTÁN fut. Ha csak
            # a `start()`-ig mérnénk, a számláló akkor is nulla lenne, ha a
            # főszál később mégis maga söpri az ini-ket — az őrnek nem volna
            # foga. (Ezt mutációval ellenőriztük: a letét kiürítésével a
            # szűkebb ablak NEM bukott el.)
            controller.waitForBackgroundWorkers(120.0)
            for _ in range(20):
                QCoreApplication.processEvents()
            return szamlalo["fosz"]
        finally:
            controller.shutdown()
            controller.waitForBackgroundWorkers(120.0)
    finally:
        folder_ini.load_document = eredeti


def _sopres_ms(db) -> float:
    """A referencia: EGY teljes `.picasa.ini`-söprés ugyanezen a gépen."""
    with open_index(db) as conn:
        load_side_pane_collections(conn)  # bemelegítés (lemez-gyorstár)
        started = time.perf_counter()
        load_side_pane_collections(conn)
        return (time.perf_counter() - started) * 1000.0


class TestIndulasNemSkalazodikAzIniSopressel:
    def test_a_foszal_egyetlen_ini_t_sem_olvas_indulaskor(self, qt_app, tmp_path):
        """#1689: MUNKAMENNYISÉG-mérce — terheléstől független.

        A #1601 óta az ini-söprés a háttér-szinkron szálán fut. A főszálon
        tehát NULLA `.picasa.ini`-olvasásnak kell történnie, és ez a szám a
        könyvtár méretével sem nőhet.
        """
        kicsi = _konyvtar_es_index(tmp_path, "kicsi_db", _KICSI)
        nagy = _konyvtar_es_index(tmp_path, "nagy_db", _NAGY)

        kicsi_olvasas = _fosz_ali_ini_olvasasok(*kicsi)
        nagy_olvasas = _fosz_ali_ini_olvasasok(*nagy)

        assert nagy_olvasas == kicsi_olvasas == 0, (
            f"a főszál ini-t olvas az induláskor: {_KICSI} mappa → "
            f"{kicsi_olvasas} olvasás, {_NAGY} mappa → {nagy_olvasas}. "
            "A #1601 óta az ini-söprésnek a háttér-szinkron szálán kell "
            "futnia, nem a felület szálán."
        )

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
