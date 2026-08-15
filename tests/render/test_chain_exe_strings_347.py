"""#347: az exe-string-bányászat (`docs/specs/picasa-exe-strings.md`) által
azonosított, de a spec addig nem dokumentált `filters=` nevek a láncban.

FONTOS: ezek golden-méréssel MÉG NEM kalibráltak (nincs mögöttük vizuális
modell) — a lánc csak FELISMERI őket, a "nem renderelhető" összesített
jelentésbe (a `apply_filters` `skipped` visszatérési értéke) számítanak, de
nem futtatunk rájuk kitalált implementációt (MEMORY 2026-07-30, őszinteség-
szabály). A `picnik=1;` ez alól kivétel: az nem effekt, hanem boolean
jelző-token (mint a már ismert `redeye=1;`/`retouch=1;`), ezért érvényes
no-op-ként nyelődik el — nem kerül a kihagyott-listába.

A #347 lezáró auditja (2026-08-06) szerint a hét eredeti név közül HAT
mostanra rendezett: `glow` (v1) golden-mérve, `RoundedEdges`/`Matte`/
`NightVision` a #381 filterdesc-csővezetéken renderel, `picnik` no-op
jelzőként nyelődik el, és `grain` (v1) is renderel (ld. lent,
`TestGrainV1NowRendered`) — ez a `filterdesc-registry.md` szerint a
`grain2`-vel MEGEGYEZŐ, paraméter nélküli "Film Grain" oneclick család régi
tagja, ezért a már golden-mért `grain2`-modellt (`apply_grain`) használja
KÖZELÍTÉSKÉNT (a `grain` v1-re önmagára nincs külön golden-mérés). A hetedik,
`radtint` a #565-ben rendeződött: a natív regisztráció, a feldolgozó mag és a
maszk-LUT visszafejtésével megvan a csővezeték (radiális szorzó-tint, köbös
smoothstep maszk) — ld. `TestRadtintNowRendered` lent. Ezzel a #347 mind a
hét neve renderel.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import KNOWN_UNRENDERED_OPS, apply_filters

#: A #347 mind a hét neve renderel: `roundededges`/`matte`/`nightvision` az
#: #381-ben, `grain` (v1) és `picnik` a lezáró auditban (2026-08-06),
#: `radtint` a #565-ben. A regiszter viszont NEM ürült ki — a #382-es
#: filterdesc-nevek még benne állnak, azokon marad a szerződés (felismerés +
#: jelentés vizuális modell nélkül).
#: #687: a `triple` (és a `shadow`) is renderel — a még modell nélküli
#: nevek a `colorfix`, a `rainbow`, a `blur` és a `whitept`.
_STILL_UNRENDERED_KEYS = ("blur", "colorfix", "rainbow")


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(11)
    return rng.integers(30, 220, size=(48, 64, 3), dtype=np.uint8)


class TestKnownUnrenderedRegistry:
    def test_uj_nevek_mind_a_regiszterben_vannak(self):
        for key in _STILL_UNRENDERED_KEYS:
            assert key in KNOWN_UNRENDERED_OPS

    @pytest.mark.parametrize("key", _STILL_UNRENDERED_KEYS)
    def test_lanc_felismeri_de_nem_renderel_es_jelenti(self, key, sample):
        # a lánc nem dob kivételt, a kép változatlan marad (nincs vizuális
        # modell), de a nevet a kihagyott-listában jelenti — nem csendben
        # tűnik el
        result, skipped = apply_filters(sample, parse_filters(f"{key}=1;"))
        assert np.array_equal(result, sample)
        assert key in [name.casefold() for name in skipped]

    def test_vegyes_lanc_a_tobbi_effekt_azert_lefut(self, sample):
        # egy ismert (renderelt) effekt + egy felismert-de-renderelhetetlen
        # egy láncban: az ismert effekt hasson, a másik csak jelentve legyen
        result, skipped = apply_filters(
            sample, parse_filters("Invert=1;rainbow=1;")
        )
        assert not np.array_equal(result, sample), "az Invert lefutott"
        assert skipped == ("rainbow",)


class TestGlimmerNowRendered:
    """#381: a `roundededges`/`matte`/`nightvision` a `filterdesc.xml` egzakt
    csővezetékét kapta — már NEM a `KNOWN_UNRENDERED_OPS` tagjai, a lánc
    ténylegesen renderel rájuk (nem csak felismeri és kihagyja).
    """

    @pytest.mark.parametrize(
        ("spelled", "key"), [("RoundedEdges", "roundededges"), ("Matte", "matte"), ("NightVision", "nightvision")]
    )
    def test_mar_nem_a_kihagyott_regiszterben(self, spelled, key):
        assert key not in KNOWN_UNRENDERED_OPS

    @pytest.mark.parametrize(
        ("spelled", "key"), [("RoundedEdges", "roundededges"), ("Matte", "matte"), ("NightVision", "nightvision")]
    )
    def test_a_lanc_tenylegesen_renderel(self, spelled, key, sample):
        del key
        result, skipped = apply_filters(sample, parse_filters(f"{spelled}=1;"))
        assert skipped == (), f"{spelled}: a lánc még mindig kihagyja"
        assert not np.array_equal(result, sample)


class TestPicnikNoopMarker:
    def test_picnik_onmagaban_nem_valtoztat_es_nem_jelentett(self, sample):
        result, skipped = apply_filters(sample, parse_filters("picnik=1;"))
        assert np.array_equal(result, sample)
        assert skipped == ()

    def test_picnik_masik_effekt_mellett_sem_jelentett(self, sample):
        result, skipped = apply_filters(
            sample, parse_filters("Invert=1;picnik=1;")
        )
        assert not np.array_equal(result, sample)
        assert skipped == ()

    def test_picnik_nem_allitja_meg_a_lancot(self, sample):
        # a picnik jelző + egy hibás bejegyzés + egy jó effekt együtt
        result, skipped = apply_filters(
            sample, parse_filters("picnik=1;Boost=1,zzz;Invert=1;")
        )
        assert not np.array_equal(result, sample)
        assert skipped == ("Boost",)

    def test_uj_es_ismeretlen_egyszerre_a_kihagyott_listaban(self, sample):
        # egy teljesen ismeretlen (soha nem dokumentált) név és egy #347-es
        # felismert-de-renderelhetetlen név is a kihagyott-listába kerül —
        # a lista NEM különbözteti meg az API szintjén, a
        # KNOWN_UNRENDERED_OPS regiszter felelős ezért a downstream
        # jelentésben
        result, skipped = apply_filters(
            sample, parse_filters("totallyunknownfilter=1;rainbow=1;")
        )
        assert np.array_equal(result, sample)
        assert skipped == ("totallyunknownfilter", "rainbow")
        assert "rainbow" in KNOWN_UNRENDERED_OPS
        assert "totallyunknownfilter" not in KNOWN_UNRENDERED_OPS


class TestGrainV1NowRendered:
    """#347 lezáró audit (2026-08-06): a `grain` (v1) a `filterdesc-
    registry.md` szerint a `grain2`-vel MEGEGYEZŐ, paraméter nélküli
    "Film Grain" oneclick család régi tagja (`grain` = "Film Grain (Old)",
    `grain2` = "Film Grain" — sem az egyik, sem a másik sorhoz nincs
    csúszka/szín/kurzor dokumentálva, csak a `fullres+slow` sávjelző
    különbözik). Mivel a `grain` v1-re önmagára nincs külön golden-mérés,
    a már golden-mért `grain2`-modellt (`apply_grain`, ld.
    `docs/specs/filters-decoded.md` MÉRT sora) használjuk KÖZELÍTÉSKÉNT —
    ugyanaz a minta, mint a `glow`/`glow2`, `unsharp`/`unsharp2`,
    `finetune`/`finetune2` v1/v2 párosításoknál.
    """

    def test_mar_nem_a_kihagyott_regiszterben(self):
        assert "grain" not in KNOWN_UNRENDERED_OPS

    def test_a_lanc_tenylegesen_renderel(self, sample):
        result, skipped = apply_filters(sample, parse_filters("grain=1;"))
        assert skipped == (), "grain: a lánc még mindig kihagyja"
        assert not np.array_equal(result, sample)

    def test_grain_es_grain2_ugyanazt_a_modellt_hasznalja(self, sample):
        # mindkettő a determinisztikus (seed=0) apply_grain-t hívja —
        # paraméter nélküli oneclick lévén a kimenetnek meg kell egyeznie
        grain_result, _ = apply_filters(sample, parse_filters("grain=1;"))
        grain2_result, _ = apply_filters(sample, parse_filters("grain2=1;"))
        assert np.array_equal(grain_result, grain2_result)


class TestRadtintNowRendered:
    """#565: a `radtint` a natív visszafejtés (regisztráció `0x8f8730`,
    mag `0x90b370`, maszk-LUT `0x90aeb0`) alapján renderel — radiális
    SZORZÓ-tint köbös smoothstep maszkkal."""

    def test_mar_nem_a_kihagyott_regiszterben(self):
        assert "radtint" not in KNOWN_UNRENDERED_OPS

    def test_a_lanc_tenylegesen_renderel(self, sample):
        result, skipped = apply_filters(sample, parse_filters("radtint=1;"))
        assert skipped == ()
        assert not np.array_equal(result, sample)
