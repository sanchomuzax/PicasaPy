"""#643 — TELJES-KORPUSZ próba: ír-e BÁRMELYIK effektünk elvetendő tagot?

A #643 tulajdonosi kérdése („nem ugyanazt látom a két oldalon") csak akkor
válaszolható meg, ha tételesen tudjuk: a szerkesztő MINDEN alkalmazható
effektje olyan `filters=` tagot ír-e, amelyet az eredeti Picasa lánc-bejárója
elfogad. A bejáró az első hibás tagnál megáll, és onnantól a lánc hátralévő
része sem fut le — tehát EGYETLEN rossz effektünk az utána alkalmazott
összeset is megölné a Picasában.

Ez a teszt ezért az egész katalógust végigjárja, MINDKÉT alkalmazási úton:

1. a paraméter nélküli / dokumentált alapértékes út (`applyEffect`), és
2. a csúszkás út (`_session_with_effect` → `resolve_effect_params` +
   `format_param_values`), a katalógus alapértékeivel.

A mérce a `picasapy.ini.filter_guard` — ugyanaz az őr, amelyik az írást is
kapuzza —, plusz a kanonikus írásmód (#695: a Picasa bájtra illeszti a nevet).
"""

from __future__ import annotations

import pytest

from picasapy.app.edit_controller import (
    _APPLICABLE_EFFECTS,
    _EFFECT_INI_NAMES,
    _EFFECT_PARAMS,
)
from picasapy.app.effect_params import format_param_values, resolve_effect_params
from picasapy.edit.session import EditSession
from picasapy.ini.filter_guard import inspect_chain
from picasapy.ini.filter_registry import canonical_filter_name
from picasapy.ini.rect64 import Rect64
from picasapy.ini.retouch import RetouchPatch

#: A csúszkás út képfüggő tartományaihoz (`CornerRadius`, `CaptionHeight`…)
_PROBE_SIZE = (1600, 1200)


def _chain_for(name: str, params: tuple[str, ...]) -> str:
    return f"{name}={','.join(params)};"


def _assert_elfogadhato(chain: str) -> None:
    """A lánc átmegy a Picasa három mért szabályán, és kanonikus írásmódú."""
    defects = inspect_chain(chain)
    assert not defects, "; ".join(defect.describe() for defect in defects)
    name = chain.split("=", 1)[0]
    assert canonical_filter_name(name) == name, (
        f"a(z) {name!r} nem a kanonikus írásmód (a Picasa bájtra illeszti a "
        f"nevet, #695) — várt: {canonical_filter_name(name)!r}"
    )


@pytest.mark.parametrize("key", sorted(_APPLICABLE_EFFECTS))
class TestEffektKorpusz:
    """A szerkesztő MINDEN alkalmazható effektje, mindkét úton."""

    def test_alapertekes_ut(self, key):
        """`applyEffect`: paraméter nélküli / `_EFFECT_PARAMS`-alapértékes."""
        _assert_elfogadhato(
            _chain_for(
                _EFFECT_INI_NAMES.get(key, key), _EFFECT_PARAMS.get(key, ("1",))
            )
        )

    def test_csuszkas_ut(self, key):
        """`_session_with_effect`: a csúszka-katalógus alapértékeivel."""
        catalogue = resolve_effect_params(key, *_PROBE_SIZE)
        if not catalogue:
            pytest.skip("nincs csúszka-katalógusa — az alapértékes út fedi")
        resolved = [
            (param.color if param.kind == "color" else param.default)
            for param in catalogue
        ]
        formatted = format_param_values(resolved, catalogue)
        _assert_elfogadhato(
            _chain_for(_EFFECT_INI_NAMES.get(key, key), ("1", *formatted))
        )


class TestEszkozokKorpusz:
    """A nem effekt-gombos, de láncot író eszközök (vágás, döntés,
    finomhangolás, retusálás, vörösszem, egygombos javítások)."""

    @staticmethod
    def _lanc(session: EditSession) -> str:
        return session.to_value()

    @pytest.mark.parametrize(
        ("cimke", "keszit"),
        [
            ("crop64", lambda s: s.append_crop(Rect64(0.1, 0.1, 0.9, 0.9))),
            ("tilt", lambda s: s.set_tilt(0.3, 1.1)),
            (
                "finetune2",
                lambda s: s.set_finetune(
                    fill=0.2, highlights=0.3, shadows=0.4, temperature=-0.5
                ),
            ),
            (
                "retouch v1",
                lambda s: s.set_retouch_regions((Rect64(0.1, 0.1, 0.2, 0.2),)),
            ),
            (
                "retouch v2",
                lambda s: s.set_retouch_patches(
                    (RetouchPatch(0.1, 0.1, 0.2, 0.2, 0.05),)
                ),
            ),
            (
                "redeye régiós",
                lambda s: s.set_redeye_regions((Rect64(0.1, 0.1, 0.2, 0.2),)),
            ),
            ("redeye üres", lambda s: s.set_redeye_regions(())),
            ("redeye toggle", lambda s: s.toggle("redeye")),
            ("enhance", lambda s: s.apply("enhance")),
            ("autolight", lambda s: s.apply("autolight")),
            ("autocolor", lambda s: s.apply("autocolor")),
            # a csoportos szerkesztés paraméter nélküli effektjei (#425)
            ("batch unsharp", lambda s: s.append_effect("unsharp")),
            ("batch grain2", lambda s: s.append_effect("grain2")),
            ("batch warm", lambda s: s.append_effect("warm")),
        ],
    )
    def test_eszkoz_lanca_elfogadhato(self, cimke, keszit):
        del cimke
        chain = self._lanc(keszit(EditSession()))
        assert inspect_chain(chain) == (), "; ".join(
            defect.describe() for defect in inspect_chain(chain)
        )


class TestKorpuszLefedettseg:
    """Az őr csak akkor ér valamit, ha tényleg a teljes katalógust nézzük."""

    def test_minden_alkalmazhato_effekt_vizsgalva(self):
        assert len(_APPLICABLE_EFFECTS) >= 57, (
            "a katalógus zsugorodott — a korpusz-próba lefedettsége csökkent"
        )
