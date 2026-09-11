"""A Picasa `ytResampler` Lanczos-4 magja (#871).

Az őrök három dolgot mérnek, ebben a sorrendben:

1. **a mag betű szerint** — `w(x) = sinc(πx)·sinc(πx/4)`, a
   `docs/specs/filters-decoded.md` „A Lanczos-4, betű szerint" szakasza
   szerint (`0xa3feed`);
2. **a mag SZÉLESEDIK kicsinyítéskor** — `sugár / lépték`
   (`0x00a3f745`–`0x00a3f74b`). Ez az a pont, amiben a `cv2.INTER_LANCZOS4`
   **nem** a Picasa Lanczos-a: az OpenCV fix, 8 csapos magja kicsinyítéskor
   aliasol, mert nem tágul a forrásban;
3. **túllövés** — a Lanczos negatív lebenyei kilépnek a forrás
   értéktartományából; a `cv2.INTER_AREA` soha.

A 2. pont őre azért fontos, mert egy „Lanczos-ra váltottunk" javítás a
`cv2.INTER_LANCZOS4`-gyel is zöldre menne az 1. és a 3. pontra — közben
mérhetően ROSSZABB képet adna (ld. a jegy mérési táblája).
"""

import math

import numpy as np
import pytest

from picasapy.resample import lanczos4_kicsinyites, lanczos4_suly


def _referencia_suly(x: float) -> float:
    """A spec képlete, kézzel — a modul NEM ezt hívja."""
    x = abs(x)
    if x >= 4.0:
        return 0.0
    if x == 0.0:
        return 1.0
    a = x * math.pi
    b = x * 0.25 * math.pi
    return (math.sin(a) / a) * (math.sin(b) / b)


class TestMag:
    """A súlyfüggvény alakja (`0xa3feed`)."""

    @pytest.mark.parametrize(
        "x, vart",
        [
            (0.0, 1.0),
            (0.5, 0.6203830132406946),
            (1.5, -0.16641523160350802),
            (2.5, 0.05990948337726289),
            (3.5, -0.012660877821238668),
        ],
    )
    def test_ismert_ertekek(self, x, vart):
        assert lanczos4_suly(np.array([x]))[0] == pytest.approx(vart, abs=1e-12)

    @pytest.mark.parametrize("x", [1.0, 2.0, 3.0])
    def test_egesz_helyeken_nulla(self, x):
        """A Lanczos INTERPOLÁLÓ: az egész eltolásokon pontosan 0."""
        assert lanczos4_suly(np.array([x]))[0] == pytest.approx(0.0, abs=1e-12)

    @pytest.mark.parametrize("x", [4.0, 4.5, 10.0, -4.0, -7.25])
    def test_tartosugaron_kivul_nulla(self, x):
        assert lanczos4_suly(np.array([x]))[0] == 0.0

    def test_paros_fuggveny(self):
        minta = np.linspace(-4.5, 4.5, 91)
        assert np.allclose(lanczos4_suly(minta), lanczos4_suly(-minta))

    def test_egyezik_a_spec_kepletevel(self):
        minta = np.linspace(-5.0, 5.0, 201)
        vart = np.array([_referencia_suly(float(x)) for x in minta])
        assert np.allclose(lanczos4_suly(minta), vart, atol=1e-12)


