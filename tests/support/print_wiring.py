"""A nyomtatás-vezérlő bekötése a teszt-fixture-ökbe (#1472).

Azért KÖZÖS helyen él, mint a `folder_hierarchy_wiring` (#1454): két
`qml_app` fixture van (`tests/app/` és `tests/app/qml_functional/` alatt),
és a féloldalas tükrözés a projektben már megfogott minket — a `Main.qml`
`PrintDialog`-ja `typeof`-őr mögül hivatkozik a vezérlőre, tehát a hiány
NEM szállna el, csak némán semmit nem mérnénk.

Az import védett, a `application.py`-val azonos okból: a
`PySide6.QtPrintSupport` a Debian/Ubuntu-féle rendszercsomagban külön
modul (#664). Ahol hiányzik, ott a bekötés kimarad, és a rá épülő tesztek
saját `skipif`-jükkel maradnak ki.
"""

from __future__ import annotations


def wire_print(engine, photo_source):
    """A vezérlő létrehozása és regisztrálása — az `application.py` tükre.

    A visszatérési érték a vezérlő (hiányzó QtPrintSupport esetén `None`);
    a hívó fixture tartsa életben, amíg a motor él.
    """
    try:
        from picasapy.app.print_controller import PrintController
    except ImportError:  # pragma: no cover — csak a hiányos Qt-telepítésen
        engine.rootContext().setContextProperty("printController", None)
        return None

    print_controller = PrintController(photo_source=photo_source)
    engine.rootContext().setContextProperty("printController", print_controller)
    return print_controller
