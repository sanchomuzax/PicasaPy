"""#1720 — a QML-példányosítás MUNKAMENNYISÉG-őre.

**Miért nem időt mér.** A #1653/#1689 tanulsága, hogy egy időküszöb
terhelés alatt használhatatlan: ugyanaz a fa a fejlesztői gépen 3,4 és
5,3 másodperc között ingadozott PERCEKEN belül, mérhető változás nélkül.
A felépült **objektumok száma** viszont determinisztikus — kétszer futtatva
bájtra ugyanaz —, és pontosan azt a munkát méri, amit a #1720 csökkent.

**Mit őriz.**

1. A `Main.qml` betöltésekor felépülő QObjectek száma nem nőhet vissza.
2. A halasztott párbeszédek induláskor **létre sem jönnek** — ez a
   nyereség forrása, és önmagában is bukik, ha valaki visszaveszi a
   `DeferredDialog`-ot.
3. A szövegmezők jobbklikk-menüje induláskor nincs meg, viszont **egy
   jobbklikkre megjelenik** — a halasztás nem teheti némán hatástalanná.

A 2. és 3. pont MŰKÖDÉS-őre (a párbeszéd tényleg megnyílik-e) a saját
tesztfájljaikban él, a VALÓDI menüponton/gombon át:
`test_qml_folder_manager_kattintas_1200.py`, `test_qml_dedup.py`,
`test_qml_import_source.py`, `test_import_menupont_1615.py`,
`test_arckereses_bekotes_1473.py`, `test_nyomtatas_bekotes_1472.py`,
`test_compact_dialog_449.py`, `test_qml_move_database.py`,
`test_qml_options_dialog.py`, `test_qml_webexport_dialog.py`,
`test_save_dialogs_444.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Qt

import picasapy.app

_QML_DIR = Path(picasapy.app.__file__).parent / "qml"

#: A felépült objektumok PLAFONJA. A #1720 előtt 20 558 volt, utána
#: 12 073 (`docs/benchmarks/2026-08-31-qml-peldanyositas-1720.md`). A
#: plafon a mért érték + 3% tartalék: a Qt-verzió apró eltéréseit
#: elviseli, egy visszavett halasztást viszont nem.
OBJEKTUM_PLAFON = 12_500

#: Egy ÜRES őr mindig zöld. Az alsó korlát a pozitív kontroll: ha a fa
#: ennyinél kevesebb objektumból áll, nem a felület épült fel, hanem a
#: mérés romlott el (pl. a `Main.qml` némán hibára futott).
OBJEKTUM_ALSO_KORLAT = 5_000

#: Induláskor NEM létezhetnek — mindegyik `DeferredDialog` mögött ül.
HALASZTOTT_PARBESZEDEK = (
    "aboutDialog",
    "compactDatabaseDialog",
    "dedupDialog",
    "editOverwriteDialog",
    "exportDialog",
    "faceScanDialog",
    "folderManagerDialog",
    "importSourceDialog",
    "moveDatabaseDialog",
    "optionsDialog",
    "printDialog",
    "saveDialogs",
    "webExportDialog",
)


def _objektumszam(window) -> int:
    return len(window.findChildren(QObject)) + 1


class TestPeldanyositasMunkamennyiseg:
    def test_a_felepult_objektumok_szama_a_plafon_alatt_marad(self, qml_app):
        """#1720: a példányosítás munkamennyisége nem nőhet vissza."""
        window, _controller, _engine = qml_app

        darab = _objektumszam(window)

        assert darab > OBJEKTUM_ALSO_KORLAT, (
            f"mindössze {darab} objektum épült fel — ez nem eredmény, "
            "hanem mérési hiba (a felület nem állt fel)"
        )
        assert darab <= OBJEKTUM_PLAFON, (
            f"{darab} objektum épül fel induláskor, a plafon "
            f"{OBJEKTUM_PLAFON}. A #1720 halasztásaiból visszavettek "
            "valamit — a plafont csak MÉRÉSSEL együtt szabad emelni."
        )

    @pytest.mark.parametrize("nev", HALASZTOTT_PARBESZEDEK)
    def test_a_halasztott_parbeszed_induláskor_letre_sem_jon(
        self, qml_app, nev
    ):
        window, _controller, _engine = qml_app

        assert window.findChild(QObject, nev) is None, (
            f"a(z) {nev} már induláskor felépült — a #1720 `DeferredDialog` "
            "burka lekerült róla, vagy valami idő előtt megnyitotta"
        )