class TestAtmeretezes:
    def test_azonos_meret_valtozatlan(self):
        """1 : 1 léptéknél a Lanczos pontos másolatot ad (interpoláló mag)."""
        rng = np.random.default_rng(871)
        kep = rng.integers(0, 256, (23, 31, 3), dtype=np.uint8)
        assert np.array_equal(lanczos4_kicsinyites(kep, 31, 23), kep)

    def test_egyenletes_kep_egyenletes_marad(self):
        """A súlyok fázisonként 1-re összegződnek — konstans kép nem sodródik."""
        kep = np.full((400, 600, 3), 137, dtype=np.uint8)
        assert np.array_equal(
            lanczos4_kicsinyites(kep, 150, 100),
            np.full((100, 150, 3), 137, dtype=np.uint8),
        )

    def test_szurkearnyalatos_kepet_is_kezel(self):
        kep = np.full((200, 200), 90, dtype=np.uint8)
        eredmeny = lanczos4_kicsinyites(kep, 50, 50)
        assert eredmeny.shape == (50, 50)
        assert np.array_equal(eredmeny, np.full((50, 50), 90, dtype=np.uint8))

    def test_alak_es_tipus(self):
        rng = np.random.default_rng(2)
        kep = rng.integers(0, 256, (120, 90, 3), dtype=np.uint8)
        eredmeny = lanczos4_kicsinyites(kep, 30, 40)
        assert eredmeny.shape == (40, 30, 3)
        assert eredmeny.dtype == np.uint8

    def test_egy_kepponta_kicsinyites_is_mukodik(self):
        kep = np.full((64, 64, 3), 200, dtype=np.uint8)
        assert lanczos4_kicsinyites(kep, 1, 1).shape == (1, 1, 3)


