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
