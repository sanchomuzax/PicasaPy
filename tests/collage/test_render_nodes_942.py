"""A `render_nodes` — a rajzoló szétválasztása elrendezésre és rajzolásra (#942).

Spec: `docs/specs/kollazs-panel-ui-spec.md` **6.5**.

A jegy magva egy WYSIWYG-adósság: a `make_picasa_collage` MAGA számolta ki az
elrendezést, tehát egy kézzel átrendezett vásznat nem tudott kirenderelni —
mentéskor a felhasználó mást kapott volna, mint amit lát. A megoldás a
kettéválasztás (`layout_nodes` → `render_nodes`), és ennek a refaktornak a
rajzon **semmit** nem szabad változtatnia.

Ezért a lap két, egymást kiegészítő őrt tart:

1. **Bájtazonossági ujjlenyomatok** — a `make_picasa_collage` kimenetének
   SHA-256-a mind a hat témára, mindhárom keretre, két térköz-állásban. A
   számok a refaktor ELŐTTI kódból származnak; ha a refaktor bármit
   elmozdított volna, ezek buknak.
2. **Viselkedési állítások** a `render_nodes`-ra: hogy tényleg a MEGADOTT
   elhelyezést rajzolja, és nem számol elrendezést.
"""

from __future__ import annotations

import hashlib
import math

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
from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    layout_nodes,
    make_picasa_collage,
    render_nodes,
)
from picasapy.collage.themes import (
    BORDER_THEMES,
    COLLAGE_THEMES,
    CONTACTSHEET,
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


def _ujjlenyomat(kep):
    return hashlib.sha256(kep.tobytes()).hexdigest()[:16]


# --- 1. Bájtazonosság: a refaktor nem változtat a rajzon ---------------------

#: A `make_picasa_collage` kimenetének ujjlenyomata a #942 refaktora ELŐTT.
#:
#: A mérés paraméterei: `_mintakepek()` hét képe, 407 × 311-es lap, `seed=12345`,
#: háttér `(30, 60, 90)`, `caption="Proba"`. A kulcs `(téma, keret, térköz)`.
#:
#: ⚠️ Ezeket a számokat **tilos** „hozzáigazítani" egy bukó futáshoz. Ha
#: buknak, a refaktor elmozdított valamit a rajzon — az a hiba, nem a szám.
#: Szándékos rajz-változtatáskor (új jegy!) kell csak újramérni őket.
ELVART_UJJLENYOMATOK = {
    ("picturepile", "noborder", 0.0): "4e9bf8f2ee48fd1e",
    ("picturepile", "noborder", 0.4): "4e9bf8f2ee48fd1e",
    ("picturepile", "whiteborder", 0.0): "b8397989aa02ccea",
    ("picturepile", "whiteborder", 0.4): "b8397989aa02ccea",
    ("picturepile", "polaroid", 0.0): "480e5f069f6926f6",
    ("picturepile", "polaroid", 0.4): "480e5f069f6926f6",
    ("picturegrid", "noborder", 0.0): "b337715bd19c356b",
    ("picturegrid", "noborder", 0.4): "0bc8aedb8e2bd45b",
    ("picturegrid", "whiteborder", 0.0): "b337715bd19c356b",
    ("picturegrid", "whiteborder", 0.4): "0bc8aedb8e2bd45b",
    ("picturegrid", "polaroid", 0.0): "b337715bd19c356b",
    ("picturegrid", "polaroid", 0.4): "0bc8aedb8e2bd45b",
    ("framegrid", "noborder", 0.0): "b337715bd19c356b",
    ("framegrid", "noborder", 0.4): "0bc8aedb8e2bd45b",
    ("framegrid", "whiteborder", 0.0): "b337715bd19c356b",
    ("framegrid", "whiteborder", 0.4): "0bc8aedb8e2bd45b",
    ("framegrid", "polaroid", 0.0): "b337715bd19c356b",
    ("framegrid", "polaroid", 0.4): "0bc8aedb8e2bd45b",
    ("regulargrid", "noborder", 0.0): "acf57683d7d196cc",
    ("regulargrid", "noborder", 0.4): "6e1d77d4be52db05",
    ("regulargrid", "whiteborder", 0.0): "acf57683d7d196cc",
    ("regulargrid", "whiteborder", 0.4): "6e1d77d4be52db05",
    ("regulargrid", "polaroid", 0.0): "acf57683d7d196cc",
    ("regulargrid", "polaroid", 0.4): "6e1d77d4be52db05",
    ("contactsheet", "noborder", 0.0): "eddd76b53779223f",
    ("contactsheet", "noborder", 0.4): "c106b57d5e221b2f",
    ("contactsheet", "whiteborder", 0.0): "eddd76b53779223f",
    ("contactsheet", "whiteborder", 0.4): "c106b57d5e221b2f",
    ("contactsheet", "polaroid", 0.0): "eddd76b53779223f",
    ("contactsheet", "polaroid", 0.4): "c106b57d5e221b2f",
    ("multiexp", "noborder", 0.0): "f94d7cd0cb779de2",
    ("multiexp", "noborder", 0.4): "f94d7cd0cb779de2",
    ("multiexp", "whiteborder", 0.0): "f94d7cd0cb779de2",
    ("multiexp", "whiteborder", 0.4): "f94d7cd0cb779de2",
    ("multiexp", "polaroid", 0.0): "f94d7cd0cb779de2",
    ("multiexp", "polaroid", 0.4): "f94d7cd0cb779de2",
}


@pytest.mark.parametrize("kulcs", sorted(ELVART_UJJLENYOMATOK))
def test_a_refaktor_nem_valtoztat_a_rajzon(tmp_path, kulcs):
    """A `make_picasa_collage` kimenete BÁJTAZONOS a refaktor előttivel."""
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
    )
    jelentes = make_picasa_collage(forrasok, beallitas)
    assert _ujjlenyomat(jelentes.image) == ELVART_UJJLENYOMATOK[kulcs], (
        f"A(z) {tema}/{keret} (térköz {terkoz}) rajza megváltozott. "
        "Ez a refaktor hibája — az ujjlenyomatot NE igazítsd hozzá."
    )


