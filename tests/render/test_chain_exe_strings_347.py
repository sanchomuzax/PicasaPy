"""#347: az exe-string-bányászat (`docs/specs/picasa-exe-strings.md`) által
azonosított, de a spec addig nem dokumentált `filters=` nevek a láncban.

FONTOS: ezek golden-méréssel MÉG NEM kalibráltak (nincs mögöttük vizuális
modell) — a lánc csak FELISMERI őket, a "nem renderelhető" összesített
jelentésbe (a `apply_filters` `skipped` visszatérési értéke) számítanak, de
nem futtatunk rájuk kitalált implementációt (MEMORY 2026-07-30, őszinteség-
szabály). A `picnik=1;` ez alól kivétel: az nem effekt, hanem boolean
jelző-token (mint a már ismert `redeye=1;`/`retouch=1;`), ezért érvényes
no-op-ként nyelődik el — nem kerül a kihagyott-listába.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import KNOWN_UNRENDERED_OPS, apply_filters

_NEW_UNRENDERED_KEYS = (
    "grain",
    "radtint",
    "roundededges",
    "matte",
    "nightvision",
)


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(11)
    return rng.integers(30, 220, size=(48, 64, 3), dtype=np.uint8)


class TestKnownUnrenderedRegistry:
    def test_uj_nevek_mind_a_regiszterben_vannak(self):
        for key in _NEW_UNRENDERED_KEYS:
            assert key in KNOWN_UNRENDERED_OPS

    @pytest.mark.parametrize("key", _NEW_UNRENDERED_KEYS)
    def test_lanc_felismeri_de_nem_renderel_es_jelenti(self, key, sample):
        # a lánc nem dob kivételt, a kép változatlan marad (nincs vizuális
        # modell), de a nevet a kihagyott-listában jelenti — nem csendben
        # tűnik el
        result, skipped = apply_filters(sample, parse_filters(f"{key}=1;"))
        assert np.array_equal(result, sample)
        assert key in [name.casefold() for name in skipped]

    @pytest.mark.parametrize(
        ("spelled", "key"),
        [
            ("grain", "grain"),
            ("radtint", "radtint"),
            ("RoundedEdges", "roundededges"),
            ("Matte", "matte"),
            ("NightVision", "nightvision"),
        ],
    )
    def test_picasa_eredeti_iras_is_felismert(self, spelled, key, sample):
        result, skipped = apply_filters(sample, parse_filters(f"{spelled}=1;"))
        assert np.array_equal(result, sample)
        assert spelled in skipped

    def test_vegyes_lanc_a_tobbi_effekt_azert_lefut(self, sample):
        # egy ismert (renderelt) effekt + egy #347-es felismert-de-
        # renderelhetetlen egy láncban: az ismert effekt hasson, a másik
        # csak jelentve legyen
        result, skipped = apply_filters(
            sample, parse_filters("Invert=1;grain=1;")
        )
        assert not np.array_equal(result, sample), "az Invert lefutott"
        assert skipped == ("grain",)


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
        # felismert név is a kihagyott-listába kerül — a lista NEM
        # különbözteti meg az API szintjén, a KNOWN_UNRENDERED_OPS regiszter
        # felelős ezért a downstream jelentésben
        result, skipped = apply_filters(
            sample, parse_filters("totallyunknownfilter=1;grain=1;")
        )
        assert np.array_equal(result, sample)
        assert skipped == ("totallyunknownfilter", "grain")
        assert "grain" in KNOWN_UNRENDERED_OPS
        assert "totallyunknownfilter" not in KNOWN_UNRENDERED_OPS
