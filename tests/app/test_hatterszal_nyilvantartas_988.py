"""Minden háttérmunka BE VAN KÖTVE a folyamat-szintű bevárásba (#988/#999).

## A lelet

Két tesztfájl szegmentálási hibával (SIGSEGV) állt le a CI-ben, terhelés
alatt: a `test_collage_controller_943.py` (#988) és a `test_editor.py`
(#999). A projekt ezt a hibaosztályt ismeri (#430/#438): egy daemon-szálról
emitált Qt-jelzés megöli a processzt, ha a küldő objektum közben
megsemmisül. A megoldás is megvolt — a lebontásnak be kell várnia a
szálakat, amíg a controllerek még élnek.

**A baj nem a mechanizmus volt, hanem a lefedettsége.** A teszt-fixture-ök
teardownja **kézzel felsorolta**, mely controllereket várja be, és a lista
elcsúszott attól, amit a fixture ténylegesen létrehoz:

| a fixture létrehozza | a régi teardown bevárta? |
|---|---|
| `AppController`, `Discovery`, `FolderTree`, `ImportSource`, `Compact` | igen |
| **`EditController`** (a `test_editor.py` ezt mozgatja) | **nem** |
| **`FaceScanController`** | **nem** |
| **`ThumbnailProvider` / `EffectThumbnailProvider` `QThreadPool`-ja** | **nem** |

## Mit állít ez a fájl

Azt, hogy a lista **nem tud újra elcsúszni**: a `_start_background` maga
jelentkezik be egy folyamat-szintű nyilvántartásba, a `QThreadPool`-t tartó
szolgáltatók pedig a `register_pool_owner`-rel — a teardown egyetlen
hívással vár be mindent.

⚠️ **Ez NEM terhelés-teszt.** A SIGSEGV véletlenszerű, a reprodukálásához
CPU-éhezés kell; a repóba ilyet tenni órákra lekötné a gépet, és nem is
bizonyítana többet. Amit determinisztikusan állítani lehet — és amit a
javítás tényleg megváltoztat —, az a **szerkezet**: nincs olyan háttérmunka
az `app` rétegben, ami kimaradhatna a bevárásból.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path

import picasapy.app
from picasapy.app.worker_thread import (
    BackgroundWorkerMixin,
    register_pool_owner,
    running_background_workers,
    wait_for_all_background_workers,
)

APP_DIR = Path(picasapy.app.__file__).parent


class _Pelda(BackgroundWorkerMixin):
    """Tetszőleges szálindító — NINCS és nem is lesz semmilyen listán."""


class _PoolTulajdonos:
    """`wait_for_done`-t nyújtó objektum, a szolgáltatók mintájára."""

    def __init__(self) -> None:
        self.vart = False

    def wait_for_done(self, msecs: int = 10_000) -> bool:
        self.vart = True
        return True


class TestABevarasFolyamatSzintu:
    """A bevárás nem a hívó listáján múlik, hanem a nyilvántartáson."""

    def test_a_fel_nem_sorolt_objektum_szalat_is_bevarja(self):
        """Ez a #999 lényege: az `EditController` sem volt a listán."""
        indulhat = threading.Event()
        pelda = _Pelda()
        pelda._start_background(indulhat.wait, name="teszt-szal")

        assert "teszt-szal" in running_background_workers()

        indulhat.set()

        assert wait_for_all_background_workers(10.0)
        assert running_background_workers() == ()

    def test_a_bejelentkezett_poolt_is_bevarja(self):
        tulajdonos = _PoolTulajdonos()
        register_pool_owner(tulajdonos)

        assert wait_for_all_background_workers(5.0)
        assert tulajdonos.vart, "a pool-tulajdonos `wait_for_done`-ja nem futott"


class TestNincsKikerulesiUt:
    """Az őr: az `app` rétegben ne lehessen a nyilvántartást megkerülni."""

    def test_nincs_nyers_szalinditas_az_app_retegben(self):
        """Szálat csak a mixinen át — különben kimaradna a bevárásból."""
        talalatok = [
            f"{ut.name}:{szam}"
            for ut in APP_DIR.rglob("*.py")
            if ut.name != "worker_thread.py"
            for szam, sor in enumerate(
                ut.read_text(encoding="utf-8").splitlines(), start=1
            )
            if "threading.Thread(" in sor
        ]

        assert not talalatok, (
            "nyers threading.Thread az app rétegben — használd a "
            "BackgroundWorkerMixin._start_background-ot (#430/#438/#988): "
            + ", ".join(talalatok)
        )

    def test_minden_QThreadPool_tulajdonos_bejelentkezik(self):
        """Aki `QThreadPool`-t tart, hívja a `register_pool_owner`-t."""
        hianyzik = [
            ut.name
            for ut in APP_DIR.rglob("*.py")
            if "QThreadPool()" in (forras := ut.read_text(encoding="utf-8"))
            and "register_pool_owner(self)" not in forras
        ]

        assert not hianyzik, (
            "QThreadPool bejelentkezés nélkül — a lebontás nem várná be "
            "(#988/#999): " + ", ".join(hianyzik)
        )


