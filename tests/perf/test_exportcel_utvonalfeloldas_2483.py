"""#2483 ŐR: az exportcélok visszavétele nem oldhat fel útvonalakat feleslegesen.

## A lelet

A tulajdonos indulási naplója (v0.8.293, Windows 11, 2026-09-05) szerint az
indulás 30,4 másodperc, és ebből **26 117 ms (86%) az „exportcélok
visszavétele" szakasz** — miközben a #1667 védelme ép, és a #1674
inkrementális kihagyása MŰKÖDIK: nulla fájlnyitás, nulla fotósor-írás.

A #1667 őre (`test_exportcelok_indulas_1667.py`) ezért ZÖLD maradt: az a
mérőszám a **fájlnyitást** (`read_file_metadata`) számolja, ez a szakasz
viszont nem attól drága. MÉRVE (helyi lemez, 4 változatlan exportcél,
hívási helyre visszavezetve):

```
    35 fájlrendszer-hívás CÉLONKÉNT, ebből 32 (91%) merő útvonal-feloldás
    22/cél  lstat  ← name_filters.py `_normalised_path_parts`
    10/cél  lstat  ← paths.py `normalize_path`
     1/cél  stat   ← exported_folders.py `existing_exported_folders`
     1/cél  scandir← walker.py `scan_folder`
     1/cél  stat   ← walker.py `_scan_folder` (a mappa mtime-ja)
```

Két szerkezeti ok:

1. **A gyári kizárólista mappánként újraépült.** A `scan_folder` minden
   hívásnál `default_name_filters()`-t hívott, és a `NameFilters.__post_init__`
   MINDEN alkalommal feloldotta (`Path.resolve()`) mind az öt gyári
   útvonal-előtagot (`~/.cache`, `~/.local/share/Trash`, `/proc`, `/sys`,
   `/usr`). Ezek konstansok: a feloldásuk munkamenetenként EGYSZER kell.
2. **A `sync_folder` kétszer oldotta fel UGYANAZT az útvonalat**, mert az
   indulási ág a gyökeret és a mappát azonos értékkel adja át
   (`sync_folder(conn, mappa, mappa)`).

**Miért ez adja a 26 másodpercet.** A #1706 ugyanezen a gépen mérte, hogy
egy útvonal-rendszerhívás a tulajdonos tárolóján ~47 ms. A naplóban 12
védett gyökér szerepel (≈10 nyilvántartott exportcél); 10 × ~50 hívás ×
47 ms ≈ 23,5 s — a mért 26 117 ms ebbe a tartományba esik. A munka
mennyisége tehát a magyarázat, nem a gép.

## Miért DARABSZÁMOT mér ez az őr

A #1653 mérése szerint ugyanaz a szakasz ugyanazon a commiton 7,5-szeres
szórást mutat — időküszöb itt nem lehet nem-flaky. A hívásszám viszont
determinisztikus.

## Miért „a fán KÍVÜLI hívás" az első állítás

Depth-független és nulla-értékű: a próbakönyvtáron kívülre eső feloldás
csakis a gyári előtagok újrafeloldása lehet. Egy abszolút hívásszám-küszöb
ezzel szemben a `--basetemp` mélységétől függne, tehát flaky lenne.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.application import _ujraindexelt_exportcelok
from picasapy.app.exported_folders import EXPORTED_FOLDERS_SETTINGS_KEY
from picasapy.index import open_index, sync_folder
from picasapy.scanner.name_filters import default_name_filters
from support.jpeg_factory import make_jpeg

#: A #139 frissesség-védőablaka 2 s — a próbának ennél idősebb mappa kell,
#: különben a kihagyás nem lép életbe, és nem a steady state-et mérnénk.
#: Az mtime-ot ezért visszaállítjuk, nem várunk.
_REGI_ELTOLAS_S = 3600


#: #2555: a MÉRŐEGYSÉG POSIX-specifikus, ezért a fájl Windowson kimarad.
#:
#: A korlát egységét futásidőben kalibráljuk: megmérjük, hány
#: fájlrendszer-hívásba kerül EGY `Path.resolve()`. A számláló az
#: `os.lstat` / `stat` / `scandir` / `readlink` függvényeket csomagolja be
#: — POSIX-on a `resolve()` ezeken megy, komponensenként egy `lstat`.
#: Windowson viszont az `nt._getfinalpathname` natív hívást használja,
#: amit ez a számláló NEM lát: a kalibráció 0-t mérne.
#:
#: ⚠️ A kihagyás indoka NEM az, hogy „Windowson nem működik", hanem hogy
#: ott a fájl mind a négy állítása ÜRESEN teljesülne — a számláló egyetlen
#: feloldást sem lát, tehát „a fán kívülre nem esik hívás" magától igaz
#: lenne. Az üresen zöld őr rosszabb a pirosnál: hamis biztonság.
#:
#: A #2483 gyorsítása ettől függetlenül Windowson is hat; a mérése ott
#: külön munka (a számlálónak az `nt._getfinalpathname`-et is be kellene
#: csomagolnia) — ld. a #2555 zárószakaszát.
pytestmark = pytest.mark.skipif(
    os.name == "nt",
    reason=(
        "a korlát egységét egy `Path.resolve()` hívásszáma adja, a "
        "`resolve()` viszont Windowson az `nt._getfinalpathname`-en megy, "
        "amit ez a számláló nem lát — ott mind a négy állítás ÜRESEN "
        "teljesülne (#2555)"
    ),
)


class _Hivasszamlalo:
    """A fájlrendszer-hívások számlálója, útvonal szerint bontva.

    A `Path.resolve()` NEM `os.stat`-ot hív, hanem `os.lstat`-ot (és
    symlinknél `os.readlink`-et) — a #1667 őre ezért nem látta ezt a
    költséget."""

    FIGYELT = ("stat", "lstat", "scandir", "readlink")

    def __init__(self) -> None:
        self.osszes = 0
        self.utvonalak: list[str] = []
        self._eredeti: dict[str, object] = {}

    def __enter__(self) -> "_Hivasszamlalo":
        for nev in self.FIGYELT:
            eredeti = getattr(os, nev)
            self._eredeti[nev] = eredeti
            setattr(os, nev, self._burkol(eredeti))
        return self

    def __exit__(self, *_) -> None:
        for nev in self.FIGYELT:
            setattr(os, nev, self._eredeti[nev])

    def _burkol(self, eredeti):
        def burkolt(ut, *a, **k):
            self.osszes += 1
            try:
                self.utvonalak.append(os.fspath(ut))
            except TypeError:  # fájlleíró — nem útvonal
                self.utvonalak.append("")
            return eredeti(ut, *a, **k)

        return burkolt

    def fan_kivul(self, fa: Path) -> list[str]:
        """A `fa` részfáján KÍVÜLI útvonalak.

        A fa ŐSEI nem számítanak kívülinek: egy útvonal feloldása
        természetszerűen végigmegy a komponensein, tehát a `/tmp`-ig
        felmenő `lstat`-ok a célmappa feloldásának a részei, nem
        felesleges munka."""
        gyoker = str(fa)
        osok = {str(szulo) for szulo in [fa, *fa.parents]}
        return sorted(
            {
                ut
                for ut in self.utvonalak
                if ut and not ut.startswith(gyoker) and ut not in osok
            }
        )


def _oregits(mappa: Path) -> None:
    """A mappa és tartalma „régi" lesz, hogy a #139 védőablaka ne fogja meg."""
    for elem in sorted(mappa.rglob("*"), reverse=True):
        regi = elem.stat().st_mtime - _REGI_ELTOLAS_S
        os.utime(elem, (regi, regi))
    regi = mappa.stat().st_mtime - _REGI_ELTOLAS_S
    os.utime(mappa, (regi, regi))


