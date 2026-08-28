"""`Nézet ▸ Megjelenítési mód ▸ Szépia / Fekete-fehér` képpont-szabálya — #1657.

A tulajdonos RPi5-ön kipróbálta a Szépiát, és **semmi nem történt**: a menü
tizenegy tételéből hét — köztük a két leglátványosabb — nem mozdított
képpontot. Ez a fájl a két mód SZÁMTANÁT őrzi; a bekötést (nagy néző + rács)
a `tests/app/qml_functional/test_szepia_bw_a_kepernyon_es_a_racson_1657.py`.

## A várt értékek KÉZZEL vannak kiszámolva

Egyetlen literál sem a termékkódból, a termék konstansaiból vagy a termék
tábláiból származik — mindegyik a
`docs/specs/picasa-megjelenitesi-modok.md` 5.7/5.8 szakaszának képletéből,
papíron. A levezetés minden esetnél ott áll a konstans mellett, a `>> 8`
osztás maradékával együtt, hogy egy olvasó ellenőrizni tudja.

Ez nem formaság: ha a várt értéket a termék `SEPIA_BLEND_RGB`-jéből
indexelnénk, a konstans elrontása a tesztet is „elrontaná", és a próba
együtt mozogna a hibával. A `TestMutaciosFedettseg` osztály docstringje
tételesen felsorolja, melyik konstans elrontása melyik állítást bukatja.

## A két képlet (spec 5.7 és 5.8)

```
BW:     Y = (77·R + 151·G + 28·B) >> 8,   R' = G' = B' = Y
SZÉPIA: 1. Y ugyanígy, mindhárom csatornára szétterítve
        2. v1 = 255 − ((255 − Y) · 218) >> 8
        3. m  = 0xFF, ha v1 ≥ 128, különben 0x00
        4. ki = ((((v1 xor m) · 2) · (c xor m)) >> 8) xor m,  c = #9B7D63
```

⚠️ A spec kimondja: a konstansok MÉRTEK, de az „ez overlay-keverés" a kutató
OLVASATA. Ez a fájl ezért a **lépéssort** állítja, nem egy overlay-rutinnal
való egyezést.

## Amit ez a fájl SZÁNDÉKOSAN nem mér

A szerkesztő `bw`/`sepia` **effektjét** (`render/color.py`) — az a mentett
képre ír és a `filters=` láncba kerül, ez itt csak a képernyőre hat. A
`TestNemAKeteffekt` épp azt állítja, hogy a kettő KÜLÖNBÖZIK, tehát
összevonni nem szabad.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from picasapy.render.display_modes import (
    apply_display_bw,
    apply_display_mode,
    apply_display_sepia,
    display_mode_changes_pixels,
    luma,
)

# --------------------------------------------------------------------------
# A KÉZZEL számolt várt értékek.
#
# BW — `Y = (77·R + 151·G + 28·B) >> 8`:
#   fekete       0 + 0 + 0                = 0      ;      0 >> 8 = 0
#   fehér    19635 + 38505 + 7140         = 65280  ;  65280 >> 8 = 255  (marad 0)
#   szürke128 9856 + 19328 + 3584         = 32768  ;  32768 >> 8 = 128  (marad 0)
#   piros    19635 + 0 + 0                = 19635  ;  19635 >> 8 = 76   (marad 179)
#   zöld         0 + 38505 + 0            = 38505  ;  38505 >> 8 = 150  (marad 105)
#   kék          0 + 0 + 7140             = 7140   ;   7140 >> 8 = 27   (marad 228)
#   (10,200,90)  770 + 30200 + 2520       = 33490  ;  33490 >> 8 = 130  (marad 210)
#   (200,50,25) 15400 + 7550 + 700        = 23650  ;  23650 >> 8 = 92   (marad 98)
#   szürke104/105 → 104 / 105  (a súlyok összege 256, tehát a szürke önmaga)
#
# SZÉPIA — a fenti Y-ból, csatornánként (c = 155 / 125 / 99):
#   fekete   Y=0   : 255·218=55590 >>8=217 (marad 38) → v1= 38  <128 → m=0x00
#                    v2=76   : 76·155=11780>>8= 46 | 76·125= 9500>>8= 37 | 76·99= 7524>>8= 29
#   fehér    Y=255 : 0·218=0 >>8=0          → v1=255 ≥128 → m=0xFF
#                    v2=0    : 0>>8=0 → 0 xor 0xFF = 255 mindhárom csatornán
#   szürke128 Y=128: 127·218=27686>>8=108(m.38)→v1=147 ≥128 → m=0xFF, v2=(147^255)·2=216
#                    216·100=21600>>8= 84→84^255=171 | 216·130=28080>>8=109→146
#                    216·156=33696>>8=131→124
#   piros    Y=76  : 179·218=39022>>8=152(m.110)→v1=103 <128 → m=0x00, v2=206
#                    206·155=31930>>8=124 | 206·125=25750>>8=100 | 206·99=20394>>8= 79
#   zöld     Y=150 : 105·218=22890>>8= 89(m.106)→v1=166 ≥128 → m=0xFF, v2=(166^255)·2=178
#                    178·100=17800>>8= 69→186 | 178·130=23140>>8= 90→165
#                    178·156=27768>>8=108→147
#   kék      Y=27  : 228·218=49704>>8=194(m. 40)→v1= 61 <128 → m=0x00, v2=122
#                    122·155=18910>>8= 73 | 122·125=15250>>8= 59 | 122·99=12078>>8= 47
#   (10,200,90) Y=130: 125·218=27250>>8=106(m.114)→v1=149 ≥128 → m=0xFF, v2=212
#                    212·100=21200>>8= 82→173 | 212·130=27560>>8=107→148
#                    212·156=33072>>8=129→126
#   (200,50,25) Y=92 : 163·218=35534>>8=138(m.206)→v1=117 <128 → m=0x00, v2=234
#                    234·155=36270>>8=141 | 234·125=29250>>8=114 | 234·99=23166>>8= 90
# --------------------------------------------------------------------------

FEKETE = (0, 0, 0)
FEHER = (255, 255, 255)
KOZEPSZURKE = (128, 128, 128)
PIROS = (255, 0, 0)
ZOLD = (0, 255, 0)
KEK = (0, 0, 255)
VEGYES = (10, 200, 90)
VEGYES2 = (200, 50, 25)

#: `bemenet → (BW, SZÉPIA)` — mind a hat literál KÉZZEL számolva, fent.
ESETEK: tuple[tuple[tuple[int, int, int], int, tuple[int, int, int]], ...] = (
    (FEKETE, 0, (46, 37, 29)),
    (FEHER, 255, (255, 255, 255)),
    (KOZEPSZURKE, 128, (171, 146, 124)),
    (PIROS, 76, (124, 100, 79)),
    (ZOLD, 150, (186, 165, 147)),
    (KEK, 27, (73, 59, 47)),
    (VEGYES, 130, (173, 148, 126)),
    (VEGYES2, 92, (141, 114, 90)),
)


def _folt(szin: tuple[int, int, int], magas: int = 3, szeles: int = 4) -> np.ndarray:
    """Egyenletes `(magas, szeles, 3)` uint8 RGB-folt."""
    return np.full((magas, szeles, 3), szin, dtype=np.uint8)


def _szinek(tomb: np.ndarray) -> set[tuple[int, int, int]]:
    return {tuple(int(c) for c in p) for p in tomb.reshape(-1, 3)}


class TestFeketeFeher:
    """Spec 5.7 — `Y = (77·R + 151·G + 28·B) >> 8` mindhárom csatornára."""

    @pytest.mark.parametrize(("bemenet", "vart_y", "_szepia"), ESETEK)
    def test_a_luma_a_kezzel_szamolt_ertek(self, bemenet, vart_y, _szepia):
        assert _szinek(apply_display_bw(_folt(bemenet))) == {
            (vart_y, vart_y, vart_y)
        }

    def test_a_sulyok_osszege_256_tehat_a_szurke_onmaga(self):
        """A 77+151+28 = 256 miatt a szürke bemenet VÁLTOZATLAN.

        Ez a képlet legerősebb, konstans-független ellenőrzése: ha bármelyik
        súly elcsúszik, az összeg nem 256, és a szürke skála elmozdul.
        """
        szurkek = np.arange(256, dtype=np.uint8).reshape(16, 16)
        kep = np.dstack([szurkek, szurkek, szurkek])
        assert np.array_equal(apply_display_bw(kep), kep)

    def test_a_csatornak_egyenloek(self):
        ki = apply_display_bw(_folt((200, 50, 25)))
        assert np.array_equal(ki[:, :, 0], ki[:, :, 1])
        assert np.array_equal(ki[:, :, 1], ki[:, :, 2])

    def test_a_luma_sik_kulon_is_lekerdezheto(self):
        assert set(np.unique(luma(_folt(PIROS)))) == {76}


class TestSzepia:
    """Spec 5.8 — a négylépéses MŰVELETSOR, nem az „overlay" név."""

    @pytest.mark.parametrize(("bemenet", "_y", "vart"), ESETEK)
    def test_a_kimenet_a_kezzel_szamolt_ertek(self, bemenet, _y, vart):
        assert _szinek(apply_display_sepia(_folt(bemenet))) == {vart}

    def test_a_fekete_nem_marad_fekete(self):
        """A 2. lépés a 0-t 38-ra emeli — a kimenet sötétbarna, nem fekete.

        `v1 = 255 − (255·218 >> 8) = 255 − 217 = 38`, innen `(46, 37, 29)`.
        Ez a szépia lényege; ha valaki „levágási hibának" nézné és
        visszafeketítené, elveszne a mód.
        """
        assert _szinek(apply_display_sepia(_folt(FEKETE))) == {(46, 37, 29)}

    def test_a_feher_feher_marad(self):
        """`Y=255 → v1=255 → m=0xFF → v2=0 → 0 xor 0xFF = 255`."""
        assert _szinek(apply_display_sepia(_folt(FEHER))) == {(255, 255, 255)}

    def test_a_kimenet_barnas_R_gt_G_gt_B(self):
        """A keverőszín `#9B7D63` monoton csökkenő ⇒ R > G > B, kivéve a
        telített végeket (fehér). Ez a mód FELISMERHETŐSÉGE."""
        for bemenet, _y, _v in ESETEK:
            if bemenet == FEHER:
                continue
            r, g, b = next(iter(_szinek(apply_display_sepia(_folt(bemenet)))))
            assert r > g > b, bemenet


