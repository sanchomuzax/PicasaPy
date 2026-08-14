"""Gépi elrendezés-ellenőr: túlcsordulás és átfedés a KIRAJZOLT fában — #656/1.

Miért ez a fájl létezik: a felhasználó több elrendezési hibát talált éles
használatban, végig zöld CI mellett — az effekt-csúszkák nem férnek a bal
oszlop szélességébe, gombok rossz helyre csúsznak. A meglévő tesztek
komponensenként, konkrét elvárásokkal dolgoznak; ez azt jelenti, hogy csak
azt fogják meg, amire valaki előre gondolt.

Ez a fájl más: **invariánst** ellenőriz, nem konkrét elvárást. Két állítás,
ami minden felületre igaz kell legyen, referencia nélkül is:

1. egy vezérlő ne lógjon ki a szülője dobozából (túlcsordulás);
2. két testvér ne fedje egymást ott, ahol nem szándékos.

A #656 tervének 1. fázisa ez, és szándékosan **nem** igényli az eredeti
Picasa layout-forrásait: tiszta önellenőrzés a saját felületünkön.

A mérés a `test_editor_panel_rendered_651.py` mintáját követi: valódi
`QQuickView`, több ablakméret, az ABLAK koordinátarendszerében mért
geometria. A `Repeater`/`ListView` delegáltjait `findChild` NEM találja meg,
ezért a VIZUÁLIS fát járjuk be.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, Property, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView

from support.uiaudit_geometry import (
    Violation,
    find_overflows,
    find_overlaps,
    format_report,
)

_KEEPALIVE: list[object] = []


class _EditControllerStub(QObject):
    """Annyi az EditControllerből, amennyitől a csempék BÉLYEGKÉPESEK.

    Nem kényelmi részlet: bélyegkép nélkül a csempe ~24 képpont magas,
    élesben ~98 — a geometria mérése enélkül hamis biztonságot adna
    (a #651 tanulsága).
    """

    @Property(str, constant=True)
    def previewSource(self):
        return "image://editpreview/42?rev=1"

    @Property("QVariantList", constant=True)
    def legacyEffectsInChain(self):
        return []


def _render(qt_app, qml: str, width: int, height: int):
    """A QML valódi ablakban, adott mérettel — a layoutok tényleg lefutnak."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    stub = _EditControllerStub()
    view.engine().rootContext().setContextProperty("editController", stub)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

    component = QQmlComponent(view.engine())
    component.setData(qml.encode("utf-8"), QUrl())
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors

    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(width, height)
    root.setWidth(width)
    root.setHeight(height)
    _KEEPALIVE.extend((view, root, component, stub))
    view.show()
    return root


#: Szintetikus felület EGY szándékos hibával: a belső elem 40 képponttal
#: szélesebb a dobozánál. Pontosan az a hibaosztály, amit a felhasználó
#: „a csúszkák nem fitelnek a bal oszlop szélességéhez" néven jelzett.
_TULCSORDULO_QML = """
import QtQuick
Item {
    objectName: "gyoker"
    Rectangle {
        objectName: "doboz"
        x: 10; y: 10; width: 200; height: 100
        Rectangle {
            objectName: "tulcsordulo"
            x: 0; y: 0; width: 240; height: 30
        }
        Rectangle {
            objectName: "rendben"
            x: 0; y: 40; width: 180; height: 30
        }
    }
}
"""

#: Két testvér, amelyek átfedik egymást — a másik hibaosztály.
_ATFEDO_QML = """
import QtQuick
Item {
    objectName: "gyoker"
    Rectangle {
        objectName: "doboz"
        x: 0; y: 0; width: 300; height: 200
        Rectangle { objectName: "elso";  x: 0;  y: 0; width: 100; height: 50 }
        Rectangle { objectName: "masodik"; x: 60; y: 0; width: 100; height: 50 }
    }
}
"""

#: Hibátlan felület — az ellenőrnek NEM szabad panaszkodnia rá.
_TISZTA_QML = """
import QtQuick
Item {
    objectName: "gyoker"
    Rectangle {
        objectName: "doboz"
        x: 0; y: 0; width: 300; height: 200
        Rectangle { objectName: "elso";  x: 0; y: 0;  width: 100; height: 50 }
        Rectangle { objectName: "masodik"; x: 0; y: 60; width: 100; height: 50 }
    }
}
"""


class TestTulcsordulasErzekeles:
    """Az ELLENŐR maga: megfogja-e a szándékosan elrontott elrendezést?"""

    def test_megfogja_a_szeles_gyereket(self, qt_app):
        root = _render(qt_app, _TULCSORDULO_QML, 400, 300)
        sertesek = find_overflows(root)
        nevek = {sertes.item for sertes in sertesek}
        assert "tulcsordulo" in nevek, format_report(sertesek)

    def test_a_jo_meretu_gyerekre_NEM_panaszkodik(self, qt_app):
        root = _render(qt_app, _TULCSORDULO_QML, 400, 300)
        nevek = {sertes.item for sertes in find_overflows(root)}
        assert "rendben" not in nevek

    def test_tiszta_feluleten_nincs_serles(self, qt_app):
        root = _render(qt_app, _TISZTA_QML, 400, 300)
        sertesek = find_overflows(root)
        assert sertesek == [], format_report(sertesek)

    def test_a_turest_tiszteletben_tartja(self, qt_app):
        """Egy képpontnyi kilógás nem hiba — a tört geometria miatt kell tűrés."""
        root = _render(qt_app, _TULCSORDULO_QML, 400, 300)
        # 40 képpont a tényleges kilógás; 50-es tűréssel már nem hiba
        assert find_overflows(root, tolerance=50.0) == []


class TestAtfedesErzekeles:
    def test_megfogja_az_atfedo_testvereket(self, qt_app):
        root = _render(qt_app, _ATFEDO_QML, 400, 300)
        parok = {tuple(sorted((s.item, s.other or ""))) for s in find_overlaps(root)}
        assert ("elso", "masodik") in parok

    def test_egymas_alatti_testvereket_nem_jelzi(self, qt_app):
        root = _render(qt_app, _TISZTA_QML, 400, 300)
        assert find_overlaps(root) == []


class TestRiport:
    def test_ures_listabol_ures_riport(self):
        assert format_report([]) == "nincs elrendezés-sértés"

    def test_a_riport_tartalmazza_a_nevet_es_a_mertekét(self):
        sertes = Violation(
            kind="overflow", item="csuszka", parent="baloszlop",
            detail="40.0 képponttal szélesebb", other=None,
        )
        szoveg = format_report([sertes])
        assert "csuszka" in szoveg
        assert "baloszlop" in szoveg
        assert "40.0" in szoveg


@pytest.mark.parametrize("width", [260, 280, 340])
class TestValosSzerkesztoPanel:
    """A VALÓS szerkesztő-panel több oszlopszélességgel.

    Ez az a mérés, ami a felhasználó által jelzett hibaosztályt megfogja.
    Az ismert, még nem javított sértések az `ismert_sertesek.json`-ban
    vannak — a teszt csak az ÚJAKRA bukik el, hogy ne blokkolja a
    fejlesztést, de a regressziót elkapja.
    """

    def test_nincs_uj_tulcsordulas(self, qt_app, width):
        from support.uiaudit_geometry import load_allowlist, subtract_allowlist

        qml = """
        import QtQuick
        import QtQuick.Layouts
        import PicasaPy 1.0
        Item {
            objectName: "auditRoot"
            Rectangle {
                objectName: "baloszlop"
                anchors.fill: parent
                EditorPanel {
                    objectName: "auditPanel"
                    anchors.fill: parent
                }
            }
        }
        """
        root = _render(qt_app, qml, width, 800)
        sertesek = find_overflows(root)
        ujak = subtract_allowlist(sertesek, load_allowlist())
        assert ujak == [], format_report(ujak)
