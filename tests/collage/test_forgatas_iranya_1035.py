"""A forgatás IRÁNYA: a vászon és a mentés ugyanabba az irányba dönt (#1035).

A hiba a felhasználó MUNKÁJÁT rontotta: amit ferdén balra dőlve látott az
élő vásznon, az jobbra dőlve mentődött. A Képkupac legyezőszerű dőlése az
elrendezés egyik legjellegzetesebb vonása, tehát nem apró eltérés.

## Az EREDETI konvenciója (golden-méréssel igazolva, #1035)

A `.cxf` a `theta`-t radiánban, előjelesen tárolja, és az eredeti Picasa
**előjelváltás nélkül**, ezzel a képlettel használja (`y` LEFELÉ,
képernyő-koordináta):

    X = cx + u·cos(θ) − v·sin(θ)
    Y = cy + u·sin(θ) + v·cos(θ)

Következmény, és ez a lap **megkülönböztető próbája**: a csempe **felső
éle közepe** (`u = 0`, `v = −b`) pozitív `theta` mellett `X = cx + b·sin(θ)`,
vagyis **JOBBRA** mozdul.

## Melyik oldalunk tévedett

| oldal | a felső él közepe `theta = +0,5`-nél |
|---|---|
| az eredeti (a fenti képlet) | +47,9 → **jobbra** |
| a QML vászon (`rotation: theta·180/π`) | +47,9 → **jobbra** ✅ |
| a MAG a javítás előtt (`cv2.getRotationMatrix2D`) | −47,9 → **balra** ❌ |

Az OpenCV a pozitív szöget az óramutatóval **ellentétesen** forgatja, az
eredeti képlete (y lefelé) viszont vele **egyezően**. A javítás ezért a
renderelőben van (`render.screen_rotation`), és **csak az előjel** változott.

## ⚠️ Amihez tilos volt hozzányúlni: a TÁROLT `theta`

A `.cxf` a `theta`-t tárolja, és mi pontosan azt írjuk vissza, amit a
Picasa írt (mind a nyolc golden fájl bájtra azonos a `loads` → `dumps`
úton). Ha valaki „egyszerűbbnek" látja a modellben vagy a `.cxf` írásakor
negálni, azzal a kétirányú Picasa-kompatibilitást töri el — és az **csak
akkor derül ki, ha valaki visszanyitja a fájlt az igazi Picasában**. Ezért
a lapon külön őr áll a tárolt érték változatlanságára: a bájtazonosság
önmagában NEM fogná meg, ha a negálás a rajzolás előtt, a modellben
történne.

## ⚠️ Amit ez a lap NEM dönt el

Az árnyék **eltolása** (`0x0087b411`, `0x0087b423`) a csomópont
eltolás-komponenseihez adódik, de nincs levezetve, hogy ez a forgatás
ELŐTT vagy UTÁN történik — vagyis nem tudjuk, hogy az eltolás
képernyő-igazított, vagy a képpel együtt fordul. A golden-anyag ezt nem
dönti el (3–5 képpont eltolás 1–5°-os szögeknél a mérési hiba alatt van).
A lap ezért csak azt állítja, hogy az árnyék sziluettje a csempével
EGYÜTT fordul — az eltolás koordinátarendszere nyitott kérdés marad.

## A golden anyag és a nyilvános repó

A nyolc golden `.cxf` a felhasználó saját kollázsaiból származik, a
**privát** `sanchomuzax/picasapy-agent` repóban él, a nyilvános repóba nem
kerülhet. Ezért két rétegben mérünk: a CI-ben mindig futó őrök **generált**
mintával dolgoznak (a saját írónk kimenetével, tehát formátumhű), a
fejlesztői gépen pedig egy további eset a **valódi nyolc fájlt** is
átfuttatja — ha a privát anyag nincs a helyén, kihagyja magát.
"""

from __future__ import annotations

import math
import re
import zipfile
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtGui import QTransform

from picasapy.collage import cxf
from picasapy.collage.layout import Placement
from picasapy.collage.render import _rotated_paste
from picasapy.collage.shadow import ShadowParams, draw_shadow

#: Próba-szögek radiánban. A ±0,0894 a golden `AI1` legnagyobb szögű
#: csomópontja (−5,12°), a ±0,5 a #1021 mérésének szöge (28,6°).
PROBA_THETAK = (0.5, -0.5, 0.0894, -0.0894, 0.25)

_CSEMPE = 200  # a próbacsempe oldala
_VASZON = 600  # a próbavászon oldala
_CSEMPE_X = 200  # a csempe bal felső sarka a vásznon
_CSEMPE_Y = 200

#: A jelölő a csempe FELSŐ ÉLÉNEK közepén — ez a megkülönböztető pont. Egy
#: képpontnyira beljebb, hogy a csempe elforgatott élének fedettségi
#: átmenete ne keveredjen bele.
_JEL_SOROK = slice(1, 13)
_JEL_OSZLOPOK = slice(94, 106)

