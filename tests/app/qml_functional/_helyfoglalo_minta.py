"""Helyfoglaló menütétel a jelölés-tesztekhez (#416, #3537).

A jelölés-tesztek korábban az alkalmazás egy még be nem kötött tételét
vették mintának. A #5704 óta induláskor nincs ilyen tétel (a gyűjtemény
jelszó-tétele élő lett), ezért ha az ablakban nem találunk helyfoglalót,
egy saját `PicasaMenuItem { placeholder: true }`-t hozunk létre ugyanazzal
a komponenssel, és azon mérünk.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent

_TARTSD_MEG: list[object] = []

_MINTA_QML = b"""import QtQuick
import QtQuick.Controls
import PicasaPy
Menu {
    objectName: "mintaHelyfoglaloMenu"
    PicasaMenuItem {
        objectName: "mintaHelyfoglalo"
        text: "Minta helyfoglal\xc3\xb3"
        placeholder: true
    }
}
"""


def helyfoglalo_tetelek(window, engine) -> list:
    """Az ablak helyfoglaló menütételei; ha nincs, egy létrehozott minta."""
    talalt = [
        obj
        for obj in window.findChildren(QObject)
        if obj.property("placeholder") is True and obj.property("text")
    ]
    if talalt:
        return talalt
    comp = QQmlComponent(engine)
    comp.setData(_MINTA_QML, QUrl())
    menu = comp.create(engine.rootContext())
    assert comp.errors() == [], comp.errors()
    menu.setParent(window)
    menu.setProperty("parent", window.property("contentItem"))
    _TARTSD_MEG.extend([comp, menu])
    tetel = menu.findChild(QObject, "mintaHelyfoglalo")
    assert tetel is not None
    return [tetel]