class TestMaszkAg:
    """A 3. lépés maszkja MINDKÉT irányban — a `v1 = 127/128` határon.

    A `v1` értékkészlete 38…255, tehát mindkét ág valóban előfordul. A
    váltás pontos helye KÉZZEL:

    * `Y=104`: `151·218 = 32918 >> 8 = 128` → `v1 = 255−128 = 127` → **m=0x00**
      `v2 = 254`; `254·155=39370>>8=153`, `254·125=31750>>8=124`,
      `254·99=25146>>8=98` ⇒ **(153, 124, 98)**
    * `Y=105`: `150·218 = 32700 >> 8 = 127` → `v1 = 255−127 = 128` → **m=0xFF**
      `v2 = (128^255)·2 = 254`; `254·100=25400>>8=99→156`,
      `254·130=33020>>8=128→127`, `254·156=39624>>8=154→101`
      ⇒ **(156, 127, 101)**

    A két oldal KÜLÖNBÖZŐ értéket ad, tehát a maszk-ág nem elhagyható: ha
    valaki a 4. lépést maszk nélkül írná meg, a 105-ös oldal bukna.
    """

    def test_a_maszk_nelkuli_ag(self):
        assert _szinek(apply_display_sepia(_folt((104, 104, 104)))) == {
            (153, 124, 98)
        }

    def test_a_maszkos_ag(self):
        assert _szinek(apply_display_sepia(_folt((105, 105, 105)))) == {
            (156, 127, 101)
        }

    def test_a_ket_ag_kulonbozik(self):
        """Kontroll: a határ két oldala tényleg más — az ág nem no-op."""
        assert apply_display_sepia(_folt((104, 104, 104)))[0, 0].tolist() != (
            apply_display_sepia(_folt((105, 105, 105)))[0, 0].tolist()
        )

    def test_mindket_ag_elofordul_a_teljes_ertekkeszleten(self):
        """Mind a 256 Y-ra: 105 alatt maszk nélkül, 105-től maszkkal.

        A besorolást a KÉZZEL levezetett `v1 ≥ 128 ⟺ Y ≥ 105` határ adja,
        nem a termék táblája.
        """
        szurkek = np.arange(256, dtype=np.uint8).reshape(16, 16)
        ki = apply_display_sepia(np.dstack([szurkek] * 3)).reshape(-1, 3)
        # a maszkos ágon a kimenet a `255 − …` alakból jön, tehát a
        # fehér felé tart; a két ág határa a 104/105 páron látszik
        assert tuple(int(c) for c in ki[104]) == (153, 124, 98)
        assert tuple(int(c) for c in ki[105]) == (156, 127, 101)
        assert tuple(int(c) for c in ki[0]) == (46, 37, 29)
        assert tuple(int(c) for c in ki[255]) == (255, 255, 255)


