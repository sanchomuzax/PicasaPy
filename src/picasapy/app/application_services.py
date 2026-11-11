"""application services az alkalmazásindítóhoz."""

from __future__ import annotations

import logging
import os
import sqlite3
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QLibraryInfo, QLocale, QSettings, QTimer, QTranslator
from PySide6.QtGui import QGuiApplication

from picasapy.index import open_index
from picasapy.perf import start_startup_timeline
from picasapy.perf.logwriter import session_header
from picasapy.perf.tesztuzem import (
    argv_kapcsolo_nelkul,
    irj_indulasi_naplot,
    konyvtar_merete,
    naplo_szovege,
    tarolo_tipusa,
)
from picasapy.version import version_string
from . import application as _app
from .i18n_build import forditsd
from .language_controller import (
    DEFAULT_LANGUAGE,
    LANGUAGE_KEY,
    coerce_language,
    resolve_first_run_language,
    resolve_startup_language,
)

if TYPE_CHECKING:
    from .controller import AppController
    from .dedup_controller import DedupController
    from .fileops_controller import FileOpsController

def wire_fileops(fileops: FileOpsController, controller: AppController) -> None:
    """Fájlműveletek utáni index-frissítés (#15): a sikeres átnevezés/
    áthelyezés/másolás/törlés után az érintett mappák célzott resyncje, hogy
    a rács (és a .picasa.ini-t követő szekció) azonnal a valós állapotot
    mutassa."""

    from .application_platform import _watched_folder_of

    def refresh(*paths: str) -> None:
        seen: set[str] = set()
        for path in paths:
            folder = _watched_folder_of(path, controller.watchedFolders)
            if folder is not None and folder not in seen:
                seen.add(folder)
                controller.resyncFolder(folder)

    fileops.photoRenamed.connect(lambda old, new: refresh(old, new))
    fileops.photoMoved.connect(lambda old, new: refresh(old, new))

    def select_new_folder_when_indexed(folder: str) -> None:
        from picasapy.index import photos_in_folder

        previous = controller.currentFolder
        active = True

        def after_sync() -> None:
            nonlocal active
            if not active:
                return
            if controller.currentFolder != previous:
                active = False
                controller.syncFinished.disconnect(after_sync)
                return
            with open_index(controller._db_path) as conn:
                ready = bool(photos_in_folder(conn, folder))
            if ready:
                active = False
                controller.syncFinished.disconnect(after_sync)
                controller.selectFolder(folder)
                QTimer.singleShot(0, lambda: (
                    controller.showSelectedFolderToken(folder)
                    if controller.currentFolder == folder else None
                ))

        controller.syncFinished.connect(after_sync)

    fileops.newFolderMoveFinished.connect(select_new_folder_when_indexed)
    fileops.photoMoveFailed.connect(lambda old, dest: refresh(old, dest))

    def torles_utan(path: str) -> None:
        """#1227: a sor AZONNAL tűnjön el, a resync csak utólag egyeztessen.

        A sorrend számít: előbb a látható hatás (a rács kiveszi a sort),
        utána a lemez/index egyeztetése. Fordítva a felhasználó a szinkron
        végéig nézné a törölt képet — nagy könyvtárnál percekig.
        """
        controller.removeDeletedRow(path)
        refresh(path)

    fileops.photoDeleted.connect(torles_utan)
    # #1522: másolásnál CSAK a célmappa változott — a forrás érintetlen
    # marad, annak újraolvasása fölösleges lemez- és indexmunka volna.
    fileops.photoCopied.connect(lambda _source, new: refresh(new))
    # #1538: a MAPPA áthelyezése SZÁNDÉKOSAN nem a `refresh()`-en megy. Az
    # fájlutakra van szabva (`_watched_folder_of` a `.parent`-et veszi),
    # tehát egy mappára a SZÜLŐT olvasná újra — ráadásul nem-rekurzívan,
    # így sem az áthelyezett mappa sora, sem az almappáié nem kerülne a
    # helyére. A részfa-logika a vezérlőben él (`resyncMovedFolder`), mert
    # a RÉGI oldalhoz az INDEXET kell megkérdezni: a lemezen az már nincs.
    fileops.folderMoved.connect(lambda old, new: controller.resyncMovedFolder(old, new))
    # #1638: a lomtárba tett mappa kivezetése az indexből — ugyanaz a
    # részfa-logika, mint az áthelyezés RÉGI oldalán (a lemezen már nincs
    # meg, tehát az indexet kell megkérdezni).
    fileops.folderDeleted.connect(lambda path: controller.resyncDeletedFolder(path))

