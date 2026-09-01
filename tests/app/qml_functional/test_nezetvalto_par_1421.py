"""#1421 — a `flatview`/`folderview` pár az eszköztáron.

A #1421 „kihelyezés" csoportjának harmadik (utolsó) darabja. A NÉZET
megvolt (Nézet ▸ Mappanézet, #1454), csak gomb nem vezetett hozzá.

## ⚠️ KIZÁRÓ pár, nem két kapcsoló

Pontosan az egyik aktív — ez a #1464/#1468 rádió-csapdájának a testvére.
Itt nincs `checkable`, tehát a csapda maga nem áll fenn; a két gomb
kizárólagosságát az AZONOS forrásból (`treeViewActive`) származó,
egymást tagadó kötés adja, nem külön állapot.

## Ikonos, mert a mért hely 30 × 22

Ugyanaz a tanulság, mint az `newalbum`-nál (29 × 22): abba felirat nem
fér. A mért méret itt is megmondta a megvalósítást.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

_TOOLBAR = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/MainToolbar.qml"
)
_MAIN = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml/Main.qml"


def _blokk(nev: str) -> str:
    forras = _TOOLBAR.read_text(encoding="utf-8")
    kezdet = forras.index(f'objectName: "{nev}"')
    return forras[kezdet : kezdet + 900]


class TestAKetGomb:
    def test_mindketto_letezik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        for nev in ("toolbarFlatViewButton", "toolbarTreeViewButton"):
            assert window.findChild(QObject, nev) is not None, nev

    def test_a_MERT_meretet_hasznaljak(self):
        """30 × 22 egyenként, 60 × 22 a csoport."""
        for nev in ("toolbarFlatViewButton", "toolbarTreeViewButton"):
            blokk = _blokk(nev)
            assert "width: 30" in blokk and "height: 22" in blokk, nev
        assert "Layout.preferredWidth: 60" in _blokk("toolbarFolderViewToggle")

    def test_ikonosak_nem_feliratosak(self):
        """A 30 × 22-be felirat nem fér — ugyanaz, mint az `newalbum`-nál."""
        for nev in ("toolbarFlatViewButton", "toolbarTreeViewButton"):
            assert "qsTr(" not in _blokk(nev).split("ToolTip.text")[0], nev

    def test_van_buboreksugojuk(self):
        for nev in ("toolbarFlatViewButton", "toolbarTreeViewButton"):
            assert "ToolTip.text" in _blokk(nev), nev


class TestAKizarolagossag:
    def test_egymast_TAGADO_kotes_egy_forrasbol(self):
        """Pontosan az egyik aktív — külön állapot nélkül.

        Két független kapcsolóból lehetne olyan helyzet, hogy egyik sem
        (vagy mindkettő) aktív; a tagadó kötés ezt kizárja."""
        assert "aktiv: !toolbar.treeViewActive" in _blokk("toolbarFlatViewButton")
        assert "aktiv: toolbar.treeViewActive" in _blokk("toolbarTreeViewButton")

    def test_ugyanazt_a_vezerlot_hivja_mint_a_menu(self):
        """Egy állapot, két felület — a Nézet ▸ Mappanézet ugyanezt állítja."""
        fo = _MAIN.read_text(encoding="utf-8")
        assert "folderHierarchyController.setTreeView(false)" in fo
        assert "folderHierarchyController.setTreeView(true)" in fo


class TestAszukAblak:
    def test_a_csoport_elrejtozik(self):
        blokk = _blokk("toolbarFolderViewToggle")
        assert "visible: !toolbar.toolbarCompact" in blokk
        assert "Layout.minimumWidth: 0" in blokk