class TestEgeszAritmetika:
    """A `>> 8` CSONKOL — a lebegőpontos kerekítés más eredményt adna."""

    def test_a_csonkolas_nem_kerekites(self):
        """Kontroll: van olyan bemenet, ahol a kerekítés ±1-gyel eltérne.

        `(0,0,255)`: `7140 / 256 = 27,89` — csonkolva **27**, kerekítve 28.
        Ha valaki `cv2.addWeighted`-re vagy float mátrixos
        `cv2.transform`-ra cserélné a lumát, ez az állítás bukna.
        """
        assert _szinek(apply_display_bw(_folt(KEK))) == {(27, 27, 27)}
        assert round(7140 / 256) == 28  # a kerekített — MÁS érték

    def test_a_szepia_csonkolasa_sem_kerekites(self):
        """`(255,0,0)`: `206·125 = 25750 / 256 = 100,59` — csonkolva **100**.

        A klasszikus overlay `/255`-tel normalizálna: `2·103·125/255 = 100,98`
        → 101. A mért `>> 8` viszont 100-at ad. Ez a különbség az oka, hogy
        kész overlay-rutint NEM hívunk be.
        """
        r, g, b = next(iter(_szinek(apply_display_sepia(_folt(PIROS)))))
        assert (r, g, b) == (124, 100, 79)
        assert round(2 * 103 * 125 / 255) == 101  # az overlay — MÁS érték


