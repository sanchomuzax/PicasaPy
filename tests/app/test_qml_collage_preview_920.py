"""#920 (1. szelet) — élő kollázs-előnézet a vak renderelés helyett.

A Kollázs eddig VAKON dolgozott: a párbeszédben elrendezést és keretet
kellett választani, a program egyben fájlba renderelt, és a felhasználó
csak utána látta, mit kapott. Az eredetiben a panel jobb oldalán élő vászon
áll.

Ez a szelet az előnézetet és a keverés-gombot hozza. Az őrök a VALÓDI úton
mennek végig (a #936 tanulsága: a párbeszédet közvetlenül hívó teszt zöld
maradhat egy törött felület fölött).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer

from support.qt_wait import hangos_hurok, varj_feltetelre
from tests.support.qml_halasztott import epitsd_fel


def _settle(qt_app, rounds=6):
    for _ in range(rounds):
        qt_app.processEvents()
        pause = QEventLoop()
        QTimer.singleShot(20, pause.quit)
        pause.exec()


def _var(controller, jelzes, hivas, ms=8000):
    """A `jelzes` bevárása a `hivas` után — HANGOS vészfékkel (#1467).

    A hívók eddig is `assert _var(...)`-t írtak, de a bukás-üzenet üres
    volt; a közös segéd megnevezi, MELYIK jelzés maradt el."""
    loop = hangos_hurok(jelzes, timeout_ms=ms)
    hivas()
    loop.exec()
    return loop.jelzes_megjott



@pytest.fixture(autouse=True)
def _felepitett_parbeszedek(qml_app, request):
    """#2096: a Létrehozás-párbeszédek halasztva épülnek fel.

    Ez a fájl a VISELKEDÉSÜKET méri, nem a felépülés pillanatát (azt a
    #1720 őre), ezért a szokásos esetek előtt felépítjük őket — így az
    alábbi `findChild`-ok változatlanul maradhatnak. Az előnézet-hiba teszt
    kivétel: annak azt is mérnie kell, hogy a hibakezelő építi fel a
    párbeszédet, ha addig még nem nyitották meg."""
    if request.node.name != "test_a_valodi_elonezet_hiba_megjelenik_a_felhasznalonak":
        epitsd_fel(qml_app[0], "createDialogs")

class TestElonezet:
    def test_a_kijelolesre_keszul_elonezet(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        assert _var(
            controller,
            controller.collagePreviewReady,
            lambda: controller.requestCollagePreview([0, 1], "picturegrid", "noborder"),
        ), "nem készült előnézet"
        assert controller.collage_preview_provider.has_image

    def test_ures_kijelolesnel_nincs_kep_de_jelez(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        assert _var(
            controller,
            controller.collagePreviewReady,
            lambda: controller.requestCollagePreview([], "picturegrid", "noborder"),
        )
        assert controller.collage_preview_provider.has_image is False

    def test_ismeretlen_tema_hibat_jelez(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        assert _var(
            controller,
            controller.collagePreviewFailed,
            lambda: controller.requestCollagePreview([0], "mandala", "noborder"),
        )


class TestKeveres:
    def test_a_keveres_lepteti_a_magot(self, qml_app):
        window, controller, lib, engine = qml_app
        elozo = controller.collageSeed
        controller.shuffleCollage()
        assert controller.collageSeed == elozo + 1

    def test_a_mentes_a_LATOTT_magot_hasznalja(self, qml_app, qt_app, tmp_path):
        """Amit az előnézeten lát, azt kapja mentéskor is — enélkül a
        keverés-gomb hazudna."""
        window, controller, lib, engine = qml_app
        controller.shuffleCollage()
        mag = controller.collageSeed
        cel = tmp_path / "kollazs.jpg"
        assert _var(
            controller,
            controller.collageFinished,
            lambda: controller.makeCollage([0, 1], "picturepile", str(cel), "noborder"),
            ms=20000,
        )
        assert cel.exists()
        assert controller.collageSeed == mag, "a mentés nem változtathatja a magot"


class TestFelulet:
    def test_a_valodi_elonezet_hiba_megjelenik_a_felhasznalonak(
        self, qml_app, qt_app, monkeypatch
    ):
        window, controller, lib, engine = qml_app
        hiba = "preview render failed"

        def hibas_render(*_args, **_kwargs):
            raise OSError(hiba)

        monkeypatch.setattr(
            "picasapy.app.create_controller.make_picasa_collage", hibas_render
        )
        halasztott = window.findChild(QObject, "createDialogs")
        assert halasztott is not None
        assert halasztott.property("item") is None

        hibak = []
        controller.collagePreviewFailed.connect(hibak.append)
        alapmagassag = window.height()
        for eltolás in (-5, 0, 5):
            ablakmagassag = alapmagassag + eltolás
            window.resize(window.width(), ablakmagassag)
            assert varj_feltetelre(
                qt_app,
                lambda vart=ablakmagassag: window.height() == vart,
                masodperc=3,
            )

            hibak.clear()
            controller.requestCollagePreview([0], "picturegrid", "noborder")
            assert varj_feltetelre(qt_app, lambda: bool(hibak), masodperc=3), (
                "a renderelő valódi hibaága nem futott le"
            )
            assert varj_feltetelre(
                qt_app,
                lambda: (
                    window.findChild(QObject, "createResultDialog") is not None
                    and window.findChild(QObject, "createResultDialog").property(
                        "visible"
                    )
                ),
                masodperc=3,
            ), "a valódi előnézet-hiba nem jutott el a felhasználóig"
            dialog = window.findChild(QObject, "createResultDialog")
            szoveg = window.findChild(QObject, "createResultText")
            assert dialog is not None
            assert szoveg is not None
            assert hibak == [hiba]
            assert "The collage could not be created." in szoveg.property("text")
            assert hiba in szoveg.property("text")
            dialog.metaObject().invokeMethod(dialog, "close")
            assert varj_feltetelre(
                qt_app,
                lambda aktualis=dialog: not aktualis.property("visible"),
                masodperc=3,
            )

    def test_a_parbeszedben_ott_az_elonezet_es_a_keveres(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        dialog = window.findChild(QObject, "collageDialog")
        dialog.metaObject().invokeMethod(dialog, "openForSelection")
        _settle(qt_app, 3)
        assert window.findChild(QObject, "collagePreviewImage") is not None
        assert window.findChild(QObject, "collageShuffleButton") is not None

    def test_forras_nelkul_az_elonezet_rejtve(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [])
        dialog = window.findChild(QObject, "collageDialog")
        dialog.metaObject().invokeMethod(dialog, "openForSelection")
        _settle(qt_app, 3)
        assert window.findChild(QObject, "collagePreviewImage").property("visible") is False