#: A jelölő súlypontja a csempén belül, folytonos koordinátában (a `[i, j]`
#: képpont közepe `(j + 0,5 ; i + 0,5)`).
_JEL_U = 0.0  # (94,5 + 105,5) / 2 − 100
_JEL_V = -93.0  # (1,5 + 12,5) / 2 − 100

#: A csempe közepe a vásznon, folytonos koordinátában.
_KOZEP_X = _CSEMPE_X + _CSEMPE / 2
_KOZEP_Y = _CSEMPE_Y + _CSEMPE / 2

#: A mérés tűrése képpontban: a `_rotated_paste` egész képpontra kerekít, a
#: `warpAffine` pedig interpolál — ez együtt legfeljebb egy-két képpont.
_TURES_PX = 2.0

_QML_CSOMOPONT = (
    Path(__file__).resolve().parents[2]
    / "src/picasapy/app/qml/PicasaPy/CollageNode.qml"
)


def _jelolt_csempe() -> np.ndarray:
    """Fehér csempe, a FELSŐ ÉLE közepén kék jelölővel (BGR)."""
    csempe = np.full((_CSEMPE, _CSEMPE, 3), 255, dtype=np.uint8)
    csempe[_JEL_SOROK, _JEL_OSZLOPOK] = (255, 0, 0)
    return csempe


def _jel_sulypontja(vaszon: np.ndarray) -> tuple[float, float]:
    """A kék jelölő súlypontja a vásznon, folytonos koordinátában.

    A súly a „kékség": `kék − zöld`. Fehéren (a vászon és a csempe) nulla, a
    jelölőn 255 — és **feketén is nulla**, ami itt lényeges: a `warpAffine`
    a csempe elforgatott élén fehér→fekete átmenetet hagy, egy puszta
    „255 − zöld" súly ezt az egész kerületet beszámítaná, és elnyomná a
    jelölőt. Az interpolált élek arányosan számítanak bele, ezért a súlypont
    a képpontrácsnál finomabb."""
    suly = np.clip(
        vaszon[:, :, 0].astype(np.float64) - vaszon[:, :, 1].astype(np.float64),
        0.0,
        None,
    )
    osszeg = float(suly.sum())
    assert osszeg > 0.0, "a jelölő nem került a vászonra"
    sorok, oszlopok = np.indices(suly.shape[:2])
    x = float((suly * (oszlopok + 0.5)).sum() / osszeg)
    y = float((suly * (sorok + 0.5)).sum() / osszeg)
    return (x, y)


def _mag_jel_helye(theta: float) -> tuple[float, float]:
    """A jelölő helye a MENTÉSI úton (a mag `_rotated_paste`-je)."""
    vaszon = np.full((_VASZON, _VASZON, 3), 255, dtype=np.uint8)
    _rotated_paste(
        vaszon,
        _jelolt_csempe(),
        Placement(
            x=_CSEMPE_X,
            y=_CSEMPE_Y,
            width=_CSEMPE,
            height=_CSEMPE,
            angle=math.degrees(theta),
        ),
    )
    return _jel_sulypontja(vaszon)


def _sziluett(theta: float) -> np.ndarray:
    """A csempe TÉNYLEGES lenyomata a vásznon (fekete csempe fehér lapon)."""
    vaszon = np.full((_VASZON, _VASZON, 3), 255, dtype=np.uint8)
    _rotated_paste(
        vaszon,
        np.zeros((_CSEMPE, _CSEMPE, 3), dtype=np.uint8),
        Placement(
            x=_CSEMPE_X,
            y=_CSEMPE_Y,
            width=_CSEMPE,
            height=_CSEMPE,
            angle=math.degrees(theta),
        ),
    )
    return vaszon[:, :, 0] < 128


def _eredeti_keplet(theta: float) -> tuple[float, float]:
    """A jelölő VÁRT helye az eredeti Picasa konvenciója szerint."""
    x = _KOZEP_X + _JEL_U * math.cos(theta) - _JEL_V * math.sin(theta)
    y = _KOZEP_Y + _JEL_U * math.sin(theta) + _JEL_V * math.cos(theta)
    return (x, y)


# --- 1. Az irány az EREDETIÉVEL egyezik --------------------------------------


@pytest.mark.parametrize("theta", PROBA_THETAK)
def test_a_mentesi_ut_az_eredeti_kepletet_koveti(theta):
    """A mag oda teszi a jelölőt, ahova az eredeti képlete mondja."""
    mert_x, mert_y = _mag_jel_helye(theta)
    vart_x, vart_y = _eredeti_keplet(theta)
    assert mert_x == pytest.approx(vart_x, abs=_TURES_PX)
    assert mert_y == pytest.approx(vart_y, abs=_TURES_PX)


