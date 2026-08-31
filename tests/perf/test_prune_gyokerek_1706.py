"""#1706 ŐR: a `prune_foreign_folders` védett gyökereinek FELOLDÁSA.

## A lelet, amit ez az őr befagyaszt

A tulajdonos harmadik indulási naplója (v0.8.133 → v0.8.134) az „ottragadt
mappák takarítása (#58)" szakaszt **125 ms → 969 ms**-ra (7,8×) mérte,
miközben az indexelt mappák száma 16 → 18 (+2), a képeké változatlan.

MÉRVE (#1706, ez a gép, helyi lemez): a `prune_foreign_folders` két
egymástól FÜGGETLEN munkarészből áll —

1. **a védett gyökerek FELOLDÁSA** (`normalize_path`, `Path.resolve()`) —
   MINDEN gyökérre (figyelt mappa + nyilvántartott exportcél) lefut, és
   rendszerhívást (`stat`/`lstat`) igényel minden útvonal-komponensre.
   Helyi lemezen 21 gyökér feloldása **83** ilyen hívást igényelt (~4/gyökér);
2. **az összevetés** (`_is_under`, tiszta Python `Path.is_relative_to`) —
   ugyanazon a gépen **mikroszekundumos** akkor is, ha a `folders` tábla
   több száz sort tartalmaz (ld. `test_az_osszevetes_nem_no_aranytalanul`).

A 16 → 18 indexelt mappa (a `folders` tábla mérete) tehát ÖNMAGÁBAN nem
magyarázza a 7,8×-es növekedést — a #1697 (Duplikátumok/Duplikátumok
beágyazódás) különben is a FIGYELT GYÖKÉR ALATT keletkezik, tehát a prune-t
és az exportcél-visszavételt (#1565) egyáltalán nem érinti (ld.
`test_a_figyelt_gyoker_alatti_uj_mappa_nem_erinti_a_vedett_gyokerlistat`
lent). A domináns tényező a NYILVÁNTARTOTT EXPORTCÉLOK LISTÁJÁNAK MÉRETE
(`MAX_EXPORTED_FOLDERS = 20`), ami a `_takaritas_gyokerei`-n át kerül a
prune-ba, és amelynek mérete FÜGGETLEN az „indexelt mappák" számától (egy
nyilvántartott, de a lemezen nem létező exportcél is védett gyökér —
#1560).

## Amit ez az őr javít

A `_resolved_protected_roots` (#1706) kihagyja a PONTOSAN EGYEZŐ nyers
útvonal ismételt feloldását — biztonságosan: ugyanaz a string ugyanarra a
feloldott útra vezet, tehát a kihagyás a végeredményt nem változtatja.

## Amit ez az őr NEM állít

Nem állítja, hogy ez megoldja a tulajdonos teljes 7,8×-es növekedését — a
pontos ok (mennyi EGYEDI exportcél van nyilvántartva a gépén) a mi
oldalunkról nem mérhető. A jelentés (#1706) ezt konkrét, önállóan
megvalósítható jegyekként adja tovább.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.application import _takaritas_gyokerei
from picasapy.app.exported_folders import EXPORTED_FOLDERS_SETTINGS_KEY
from picasapy.index import open_index, prune_foreign_folders, sync_folder, sync_tree
from picasapy.index import sync as sync_modul
from support.jpeg_factory import make_jpeg


class _FeloldasSzamlalo:
    """Hányszor hívódott a `normalize_path` a `sync` modulból — ez a
    munkamennyiség-mérce, nem az idő (a #1653/#1667 tanulsága szerint az
    időküszöb terhelés alatt flaky)."""

    def __init__(self) -> None:
        self.hivasok = 0
        self.kapott_utvonalak: list[str] = []


@pytest.fixture
def feloldas_szamlalo(monkeypatch) -> _FeloldasSzamlalo:
    szamlalo = _FeloldasSzamlalo()
    eredeti = sync_modul.normalize_path

    def merve(path):
        szamlalo.hivasok += 1
        szamlalo.kapott_utvonalak.append(str(path))
        return eredeti(path)

    monkeypatch.setattr(sync_modul, "normalize_path", merve)
    return szamlalo


@pytest.fixture
def konyvtar(tmp_path):
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "IMG_0001.jpg", size=(32, 24))

    export_root = tmp_path / "exportcelok"
    cel = export_root / "export000"
    cel.mkdir(parents=True)
    make_jpeg(cel / "IMG_0001.jpg", size=(32, 24))

    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
        sync_folder(conn, cel, cel)
    return db, gyoker, cel


class TestAGyokerFeloldasNemIsmetliMagat:
    """(1) A munkamennyiség-állítás — a #1706 javításának foga."""

    def test_pontosan_egyezo_nyilvantartott_exportcel_csak_egyszer_oldodik_fel(
        self, konyvtar, feloldas_szamlalo
    ):
        db, gyoker, cel = konyvtar
        # ⚠️ Valós helyzet: a nyilvántartás korábbi hibából (vagy két
        # munkamenetből) ugyanazt a célt többször is tartalmazhatja — a
        # `remember_exported_folder` csak az ÚJ beszúrásnál dedupol, egy
        # meglévő, sérült beállításban a duplikátum megmaradhat.
        settings = QSettings(
            str(cel.parent.parent / "settings.ini"), QSettings.Format.IniFormat
        )
        settings.setValue(
            EXPORTED_FOLDERS_SETTINGS_KEY, [str(cel)] * 5,
        )
        gyokerek = _takaritas_gyokerei((str(gyoker),), settings)
        # #1675: +1 a Kollázsok mappa, ami azóta szintén VÉDETT gyökér
        assert len(gyokerek) == 7, (
            "az előfeltétel sérült: 1 figyelt gyökér + 5x ugyanaz az "
            "exportcél + a Kollázsok mappa kell a nyers listában"
        )

        with open_index(db) as conn:
            prune_foreign_folders(conn, gyokerek)

        # #1675: 2 → 3 — a Kollázsok mappa azóta szintén védett gyökér,
        # tehát egy további EGYEDI útvonal oldódik fel
        assert feloldas_szamlalo.hivasok == 3, (
            f"a `normalize_path` {feloldas_szamlalo.hivasok}-szor futott le "
            "6 nyers gyökérre, pedig ezek közül csak 2 EGYEDI útvonal van "
            "(a figyelt gyökér + az exportcél). Minden fölösleges hívás "
            "fájlrendszer-szintű `stat`/`lstat`-ot jelent — hálózati "
            "megosztáson (a tulajdonos NAS-on tartja a könyvtárát) ez a "
            "költség dominál (#1706)."
        )

    def test_a_vedelem_ismetelt_gyokerrel_is_mukodik(
        self, konyvtar, feloldas_szamlalo
    ):
        """A dedup nem gyengítheti a #1667 védelmét."""
        db, gyoker, cel = konyvtar
        settings = QSettings(
            str(cel.parent.parent / "settings.ini"), QSettings.Format.IniFormat
        )
        settings.setValue(EXPORTED_FOLDERS_SETTINGS_KEY, [str(cel)] * 3)
        gyokerek = _takaritas_gyokerei((str(gyoker),), settings)

        with open_index(db) as conn:
            prune_foreign_folders(conn, gyokerek)
            maradt = [
                row["path"] for row in conn.execute("SELECT path FROM folders")
            ]

        assert str(cel.resolve()) in maradt, (
            "az ismételt nyilvántartású exportcél kiesett az indexből — a "
            "dedup elrontotta a #1667 védelmét"
        )

    def test_a_szamlalo_nem_uresedett_ki(self, konyvtar, feloldas_szamlalo):
        """Pozitív kontroll: EGYEDI gyökereknél nincs dedup, mindegyik
        feloldódik — a fenti nulla-nem-csökkenés nem mérési hiba."""
        db, gyoker, cel = konyvtar
        masik_cel = cel.parent / "export001"
        masik_cel.mkdir()
        make_jpeg(masik_cel / "IMG_0001.jpg", size=(32, 24))
        with open_index(db) as conn:
            sync_folder(conn, masik_cel, masik_cel)

        settings = QSettings(
            str(cel.parent.parent / "settings.ini"), QSettings.Format.IniFormat
        )
        settings.setValue(
            EXPORTED_FOLDERS_SETTINGS_KEY, [str(cel), str(masik_cel)]
        )
        gyokerek = _takaritas_gyokerei((str(gyoker),), settings)
        # #1675: +1 a Kollázsok mappa (azóta védett gyökér)
        assert len(gyokerek) == 4, (
            "1 figyelt gyökér + 2 KÜLÖNBÖZŐ exportcél + a Kollázsok mappa"
        )

        # a builder (`sync_folder`) fenti hívása is a mért fogantyún megy —
        # a MÉRÉST innentől nullázzuk, hogy csak a `prune` alatti feloldást
        # lássuk
        feloldas_szamlalo.hivasok = 0
        with open_index(db) as conn:
            prune_foreign_folders(conn, gyokerek)

        assert feloldas_szamlalo.hivasok == 4, (
            f"4 EGYEDI gyökérre {feloldas_szamlalo.hivasok} feloldás futott "
            "— a számláló nem azt méri, amit hiszünk, tehát a fenti "
            "dedup-állítás sem bizonyít semmit"
        )


