"""#1654: tartós „tesztüzem" — a mag tesztjei.

A jegy azt a hiányt tölti be, amit sem a #211 (Teljesítmény-monitor: csak
MENETKÖZBEN kapcsolható), sem a #1601 (`PICASAPY_STARTUP_TIMELINE=1`:
környezeti változó, a tulajdonos nem fejlesztő) nem tud: az **indulás**
mérését a felhasználó gépén, egy kattintással.

Ez a fájl a Qt-mentes magot méri (`picasapy.perf.tesztuzem`). A vezérlő és
a menü tesztjei külön fájlban élnek.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import pytest

from picasapy.perf.tesztuzem import (
    MEGOSZTAS_LINUX,
    MEGOSZTAS_WINDOWS,
    NAPLO_ALMAPPA,
    TESZTUZEM_BEALLITAS_KULCS,
    TESZTUZEM_KAPCSOLO,
    KonyvtarMeret,
    argv_kapcsolo_nelkul,
    argv_tesztuzem,
    ertek_igaz,
    irj_indulasi_naplot,
    konyvtar_merete,
    legutobbi_indulasi_naplo,
    megosztas_elerheto,
    megosztas_gyokere,
    naplo_atadasa,
    naplo_celmappa,
    naplo_fajlneve,
    naplo_szovege,
    utvonalmentes,
)


class TestKapcsoloErtekek:
    """A tartós beállítás értékének értelmezése.

    A `QSettings` az INI-formátumban SZTRINGET ad vissza (`"true"`), a
    natív tárolóból viszont `bool`-t — mindkettőt ugyanúgy kell érteni,
    különben a mód platformfüggően „elfelejtődik"."""

    @pytest.mark.parametrize(
        "ertek", [True, "1", "true", "TRUE", "igen", "yes", "on", "be"]
    )
    def test_igaz_ertekek(self, ertek):
        assert ertek_igaz(ertek) is True

    @pytest.mark.parametrize(
        "ertek", [None, False, "", "0", "false", "nem", "off", "  ", "izé"]
    )
    def test_hamis_ertekek(self, ertek):
        assert ertek_igaz(ertek) is False


class TestParancssoriKapcsolo:
    """`--tesztuzem` — a #1654 második pontja."""

    def test_a_kapcsolo_neve(self):
        assert TESZTUZEM_KAPCSOLO == "--tesztuzem"

    def test_felismeri_a_kapcsolot(self):
        assert argv_tesztuzem(["picasapy", "--tesztuzem"]) is True

    def test_kapcsolo_nelkul_hamis(self):
        assert argv_tesztuzem(["picasapy", "/valahol/kepek"]) is False

    def test_a_kapcsolot_LEVALASZTJA_az_argumentumokbol(self):
        """⚠️ Ez nem kozmetika: a `_resolve_usort`-hoz hasonlóan az
        `application._resolve_roots` MINDEN `argv[1:]` elemet figyelt
        gyökérnek vesz. Ha a kapcsoló bennmarad, a program egy
        `--tesztuzem` nevű mappát próbál indexelni."""
        assert argv_kapcsolo_nelkul(["picasapy", "--tesztuzem", "/kepek"]) == [
            "picasapy",
            "/kepek",
        ]

    def test_az_eredeti_lista_valtozatlan_marad(self):
        """Immutabilitás: a hívó listáját nem írjuk át a lába alatt."""
        eredeti = ["picasapy", "--tesztuzem", "/kepek"]
        argv_kapcsolo_nelkul(eredeti)
        assert eredeti == ["picasapy", "--tesztuzem", "/kepek"]

    def test_tobbszoros_elofordulas_is_eltunik(self):
        assert argv_kapcsolo_nelkul(
            ["picasapy", "--tesztuzem", "/a", "--tesztuzem"]
        ) == ["picasapy", "/a"]


