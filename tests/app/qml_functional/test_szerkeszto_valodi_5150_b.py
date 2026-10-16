"""A Szerkesztő retusálási, visszavonás-sori és szöveg-vezérlői VALÓDI
kattintással (#5150, 8. rész, 2. fájl).

Lefedve (a jegy B-listája, „Szerkesztő" csoport):
- Retusálás: `retouchResetButton`, `retouchUndoPatchButton`,
  `retouchRedoPatchButton`;
- Visszavonás-sor: `editRedoButton`;
- Szöveg: `textCopyCaptionButton`, `textFontSizeBox` (a lenyíló lista
  valódi sorára kattintva), `textBoldButton`, `textItalicButton`,
  `textUnderlineButton`, `textFillDisabledCheck`, `textRemoveAllButton`.

Az állapot-előkészítés a controlleren (retusálási folt, szöveg, felirat)
vagy a már kattintással elért fülön történik. A tesztelt vezérlő mindig
valódi egérkattintás. A hatást a controller állapotán nézzük.
"""

from __future__ import annotations

from PySide6.QtCore import QObject

from _szerkeszto_5150_helpers import (
    folt_veglegesitve,
    item,
    kattint,
    nyitott_panel,
    retusalas_nyitva,
    sor,
    szerkeszto,
    szovegeszkoz,
    varj,
)
from support.qt_wait import wait_for_photo_op