class TestAzOsszevetesOlcso:
    """(2) A #1706 gyanúja szerint az ÖSSZEVETÉS (nem a feloldás) is
    költséges lehet nagy `folders` táblán — ez az őr ezt méri és cáfolja:
    a tiszta Python összevetés a gyökerek számának NÖVELÉSE mellett sem
    igényel fájlrendszer-hívást."""

    def test_az_osszevetes_nem_hivja_ujra_a_feloldast_mappankent(
        self, konyvtar, feloldas_szamlalo
    ):
        db, gyoker, cel = konyvtar
        # 50 további, egymástól KÜLÖNBÖZŐ almappa a figyelt gyökér alatt —
        # ez a `folders` tábla méretét növeli, a védett gyökerek számát nem.
        with open_index(db) as conn:
            for i in range(50):
                almappa = gyoker / f"alszekcio{i:03d}"
                almappa.mkdir()
                make_jpeg(almappa / "a.jpg", size=(16, 16))
            sync_tree(conn, gyoker)

        settings = QSettings(
            str(cel.parent.parent / "settings.ini"), QSettings.Format.IniFormat
        )
        settings.setValue(EXPORTED_FOLDERS_SETTINGS_KEY, [str(cel)])
        gyokerek = _takaritas_gyokerei((str(gyoker),), settings)

        # a fenti `sync_tree` építő hívása is a mért fogantyún megy — a
        # MÉRÉST innentől nullázzuk, hogy csak a `prune` alatti feloldást
        # lássuk
        feloldas_szamlalo.hivasok = 0
        with open_index(db) as conn:
            folder_count = conn.execute(
                "SELECT COUNT(*) FROM folders"
            ).fetchone()[0]
            prune_foreign_folders(conn, gyokerek)

        assert folder_count >= 51, (
            "az előfeltétel sérült: a `folders` táblának ~50 sort kellett "
            "volna tartalmaznia a prune előtt"
        )
        # A feloldás csak a 2 VÉDETT GYÖKÉRRE fut (figyelt gyökér +
        # exportcél) — a folders tábla 50+ sora nem okoz további feloldást,
        # mert az összevetés (`_is_under`) tiszta Python, nem hív
        # `normalize_path`-ot mappánként.
        # #1675: 2 → 3 — a Kollázsok mappa azóta szintén védett gyökér,
        # tehát egy további EGYEDI útvonal oldódik fel
        assert feloldas_szamlalo.hivasok == 3, (
            f"a `normalize_path` {feloldas_szamlalo.hivasok}-szor futott le "
            f"{folder_count} indexelt mappa mellett, pedig csak 3 védett "
            "gyökér van — az összevetésnek A GYÖKEREK SZÁMÁVAL kellene "
            "skáláznia, NEM a mappák számával (#1706 2. gyanúja)"
        )


