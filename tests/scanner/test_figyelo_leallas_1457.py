"""#1457: a figyelő leállítása NEM hagyhat élő szálat referencia nélkül.

## A mérés, ami idevezetett

A CI utolsó 40 futásának naplójából **tizenhárom** jel nélküli összeomlás jött
elő (a futtató újrapróbálta őket, ezért a bukás nem látszott):

| fájl | összeomlás | `start()`-ot hív? |
|---|---|---|
| `test_projekt_mappa_figyeles_1123.py` | 7 | igen |
| `test_elo_frissules_1435.py` | 2 | igen |
| `test_gyoker_athelyezes_kovetes_1542.py` | 1 | igen |
| `test_csillag_lanc_1438.py` | 2 | **nem** |
| `test_naplo_lefedettseg_750.py` | 1 | **nem** |

Kilépőkódok: `-11` (SIGSEGV) 5×, `0xC0000005` 2×, `0xC0000409` 6×.

Tizenháromból **tíz** a `controller.start()`-ot hívó tizenhárom
app-tesztfájl valamelyikéből jön (a `tests/app` több mint 200 fájljából)
— ezek futtatják a valódi figyelőt és a lekérdező időzítőket. ⚠️ A
maradék három NEM ilyen fájl, tehát a `start()` nem az egyetlen út.

## Amit ez a fájl állít

A `LibraryWatcher.stop()` `join(timeout=5)`-öt hív, és utána **minden
esetben** eldobta a megfigyelőre mutató referenciát. Ha a join
időtúllépéssel tér vissza, a szál TOVÁBB FUT, a hívó viszont már
leállítottnak hiszi — a szál pedig egy lebontás alatt álló objektumra
mutató kezelővel dolgozik.

⚠️ **Ez a mechanizmus, nem a bizonyított diagnózis.** Hogy az
összeomlásokat tényleg ez okozza-e, a következő CI-összeomlás
veremképéből derül ki (a futtató most már kiírja — ugyanez a jegy).
Amit itt javítunk, az attól függetlenül hiba: a néma eldobás.
"""

from __future__ import annotations

import threading

from picasapy.scanner.watcher import LibraryWatcher


class _NemAllMeg:
    """Olyan megfigyelő, aminek a `join`-ja időtúllépéssel tér vissza."""

    def __init__(self) -> None:
        self.stop_hivva = False
        self.join_hivva = False

    def stop(self) -> None:
        self.stop_hivva = True

    def join(self, timeout=None) -> None:
        self.join_hivva = True

    def is_alive(self) -> bool:
        return True


class _RendesenMegall(_NemAllMeg):
    def is_alive(self) -> bool:
        return False


class TestALeallas:
    def test_a_rendesen_megallo_megfigyelo_referenciaja_elengedheto(self):
        figyelo = LibraryWatcher((), lambda _mappak: None)
        figyelo._observer = _RendesenMegall()
        figyelo._running = True
        figyelo.stop()
        assert figyelo._observer is None
        assert figyelo.leallt() is True

    def test_az_ELO_szalat_NEM_dobjuk_el_nemán(self, caplog):
        figyelo = LibraryWatcher((), lambda _mappak: None)
        megfigyelo = _NemAllMeg()
        figyelo._observer = megfigyelo
        figyelo._running = True
        figyelo.stop()
        assert megfigyelo.stop_hivva and megfigyelo.join_hivva
        assert figyelo._observer is megfigyelo, (
            "az élő szálra mutató referenciát eldobtuk — a szál egy lebontás "
            "alatt álló objektumra mutató kezelővel fut tovább"
        )
        assert figyelo.leallt() is False
        assert any(
            "figyelő" in rekord.message.lower() for rekord in caplog.records
        ), "az időtúllépés némán maradt"

    def test_a_leallt_ures_figyelore_is_valaszol(self):
        figyelo = LibraryWatcher((), lambda _mappak: None)
        assert figyelo.leallt() is True

    def test_a_visszajelzes_nem_dob_ha_a_megfigyelo_nem_ismer_is_alive_ot(self):
        """A watchdog `Observer`-e `threading.Thread` leszármazott, tehát
        ismeri — de a próbák és a régebbi verziók kedvéért a hiánya nem
        dönthet le semmit."""

        class _Csupasz:
            def stop(self):
                pass

            def join(self, timeout=None):
                pass

        figyelo = LibraryWatcher((), lambda _mappak: None)
        figyelo._observer = _Csupasz()
        figyelo._running = True
        figyelo.stop()
        assert figyelo._observer is None

    def test_a_valodi_megfigyelo_szal_leszarmazott(self):
        """A `is_alive` létezése nem feltevés: a watchdog megfigyelője
        `threading.Thread`."""
        from watchdog.observers import Observer

        assert issubclass(Observer, threading.Thread)


class TestAVarakozas3059:
    """#3059: a teszt-segéd MEGVÁRJA a megfigyelő szálat.

    A windowsos CI-n a `test_projekt_mappa_figyeles_1123.py` `0xC0000409`
    fast-faillel omlott össze — kétszer egymás után. A segéd eddig EGYSZER
    kérdezte meg, leállt-e a szál, és ha nem, továbbengedte a teardownt: a
    megfigyelő szál a lebontás közben is futott.
    """

    def test_a_segéd_VÁR_a_szálra(self):
        """Forrás-szintű állítás: van ciklus és határidő.

        Viselkedésben nem reprodukálható: a szál megállása gépfüggő, és a
        hiba pont ott jött elő, ahol nem tudunk futtatni (Windows)."""
        from pathlib import Path

        import tests.support.figyelo as modul

        forras = Path(modul.__file__).read_text(encoding="utf-8")
        assert "_VARAKOZAS_S" in forras
        assert "while not figyelo.leallt()" in forras

    def test_a_le_nem_allt_figyelot_NEM_dobja_el(self):
        """A referencia eldobása a szál alól szabadítaná fel a figyelőt."""
        from tests.support.figyelo import allitsd_le_a_figyelot

        class MakacsFigyelo:
            def stop(self):
                pass

            def leallt(self):
                return False

        class Vezerlo:
            _watcher = MakacsFigyelo()

        vezerlo = Vezerlo()
        allitsd_le_a_figyelot(vezerlo)

        assert vezerlo._watcher is not None, (
            "a le nem állt figyelő referenciáját eldobtuk"
        )
