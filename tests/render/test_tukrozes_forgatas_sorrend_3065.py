"""#3065: előbb TÜKRÖZÉS, utána FORGATÁS — a mért sorrend.

## A mérés

`docs/specs/picasa-ini-format.md` „⛳ MEGVAN A SORREND”: három egymástól
független összeállító betűre azonos alakban előbb a tükrözés-maszk két
bitjét dolgozza fel (`0x009a9ea0` vízszintes, `0x009a9dd0` függőleges), és
CSAK UTÁNA hívja a forgatást (`0x009aa270`) —
`0x0042ef68`/`0x0042ef77`/`0x0042f02d`,
`0x006b5047`/`0x006b5056`/`0x006b50ba`,
`0x00805171`/`0x00805181`/`0x00805229`.

⇒ `kép = forgat(tükröz(eredeti))`.

## Miért nem mindegy

A két művelet NEM kommutál: `tükröz_v ∘ forgat90 = forgat90 ∘ tükröz_h`,
azaz 90°/270° mellett a fölcserélt sorrend a MÁSIK tengelyre tükröz. A hiba
tehát csak akkor látszik, ha egyszerre áll forgatás ÉS tükrözés, és a
forgatás nem 0°/180°.

## Amit ez a lap mér

A KIMENETET, nem a hívási sorrendet: egy aszimmetrikus mintaképre a kapott
képpont-tömb egyezzen a `forgat(tükröz(kép))` referenciával, és **térjen el**
a `tükröz(forgat(kép))`-től. A második fele a KONTROLL — enélkül az őr akkor
is zöld lenne, ha a két sorrend ugyanazt adná, azaz ha a próba semmit nem mér.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from picasapy.render.flip import FLIP_HORIZONTAL, FLIP_VERTICAL, apply_flip


def _aszimmetrikus(szelesseg: int = 40, magassag: int = 20) -> np.ndarray:
    """Minden sarok más — így BÁRMELYIK tengelycsere kimutatható.

    Sima „bal fehér / jobb fekete” kép nem elég: a függőleges tükrözés azon
    NEM változtat, tehát a próba vakon átmenne."""
    kep = np.zeros((magassag, szelesseg, 3), dtype=np.uint8)
    fy, fx = magassag // 2, szelesseg // 2
    kep[:fy, :fx] = (255, 0, 0)      # bal-felső:  kék (BGR)
    kep[:fy, fx:] = (0, 255, 0)      # jobb-felső: zöld
    kep[fy:, :fx] = (0, 0, 255)      # bal-alsó:   vörös
    kep[fy:, fx:] = (255, 255, 255)  # jobb-alsó:  fehér
    return kep


def _forgat(kep: np.ndarray, lepes: int) -> np.ndarray:
    for _ in range(int(lepes) % 4):
        kep = cv2.rotate(kep, cv2.ROTATE_90_CLOCKWISE)
    return kep


def _mert_sorrend(kep, lepes, maszk):
    """`forgat(tükröz(kép))` — ez a MÉRT."""
    return _forgat(apply_flip(kep, maszk), lepes)


def _felcserelt(kep, lepes, maszk):
    """`tükröz(forgat(kép))` — ez volt nálunk, és ez a kontroll."""
    return apply_flip(_forgat(kep, lepes), maszk)


#: azok az esetek, ahol a két sorrend TÉNYLEGESEN eltér
ELTERO = [(1, FLIP_HORIZONTAL), (1, FLIP_VERTICAL), (3, FLIP_HORIZONTAL),
          (3, FLIP_VERTICAL)]


class TestAKontroll:
    """Előbb bizonyítsuk, hogy a próba egyáltalán mér valamit."""

    @pytest.mark.parametrize(("lepes", "maszk"), ELTERO)
    def test_a_ket_sorrend_ELTER(self, lepes, maszk):
        kep = _aszimmetrikus()
        assert not np.array_equal(
            _mert_sorrend(kep, lepes, maszk), _felcserelt(kep, lepes, maszk)
        ), (
            f"a két sorrend ugyanazt adja (lépés={lepes}, maszk={maszk}) — "
            "ezen az eseten az őr semmit nem mérne"
        )

    @pytest.mark.parametrize(("lepes", "maszk"), [(0, FLIP_HORIZONTAL),
                                                  (2, FLIP_HORIZONTAL),
                                                  (2, FLIP_VERTICAL),
                                                  (1, FLIP_HORIZONTAL | FLIP_VERTICAL)])
    def test_ahol_NEM_ter_el_azt_is_mondjuk_ki(self, lepes, maszk):
        """0°/180°-nál, és mindkét tengelyre tükrözve a sorrend közömbös —
        ezeken az eseteken a jegy hibája nem is látszik."""
        kep = _aszimmetrikus()
        assert np.array_equal(
            _mert_sorrend(kep, lepes, maszk), _felcserelt(kep, lepes, maszk)
        )


class TestAzExport:
    @pytest.mark.parametrize(("lepes", "maszk"), ELTERO)
    def test_az_export_a_MERT_sorrendet_adja(self, tmp_path, lepes, maszk):
        from picasapy.export import ExportItem, export_photos

        forras = tmp_path / "sarkok.png"
        kep = _aszimmetrikus()
        cv2.imwrite(str(forras), kep)
        beolvasott = cv2.imread(str(forras))

        jelentes = export_photos(
            [ExportItem(forras, rotate_steps=lepes, flip_flags=maszk)],
            tmp_path / "ki",
        )
        kimenet = cv2.imread(str(jelentes.exported[0]))

        varhato = _mert_sorrend(beolvasott, lepes, maszk)
        rossz = _felcserelt(beolvasott, lepes, maszk)
        #: JPEG-kimenet, ezért nem bájthű az egyezés — a sarkok színe dönt
        assert _sarkok(kimenet) == _sarkok(varhato), (
            f"az export nem a mért sorrendet adja (lépés={lepes}, maszk={maszk})"
        )
        assert _sarkok(kimenet) != _sarkok(rossz)


class TestAMentes:
    @pytest.mark.parametrize(("lepes", "maszk"), ELTERO)
    def test_a_mentes_a_MERT_sorrendet_adja(self, tmp_path, lepes, maszk):
        from picasapy.app.save_controller import _render_for_save

        forras = tmp_path / "sarkok.png"
        kep = _aszimmetrikus()
        cv2.imwrite(str(forras), kep)
        beolvasott = cv2.imread(str(forras))

        kimenet = _render_for_save(
            forras, rotate_steps=lepes, filters="", flip_flags=maszk
        )

        assert _sarkok(kimenet) == _sarkok(_mert_sorrend(beolvasott, lepes, maszk)), (
            f"a mentés nem a mért sorrendet adja (lépés={lepes}, maszk={maszk})"
        )
        assert _sarkok(kimenet) != _sarkok(_felcserelt(beolvasott, lepes, maszk))


def _sarkok(kep: np.ndarray) -> list[tuple[int, int, int]]:
    """A négy sarok domináns színe — JPEG-tűrő ujjlenyomat."""
    m, sz = kep.shape[:2]
    ki = []
    for y0, y1, x0, x1 in ((0, m // 4, 0, sz // 4), (0, m // 4, -sz // 4, sz),
                           (-m // 4, m, 0, sz // 4), (-m // 4, m, -sz // 4, sz)):
        resz = kep[y0:y1, x0:x1] if y1 <= m else kep[y0:, x0:x1]
        atlag = resz.reshape(-1, 3).mean(axis=0)
        ki.append(tuple(int(round(v / 128) * 128) for v in atlag))
    return ki