class TestAKetUjMappaNemErintiAVedettGyokerlistat:
    """(3) A #1706 1. gyanúja: a két új mappa (feltehetően a #1697
    Duplikátumok/Duplikátumok) a FIGYELT GYÖKÉR ALATT keletkezik — ez a
    teszt megmutatja, hogy egy ilyen új almappa nem növeli a védett
    gyökerek listáját, tehát nem hat sem a feloldásra, sem az
    exportcélok visszavételére."""

    def test_a_figyelt_gyoker_alatti_uj_mappa_nem_novel_vedett_gyokeret(
        self, konyvtar
    ):
        db, gyoker, cel = konyvtar
        settings = QSettings(
            str(cel.parent.parent / "settings.ini"), QSettings.Format.IniFormat
        )
        settings.setValue(EXPORTED_FOLDERS_SETTINGS_KEY, [str(cel)])

        elotte = _takaritas_gyokerei((str(gyoker),), settings)

        # a #1697 mintája: a figyelt gyökér ALATT jön létre egymásba
        # ágyazott „Duplikátumok" mappapár
        dup = gyoker / "Duplikátumok"
        dup.mkdir()
        make_jpeg(dup / "a.jpg", size=(16, 16))
        dup_dup = dup / "Duplikátumok"
        dup_dup.mkdir()
        make_jpeg(dup_dup / "a.jpg", size=(16, 16))
        with open_index(db) as conn:
            sync_tree(conn, gyoker)
            mappaszam = conn.execute(
                "SELECT COUNT(*) FROM folders"
            ).fetchone()[0]

        utana = _takaritas_gyokerei((str(gyoker),), settings)

        assert mappaszam >= 3, (
            "az előfeltétel sérült: a Duplikátumok/Duplikátumok párnak meg "
            "kellett volna jelennie az indexelt mappák közt"
        )
        assert utana == elotte, (
            "a figyelt gyökér alatt keletkezett új mappa megváltoztatta a "
            "VÉDETT GYÖKEREK listáját — pedig ez a lista csak a figyelt "
            "mappáktól és a nyilvántartott exportcéloktól függ, egy "
            "közönséges almappától nem (#1706 1. gyanújának cáfolata)"
        )
