"""#1667 ŐR: az exportcélok visszavétele nem olvashatja újra a könyvtárat.

## A lelet, amit ez az őr befagyaszt

A tulajdonos tesztüzem-naplója (v0.8.128, Windows 11, saját gép) egyetlen
indulási lépést nevezett meg:

```
    8406.3 ms (77.8%)  exportcélok visszavétele (#1565)
   10809.6 ms          ÖSSZESEN (indulás → kész ablak)
      16 indexelt mappa, 421 indexelt kép
```

**Tizenhat mappa, 8,4 másodperc.** Nem méretfüggés — szerkezeti hiba volt.

## Miért került 8,4 másodpercbe

A `prune_foreign_folders` (#58) MINDEN, a figyelt gyökereken kívüli mappát
kitakarított az indexből, a `folder_scan_state`-tel és a `photos` sorokkal
együtt. Az exportcél (`<Képek>/Picasa/Exports/…`) pontosan ilyen. A
közvetlenül utána futó `_ujraindexelt_exportcelok` tehát **üres indexre**
épített vissza: a `_sync_folder` inkrementális kihagyása (#139: változatlan
fájlnál nincs EXIF-olvasás) nem tudott működni, mert nem volt mihez
hasonlítania. Minden exportált képre lefutott a `read_file_metadata` —
azaz **minden induláskor minden exportált fájl megnyílt**.

MÉRVE (RPi5, 4 exportcél / 180 kép, meleg lapgyorstár, 2026-08-27):

| | fájlnyitás (`read_file_metadata`) | idő |
|---|---:|---:|
| a javítás előtt | **180** | 44–52 ms |
| a javítással | **0** | 7–9 ms |

A Windows-többszöröző ugyanaz, amit a #1653 kimért: az indulás nem
processzor-, hanem **fájlbeolvasás-korlátos**. Egy fájlnyitás ott valós
idejű vírusvizsgálaton (és a tulajdonosnál gyakran hálózati körön) megy
át — a helyi 44 ms így lesz 8 406 ms.

## Miért DARABSZÁMOT mér ez az őr, nem időt

A #1653 lemérte: ugyanaz a szakasz, ugyanaz a commit, ugyanaz a futó
**490–3 679 ms** között szórt (7,5-szeres). Egy nem-flaky időküszöb
~10 s-nál lenne, ami egy kétszeres lassulást már nem fogna meg. A
munkamennyiség viszont determinisztikus: nincs óra, nincs terhelésfüggés.

## A három állítás

1. **munkamennyiség** — változatlan exportcélokon az indulási kör NULLA
   fájlt nyit meg és NULLA fotósort ír;
2. **elhelyezés** — a visszavétel az első kirajzolt képkocka UTÁN fut
   (`_start_and_finish`), nem a kritikus úton;
3. **a mérés nem üresedett ki** — ugyanaz a számláló egy ELSŐ indexelésen
   bizonyítottan pozitív számot ad.

A #1565 funkciója (a figyelt gyökereken kívülre exportált képek látszanak)
külön őrizve: `tests/app/test_exportcel_indexelese_1565.py`.

## Mutációs bizonyíték (2026-08-27, RPi5)

| # | mutáció | bukó őr |
|---|---|---|
| a | `_takaritas_gyokerei` csak a `roots`-ot adja vissza (a javítás visszavonva) | `…nulla_fajlnyitas_es_nulla_iras` — *„az indulás **6** exportált képfájlt nyitott meg"* + `…akkor_is_vedett_ha_epp_nem_lathato` |
| b | `_ujraindexelt_exportcelok` nem szinkronizál semmit (a #1565 elrontva) | `test_az_indexbe_meg_be_nem_kerult_exportcel_indulaskor_bekerul` (#1565) |
| c | `_ujraindexelt_exportcelok` közvetlen hívása visszakerül a kritikus útra | `test_a_nyers_ujraindexeles_sincs_a_kritikus_uton` |
| c2 | `_exportcelok_visszavetele` maga kerül a kritikus útra | `test_a_visszavetel_az_elso_kepkocka_utan_fut` |

⚠️ A (b) mutáció **első nekifutásra ÁTMENT**, és ez önmagában lelet: a
#1565 addigi őre (`test_ujraindulas_utan_is_latszik`) a #1667 óta a
takarítás-VÉDELMET méri, nem a visszavételt. A funkciónak maradt egy fele,
amit csak a visszavétel tud — az indexben még nem szereplő exportcél
felvétele —, és arra új őr készült (b sora). Egy „zöld mutáció" nem a
javítás igazolása, hanem a hiányzó állítás megnevezése.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.application import (
    _takaritas_gyokerei,
    _ujraindexelt_exportcelok,
)
from picasapy.app.exported_folders import EXPORTED_FOLDERS_SETTINGS_KEY
from picasapy.index import open_index, prune_foreign_folders, sync_folder
from picasapy.index import sync as sync_modul
from support.jpeg_factory import make_jpeg

#: Exportcél-mappa és kép/mappa a próbakönyvtárban. Kicsi, de a hibás
#: viselkedésnél is bizonyítottan pozitív számot ad (ld. a harmadik teszt).
_EXPORTCEL_SZAM = 2
_KEP_PER_EXPORTCEL = 3


class _Szamlalo:
    """Az indulási kör MUNKAMENNYISÉGE — fájlnyitás és fotósor-írás.

    Nem óra: mindkét szám determinisztikus, tehát az őr nem flaky."""

    def __init__(self) -> None:
        self.fajlnyitas = 0
        self.fotosor_iras = 0

    def figyeld_a_kapcsolatot(self, conn) -> None:
        def nyom(utasitas: str) -> None:
            elso = utasitas.strip().upper()
            if elso.startswith(("INSERT INTO PHOTOS", "UPDATE PHOTOS")):
                self.fotosor_iras += 1

        conn.set_trace_callback(nyom)


@pytest.fixture
def szamlalo(monkeypatch) -> _Szamlalo:
    """A `read_file_metadata` hívásainak számlálása a `sync` modulban.

    A modul FOGANTYÚJÁT cseréljük (`sync.read_file_metadata`), nem a
    `metadata` csomagot — így a csere pontosan azt az egy döntést mozdítja,
    amit mérni akarunk."""
    szam = _Szamlalo()
    eredeti = sync_modul.read_file_metadata

    def merve(path):
        szam.fajlnyitas += 1
        return eredeti(path)

    monkeypatch.setattr(sync_modul, "read_file_metadata", merve)
    return szam


@pytest.fixture
def konyvtar(tmp_path):
    """Figyelt gyökér + a gyökéren KÍVÜLI exportcélok, kész indexszel."""
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "IMG_0001.jpg", size=(32, 24))

    exportok = tmp_path / "Kepek" / "Picasa" / "Exports"
    celok = []
    for i in range(_EXPORTCEL_SZAM):
        cel = exportok / f"export{i}"
        cel.mkdir(parents=True)
        for j in range(_KEP_PER_EXPORTCEL):
            make_jpeg(cel / f"IMG_{j:04d}.jpg", size=(32, 24))
        celok.append(cel)

    for cel in celok:
        assert not cel.resolve().is_relative_to(gyoker.resolve()), (
            f"az exportcél ({cel}) a figyelt gyökér ALATT van — a "
            "`prune_foreign_folders` ki sem dobná, tehát az őr üresen zöld "
            "lenne (#1626)"
        )

    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    settings.setValue(
        EXPORTED_FOLDERS_SETTINGS_KEY, [str(cel) for cel in celok]
    )

    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_folder(conn, gyoker, gyoker)
        for cel in celok:
            sync_folder(conn, cel, cel)
    return db, gyoker, celok, settings


def _indulasi_kor(db: Path, gyoker: Path, settings, szamlalo: _Szamlalo):
    """EGY indulás index-munkája, a `run()` lépéseivel és sorrendjében.

    A takarítás a kritikus úton fut, a visszavétel az első képkocka után —
    de a KETTŐ EGYÜTT adja ki az indulás index-munkáját, tehát az őr
    mindkettőt egy körben méri."""
    with open_index(db) as conn:
        prune_foreign_folders(conn, _takaritas_gyokerei((str(gyoker),), settings))
        szamlalo.figyeld_a_kapcsolatot(conn)
        _ujraindexelt_exportcelok(conn, settings)
        conn.set_trace_callback(None)
        mappak = [row["path"] for row in conn.execute("SELECT path FROM folders")]
        kepek = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    return mappak, kepek


class TestAzIndulasNemOlvassaUjraAzExportcelokat:
    def test_valtozatlan_exportcelnal_nulla_fajlnyitas_es_nulla_iras(
        self, konyvtar, szamlalo
    ):
        """(1) A munkamennyiség-állítás — ez a #1667 javításának foga."""
        db, gyoker, celok, settings = konyvtar

        mappak, kepek = _indulasi_kor(db, gyoker, settings, szamlalo)

        # előfeltétel: a kör tényleg értelmes adaton futott
        assert kepek == 1 + _EXPORTCEL_SZAM * _KEP_PER_EXPORTCEL, (
            "az indulási kör után nincs meg minden kép az indexben — az őr "
            f"üres adaton mérne ({kepek} kép)"
        )

        assert szamlalo.fajlnyitas == 0, (
            f"az indulás {szamlalo.fajlnyitas} exportált képfájlt nyitott "
            f"meg, pedig egyikük sem változott. A #1667 lelete pontosan ez "
            f"volt: a `prune_foreign_folders` kidobta az exportcélok "
            f"indexsorait, a visszavétel pedig nulláról olvasta vissza az "
            f"EXIF/IPTC-t minden képről. A tulajdonos gépén ez 8 406 ms "
            f"volt — az indulás 77,8%-a. A javítás: a nyilvántartott "
            f"exportcélok VÉDETT gyökerek a takarításnál "
            f"(`_takaritas_gyokerei`)."
        )
        assert szamlalo.fotosor_iras == 0, (
            f"az indulás {szamlalo.fotosor_iras} fotósort írt változatlan "
            f"exportcélokon. Minden ilyen írás elsüti az FTS-triggert "
            f"(delete+insert), hízlalja a WAL-t és koptatja a flash-t — a "
            f"#139 óta pont ezt kerüljük a figyelt gyökereken."
        )

        for cel in celok:
            assert str(cel.resolve()) in mappak, (
                f"az exportcél ({cel}) kiesett az indexből — a gyorsítás "
                "elvitte a #1565 funkcióját"
            )

    def test_a_szamlalo_nem_uresedett_ki(self, tmp_path, szamlalo):
        """(3) Pozitív kontroll: ugyanaz a számláló ELSŐ indexelésen mér.

        A #1476/#1468 tanulsága: a nulla lehet a mérés hibája is. Ha a
        `read_file_metadata` fogantyúja elmozdulna (átnevezés, közvetlen
        import a hívás helyén), az első teszt NÉMÁN zöld maradna."""
        cel = tmp_path / "friss"
        cel.mkdir()
        for j in range(_KEP_PER_EXPORTCEL):
            make_jpeg(cel / f"IMG_{j:04d}.jpg", size=(32, 24))

        with open_index(tmp_path / "index.db") as conn:
            szamlalo.figyeld_a_kapcsolatot(conn)
            sync_folder(conn, cel, cel)
            conn.set_trace_callback(None)

        assert szamlalo.fajlnyitas == _KEP_PER_EXPORTCEL, (
            f"az ELSŐ indexelés {szamlalo.fajlnyitas} fájlt nyitott meg "
            f"{_KEP_PER_EXPORTCEL} helyett — a számláló nem azt méri, amit "
            "hiszünk, tehát a nulla-állítás sem bizonyít semmit"
        )
        assert szamlalo.fotosor_iras >= _KEP_PER_EXPORTCEL, (
            "az első indexelés nem írt fotósort — a SQL-nyomkövetés nem "
            "arra a kapcsolatra van kötve, amelyik ír"
        )


