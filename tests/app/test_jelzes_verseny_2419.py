"""#2419 — a varakozo segito eloszor kossen be, csak azutan inditson.

A #2408 ota a `_wait` segito maga all meg, ha a jelzes nem erkezik meg —
ezert a bukas mar a VARAKOZASRA mutat. Az viszont nyitva maradt, hogy
MIERT nem erkezik meg. A meres szerint nem lassusag: a vezerlo a munkat
hattelszalon vegzi, es ha a hivo a bekotes ELOTT inditja el, a jelzes
megelozheti a bekotest — akkor pedig soha nem jon meg.

Az itteni orok ezt a sorrendet allitjak, determinisztikusan: a kivalt
muvelet MAR A HIVASBAN, szinkron modon jelez. Ha a segito eloszor
inditana, ez a jelzes garantaltan elveszne, es a teszt az idokorlatot
kiulve bukna.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from tests.app.test_regi_originals_a_feluleten_1425 import _wait


class _AzonnalJelzo(QObject):
    """Olyan `muvelet`, amely mar a hivas alatt kesz — ez a legrosszabb eset."""

    kesz = Signal(int, int)

    def inditas(self) -> None:
        self.kesz.emit(3, 0)


def test_a_hivas_kozben_kiadott_jelzes_sem_veszik_el(qt_app):
    jelzo = _AzonnalJelzo()

    eredmeny = _wait(jelzo.kesz, qt_app, jelzo.inditas, timeout_ms=3000)

    assert eredmeny["args"] == (3, 0)


def test_a_bekotes_a_kivaltas_elott_tortenik(qt_app):
    """Nem az eredmenyt, hanem a SORRENDET allitja."""
    jelzo = _AzonnalJelzo()
    naplo: list[str] = []

    jelzo.kesz.connect(lambda *_: naplo.append("jelzes"))

    def inditas() -> None:
        naplo.append("inditas")
        jelzo.inditas()

    _wait(jelzo.kesz, qt_app, inditas, timeout_ms=3000)

    assert naplo == ["inditas", "jelzes"], (
        "a jelzesnek az inditas UTAN kell jonnie, de a bekotesnek MAR "
        f"allnia kellett — naplo: {naplo}"
    )
