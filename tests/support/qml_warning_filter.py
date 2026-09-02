"""A QML-figyelmeztetés-őr osztályozója (a #305-ös őr, a #309-es szűkítéssel).

Külön modul, nem a `conftest.py`-ban: a conftest nem importálható a
tesztekből (nem csomag), a `tests/support/` viszont a `pythonpath` révén
igen — így az osztályozó önmagában is tesztelhető.

## Mire hasal el az őr, és mire nem

KIZÁRÓLAG a QML-SZKRIPTHIBÁKRA. Ezek a minták mindig a MI kódunk hibái
(kötés hivatkozik nem létező tagra, rossz típust rendel értékül), és
platformfüggetlenek — ilyet sose írjunk ki.

A korábbi, MINDEN Qt-figyelmeztetésre elhasaló változat (#305) a
windows-latest CI-lábat buktatta olyan környezeti üzenetekre, amiknek semmi
közük a kódhoz: hiányzó fontkönyvtár a runneren, `OpenThemeData() failed`
offscreen módban, illetve a natív Windows-stílus „nem támogatja a
testreszabást" figyelmeztetése. Ezek platformfüggő zajok; ha az őr rájuk is
elhasal, minden jövőbeli Qt-/runner-változás hamis pirosat okoz — épp az
ellenkezőjét annak, amit a #305 el akart érni (a VALÓDI hibák láthatósága).

Ezért NE tágítsd vissza „minden figyelmeztetésre" gondolkodás nélkül: a
szűk, mintaalapú szűrés a szándékolt viselkedés.
"""

from __future__ import annotations

#: #2072: a QT SAJÁT QML-jéből érkező üzenetek origója. Ezeket nem mi
#: írtuk, és nem is javíthatjuk — a szűrőnek figyelmen kívül kell hagynia
#: őket, bármilyen mintát tartalmaznak.
#:
#: A mérés (`ci.yml` 33687325094, windows 1/4): a Qt Controls natív
#: Windows-stílusának `Button.qml`-je négy `TypeError`-t ír ki minden
#: gomb-példányosításkor:
#:
#:     qrc:/qt-project.org/imports/QtQuick/Controls/Windows/Button.qml:28:9:
#:         TypeError: Cannot read property 'height' of null
#:
#: Az őr ezekre elhasalt, tehát Windowson MINDEN gombot példányosító teszt
#: elbukott — és mivel a windows-láb nem blokkol, ez hónapokig láthatatlan
#: maradhatott, közben elfedve minden VALÓDI windows-specifikus hibát
#: (pl. a #998-at).
#:
#: ⚠️ Ez ORIGÓ szerinti szűrés, nem minta szerinti: a mi QML-ünkből
#: (`file:///…`) érkező azonos szövegű üzenet TOVÁBBRA IS buktat.
IDEGEN_QML_EREDET = (
    "qrc:/qt-project.org/",
)

QML_SCRIPT_ERROR_PATTERNS = (
    "TypeError",
    "ReferenceError",
    "SyntaxError",
    "Unable to assign",
    "is not a function",
    # #506: `qt.qml.propertyCache.append: Member X of the object Y
    # overrides a member of the base object.` — saját komponens tulajdonsága
    # elfedi az alaposztály (pl. Item/Control `palette`) azonos nevű tagját.
    # Mindig a mi kódunk hibája (névütközés), platformfüggetlen — sose
    # buktatná el hamisan a CI-t.
    "overrides a member of the base object",
    # #1697: `QML QQuickText: Cannot anchor to an item that isn't a parent or
    # sibling.` — a kötés a KOMPONENS létrehozásakor értékelődik ki, tehát
    # egy futásidejű `parent`-átállítás ELŐTTI állapotra kell érvényesnek
    # lennie. Ez mindig a MI kötésünk hibája, platformfüggetlen, és a hatása
    # néma: az elem odakerül, ahova az alapértelmezés teszi, nem oda, ahova
    # szántuk. A tulajdonos konzolján jelent meg minden induláskor, kétszer —
    # a tesztek addig nem fogták meg, mert ez a minta hiányzott innen.
    "Cannot anchor to an item",
)

# #1599/#1748: a `Binding loop detected` minta SZÁNDÉKOSAN nincs a listában.
# Felvettük, és a CI azonnal MEGMÉRTE, hogy legalább két további párbeszédünk
# hurkol (`SaveDialogs.qml:171`, `UnnamedFacesView.qml:283`) — a forrás-söprés
# szerint 38 párbeszéd hordozza ugyanazt a mintát. A minta bekapcsolása tehát
# nem egy őr bevezetése volna, hanem egy több tucat helyet érintő javítás
# kikényszerítése egyetlen kiadás közben.
#
# A #1599 saját hurkát ezért CÉLZOTT teszt őrzi
# (`tests/app/qml_functional/test_kotesi_hurok_fusion_1599.py`, Fusion
# stílusú gyerekprocesszben), a többi a #1748 hatóköre — ott a minta
# bekapcsolása az utolsó lépés, a javítások UTÁN.


def is_qml_script_error(message: str) -> bool:
    """QML-szkripthiba-e az üzenet (a mi kötéseink hibája), vagy környezeti zaj.

    #2072: az idegen (Qt saját) QML-ből érkező üzenet SOHA nem a mi hibánk,
    ezért az origó-ellenőrzés a mintaillesztés ELŐTT áll.
    """
    if any(eredet in message for eredet in IDEGEN_QML_EREDET):
        return False
    return any(pattern in message for pattern in QML_SCRIPT_ERROR_PATTERNS)