class TestAVisszavetelNincsAKritikusUton:
    """(2) Az elhelyezés-állítás.

    A #1601 a `könyvtár betöltése` lépést azért tolta a `frameSwapped`
    mögé, mert az indulási munka nem tarthatja vissza az ablakot. Az
    exportcél-karbantartásra ugyanez igaz — és a #1667 leletében pont ez a
    lépés állt az első képkocka ELŐTT, 8,4 másodpercig.

    Az őr a forrás SZERKEZETÉT nézi (`ast`), nem szöveget keres: egy
    átnevezés vagy egy sortörés nem üresíti ki."""

    @staticmethod
    def _run_fa() -> ast.FunctionDef:
        """A `run()` szintaxisfája — a MODULFÁJLBÓL kibontva.

        Az `inspect.getsource(run)` behúzott szövege önmagában nem
        elemezhető (`IndentationError`), a `cleandoc` pedig a törzs
        behúzását is elvenné. A modul egészének elemzése ettől mentes."""
        from picasapy.app import application

        modul = ast.parse(
            Path(application.__file__).read_text(encoding="utf-8")
        )
        for node in modul.body:
            if isinstance(node, ast.FunctionDef) and node.name == "run":
                return node
        raise AssertionError("nincs `run()` az application.py-ban")

    @staticmethod
    def _hivasok(csomopont, nev: str) -> list[ast.Call]:
        return [
            node
            for node in ast.walk(csomopont)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == nev
        ]

    def test_a_visszavetel_az_elso_kepkocka_utan_fut(self):
        run_fa = self._run_fa()
        elso_kepkocka_utan = [
            node
            for node in ast.walk(run_fa)
            if isinstance(node, ast.FunctionDef)
            and node.name == "_start_and_finish"
        ]
        assert elso_kepkocka_utan, (
            "a `run()`-ban nincs `_start_and_finish` — a #1601 első-képkocka "
            "utáni ága eltűnt, tehát az elhelyezés-állítás értelmezhetetlen"
        )

        osszes = self._hivasok(run_fa, "_exportcelok_visszavetele")
        halasztott = self._hivasok(elso_kepkocka_utan[0], "_exportcelok_visszavetele")

        assert osszes, (
            "a `run()` sehol nem hívja az exportcélok visszavételét — a "
            "#1565 önjavító ága elveszett"
        )
        assert len(halasztott) == len(osszes), (
            f"az exportcélok visszavétele a KRITIKUS ÚTON is fut "
            f"({len(osszes) - len(halasztott)} hívás az első kirajzolt "
            f"képkocka előtt). A #1667 lelete szerint ez a lépés a "
            f"tulajdonos gépén 8 406 ms-ig tartotta vissza az ablakot; a "
            f"helye a `_start_and_finish`-ben van, a #1601 mintájára."
        )

    def test_a_nyers_ujraindexeles_sincs_a_kritikus_uton(self):
        """A megkerülő út is zárva: a belső függvény közvetlen hívása is
        csak az első képkocka után állhat."""
        run_fa = self._run_fa()
        kozvetlen = self._hivasok(run_fa, "_ujraindexelt_exportcelok")
        assert not kozvetlen, (
            "a `run()` közvetlenül hívja a `_ujraindexelt_exportcelok`-t — "
            "az elhelyezés-őr így megkerülhető. A hívás a "
            "`_exportcelok_visszavetele`-n át menjen, ami az első képkocka "
            "után fut (#1667)."
        )

    def test_a_takaritas_a_vedett_gyokereket_kapja(self):
        """A javítás másik fele: a takarítás ki sem dobja az exportcélt."""
        run_fa = self._run_fa()
        takaritasok = self._hivasok(run_fa, "prune_foreign_folders")
        assert takaritasok, "a `run()` nem takarít induláskor (#58)"
        for hivas in takaritasok:
            argumentumok = [ast.dump(arg) for arg in hivas.args]
            assert any("_takaritas_gyokerei" in arg for arg in argumentumok), (
                "a `prune_foreign_folders` NEM a védett gyökereket kapja — "
                "minden induláskor kidobja a nyilvántartott exportcélokat, "
                "és a visszaépítés újraolvassa az összes exportált kép "
                "EXIF-jét (#1667)"
            )