class TestATeardownAKozosBevarotHivja:
    """A két fixture ne térjen vissza a kézzel karbantartott listához."""

    def test_mindket_conftest_a_folyamat_szintut_hivja(self):
        gyoker = Path(__file__).resolve().parent
        conftestek = (gyoker / "conftest.py", gyoker / "qml_functional" / "conftest.py")

        for ut in conftestek:
            forras = ut.read_text(encoding="utf-8")

            assert "wait_for_all_background_workers(" in forras, (
                f"{ut.name}: a teardown nem a folyamat-szintű bevárót hívja"
            )
            assert not re.search(r"for bg_controller in \(", forras), (
                f"{ut.name}: visszatért a kézzel felsorolt controller-lista"
            )

    def test_a_bevaras_megelozi_a_qml_motor_megsemmisiteset(self):
        """#1193: a futó pool-job még élő Qt-válaszra küldjön jelzést."""
        gyoker = Path(__file__).resolve().parent
        conftestek = (gyoker / "conftest.py", gyoker / "qml_functional" / "conftest.py")

        for ut in conftestek:
            forras = ut.read_text(encoding="utf-8")

            assert forras.rindex("wait_for_all_background_workers(") < forras.rindex(
                "engine.deleteLater()"
            ), (
                f"{ut}: a QML-motor megsemmisítése futó háttérmunka mellett "
                "hozzáférési hibát okozhat"
            )


class TestABevarasVerdiktjeIgaz:
    """#999: a bevárás ne mondhasson „minden leállt"-ot futó szál mellett.

    A #430/#438 óta a lebontás egyetlen garanciára támaszkodik: ha a
    `wait_for_all_background_workers()` `True`-t ad, akkor egyetlen
    háttérszál sem nyúl többé Qt-objektumhoz. A #999 körében **két olyan
    utat mértünk ki, amelyen ez a verdikt HAMIS lehetett** — mindkettő a
    bevárón belül, nem a hívóknál. Az alábbi két őr ezeket zárja le.

    ⚠️ Amit ezek az őrök NEM állítanak: hogy a #999 szegmentálási hibája
    ezzel megszűnt. A hibát a mai `main`-en nem sikerült reprodukálni; ami
    itt bizonyított, az a bevárás verdiktjének helyessége, nem a
    SIGSEGV eltűnése.
    """

    def test_a_szal_a_nyilvantartasban_marad_az_utolso_qt_hivasaig(
        self, monkeypatch
    ):
        """A `registry.end()` Qt-jelzést emitál — a szál addig látszódjon.

        A `_start_background` `finally`-ága korábban ELŐBB vette ki a szálat
        a nyilvántartásból, és csak AZUTÁN hívta a `registry.end()`-et
        (`busy_registry.AppBusyRegistry.end` → `_endRequested.emit()`). A
        bevárás így egy még emitáló szálat sem látott.

        Mérve a javítás előtt: a `wait_for_all_background_workers()` 0,000
        mp alatt `True`-t adott, miközben a szál bent állt az `end()`-ben.
        """
        from picasapy.app import busy_registry

        benne_van = threading.Event()
        elengedheto = threading.Event()
        eredeti_end = busy_registry.AppBusyRegistry.end

        def lassu_end(maga):
            benne_van.set()
            elengedheto.wait(10.0)
            return eredeti_end(maga)

        monkeypatch.setattr(busy_registry.AppBusyRegistry, "end", lassu_end)

        pelda = _Pelda()
        szal = pelda._start_background(lambda: None, name="utolso-qt-hivas-999")
        try:
            assert benne_van.wait(10.0), "a szál nem ért el a registry.end()-ig"

            # EBBEN A PILLANATBAN a szál ÉL, és épp Qt-jelzést emitál.
            assert szal.is_alive()
            assert "utolso-qt-hivas-999" in running_background_workers(), (
                "a szál kikerült a nyilvántartásból, MIELŐTT az utolsó "
                "Qt-hívása lefutott volna — a bevárás így nem várja be (#999)"
            )
        finally:
            elengedheto.set()

        assert wait_for_all_background_workers(10.0)
        assert running_background_workers() == ()

    def test_a_bevaras_alatt_indult_szalat_is_bevarja(self, monkeypatch):
        """Nem egyetlen pillanatkép: a menet közben induló szál is számít.

        A bevárás korábban EGYSZER másolta le a `_ALL_WORKERS` halmazt, és
        azt a listát járta végig. Egy háttérmunka viszont indíthat újabbat:
        az `IndexWriterQueue.submit()` bármely szálról hívható, és ő indítja
        a futtató szálat (`index_writer_queue.py`).

        Az őr ÓRA NÉLKÜL determinisztikus: a `_Thread` cserélhető
        fogantyúján át figyeljük, mikor kezdi a bevárás az első szál
        `join()`-ját — a második szál PONTOSAN ekkor indul, és csak akkor
        ér véget, amikor a bevárás őt is bevárja. Ha a bevárás nem nyúl
        érte, a neve nem kerül a `bevart_nevek` listába, és az őr elbukik.
        """
        from picasapy.app import worker_thread

        elso_joinolva = threading.Event()
        masodik_joinolva = threading.Event()
        bevart_nevek: list[str] = []

        class _JoinKapu(threading.Thread):
            """Naplózza, melyik szálat várta be a bevárás — és kapuzza is."""

            def join(self, timeout=None):
                bevart_nevek.append(self.name)
                if self.name == "masodik-999":
                    masodik_joinolva.set()
                else:
                    elso_joinolva.set()
                return super().join(timeout)

        monkeypatch.setattr(worker_thread, "_Thread", _JoinKapu)

        pelda = _Pelda()

        def masodik() -> None:
            # csak a bevárás engedheti el: ha nem vár be, itt lejár az idő,
            # és a főszál állítása buktatja meg az őrt
            masodik_joinolva.wait(3.0)

        def elso() -> None:
            # a második szál PONTOSAN a bevárás alatt indul
            assert elso_joinolva.wait(10.0)
            pelda._start_background(masodik, name="masodik-999")

        pelda._start_background(elso, name="elso-999")

        assert wait_for_all_background_workers(20.0)
        assert "masodik-999" in bevart_nevek, (
            "a bevárás ALATT indult szálat a bevárás nem várta be — "
            "egyetlen pillanatképről dolgozott (#999)"
        )
        assert running_background_workers() == ()
