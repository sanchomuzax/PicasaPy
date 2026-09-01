"""#1917: a tálca helyi menüje HÉT tétel + elválasztó, nem kettő.

## A lelet

A menü korábban két tételes volt, mert a `Tray::` névtérben **pontosan
két** parancsazonosító van. **A névtér-számlálásból nem következik a menü
hossza:** a másik öt tétel MÁS névterekből öröklődik ide.

## Bizonyíték — bináris, cím szerint

A menü-leíró tábla a `0x00732ee0` címen épül fel (egyszeri init, a
`0xda038c` bitjével őrizve; a bejegyzések a `0xd6edc0`-tól, 20 bájtos
lépésekkel). Hívó: `0x005e7d10`.

| # | parancsazonosító (cím) | angol felirat (cím) |
|---|---|---|
| 1 | `AlbumPhoto::ID_PICTURE_VIEW` (`0xcadb44`) | `&View and Edit` (`0xc8d8b8`) |
| 2 | `Tray::ID_PICTURE_HOLDINPICTURETRAY` (`0xcae618`) | `&Hold Selection` (`0xcae63c`) |
| 3 | `Tray::ID_REMOVE_SELECTION` (`0xcae5e4`) | `&Remove Selection` (`0xcae600`) |
| 4 | `AlbumPhoto::ID_PICTURE_ROTATECLOCKWISE` (`0xcadf04`) | `R&otate Clockwise` (`0xc8d7c4`) |
| 5 | `AlbumPhoto::ID_PICTURE_ROTATECOUNTERCLOCKWISE` (`0xcadbc0`) | `Rotate &Counterclockwise` (`0xc8d778`) |
| 6 | `FolderPhotoWin::ID_FILE_LOCATEONDISK` (`0xcadd5c`) | `&Locate on Disk` (`0xc8c520`) |
| 7 | — | elválasztó (`CMenuBar::Enter`, `0xc8c4e4`) |
| 8 | `AlbumPhotoWin::ID_PICTURE_PROPERTIES` (`0xcadedc`) | `Propert&ies` (`0xc8d800`) |

⚠️ A 2. tétel angol felirata **`&Hold Selection`**, nem „Keep Selection" —
az utóbbi a mi találgatásunk volt.

## Amit ez az őr állít

1. mind a hét tétel + az elválasztó ott van, a MÉRT sorrendben;
2. a feliratok a mért angol alakok (a `&` gyorsbillentyűvel együtt);
3. az öt örökölt tétel jelzése ELJUT a `Main.qml`-ig — nem néma;
4. a régi, találgatott „Keep Selection" felirat nem tér vissza.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

_MENU = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "TrayContextMenu.qml"
).read_text(encoding="utf-8")
_TRAYBAR = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "TrayBar.qml"
).read_text(encoding="utf-8")
_MAIN = (
    Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
).read_text(encoding="utf-8")

#: a MÉRT sorrend — az `objectName` és az angol felirat
_TETELEK = (
    ("trayMenuViewAndEdit", "&View and Edit"),
    ("trayMenuKeepSelection", "&Hold Selection"),
    ("trayMenuRemoveSelection", "&Remove Selection"),
    ("trayMenuRotateRight", "R&otate Clockwise"),
    ("trayMenuRotateLeft", "Rotate &Counterclockwise"),
    ("trayMenuLocate", "&Locate on Disk"),
    ("trayMenuSeparator", None),
    ("trayMenuProperties", "Propert&ies"),
)


class TestATeljesMenu:
    def test_mind_a_nyolc_elem_ott_van(self):
        for nev, _felirat in _TETELEK:
            assert f'objectName: "{nev}"' in _MENU, f"hiányzik: {nev}"

    def test_a_MERT_sorrendben(self):
        helyek = [
            _MENU.index(f'objectName: "{nev}"') for nev, _f in _TETELEK
        ]
        assert helyek == sorted(helyek), (
            "a tételek sorrendje eltér a mérttől (a menü-leíró tábla "
            "felépítési sorrendje, 0x00732ee0)"
        )

    def test_a_MERT_feliratokkal(self):
        for nev, felirat in _TETELEK:
            if felirat is None:
                continue
            kezdet = _MENU.index(f'objectName: "{nev}"')
            blokk = _MENU[kezdet : kezdet + 400]
            assert f'qsTr("{felirat}")' in blokk, f"{nev}: nem {felirat!r}"

    def test_van_ELVALASZTO(self):
        assert "MenuSeparator" in _MENU

    def test_a_talalgatott_felirat_nem_ter_vissza(self):
        assert "Keep Selection" not in _MENU, (
            "a „Keep Selection" " a mi találgatásunk volt; az eredeti "
            "„&Hold Selection" " (0xcae63c)"
        )


class TestAzOtOrokoltTetelNemNEMA:
    """A #1798/#1052 osztálya: a jelzésnek EL KELL JUTNIA a vezérlőig."""

    def test_a_menu_jelzeseit_a_TrayBar_elkapja(self):
        for kezelo in (
            "onViewAndEditRequested",
            "onRotateRightRequested",
            "onRotateLeftRequested",
            "onLocateRequested",
            "onPropertiesRequested",
        ):
            assert kezelo in _TRAYBAR, f"a TrayBar nem fogja el: {kezelo}"

    def test_a_TrayBar_jelzeseit_a_Main_elkapja(self):
        for kezelo in (
            "onViewAndEditRequested",
            "onTrayRotateRightRequested",
            "onTrayRotateLeftRequested",
            "onTrayLocateRequested",
            "onTrayPropertiesRequested",
        ):
            assert kezelo in _MAIN, f"a Main.qml nem fogja el: {kezelo}"

    def test_a_kezelok_a_TALCA_blokkjaban_allnak(self):
        """⚠️ A `Main.qml` több helyen is fogad hasonló nevű jelzést (a rács
        helyi menüje, a menüsor). A tálca kezelőinek a `footer: TrayBar`
        blokkjában kell lenniük — máshová téve a rács menüjének
        tulajdonságát írnák felül, és a QML „Property value set multiple
        times"-szal el sem indulna."""
        talca_kezdet = _MAIN.index("footer: TrayBar {")
        for kezelo in (
            "onTrayRotateRightRequested",
            "onTrayLocateRequested",
            "onTrayPropertiesRequested",
        ):
            assert _MAIN.index(kezelo) > talca_kezdet, (
                f"{kezelo} a TrayBar blokkja ELŐTT áll"
            )