def test_a_felso_el_kozepe_pozitiv_thetara_JOBBRA_mozdul():
    """A #1035 megkülönböztető próbája, számmal.

    `theta = +0,5` rad, `b = 93`: az eredeti szerint az eltolás
    `+93·sin(0,5) = +44,6` képpont — JOBBRA. A javítás előtt a mag ugyanennyit
    adott BALRA."""
    mert_x, _ = _mag_jel_helye(0.5)
    eltolas = mert_x - _KOZEP_X
    assert eltolas > 0.0, "a mag az eredetivel ELLENTÉTES irányba forgat"
    assert eltolas == pytest.approx(-_JEL_V * math.sin(0.5), abs=_TURES_PX)


def _legfelso_sarok_x(theta: float) -> float:
    """A KIRAJZOLT csempe legmagasabb pontjának x-e (a kiálló sarok)."""
    sziluett = _sziluett(theta)
    sorok = np.flatnonzero(sziluett.any(axis=1))
    assert sorok.size > 0, "a csempe nem került a vászonra"
    oszlopok = np.flatnonzero(sziluett[sorok[0]])
    return float(oszlopok.mean() + 0.5)


@pytest.mark.parametrize(
    ("theta", "jobbra"), [(-0.0894, True), (0.0894, False), (-0.25, True)]
)
def test_a_negativ_theta_a_jobb_oldalt_emeli(theta, jobbra):
    """„Negatív theta = a kép JOBB oldala magasabban" (#1035 golden-mérés).

    A megkülönböztető nem a képlet újramondása, hanem a KIRAJZOLT csempe:
    melyik sarka a legmagasabb. Negatív `theta`-nál a JOBB, pozitívnál a
    BAL — a javítás előtt fordítva volt."""
    sarok_x = _legfelso_sarok_x(theta)
    if jobbra:
        assert sarok_x > _KOZEP_X, "a legmagasabb sarok nem a jobb oldalon van"
    else:
        assert sarok_x < _KOZEP_X, "a legmagasabb sarok nem a bal oldalon van"


# --- 2. A KÉT ÚT EGYEZÉSE ----------------------------------------------------


def test_a_qml_vaszon_kotese_elojelvaltas_nelkul_forgat():
    """A vászon oldala: `rotation: theta * 180 / Math.PI`, negálás nélkül.

    Ez a kötés adja a QML `Item.rotation`-t, ami a Qt-ben **fokban, az
    óramutatóval egyező** irányú. Ha valaki ide negálást tesz, a két út
    ismét szétválik — ezért a kötés szövege maga is őrzött."""
    forras = _QML_CSOMOPONT.read_text(encoding="utf-8")
    talalat = re.search(r"^\s*rotation:\s*(.+)$", forras, re.MULTILINE)
    assert talalat is not None, "nincs `rotation` kötés a CollageNode.qml-ben"
    assert talalat.group(1).strip() == "theta * 180 / Math.PI"


@pytest.mark.parametrize("theta", PROBA_THETAK)
def test_a_vaszon_es_a_mentes_ugyanoda_dont(theta):
    """A KÉT ÚT egyezése ugyanarra a `theta`-ra — a jegy magja.

    A vászon oldalát nem feltételezzük, hanem a Qt SAJÁT forgatásával
    számoljuk ki: a `QTransform.rotate` ugyanabban a konvencióban forgat,
    mint a QML `Item.rotation` (fok, óramutatóval egyező, y lefelé). Az
    összevetés így akkor is megfog egy elcsúszást, ha valaki csak az egyik
    oldalt igazítja."""
    atalakito = QTransform()
    atalakito.rotate(theta * 180 / math.pi)  # pontosan a QML-kötés kifejezése
    vaszon_x, vaszon_y = atalakito.map(_JEL_U, _JEL_V)

    mert_x, mert_y = _mag_jel_helye(theta)
    assert mert_x - _KOZEP_X == pytest.approx(vaszon_x, abs=_TURES_PX)
    assert mert_y - _KOZEP_Y == pytest.approx(vaszon_y, abs=_TURES_PX)


# --- 3. Az árnyék a csempével EGYÜTT fordul ----------------------------------


def _arnyek_sziluettje(theta: float) -> np.ndarray:
    """Az árnyék lenyomata ugyanoda, eltolás és elmosás nélkül."""
    vaszon = np.full((_VASZON, _VASZON, 3), 255, dtype=np.uint8)
    draw_shadow(
        vaszon,
        x=_CSEMPE_X,
        y=_CSEMPE_Y,
        width=_CSEMPE,
        height=_CSEMPE,
        theta=theta,
        params=ShadowParams(offset_x=0.0, offset_y=0.0, blur=0.0, opacity=1.0),
    )
    return vaszon[:, :, 0] < 128