def wire_dedup(dedup: DedupController, controller: AppController) -> None:
    """A duplikátum-kezelő utáni index-frissítés (#1539).

    A dedup mindkét feloldó művelete a LEMEZT változtatja meg, az indexnek
    viszont eddig egyikről sem szólt: az `itemResolved`-nek egyetlen
    fogyasztója volt, a dialógus sorát levevő QML-kezelő.

    Mérve (valódi vezérlő, produkciós `FOLDER_POLL_MS`, figyelő nélkül): a
    „Duplikátumok" almappába mozgatott kép **25 s alatt sem jelent meg**, a
    forrásmappából pedig 10,3 s-ig (a #1275 lekérdezéssel), illetve
    egyáltalán nem (anélkül) tűnt el a sora.

    Két jelzés kell, mert két mappa változik:

    * `itemResolved` — a FORRÁSMAPPA, mindkét ágon (kukázás és áthelyezés
      is onnan viszi el a képet);
    * `photoRelocated` — a CÉLMAPPA, ami frissen létrehozott, sosem
      indexelt könyvtár (a #1522 alakja).

    A `deleteOthers` ágán SZÁNDÉKOSAN nincs második kötés: a Kuka nem a
    figyelt körben van, oda nincs mit újraolvasni."""
    dedup.itemResolved.connect(controller.resyncOutputFolder)
    dedup.photoRelocated.connect(lambda _source, new: controller.resyncOutputFolder(new))

def _configured_language(settings: QSettings | None = None) -> str:
    """Az EBBEN a futásban érvényes nyelv: a környezeti változó nyer, utána
    a mentett beállítás, végül az alapértelmezés (#333).

    CSAK OLVAS (#3555): futás közben is hívják (pl. a kollázs mappanevéhez,
    `collage_output._felulet_nyelve`), és ott a megerősített, de a KÖVETKEZŐ
    indításra váró választás még nem érvényes. A beérést az induláskori
    `_startup_language` végzi.
    """
    forced = os.environ.get("PICASAPY_LANG")
    if forced:
        return coerce_language(forced)
    if settings is None:
        settings = QSettings("PicasaPy", "PicasaPy")
    return coerce_language(settings.value(LANGUAGE_KEY, DEFAULT_LANGUAGE))

def _startup_language(
    settings: QSettings | None = None, *, prompt_timeout_ms: int | None = None
) -> str:
    """Az induláskor betöltendő nyelv — itt érik be a függő választás
    (#3555, `resolve_startup_language`), a fordító betöltése előtt. Hiányzó
    nyelvbeállításnál előbb az egyszeri rendszer-nyelv-felajánlást intézi
    (`resolve_first_run_language`, #4325).

    Ez a legkorábbi lehetséges hely; az `AppController` saját induláskori
    hívása ugyanerre a `QSettings`-re már csak szinkronban talál mindent
    (idempotens). A környezeti változó itt is nyer, és nem nyúl a
    beállításhoz.
    """
    forced = os.environ.get("PICASAPY_LANG")
    if forced:
        return coerce_language(forced)
    if settings is None:
        settings = QSettings("PicasaPy", "PicasaPy")
    selected = resolve_first_run_language(
        settings,
        lambda system_language: _app._ask_first_run_language(
            system_language, timeout_ms=prompt_timeout_ms
        ),
    )
    if selected is not None:
        return selected
    return resolve_startup_language(settings)

