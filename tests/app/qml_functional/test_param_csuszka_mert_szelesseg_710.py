"""#710 — a paraméter-alpanel csúszkája a MÉRT `editslider`-geometriát kapja.

## Hogyan dőlt el

A kérdés („a paraméter-alpanel csúszkája 191 × 27, mint a Finomhangolás füléé,
vagy panel-széles?") sokáig nyitott volt, és **képernyőképet kértünk** rá. A
tulajdonos 2026-09-18-án joggal visszautasította:

> „Ez nem tőlem kérdezendő adat. Az effekt-alpanel elrendezése … a
> respack.yt / .tre erőforrásokból pontosan kimérhető … Screenshotot nem
> küldök, és azt sem mondom meg, melyik effektet néztem: ez félrevezető
> mintát adna, ha épp az az egy effekt eltér a normától."

A FORRÁS döntött (`docs/specs/ui-audit-editor.md` 4.3/a):

* az `editpanel.tre`-ben mind a négy `editsliderN_container` ugyanannak az
  `editcontrol_well`-nek a gyermeke (`m_centerXY`, `m_hidden`);
* a `tab3`–`tab5` nem hoz létre effekt-specifikus slider-konténert, és a 2–4.
  konténer ugyanahhoz a feldolgozó címhez kötődik (`0x007518e0`);
* a **127 × 27** méret a KÜLÖN `scaleslider` családé (Derítőfény).

⇒ a paraméter-alpanel ugyanazt a **191 × 27** geometriát használja.

## Amit ez a fájl mér — és amit NEM

A csúszka kirajzolt SZÉLESSÉGÉT és a sor teljes szélességét méri az élő
panelen. ⚠️ Nem méri, hogy a panelünk teljes szélessége megegyezik-e az
eredeti 251 képpontos `editcontrol_well`-ével — a mi panelünk állítható, ezért
a csúszka a soron BELÜL középre igazítva ül; a bal margóhoz igazítás egy
eltérő szélességű panelen elcsúsztatná a képtől.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app.application as app_module

from test_param_panel_layout_700 import _child, _open_holga

_QML = Path(app_module._APP_DIR) / "qml" / "PicasaPy"

#: a mért `editslider`-geometria (`szerkeszto-panel-meretek.md` 4.)
MERT_SZELESSEG = 191
MERT_MAGASSAG = 27


class TestACsuszkaMERTSzelessege:
    def test_a_csuszka_191_kepont_szeles(self, qt_app):
        gyoker, _ = _open_holga(qt_app)
        csuszka = _child(gyoker, "effectParamSlider0")
        assert round(csuszka.width()) == MERT_SZELESSEG, (
            f"a csúszka {csuszka.width():.0f} px — a mért `editslider` "
            f"{MERT_SZELESSEG} px (a Finomhangolás füléé ugyanennyi)"
        )

    def test_a_csuszka_magassaga_a_mert_27(self, qt_app):
        gyoker, _ = _open_holga(qt_app)
        csuszka = _child(gyoker, "effectParamSlider0")
        assert round(csuszka.height()) == MERT_MAGASSAG

    def test_a_TARTALOM_tovabbra_is_panel_szeles(self, qt_app):
        """A #700 bejelentése: „a bal szélére szorul a területnek".

        A csúszka fix szélessége NEM szűkítheti a tartalom-oszlopot — az
        első nekifutásom épp ezt rontotta el (körkörös szélesség-kötés).
        """
        gyoker, _ = _open_holga(qt_app, width=280)
        oszlop = _child(gyoker, "effectParamColumn")
        panel = _child(gyoker, "editorEffectParamScroll")
        assert oszlop.width() >= panel.width() - 24

    def test_a_csuszka_a_tartalmon_BELUL_kozepen_ul(self, qt_app):
        gyoker, _ = _open_holga(qt_app, width=280)
        csuszka = _child(gyoker, "effectParamSlider0")
        oszlop = _child(gyoker, "effectParamColumn")
        kozep = csuszka.mapToItem(oszlop, csuszka.width() / 2, 0).x()
        assert abs(kozep - oszlop.width() / 2) <= 1.0, "a csúszka nem a tartalom közepén ül"

    def test_KESKENY_panelen_sem_log_ki(self, qt_app):
        """Ha a panel szűkebb a mért 191-nél, a csúszka befér."""
        gyoker, _ = _open_holga(qt_app, width=160)
        csuszka = _child(gyoker, "effectParamSlider0")
        oszlop = _child(gyoker, "effectParamColumn")
        assert csuszka.width() <= oszlop.width() + 1


class TestASZAMOKEgyHelyenElnek:
    """A mért számok a közös `EditorSlider`-ben állnak, nem a panelekben."""

    def test_a_param_panel_a_KOZOS_komponens_szamait_hasznalja(self):
        forras = (_QML / "EditorParamPanel.qml").read_text(encoding="utf-8")
        assert "paramSlider.mertSzelesseg" in forras
        assert "paramSlider.mertMagassag" in forras

    def test_a_panel_nem_ir_le_sajat_191_et(self):
        forras = (_QML / "EditorParamPanel.qml").read_text(encoding="utf-8")
        kotesek = [
            sor
            for sor in forras.splitlines()
            if "191" in sor and not sor.strip().startswith(("//", "//:", "#"))
        ]
        assert kotesek == [], f"beégetett 191 a kötésekben: {kotesek}"