class TestSzovegmezoMenuHalasztva:
    """#1720 legnagyobb egyetlen tétele: a 40 szövegmező-menü.

    Mérve 5562 objektum (a fa 27%-a). A halasztás akkor ér valamit, ha a
    menü az első jobbklikkre TÉNYLEG megjelenik — ezért a két állítás
    EGY tesztfájlban, egymás mellett áll."""

    def test_indulaskor_egyetlen_szovegmezo_menu_sincs(self, qml_app):
        window, _controller, _engine = qml_app

        assert window.findChild(QObject, "textFieldContextMenu") is None, (
            "a szövegmező-menü induláskor felépült — a "
            "`TextFieldContextArea` `Component`-je visszakerült "
            "közvetlen deklarációba"
        )

    def test_a_forrasban_egyetlen_kozvetlen_deklaracio_sincs(self):
        """A futásidejű őr csak azt látja, ami a Main.qml alá kerül. Ez az
        állítás a TELJES fát nézi: `TextFieldContextMenu` csak a
        `TextFieldContextArea` `Component`-jében és a saját fájljában
        szerepelhet."""
        talalt = [
            ut.name
            for ut in sorted((_QML_DIR / "PicasaPy").glob("*.qml"))
            if ut.name not in ("TextFieldContextMenu.qml",
                               "TextFieldContextArea.qml")
            and "TextFieldContextMenu {" in ut.read_text(encoding="utf-8")
        ]
        assert talalt == [], (
            "közvetlenül példányosított TextFieldContextMenu: "
            f"{talalt} — a menü a `TextFieldContextArea`-n át jár, hogy "
            "halasztva épüljön (#1720)"
        )


class TestSzovegmezoMenuMukodik:
    """A MŰKÖDÉS őre: a halasztott menü a VALÓDI jobbklikkre megnyílik.

    Nem a `Main.qml`-en mérjük: az indulási fa 29 szövegmezője mind
    csukott párbeszédben ül, tehát ott nincs mire kattintani. A
    `TextFieldContextArea` viszont EGYETLEN komponens — ha egy valódi
    jobbgombos kattintás megnyitja, mind a 29 helyen megnyitja."""

    _QML = (
        "import QtQuick\n"
        "import QtQuick.Controls\n"
        "import QtQuick.Window\n"
        "import PicasaPy 1.0\n"
        "Window {\n"
        "  width: 200; height: 60; visible: true\n"
        '  TextField { id: mezo; objectName: "mezo"; anchors.fill: parent\n'
        '              text: "abc"\n'
        "              TextFieldContextArea { objectName: \"terulet\" } }\n"
        "}\n"
    )

    def test_a_valodi_jobbklikk_felepiti_es_megnyitja_a_menut(
        self, qt_app, qml_app
    ):
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent, QQmlEngine
        from PySide6.QtTest import QTest

        _window, _controller, engine = qml_app
        komponens = QQmlComponent(engine)
        komponens.setData(self._QML.encode("utf-8"), QUrl())
        hibak = [h.toString() for h in komponens.errors()]
        assert hibak == [], hibak
        ablak = komponens.create()
        assert ablak is not None
        QQmlEngine.setObjectOwnership(
            ablak, QQmlEngine.ObjectOwnership.CppOwnership
        )
        try:
            qt_app.processEvents()
            terulet = ablak.findChild(QObject, "terulet")
            assert terulet is not None
            assert terulet.property("contextMenu") is None, (
                "a menü már a jobbklikk előtt felépült"
            )

            QTest.mouseClick(ablak, Qt.MouseButton.RightButton)
            qt_app.processEvents()

            menu = terulet.property("contextMenu")
            assert menu is not None, (
                "a jobbklikk nem hozta létre a szövegmező-menüt — a #1720 "
                "halasztása NÉMÁN hatástalanná tette a #422 menüjét"
            )
            assert menu.findChild(QObject, "textMenuCopy") is not None, (
                "a felépült menüben nincs Másolás tétel"
            )
            assert menu.property("visible") is True, (
                "a menü felépült, de nem nyílt meg"
            )
        finally:
            ablak.deleteLater()
            qt_app.processEvents()
