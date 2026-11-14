"""#6945: a „Kilépés most” gomb a futó háttérmunka mellett is kiléptet.

A tulajdonos (2026-11-14, 1.0.117): háttérmunka közben a kilépést választotta,
megjelent a „Kilépés a PicasaPy-ból” kérdés, de a „Kilépés most” után a program
nem állt le, a folyamatot kívülről kellett megölni.

KIVÁLTÓ OK (a valódi alkalmazáson, a Qt eseményeinek naplózásával mérve): a
`Qt.quit()` a Qt-ban `QEvent::Quit`-ot küld, az pedig bezárási kérést a
főablaknak. A főablak `onClosing`-ja a futó munka miatt visszavonta, és újra
feltette a kérdést, így az `aboutToQuit` sosem jött el. A megerősített kilépést
semmi nem jegyezte meg.

Az őrök külön folyamatban futtatják a VALÓDI alkalmazást (`main()`), a valódi
gombot kattintják, és határidővel mérik a folyamat végét. A #671-es forrás-őrök
ezt nem tudták megfogni: élő kilépést sosem hajtottak végre.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg
from support.kilepes_proba_6945 import futtasd

#: „legfeljebb néhány másodperc”: a lassú CI-gépet is elbíró felső korlát
HATARIDO_S = 20.0


def _konyvtar(tmp_path):
    mappa = tmp_path / "kepek"
    mappa.mkdir()
    make_jpeg(mappa / "a.jpg", size=(64, 48))
    return mappa


def _kiir(eredmeny) -> str:
    return (
        f"kilepett={eredmeny.kilepett} ido={eredmeny.kilepesi_ido_s} "
        f"kod={eredmeny.visszateresi_kod}\n--- kimenet ---\n{eredmeny.kimenet[-3000:]}"
        f"\n--- veremkep ---\n{eredmeny.veremkep[-3000:]}"
    )


@pytest.mark.parametrize(
    ("belepes", "munka"),
    [
        pytest.param("kilepes", "hatter", id="fajl-kilepes-hattermunkaval"),
        pytest.param("close", "hatter", id="ablak-x-hattermunkaval"),
        pytest.param("kilepes", "semmi", id="kontroll-munka-nelkul"),
    ],
)
def test_a_kilepes_most_utan_a_folyamat_hataridon_belul_veget_er(
    tmp_path, belepes, munka
):
    eredmeny = futtasd(
        tmp_path / "profil",
        _konyvtar(tmp_path),
        belepes=belepes,
        munka=munka,
        hatarido_s=HATARIDO_S,
    )

    assert eredmeny.eljutott_a_kattintasig, (
        "a próba nem jutott el a gombnyomásig (a kérdés nem jelent meg, vagy az "
        "indulás elakadt)\n" + _kiir(eredmeny)
    )
    assert eredmeny.kilepett, (
        f"a folyamat {HATARIDO_S} s után is fut a „Kilépés most” gomb nyomása "
        "után\n" + _kiir(eredmeny)
    )
    assert eredmeny.visszateresi_kod == 0, _kiir(eredmeny)
    assert eredmeny.kilepesi_ido_s is not None
    assert eredmeny.kilepesi_ido_s < HATARIDO_S, _kiir(eredmeny)