def _install_qt_translator(app: QGuiApplication) -> None:
    """A Qt saját (`qtbase_*.qm`) fordítója — a Quick Controls szabványos
    gombjai (Mégse, Abbrechen…) ebből jönnek. A PicasaPy `.qm`-jei ezt nem
    hozzák, és a Qt nem tölti be magától; a default QLocale csak a nyelvet
    választja ki, a fájlt nekünk kell betölteni (#4881).

    Hiányzó fájlnál (a `qt6-translations-l10n` csomag nélkül) hangos
    figyelmeztetés, és az angol gombfeliratok maradnak."""
    tr = QTranslator(app)
    if tr.load(QLocale(), "qtbase", "_", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(tr)
    else:
        logging.getLogger(__name__).warning(
            "a Qt fordítása (qtbase_%s.qm) nem található — a szabványos gombok angolul maradnak",
            QLocale().name(),
        )

def _install_translator(app: QGuiApplication, language: str | None = None) -> QTranslator | None:
    """A `language` (vagy a beállított) nyelv fordítójának telepítése.

    Az angol katalógus azonos fordításokat tartalmaz, de a forrásszövegek
    maguk angolok — ezért ott nem telepítünk fordítót.
    """
    code = coerce_language(language) if language else _app._startup_language()
    # #4881: a Quick Controls párbeszédeinek szabványos gombjai (OK, Mégse…)
    # az alapértelmezett QLocale-ból töltik a Qt saját fordítását — enélkül a
    # rendszer nyelvén jelennének meg a választott felületi nyelv helyett.
    # ADR-004 (nyelv ≠ területi beállítás): a NYELV a felületé, a TERÜLET
    # (tizedesjel, időformátum, mértékegység) marad a rendszeré.
    QLocale.setDefault(QLocale(QLocale(code).language(), QLocale.system().territory()))
    if code == DEFAULT_LANGUAGE:
        return None
    _install_qt_translator(app)
    # #4817: forrásból indítva a `.qm` itt készül el a `.ts`-ből. A
    # PyInstaller-csomagban a `.qm` a build terméke (#6344): ott nincs mit
    # fordítani, és a `Program Files` alá írni sem lehetne.
    if not getattr(sys, "frozen", False):
        forditsd(_app._I18N_DIR / f"picasapy_{code}.ts")
    translator = QTranslator(app)
    if translator.load(f"picasapy_{code}", str(_app._I18N_DIR)):
        app.installTranslator(translator)
        return translator
    return None

def _indexelt_kepszamok(data_dir: Path) -> tuple[int, ...]:
    """A mappánkénti képdarabszámok az indexből — CSAK SZÁMOK.

    ⚠️ Adatvédelem (#211/#1654): a mappanevek és útvonalak itt SZÁNDÉKOSAN
    eldobódnak, még mielőtt a naplóösszeállítóhoz érnének. A #1653 fő
    gyanúja a méretfüggés, ahhoz pedig a darabszám elég.

    Hibánál üres sorozat: egy diagnosztika nem dönthet el egy indulást."""
    try:
        with open_index(data_dir / "index.db") as conn:
            return tuple(
                int(count)
                for _name, _path, count, *_rest in _app._lazy_app_symbol(
                    "sorted_folder_rows"
                )(conn)
            )
    except sqlite3.DatabaseError:
        logging.getLogger(__name__).warning(
            "a könyvtárméret leolvasása hibára futott", exc_info=True
        )
        return ()

def _jelentsd_az_idovonalat(
    timeline, kepszamok=None, vedett_gyokerek=None, *, run_log=None
) -> None:
    """#6385: az indulási idővonal és a tárolótípus naplózása minden futáskor.

    Az alap napló a korai, rotáló futásfájlba kerül. A részletes tesztüzem
    továbbra is ír átadható, időbélyeges naplót is.

    A `kepszamok` és `vedett_gyokerek` késleltetett hívók: csak a részletes
    tesztüzem kéri le ezeket, hogy a szokásos indulás ne nyisson indexet.

    A jelentés nem tartalmaz fájlnevet, teljes útvonalat és
    felhasználónevet, ld. `perf/tesztuzem.py` (`utvonalmentes`).

    Hibája soha nem akadályozhatja az indulást — egy diagnosztika nem
    fontosabb a programnál."""
    if not timeline.enabled:
        return
    try:
        from PySide6.QtCore import qVersion

        verzio = version_string()
        qt_verzio = qVersion() or ""
        tarolo = {
            "a program helye": tarolo_tipusa(Path(__file__).resolve()),
            "a könyvtár helye": tarolo_tipusa(_app._data_dir()),
        }
        if kepszamok is None and vedett_gyokerek is None:
            # A szokásos indulás csak a szakaszokat, időket és tárhelytípust
            # rögzíti; az indexméret lekérdezése a részletes tesztüzemé.
            szoveg = timeline.render(app_version=verzio, qt_version=qt_verzio)
            szoveg += "\nA tároló típusa (útvonal nélkül):\n"
            szoveg += "".join(f"  {cimke}: {tipus}\n" for cimke, tipus in tarolo.items())
        else:
            szoveg = naplo_szovege(
                idovonal_jelentes=timeline.render(
                    app_version=verzio, qt_version=qt_verzio
                ),
                fejlec=session_header(verzio, qt_verzio),
                meret=konyvtar_merete(kepszamok() if kepszamok is not None else ()),
                vedett_gyokerek=(
                    len(vedett_gyokerek()) if vedett_gyokerek is not None else None
                ),
                tarolo=tarolo,
            )
        if run_log is not None:
            run_log.write(szoveg)
        if run_log is None or kepszamok is not None or vedett_gyokerek is not None:
            print(szoveg, file=sys.stderr)
            target = irj_indulasi_naplot(szoveg, _app.default_log_dir())
            if target is not None:
                print(f"Az indulási napló ide került: {target}", file=sys.stderr)
    except Exception:  # noqa: BLE001 - a diagnosztika sosem viheti el az appot
        logging.getLogger(__name__).warning(
            "az indulási idővonal kiírása hibára futott", exc_info=True
        )

def _indulasi_idovonal(
    argv: list[str],
    *,
    settings=None,
    environ: Mapping[str, str] | None = None,
    entry_at: float | None = None,
    run_log=None,
    clock=time.perf_counter,
) -> tuple[object, list[str]]:
    """A `run()` LEGELSŐ érdemi lépése: mérünk-e, és mivel indulunk (#1654).

    Az idővonal minden indításkor aktív, mert a hibaelhárításhoz a
    következő indulásból is kell adat.

    Három út kapcsolja be a részletes, indexméretet is tartalmazó mérést:

    * a **tartós tesztüzem** (`QSettings`), amit a `Súgó ▸ Tesztüzem`
      menüpont állít, és ami TÚLÉLI a kilépést. Ez az a bejárat, amit a
      tulajdonos használ: bekapcsolja, kilép, és a KÖVETKEZŐ indulás
      magától méri magát;
    * a `--tesztuzem` **parancssori kapcsoló** — csak erre a futásra, a
      beállítást nem írja át (fejlesztői és CI-oldal);
    * a `PICASAPY_STARTUP_TIMELINE=1` **környezeti változó** (#1601), amire
      a #1653 windowsos CI-mérése épül.

    A visszaadott argumentumlistából a `--tesztuzem` kikerül: az
    `_resolve_roots` MINDEN `argv[1:]` elemet figyelt gyökérnek vesz, tehát
    bennhagyva egy `--tesztuzem` nevű mappát próbálnánk indexelni.

    ⚠️ Az `entry_at` szakaszát ITT zárjuk le, közvetlenül a példány
    létrehozása után: a naplózás így az ELSŐ ezredmásodperctől — a Python-
    és PySide6-importoktól — fut, nem csak innentől."""
    timeline = start_startup_timeline(environ, forced=True, clock=clock)
    if run_log is not None:
        timeline._set_mark_observer(
            lambda label, elapsed_ms: run_log.mark(
                f"{label} ({elapsed_ms:.1f} ms)"
            )
        )
    if entry_at is not None:
        timeline.mark_from(entry_at, "Python- és PySide6-modulok betöltése")
    return timeline, argv_kapcsolo_nelkul(argv)

def argv_onellenorzes(argv: list[str]) -> tuple[bool, list[str]]:
    """`(kérték-e, a kapcsoló nélküli argumentumlista)`."""
    kert = _app._ONELLENORZES_KAPCSOLO in argv
    if not kert:
        return False, list(argv)
    return True, [elem for elem in argv if elem != _app._ONELLENORZES_KAPCSOLO]

def argv_indulasellenorzes(argv: list[str]) -> tuple[bool, list[str]]:
    """A teljes, ablakmegjelenítésig futó Windows-CI füstpróba kapcsolója."""
    kert = _app._INDULAS_ELLENORZES_KAPCSOLO in argv
    if not kert:
        return False, list(argv)
    return True, [elem for elem in argv if elem != _app._INDULAS_ELLENORZES_KAPCSOLO]
