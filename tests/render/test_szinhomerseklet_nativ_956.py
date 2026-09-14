"""A finetune2 színhőmérséklete a NATÍV úton számol — a #956 őre.

## Mi változott

A csúszka nálunk eddig **csatornánkénti konstans szorzás** volt
(`_TEMPERATURE_GAINS`). A binárisban viszont (`0x0090e9d0`, 54 bájt) ez áll:

```asm
fmul  [0xcf47e0]                ; × 37,0
fadd  [0xcf4610]                ; + 55,0
fistp [esp+0xc]                 ; i
mov   eax, [eax*4 + 0xc7cf98]   ; k = FEKETETEST_TÁBLA[i]
call  0x90eda0                  ; ← az autocolor MÁTRIX-alkalmazója (#759)
```

⇒ a művelet **3×3-as mátrix**, nem csatornánkénti szorzás. A kereszt-tag a
hívás szerkezetéből következik, nem statisztikai lelet — egy csatornánkénti
modell **szerkezetileg** nem tudja előállítani.

## ⛔ ÖNHELYESBÍTÉS: a kerekítés NEM csonkolás

A jegy és a spec is `i = (int)(temp·37 + 55)`-öt, azaz **nulla felé
csonkolást** ír. A diszasszemblált törzsben viszont **nincs**
vezérlőszó-állítás (`fnstcw` / `or 0xc00`), tehát az `fistp` az x87
alapértelmezett módjában fut: **a legközelebbi egészre, döntetlennél a
párosra**.

A spec SAJÁT index-táblája is ezt igazolja — a csonkolás két állásban mást
adna:

| temp | `temp·37 + 55` | csonkolva | legközelebbi | a spec szerint |
|---:|---:|---:|---:|---:|
| +0,5 | 73,5 | 73 | **74** | **74** |
| +0,8 | 84,6 | 84 | **85** | **85** |

A `test_a_kerekites_a_LEGKOZELEBBI_egeszre_megy` ezt kikötésbe teszi, hogy a
„csonkolás" mondat ne szivárogjon vissza.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.tone import (
    FEKETETEST_TABLA,
    _TEMPERATURE_GAINS,
    apply_color_temperature,
    feketetest_index,
    feketetest_szin,
)

#: A spec `filters-decoded.md` mért index-táblája: (temp, index, k).
MERT_ALLASOK = (
    (-1.0, 18, (255, 173, 94)),
    (-0.8, 25, (255, 196, 137)),
    (-0.5, 36, (255, 221, 190)),
    (0.0, 55, (255, 249, 253)),
    (0.5, 74, (221, 230, 255)),
    (0.8, 85, (208, 222, 255)),
    (1.0, 92, (202, 218, 255)),
)


class TestAzIndexkepletES_aTabla:
    @pytest.mark.parametrize("temp,index,_k", MERT_ALLASOK)
    def test_az_index_a_mert_ertek(self, temp: float, index: int, _k) -> None:
        assert feketetest_index(temp) == index

    @pytest.mark.parametrize("temp,_index,k", MERT_ALLASOK)
    def test_a_tabla_bejegyzese_a_binarisbol_valo(self, temp: float, _index, k) -> None:
        assert feketetest_szin(temp) == k

    def test_a_kerekites_a_LEGKOZELEBBI_egeszre_megy(self) -> None:
        """⛔ Csonkolással a +0,5 és a +0,8 állás MÁS indexre esne.

        A natív törzsben nincs vezérlőszó-állítás, tehát az `fistp` a
        legközelebbi egészre kerekít — a spec mért index-táblája is ezt
        adja. Ha valaki „javításnak" szánva csonkolásra írja át, ez bukik."""
        assert feketetest_index(0.5) == 74, "csonkolva 73 lenne"
        assert feketetest_index(0.8) == 85, "csonkolva 84 lenne"

    def test_a_tabla_a_csuszka_TELJES_tartomanyat_fedi(self) -> None:
        """A csúszka [−1, 1] tartománya a 18…92 indexeket címzi."""
        assert feketetest_index(-1.0) in FEKETETEST_TABLA
        assert feketetest_index(1.0) in FEKETETEST_TABLA
        assert set(FEKETETEST_TABLA) >= {i for _t, i, _k in MERT_ALLASOK}

    def test_a_tartomanyon_kivuli_ertek_a_vegpontra_esik(self) -> None:
        assert feketetest_index(-3.0) == feketetest_index(-1.0)
        assert feketetest_index(7.5) == feketetest_index(1.0)


