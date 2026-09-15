"""A keret-effektek forrás → kimenet leképezése (#3166, a #819 `resizes` ága).

## Miért kell

A `cropOverlay` és a `facesOverlay` a KIRAJZOLT kép téglalapjára
horgonyozódik, az arcokat pedig relatív `[0..1]` koordinátákkal rajzolja.
Ha a lánc keret-effektet tartalmaz, a kirajzolt kép a **keretezett**
kimenet — a relatív koordináta tehát a keretre skálázódik, nem a fényképre.

## Miért ÍGY mérünk — három csapda, mindhárom megkerülve

A leképezés a renderelő aritmetikáját tükrözi, tehát **elsodródhat** tőle.
Ezért egyik próba sem képletet hasonlít képlethez: mindegyik egy jelölőt tesz
a forrásba, lefuttatja a VALÓDI láncot, és megméri, hova került.

1. ⛔ **A jelölőt nem a SZÍNE alapján keressük.** A keretek maguk is fehéret
   és feketét használnak (a `Border` belső gyűrűje `ffffff`), tehát a
   „legvilágosabb képpont" a keretet találná meg.
2. ⛔ **A háttér nem lehet egyenletes, a jelölő pedig nem lehet erős.** A
   `Cinemascope` lánca `autofix`-ot futtat, tehát a jelölő a HISZTOGRAMON át
   az egész kimenetre visszahat. Egyenletes háttérnél ez odáig fajul, hogy a
   jelölő nélküli render csupa 255 lesz, és a különbség **pont a jelölő
   helyén nulla** (mérve). Ezért gradiens a háttér és mindössze
   `SAV_DELTA = 18` a jelölő.
3. ⛔ **Egyetlen négyzet alakú jelölő sem elég**, mert a `Polaroid` forgat:
   a jelölő súlypontja csak akkor egyezik a leképezett középponttal, ha a
   jelölő alakja az adott tengelyen végig tart.

**A megoldás:** tengelyenként egy-egy SÁV jelölő (vízszintes a `y`-hoz,
függőleges az `x`-hez), és a különbség-kép tengelyre vetített profiljából
a MEDIÁN fölötti rész súlypontja. A medián levonása tünteti el a 2. pont
globális eltolódását; az affin leképezés pedig a súlypontot a súlypontba
viszi, tehát a forgatás sem visz félre.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.chain_geometry import keret_geometria

FORRAS_W, FORRAS_H = 800, 600

#: A jelölő-sáv vastagsága és a középvonala a forrásban.
SAV = 24
SAV_X, SAV_Y = 300, 220

#: Megengedett eltérés a megjósolt és a mért középvonal közt.
TURES_PX = 1.5

#: (láncszöveg, elvárt-e méretváltozás)
LANCOK = (
    ("Border=1,20,5,0,000000,ffffff,0", True),
    ("MuseumMatte=1,25,40,1a0e03,f0eae4", True),
    ("DropShadow=1,4,90,10,000000,ffffff,30", True),
    ("Polaroid=1,5,e2e2e2", True),
    ("Cinemascope=1", True),
    ("RoundedEdges=1", False),
)

#: Tisztán eltolásos szűrők — ott a mért eltérésnek NULLÁNAK kell lennie.
CSAK_ELTOLAS = (
    "Border=1,20,5,0,000000,ffffff,0",
    "MuseumMatte=1,25,40,1a0e03,f0eae4",
    "DropShadow=1,4,90,10,000000,ffffff,30",
)


#: A jelölő-sáv világosítása. **Szándékosan kicsi**: a `Cinemascope` lánca
#: `autofix`-ot futtat, tehát a jelölő a HISZTOGRAMON át az egész képre
#: visszahat. 18 fokozatnál ez a visszahatás a profil alapszintje alá kerül.
SAV_DELTA = 18


def _hatter() -> np.ndarray:
    """Két irányban változó gradiens.

    ⛔ **Egyenletes háttérrel ez a mérés NEM működik**, és ezt megmértük: a
    konstans képet az `autofix` teljesen kifeszíti, ezért a jelölő nélküli
    render csupa 255 lesz, a jelölő sorai pedig MINDKÉT futásban 255-ök —
    a különbség pont ott nulla, ahol a jelölő van. A gradiens adja az
    `autofix`-nak a valódi hisztogramot."""
    fuggoleges = np.linspace(30, 220, FORRAS_H, dtype=np.float32)[:, None]
    vizszintes = np.linspace(-20, 20, FORRAS_W, dtype=np.float32)[None, :]
    szurke = np.clip(fuggoleges + vizszintes, 0, 255).astype(np.uint8)
    return np.dstack([szurke, szurke, szurke])


def _forras(sav: str | None) -> np.ndarray:
    """Gradiens háttér, opcionálisan egy teljes szélességű/magasságú,
    enyhén világosabb sávval (`"vizszintes"` / `"fuggoleges"`)."""
    kep = _hatter()
    if sav == "vizszintes":
        resz = kep[SAV_Y : SAV_Y + SAV, :]
        kep[SAV_Y : SAV_Y + SAV, :] = np.clip(resz.astype(np.int16) + SAV_DELTA, 0, 255)
    elif sav == "fuggoleges":
        resz = kep[:, SAV_X : SAV_X + SAV]
        kep[:, SAV_X : SAV_X + SAV] = np.clip(resz.astype(np.int16) + SAV_DELTA, 0, 255)
    return kep


def _profil_kozep(profil: np.ndarray) -> float:
    """A 60. percentilis fölötti rész súlypontja — ld. a modul docstringjét.

    A percentilis (és nem a medián) azért kell, mert a méretnövelő szűrők
    kimenetének jó része keret: ott a különbség nulla, tehát a medián a
    keret felé húzna."""
    suly = np.clip(profil - np.percentile(profil, 60), 0.0, None)
    assert suly.sum() > 0, "a jelölő nem hagyott nyomot a kimenetben"
    return float((np.arange(suly.size) * suly).sum() / suly.sum())


def _mert_kozepvonal(lanc: str, sav: str) -> float:
    """A jelölő-sáv MÉRT középvonala a valódi renderelt kimenetben."""
    ops = parse_filters(lanc)
    vel = apply_filters(_forras(sav), ops)[0].astype(np.float64)
    nelkul = apply_filters(_forras(None), ops)[0].astype(np.float64)
    assert vel.shape == nelkul.shape
    elteres = np.abs(vel - nelkul).sum(axis=2)
    # vízszintes sáv → soronkénti profil (y); függőleges sáv → oszloponkénti (x)
    return _profil_kozep(elteres.sum(axis=1) if sav == "vizszintes" else elteres.sum(axis=0))


def _megjosolt(matrix, x: float, y: float) -> tuple[float, float]:
    (a, b, c), (d, e, f) = matrix
    return a * x + b * y + c, d * x + e * y + f


def _sav_kozep() -> float:
    return SAV_X + (SAV - 1) / 2.0


@pytest.mark.parametrize("lanc, valtozik", LANCOK)
def test_a_kimeneti_meret_egyezik_a_rendereltel(lanc, valtozik):
    """A megjósolt kimeneti méret a TÉNYLEGES renderével egyezzen."""
    ops = parse_filters(lanc)
    jelentes = apply_filters(_forras(None), ops)
    assert not jelentes[1], f"a lánc kimaradt: {jelentes[1]}"
    rendereltek = jelentes[0]

    geo = keret_geometria(ops, FORRAS_W, FORRAS_H)
    assert (geo.szelesseg, geo.magassag) == (rendereltek.shape[1], rendereltek.shape[0])
    valtozott = (geo.szelesseg, geo.magassag) != (FORRAS_W, FORRAS_H)
    assert valtozott is valtozik


@pytest.mark.parametrize("lanc, _valtozik", LANCOK)
def test_a_fuggoleges_sav_oda_kerul_ahova_a_lekepezes_mondja(lanc, _valtozik):
    """`x` tengely: a függőleges jelölő-sáv mért és megjósolt középvonala."""
    mert_x = _mert_kozepvonal(lanc, "fuggoleges")
    geo = keret_geometria(parse_filters(lanc), FORRAS_W, FORRAS_H)
    # a sáv végig tart `y`-ban, tehát a súlypontja a kép függőleges közepén ül
    jos_x, _ = _megjosolt(geo.matrix, _sav_kozep(), (FORRAS_H - 1) / 2.0)
    assert abs(jos_x - mert_x) <= TURES_PX, f"{lanc}: x {jos_x:.2f} ≠ {mert_x:.2f}"


@pytest.mark.parametrize("lanc, _valtozik", LANCOK)
def test_a_vizszintes_sav_oda_kerul_ahova_a_lekepezes_mondja(lanc, _valtozik):
    """`y` tengely: a vízszintes jelölő-sáv mért és megjósolt középvonala."""
    mert_y = _mert_kozepvonal(lanc, "vizszintes")
    geo = keret_geometria(parse_filters(lanc), FORRAS_W, FORRAS_H)
    _, jos_y = _megjosolt(geo.matrix, (FORRAS_W - 1) / 2.0, SAV_Y + (SAV - 1) / 2.0)
    assert abs(jos_y - mert_y) <= TURES_PX, f"{lanc}: y {jos_y:.2f} ≠ {mert_y:.2f}"


@pytest.mark.parametrize("lanc", CSAK_ELTOLAS)
def test_a_tisztan_eltolasos_szuroknel_az_elteres_NULLA(lanc):
    """A tűrés nem takar pontatlanságot: ahol csak eltolás van, ott egyezik.

    A `Border`, a `MuseumMatte` és a `DropShadow` a képet átméretezés és
    forgatás nélkül teszi a vászonra, tehát a mért középvonalnak
    **századképpontnyi** pontossággal a megjósolt helyre kell esnie.

    ⚠️ A `0.01` nem enyhítés, hanem a súlypont-összegzés lebegőpontos
    maradéka. Kerekített egészeket szándékosan NEM hasonlítunk: a mért érték
    tipikusan pont `x,5`, ahol a Python bankári kerekítése egy hajszálnyi
    zajtól is átbillen (`round(296.5) == 296`, de `round(296.5004) == 297`)."""
    geo = keret_geometria(parse_filters(lanc), FORRAS_W, FORRAS_H)
    jos_x, _ = _megjosolt(geo.matrix, _sav_kozep(), (FORRAS_H - 1) / 2.0)
    _, jos_y = _megjosolt(geo.matrix, (FORRAS_W - 1) / 2.0, SAV_Y + (SAV - 1) / 2.0)
    assert abs(jos_x - _mert_kozepvonal(lanc, "fuggoleges")) < 0.01
    assert abs(jos_y - _mert_kozepvonal(lanc, "vizszintes")) < 0.01


def test_keret_nelkuli_lanc_azonossag():
    """Keret-effekt nélkül a leképezés az azonosság, a méret változatlan."""
    geo = keret_geometria(parse_filters("sepia=1;"), FORRAS_W, FORRAS_H)
    assert (geo.szelesseg, geo.magassag) == (FORRAS_W, FORRAS_H)
    assert geo.matrix == ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    assert geo.valtoztat is False


def test_ures_lanc_azonossag():
    geo = keret_geometria((), FORRAS_W, FORRAS_H)
    assert geo.valtoztat is False
    assert (geo.szelesseg, geo.magassag) == (FORRAS_W, FORRAS_H)


def test_ket_keret_egymas_utan_osszeadodik():
    """Láncolt keretek: a leképezések ÖSSZEFŰZŐDNEK, nem az utolsó nyer."""
    egy = keret_geometria(parse_filters("Border=1,20,5,0,000000,ffffff,0"), FORRAS_W, FORRAS_H)
    ketto = keret_geometria(
        parse_filters("Border=1,20,5,0,000000,ffffff,0;Border=1,10,0,0,000000,ffffff,0"),
        FORRAS_W,
        FORRAS_H,
    )
    assert ketto.szelesseg == egy.szelesseg + 20
    assert ketto.matrix[0][2] == egy.matrix[0][2] + 10
