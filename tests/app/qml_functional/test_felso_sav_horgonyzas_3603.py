"""A felső eszköztár bal gombsora és a keresősáv horgonyzása — KIRAJZOLVA
(#3603, a #3582 R2/R3-összevetésének két talált eltérése).

## Honnan jönnek a számok

A tulajdonos 1920 px széles Picasa-képernyőképe
(`research/testdata/screenshot/Képernyőkép 2026-07-18 150933.png`) +
a `thumbui.tre`/`searchcontainer.tre` kényszerei, levezetve a
`docs/specs/picasa-fo-ablak-elrendezes.md` „R2/R3" szakaszában:

- a négy bal gomb FIX bal-felső horgonyú (`m_offsetLT`): x 6 / 124 / 160
  (190) / 225, mind y 9 a sáv tetejétől — az ablakszélességtől FÜGGETLEN;
- a szűrőzóna bal széle `0,4 · W − 2` (`filterbase`);
- a keresőmező látható kerete (`searchbase`, 24 magas) bal széle
  `0,4 · W + 238`, jobb széle `W − 47`.

A képernyőkép (W = 1920) ezt adja: Importálás 6, új album 124,
nézetváltó 160, ▾ 225, szűrők 766, mező 1006 … 1872.

## Miért KIRAJZOLT, jelenet-koordinátában

A `MainToolbar.qml` a `Main.qml` `header:`-je — a `mainToolbar`
koordinátarendszerében mérünk (`mapToItem`), mert a bal gombsor és a
kereső/szűrő-zóna a `content` belső `Item` gyerekei, nem közvetlenül a
sávé.

## A verzió-címke ütközése — NYITOTT PONT

A keresőmező jobb széle a képlet szerint `W − 47` lenne, ez viszont
ÜTKÖZNE a verzió-címkével (#706 — Picasa eredetijében ott semmi nincs,
ez a mi hozzáadott elemünk, ~89 px széles). A #3603 ezt nem mondja ki:
a mező jobb széle ezért a verzió-címke ELŐTT áll meg, nem pontosan
`W − 47`-nél — ezt a tesztek is így mérik (felső korlátként, nem
egyenlőségként). A pontos elrendezés (mozduljon-e/zsugorodjon-e a
verzió-címke) tulajdonosi döntés.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF

#: Fél képpont tűrés: a QML geometriája tört szám lehet.
TURES = 0.5

#: A mért ablakszélességek.
ABLAKOK = (1280, 1600, 1920)


def _elem(window, nev: str) -> QObject:
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található a kirajzolt fában"
    return obj


def _szelesseg(window, qt_app, szelesseg: int) -> None:
    window.setProperty("width", szelesseg)
    for _ in range(4):
        qt_app.processEvents()


def _x_a_savban(window, nev: str) -> float:
    sav = _elem(window, "mainToolbar")
    elem = _elem(window, nev)
    return elem.mapToItem(sav, QPointF(0, 0)).x()


def _y_a_savban(window, nev: str) -> float:
    sav = _elem(window, "mainToolbar")
    elem = _elem(window, nev)
    return elem.mapToItem(sav, QPointF(0, 0)).y()


class TestABalGombsorFixHelye:
    """A négy gomb x/y-ja NEM függ az ablakszélességtől."""

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_negy_gomb_x_helye(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        assert _x_a_savban(window, "toolbarImportButton") == pytest.approx(6, abs=TURES)
        assert _x_a_savban(window, "toolbarNewAlbumButton") == pytest.approx(124, abs=TURES)
        assert _x_a_savban(window, "toolbarFolderViewToggle") == pytest.approx(160, abs=TURES)
        assert _x_a_savban(window, "toolbarFolderViewPopupButton") == pytest.approx(225, abs=TURES)

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_nezetvalto_par_belso_x_helye(self, qml_app_module, qt_app, ablak):
        """`flatview` 160, `folderview` 190 — a `hviewtoggle` csoporton belül."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        assert _x_a_savban(window, "toolbarFlatViewButton") == pytest.approx(160, abs=TURES)
        assert _x_a_savban(window, "toolbarTreeViewButton") == pytest.approx(190, abs=TURES)

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_negy_gomb_teteje_a_sav_tetejetol_9(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        for nev in (
            "toolbarImportButton",
            "toolbarNewAlbumButton",
            "toolbarFolderViewToggle",
            "toolbarFolderViewPopupButton",
        ):
            assert _y_a_savban(window, nev) == pytest.approx(9, abs=TURES), nev


class TestASzuroesKeresoKeplet:
    """A szűrőzóna és a keresőmező bal széle az ablakszélesség FÜGGVÉNYE."""

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_szurozona_bal_szele(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        vart = 0.4 * ablak - 2
        assert _x_a_savban(window, "toolbarFilterZone") == pytest.approx(vart, abs=TURES)

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_keresomezo_bal_szele(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        vart = 0.4 * ablak + 238
        assert _x_a_savban(window, "toolbarSearchBox") == pytest.approx(vart, abs=TURES)

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_keresomezo_24_magas(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        kereso = _elem(window, "toolbarSearchBox")
        assert kereso.property("height") == 24

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_keresomezo_jobb_szele_nem_lepi_at_a_kepletet(
        self, qml_app_module, qt_app, ablak
    ):
        """A jobb szél FELSŐ korlátja `W − 47` — a verzió-címke (#706)
        miatt ehelyütt nem éri el pontosan, ld. a fájl fejléce."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        kereso = _elem(window, "toolbarSearchBox")
        jobb_szel = _x_a_savban(window, "toolbarSearchBox") + kereso.property("width")
        assert jobb_szel <= ablak - 47 + TURES

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_keresomezo_nem_fedi_a_verziocimket(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        kereso = _elem(window, "toolbarSearchBox")
        jobb_szel = _x_a_savban(window, "toolbarSearchBox") + kereso.property("width")
        verzio_bal_szel = _x_a_savban(window, "versionLabel")
        assert jobb_szel <= verzio_bal_szel + TURES


class TestASzukAblakosElrejtesNemUtkozik:
    """A #423 elrejtése (`toolbarCompact`, 1080px) a küszöb ALATT dolgozik —
    a küszöbnél/felette a fix gombsor és a szűrőzóna nem ütközhet."""

    @pytest.mark.parametrize("ablak", (1080, 1280, 1920))
    def test_nincs_atfedes_a_gombsor_es_a_szurozona_kozott(
        self, qml_app_module, qt_app, ablak
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        popup = _elem(window, "toolbarFolderViewPopupButton")
        gombsor_jobb_szel = (
            _x_a_savban(window, "toolbarFolderViewPopupButton")
            + popup.property("width")
        )
        szurozona_bal_szel = _x_a_savban(window, "toolbarFilterZone")
        assert szurozona_bal_szel >= gombsor_jobb_szel, (
            f"{ablak}px-nél a szűrőzóna ({szurozona_bal_szel}) a fix "
            f"gombsor ({gombsor_jobb_szel}) elé csúszott"
        )
