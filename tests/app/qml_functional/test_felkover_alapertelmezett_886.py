"""#886 — a félkövér alapértelmezett menütétel: PONTOSAN KETTŐ van.

A jegy egyik pontja („félkövér alapértelmezett tétel ott, ahol az
eredetiben van, `SetMenuDefaultItem`") eddig csak annyit tudott, hogy a
hívás LÉTEZIK. Ez a teszt a 2026-09-18-i mérésre épül, amely megadja,
melyik tételről van szó — és azt is, hol NEM lehet félkövér tétel.

## A mérés (Picasa3.exe, `SetMenuDefaultItem` = `[0x00c408bc]`)

Az importnak **egyetlen** hívó függvénye van, a táblavezérelt menüépítő
(`0x0056c5a0`), abban **két** hívóhely:

```
0x0056dbc8  push 0            ; fByPos = 0  -> MF_BYCOMMAND
0x0056dbca  push 0x9cc6       ; a parancsazonosító
0x0056dbd0  call dword ptr [0xc408bc]

0x0056dbee  push 0
0x0056dbf0  push 0x9ca0
0x0056dbf6  call dword ptr [0xc408bc]
```

Három következménye van, és mindhárom mérve:

1. **A harmadik argumentum 0**, tehát az alapértelmezett tételt
   `MF_BYCOMMAND` jelöli ki — parancsazonosító szerint, nem pozícióval.
   A menü sorrendje ezt tehát nem befolyásolja.
2. **A kontextus dönti el, melyik**. A hívás előtti kapu az építő második
   argumentumát (`[esp+0xdc]`, a menütételből kiolvasott `wID`) hasonlítja:
   `0x8a` → `0x9cc6`; `0xa4`, `0x70`, `0x8b` → `0x9ca0`; minden más
   azonosító (köztük a `0x77` és a `0xa6`, az ui-audit B.3 szerinti
   ALBUM-ágak) **alapértelmezett tétel nélkül** marad.
3. **Csak a helyi menü útján van alapértelmezett tétel.** A negyedik
   argumentum (`[esp+0xe4]`) nullán átugorja az egész blokkot; a helyi
   menü belépési pontja (`0x005e7c99`) `1`-et ad át, az építő másik hívója
   (`0x0056f418`) `0`-t — az utóbbi `-1` azonosítóval jön, tehát a
   menüsor-út eleve kizárt.

A két parancsazonosító feliratát a `picasa-gyorsbillentyuk.md` adja:
`0x9ca0` = „Megjelenítés és szerkesztés" (`Enter`, a rácsban álló kép
helyi menüje), `0x9cc6` = „Visszatérés a könyvtárhoz" (`Esc`, a néző
helyi menüje).

## Amit ez a teszt őriz

- a két menüben a félkövér tétel PONTOSAN az, amelyik a mérés szerint az;
- **egyetlen más helyi menünkben sincs félkövér tétel** — a mérés szerint
  a Picasa soha nem állít be más parancsot alapértelmezettnek.

⚠️ Ez **nem** vizuális egyezés-mérés: a félkövérség tényét állítja, nem
azt, hogy a betűkép képpontra egyezik az XP-menüével. Az utóbbihoz
referencia kell, amit a #886 kimond, hogy nem szerezhető meg (a natív
menüt a Windows témamotorja rajzolta).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE: list[object] = []

_QML_PICASAPY = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy"
)

#: A mérés szerinti két alapértelmezett tétel: komponens -> (objectName,
#: parancsazonosító). A parancsazonosító a bizonyíték horgonya — a
#: felirat fordítással változhat, az azonosító nem.
ALAPERTELMEZETT = {
    "PhotoContextMenu": ("contextMenuOpen", "0x9ca0"),
    "TrayContextMenu": ("trayMenuViewAndEdit", "0x9ca0"),
    "ViewerContextMenu": ("viewerMenuBackToLibrary", "0x9cc6"),
}


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _menu(engine, komponens: str):
    component = QQmlComponent(engine)
    component.setData(
        (
            "import QtQuick\nimport PicasaPy 1.0\n"
            f'{komponens} {{ objectName: "menu" }}\n'
        ).encode("utf-8"),
        QUrl(),
    )
    root = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert root is not None
    QQmlEngine.setObjectOwnership(root, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, root))
    return root


def _menutetel(elem: QObject) -> bool:
    """Csak a menüTÉTELEK érdekesek. A tétel belső címkéje (`IconLabel`)
    ÖRÖKLI a betűt, tehát a félkövér tétel alatt mindig megjelenik egy
    félkövér címke is — az nem külön tétel."""
    return "MenuItem" in elem.metaObject().className()


def _felkover(elem: QObject) -> bool:
    """A `font` tulajdonság `QFont`-ként jön vissza; a menütételeken ez a
    Quick Controls összeállított betűje, tehát a `bold` a tényleges
    megjelenítést mondja meg."""
    betu = elem.property("font")
    return bool(betu is not None and betu.bold())


class TestAKetMertAlapertelmezettTetel:
    @pytest.mark.parametrize(
        ("komponens", "nev", "cmd"),
        [(k, *v) for k, v in ALAPERTELMEZETT.items()],
        ids=list(ALAPERTELMEZETT),
    )
    def test_a_mert_tetel_felkover(self, qml_engine, komponens, nev, cmd) -> None:
        menu = _menu(qml_engine, komponens)

        tetel = menu.findChild(QObject, nev)

        assert tetel is not None, f"{komponens}: nincs {nev} tétel"
        assert _felkover(tetel), (
            f"{komponens}: a(z) {cmd} parancs tétele nem félkövér, pedig a"
            " Picasa a SetMenuDefaultItem-mel ezt jelöli ki"
        )


class TestMasTetelNemFelkover:
    """A menü TÖBBI tétele nem lehet félkövér: `SetMenuDefaultItem`-ből
    menünként egy van, és `MF_BYCOMMAND`-dal pontosan egy parancsra."""

    @pytest.mark.parametrize("komponens", list(ALAPERTELMEZETT), ids=list(ALAPERTELMEZETT))
    def test_csak_egy_felkover_tetel_van(self, qml_engine, komponens) -> None:
        menu = _menu(qml_engine, komponens)
        varakozott = ALAPERTELMEZETT[komponens][0]

        felkoverek = sorted(
            elem.objectName()
            for elem in menu.findChildren(QObject)
            if elem.objectName() and _menutetel(elem) and _felkover(elem)
        )

        assert felkoverek == [varakozott], (
            f"{komponens}: a félkövér tételek {felkoverek}, a mérés szerint"
            f" csak {varakozott!r} lehet az"
        )


#: A `font.bold` forrás-szintű előfordulása a helyi menük QML-jeiben. A
#: fenti futásidejű próba csak azokat a menüket tudja betölteni, amelyek
#: önállóan példányosíthatók; a forrás-őr MINDEGYIKRE kiterjed, és a
#: feltételes kötést (`font.bold: valami`) is megfogja.
_BOLD = re.compile(r"font\.bold\s*:")

#: A mérés szerint ebben a két fájlban — és csak ebben — van félkövér
#: menütétel.
_FELKOVERT_TARTALMAZ = {
    "PhotoContextMenu.qml",
    "TrayContextMenu.qml",
    "ViewerContextMenu.qml",
}


def _helyi_menu_fajlok() -> list[Path]:
    return sorted(
        p for p in _QML_PICASAPY.glob("*.qml")
        if "ContextMenu" in p.name
    )


class TestForrasOr:
    def test_van_mit_ellenoriznie(self) -> None:
        """A minta hibája ne látszódjon zöldnek: legyen mit átfésülni, és
        legyen benne a két ismert pozitív is."""
        nevek = {p.name for p in _helyi_menu_fajlok()}

        assert len(nevek) >= 8, nevek
        assert _FELKOVERT_TARTALMAZ <= nevek, nevek

    def test_mas_helyi_menuben_nincs_felkover(self) -> None:
        talalt = {
            p.name
            for p in _helyi_menu_fajlok()
            if _BOLD.search(p.read_text(encoding="utf-8"))
        }

        assert talalt == _FELKOVERT_TARTALMAZ, (
            "a mérés szerint a Picasa csak a 0x9ca0 és a 0x9cc6 parancsot"
            f" jelöli alapértelmezettnek; félkövért tartalmaz: {sorted(talalt)}"
        )