def test_minden_tema_es_keret_le_van_fedve():
    """Az ujjlenyomat-tábla mind a hat témát és mindhárom keretet lefedi.

    Enélkül egy új téma némán kimaradhatna az őrből."""
    lefedett_temak = {kulcs[0] for kulcs in ELVART_UJJLENYOMATOK}
    lefedett_keretek = {kulcs[1] for kulcs in ELVART_UJJLENYOMATOK}
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


def test_a_render_nodes_nem_szamol_elrendezest(tmp_path):
    """UGYANAZ a csomópontlista UGYANAZT rajzolja, bármelyik téma van beállítva.

    Ez a jegy lényege: a rajzoló nem nyúl a téma pakolójához. Ha bármelyik
    téma befolyásolná a kimenetet, a kézi elrendezés mentéskor elveszne."""
    ut = _ir_kepet(tmp_path / "kek.png", 30, 50, (255, 0, 0))
    csomopontok = [
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
    kepek = [
        render_nodes(
            csomopontok,
            PicasaCollageSettings(theme=tema, width=400, height=300, spacing=0.7),
        ).image
        for tema in COLLAGE_THEMES
    ]
    for kep in kepek[1:]:
        assert np.array_equal(kep, kepek[0])


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


@pytest.mark.parametrize("tema", [MULTIEXP, CONTACTSHEET])
def test_a_csomopont_nelkuli_temak_hangosan_szolnak(tmp_path, tema):
    """A Többszörös exponálás és az Indexkép nem csomópontos — ezt ki is mondja.

    Néma üres lista helyett hiba: aki ezekre hív, elgépelte a témát."""
    beallitas = PicasaCollageSettings(theme=tema, width=400, height=300)
    with pytest.raises(ValueError, match="nincs csomópont-elrendezés"):
        layout_nodes([], [], beallitas)


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