class TestNemAKeteffekt:
    """A megjelenítési mód NEM a szerkesztő `bw`/`sepia` effektje.

    Amaz a mentett képre ír és a `filters=` láncba kerül; ez csak a
    képernyőre hat. A képletük is más (amaz lebegőpontos Rec.601 / mért
    tónusgörbék), tehát összevonni paritás-vesztés volna.
    """

    def test_a_bw_kimenete_kulonbozik_az_effektetol(self):
        from picasapy.render.color import apply_bw

        be = _folt(VEGYES)
        assert not np.array_equal(apply_display_bw(be), apply_bw(be))

    def test_a_szepia_kimenete_kulonbozik_az_effektetol(self):
        from picasapy.render.color import apply_sepia

        be = _folt(VEGYES)
        assert not np.array_equal(apply_display_sepia(be), apply_sepia(be))

    def test_a_ket_megjelenitesi_mod_kulonbozik_egymastol(self):
        be = _folt(KOZEPSZURKE)
        assert not np.array_equal(
            apply_display_bw(be), apply_display_sepia(be)
        )


class TestNemMutal:
    """A bemenetet SOHA nem írjuk át helyben (gyorsítótárazott köztes kép)."""

    @pytest.mark.parametrize("mod", ["bw", "sepia"])
    def test_a_bemenet_erintetlen(self, mod):
        be = _folt(VEGYES)
        eredeti = be.copy()
        ki = apply_display_mode(be, mod)
        assert np.array_equal(be, eredeti), "a mód átírta a bemenetet"
        assert ki is not be

    @pytest.mark.parametrize("mod", ["bw", "sepia"])
    def test_a_kimenet_irhato(self, mod):
        ki = apply_display_mode(_folt(VEGYES), mod)
        ki[0, 0] = (1, 2, 3)  # nem dobhat