class TestAMuveletMATRIX:
    """A kereszt-tag a hívás szerkezetéből jön — ezt csatornánkénti modell
    nem tudja előállítani."""

    def test_a_tiszta_ZOLD_kepponton_a_voros_es_a_kek_is_mozdul(self) -> None:
        """Csatornánkénti szorzással a tiszta zöldből SOHA nem lesz vörös
        vagy kék összetevő — a mátrixnál viszont lesz (mérve: a hideg végen
        `(0, 200, 0)` → `(3, 207, 27)`)."""
        kep = np.zeros((1, 1, 3), dtype=np.uint8)
        kep[0, 0] = (0, 200, 0)
        ki = apply_color_temperature(kep, -1.0)
        assert ki[0, 0, 0] > 0 and ki[0, 0, 2] > 0, (
            f"a tiszta zöldből nem lett vörös/kék összetevő ({tuple(ki[0, 0])}) "
            "— a művelet csatornánkénti maradt, nem mátrix"
        )

    @pytest.mark.parametrize(
        "temp,arany",
        [(-1.0, 0.1176), (0.0, 0.0063), (1.0, 0.0323)],
        ids=["hideg", "kozep", "meleg"],
    )
    def test_az_atlon_kivuli_arany_a_SPEC_szerinti(self, temp: float, arany: float) -> None:
        """A spec `filters-decoded.md` mért `max|átlón kívül| / átló` értékei.

        Ez köti a megvalósítást a visszafejtett mátrixhoz: ha a tábla vagy a
        mátrix-építő elcsúszik, ez a szám azonnal elmozdul."""
        from picasapy.render.autocolor_matrix import autocolor_matrix_16_16

        m = autocolor_matrix_16_16(*feketetest_szin(temp)) / 65536.0
        atlo = np.abs(np.diag(m)).max()
        kivul = np.abs(m - np.diag(np.diag(m))).max()
        assert abs(kivul / atlo - arany) < 0.0005

    def test_a_tabla_NULLA_bejegyzese_nem_semleges(self) -> None:
        """Az 55. bejegyzés (255, 249, 253) — a TÁBLÁRA igaz, hogy nem
        semleges. Hogy ebből mi következik a kimenetre, az a következő
        próba."""
        assert feketetest_szin(0.0) == (255, 249, 253)

    def test_a_temp_NULLA_AZONOSSAG_mert_a_HIVO_kapuz(self) -> None:
        """⛔ **A jegy kikötése ezen a ponton MEGDŐLT.**

        A jegy külön tesztet kért arra, hogy `temp = 0` NEM azonosság — a
        tábla 55. bejegyzése alapján. A bejegyzésről ez igaz, **de a stádium
        el sem indul nullánál**: a hívó (`0x008f7ee0`) összehasonlít
        nullával, és egyezéskor átugorja a hőmérséklet-ágat
        (`0x008f7fe6 jnp 0x8f8062`); a `0x90e9d0` csak a nem nulla ágon
        hívódik. A hívóhelyeket indextől független pásztázás adta (kettő:
        `0x8f8010`, `0x8f8051`; kontroll a `0x90eda0` kilenc hívója).

        ⚠️ Ez nem szőrszálhasogatás: kapu nélkül **minden** semleges
        `finetune2`-es kép némán elszíneződne — a nulla állás mátrixa mérve
        `(128,128,128)` → `(126,129,126)`, ami sík szürkén látszik."""
        kep = np.full((4, 4, 3), 180, dtype=np.uint8)
        assert np.array_equal(apply_color_temperature(kep, 0.0), kep)

    def test_a_nulla_koruli_allasok_viszont_MOZDITANAK(self) -> None:
        """A kapu PONTOSAN a nullára szól — a szomszédos állások dolgoznak,
        tehát nem egy széles holtsáv került be."""
        kep = np.full((4, 4, 3), 180, dtype=np.uint8)
        for temp in (-0.05, 0.05):
            assert not np.array_equal(apply_color_temperature(kep, temp), kep)

    def test_a_hideg_veg_erosebb_a_melegnel(self) -> None:
        """A mért trend: a kereszt-tag a hideg végen a legnagyobb."""
        kep = np.full((4, 4, 3), 128, dtype=np.uint8)
        hideg = apply_color_temperature(kep, -1.0).astype(int)
        meleg = apply_color_temperature(kep, 1.0).astype(int)
        alap = kep.astype(int)
        assert np.abs(hideg - alap).mean() > np.abs(meleg - alap).mean()

    def test_a_kimenet_alakja_es_tipusa_valtozatlan(self) -> None:
        kep = np.random.default_rng(0).integers(0, 256, (7, 5, 3), dtype=np.uint8)
        ki = apply_color_temperature(kep, -0.4)
        assert ki.shape == kep.shape and ki.dtype == np.uint8


class TestAGpuKozelites:
    """A `_TEMPERATURE_GAINS` MARAD — a GPU-előnézet egyetlen uniformot kap."""

    def test_a_kozelito_tabla_megvan(self) -> None:
        assert len(_TEMPERATURE_GAINS) == 7

    def test_a_kod_KIMONDJA_hogy_kozelites(self) -> None:
        """A komment sem hazudhat: a tábla mellett ott kell állnia, hogy ez
        közelítés, és hol a pontos út."""
        from picasapy.render import tone

        forras = tone.__file__.replace(".pyc", ".py")
        with open(forras, encoding="utf-8") as f:
            szoveg = f.read()
        kezdet = szoveg.index("_TEMPERATURE_GAINS")
        fej = szoveg[max(0, kezdet - 2000) : kezdet]
        assert "közelítés" in fej or "KÖZELÍTÉS" in fej
        assert "GPU" in fej
