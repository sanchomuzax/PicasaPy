"""Az ÉLŐ előnézet ugyanazt adja, mint a mentés/export (#3169).

## A hiba, amit ez a lap megfog

Az `apply_filters` **szándékosan átrendezi** a láncot: előbb a nem-keret
effektek, **utána a vágás** (#330), **legvégül a keretek**. Ez a rendezés
egyetlen híváson belül érvényes.

A szerkesztő élő előnézete viszont **kettévágta** a láncot a lánc-prefix
gyorsítótár miatt (`_render_cached`): a prefix-hívás a SAJÁT végén
alkalmazta a benne lévő vágást/keretet, és az utolsó op **arra** futott rá.
Teljes láncnál viszont az utolsó op futna előbb.

**Mérve (2026-09-15, 800 × 600-as próbakép, átlagos abszolút eltérés):**

| lánc | eltérés |
|---|---|
| `crop64=1,…;Vignette=1,50,50` | **18,20** |
| `Border=1,20,5,…;Vignette=1,50,50` | **7,90** |
| `Border=1,20,5,…;sepia=1` | **3,95** |
| `Polaroid=1,5,…;sepia=1` | **2,79** |

Az export (`export/exporter.py`) és a bélyegkép (`thumbs/cache.py`) a
TELJES láncot futtatja ⇒ az előnézet és a mentett kép eltért.

⚠️ **Amit ez a lap NEM állít:** hogy melyik sorrend a HELYES az eredeti
Picasához képest. Az külön kérdés (#3169 első „Kész, ha" pontja, a bináris
oldalról). Itt a követelmény a BELSŐ egyezés: amit a felhasználó lát, az
legyen az, amit ment.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters

#: Láncok, ahol keret-effektet vagy vágást NEM-keret effekt követ — ezek a
#: mért eltérők. A `sepia` pontszerű, a `Vignette` térbeli: mindkettőre kell
#: fogás, mert a kettő máshogy érzékeny a sorrendre.
ATRENDEZODO = (
    "crop64=1,3fff3fffbfffbfff;Vignette=1,50,50",
    "Border=1,20,5,0,000000,ffffff,0;Vignette=1,50,50",
    "Border=1,20,5,0,000000,ffffff,0;sepia=1",
    "Polaroid=1,5,e2e2e2;sepia=1",
    "Cinemascope=1;Vignette=1,50,50",
)

#: Kontroll: ezeknél nincs átrendezés, tehát a két útnak MÁR MA egyeznie kell.
#: Ha ezek buknának, a próba maga volna rossz, nem a kód.
VALTOZATLAN = (
    "bw=1;sepia=1",
    "sepia=1;Border=1,20,5,0,000000,ffffff,0",
)


def _forras() -> np.ndarray:
    """Gradiens + függőleges csíkok: a térbeli effektek is megfognak rajta."""
    y = np.linspace(30, 220, 600, dtype=np.float32)[:, None]
    x = np.linspace(-20, 20, 800, dtype=np.float32)[None, :]
    szurke = np.clip(y + x, 0, 255).astype(np.uint8)
    kep = np.dstack([szurke, szurke, szurke])
    kep[:, ::50] = 255
    return kep


def _provider():
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.mark.parametrize("lanc", ATRENDEZODO + VALTOZATLAN)
def test_az_elonezet_egyezik_a_teljes_lanccal(qt_app, lanc):
    """A gyorsítótáras előnézet bitre ugyanaz, mint a teljes lánc."""
    ops = parse_filters(lanc)
    forras = _forras()
    varhato = apply_filters(forras, ops)[0]
    kapott = _provider()._render_cached("1", forras, ops)
    assert kapott is not None
    assert kapott.shape == varhato.shape, f"{lanc}: más a kimeneti méret"
    assert np.array_equal(kapott, varhato), (
        f"{lanc}: átlagos eltérés "
        f"{np.abs(kapott.astype(int) - varhato.astype(int)).mean():.3f}"
    )


@pytest.mark.parametrize("lanc", ATRENDEZODO)
def test_a_csuszka_huzasa_sem_rontja_el(qt_app, lanc):
    """Ismételt hívás (csúszka-húzás) után is egyeznie kell.

    A gyorsítótár a MÁSODIK hívásnál talál — a hiba épp ott jelentkezne, ha
    a prefix a keretet/vágást már tartalmazná."""
    ops = parse_filters(lanc)
    forras = _forras()
    p = _provider()
    p._render_cached("1", forras, ops)          # feltölti a prefix-gyorsítótárat
    kapott = p._render_cached("1", forras, ops)  # innen már találatból megy
    varhato = apply_filters(forras, ops)[0]
    assert np.array_equal(kapott, varhato)


def test_ures_lanc_es_egytagu_lanc(qt_app):
    """A két szélső eset változatlanul működjön."""
    forras = _forras()
    p = _provider()
    assert np.array_equal(p._render_cached("1", forras, ()), forras)
    ops = parse_filters("sepia=1")
    assert np.array_equal(
        p._render_cached("1", forras, ops), apply_filters(forras, ops)[0]
    )
