"""A `render_nodes` — a rajzoló szétválasztása elrendezésre és rajzolásra (#942).

Spec: `docs/specs/kollazs-panel-ui-spec.md` **6.5**.

A jegy magva egy WYSIWYG-adósság: a `make_picasa_collage` MAGA számolta ki az
elrendezést, tehát egy kézzel átrendezett vásznat nem tudott kirenderelni —
mentéskor a felhasználó mást kapott volna, mint amit lát. A megoldás a
kettéválasztás (`layout_nodes` → `render_nodes`), és ennek a refaktornak a
rajzon **semmit** nem szabad változtatnia.

Ezért a lap két, egymást kiegészítő őrt tart:

1. **A refaktor ELŐTTI rajzoló, mint orákulum** (`_regi_make_picasa_collage`)
   — a #942 előtti `picasa_render.py` rajzoló-fele szó szerint, befagyasztva.
   Az őr azt állítja, hogy a mai `make_picasa_collage` kimenete **bájtra
   azonos** vele, mind a hat témára, mindhárom keretre, két térköz-állásban.
2. **Viselkedési állítások** a `render_nodes`-ra: hogy tényleg a MEGADOTT
   elhelyezést rajzolja, és nem számol elrendezést.

⚠️ **Miért orákulum, és miért nem beégetett SHA-256.** Az első változat a
kimenet ujjlenyomatait rögzítette számként. Linuxon zöld volt, a
Windows-lábon viszont a Képkupac + Polaroid párosra elbukott: az OpenCV
átméretezése/forgatása **nem bitre azonos** a platformok között. A beégetett
hash tehát többet állított, mint amit ez a jegy ígér — nem azt, hogy „a
refaktor nem változtatott a rajzon", hanem azt, hogy „az OpenCV mindenhol
ugyanazt adja". Az orákulum pontosan a helyes állítást méri: UGYANABBAN a
processzben, ugyanazon az OpenCV-n futtatja a régi és az új utat, és a kettőt
veti össze. Platformfüggetlen, és szigorúbb is — képpontokat hasonlít, nem
kivonatot.

A `_regi_*` függvények **befagyasztott másolatok**: a #942 előtti viselkedést
kódolják, ezért szándékosan nem követik a `picasa_render.py` további
fejlődését. Ha egy későbbi jegy TUDATOSAN változtat a rajzon, ezt az őrt
akkor kell — kimondva, a jegyben indokolva — nyugdíjazni.

## ⚠️ ÁTVEZETÉS: a forgatás iránya (#1035)

A #1035 megfordította a forgatás előjelét a magban (a `.cxf` `theta`-ja az
óramutatóval EGYEZŐ irányt jelent, az OpenCV viszont ellentétesen forgat).
A Képkupac rajza tehát **tudatosan megváltozott** — de ez az őr **nem**
változott vele, és nem is kellett hozzányúlni: az orákulum `_regi_render_pile`
a MAI `render._rotated_paste`-et hívja, nem a forgatás befagyasztott másolatát.
A két oldal ezért együtt mozdult, a bájtazonosság sértetlen maradt (mind a hat
téma, mindhárom keret, két térköz-állás).

⚠️ Ebből az is következik, hogy **ez az őr a forgatás IRÁNYÁRA vak** — azt a
`test_forgatas_iranya_1035.py` méri, a felső él eltolásával és a vászonnal
való összevetéssel.

## ⚠️ ÁTVEZETÉS: a vetett árnyék (#977)

A #977 bekötötte a vetett árnyékot, amit a #942 előtti rajzoló **egyáltalán
nem rajzolt**. Az árnyék két témánál alapból BE van kapcsolva (a
képesség-maszk 14. bitje: **Képkupac** és **Indexkép**), tehát az orákulummal
való összevetés ott **12 esetben** (2 téma × 3 keret × 2 térköz-állás)
szükségszerűen eltérne.

Az őr ezért **nem nyugdíjba megy, hanem élesedik**: a bájtazonossági rács
mostantól kimondottan `shadow=False`-szal mér. Így pontosan azt állítja,
amit a #942 ígért — *az ELRENDEZÉS és a csempe-rajz nem változott* —, és nem
azt, hogy „soha semmi nem kerül a lapra". A tudatos változást külön eset
rögzíti (`test_az_arnyek_a_ket_alapertelmezetten_arnyekos_temat_valtoztatja`):
ott az orákulumtól való eltérés **kötelező**, és csak SÖTÉTÍTÉS lehet.
"""

from __future__ import annotations