class TestRetusalas:
    def test_visszaallitas_gomb_valodi_kattintasra_uritii_a_foltokat(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        retusalas_nyitva(window, qt_app, panel)
        lanc = szerkeszto(viewer)
        folt_veglegesitve(lanc)
        assert varj(qt_app, lambda: lanc.property("retouchPendingCount") == 1)

        kattint(window, item(window, "retouchResetButton"), qt_app)

        assert varj(qt_app, lambda: lanc.property("retouchPendingCount") == 0), (
            "a Visszaállítás kattintás nem ürítette ki a foltokat"
        )

    def test_folt_visszavonas_gomb_valodi_kattintasra_visszaveszi_a_foltot(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        retusalas_nyitva(window, qt_app, panel)
        lanc = szerkeszto(viewer)
        folt_veglegesitve(lanc)
        assert varj(qt_app, lambda: lanc.property("canUndoPatch") is True), (
            "a próba feltétele: van visszavonható folt"
        )

        kattint(window, item(window, "retouchUndoPatchButton"), qt_app)

        assert varj(qt_app, lambda: lanc.property("retouchPendingCount") == 0), (
            "a Folt visszavonása kattintás nem vette vissza a foltot"
        )
        assert lanc.property("canRedoPatch") is True

    def test_folt_ismetles_gomb_valodi_kattintasra_visszahozza_a_foltot(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        retusalas_nyitva(window, qt_app, panel)
        lanc = szerkeszto(viewer)
        folt_veglegesitve(lanc)
        lanc.undoPatch()
        assert varj(qt_app, lambda: lanc.property("canRedoPatch") is True), (
            "a próba feltétele: van ismételhető folt"
        )

        kattint(window, item(window, "retouchRedoPatchButton"), qt_app)

        assert varj(qt_app, lambda: lanc.property("retouchPendingCount") == 1), (
            "a Folt ismétlése kattintás nem hozta vissza a foltot"
        )


class TestVisszavonasSor:
    def test_ujra_gomb_valodi_kattintasra_visszahozza_az_effektet(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        kattint(window, item(window, "editTabEffects"), qt_app)
        lanc = szerkeszto(viewer)
        kattint(window, item(window, "effectWarm"), qt_app)
        assert varj(
            qt_app, lambda: lanc.property("effectChainCounts").get("warm", 0) == 1
        ), "a próba feltétele: a Warmify a láncon van"
        lanc.undo()
        assert varj(qt_app, lambda: lanc.property("canRedo") is True), (
            "a próba feltétele: az Ismétlés elérhető"
        )

        kattint(window, item(window, "editRedoButton"), qt_app)

        assert varj(
            qt_app, lambda: lanc.property("effectChainCounts").get("warm", 0) == 1
        ), "az Ismétlés kattintás nem tette vissza a Warmify-t"


class TestSzoveg:
    def test_felirat_masolasa_valodi_kattintasra_a_piszkozatba_teszi(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, controller, _viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        wait_for_photo_op(controller, lambda: controller.setCaption(0, "Nyaralas"))
        szovegeszkoz(window, qt_app)
        assert varj(qt_app, lambda: panel.property("textActive") is True)
        assert panel.property("textDraftContent") == "", "a próba feltétele: üres piszkozat"
        assert varj(qt_app, lambda: panel.property("captionText") == "Nyaralas"), (
            "a próba feltétele: a képnek van felirata"
        )

        kattint(window, item(window, "textCopyCaptionButton"), qt_app)

        assert varj(qt_app, lambda: panel.property("textDraftContent") == "Nyaralas"), (
            "a Felirat másolása kattintás nem másolta a feliratot"
        )

    def test_betumeret_valodi_kattintasra_a_listabol_valasztva_allitja(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        szovegeszkoz(window, qt_app)
        assert varj(qt_app, lambda: panel.property("textActive") is True)
        lanc = szerkeszto(viewer)
        valasztasok = list(panel.property("fontSizeChoices"))
        assert len(valasztasok) > 1, "a betűméret-lista üres"
        index = 0 if valasztasok[0] != lanc.property("textFontSize") else 1
        cel = valasztasok[index]
        assert lanc.property("textFontSize") != cel, "a próba feltétele: más méret"

        doboz = item(window, "textFontSizeBox")
        kattint(window, doboz, qt_app)
        popup = doboz.findChild(QObject, "picasaComboPopup")
        lista = doboz.findChild(QObject, "picasaComboList")
        assert popup is not None and lista is not None, "a betűméret-lista nem nyílt meg"
        assert varj(qt_app, lambda: popup.property("visible") is True)
        elem = sor(lista, index, qt_app)
        kattint(elem.window(), elem, qt_app)

        assert varj(qt_app, lambda: lanc.property("textFontSize") == cel), (
            "a betűméret-választás nem állította be a méretet"
        )

    def test_felkover_valodi_kattintasra_bekapcsolja(self, qml_app_negyzet_kepek, qt_app):
        window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        szovegeszkoz(window, qt_app)
        assert varj(qt_app, lambda: panel.property("textActive") is True)
        lanc = szerkeszto(viewer)
        assert lanc.property("textBold") is False

        kattint(window, item(window, "textBoldButton"), qt_app)

        assert varj(qt_app, lambda: lanc.property("textBold") is True), (
            "a Félkövér kattintás nem kapcsolta be"
        )

    def test_dolt_valodi_kattintasra_bekapcsolja(self, qml_app_negyzet_kepek, qt_app):
        window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        szovegeszkoz(window, qt_app)
        assert varj(qt_app, lambda: panel.property("textActive") is True)
        lanc = szerkeszto(viewer)
        assert lanc.property("textItalic") is False

        kattint(window, item(window, "textItalicButton"), qt_app)

        assert varj(qt_app, lambda: lanc.property("textItalic") is True), (
            "a Dőlt kattintás nem kapcsolta be"
        )

    def test_alahuzott_valodi_kattintasra_bekapcsolja(self, qml_app_negyzet_kepek, qt_app):
        window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        szovegeszkoz(window, qt_app)
        assert varj(qt_app, lambda: panel.property("textActive") is True)
        lanc = szerkeszto(viewer)
        assert lanc.property("textUnderline") is False

        kattint(window, item(window, "textUnderlineButton"), qt_app)

        assert varj(qt_app, lambda: lanc.property("textUnderline") is True), (
            "az Aláhúzott kattintás nem kapcsolta be"
        )

    def test_kitoltes_jelolo_valodi_kattintasra_kikapcsolja_a_kitoltest(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        szovegeszkoz(window, qt_app)
        assert varj(qt_app, lambda: panel.property("textActive") is True)
        lanc = szerkeszto(viewer)
        assert lanc.property("textFillEnabled") is True, "a próba feltétele: van kitöltés"

        kattint(window, item(window, "textFillDisabledCheck"), qt_app)

        assert varj(qt_app, lambda: lanc.property("textFillEnabled") is False), (
            "a kitöltés-kikapcsoló kattintás nem kapcsolta ki a kitöltést"
        )

    def test_mindent_torol_gomb_valodi_kattintasra_eltavolitja_a_szoveget(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        szovegeszkoz(window, qt_app)
        assert varj(qt_app, lambda: panel.property("textActive") is True)
        lanc = szerkeszto(viewer)
        # állapot-előkészítés: egy szöveg a képen
        lanc.previewTextPlacement(0.3, 0.6)
        lanc.setTextDraft("Nyaralas")
        lanc.applyText()
        assert varj(qt_app, lambda: lanc.property("hasTextOverlay") is True), (
            "a próba feltétele: van szöveg a képen"
        )

        kattint(window, item(window, "textRemoveAllButton"), qt_app)

        assert varj(qt_app, lambda: lanc.property("hasTextOverlay") is False), (
            "a Mindent töröl kattintás nem törölte a szöveget"
        )