class TestMagSzelesedik:
    """A mag szélessége `sugár / lépték` — enélkül a kicsinyítés aliasol.

    Ez az őr választja el a spec-hű magot a `cv2.INTER_LANCZOS4`-től.
    """

    @staticmethod
    def _egyetlen_vilagos_sor(oldal: int = 256) -> np.ndarray:
        """Fekete kép EGYETLEN világos sorral — az „impulzusválasz" próba."""
        kep = np.zeros((oldal, 64), dtype=np.uint8)
        kep[oldal // 2, :] = 255
        return kep

    def test_egyetlen_forrassor_tobb_celsorra_terul_szet(self):
        """8× kicsinyítésnél a mag sugara a forrásban 4·8 = 32 képpont, így
        egyetlen világos forrássor **több** célsort érint. Fix, 4-es sugarú
        maggal a hatás fél célsorra szorulna — vagyis a sor akár teljesen
        elveszne."""
        nyers = lanczos4_kicsinyites(self._egyetlen_vilagos_sor(), 8, 32, vagas=False)
        erintett = int((np.abs(nyers[:, 0]) > 0.5).sum())
        assert erintett >= 5

    def test_a_cv2_lanczos4_ugyanezt_a_sort_ELNYELI(self):
        """Kontroll: ha valaki `cv2.INTER_LANCZOS4`-re cserélné a magot, ez
        az eset megmutatja a különbséget — az OpenCV magja nem tágul a
        forrásban, ezért a sor **nyomtalanul eltűnik**. (A `INTER_AREA`
        megtartja, csak egyetlen célsorba sűrítve.)"""
        cv2 = pytest.importorskip("cv2")
        kep = self._egyetlen_vilagos_sor()
        cv_eredmeny = cv2.resize(kep, (8, 32), interpolation=cv2.INTER_LANCZOS4)
        assert cv_eredmeny.max() == 0
        area = cv2.resize(kep, (8, 32), interpolation=cv2.INTER_AREA)
        assert int((area[:, 0] > 0).sum()) == 1


class TestTullendules:
    """A Lanczos negatív lebenyei — a jegy „vizuális összevetés" pontja
    mérhető alakban."""

    @staticmethod
    def _el(szeles: int = 256) -> np.ndarray:
        kep = np.zeros((szeles, szeles, 3), dtype=np.uint8)
        kep[:, szeles // 2 :] = 255
        return kep

    def test_kontrasztos_el_mellett_tullo(self):
        eredmeny = lanczos4_kicsinyites(self._el(), 64, 64)
        # A forrásban CSAK 0 és 255 van; a Lanczos ennél sötétebbet és
        # világosabbat is rajzolna — a 8 bites vágás miatt a túllövés a
        # 0/255 határon „megáll", ezért a vágás ELŐTTI jelet nézzük.
        nyers = lanczos4_kicsinyites(self._el(), 64, 64, vagas=False)
        assert nyers.min() < -1.0
        assert nyers.max() > 256.0
        # a vágott kimenet ettől még érvényes 8 bites kép
        assert eredmeny.min() == 0 and eredmeny.max() == 255

    def test_inter_area_nem_lo_tul(self):
        """Kontroll: a mai (területi átlagoló) út elvileg sem lő túl."""
        cv2 = pytest.importorskip("cv2")
        eredmeny = cv2.resize(self._el(), (64, 64), interpolation=cv2.INTER_AREA)
        assert eredmeny.min() == 0 and eredmeny.max() == 255


class TestBekotes:
    """A Picasa magja a BÉLYEGKÉP-úton megy — és CSAK ott.

    A hatókört a MÉRÉS szabja meg, nem az elv: a #871 mércéje a Picasa
    `bigthumbs` tára (119 kép, 288 képpont), ahol a mag mindhárom
    metrikán javít ÉS gyorsabb (23 ms vs 56 ms). Nagy kimenetnél viszont
    az ára 16× (4000 × 3000 → 1600: 300 ms vs 18 ms), ezért az általános
    út — amit az export és az importálás hív — `INTER_AREA` marad.

    A #2669 köre megpróbálta a magot a 3×-os küszöb alá vinni, és **nem
    sikerült**: nyolc mért irányból a legjobb 2,0×-t hozott, a teljes út
    így is 7,9×. Az őr tehát nem „ideiglenes", hanem mért határ —
    `docs/benchmarks/2026-09-08-2669-mag-gyorsitas.md`.
    """

    def test_a_BELYEGKEP_ut_a_picasa_magjat_hasznalja(self):
        from picasapy.cvimage import scale_down_picasa_mag
        from picasapy.resample import picasa_kicsinyites

        rng = np.random.default_rng(871)
        kep = rng.integers(0, 256, (300, 400, 3), dtype=np.uint8)
        assert np.array_equal(
            scale_down_picasa_mag(kep, 100), picasa_kicsinyites(kep, 100, 75)
        )

    def test_a_belyegkep_ut_mar_nem_puszta_inter_area(self):
        """Az őr foga: ha valaki visszaállítaná az `INTER_AREA`-t, ez bukik."""
        cv2 = pytest.importorskip("cv2")
        from picasapy.cvimage import scale_down_picasa_mag

        rng = np.random.default_rng(3)
        kep = rng.integers(0, 256, (300, 400, 3), dtype=np.uint8)
        area = cv2.resize(kep, (100, 75), interpolation=cv2.INTER_AREA)
        assert not np.array_equal(scale_down_picasa_mag(kep, 100), area)

    def test_az_ALTALANOS_ut_INTER_AREA_marad(self):
        """A másik irány őre: ha valaki a `scale_down`-t is átkötné, az
        exportot 16×-ra lassítaná. A #2669 gyorsítási köre után is 7,9×
        maradna, ezért ez a próba tartja a határt."""
        cv2 = pytest.importorskip("cv2")
        from picasapy.cvimage import scale_down

        rng = np.random.default_rng(3)
        kep = rng.integers(0, 256, (300, 400, 3), dtype=np.uint8)
        assert np.array_equal(
            scale_down(kep, 100),
            cv2.resize(kep, (100, 75), interpolation=cv2.INTER_AREA),
        )

    def test_a_belyegkep_gyorsitotar_a_MAG_utat_hivja(self):
        """Forrás-szintű kapu: a bekötés két híváshelye ne csússzon vissza."""
        from pathlib import Path

        szoveg = (
            Path(__file__).resolve().parents[1]
            / "src" / "picasapy" / "thumbs" / "cache.py"
        ).read_text(encoding="utf-8")
        #: #598: HÁROM híváshely — a szűretlen bélyegkép, a szerkesztett, és
        #: a rétegzett tár SZINT-levezetése (a kis szint a nagyobbik kész
        #: bélyegképéből áll elő). Mindhárom ugyanazt a magot hívja; a kapu
        #: azt őrzi, hogy egyik se csússzon vissza az OpenCV-alapértelmezésre.
        assert szoveg.count("scale_down_picasa_mag(") == 3, (
            "a bélyegkép-gyorsítótárban nem a várt HÁROM híváshely hívja a "
            "Picasa magját (a szűretlen, a szerkesztett bélyegkép és a "
            "szint-levezetés, #598)"
        )
        assert "scale_down_picasa_mag,\n" in szoveg, "hiányzik az import"

    def test_a_muveszi_szurok_kicsinyitese_valtozatlan(self):
        """A jegy szűk hatóköre: a pixelezéshez használt doboz-átlagolás
        SZÁNDÉKOS, ahhoz nem nyúlunk (`effects_artistic`, `focal`)."""
        from pathlib import Path

        gyoker = Path(__file__).resolve().parents[1] / "src" / "picasapy" / "render"
        for nev in ("effects_artistic.py", "focal.py"):
            szoveg = (gyoker / nev).read_text(encoding="utf-8")
            assert "cv2.INTER_AREA" in szoveg, nev
            assert "picasa_kicsinyites" not in szoveg, nev


class TestGyorsFelezes:
    """A pontosan 2 : 1 lépés rögzített magja — a gyorsítás nem változtat
    a matematikán."""

    def test_a_mag_16_csapos_es_1re_osszegzodik(self):
        from picasapy.resample import felezo_mag

        mag = felezo_mag()
        assert mag.shape == (16,)
        assert float(mag.sum()) == pytest.approx(1.0, abs=1e-6)
        assert np.allclose(mag, mag[::-1], atol=1e-7)  # szimmetrikus
        assert (mag < 0).any()  # negatív lebenyek: ez Lanczos, nem doboz

    @pytest.mark.parametrize(
        "alak, cel", [((300, 400, 3), (200, 150)), ((512, 512, 3), (256, 256))]
    )
    def test_a_gyors_ut_egyezik_az_altalanossal(self, alak, cel):
        """Az elő-szűrt képen a gyors (OpenCV-s) és az általános (NumPy-s)
        út ugyanazt adja — a lebegőpontos kerekítés egy szintjén belül."""
        cv2 = pytest.importorskip("cv2")
        from picasapy.resample import lanczos4_kicsinyites, picasa_kicsinyites

        rng = np.random.default_rng(871)
        kep = rng.integers(0, 256, alak, dtype=np.uint8)
        cel_sz, cel_ma = cel
        elo = cv2.resize(kep, (2 * cel_sz, 2 * cel_ma), interpolation=cv2.INTER_AREA)
        gyors = picasa_kicsinyites(kep, cel_sz, cel_ma)
        altalanos = lanczos4_kicsinyites(elo, cel_sz, cel_ma)
        assert np.abs(gyors.astype(int) - altalanos.astype(int)).max() <= 1

    def test_enyhe_kicsinyitesnel_a_MAG_nem_fut(self):
        """2× alatti kicsinyítésnél a Picasa magja SZÁNDÉKOSAN nem fut.

        Az első változat itt a tiszta Lanczos-4 lépést adta. Mérve: a
        `bigthumbs` mérce egyetlen párja sem esik ebbe a sávba (mind
        legalább 2×), tehát nem tudjuk, melyik a hűbb — az ára viszont
        ismert: 2048 × 1536 → 1536 esetén 887 ms a 8,9 ms helyett.
        Bizonyíték nélküli, 99×-es lassítás nem mehet ki. Részletesen a
        `picasa_kicsinyites` docstringjében és a `TestAKetszeresAlattiSav`
        osztályban."""
        cv2 = pytest.importorskip("cv2")
        from picasapy.resample import lanczos4_kicsinyites, picasa_kicsinyites

        rng = np.random.default_rng(4)
        kep = rng.integers(0, 256, (200, 200, 3), dtype=np.uint8)
        kapott = picasa_kicsinyites(kep, 150, 150)
        assert np.array_equal(
            kapott, cv2.resize(kep, (150, 150), interpolation=cv2.INTER_AREA)
        )
        assert not np.array_equal(kapott, lanczos4_kicsinyites(kep, 150, 150))

    def test_egyenletes_kep_a_gyors_uton_sem_sodrodik(self):
        kep = np.full((800, 800, 3), 42, dtype=np.uint8)
        from picasapy.resample import picasa_kicsinyites

        assert np.array_equal(
            picasa_kicsinyites(kep, 100, 100), np.full((100, 100, 3), 42, dtype=np.uint8)
        )


class TestAKetszeresAlattiSav:
    """#871: a 2× alatti kicsinyítés SZÁNDÉKOSAN a régi úton marad.

    A jegy mércéje a Picasa `bigthumbs` tára (119 kép, 288 képpont) — abban
    minden pár legalább 2×-es kicsinyítés, tehát az enyhe sávra **nincs
    bizonyítékunk**, melyik a hűbb. Az ára viszont mérve van: ott nincs mit
    elő-szűrni, ezért a csapónként számoló általános út futna, 2048 × 1536
    → 1536 esetén 887 ms az `INTER_AREA` 8,9 ms-a helyett (**99×**).

    Ez az őr azt tartja, hogy a határ ne csússzon el némán: sem lefelé
    (a lassú út ne szivárogjon be az enyhe sávba), sem fölfelé (a mért,
    2× fölötti sáv ne essen vissza a régi útra).
    """

    def test_a_ketszeres_ALATT_az_INTER_AREA_fut(self):
        """Bitre azonos az `INTER_AREA`-val — tehát tényleg az fut."""
        cv2 = pytest.importorskip("cv2")
        from picasapy.resample import picasa_kicsinyites

        rng = np.random.default_rng(871)
        kep = rng.integers(0, 256, (300, 400, 3), dtype=np.uint8)
        # 400 → 300 = 1,33× — a kétszeres alatt
        kapott = picasa_kicsinyites(kep, 300, 225)
        vart = cv2.resize(kep, (300, 225), interpolation=cv2.INTER_AREA)
        assert np.array_equal(kapott, vart), (
            "a 2× alatti sáv nem az INTER_AREA-t hívja — a jegy mérése "
            "erre a sávra nem terjed ki, a lassú út pedig 99× drágább"
        )

    def test_a_ketszeres_FOLOTT_NEM_az_INTER_AREA_fut(self):
        """A mért sáv a Picasa magján megy — ha ez is `INTER_AREA` lenne,
        a jegy egész munkája elveszne, és a próba fentebb mégis zöld
        maradna."""
        cv2 = pytest.importorskip("cv2")
        from picasapy.resample import picasa_kicsinyites

        rng = np.random.default_rng(1871)
        kep = rng.integers(0, 256, (400, 600, 3), dtype=np.uint8)
        # 600 → 300 = pontosan 2× — a mért sáv alja
        kapott = picasa_kicsinyites(kep, 300, 200)
        vart = cv2.resize(kep, (300, 200), interpolation=cv2.INTER_AREA)
        assert not np.array_equal(kapott, vart), (
            "a 2× fölötti sáv is az INTER_AREA-ra esett vissza — a Picasa "
            "magja nem fut sehol"
        )

    def test_a_hatar_PONTOSAN_a_ketszeres(self):
        """A `ELO_SZURES_SZORZO` a határ; ha valaki átírja, ez szól."""
        from picasapy.resample import ELO_SZURES_SZORZO

        assert ELO_SZURES_SZORZO == 2, (
            "a 2× határhoz mérés tartozik (a bigthumbs-mérce minden párja "
            "legalább 2×); más érték új mérést igényel"
        )
