"""#1716 ŐR: az ottragadt mappák takarítása (#58) lekerül a kritikus útról.

## A lelet, amit ez az őr befagyaszt

A tulajdonos gépén mérve (#1706 modellje szerint):

```
védett gyökerek:  10
ottragadt mappák takarítása (#58):  2293,9 ms   ← A KRITIKUS ÚTON
```

10 gyökér × ~4 `lstat` = 40 hálózati hívás; NAS-on ~47 ms/`stat` → ~1,9 s —
nagyságrendileg egyezik a mért 2294 ms-mal. A feloldás ára ELKERÜLHETETLEN
(#1706/#1667 óta a nyilvántartott exportcélokat létezés-ellenőrzés nélkül
kell védeni), a #1711 már kiszedte a nyilvánvaló ismétlődést — több nem
hozható ki belőle a védelem gyengítése nélkül.

## A megoldás: ODÉBB, nem OLCSÓBB

Pontosan a #1667 mintája: a takarítás az első kirajzolt képkocka UTÁN fut
(`_start_and_finish` → `_ottragadt_mappak_takaritasa`), nem a kritikus úton.

## Miért DARABSZÁMOT mér ez az őr, nem időt

A #1653/#1667/#1706 tanulsága: egy időküszöb terhelés alatt flaky (a #1653
mérése szerint ugyanaz a szakasz 7,5-szörös szórást mutatott). A `normalize_
path`-hívások száma (a #1706 mérőszáma) viszont determinisztikus.

## A három állítás

1. **munkamennyiség** — a `run()` MOST már takarítás nélküli, első
   index-megnyitó blokkja NULLA útvonalat old fel; a takarítás (ahol ez
   ténylegesen megtörténik) pozitív számot ad, ha van védendő gyökér;
2. **elhelyezés** — a takarítás az első kirajzolt képkocka UTÁN fut
   (`_start_and_finish`), és a megkerülő út (a nyers `prune_foreign_
   folders` közvetlen hívása) is zárva;
3. **versenyhelyzet** — a takarítás a `_start_initial_scan` (tehát a
   `controller.start()` → `rescan()` háttérszál-indítás) ELŐTT fejeződik
   be. Ez a sorrend a szinkronpont: amíg ez áll, a háttér-szinkron szál a
   takarítás `commit()`-ja UTÁN keletkezik, tehát a kettő SOHA nem írja
   egyszerre ugyanazt az indexet.

A takarítás FUNKCIÓJA (mit töröl, mit véd) változatlan — azt a meglévő #58
őrök fedik (`tests/index/test_sync.py::TestPruneForeignFolders`,
`tests/perf/test_prune_gyokerek_1706.py`), ez a fájl csak az ELHELYEZÉST és
a MUNKAMENNYISÉGET méri.

## Mutációs bizonyíték (2026-08-28)

| # | mutáció | bukó őr |
|---|---|---|
| a | a takarítás hívása kikerül a `_start_and_finish`-ből (visszakerül a `run()` kritikus útjára) | `test_a_run_kritikus_utja_nem_hivja_a_takaritast`, `test_a_start_and_finish_hivja_a_takaritast` |
| a2 | a nyers `prune_foreign_folders` közvetlen hívása kerül a `run()`-ba (megkerülő út) | `test_a_nyers_prune_sincs_a_run_kritikus_utjan` |
| b | a `prune_foreign_folders` törlő ága elrontva (pl. a `DELETE FROM folders` kikommentezve) | `tests/index/test_sync.py::TestPruneForeignFolders::test_folders_outside_roots_removed`, `tests/perf/test_prune_gyokerek_1706.py` guardjai |
| c | a takarítás hívása a `_start_initial_scan` MÖGÉ kerül a `_start_and_finish`-ben (a szinkronpont elvétele) | `test_a_takaritas_a_hatterszinkron_elott_fejezodik_be` |
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.app import collage_prefs
from picasapy.app.application import (
    _onjavito_kollazsmappa,
    _ottragadt_mappak_takaritasa,
)
from picasapy.app.exported_folders import EXPORTED_FOLDERS_SETTINGS_KEY
from picasapy.index import open_index, sync_folder
from picasapy.index import sync as sync_modul
from support.jpeg_factory import make_jpeg


class _FeloldasSzamlalo:
    """A `normalize_path`-hívások száma — a #1706 mérőszáma, itt az
    ELHELYEZÉS igazolására: hol futnak le ezek a hívások, a takarítás
    ELŐTTI blokkban vagy magában a takarításban."""

    def __init__(self) -> None:
        self.hivasok = 0


@pytest.fixture
def feloldas_szamlalo(monkeypatch) -> _FeloldasSzamlalo:
    szamlalo = _FeloldasSzamlalo()
    eredeti = sync_modul.normalize_path

    def merve(path):
        szamlalo.hivasok += 1
        return eredeti(path)

    monkeypatch.setattr(sync_modul, "normalize_path", merve)
    return szamlalo


@pytest.fixture
def konyvtar(tmp_path):
    """Figyelt gyökér + egy ottragadt (idegen) mappa, kész indexszel."""
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "IMG_0001.jpg", size=(32, 24))

    # ⚠️ #1682: NE csak kis/nagybetűben térjen el a két mappanév.
    idegen = tmp_path / "ottragadt_regi_gyoker"
    idegen.mkdir()
    make_jpeg(idegen / "IMG_0002.jpg", size=(32, 24))

    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_folder(conn, gyoker, gyoker)
        sync_folder(conn, idegen, idegen)

    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    settings.setValue(EXPORTED_FOLDERS_SETTINGS_KEY, [])
    # ⚠️ hermetikus teszt: a `_onjavito_kollazsmappa` (#1075) alapértelmezés
    # szerint a FELHASZNÁLÓ VALÓS Képek/Kollázsok mappáját nézné meg — egy
    # nem létező tmp-útvonalra állítva NEM nyúl a géphez, és a munkamennyi-
    # ség-mérésbe sem kever bele idegen `normalize_path`-hívást.
    settings.setValue(collage_prefs.OUTPUT_DIR_KEY, str(tmp_path / "nincs_kollazs"))
    return db, gyoker, idegen, settings


class TestAMunkamennyisegAKritikusUtonNullaraCsokken:
    """(1) A munkamennyiség-állítás — ez a #1716 javításának foga."""

    def test_a_takaritas_elotti_blokk_nulla_utvonalat_old_fel(
        self, konyvtar, feloldas_szamlalo
    ):
        """A `run()` első, index-megnyitó blokkjában a takarítás UTÁN már
        csak a Kollázsok-mappa önjavítása fut (`_onjavito_kollazsmappa`) —
        ez SOHA nem old fel útvonalat védett gyökér ellenőrzéséhez, tehát a
        kritikus úton lévő munkamennyiség nullára csökkent."""
        db, gyoker, idegen, settings = konyvtar

        with open_index(db) as conn:
            _onjavito_kollazsmappa(conn, settings)

        assert feloldas_szamlalo.hivasok == 0, (
            f"a `run()` kritikus útján maradt blokk {feloldas_szamlalo.hivasok} "
            "útvonalat oldott fel — pedig a #1716 óta a takarítás (és vele "
            "az összes `normalize_path`-hívás) nem itt fut"
        )

    def test_a_takaritas_maga_pozitiv_szamot_ad(self, konyvtar, feloldas_szamlalo):
        """Pozitív kontroll (#1476/#1468 tanulsága): a nulla fenti állítása
        nem a számláló hibája — ugyanaz a számláló, a takarításra alkalmazva,
        pozitív számot ad, ha van védendő gyökér."""
        db, gyoker, idegen, settings = konyvtar

        _ottragadt_mappak_takaritasa(db, (str(gyoker),), settings)

        assert feloldas_szamlalo.hivasok > 0, (
            "a takarítás maga NULLA útvonalat oldott fel, pedig van egy "
            "figyelt gyökér — a számláló nem azt méri, amit hiszünk, tehát "
            "a fenti nulla-állítás sem bizonyít semmit"
        )

    def test_a_takaritas_tenylegesen_kidobja_az_ottragadt_mappat(
        self, konyvtar
    ):
        """A munkamennyiség-mérés nem üres adaton fut: a takarítás UTÁN az
        idegen mappa tényleg kikerül az indexből, a figyelt gyökér marad."""
        db, gyoker, idegen, settings = konyvtar

        _ottragadt_mappak_takaritasa(db, (str(gyoker),), settings)

        with open_index(db) as conn:
            mappak = [row["path"] for row in conn.execute("SELECT path FROM folders")]

        assert str(idegen.resolve()) not in mappak, (
            "az ottragadt mappa nem tűnt el a takarítás után — a #58 "
            "funkciója sérült az áthelyezés során"
        )
        assert str(gyoker.resolve()) in mappak, (
            "a figyelt gyökér is eltűnt — a takarítás túl sokat vitt el"
        )