import copy
import math
from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.collage.nodes import (
    SHEET_UNITS,
    CollageNode,
    border_growth,
    outer_box,
    photo_box,
    pixels_to_sheet,
    sheet_to_pixels,
)
from picasapy.collage.fitting import MsvcRandom, fit_inside
from picasapy.collage.frames import apply_border
from picasapy.collage.layout import Placement
from picasapy.collage.multi_exposure import blend_multi_exposure
from picasapy.collage.packing import pack
from picasapy.collage.picasa_render import (
    _FRAMEGRID_CENTER as FRAMEGRID_CENTER,
)
from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    _draw_contact_header,
    layout_nodes,
    layout_nodes_for_aspects,
    make_picasa_collage,
    render_nodes,
)
from picasapy.collage.pile import pile_layout, pile_top_left
from picasapy.collage.rects import to_pixel_rects
from picasapy.collage.regular_grid import regular_grid_rects, regular_grid_shape
from picasapy.collage.render import _paste, _rotated_paste, fit_to_frame
from picasapy.collage.themes import (
    BORDER_THEMES,
    COLLAGE_THEMES,
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    NOBORDER,
    PICTUREGRID,
    PICTUREPILE,
    POLAROID,
    REGULARGRID,
    WHITEBORDER,
)

# --- Segédek ----------------------------------------------------------------


def _ir_kepet(utvonal, szelesseg, magassag, szin):
    """Egyszínű BGR próbakép a lemezre."""
    kep = np.empty((magassag, szelesseg, 3), dtype=np.uint8)
    kep[:, :] = szin
    assert cv2.imwrite(str(utvonal), kep)
    return utvonal


