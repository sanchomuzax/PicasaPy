"""#315: az effekt-gombok, a vezérlő és a renderelő lánc EGY halmazt lássanak.

A hiba, amit ez a teszt kizár: a felületen megjelenik egy effekt-gomb,
amihez a vezérlő nem ismer nevet (ValueError kattintásra), vagy amihez a
renderelőnek nincs handlere (a gomb „csinál valamit", de a kép nem változik).
Az `unsharp` (Élesítés) és a `Vignette` évekig pontosan így hiányzott a
felületről, miközben a renderelő már tudta őket.
"""

from __future__ import annotations

import re
from pathlib import Path

from picasapy.app.edit_controller import _EFFECT_INI_NAMES, _EFFECT_NAMES
from picasapy.edit.session import EditSession
from picasapy.render.chain import _HANDLERS

#: #496: az effekt-fülek önálló fájlokba kerültek az `EditorPanel.qml`-ből —
#: a gombokat ezért a MODUL EGÉSZÉBEN keressük, nem egyetlen fájlban.
_QML_DIR = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "picasapy"
    / "app"
    / "qml"
    / "PicasaPy"
)


def _effects_requested_by_the_ui() -> set[str]:
    """Az effekt-fülek gombjai által küldött nevek, a QML-ből kiolvasva."""
    found: set[str] = set()
    for path in _QML_DIR.glob("*.qml"):
        found.update(
            re.findall(
                r'panel\.effectRequested\("([^"]+)"\)',
                path.read_text(encoding="utf-8"),
            )
        )
    return found


class TestEffectNameCoverage:
    def test_every_ui_button_is_known_to_the_controller(self):
        missing = _effects_requested_by_the_ui() - set(_EFFECT_NAMES)
        assert not missing, (
            f"UI-gomb van, vezérlő-név nincs: {sorted(missing)} — "
            "kattintásra ValueError"
        )

    def test_every_controller_effect_has_a_render_handler(self):
        missing = set(_EFFECT_NAMES) - set(_HANDLERS)
        assert not missing, (
            f"vezérlő ismeri, a renderelő nem: {sorted(missing)} — "
            "a gomb nem változtatna a képen"
        )

    def test_sharpen_and_vignette_are_present(self):
        # a két konkrét hiány, amit a felhasználó bejelentett
        assert "unsharp" in _EFFECT_NAMES
        assert "vignette" in _EFFECT_NAMES
        assert "unsharp" in _effects_requested_by_the_ui()
        assert "vignette" in _effects_requested_by_the_ui()


class TestIniNameCompatibility:
    """A `.picasa.ini`-be azzal a betűzéssel kell írni, amit a Picasa is ír
    (round-trip elv, CLAUDE.md 1. döntés) — a Vignette NAGYBETŰS."""

    def test_vignette_is_written_capitalised(self):
        session = EditSession().append_effect(
            _EFFECT_INI_NAMES.get("vignette", "vignette")
        )
        assert session.to_value() == "Vignette=1;"

    def test_lowercase_effects_are_unchanged(self):
        for key in ("sepia", "bw", "unsharp"):
            assert _EFFECT_INI_NAMES.get(key, key) == key

    def test_render_still_handles_the_capitalised_name(self):
        # a renderelő kis-nagybetű-tűrő: amit kiírunk, azt vissza is olvassa
        from picasapy.ini.filters import parse_filters

        ops = parse_filters("Vignette=1;")
        assert ops and ops[0].name.casefold() in _HANDLERS