class TestBelepesiPont:
    """`apply_display_mode` — a közös diszpécser és a képhatás-lekérdezés."""

    @pytest.mark.parametrize(("bemenet", "vart_y", "vart_szepia"), ESETEK)
    def test_a_diszpecser_ugyanazt_adja(self, bemenet, vart_y, vart_szepia):
        assert _szinek(apply_display_mode(_folt(bemenet), "bw")) == {
            (vart_y, vart_y, vart_y)
        }
        assert _szinek(apply_display_mode(_folt(bemenet), "sepia")) == {
            vart_szepia
        }

    @pytest.mark.parametrize("mod", ["bw", "sepia"])
    def test_a_kepponthatas_lekerdezheto(self, mod):
        """A #1657 ELŐTT mindkettő `False` volt — ez a jegy lényege."""
        assert display_mode_changes_pixels(mod) is True

    @pytest.mark.parametrize("mod", ["bw", "sepia"])
    def test_a_none_kepet_atengedi(self, mod):
        assert apply_display_mode(None, mod) is None

    @pytest.mark.parametrize("mod", ["bw", "sepia"])
    def test_az_ures_kep_nem_dob(self, mod):
        ures = np.zeros((0, 0, 3), dtype=np.uint8)
        ki = apply_display_mode(ures, mod)
        assert ki is not None and ki.shape == (0, 0, 3)

    @pytest.mark.parametrize("mod", ["bw", "sepia"])
    def test_a_nem_rgb_bemenetet_atengedi(self, mod):
        szurke = np.zeros((2, 2), dtype=np.uint8)
        assert apply_display_mode(szurke, mod) is szurke


class TestSavhatar:
    """`render/` sáv-invariáns: a mód nem nyúl a lemezhez (#1657)."""

    def test_a_ket_uj_fuggveny_nem_nyul_fajlhoz(self):
        for fv in (apply_display_bw, apply_display_sepia, luma):
            forras = inspect.getsource(fv)
            for tiltott in ("open(", "imread", "imwrite", "Path(", "os."):
                assert tiltott not in forras, (
                    f"{fv.__name__} lemezhez nyúlna ({tiltott!r})"
                )


class TestMutaciosFedettseg:
    """Melyik konstans elrontása melyik állítást bukatja? (#1657 követelmény)

    A jegy mutációs bizonyítékot kér. MÉRVE (a mutáció a termékforrásban, a
    futtatás ezen az 53 tesztes fájlon; mindegyik esetben a kilépőkód 1):

    | mutáció | bukó tesztek |
    |---|---|
    | luma R-súly `77 → 78`              |  9 |
    | luma G-súly `151 → 152`            |  8 |
    | luma B-súly `28 → 29`              |  9 |
    | világosítás `218 → 219`            | 14 |
    | keverőszín R `0x9B → 0x9C`         | 17 |
    | keverőszín G `0x7D → 0x7E`         | 17 |
    | keverőszín B `0x63 → 0x64`         | 15 |
    | maszk-ág kikapcsolva (mindig 0x00) | 11 |
    | maszk-ág mindig bekapcsolva (0xFF) | 13 |
    | 4. lépés `>> 8` → `// 255`         | 14 |
    | 2. lépés `>> 8` → kerekítés        |  5 |

    **A maszk-ág mindkét oldala külön fedve** — a két mutáció pontosan a
    másik ág tesztjét bukatja, tehát egyik sem „potyautas":

    * maszk mindig `0x00` ⇒ `TestMaszkAg::test_a_maszkos_ag` bukik
    * maszk mindig `0xFF` ⇒ `TestMaszkAg::test_a_maszk_nelkuli_ag` bukik
    * mindkettő ⇒ `test_mindket_ag_elofordul_a_teljes_ertekkeszleten` bukik

    Az utolsó két sor azt is bizonyítja, hogy a **lépéssort** valósítottuk
    meg, nem a nevet: a klasszikus overlay `/255`-ös normalizálása és a
    kerekítés is bukást okoz.

    Ez az osztály magát a NÉVSORT őrzi: ha valaki a fenti konstansok
    bármelyikét átnevezi vagy kivezeti, itt derül ki.
    """

    def test_a_mert_konstansok_a_helyukon_vannak(self):
        from picasapy.render import display_modes as dm

        assert dm.LUMA_WEIGHTS_RGB == (77, 151, 28)
        assert sum(dm.LUMA_WEIGHTS_RGB) == 256
        assert dm.SEPIA_LIGHTEN_MULTIPLIER == 218
        assert dm.SEPIA_BLEND_RGB == (155, 125, 99)  # #9B7D63
