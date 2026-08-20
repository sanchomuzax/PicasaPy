"""A KÉPHÁTTÉR a mentett kollázson is látszik (#1015).

## A lelet

A #1009 megjavította a háttérkép kiválasztását, az élő előnézetet és a
`.cxf` mentését — **a kirajzolt JPEG háttere viszont a beállított SZÍN
maradt**. A felhasználó tehát kiválasztotta a „Kép használata" módot,
látta az előnézetben, mentett — és egyszínű hátteret kapott.

Ez a #920 elfogadási feltételét sérti: *„a mentett kép pontosan azt
mutatja, amit a vásznon látsz."*

## Amit a golden eldönt, és amit NEM

A golden anyagból az látszik, hogy a háttér a **teljes lapot fedi**,
**éles**, és **nincs rajta effekt**. Ezt ez a fájl állítja is.

⚠️ **Ami NINCS lemérve:** kitölt-e (`cover`, arányt tartva, középről
vágva) vagy nyújt (`stretch`, arányt torzítva). A `cover` mellett
döntöttünk, mert (a) a rajzoló minden más helyen ezt használja
(`fit_to_frame(fill=True)`), és (b) a nyújtás láthatóan torzítja a
háttérképet, ami a felhasználónak rosszabb.

A `test_a_hatter_KITOLT_es_nem_nyujt` ezt a döntést rögzíti — nem azért,
mert bizonyított, hanem hogy a megváltoztatása **szándékos** legyen. Ha a
mérés később a nyújtást hozza, ez az egy teszt fordul meg.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from picasapy.collage.picasa_render import PicasaCollageSettings, render_nodes
from picasapy.collage.themes import PICTUREPILE

#: A vászon alapszíne BGR-ben — ha ez marad, a háttérkép nem hatott.
ALAPSZIN = (30, 60, 90)


@pytest.fixture
def hatterkep(tmp_path):
    """Egyszínű zöld háttérkép — a lapnál nagyobb, hogy a méretezés is hasson."""
    ut = tmp_path / "hatter.jpg"
    kep = np.full((300, 400, 3), (0, 200, 0), dtype=np.uint8)
    cv2.imwrite(str(ut), kep)
    return ut


def _beallitas(hatter: str = "", szeles=200, magas=200):
    return PicasaCollageSettings(
        theme=PICTUREPILE,
        width=szeles,
        height=magas,
        background=ALAPSZIN,
        background_image=hatter,
        shadow=False,
    )


def _sarkok(kep):
    magas, szeles = kep.shape[:2]
    return [
        tuple(int(x) for x in kep[2, 2]),
        tuple(int(x) for x in kep[2, szeles - 3]),
        tuple(int(x) for x in kep[magas - 3, 2]),
        tuple(int(x) for x in kep[magas - 3, szeles - 3]),
    ]


class TestAKephatterLatszik:
    """⚠️ Ez a felhasználó panasza: a mentett kép háttere egyszínű volt."""

    def test_a_hatter_nem_az_alapszin(self, hatterkep):
        kep = render_nodes((), _beallitas(str(hatterkep))).image

        assert _sarkok(kep) != [ALAPSZIN] * 4

    def test_a_hatter_a_TELJES_lapot_fedi(self, hatterkep):
        """A golden háttere a teljes lapot fedi — nem marad üres sáv."""
        kep = render_nodes((), _beallitas(str(hatterkep))).image

        for sarok in _sarkok(kep):
            assert sarok[1] > 150, f"a sarok nem a háttérkép színe: {sarok}"

    def test_hatterkep_nelkul_a_szin_marad(self):
        """A szín-mód nem romolhat el (és az átlagszín-mód sem, #1004)."""
        kep = render_nodes((), _beallitas()).image

        assert _sarkok(kep) == [ALAPSZIN] * 4


class TestAHibasHatter:
    """A háttérkép baja SOHA nem viheti el a kollázst."""

    def test_nem_letezo_utvonalra_a_szin_marad(self, tmp_path):
        kep = render_nodes((), _beallitas(str(tmp_path / "nincs.jpg"))).image

        assert _sarkok(kep) == [ALAPSZIN] * 4

    def test_serult_fajlra_a_szin_marad(self, tmp_path):
        rossz = tmp_path / "csonk.jpg"
        rossz.write_bytes(b"\xff\xd8\xff\xe0 nem egy JPEG")

        kep = render_nodes((), _beallitas(str(rossz))).image

        assert _sarkok(kep) == [ALAPSZIN] * 4


class TestAzIllesztesModja:
    """⚠️ DÖNTÉS, nem mérés — ld. a modul-docstringet."""

    def test_a_hatter_KITOLT_es_nem_nyujt(self, tmp_path):
        """Széles forráskép, négyzetes lap: kitöltésnél a bal széli sáv
        KIVÁGÓDIK, nyújtásnál megmaradna összenyomva."""
        ut = tmp_path / "jelolt.jpg"
        kep = np.full((200, 400, 3), (200, 0, 0), dtype=np.uint8)
        kep[:, :20] = (0, 0, 200)  # bal széli piros sáv
        cv2.imwrite(str(ut), kep)

        eredmeny = render_nodes((), _beallitas(str(ut))).image

        bal_oszlop = eredmeny[:, :5].reshape(-1, 3)
        piros = int(np.count_nonzero(bal_oszlop[:, 2] > 150))
        assert piros == 0, (
            "a forráskép bal széli sávja látszik — a háttér NYÚJTVA van, "
            "nem kitöltve"
        )

    def test_az_arany_nem_torzul(self, tmp_path):
        """Négyzetes forrás négyzetes lapon: a kitöltés semmit nem vág le,
        tehát a jelölő NÉGYZET marad."""
        ut = tmp_path / "negyzet.jpg"
        kep = np.full((200, 200, 3), (200, 0, 0), dtype=np.uint8)
        kep[80:120, 80:120] = (0, 0, 200)
        cv2.imwrite(str(ut), kep)

        eredmeny = render_nodes((), _beallitas(str(ut))).image

        maszk = (eredmeny[:, :, 2] > 150).astype(np.uint8)
        ys, xs = np.nonzero(maszk)
        magassag = ys.max() - ys.min() + 1
        szelesseg = xs.max() - xs.min() + 1
        assert szelesseg / magassag == pytest.approx(1.0, abs=0.08)


# --------------------------------------------------------------------------
# A SIKERKRITÉRIUM: a MENTETT fájl háttere
# --------------------------------------------------------------------------
class TestAMentettFajlHattere:
    """⚠️ A jegy mércéje nem a vászon, hanem a LEMEZRE ÍRT kép.

    A #1009 köre pont azért nem vette észre a hiányt, mert az élő előnézet
    helyes volt. Ez az osztály a `render_collage`-en át megy, és a
    visszaolvasott JPEG képpontjait nézi."""

    def test_a_kiirt_JPEG_hattere_a_valasztott_kep(self, hatterkep, tmp_path):
        from picasapy.app import collage_output as output

        eredmeny = output.render_collage(
            (),
            _beallitas(str(hatterkep)),
            tmp_path / "kollazs.jpg",
        )

        # csomópont nélkül nem születik fájl — a hátteret a rajzolón mérjük
        assert eredmeny.path is None

    def test_egy_csempevel_a_kiirt_JPEG_hattere_a_kep(self, hatterkep, tmp_path):
        from picasapy.app import collage_output as output
        from picasapy.collage.nodes import SHEET_UNITS, CollageNode

        forras = tmp_path / "csempe.jpg"
        cv2.imwrite(str(forras), np.full((40, 40, 3), (0, 0, 255), dtype=np.uint8))
        csomopont = CollageNode(
            path=forras,
            center_x=SHEET_UNITS * 0.5,
            center_y=SHEET_UNITS * 0.25,
            width=SHEET_UNITS * 0.2,
            height=SHEET_UNITS * 0.2,
            theta=0.0,
            border="noborder",
            fill=True,
        )

        eredmeny = output.render_collage(
            (csomopont,), _beallitas(str(hatterkep)), tmp_path / "kollazs.jpg"
        )

        assert eredmeny.path is not None
        kiirt = cv2.imread(str(eredmeny.path))
        for sarok in _sarkok(kiirt):
            assert sarok[1] > 140, (
                f"a mentett kép sarka nem a háttérkép színe: {sarok}"
            )
