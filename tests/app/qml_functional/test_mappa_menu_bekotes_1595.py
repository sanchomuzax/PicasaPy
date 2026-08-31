"""#1595 — a Mappa menü négy néma tétele élő lett.

A menüsáv `Mappa` menüjében négy tétel állt néma helyfoglalóként, pedig a
motorjuk régóta megvan — csak a mappa HELYI menüjéből lehetett elérni
őket:

| tétel | mi hajtja | mióta |
|---|---|---|
| Áthelyezés… | `fileOpsController.moveFolder` | #457 |
| Törlés… | `fileOpsController.deleteFolder` | #1638 |
| Eltávolítás a Picasából… | `controller.removeFolder` | #1249 |
| Keresés a lemezen | `fileOpsController.revealFolder` | #422 |

Mind a négy a **megnyitott** mappára hat — az eredetiben a „Mappa" menü
ezt jelenti.

⚠️ **Amit ez a jegy NEM csinál:** a `Rendezés` almenü készletének cseréjét.
A jegy azt írta, hogy a menüsáv a „rossz" (ötös, hosszú feliratú)
készletet használja a helyi menü négyes készlete helyett. A kód mérése ezt
CÁFOLJA: a menüsáv `Rendezés`-e a MAPPÁKAT rendezi (`setFolderSort`,
#1454), a helyi menüé a mappa KÉPEIT (`setFolderPhotoSort`, #1436) — két
külön funkció, nem ugyanaz kétszer. Az összevonásuk viselkedés-változás
lenne, nem paritás-javítás.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

#: a négy tétel, és a jelzés, amit ki kell váltania
TETELEK = (
    "menuFolderMove",
    "menuFolderDelete",
    "menuFolderRemoveFromPicasa",
    "menuFolderLocate",
)


class TestANegyTetelElo:
    @pytest.mark.parametrize("nev", TETELEK)
    def test_a_tetel_mar_nem_helyfoglalo(self, qml_app, nev):
        window, _controller, _engine = qml_app
        tetel = window.findChild(QObject, nev)
        assert tetel is not None, f"{nev} nem található a Mappa menüben"
        assert tetel.property("placeholder") is not True, (
            f"{nev} még mindig néma helyfoglaló (#1595)"
        )
        assert tetel.property("enabled") is True, (
            f"{nev} le van tiltva — a bekötése némán hatástalan"
        )


class TestAValodiUt:
    """A menütételtől a párbeszédig — a vezérlőre kattintva, nem a
    metódust hívva (MEMORY)."""

    def test_a_torles_a_megnyitott_mappara_kerdez_ra(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _engine = qml_app
        tetel = window.findChild(QObject, "menuFolderDelete")
        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        parbeszed = window.findChild(QObject, "deleteFolderConfirmDialog")
        assert parbeszed is not None and parbeszed.property("visible") is True, (
            "a Mappa ▸ Törlés… nem nyitotta meg a megerősítést (#1595)"
        )
        felirat = window.findChild(QObject, "deleteFolderConfirmMessageLabel")
        aktualis = controller.currentFolder
        assert aktualis, "nincs megnyitott mappa — a próba nem bizonyítana"
        nev = aktualis.rstrip("/").split("/")[-1]
        assert nev in felirat.property("text"), (
            "a megerősítés nem a MEGNYITOTT mappát nevezi meg: "
            f"{felirat.property('text')!r}"
        )

    def test_az_athelyezes_megnyitja_a_mappavalasztot(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, _controller, _engine = qml_app
        tetel = window.findChild(QObject, "menuFolderMove")
        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        valaszto = window.findChild(QObject, "moveFolderDialog")
        assert valaszto is not None, "moveFolderDialog nem található"
        assert valaszto.property("visible") is True, (
            "a Mappa ▸ Áthelyezés… nem nyitotta meg a mappaválasztót (#1595)"
        )


class TestARendezesValtozatlan:
    """Regresszió: a menüsáv rendezés-készlete NEM változott — a jegy
    javaslata a mérés szerint téves volt (ld. a modul docstringjét)."""

    def test_a_menusav_rendezese_otos_marad(self, qml_app):
        window, _controller, _engine = qml_app
        for nev in (
            "menuFolderSortByDate",
            "menuFolderSortByChanged",
            "menuFolderSortBySize",
            "menuFolderSortByName",
            "menuFolderSortReverse",
        ):
            assert window.findChild(QObject, nev) is not None, (
                f"{nev} eltűnt a menüsáv Rendezés almenüjéből — a mappák "
                "rendezése (#1454) nem cserélhető a képek rendezésére"
            )