def _konyvtar(alap: Path, cel_szam: int) -> tuple[Path, QSettings, list[Path]]:
    """`cel_szam` darab, az indexben MÁR SZEREPLŐ, változatlan exportcél."""
    celok = []
    for i in range(cel_szam):
        cel = alap / "kimenet" / "Picasa" / "Exports" / f"export{i}"
        cel.mkdir(parents=True)
        for j in range(3):
            make_jpeg(cel / f"IMG_{j:04d}.jpg", size=(32, 24))
        celok.append(cel)

    settings = QSettings(
        str(alap / "settings.ini"), QSettings.Format.IniFormat
    )
    settings.setValue(
        EXPORTED_FOLDERS_SETTINGS_KEY, [str(cel) for cel in celok]
    )

    db = alap / "index.db"
    with open_index(db) as conn:
        for cel in celok:
            sync_folder(conn, cel, cel, incremental=True)
    for cel in celok:
        _oregits(cel)
    # az öregítés után újra kell rögzíteni a scan-állapotot, különben az
    # eltolt mtime „változásnak" látszana
    with open_index(db) as conn:
        for cel in celok:
            sync_folder(conn, cel, cel, incremental=True)
    return db, settings, celok


def _indulasi_kor(db: Path, settings) -> _Hivasszamlalo:
    with open_index(db) as conn:
        with _Hivasszamlalo() as szamlalo:
            _ujraindexelt_exportcelok(conn, settings)
    return szamlalo


@pytest.fixture(autouse=True)
def _bemelegitett_szurok():
    """A gyári kizárólista feloldása MUNKAMENETENKÉNT egyszer jogos —
    a próba a MAPPÁNKÉNTI ismétlést méri, nem az elsőt."""
    default_name_filters()


