"""`ID_VIEW_OV` — a túlcsordult (kifehéredett) képpontok jelölése — #1576.

A szabály MÉRVE (`0x009e8810`, 49 bájt), a bizonyíték a
`docs/specs/picasa-megjelenitesi-modok.md` **5.6. szakasza**:

```asm
mov esi, [pixel]
and esi, 0xffffff
cmp esi, 0xffffff          ; B == G == R == 255 ?
jne tovabb
mov dword ptr [pixel], 0xffff7f7f
```

Három dolog, amit ez a fájl ŐRIZ — mindhárom azért, mert a „javítás"
kísértése valódi, és paritás-vesztés volna:

1. **Nincs tűrés.** A `254` MÉG NEM túlcsordulás. Aki a küszöböt `>= 254`-re
   lazítja, ezeket a teszteket bukja.
2. **Nincs csatornánkénti jelölés.** A `(255, 200, 10)` képpont R-csatornája
   telített, de az eredeti NEM jelöli — csak a mindhárom csatornán fehéret.
3. **A fekete oldali levágás nincs jelölve.** A `(0, 0, 0)` érintetlen.

A jelölőszín a beírt dword bájtsorrendjéből: `0xFFFF7F7F` ⇒ `B=0x7F`,
`G=0x7F`, `R=0xFF` ⇒ **RGB(255, 127, 127)**.

A `render/` sáv szabálya (CLAUDE.md): az effektek nem nyúlnak a lemezhez —
képet kapnak, képet adnak. Az utolsó osztály ezt is méri.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from picasapy.render.display_modes import (
    OVERFLOW_MARK_RGB,
    apply_display_mode,
    display_mode_changes_pixels,
    mark_overflow,
)


def _raszter(*szinek: tuple[int, int, int]) -> np.ndarray:
    """1 soros raszter a megadott képpontokból (H=1, W=len, 3)."""
    return np.array([list(szinek)], dtype=np.uint8)


class TestJeloloSzin:
    """A konstans maga — a dword bájtsorrendjéből levezetve."""

    def test_a_jelolo_szin_ff7f7f(self):
        assert OVERFLOW_MARK_RGB == (255, 127, 127)


class TestKuszob:
    """A jegy MAGJA: pontosan a (255, 255, 255) és semmi más."""

    def test_a_tokeletes_feher_jelolodik(self):
        eredmeny = mark_overflow(_raszter((255, 255, 255)))
        assert tuple(eredmeny[0, 0]) == OVERFLOW_MARK_RGB

    @pytest.mark.parametrize(
        "szin",
        [
            (254, 255, 255),  # egy csatorna 254 — MÉG NEM túlcsordulás
            (255, 254, 255),
            (255, 255, 254),
            (254, 254, 254),
            (0, 0, 0),  # a fekete oldali levágás NINCS jelölve
            (255, 200, 10),  # csatornánkénti telítés — NEM jelölődik
            (10, 255, 255),
            (255, 127, 127),  # maga a jelölőszín sem jelölődik
        ],
    )
    def test_minden_mas_valtozatlan(self, szin):
        eredmeny = mark_overflow(_raszter(szin))
        assert tuple(eredmeny[0, 0]) == szin

    def test_vegyes_raszterben_csak_a_feher_valtozik(self):
        forras = _raszter(
            (255, 255, 255), (254, 255, 255), (0, 0, 0), (255, 255, 255)
        )
        eredmeny = mark_overflow(forras)
        assert [tuple(p) for p in eredmeny[0]] == [
            OVERFLOW_MARK_RGB,
            (254, 255, 255),
            (0, 0, 0),
            OVERFLOW_MARK_RGB,
        ]

    def test_a_teljesen_fehér_kep_minden_keppontja_jelolodik(self):
        forras = np.full((7, 5, 3), 255, dtype=np.uint8)
        eredmeny = mark_overflow(forras)
        assert np.all(eredmeny == np.array(OVERFLOW_MARK_RGB, dtype=np.uint8))

    def test_a_masodik_futas_nem_terjeszkedik(self):
        """A jelölés IDEMPOTENS — a jelölőszín nem fehér, tehát nem terjed."""
        forras = _raszter((255, 255, 255), (0, 0, 0))
        egyszer = mark_overflow(forras)
        ketszer = mark_overflow(egyszer)
        assert np.array_equal(egyszer, ketszer)


class TestValtozatlansag:
    """A bemenetet SOHA nem írjuk át (immutabilitás) — és típus/alak marad."""

    def test_a_bemeneti_tomb_valtozatlan(self):
        forras = _raszter((255, 255, 255), (1, 2, 3))
        masolat = forras.copy()
        mark_overflow(forras)
        assert np.array_equal(forras, masolat), (
            "a jelölés HELYBEN írta át a bemenetet — a hívó (edit-előnézet) "
            "gyorsítótárát mérgezné meg"
        )

    def test_alak_es_tipus_marad(self):
        forras = np.zeros((4, 6, 3), dtype=np.uint8)
        eredmeny = mark_overflow(forras)
        assert eredmeny.shape == forras.shape
        assert eredmeny.dtype == np.uint8

    def test_jelolendo_nelkul_bajtra_azonos(self):
        forras = np.arange(4 * 6 * 3, dtype=np.uint8).reshape((4, 6, 3))
        eredmeny = mark_overflow(forras)
        assert np.array_equal(eredmeny, forras)


class TestModValaszto:
    """`apply_display_mode` — a tizenegy mód közös belépési pontja."""

    def test_az_overflow_jelol(self):
        eredmeny = apply_display_mode(_raszter((255, 255, 255)), "overflow")
        assert tuple(eredmeny[0, 0]) == OVERFLOW_MARK_RGB

    @pytest.mark.parametrize(
        "mode",
        ["auto", "normal", "dither16", "rdesk", "", "ismeretlen"],
    )
    def test_a_tobbi_mod_ma_atenged(self, mode):
        """A még megvalósítatlan módokra átereszt.

        A `lcd`/`projector` (#1577) és a `linear` (#1578) azóta KIKERÜLT
        ebből a névsorból — a képpont-szabályukat a
        `tests/render/test_display_modes_1577_1578.py` őrzi —, a `sepia` és
        a `bw` pedig a #1657 óta (`test_display_modes_szepia_bw_1657.py`).
        A maradék (`dither16`, `rdesk`, `mac`) külön jegyeké.
        """
        forras = _raszter((255, 255, 255), (0, 0, 0))
        eredmeny = apply_display_mode(forras, mode)
        assert np.array_equal(eredmeny, forras)

    def test_a_none_kepet_atengedi(self):
        assert apply_display_mode(None, "overflow") is None

    @pytest.mark.parametrize(
        "mode,vart",
        [("overflow", True), ("auto", False), ("normal", False),
         ("bw", True), ("sepia", True), ("", False), ("ismeretlen", False)],
    )
    def test_a_kepponthatas_lekerdezheto(self, mode, vart):
        """A hívó ebből tudja, kell-e egyáltalán másolatot készítenie."""
        assert display_mode_changes_pixels(mode) is vart


class TestSavhatar:
    """`render/` sáv-invariáns: az effektek NEM nyúlnak a lemezhez."""

    def test_a_modul_forrasa_nem_nyul_fajlhoz(self):
        from picasapy.render import display_modes

        forras = inspect.getsource(display_modes)
        for tiltott in ("open(", "imread", "imwrite", "Path(", "os."):
            assert tiltott not in forras, (
                f"a display_modes modul lemezhez nyúlna ({tiltott!r}) — "
                "ez sávhatár-átlépés"
            )