class TestATakaritasNincsAKritikusUton:
    """(2) Az elhelyezés-állítás — a #1667 AST-alapú mintája.

    A forrás SZERKEZETÉT nézi, nem szöveget keres: egy átnevezés vagy egy
    sortörés nem üresíti ki."""

    @staticmethod
    def _run_fa() -> ast.FunctionDef:
        """A `run()` szintaxisfája — a MODULFÁJLBÓL kibontva (az
        `inspect.getsource` behúzott szövege önmagában nem elemezhető)."""
        from picasapy.app import application

        modul = ast.parse(
            Path(application.__file__).read_text(encoding="utf-8")
        )
        for node in modul.body:
            if isinstance(node, ast.FunctionDef) and node.name == "run":
                return node
        raise AssertionError("nincs `run()` az application.py-ban")

    @classmethod
    def _start_and_finish_fa(cls) -> ast.FunctionDef:
        run_fa = cls._run_fa()
        jeloltek = [
            node
            for node in ast.walk(run_fa)
            if isinstance(node, ast.FunctionDef) and node.name == "_start_and_finish"
        ]
        if not jeloltek:
            raise AssertionError(
                "a `run()`-ban nincs `_start_and_finish` — a #1601/#1667 "
                "első-képkocka utáni ága eltűnt"
            )
        return jeloltek[0]

    @staticmethod
    def _hivasok(csomopont, nev: str) -> list[ast.Call]:
        return [
            node
            for node in ast.walk(csomopont)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == nev
        ]

    def test_a_run_kritikus_utja_nem_hivja_a_takaritast(self):
        """A `run()` TESTÉBEN (a `_start_and_finish`-en KÍVÜL) nem
        maradhat hívás — az a kritikus út, amit a #1716 tehermentesít."""
        run_fa = self._run_fa()
        start_and_finish_fa = self._start_and_finish_fa()

        osszes = self._hivasok(run_fa, "_ottragadt_mappak_takaritasa")
        belul = self._hivasok(start_and_finish_fa, "_ottragadt_mappak_takaritasa")

        assert osszes, (
            "a `run()` sehol nem hívja a `_ottragadt_mappak_takaritasa`-t — "
            "a #58 takarítás elveszett induláskor"
        )
        assert len(belul) == len(osszes), (
            f"a takarítás a KRITIKUS ÚTON is fut "
            f"({len(osszes) - len(belul)} hívás az első kirajzolt képkocka "
            f"előtt). A tulajdonos gépén ez a lépés 2 293,9 ms-ig tartotta "
            f"vissza az ablakot (#1706); a helye a `_start_and_finish`-ben "
            f"van, a #1667 mintájára."
        )

    def test_a_nyers_prune_sincs_a_run_kritikus_utjan(self):
        """A megkerülő út is zárva: a `prune_foreign_folders` NYERS
        (`_ottragadt_mappak_takaritasa` melletti) hívása sem állhat a
        `run()` kritikus útján."""
        run_fa = self._run_fa()
        start_and_finish_fa = self._start_and_finish_fa()

        osszes = self._hivasok(run_fa, "prune_foreign_folders")
        belul = self._hivasok(start_and_finish_fa, "prune_foreign_folders")

        assert len(belul) == len(osszes), (
            f"a `run()` közvetlenül hívja a `prune_foreign_folders`-t az "
            f"első képkocka ELŐTT ({len(osszes) - len(belul)} hívás) — az "
            f"elhelyezés-őr így megkerülhető. A hívás a "
            f"`_ottragadt_mappak_takaritasa`-n át menjen."
        )

    def test_a_start_and_finish_hivja_a_takaritast(self):
        """Pozitív kontroll: a `_start_and_finish` TÉNYLEG hívja a
        takarítást — a fenti nulla nem azért van, mert a hívás egyáltalán
        eltűnt a forrásból."""
        start_and_finish_fa = self._start_and_finish_fa()
        assert self._hivasok(start_and_finish_fa, "_ottragadt_mappak_takaritasa"), (
            "a `_start_and_finish` nem hívja a `_ottragadt_mappak_"
            "takaritasa`-t — a #58 takarítás teljesen elveszett"
        )

    def test_a_takaritas_a_hatterszinkron_elott_fejezodik_be(self):
        """(3) A versenyhelyzet-állítás — a #1716 SZINKRONPONTJA.

        A `_start_initial_scan` hívja a `controller.start()`-ot, ami a
        `rescan()`-on át HÁTTÉRSZÁLAT indít (`_sync_worker`, saját SQLite-
        kapcsolattal). Amíg a takarítás hívása a `_start_and_finish`-ben
        MEGELŐZI a `_start_initial_scan` hívását, a háttérszál csak a
        takarítás `commit()`-ja UTÁN keletkezik — a kettő SOHA nem írja
        egyszerre az indexet, zár nélkül is. Ha ez a sorrend felcserélődik,
        a takarítás DELETE-jei versenyhelyzetbe kerülhetnek a szál épp
        folyamatban lévő INSERT/UPDATE-jeivel (pl. egy frissen szinkroni-
        zált mappa sora eltűnhet a szál keze alól)."""
        start_and_finish_fa = self._start_and_finish_fa()

        takaritas_hivasok = self._hivasok(
            start_and_finish_fa, "_ottragadt_mappak_takaritasa"
        )
        scan_hivasok = self._hivasok(start_and_finish_fa, "_start_initial_scan")

        assert takaritas_hivasok, "nincs takarítás-hívás a `_start_and_finish`-ben"
        assert scan_hivasok, "nincs `_start_initial_scan` hívás a `_start_and_finish`-ben"

        legkesobbi_takaritas = max(node.lineno for node in takaritas_hivasok)
        legkorabbi_scan = min(node.lineno for node in scan_hivasok)

        assert legkesobbi_takaritas < legkorabbi_scan, (
            "a takarítás hívása a `_start_initial_scan` (tehát a "
            "`controller.start()` → háttér-szinkron szál indítása) UTÁN "
            "vagy azzal egy sorban áll — a #1716 szinkronpontja ez a "
            "sorrend, elvétele versenyhelyzetet nyit a takarítás DELETE-jei "
            "és a háttérszál egyidejű írásai között"
        )
