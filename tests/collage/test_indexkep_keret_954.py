"""#954 — az Indexkép keretbeállítása LÁTSZIK a képen.

## A lelet, ahogy a #942 mérése rögzítette

A keretválasztó (Egyik sem / Fehér szegély / Polaroid) az Indexképnél
látszott és állítható volt, de a rajzolás nem vette figyelembe: a téma mind
a három kerettel **bájtazonos** képet adott. A #942 ujjlenyomatai ezt
számszerűen mutatták.

## Ma már nem áll fenn — épp ezért kell az őr

A mai kód a keretet a téma SAJÁT beállításából veszi
(`_contact_sheet_nodes`: `keret = settings.effective_border`), és a három
keret három különböző képet ad. A jegy által megnevezett mechanizmus — egy
`theme=REGULARGRID` al-beállítás, amelynek a képesség-maszkja `noborder`-re
szűrte a keretet — **megszűnt**.

A javítás viszont mellékesen történt, őr nélkül. Márpedig a `regulargrid`
képesség-maszkja MA IS `borders=False`, tehát az a visszaesés, amit a jegy
leírt, egyetlen al-beállítás visszavezetésével újra előállhatna — és a
tünete néma lenne: a felhasználó állítja a keretet, a kép nem változik.

## Miért a KÉP, és nem a beállítás

Kézenfekvő lenne az `effective_border`-t állítani. Az viszont a régi hibát
sem fogta volna meg: a #954-ben az `effective_border` a HÍVÓ témán helyes
értéket adott, és a keret egy al-beállításban veszett el, lejjebb. Az őr
ezért a kimeneten mér.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pytest

from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    make_picasa_collage,
)
from picasapy.collage.themes import BORDER_THEMES, capabilities_for

CONTACTSHEET = "contactsheet"


@pytest.fixture
def kepek(tmp_path):
    from support.jpeg_factory import make_jpeg

    utak = []
    for index, meret in enumerate([(40, 30), (30, 40), (40, 40), (60, 30)]):
        ut = tmp_path / f"k{index}.jpg"
        make_jpeg(ut, size=meret)
        utak.append(ut)
    return utak


def _ujjlenyomat(utak, keret: str) -> str:
    beallitas = PicasaCollageSettings(
        theme=CONTACTSHEET, border=keret, width=600, height=450, seed=7
    )
    kep = make_picasa_collage(utak, beallitas).image
    return hashlib.sha256(np.ascontiguousarray(kep).tobytes()).hexdigest()


def test_a_harom_keret_harom_kulonbozo_kepet_ad(kepek):
    ujjlenyomatok = {keret: _ujjlenyomat(kepek, keret) for keret in BORDER_THEMES}

    assert len(set(ujjlenyomatok.values())) == len(BORDER_THEMES), (
        "az Indexkép ugyanazt a képet adja több kerettel — a beállítás "
        f"némán elveszett: {ujjlenyomatok}"
    )


def test_a_tema_kepesseg_maszkja_engedi_a_keretet(kepek):
    """A választó látszik — tehát a rajzolásnak is hatnia KELL."""
    assert capabilities_for(CONTACTSHEET).borders is True


def test_a_polaroid_keret_tobb_feheret_tesz_a_lapra(kepek):
    """Nem csak »más«, hanem a keret IRÁNYÁBA más — de csak a polaroidnál.

    ⚠️ A kézenfekvő állítás — »minden vastagabb keret több fehéret ad« —
    KIMÉRVE MEGDŐLT. A négyképes próbán:

    ```
    noborder=168645  whiteborder=167325  polaroid=176413
    ```

    A fehér szegély tehát KEVESEBB fehér képpontot ad a keret nélkülinél
    (−0,8%). Ésszerű oka van: a keretes befoglaló a cellába illeszkedik,
    tehát a fotó zsugorodik, a felszabaduló hely viszont a lapháttéré marad
    — a szegély csak akkor számítana, ha a háttér nem fehér. A polaroid
    +4,6%-a viszont jóval a zaj fölött van, mert az alsó, széles talp
    tömör fehér.

    Ezért itt CSAK a polaroid irányát állítjuk. A »mindhárom más« invariánst
    az ujjlenyomatos eset viszi; ez az eset azt teszi hozzá, hogy a
    különbség nem véletlen zaj, hanem a keret RAJZA.
    """
    aranyok = {}
    for keret in ("noborder", "polaroid"):
        beallitas = PicasaCollageSettings(
            theme=CONTACTSHEET, border=keret, width=600, height=450, seed=7
        )
        kep = make_picasa_collage(kepek, beallitas).image
        aranyok[keret] = int(np.count_nonzero(np.all(kep >= 250, axis=-1)))

    assert aranyok["polaroid"] > aranyok["noborder"] * 1.02, (
        f"a polaroid talpa nem latszik a lapon: {aranyok}"
    )
