"""#1526 - a Szerkesztés menü Copy Text / Paste Text tételei a Text-réteget kezelik.

A #5877-ben visszaállított eredeti `Copy Text` / `Paste Text` parancsok a Text
eszköz `text=` rétegét másolják, nem a képfeliratot. A korábbi, külön
felirat-vágólap API-nak (`copyCaptionText`, `pasteCaptionText`, a hozzájuk
tartozó megerősítő párbeszéd) a felületről nem volt hívója, ezért a #7027
megszüntette: az eredetiben a felirat beillesztésének megerősítése a
szövegmezőbe épül, nem a menübe. A megszűnést a `test_felirat_iras_7027.py`
őrzi; ez a fájl a menü bekötését.
"""

from __future__ import annotations

from support.menubar_components_6016 import main_sources, menu_sources

_MENU = menu_sources()
_MAIN = main_sources()


class TestAMenuBekotes:
    def test_a_ket_tetel_mar_NEM_helyfoglalo(self):
        for nev in ("menuEditCopyText", "menuEditPasteText"):
            assert f'objectName: "{nev}"' in _MENU, f"{nev} hiányzik"
            kezd = _MENU.index(f'objectName: "{nev}"')
            blokk = _MENU[kezd : kezd + 400]
            assert "placeholder: true" not in blokk, (
                f"{nev} még helyfoglaló — a felirat ígéret, a hiányzó "
                "funkció pedig hazugság (#1526)"
            )

    def test_a_menutetel_a_szovegreteg_vezerlohoz_kot(self):
        assert "onCopyTextRequested" in _MAIN
        assert "onPasteTextRequested" in _MAIN
        assert "copyTextLayer(" in _MAIN
        assert "pasteTextLayer(" in _MAIN
        assert "copyCaptionText(" not in _MAIN
        assert "pasteCaptionText(" not in _MAIN

    def test_a_beillesztes_a_szovegreteg_pufferet_figyeli(self):
        kezd = _MENU.index('objectName: "menuEditPasteText"')
        blokk = _MENU[kezd : kezd + 500]
        assert "hasTextLayerClipboard" in blokk, (
            "a Paste Text nem a Text-réteg vágólapját figyeli"
        )
        assert "hasSelectedTextLayer" in blokk, (
            "a Text eszközből származó aktuális rétegpuffer nem érhető el"
        )