class TestKonyvtarMeret:
    """A #1653 fő gyanúja a MÉRETFÜGGÉS — a naplónak tudnia kell a méretet.

    ⚠️ Adatvédelem: a függvény szignatúrája maga a garancia — csak
    SZÁMOKAT fogad. Nevet vagy útvonalat átadni sem lehet neki."""

    def test_ures_konyvtar(self):
        assert konyvtar_merete([]) == KonyvtarMeret(mappak=0, kepek=0)

    def test_mappak_es_kepek_darabszama(self):
        assert konyvtar_merete([12, 0, 340, 7]) == KonyvtarMeret(
            mappak=4, kepek=359
        )

    def test_generatorbol_is_szamol(self):
        assert konyvtar_merete(n for n in (5, 5)) == KonyvtarMeret(2, 10)


class TestUtvonalMentesites:
    """⚠️ A #211 adatvédelmi szabálya érvényben marad: a napló NEM
    tartalmazhat teljes elérési utat, fájlnevet, felhasználónevet.

    Ez a szűrő az UTOLSÓ védvonal — nem az egyetlen: a napló mezői eleve
    rögzített szövegek és számok. De egy jövőbeli, futásidejű szöveget
    bejelentő szakaszcímke enélkül némán kiszivárogtatná a mappaszerkezetet."""

    def test_unixos_utvonal_eltunik(self):
        eredmeny = utvonalmentes("szakasz: /home/valaki-neve/Képek/nyar.jpg")
        assert "valaki-neve" not in eredmeny
        assert "/home" not in eredmeny
        assert "nyar.jpg" not in eredmeny

    def test_szokozos_utvonal_MINDEN_darabja_eltunik(self):
        """A szóköz nem menedék: a „Nyaralás 2019" mappanév két tokenre
        esik, és a naiv, egy-token-egy-út szűrő a másodikat bennhagyná."""
        eredmeny = utvonalmentes(
            "/home/valaki-neve/Képek/Nyaralás 2019/IMG_1234.jpg"
        )
        for darab in ("valaki-neve", "Nyaralás", "2019/IMG_1234.jpg", "IMG_1234"):
            assert darab not in eredmeny, darab

    def test_windowsos_utvonal_eltunik(self):
        eredmeny = utvonalmentes(r"C:\Users\Sancho\Képek\IMG_1.jpg")
        assert "Sancho" not in eredmeny
        assert "C:" not in eredmeny

    def test_unc_utvonal_eltunik(self):
        eredmeny = utvonalmentes(r"\\192.168.50.187\lemez\fotok")
        assert "192.168.50.187" not in eredmeny

    def test_puszta_fajlnev_is_eltunik(self):
        assert "IMG_1234.jpg" not in utvonalmentes("a képnél: IMG_1234.jpg")

    def test_a_valodi_jelentes_sorai_ERINTETLENEK(self):
        """A szűrőnek foga van, de nem harap bele a hasznos tartalomba.

        ⚠️ Ha ez elbukik, a napló olvashatatlanná válik — a `.txt`
        szándékosan NINCS a kiszűrt kiterjesztések közt, mert egy valódi
        szakaszcímke említi (`WatchedFolders.txt`)."""
        sorok = [
            "PicasaPy — indulási idővonal (#1601)",
            "verzió: v0.8.127 (81.3706d78)",
            "rendszer: Linux-6.18-aarch64 · Python 3.12.4 · Qt 6.7.2",
            "mérés kezdete: 2026-08-27T20:41:00+00:00",
            "    2470.1  Python- és PySide6-modulok betöltése",
            "     120.4  figyelt gyökerek beolvasása (WatchedFolders.txt)",
            "    5180.0  ÖSSZESEN (indulás → kész ablak)",
            "     1910.0 ms (36.9%)  QML betöltése (Main.qml)",
        ]
        szoveg = "\n".join(sorok)
        assert utvonalmentes(szoveg) == szoveg


