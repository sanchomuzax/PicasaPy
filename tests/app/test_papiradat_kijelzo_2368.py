"""#2368: a nyomtatási párbeszéd papíradat-mezője.

## A lelet

Az eredeti panel állapotfrissítője (`0x00745980`) EGY menetben tölti fel a
négy információs mezőt, mind a négyet ugyanazzal a szövegbeállítóval
(`0x009cd870`):

```
0x00745bcc  printpanel/printername
0x00745bde  printpanel/paperinfo       <- ez hiányzott nálunk
0x00745bba  printpanel/previewnumber
0x00745e10  printpanel/statustext
```

⇒ a `paperinfo` ugyanolyan **szöveges kijelző**, mint a nyomtató neve —
nem vezérlő.

## Amit a mérés NEM adott meg

A mező **pontos szövegformátumát**: a `stringres`-ben nincs hozzá kulcs, a
bináris futásidőben állítja össze. A formátum ezért a mi választásunk; a
jegy csak azt köti ki, hogy az adat a VALÓDI lapbeállításból jöjjön.
Ezek a tesztek ennek megfelelően **nem** a szöveg pontos alakját állítják,
hanem azt, hogy a lapbeállítás megváltozása LÁTSZIK rajta.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize


@pytest.fixture
def vezerlo(qt_app):
    from picasapy.app.print_controller import PrintController

    return PrintController(lambda: [])


def _elrendezes(meret: QPageSize.PageSizeId, fekvo: bool = False) -> QPageLayout:
    return QPageLayout(
        QPageSize(meret),
        QPageLayout.Orientation.Landscape if fekvo else QPageLayout.Orientation.Portrait,
        QMarginsF(0, 0, 0, 0),
    )


def test_ket_kulonbozo_lapmeret_kulonbozo_szoveget_ad(vezerlo) -> None:
    vezerlo._oldalelrendezes = _elrendezes(QPageSize.PageSizeId.A4)
    a4 = vezerlo.paperInfo("")
    vezerlo._oldalelrendezes = _elrendezes(QPageSize.PageSizeId.A5)
    a5 = vezerlo.paperInfo("")

    assert a4 and a5, "a mező üres — a felhasználó nem látná, mire nyomtat"
    assert a4 != a5, f"két lapméret ugyanazt a szöveget adta: {a4!r}"


def test_a_tajolas_is_latszik(vezerlo) -> None:
    vezerlo._oldalelrendezes = _elrendezes(QPageSize.PageSizeId.A4)
    allo = vezerlo.paperInfo("")
    vezerlo._oldalelrendezes = _elrendezes(QPageSize.PageSizeId.A4, fekvo=True)
    fekvo = vezerlo.paperInfo("")

    assert allo != fekvo, f"a tájolás nem látszik a szövegen: {allo!r}"


def test_lapbeallitas_nelkul_sem_ures(vezerlo) -> None:
    """PDF-be nyomtatásnál (nincs nyomtató, nincs mentett elrendezés) is
    értelmes tartalmat kell adnia — a jegy kikötése."""
    vezerlo._oldalelrendezes = None
    assert vezerlo.paperInfo("").strip(), "üres papíradat PDF-módban"


def test_a_meret_szama_is_benne_van(vezerlo) -> None:
    """A papírnév önmagában kevés: az „A4" nem mond méretet annak, aki nem
    tudja fejből. A mérőszám ezért kötelező eleme a szövegnek."""
    vezerlo._oldalelrendezes = _elrendezes(QPageSize.PageSizeId.A4)
    szoveg = vezerlo.paperInfo("")
    assert any(karakter.isdigit() for karakter in szoveg), szoveg