@pytest.mark.parametrize("theta", PROBA_THETAK)
def test_az_arnyek_a_csempevel_egyutt_fordul(theta):
    """Az árnyék nem szakadhat el a képtől.

    Ez az őr a javítás előtt is zöld volt (a két hívó EGYFORMÁN tévedett) —
    a dolga az, hogy a javítás közben ne váljon szét a kettő. Eltolás és
    elmosás nélkül a két sziluettnek fedésben kell lennie."""
    csempe = _sziluett(theta)
    arnyek = _arnyek_sziluettje(theta)
    metszet = float(np.logical_and(csempe, arnyek).sum())
    unio = float(np.logical_or(csempe, arnyek).sum())
    assert unio > 0.0
    assert metszet / unio > 0.97


# --- 4. A TÁROLT `theta` érintetlen ------------------------------------------


def _proba_projekt() -> cxf.CxfProject:
    """Generált minta: forgatott és forgatás nélküli csomópontok, ±előjel."""
    return cxf.CxfProject(
        theme=cxf.PICTUREPILE,
        shadows=True,
        nodes=tuple(
            cxf.CxfNode(
                x=0.1 + 0.1 * i,
                y=0.2,
                w=0.3,
                h=0.25,
                theta=theta,
                scale=640.0,
                src=f"kep{i}.jpg",
            )
            for i, theta in enumerate((0.0, 0.5, -0.5, 0.0894, -0.0894))
        ),
    )


def test_a_cxf_korbejarasa_bajtra_azonos_generalt_mintan():
    """`dumps` → `loads` → `dumps`: a kimenet bájtra ugyanaz."""
    projekt = _proba_projekt()
    elso = cxf.dumps(projekt)
    masodik = cxf.dumps(cxf.loads(elso))
    assert masodik == elso


def test_a_tarolt_theta_a_rendereleskor_sem_valtozik():
    """A tárolt `theta` érintetlen — külön állítás a bájtazonosság mellé.

    Ez fogja meg a „modellben negálom" javítást: az a `.cxf` írását is
    tükrözné, tehát az igazi Picasa **tükrözött** kollázst olvasna vissza.
    A bájtazonosság ezt önmagában NEM fogja meg, ha a negálás egy körben
    oda-vissza megtörténik."""
    projekt = _proba_projekt()
    visszaolvasva = cxf.loads(cxf.dumps(projekt))
    assert [csomopont.theta for csomopont in visszaolvasva.nodes] == [
        csomopont.theta for csomopont in projekt.nodes
    ]


def test_a_rajzolas_nem_nyul_a_csomopontok_thetajahoz():
    """A rajzoló nem írja át a csomópontokat (immutábilis modell)."""
    from picasapy.collage.nodes import CollageNode, draw_nodes

    csomopontok = (
        CollageNode(
            center_x=500.0,
            center_y=500.0,
            width=300.0,
            height=300.0,
            theta=0.5,
            border="noborder",
        ),
    )
    elotte = [csomopont.theta for csomopont in csomopontok]
    vaszon = np.full((_VASZON, _VASZON, 3), 255, dtype=np.uint8)
    draw_nodes(
        vaszon,
        csomopontok,
        [np.full((120, 160, 3), 40, dtype=np.uint8)],
        page_width=_VASZON,
    )
    assert [csomopont.theta for csomopont in csomopontok] == elotte


# --- 5. A valódi nyolc golden fájl (csak a fejlesztői gépen) -----------------


_GOLDEN_ZIP = (
    Path.home()
    / "picasapy-agent/referencia/kollazs-golden/kollazsok-8db-cxf-parral.zip"
)


@pytest.mark.skipif(
    not _GOLDEN_ZIP.exists(),
    reason="a privát golden-anyag nincs a gépen (a nyilvános repóba nem kerülhet)",
)
def test_a_nyolc_golden_cxf_korbejarasa_bajtra_azonos():
    """A valódi nyolc Picasa-`.cxf`: `loads` → `dumps` bájtra azonos.

    A minták a privát repóban élnek (a felhasználó saját fényképei), ezért
    az eset a fejlesztői gépen mér, máshol kihagyja magát. A mérce a #1035
    javítás ELŐTTI állapota: 8 azonos, 0 eltérő."""
    with zipfile.ZipFile(_GOLDEN_ZIP) as csomag:
        nevek = sorted(n for n in csomag.namelist() if n.endswith(".cxf"))
        assert len(nevek) == 8
        for nev in nevek:
            adat = csomag.read(nev)
            projekt = cxf.loads(adat)
            assert cxf.dumps(projekt) == adat, f"{nev}: a körbejárás eltér"
            # és a tárolt szögek is változatlanok
            ujra = cxf.loads(cxf.dumps(projekt))
            assert [n.theta for n in ujra.nodes] == [n.theta for n in projekt.nodes]