class TestNaploSzovege:
    """A #1654 harmadik pontja: idővonal + fejléc + könyvtárméret."""

    @staticmethod
    def _fejlec() -> dict:
        return {
            "app_version": "v0.8.127 (81.3706d78)",
            "platform": "Linux-6.18-aarch64",
            "python_version": "3.12.4",
            "qt_version": "6.7.2",
            "started_at": "2026-08-27T20:41:00+00:00",
        }

    def test_tartalmazza_a_fejlecet(self):
        szoveg = naplo_szovege(
            idovonal_jelentes="   100.0  valami\n",
            fejlec=self._fejlec(),
            meret=KonyvtarMeret(3, 40),
        )
        assert "v0.8.127" in szoveg
        assert "Linux-6.18-aarch64" in szoveg
        assert "3.12.4" in szoveg
        assert "6.7.2" in szoveg

    def test_tartalmazza_az_idovonalat(self):
        szoveg = naplo_szovege(
            idovonal_jelentes="   100.0  QML betöltése (Main.qml)\n",
            fejlec=self._fejlec(),
            meret=KonyvtarMeret(3, 40),
        )
        assert "QML betöltése (Main.qml)" in szoveg

    def test_tartalmazza_a_konyvtar_MERETET(self):
        szoveg = naplo_szovege(
            idovonal_jelentes="",
            fejlec=self._fejlec(),
            meret=KonyvtarMeret(mappak=812, kepek=54321),
        )
        assert "812" in szoveg
        assert "54321" in szoveg

    def test_a_kimenet_UTVONALMENTES(self):
        """⚠️ Az adatvédelmi őr — ez a jegy DoD-ja.

        Beszédes útvonalakat adunk be MINDEN csatornán (szakaszcímke és
        fejléc), és egyik darabjuk sem jelenhet meg a kimenetben."""
        szoveg = naplo_szovege(
            idovonal_jelentes=(
                "   100.0  beolvasás: /home/valaki-neve/Képek/Nyaralás 2019\n"
                "   200.0  kép: IMG_1234.jpg\n"
                "   300.0  hálózat: \\\\192.168.50.187\\lemez\\fotok\n"
            ),
            fejlec={
                **self._fejlec(),
                "app_version": "v1 C:\\Users\\Sancho\\PicasaPy",
            },
            meret=KonyvtarMeret(3, 40),
        )
        for tiltott in (
            "valaki-neve",
            "Nyaralás",
            "IMG_1234",
            "192.168.50.187",
            "Sancho",
            "/home",
        ):
            assert tiltott not in szoveg, tiltott


class TestMegosztas:
    """A napló a NAS közös mappájába kerül — se feltöltés, se hitelesítés."""

    def test_linuxon_a_csatolasi_pont(self):
        assert megosztas_gyokere("linux") == Path(MEGOSZTAS_LINUX)

    def test_windowson_az_UNC_utvonal(self):
        assert megosztas_gyokere("win32") == Path(MEGOSZTAS_WINDOWS)

    def test_a_celmappa_a_rogzitett_almappa(self):
        assert naplo_celmappa(Path("/mnt/nas")) == Path("/mnt/nas") / NAPLO_ALMAPPA

    def test_a_fajlnev_idobelyeges(self):
        nev = naplo_fajlneve(datetime(2026, 8, 27, 20, 41, 5))
        assert nev == "picasapy-indulas-20260827-204105.txt"

    def test_nem_csatolt_konyvtar_NEM_elerheto(self, tmp_path):
        """⚠️ A `/mnt/nas` Linuxon akkor is LÉTEZŐ, üres könyvtár, ha a NAS
        nincs felcsatolva. Csatolás-ellenőrzés nélkül a napló némán a helyi
        lemezre kerülne, a felhasználó pedig azt hinné, hogy átadta."""
        assert megosztas_elerheto(tmp_path, ismount=lambda _p: False) is False

    def test_csatolt_konyvtar_elerheto(self, tmp_path):
        assert megosztas_elerheto(tmp_path, ismount=lambda _p: True) is True

    def test_nemletezo_gyoker_nem_elerheto(self, tmp_path):
        assert (
            megosztas_elerheto(tmp_path / "nincs", ismount=lambda _p: True) is False
        )

    def test_unc_utvonalnal_a_letezes_a_merce(self, tmp_path):
        """UNC-útvonalon nincs mit „csatolni" — az `ismount` mindig hamis
        volna, és a windowsos átadás soha nem indulna el."""
        assert (
            megosztas_elerheto(tmp_path, ismount=lambda _p: False, unc=True) is True
        )


