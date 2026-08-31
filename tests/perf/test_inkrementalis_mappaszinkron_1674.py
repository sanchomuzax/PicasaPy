"""#1674 ŐR: változatlan mappán a `sync_folder` ne statoljon minden fájlt.

## A maradék, amit a #1667 nem vitt el

A #1667 megszüntette, hogy az exportcélok minden induláskor
ÚJRAINDEXELŐDJENEK (180 fájlnyitás → 0). A `sync_folder` viszont
**továbbra is `scandir` + `stat`-olt minden fájlt**, akkor is, ha egyik sem
változott — mert a watcher-ág (`scan_folder`) `skip=None`-nal hívta a
scannert, tehát a #139 inkrementális kihagyása ott nem tudott működni.

Helyben ez 7–12 ms, de **hálózati exportcélon vagy nagy mappán valódi
költség**: minden `stat` egy külön kör a hálózaton.

## Miért DARABSZÁMOT mér

A #1653 mérése szerint ugyanaz a szakasz 490–3 679 ms között szórt
(7,5-szeres). Az időküszöb használhatatlan; a `stat`-hívások száma viszont
determinisztikus.

## A három állítás

1. **munkamennyiség** — változatlan mappán a fájlonkénti `stat` NULLA;
2. **a funkció nem sérül** — új és módosult fájl továbbra is bekerül;
3. **a mérés nem üresedett ki** — inkrementális mód NÉLKÜL ugyanez a
   számláló bizonyítottan pozitív.
"""

from __future__ import annotations

import os

import pytest

from picasapy.index import open_index, sync_folder
from picasapy.scanner import walker as walker_modul
from support.jpeg_factory import make_jpeg

#: Fájlok száma a próbamappában — a hibás viselkedésnél ennyi `stat` fut.
_FAJL_SZAM = 5


class _StatSzamlalo:
    """A FÁJLONKÉNTI munka mérője.

    A `DirEntry.stat` nem cserélhető (írásvédett attribútum), ezért nem azt
    csomagoljuk be, hanem a scanner EREDMÉNYÉT nézzük: a `_scan_folder` a
    média-hurokban **fájlonként pontosan egyszer** statol
    (`by_name[name].stat()`), és minden ilyen fájl bekerül a `files`
    mezőbe. A visszaadott `files` hossza tehát a fájlonkénti `stat`-ok
    száma — kihagyott mappánál a függvény a hurok ELŐTT tér vissza, üres
    `files`-szal."""

    def __init__(self) -> None:
        self.hivasok = 0
        self.kihagyva = 0


@pytest.fixture
def stat_szamlalo(monkeypatch) -> _StatSzamlalo:
    szam = _StatSzamlalo()
    eredeti = walker_modul._scan_folder

    def merve(*args, **kwargs):
        scan = eredeti(*args, **kwargs)
        if scan is not None:
            szam.hivasok += len(scan.files)
            if scan.skipped:
                szam.kihagyva += 1
        return scan

    monkeypatch.setattr(walker_modul, "_scan_folder", merve)
    return szam


@pytest.fixture
def mappa(tmp_path):
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    for i in range(_FAJL_SZAM):
        make_jpeg(gyoker / f"IMG_{i:04d}.jpg", size=(32, 24))
    # a #139 védőablaka: a friss mtime-ú mappát SOHA nem hagyjuk ki, hogy
    # egy épp íródó mappa ne ragadjon be. A próbához ezért öregítjük.
    regi = 1_600_000_000
    for p in [*gyoker.iterdir(), gyoker]:
        os.utime(p, (regi, regi))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_folder(conn, gyoker, gyoker)
    return db, gyoker


class TestValtozatlanMappa:
    def test_nulla_fajlonkenti_stat(self, mappa, stat_szamlalo):
        """(1) A munkamennyiség-állítás — ez a #1674 javításának foga."""
        db, gyoker = mappa
        with open_index(db) as conn:
            sync_folder(conn, gyoker, gyoker, incremental=True)

        assert stat_szamlalo.hivasok == 0, (
            f"a változatlan mappa {stat_szamlalo.hivasok} fájlonkénti "
            "`stat`-ot futtatott — a #139 kihagyása nem hatott a "
            "watcher-ágon (#1674)"
        )

    def test_a_meres_nem_uresedett_ki(self, mappa, stat_szamlalo):
        """(3) Pozitív kontroll: inkrementális mód NÉLKÜL pozitív a szám."""
        db, gyoker = mappa
        with open_index(db) as conn:
            sync_folder(conn, gyoker, gyoker)

        assert stat_szamlalo.hivasok >= _FAJL_SZAM, (
            f"a nem-inkrementális kör is csak {stat_szamlalo.hivasok} "
            "`stat`-ot futtatott — a számláló nem azt méri, amit hiszünk"
        )


class TestAFunkcioNemSerul:
    def test_uj_fajl_bekerul(self, mappa, stat_szamlalo):
        """(2) A kihagyás nem tehet vakká: új fájlnál a mappa mtime-ja
        változik, tehát a kihagyás feltétele megszűnik."""
        db, gyoker = mappa
        make_jpeg(gyoker / "UJ.jpg", size=(32, 24))

        with open_index(db) as conn:
            sync_folder(conn, gyoker, gyoker, incremental=True)
            nevek = {
                row["name"]
                for row in conn.execute("SELECT name FROM photos")
            }

        assert "UJ.jpg" in nevek, (
            "az új fájl nem került be az inkrementális szinkronnal (#1674)"
        )

    def test_modosult_fajl_frissul(self, mappa, stat_szamlalo):
        """A fájl tartalmának változása a MAPPA mtime-ját nem mindig
        módosítja — a kihagyás akkor is jogos: a #139 szerződése a
        mappa- és ini-mtime, nem a fájlonkénti tartalom. Ezt kimondjuk,
        hogy a következő olvasó ne higgye erősebbnek az őrt."""
        db, gyoker = mappa
        ini = gyoker / ".picasa.ini"
        ini.write_text("[IMG_0000.jpg]\nstar=yes\n", encoding="utf-8")

        with open_index(db) as conn:
            sync_folder(conn, gyoker, gyoker, incremental=True)

        assert stat_szamlalo.hivasok >= _FAJL_SZAM, (
            "az ini megjelenése után is kihagyta a mappát — az ini-mtime "
            "a kihagyás egyik feltétele (#139)"
        )