def _mintakepek(mappa, darab=7):
    """A bájtazonossági ujjlenyomatokhoz használt, RÖGZÍTETT képsorozat.

    A méretek és a színek szándékosan „csúnyák" (páratlan oldalak, eltérő
    oldalarányok): így a kerekítési határesetek is beleesnek a mérésbe."""
    utak = []
    for i in range(darab):
        szeles, magas = 60 + i * 17, 40 + (i * 23) % 70
        kep = np.zeros((magas, szeles, 3), dtype=np.uint8)
        kep[:, :, 0] = (i * 37) % 256
        kep[:, :, 1] = (i * 91) % 256
        kep[:, :, 2] = (i * 13) % 256
        kep[: magas // 2, : szeles // 2] = (255, 255, 255)
        ut = mappa / f"k{i}.png"
        assert cv2.imwrite(str(ut), kep)
        utak.append(ut)
    return utak


# --- 1. Bájtazonosság: a refaktor nem változtat a rajzon -------------------
#
# Az orákulum: a #942 ELŐTTI rajzoló, szó szerint. Az `_regi_` előtag jelzi,
# hogy befagyasztott másolat — ne igazítsd a mai kódhoz.


def _regi_place_in_cells(canvas, images, rects, settings, *, fill=True):
    """A #942 előtti `_place_in_cells` — a képek a cellákba illesztve."""
    cells = to_pixel_rects(
        rects, settings.width, settings.height, settings.effective_spacing
    )
    for image, cell in zip(images, cells, strict=False):
        width = max(1, cell.x1 - cell.x0)
        height = max(1, cell.y1 - cell.y0)
        tile = apply_border(
            fit_to_frame(image, width, height, fill=fill), settings.effective_border
        )
        offset_x = cell.x0 + (width - tile.shape[1]) // 2
        offset_y = cell.y0 + (height - tile.shape[0]) // 2
        _paste(canvas, tile, offset_x, offset_y)


def _regi_render_pile(canvas, images, settings):
    """A #942 előtti `_render_pile` — a Képkupac szórása és forgatása."""
    rng = MsvcRandom(settings.seed)
    places = pile_layout(len(images), settings.width, settings.height, rng)
    for image, place in zip(images, places, strict=False):
        oldal = max(1, place.size)
        magassag, szelesseg = image.shape[:2]
        cel_w, cel_h = fit_inside(szelesseg, magassag, oldal, oldal)
        tile = apply_border(
            fit_to_frame(image, max(1, cel_w), max(1, cel_h), fill=False),
            settings.effective_border,
        )
        # ⚠️ #1045: a beszorítás a `_pile_nodes`-ban él, ez a referencia-ág
        # viszont közvetlenül a `pile_layout`-ból dolgozik, tehát megkerülné.
        # Ha ez az ág nem szorít be, a két út SZÉTCSÚSZIK, és az őr olyan
        # eltérésre bukik, ami szándékos viselkedésváltozás — nem regresszió.
        #
        # A beszorítást ITT is el kell végezni, ugyanazzal a képlettel (a
        # KERETES csempe méretével), nem a javítást gyengíteni: az
        # visszahozná a kilógó képeket a felhasználónál.
        kozep_x = min(
            max(place.center_x, tile.shape[1] * 0.5),
            settings.width - tile.shape[1] * 0.5,
        )
        kozep_y = min(
            max(place.center_y, tile.shape[0] * 0.5),
            settings.height - tile.shape[0] * 0.5,
        )
        x = pile_top_left(kozep_x, tile.shape[1], settings.width, settings.width)
        y = pile_top_left(kozep_y, tile.shape[0], settings.height, settings.height)
        _rotated_paste(
            canvas,
            tile,
            Placement(
                x=round(x),
                y=round(y),
                width=tile.shape[1],
                height=tile.shape[0],
                angle=math.degrees(place.theta),
            ),
        )


def _regi_make_picasa_collage(sources, settings):
    """A #942 ELŐTTI `make_picasa_collage`, befagyasztva. Csak a képet adja."""
    paths = [Path(s) for s in sources]
    decoded = [
        cv2.imdecode(np.fromfile(str(ut), dtype=np.uint8), cv2.IMREAD_COLOR)
        for ut in paths
        if ut.exists()
    ]
    decoded = [kep for kep in decoded if kep is not None]

    canvas = np.empty((settings.height, settings.width, 3), dtype=np.uint8)
    canvas[:, :] = settings.background
    if not decoded:
        return canvas

    aspects = [kep.shape[1] / kep.shape[0] for kep in decoded]
    if settings.theme == MULTIEXP:
        canvas = blend_multi_exposure(
            decoded, settings.width, settings.height, settings.background
        )
    elif settings.theme == PICTUREPILE:
        _regi_render_pile(canvas, decoded, settings)
    elif settings.theme in (PICTUREGRID, FRAMEGRID):
        rogzitett = (
            settings.frame_center
            if settings.theme == FRAMEGRID
            and settings.frame_center is not None
            and 0 <= settings.frame_center < len(decoded)
            else None
        )
        if rogzitett is None:
            rects = pack(
                aspects, settings.width / settings.height, MsvcRandom(settings.seed)
            )
            _regi_place_in_cells(canvas, decoded, rects, settings)
        else:
            tobbi = [kep for i, kep in enumerate(decoded) if i != rogzitett]
            if tobbi:
                rects = pack(
                    [kep.shape[1] / kep.shape[0] for kep in tobbi],
                    settings.width / settings.height,
                    MsvcRandom(settings.seed),
                )
                _regi_place_in_cells(canvas, tobbi, rects, settings)
            _regi_place_in_cells(
                canvas, [decoded[rogzitett]], (FRAMEGRID_CENTER,), settings
            )
    elif settings.theme == REGULARGRID:
        sorok, oszlopok = regular_grid_shape(aspects, settings.width, settings.height)
        rects = regular_grid_rects(len(decoded), sorok, oszlopok)
        _regi_place_in_cells(canvas, decoded, rects, settings)
    elif settings.theme == CONTACTSHEET:
        sav = _draw_contact_header(canvas, settings)
        also = settings.height - sav
        alvaszon = np.empty((max(1, also), settings.width, 3), dtype=np.uint8)
        alvaszon[:, :] = settings.background
        alsobeallitas = PicasaCollageSettings(
            theme=REGULARGRID,
            border=settings.border,
            width=settings.width,
            height=max(16, also),
            background=settings.background,
            spacing=settings.spacing,
            seed=settings.seed,
        )
        sorok, oszlopok = regular_grid_shape(aspects, settings.width, max(1, also))
        rects = regular_grid_rects(len(decoded), sorok, oszlopok)
        _regi_place_in_cells(alvaszon, decoded, rects, alsobeallitas, fill=False)
        canvas[sav : sav + alvaszon.shape[0], :] = alvaszon
    else:
        raise AssertionError(f"ismeretlen téma: {settings.theme}")
    return canvas


#: A mérés rácsa: mind a hat téma × mindhárom keret × két térköz-állás.
BAJTAZONOSSAG_ESETEI = [
    (tema, keret, terkoz)
    for tema in COLLAGE_THEMES
    for keret in BORDER_THEMES
    for terkoz in (0.0, 0.4)
]


@pytest.mark.parametrize("kulcs", BAJTAZONOSSAG_ESETEI)
def test_a_refaktor_nem_valtoztat_a_rajzon(tmp_path, kulcs):
    """A `make_picasa_collage` kimenete BÁJTAZONOS a refaktor előttivel.

    Az összevetés UGYANABBAN a processzben, ugyanazon az OpenCV-n fut, ezért
    az eredmény nem függ a platformtól — csak attól, változott-e a rajz."""
    tema, keret, terkoz = kulcs
    forrasok = _mintakepek(tmp_path)
    beallitas = PicasaCollageSettings(
        theme=tema,
        border=keret,
        width=407,
        height=311,
        spacing=terkoz,
        seed=12345,
        background=(30, 60, 90),
        caption="Proba",
        # #977: az orákulum a vetett árnyékot NEM ismeri, ezért az őr
        # kimondottan árnyék nélkül mér — így az állítása továbbra is az,
        # hogy az ELRENDEZÉS és a csempe-rajz változatlan
        shadow=False,
    )
    most = make_picasa_collage(forrasok, beallitas).image
    regen = _regi_make_picasa_collage(forrasok, beallitas)
    eltero = int(np.count_nonzero(np.any(most != regen, axis=2)))
    assert eltero == 0, (
        f"A(z) {tema}/{keret} (térköz {terkoz}) rajza megváltozott: "
        f"{eltero} képpont tér el a #942 előtti kimenettől."
    )


#: A két téma, amelynél az árnyék ALAPBÓL be van kapcsolva (maszk 14. bitje).
ARNYEKOS_ALAPBOL = (PICTUREPILE, CONTACTSHEET)


@pytest.mark.parametrize("tema", ARNYEKOS_ALAPBOL)
@pytest.mark.parametrize("keret", sorted(BORDER_THEMES))
def test_az_arnyek_a_ket_alapertelmezetten_arnyekos_temat_valtoztatja(
    tmp_path, tema, keret
):
    """#977: a Képkupac és az Indexkép rajza SZÁNDÉKOSAN eltér az orákulumtól.

    Ez az eset az árnyék bekötésének kimondott ára: a #942 előtti rajzoló nem
    ismerte a vetett árnyékot, ez a kettő pedig alapból árnyékos. Az eltérés
    tehát **kötelező** — de csak SÖTÉTÍTÉS lehet: az árnyék fekete keverés,
    tehát egyetlen képpontot sem világosíthat, és a geometriát sem
    mozdíthatja el. Ha valaha egy csempe elcsúszik, itt VILÁGOSABB képpont is
    megjelenne, és az eset bukna."""
    forrasok = _mintakepek(tmp_path)
    kozos = dict(
        theme=tema,
        border=keret,
        width=407,
        height=311,
        seed=12345,
        background=(200, 210, 220),
        caption="Proba",
    )
    arnyekkal = make_picasa_collage(
        forrasok, PicasaCollageSettings(**kozos, shadow=True)
    ).image
    regen = _regi_make_picasa_collage(
        forrasok, PicasaCollageSettings(**kozos, shadow=False)
    )

    assert not np.array_equal(arnyekkal, regen), (
        f"a(z) {tema}/{keret} árnyéka nem jelent meg — pedig alapból BE van"
    )
    assert np.all(arnyekkal.astype(int) <= regen.astype(int)), (
        "az árnyék csak sötétíthet: világosabb képpont geometriai elcsúszást "
        "jelentene, nem árnyékot"
    )
    # és a kikapcsolt árnyék visszaadja a bájtazonosságot
    nelkule = make_picasa_collage(
        forrasok, PicasaCollageSettings(**kozos, shadow=False)
    ).image
    assert np.array_equal(nelkule, regen)


def test_minden_tema_es_keret_le_van_fedve():
    """A mérés rácsa mind a hat témát és mindhárom keretet lefedi.

    Enélkül egy új téma némán kimaradhatna az őrből."""
    lefedett_temak = {eset[0] for eset in BAJTAZONOSSAG_ESETEI}
    lefedett_keretek = {eset[1] for eset in BAJTAZONOSSAG_ESETEI}
    assert lefedett_temak == set(COLLAGE_THEMES)
    assert lefedett_keretek == set(BORDER_THEMES)


# --- 2. A lapegység-koordinátarendszer (spec 6.1) ---------------------------


def test_a_lapegyseg_mindket_tengelyen_ugyanaz_az_oszto():
    """`képernyő_y` osztója is a lap SZÉLESSÉGE — a lap nem torzít, csak méretez."""
    assert sheet_to_pixels(SHEET_UNITS, 800) == 800.0
    # ugyanaz az érték ugyanannyi képpont, függetlenül attól, melyik tengelyen
    # kérdezzük: a függvénynek nincs is tengely-paramétere
    assert sheet_to_pixels(512.0, 800) == 400.0


def test_a_lapegyseg_oda_vissza_valtasa_pontos():
    for lapszelesseg in (320, 407, 800, 1600, 3000):
        for kepont in (0, 1, 37, 199, 313):
            vissza = sheet_to_pixels(pixels_to_sheet(kepont, lapszelesseg), lapszelesseg)
            assert vissza == pytest.approx(kepont, abs=1e-9)


@pytest.mark.parametrize("rossz", [0, -1])
def test_a_lapegyseg_valtas_ervenytelen_lapszelessegre_hibat_dob(rossz):
    with pytest.raises(ValueError):
        sheet_to_pixels(1.0, rossz)
    with pytest.raises(ValueError):
        pixels_to_sheet(1.0, rossz)


# --- 3. A keret külső és belső doboza ---------------------------------------


@pytest.mark.parametrize("keret", sorted(BORDER_THEMES))
def test_a_kulso_doboz_megforditasa_pontos(keret):
    """`photo_box(outer_box(w, h)) == (w, h)` — enélkül a keretes kép a vásznon
    és a mentett képen más méretű lenne."""
    for szeles in range(1, 260, 3):
        for magas in range(1, 260, 7):
            kulso = outer_box(szeles, magas, keret)
            assert photo_box(*kulso, keret) == (szeles, magas), (
                f"{keret}: {szeles}×{magas} → {kulso} → "
                f"{photo_box(*kulso, keret)}"
            )


def test_a_keret_nelkuli_doboz_nem_no():
    assert border_growth(100, 80, NOBORDER) == (0, 0)
    assert outer_box(100, 80, NOBORDER) == (100, 80)
    assert photo_box(100, 80, NOBORDER) == (100, 80)


def test_a_feher_szegely_szimmetrikusan_no():
    """A fehér szegély mind a négy oldalon egyforma — a növekmény páros."""
    szeles_no, magas_no = border_growth(100, 80, WHITEBORDER)
    assert szeles_no == magas_no
    assert szeles_no % 2 == 0


def test_a_polaroid_lefele_tobbet_no_mint_felfele():
    """A Polaroid alul feliratsávot hagy — a függőleges növekmény NAGYOBB."""
    szeles_no, magas_no = border_growth(100, 100, POLAROID)
    assert magas_no > szeles_no


@pytest.mark.parametrize("hibas", [(0, 10), (10, 0), (-1, 10)])
def test_a_keretgeometria_ervenytelen_meretre_hibat_dob(hibas):
    with pytest.raises(ValueError):
        border_growth(hibas[0], hibas[1], WHITEBORDER)


def test_ismeretlen_keret_hibat_dob():
    with pytest.raises(ValueError, match="Ismeretlen képkeret"):
        border_growth(10, 10, "nincs-ilyen")


# --- 4. A csomópont-modell --------------------------------------------------


def test_a_csomopont_ervenytelen_keretet_elutasit():
    with pytest.raises(ValueError, match="Ismeretlen képkeret"):
        CollageNode(width=10, height=10, border="nincs-ilyen")


@pytest.mark.parametrize("meret", [(0.0, 10.0), (10.0, 0.0), (-1.0, 10.0)])
def test_a_csomopont_ervenytelen_meretet_elutasit(meret):
    with pytest.raises(ValueError, match="Érvénytelen csomópont-méret"):
        CollageNode(width=meret[0], height=meret[1])


# --- 5. A render_nodes a MEGADOTT elhelyezést rajzolja ----------------------


def _egyszinu_csomopont(ut, *, kozep_x, kozep_y, oldal=256.0):
    return CollageNode(
        path=ut,
        center_x=kozep_x,
        center_y=kozep_y,
        width=oldal,
        height=oldal,
        border=NOBORDER,
        fill=True,
    )


def _befoglalo(kep, hatter):
    """A háttértől eltérő képpontok befoglaló téglalapja (x0, y0, x1, y1)."""
    maszk = np.any(kep != np.array(hatter, dtype=np.uint8), axis=2)
    if not maszk.any():
        return None
    sorok = np.flatnonzero(maszk.any(axis=1))
    oszlopok = np.flatnonzero(maszk.any(axis=0))
    return (
        int(oszlopok[0]),
        int(sorok[0]),
        int(oszlopok[-1]) + 1,
        int(sorok[-1]) + 1,
    )


def test_a_csomopont_oda_kerul_ahova_a_kozeppontja_mutat(tmp_path):
    """A megadott elhelyezés PONTOSAN a megadott helyre rajzolódik."""
    hatter = (0, 0, 0)
    ut = _ir_kepet(tmp_path / "piros.png", 40, 40, (0, 0, 255))
    beallitas = PicasaCollageSettings(width=400, height=300, background=hatter)
    # 256 lapegység = 100 képpont; a középpont (128, 128) → (50, 50) képpont
    csomopont = _egyszinu_csomopont(ut, kozep_x=128.0, kozep_y=128.0)
    jelentes = render_nodes([csomopont], beallitas)
    assert _befoglalo(jelentes.image, hatter) == (0, 0, 100, 100)


def test_a_csomopont_elmozditasa_a_kimeneten_is_elmozdul(tmp_path):
    """A jegy „Kész, ha" pontja: egy csomópont elmozdítása a képen is látszik."""
    hatter = (0, 0, 0)
    ut = _ir_kepet(tmp_path / "piros.png", 40, 40, (0, 0, 255))
    beallitas = PicasaCollageSettings(width=400, height=300, background=hatter)

    elotte = render_nodes(
        [_egyszinu_csomopont(ut, kozep_x=128.0, kozep_y=128.0)], beallitas
    )
    # +256 lapegység = +100 képpont vízszintesen
    utana = render_nodes(
        [_egyszinu_csomopont(ut, kozep_x=384.0, kozep_y=128.0)], beallitas
    )

    assert _befoglalo(elotte.image, hatter) == (0, 0, 100, 100)
    assert _befoglalo(utana.image, hatter) == (100, 0, 200, 100)


def _proba_csomopontok(ut):
    return [
        CollageNode(
            path=ut,
            center_x=300.0,
            center_y=220.0,
            width=200.0,
            height=180.0,
            theta=0.3,
            border=WHITEBORDER,
        ),
        CollageNode(
            path=ut, center_x=700.0, center_y=500.0, width=260.0, height=260.0
        ),
    ]


def test_a_render_nodes_nem_szamol_elrendezest(tmp_path):
    """UGYANAZ a csomópontlista UGYANOTT rajzol, bármelyik téma van beállítva.

    Ez a jegy lényege: a rajzoló nem nyúl a téma pakolójához. Ha bármelyik
    téma befolyásolná a HELYEKET, a kézi elrendezés mentéskor elveszne.

    ⚠️ **#977: az eset át lett írva, kimondva.** Eredetileg a hat téma
    kimenetének bájtazonosságát állította. Az árnyék bekötése óta ez már
    TÖBBET állítana a kelleténél: az árnyék az eredetiben **témánként
    paraméterezett** (négy készlet, spec 9/b.2), tehát a témának *látszania
    is kell* a képen. Ami változatlan — és amit ez az eset azóta mér —, az az
    ELRENDEZÉS: árnyék nélkül a hat téma rajza továbbra is bájtazonos."""
    ut = _ir_kepet(tmp_path / "kek.png", 30, 50, (255, 0, 0))
    csomopontok = _proba_csomopontok(ut)
    kepek = [
        render_nodes(
            csomopontok,
            PicasaCollageSettings(
                theme=tema, width=400, height=300, spacing=0.7, shadow=False
            ),
        ).image
        for tema in COLLAGE_THEMES
    ]
    for kep in kepek[1:]:
        assert np.array_equal(kep, kepek[0])


def test_az_arnyek_viszont_temankent_MAS(tmp_path):
    """#977: bekapcsolt árnyékkal a témának LÁTSZANIA kell a képen.

    A négy paraméterkészlet nem díszítés: a Mozaik és a Rács árnyéka
    máshova és máshogy esik. Ha valaki egyetlen közös készletet ír, ez az
    eset bukik — ugyanaz a kép jönne ki mindkét témára."""
    ut = _ir_kepet(tmp_path / "feher.png", 30, 50, (255, 255, 255))
    # csak a TENGELYPÁRHUZAMOS csomópont: a forgatott csempe éle a
    # `warpAffine` miatt magától is sötét szegélyt kap, ami elnyomná a mérést
    csomopontok = _proba_csomopontok(ut)[1:]

    def _rajz(tema):
        return render_nodes(
            csomopontok,
            PicasaCollageSettings(
                theme=tema,
                width=400,
                height=300,
                background=(255, 255, 255),
                shadow=True,
            ),
        ).image

    mozaik, racs = _rajz(PICTUREGRID), _rajz(REGULARGRID)
    assert not np.array_equal(mozaik, racs)
    # a Rács 60 %-os árnyéka SÖTÉTEBB a Mozaik 40 %-osánál
    assert int(racs.min()) < int(mozaik.min())


def test_a_lista_sorrendje_a_rajzolasi_sorrend(tmp_path):
    """A 0. index van LEGALUL, az utolsó legfelül (`canvas.py` is ezt tartja)."""
    hatter = (0, 0, 0)
    also = _ir_kepet(tmp_path / "also.png", 20, 20, (0, 0, 255))
    felso = _ir_kepet(tmp_path / "felso.png", 20, 20, (0, 255, 0))
    beallitas = PicasaCollageSettings(width=400, height=300, background=hatter)
    csomopontok = [
        _egyszinu_csomopont(also, kozep_x=128.0, kozep_y=128.0),
        _egyszinu_csomopont(felso, kozep_x=128.0, kozep_y=128.0),
    ]
    jelentes = render_nodes(csomopontok, beallitas)
    # a fedésben lévő közös pont a LISTA VÉGÉN álló kép színét viseli
    assert tuple(int(c) for c in jelentes.image[50, 50]) == (0, 255, 0)


def test_a_forgatas_tenylegesen_elforgat(tmp_path):
    """`theta` ≠ 0 → a csempe sarkai kilógnak a tengelypárhuzamos dobozból."""
    hatter = (0, 0, 0)
    ut = _ir_kepet(tmp_path / "piros.png", 40, 40, (0, 0, 255))
    beallitas = PicasaCollageSettings(width=400, height=300, background=hatter)
    alap = _egyszinu_csomopont(ut, kozep_x=512.0, kozep_y=384.0)
    forgatott = CollageNode(
        path=ut,
        center_x=512.0,
        center_y=384.0,
        width=256.0,
        height=256.0,
        theta=math.radians(30.0),
    )
    egyenes_doboz = _befoglalo(render_nodes([alap], beallitas).image, hatter)
    forgatott_doboz = _befoglalo(render_nodes([forgatott], beallitas).image, hatter)
    assert forgatott_doboz != egyenes_doboz
    # a 30°-kal döntött négyzet befoglalója NAGYOBB
    assert forgatott_doboz[2] - forgatott_doboz[0] > egyenes_doboz[2] - egyenes_doboz[0]


def test_a_csomopont_merete_a_lap_meretevel_skalazodik(tmp_path):
    """Ugyanaz a csomópont kétszeres lapon kétszeres képpontméretet kap.

    Ez a lapegység létjogosultsága: az élő előnézet és a mentett nagy kép
    UGYANAZ a kollázs."""
    hatter = (0, 0, 0)
    ut = _ir_kepet(tmp_path / "piros.png", 40, 40, (0, 0, 255))
    csomopont = _egyszinu_csomopont(ut, kozep_x=256.0, kozep_y=256.0)
    kicsi = render_nodes(
        [csomopont], PicasaCollageSettings(width=400, height=300, background=hatter)
    )
    nagy = render_nodes(
        [csomopont], PicasaCollageSettings(width=800, height=600, background=hatter)
    )
    kicsi_doboz = _befoglalo(kicsi.image, hatter)
    nagy_doboz = _befoglalo(nagy.image, hatter)
    assert (kicsi_doboz[2] - kicsi_doboz[0]) * 2 == nagy_doboz[2] - nagy_doboz[0]
    assert (kicsi_doboz[3] - kicsi_doboz[1]) * 2 == nagy_doboz[3] - nagy_doboz[1]


# --- 6. Hiányzó képek (spec 9.4) --------------------------------------------


def test_a_hianyzo_kep_helykitolto_csempet_kap(tmp_path):
    """A nem található kép NEM tűnik el némán — a felhasználó látja a lyukat."""
    hatter = (0, 0, 0)
    beallitas = PicasaCollageSettings(width=400, height=300, background=hatter)
    csomopont = _egyszinu_csomopont(tmp_path / "nincs-ilyen.jpg", kozep_x=128.0, kozep_y=128.0)
    jelentes = render_nodes([csomopont], beallitas)
    assert _befoglalo(jelentes.image, hatter) == (0, 0, 100, 100)
    assert jelentes.missing == (tmp_path / "nincs-ilyen.jpg",)
    assert jelentes.used == ()
    assert jelentes.reasons == ("a fájl nem található",)


def test_a_missing_jelzo_a_lemezt_meg_sem_erinti(tmp_path):
    """`missing=True` → helykitöltő akkor is, ha a fájl történetesen létezne.

    A vászon a `.cxf` betöltésekor már tudja, mi hiányzik; ne kelljen újra
    lemezhez nyúlnia."""
    hatter = (0, 0, 0)
    ut = _ir_kepet(tmp_path / "letezik.png", 40, 40, (0, 0, 255))
    beallitas = PicasaCollageSettings(width=400, height=300, background=hatter)
    csomopont = CollageNode(
        path=ut, center_x=128.0, center_y=128.0, width=256.0, height=256.0, missing=True
    )
    jelentes = render_nodes([csomopont], beallitas)
    assert jelentes.missing == (ut,)
    # a helykitöltő NEM a kép színe (a kép tiszta piros volt)
    assert tuple(int(c) for c in jelentes.image[50, 50]) != (0, 0, 255)


def test_a_nem_dekodolhato_kep_kimarad_de_nem_all_meg_a_munka(tmp_path):
    hatter = (0, 0, 0)
    romlott = tmp_path / "romlott.jpg"
    romlott.write_bytes(b"ez nem kep")
    jo = _ir_kepet(tmp_path / "jo.png", 40, 40, (0, 0, 255))
    beallitas = PicasaCollageSettings(width=400, height=300, background=hatter)
    jelentes = render_nodes(
        [
            _egyszinu_csomopont(romlott, kozep_x=128.0, kozep_y=128.0),
            _egyszinu_csomopont(jo, kozep_x=640.0, kozep_y=128.0),
        ],
        beallitas,
    )
    assert jelentes.used == (jo,)
    assert jelentes.skipped == (romlott,)
    assert jelentes.missing == ()


def test_az_ut_nelkuli_csomopont_helykitoltot_kap(tmp_path):
    """A `.cxf`-ben lehet útvonal nélküli csomópont — az sem borítja fel a rajzot."""
    hatter = (0, 0, 0)
    beallitas = PicasaCollageSettings(width=400, height=300, background=hatter)
    csomopont = CollageNode(
        center_x=128.0, center_y=128.0, width=256.0, height=256.0
    )
    jelentes = render_nodes([csomopont], beallitas)
    assert _befoglalo(jelentes.image, hatter) == (0, 0, 100, 100)
    assert jelentes.skipped == ()


# --- 7. Képfelirat a Polaroid-kereten (spec 6.3) ----------------------------


def test_a_kepfelirat_csak_a_polaroid_kereten_jelenik_meg(tmp_path):
    ut = _ir_kepet(tmp_path / "szurke.png", 60, 60, (128, 128, 128))
    beallitas = PicasaCollageSettings(width=600, height=400, background=(0, 0, 0))

    def _rajzol(keret, felirat):
        csomopont = CollageNode(
            path=ut,
            center_x=512.0,
            center_y=341.0,
            width=400.0,
            height=460.0,
            border=keret,
            caption=felirat,
            fill=False,
        )
        return render_nodes([csomopont], beallitas).image

    polaroid_felirattal = _rajzol(POLAROID, "Nyaralas")
    polaroid_felirat_nelkul = _rajzol(POLAROID, "")
    feher_felirattal = _rajzol(WHITEBORDER, "Nyaralas")
    feher_felirat_nelkul = _rajzol(WHITEBORDER, "")

    assert not np.array_equal(polaroid_felirattal, polaroid_felirat_nelkul)
    assert np.array_equal(feher_felirattal, feher_felirat_nelkul)


# --- 8. Egy rajzoló, két hívó ----------------------------------------------


@pytest.mark.parametrize("tema", [PICTUREPILE, PICTUREGRID, REGULARGRID])
def test_a_ket_hivo_ugyanazt_a_kepet_adja(tmp_path, tema):
    """`layout_nodes` + `render_nodes` == `make_picasa_collage`.

    Ez az állítás mondja ki, hogy tényleg EGY rajzoló van: a mentés
    ugyanazon az úton megy, mint az élő vászon."""
    forrasok = _mintakepek(tmp_path, darab=5)
    beallitas = PicasaCollageSettings(
        theme=tema, width=407, height=311, seed=99, background=(20, 40, 60)
    )
    egyben = make_picasa_collage(forrasok, beallitas)

    kepek = [cv2.imread(str(ut), cv2.IMREAD_COLOR) for ut in forrasok]
    csomopontok = layout_nodes(kepek, forrasok, beallitas)
    ketto_lepesben = render_nodes(csomopontok, beallitas)

    assert np.array_equal(egyben.image, ketto_lepesben.image)


# ⚠️ #989: ez az eset ÁTÍRÓDOTT. A #942-es változat azt rögzítette, hogy a
# Többszörös exponálásra és az Indexképre a `layout_nodes` HIBÁT dob („nincs
# csomópont-elrendezés"). Ez a MI korábbi tervezési döntésünk volt, nem az
# eredeti viselkedése — és pontosan ez tette lehetetlenné, hogy a kollázs-panel
# vászna a témát kövesse (#989: a hat témából csak a Képkupac elrendezése
# látszott). Mindkét témának VAN geometriája: az Indexkép a fejlécsáv alatti
# rácsba rendez, a Többszörös exponálás pedig minden képet a teljes lapra
# igazít és középre tesz (`multi_exposure._centered`). A hibadobás helyére
# ezért az kerül, ami tényleg igaz: ismeretlen témára szól hangosan.
@pytest.mark.parametrize("tema", [MULTIEXP, CONTACTSHEET])
def test_a_ket_kulonleges_temanak_is_van_pakoloja(tmp_path, tema):
    """Az Indexkép és a Többszörös exponálás geometriája is csomópontos.

    A `make_picasa_collage` RAJZOLÁSA külön úton megy (a fejléc és a keverés
    miatt), de az ELRENDEZÉS innen jön — enélkül a panel kénytelen volna
    sajátot kitalálni, és a vászon mást mutatna, mint a mentett kép."""
    forrasok = _mintakepek(tmp_path, darab=4)
    kepek = [cv2.imread(str(ut), cv2.IMREAD_COLOR) for ut in forrasok]
    beallitas = PicasaCollageSettings(theme=tema, width=400, height=300)
    csomopontok = layout_nodes(kepek, forrasok, beallitas)
    assert len(csomopontok) == len(forrasok)
    assert all(n.width > 0.0 and n.height > 0.0 for n in csomopontok)


def test_az_ismeretlen_tema_hangosan_szol():
    """Néma üres lista helyett hiba: aki ide ér, elgépelte a témát.

    A `PicasaCollageSettings` maga is szűr, ezért az ismeretlen témát az
    ellenőrzés MEGKERÜLÉSÉVEL csempésszük be — a pakoló saját őre így is a
    helyén marad."""
    beallitas = PicasaCollageSettings(theme=PICTUREGRID, width=400, height=300)
    hamis = copy.copy(beallitas)
    object.__setattr__(hamis, "theme", "kollazs2000")
    with pytest.raises(ValueError, match="nincs csomópont-elrendezés"):
        layout_nodes_for_aspects([1.0], ["/k/a.jpg"], hamis)


def test_a_layout_nodes_kepszamot_es_utvonalszamot_osszeveti():
    beallitas = PicasaCollageSettings(theme=PICTUREGRID, width=400, height=300)
    with pytest.raises(ValueError, match="tartoznia kell útvonalnak"):
        layout_nodes([np.zeros((4, 4, 3), np.uint8)], [], beallitas)


def test_a_kezi_atrendezes_tullep_a_gepi_elrendezesen(tmp_path):
    """A jegy WYSIWYG-adóssága: egy KÉZZEL elmozdított csomópont máshova kerül.

    A `make_picasa_collage` a téma pakolóját futtatja; ha ugyanazokat a
    csomópontokat elmozdítjuk és a `render_nodes`-nak adjuk, a kimenetnek
    követnie kell a KÉZI helyzetet."""
    forrasok = _mintakepek(tmp_path, darab=3)
    beallitas = PicasaCollageSettings(
        theme=PICTUREGRID, width=407, height=311, seed=7, background=(0, 0, 0)
    )
    kepek = [cv2.imread(str(ut), cv2.IMREAD_COLOR) for ut in forrasok]
    csomopontok = layout_nodes(kepek, forrasok, beallitas)

    gepi = render_nodes(csomopontok, beallitas).image
    # az elsőt elhúzzuk 40 lapegységgel jobbra és lefelé
    elmozgatott = [
        CollageNode(
            path=csomopontok[0].path,
            center_x=csomopontok[0].center_x + 40.0,
            center_y=csomopontok[0].center_y + 40.0,
            width=csomopontok[0].width,
            height=csomopontok[0].height,
            theta=csomopontok[0].theta,
            border=csomopontok[0].border,
            fill=csomopontok[0].fill,
        ),
        *csomopontok[1:],
    ]
    kezi = render_nodes(elmozgatott, beallitas).image
    assert not np.array_equal(gepi, kezi)
