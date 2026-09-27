"""#3741: kettős nézet, „ab"/„aa" módban a nyitott eszköz (Vágás/
Retusálás/Szöveg/Vörösszem) átfedője a FÓKUSZBAN lévő félre essen, ne a
másikra.

## A hiba (mérve, a #3693 (PR #3732) javítása közben)

A `cropOverlay`/`retouchClickArea`/`textClickArea`/`redeyeOverlay` (és a
köztük lévő `frameContentArea`/`editorToolBar`/`paintMaskArea`/
`neutralPickArea`) mind a `photo` (QML `id`) Image-hez volt rögzítve
KÖZVETLENÜL — az a JOBB/ALSÓ fél, csak akkor a fókuszban lévő fotóé, ha
`aktivOldal === "jobb"` (az alapérték). Bal fókusznál (`aktivOldal ===
"bal"`) a ténylegesen szerkesztett fotó a `photoElotte` (BAL/FELSŐ) félen
jelenik meg (`viewerFocusBadge` `fokuszKep` mintája, `PhotoViewer.qml`
2804. sor), de az eszközök átfedője a `photo`-n maradt — vagyis a NEM
kijelölt képen.

## A javítás

A `photoArea.fokuszKep` (`aktivOldal === "bal" ? photoElotte : photo`) az
összes eszközátfedő szülője, ugyanaz a mintázat, mint a „Kijelölve"
jelvényé. Emiatt a `photo`/`photoElotte` TapHandlere is frissült: bal
fókusznál az átfedő már a `photoElotte`-n ül, tehát a `photo` kattintása
onnantól SZABAD — a fókuszváltás a „Szerkesztés jóváhagyása" kapun
(`fokuszValt`) át megy, a #3693 5. pontjának eddig hiányzó másik
irányaként.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QRectF

from tests.app.qml_functional.test_fokuszvaltas_johagyasa_3693 import (
    _nyitva,
)
from tests.app.qml_functional.test_kettos_nezet_gombsor_helye_3663 import (
    _ab_modba,
    _elem_teglalap,
    _gyerek,
    _kep_teglalap,
    _klikk,
)

_TURES = 1.0

#: (átfedő objectName, az eszközt aktiváló `viewerEditorPanel` property)
_ESZKOZOK = (
    ("cropOverlay", "cropActive"),
    ("retouchClickArea", "retouchActive"),
    ("redeyeOverlay", "redeyeActive"),
    ("textClickArea", "textActive"),
)


def _atfedo_teglalapja(window, qt_app, panel, overlay_nev, allapot):
    panel.setProperty(allapot, True)
    qt_app.processEvents()
    overlay = _gyerek(window, overlay_nev)
    r = _elem_teglalap(overlay)
    panel.setProperty(allapot, False)
    qt_app.processEvents()
    return r


class TestAzAtfedoAFokuszbanLevoFelenAll:
    """Kész-ha 1. pont: az eszközátfedők a fókuszban lévő félre kerülnek."""

    @pytest.mark.parametrize(("overlay_nev", "allapot"), _ESZKOZOK)
    def test_jobb_fokusznal_a_jobb_kepen(
        self, qml_app_negyzet_kepek, qt_app, overlay_nev, allapot
    ):
        window, _controller, _engine = qml_app_negyzet_kepek
        nezo = _ab_modba(window, qt_app)
        assert nezo.property("aktivOldal") == "jobb"
        panel = _gyerek(window, "viewerEditorPanel")

        atfedo_r = _atfedo_teglalapja(window, qt_app, panel, overlay_nev, allapot)
        kep_r = _kep_teglalap(_gyerek(window, "viewerImage"))

        for kulcs in ("bal", "fent", "jobb", "lent"):
            assert abs(kep_r[kulcs] - atfedo_r[kulcs]) <= _TURES, (
                f"{overlay_nev} {kulcs} éle {atfedo_r[kulcs]:.1f} px, "
                f"a jobb kép {kulcs} éle {kep_r[kulcs]:.1f} px"
            )

    @pytest.mark.parametrize(("overlay_nev", "allapot"), _ESZKOZOK)
    def test_bal_fokusznal_a_bal_kepen_nem_a_jobbon(
        self, qml_app_negyzet_kepek, qt_app, overlay_nev, allapot
    ):
        window, _controller, _engine = qml_app_negyzet_kepek
        nezo = _ab_modba(window, qt_app)
        _klikk(qt_app, window, _gyerek(window, "viewerSwapFocus"))
        assert nezo.property("aktivOldal") == "bal"
        panel = _gyerek(window, "viewerEditorPanel")

        atfedo_r = _atfedo_teglalapja(window, qt_app, panel, overlay_nev, allapot)
        bal_kep_r = _kep_teglalap(_gyerek(window, "viewerImageElotte"))
        jobb_kep_r = _kep_teglalap(_gyerek(window, "viewerImage"))

        for kulcs in ("bal", "fent", "jobb", "lent"):
            assert abs(bal_kep_r[kulcs] - atfedo_r[kulcs]) <= _TURES, (
                f"{overlay_nev} {kulcs} éle {atfedo_r[kulcs]:.1f} px, "
                f"a bal (fókuszban lévő) kép {kulcs} éle "
                f"{bal_kep_r[kulcs]:.1f} px"
            )
        # rontás-kontroll: a hiba előtt az átfedő a JOBB (nem fókuszban
        # lévő) képen ült, nem a bal oldalon
        assert abs(atfedo_r["bal"] - jobb_kep_r["bal"]) > 10, (
            f"{overlay_nev} még mindig a JOBB (nem fókuszban lévő) képen áll"
        )

    def test_aa_modban_is_a_fokuszbanlevo_felen(
        self, qml_app_negyzet_kepek, qt_app
    ):
        """Kész-ha 1. pont: „aa" módban is — itt a két fél ugyanazt a
        fotót mutatja, tehát a hiba csak az átfedő SAJÁT pozíciójából
        derül ki, nem a képtartalomból."""
        window, _controller, _engine = qml_app_negyzet_kepek
        nezo = _ab_modba(window, qt_app)
        _klikk(qt_app, window, _gyerek(window, "viewerLayoutAa"))
        assert nezo.property("layoutMode") == "aa"
        _klikk(qt_app, window, _gyerek(window, "viewerSwapFocus"))
        assert nezo.property("aktivOldal") == "bal"
        panel = _gyerek(window, "viewerEditorPanel")

        atfedo_r = _atfedo_teglalapja(
            window, qt_app, panel, "cropOverlay", "cropActive"
        )
        bal_kep_r = _kep_teglalap(_gyerek(window, "viewerImageElotte"))

        for kulcs in ("bal", "fent", "jobb", "lent"):
            assert abs(bal_kep_r[kulcs] - atfedo_r[kulcs]) <= _TURES


class TestAJobbKepreKattintasBalFokusznal:
    """Kész-ha 2./3. pont: bal fókusznál a JOBB képre kattintva a
    „Szerkesztés jóváhagyása" kapun át vált a fókusz — a #3693 5.
    pontjának eddig hiányzó másik iránya (a `photoElotte`-ra kattintás
    jobb fókusznál már a #3693-ban lefedett irány,
    `TestAKepreKattintassal` a `test_fokuszvaltas_johagyasa_3693.py`-ban).

    Rontás-kontroll: a javítás előtt a `photo` TapHandlere `cropActive`
    esetén MINDIG le volt tiltva (függetlenül az `aktivOldal`-tól, hiszen
    az átfedő is mindig a `photo`-n ült) — ez a teszt e nélkül a kattintás
    néma no-op maradna, és a párbeszéd sosem nyílna ki.
    """

    def test_modositott_vagasnal_a_jobb_kepre_kattintva_kerdez(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)
        _klikk(qt_app, window, _gyerek(window, "viewerSwapFocus"))
        assert nezo.property("aktivOldal") == "bal"
        panel = _gyerek(window, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        overlay = _gyerek(window, "cropOverlay")
        overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
        overlay.setProperty("hasSelection", True)
        qt_app.processEvents()

        _klikk(qt_app, window, _gyerek(window, "viewerImage"))

        assert _nyitva(window)
        assert nezo.property("aktivOldal") == "bal"

        _klikk(qt_app, window, _gyerek(window, "endEditModalityDiscardButton"))

        assert not _nyitva(window)
        assert nezo.property("aktivOldal") == "jobb"
        assert panel.property("cropActive") is False
