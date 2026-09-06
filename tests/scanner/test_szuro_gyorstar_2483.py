"""#2483 ŐR: a szűrő-gyorstár és a `mar_feloldva` kapcsoló nem változtathat
azon, MELY mappa esik ki a bejárásból.

A #2483 teljesítmény-javítása két helyen nyúlt a `scanner/` sávhoz:

1. `default_name_filters()` mostantól **gyorstárazott** példányt ad
   (`_gyari_szurok`, `lru_cache`);
2. `NameFilters.is_path_excluded` / `scan_folder` kapott egy
   `mar_feloldva` kapcsolót, amely KIHAGYJA az útvonal feloldását.

A sávtérkép kikötése (`CLAUDE.md`, adatréteg/scanner): ha a `name_filters`
változása bármely fájltípus **felvételét vagy kihagyását** módosítja, az
önálló, mért állítást igényel. A gyorsítás mérőszáma (hívásszám) ezt NEM
méri — a `tests/perf/test_exportcel_utvonalfeloldas_2483.py` akkor is zöld
lenne, ha a kizárás közben teljesen elromlana. Ezek az őrök ezért a
VISELKEDÉST rögzítik, nem a költséget.

A két külön veszély, amit mérünk:

* **elavult gyorstár** — a gyári előtagok között `~` szerepel, tehát a
  feloldásuk a futásidejű `HOME`-tól függ. Egy `HOME`-független gyorstár
  a felhasználóváltás (és minden `monkeypatch.setenv("HOME", …)`-os teszt)
  után a RÉGI home `.cache`-ét zárná ki, az újét nem;
* **a kihagyott feloldás nem lehet kihagyott kizárás** — a `mar_feloldva`
  csak a `resolve()`-ot spórolja meg, az ítéletet nem.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.scanner import scan_folder
from picasapy.scanner.name_filters import (
    DEFAULT_PATH_PREFIX_FILTERS,
    NameFilters,
    default_name_filters,
)


def _kepes_mappa(mappa: Path) -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    (mappa / "IMG_0001.jpg").write_bytes(b"x" * 32)
    return mappa


class TestGyariSzuroGyorstar:
    """A gyorstár a példányt spórolja meg — nem az ítéletet."""

    def test_ugyanazt_a_peldanyt_adja_vissza(self):
        """Ez a gyorsítás lényege: a `scan_folder` mappánként hívja, és a
        példányosítás oldotta fel mind az öt gyári előtagot."""
        assert default_name_filters() is default_name_filters()

    def test_home_valtas_utan_az_UJ_home_cache_e_esik_ki(
        self, monkeypatch, tmp_path
    ):
        """A gyorstár KULCSA a `~` feloldása utáni alak.

        Ha a gyorstár a `HOME`-tól függetlenül egyetlen példányt tartana,
        ez a próba a második `HOME`-nál bukna: a `regi/.cache` maradna
        kizárva, az `uj/.cache` pedig bejárhatóként jönne vissza."""
        regi = tmp_path / "regi"
        uj = tmp_path / "uj"

        monkeypatch.setenv("HOME", str(regi))
        monkeypatch.setenv("USERPROFILE", str(regi))
        assert default_name_filters().is_path_excluded(regi / ".cache" / "t")

        monkeypatch.setenv("HOME", str(uj))
        monkeypatch.setenv("USERPROFILE", str(uj))
        szurok = default_name_filters()

        assert szurok.is_path_excluded(uj / ".cache" / "t"), (
            "a HOME megváltozott, de a gyorstár az ELŐZŐ home `.cache`-ére "
            "beállított példányt adta vissza"
        )
        assert not szurok.is_path_excluded(regi / ".cache" / "t"), (
            "a régi home `.cache`-e a HOME-váltás után is kizárt maradt — "
            "a gyorstár elavult példányt szolgál ki"
        )

    def test_a_gyari_elotagok_valojaban_kizarnak(self):
        """Pozitív kontroll: a gyorstárazott példány NEM üres.

        E nélkül a fenti „nincs kizárva" állítások úgy is teljesülnének,
        hogy a gyári lista elveszett a gyorstárazás során."""
        szurok = default_name_filters()
        assert "/usr" in DEFAULT_PATH_PREFIX_FILTERS
        assert szurok.is_path_excluded("/usr/share/kepek")
        assert szurok.is_path_excluded("/proc/1")
        assert not szurok.is_path_excluded("/usrbin/kepek")


class TestMarFeloldvaNemHagyjaKiAKizarast:
    """A kapcsoló a `resolve()`-ot hagyja ki, az ítéletet nem."""

    @pytest.mark.parametrize("mar_feloldva", [False, True])
    def test_a_kizart_elotag_alatti_ut_mindket_agon_kizart(
        self, tmp_path, mar_feloldva
    ):
        cache = (tmp_path / "home" / ".cache").resolve()
        cache.mkdir(parents=True)
        szurok = NameFilters(path_prefix_filters=(cache,))

        assert szurok.is_path_excluded(
            cache / "thumbnails", mar_feloldva
        ), "a `mar_feloldva` ág átengedte a kizárt előtag alatti útvonalat"

    @pytest.mark.parametrize("mar_feloldva", [False, True])
    def test_a_hasonlo_nevu_mappa_egyik_agon_sem_esik_ki(
        self, tmp_path, mar_feloldva
    ):
        cache = (tmp_path / "home" / ".cache").resolve()
        cache.mkdir(parents=True)
        szurok = NameFilters(path_prefix_filters=(cache,))

        assert not szurok.is_path_excluded(
            (tmp_path / "fotok" / "Cache").resolve(), mar_feloldva
        )
        assert not szurok.is_path_excluded(
            (tmp_path / "home" / ".cache-copy").resolve(), mar_feloldva
        )

    def test_a_ket_ag_itelete_azonos_feloldott_utvonalra(self, tmp_path):
        """A `mar_feloldva` szerződése: MÁR feloldott útvonalon a két ág
        ugyanazt mondja. Ez az az állítás, ami a `sync_folder` kihagyását
        egyáltalán jogossá teszi."""
        cache = (tmp_path / "home" / ".cache").resolve()
        cache.mkdir(parents=True)
        szurok = NameFilters(path_prefix_filters=(cache,))
        utak = [
            cache,
            cache / "thumbnails" / "nagy",
            (tmp_path / "fotok").resolve(),
            (tmp_path / "home" / ".cache-copy").resolve(),
            Path("/usr"),
            Path("/"),
        ]

        for ut in utak:
            assert szurok.is_path_excluded(ut, True) == szurok.is_path_excluded(
                ut, False
            ), f"a két ág mást mond erre az útvonalra: {ut}"


class TestScanFolderMarFeloldva:
    """A kapcsoló a bejáró rétegen sem módosíthatja, mi kerül az indexbe."""

    def test_a_kizart_elotag_alatti_mappa_mar_feloldva_val_is_None(
        self, tmp_path
    ):
        # ⚠️ A mappa NEM lehet pont-előtagú: a `scan_folder` a rejtett
        # mappákat már a kizárólista ELŐTT elveti, tehát egy `.cache` nevű
        # próba akkor is None-t adna, ha az útvonal-kizárás elromlott
        # (mérve: a #2483 M2 mutációja így csúszott át).
        elotag = (tmp_path / "kizart").resolve()
        mappa = _kepes_mappa(elotag / "kepek")
        szurok = NameFilters(path_prefix_filters=(elotag,))

        # pozitív kontroll: ugyanez a mappa kizárás nélkül SCANNELHETŐ
        assert scan_folder(mappa, NameFilters()) is not None

        assert scan_folder(mappa, szurok, mar_feloldva=True) is None, (
            "a `mar_feloldva=True` átengedte a kizárt előtag alatti mappát "
            "— a kapcsoló a feloldást hivatott kihagyni, nem a kizárást"
        )

    def test_ugyanazokat_a_fajlokat_adja_a_ket_ag(self, tmp_path):
        """Sávhatár-állítás: a `mar_feloldva` egyetlen fájl felvételét
        vagy kihagyását sem változtatja meg."""
        mappa = _kepes_mappa((tmp_path / "nyaralas").resolve())
        (mappa / "IMG_0002.cr2").write_bytes(b"y" * 32)
        (mappa / "jegyzet.txt").write_text("nem média", encoding="utf-8")

        alap = scan_folder(mappa)
        gyors = scan_folder(mappa, mar_feloldva=True)

        assert alap is not None and gyors is not None
        assert [(f.name, f.kind) for f in gyors.files] == [
            (f.name, f.kind) for f in alap.files
        ]
        assert gyors.path == alap.path
        assert gyors.has_ini == alap.has_ini
        # pozitív kontroll: az összevetés nem két üres listát hasonlít
        assert {f.name for f in alap.files} == {"IMG_0001.jpg", "IMG_0002.cr2"}

    def test_a_nev_alapu_kizaras_erintetlen(self, tmp_path):
        """A gyári NÉV-kizárás (`Originals`) a `mar_feloldva` ágon is él —
        az a szabály nem az útvonal-feloldáson múlik."""
        mappa = _kepes_mappa((tmp_path / "Originals").resolve())

        assert scan_folder(mappa, mar_feloldva=True) is None