class TestNaploAtadasa:
    """Egykattintásos átadás — fájlmásolás, semmi hálózati feltöltés."""

    def test_a_naplo_a_celmappaba_kerul(self, tmp_path):
        forras = tmp_path / "indulas-1.txt"
        forras.write_text("idővonal", encoding="utf-8")
        cel = tmp_path / "nas" / NAPLO_ALMAPPA

        eredmeny = naplo_atadasa(
            forras=forras, celmappa=cel, most=datetime(2026, 8, 27, 20, 41, 5)
        )

        assert eredmeny == cel / "picasapy-indulas-20260827-204105.txt"
        assert eredmeny.read_text(encoding="utf-8") == "idővonal"

    def test_elerhetetlen_cel_OSError_t_dob(self, tmp_path):
        """A hívó (vezérlő) EBBŐL tudja, hogy a „Mentés másként…" tartalék
        kell — a néma sikertelenség a legrosszabb kimenet."""
        akadaly = tmp_path / "akadaly"
        akadaly.write_text("nem mappa", encoding="utf-8")
        with pytest.raises(OSError):
            naplo_atadasa(
                forras=tmp_path / "nincs.txt",
                celmappa=akadaly / NAPLO_ALMAPPA,
                most=datetime(2026, 8, 27, 20, 41, 5),
            )


class TestLegutobbiNaplo:
    """Az „elküldés" a LEGUTÓBBI indulási naplót viszi."""

    def test_ures_mappanal_nincs(self, tmp_path):
        assert legutobbi_indulasi_naplo(tmp_path) is None

    def test_nemletezo_mappanal_nincs(self, tmp_path):
        assert legutobbi_indulasi_naplo(tmp_path / "nincs") is None

    def test_a_legfrissebbet_adja(self, tmp_path):
        for stamp in ("20260826-101010", "20260827-204105", "20260101-000000"):
            (tmp_path / f"indulas-{stamp}.txt").write_text(stamp, encoding="utf-8")
        (tmp_path / "perf-20991231-235959.jsonl").write_text("x", encoding="utf-8")

        legutobbi = legutobbi_indulasi_naplo(tmp_path)

        assert legutobbi is not None
        assert legutobbi.name == "indulas-20260827-204105.txt"


class TestIrjIndulasiNaplot:
    def test_letrehozza_a_mappat_es_kiirja(self, tmp_path):
        cel = tmp_path / "cache" / "perf"
        ut = irj_indulasi_naplot(
            "tartalom", cel, most=datetime(2026, 8, 27, 20, 41, 5)
        )
        assert ut == cel / "indulas-20260827-204105.txt"
        assert ut.read_text(encoding="utf-8") == "tartalom"

    def test_irasi_hiba_eseten_None(self, tmp_path):
        """Egy diagnosztika SOHA nem akadályozhatja az indulást."""
        akadaly = tmp_path / "akadaly"
        akadaly.write_text("nem mappa", encoding="utf-8")
        assert irj_indulasi_naplot("tartalom", akadaly / "perf") is None


class TestKikapcsolvaKoltsegmentes:
    """A #1601 mérése: 0,2 µs/hívás kikapcsolva. Ez nem romolhat el."""

    def test_a_beallitas_kulcsa_rogzitett(self):
        assert TESZTUZEM_BEALLITAS_KULCS == "diagnostics/tesztuzem"

    def test_a_kikapcsolt_dontes_koltsege_elhanyagolhato(self):
        """A tesztüzem eldöntése kikapcsolva sem nyúlhat lemezhez.

        Az `ertek_igaz` az egyetlen dolog, ami MINDEN indításkor lefut,
        akkor is, ha a mód ki van kapcsolva."""
        ismetles = 20_000
        started = time.perf_counter()
        for _ in range(ismetles):
            ertek_igaz("false")
        per_hivas_us = (time.perf_counter() - started) / ismetles * 1_000_000
        assert per_hivas_us < 20.0
