"""#616: a Visszavonás/Újra gombsor a VALÓDI ablakban is látszik-e.

Miért kell ez, ha már van három őre (#628, #641, #703)?

Mert mind a három egy **mesterséges QML-burokban** méri az `EditorPanel`-t:
a teszt maga építi a szülőt, és ott a panel elfér. A felhasználó viszont a
`Main.qml` → `PhotoViewer.qml` valódi ős-láncát látja, ahol a panel egy
`RowLayout` `Layout.fillHeight` cellájában ül — és ha bármelyik ős túlnyúlik
az ablakon, a panel aljához igazított gombsor VELE EGYÜTT csúszik ki.

A 2026-08-15-i felhasználói képernyőképen a „Gyakori javítások" fül alatt
üres szürke terület van, gombok nélkül: a sor létezik, csak az ablakon kívül.

Ez az őr ezért a valódi `qml_app`-ot tölti be, és az ABLAK
koordinátarendszerében állít — nem a panel sajátjában.
"""

from __future__ import annotations

import pytest
from PySide6.QtQuick import QQuickItem


def _walk(item: QQuickItem, out: list[QQuickItem]) -> None:
    for child in item.childItems():
        out.append(child)
        _walk(child, out)


def _find(root: QQuickItem, name: str) -> QQuickItem | None:
    items: list[QQuickItem] = []
    _walk(root, items)
    for it in items:
        if it.objectName() == name:
            return it
    return None


@pytest.mark.parametrize("meret", [(1200, 800), (1024, 600), (900, 540)])
def test_a_gombsor_a_valodi_ablakon_belul_van(qml_app, qt_app, meret) -> None:
    """A sor alja sosem lóghat az ablak alja alá — semmilyen ablakméretnél."""
    window = qml_app[0]
    window.resize(*meret)
    # a szerkesztőpanel a NÉZŐBEN él (PhotoViewer.qml) — zárt néző mellett a
    # mérés semmit nem mond, ezért előbb kinyitjuk
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()

    root = window.contentItem()
    sor = _find(root, "editorGlobalUndoRow")
    assert sor is not None, "a Visszavonás/Újra sor nincs a jelenetben"

    # az ABLAK koordinátarendszerében — ezt látja a felhasználó
    teteje = sor.parentItem().mapToScene(sor.position()).y()
    alja = teteje + sor.height()

    assert alja <= window.height(), (
        f"a gombsor alja {alja:.0f} px-nél van, az ablak viszont csak "
        f"{window.height()} px magas — a felhasználó nem látja a "
        f"Visszavonás/Újra gombokat (ablakméret: {meret})"
    )
    assert teteje >= 0, (
        f"a gombsor teteje {teteje:.0f} px — az ablak fölé csúszott "
        f"(ablakméret: {meret})"
    )