class TestNincsFeleslegesUtvonalfeloldas:
    def test_a_probakonyvtaron_kivulre_nem_esik_fajlrendszer_hivas(self, tmp_path):
        """(1) A gyári előtagok (`~/.cache`, `/proc`, `/sys`, `/usr`, a
        Kuka) feloldása MAPPÁNKÉNT ismétlődött — ez a hívások 63%-a volt."""
        db, settings, _ = _konyvtar(tmp_path, 4)

        szamlalo = _indulasi_kor(db, settings)

        kivul = szamlalo.fan_kivul(tmp_path)
        assert not kivul, (
            "az exportcélok visszavétele a próbakönyvtáron KÍVÜL is "
            f"feloldott útvonalakat ({len(kivul)} hívás): {kivul[:8]}. "
            "Ezek a gyári kizárólista (`DEFAULT_PATH_PREFIX_FILTERS`) "
            "konstans előtagjai, amiket a `scan_folder` MINDEN mappára "
            "újra feloldott. A tulajdonos gépén egy útvonal-hívás ~47 ms "
            "(#1706), tíz exportcéllal ez önmagában másodpercek — a #2483 "
            "26 másodperces szakaszának a nagyobbik fele."
        )

    def test_exportcelonkent_legfeljebb_egy_utvonalfeloldas(self, tmp_path):
        """(2) Célonként EGY feloldás jár, nem három.

        A #2483 leletében a `sync_folder` a gyökeret és a mappát külön
        oldotta fel (holott az indulási ág ugyanazt adja át kétszer:
        `sync_folder(conn, mappa, mappa)`), a `NameFilters.is_path_excluded`
        pedig harmadszor is — ugyanarra az útvonalra.

        A korlát EGYSÉGE egy tényleges feloldás itt, ebben a
        környezetben mért ára. Így a próba nem függ a `--basetemp`
        mélységétől (abszolút küszöbnél az flakyvé tenné)."""
        db, settings, celok = _konyvtar(tmp_path, 4)

        with _Hivasszamlalo() as merce:
            celok[0].resolve()
        egy_feloldas = merce.osszes
        assert egy_feloldas >= 2, (
            "egy útvonal-feloldás nem mérhető ebben a környezetben — a "
            "korlát egysége értelmetlen lenne"
        )

        szamlalo = _indulasi_kor(db, settings)

        celonkent = szamlalo.osszes / len(celok)
        # egy feloldás + `is_dir` + `scandir` + a mappa mtime-ja + ráhagyás
        korlat = egy_feloldas + 4
        assert celonkent <= korlat, (
            f"exportcélonként {celonkent:.1f} fájlrendszer-hívás történt, a "
            f"korlát {korlat} (egy feloldás = {egy_feloldas} hívás + 4 "
            "valódi művelet). A #2483 leletében ez a szám a feloldások "
            "TÖBBSZÖRÖZŐDÉSÉBŐL jött; a tulajdonos tárolóján egy hívás "
            "~47 ms (#1706), tíz exportcéllal ez a 26 másodperces szakasz."
        )

    def test_a_sirkovek_szama_nem_szorzodik_a_celok_szamaval(self, tmp_path):
        """(2b) A `removed_folders` sírkövei (#1249) kanonikus alakban
        vannak tárolva, mégis MINDEN `sync_folder`-híváskor újra
        feloldódtak — a költség tehát sírkő × exportcél volt."""
        db, settings, _ = _konyvtar(tmp_path, 4)
        sirko_nelkul = _indulasi_kor(db, settings).osszes

        with open_index(db) as conn:
            for i in range(10):
                sirko = tmp_path / "sirko" / f"s{i}"
                sirko.mkdir(parents=True)
                conn.execute(
                    "INSERT OR IGNORE INTO removed_folders(path) VALUES (?)",
                    (str(sirko.resolve()),),
                )
            conn.commit()

        sirkovel = _indulasi_kor(db, settings).osszes

        assert sirkovel == sirko_nelkul, (
            f"tíz sírkő {sirkovel - sirko_nelkul} extra fájlrendszer-hívást "
            "okozott az exportcélok visszavételében. A sírkövek útvonala "
            "már kanonikus (`add_removed_folder` → `normalize_path`), a "
            "feloldásuk tehát tiszta veszteség — és a szorzó rossz: "
            "sírkövenként MINDEN exportcélra lefutott."
        )

    def test_a_szamlalo_nem_uresedett_ki(self, tmp_path):
        """(3) Pozitív kontroll: ugyanez a számláló egy ELSŐ indexelésen
        bizonyítottan nagy számot ad — a nulla nem a mérés hibája."""
        cel = tmp_path / "friss"
        cel.mkdir()
        for j in range(3):
            make_jpeg(cel / f"IMG_{j:04d}.jpg", size=(32, 24))

        with open_index(tmp_path / "index.db") as conn:
            with _Hivasszamlalo() as szamlalo:
                sync_folder(conn, cel, cel)

        assert szamlalo.osszes >= 4, (
            f"az első indexelés csak {szamlalo.osszes} fájlrendszer-hívást "
            "mutatott — a számláló nem azt méri, amit hiszünk, tehát a "
            "fenti korlátok sem bizonyítanak semmit"
        )