class TestAVedettGyokerek:
    """A `_takaritas_gyokerei` szerződése — a hiány nem bizonyíték (#1560)."""

    def test_a_nyilvantartott_exportcel_akkor_is_vedett_ha_epp_nem_lathato(
        self, tmp_path
    ):
        """Lecsatolt NAS / leválasztott lemez: a cél nincs meg, de a képek
        igen. Ha a hiánya miatt takarítanánk, a visszatéréskor teljes
        újraolvasás következne — ez a #1560 mért kára."""
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        nincs_meg = tmp_path / "lecsatolt" / "export"
        settings.setValue(EXPORTED_FOLDERS_SETTINGS_KEY, [str(nincs_meg)])

        assert not nincs_meg.exists(), "a próba előfeltétele, hogy ne létezzen"
        gyokerek = _takaritas_gyokerei((str(tmp_path / "kepek"),), settings)

        assert str(nincs_meg) in gyokerek, (
            "a nyilvántartott, de épp nem látható exportcél kimaradt a "
            "védett gyökerekből — egy lecsatolt NAS-on tárolt exportmappa "
            "indexsorai így egyetlen indulástól elvesznének (#1560)"
        )

    def test_a_mar_nem_nyilvantartott_cel_tovabbra_is_kitakarodik(
        self, tmp_path
    ):
        """A védelem nem szivárog: ami kiesett a nyilvántartásból, megy."""
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        settings.setValue(EXPORTED_FOLDERS_SETTINGS_KEY, [])

        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        make_jpeg(gyoker / "a.jpg", size=(32, 24))
        idegen = tmp_path / "idegen"
        idegen.mkdir()
        make_jpeg(idegen / "b.jpg", size=(32, 24))

        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_folder(conn, gyoker, gyoker)
            sync_folder(conn, idegen, idegen)
            prune_foreign_folders(
                conn, _takaritas_gyokerei((str(gyoker),), settings)
            )
            mappak = [
                row["path"] for row in conn.execute("SELECT path FROM folders")
            ]

        assert str(idegen.resolve()) not in mappak, (
            "a #58 takarítás nem dobta ki az ottragadt, nem nyilvántartott "
            "mappát — a védelem túl széles lett"
        )
