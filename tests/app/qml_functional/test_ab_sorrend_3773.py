"""#3773: „ab" módban a bal a JELENLEGI kép, a jobb a KÖVETKEZŐ — és
belépéskor a bal a KIJELÖLT.

## A hiba (mérve a #3756 (PR #3765) átnézésekor, referencia-képekből:
`Colab EN 33` „7 of 24", `Colab EN 34` a jobb képre kattintás után
„8 of 24")

Az eredeti Picasában „ab" módba lépéskor a **bal** kép a jelenlegi
(`currentIndex`), a jobb a következő (`abMasikSor`), és a bal a
kijelölt (`aktivOldal === "bal"`, alapérték). A #3013/#3014 óta nálunk
ez fordítva állt: a bal a `abMasikSor` (következő) képet mutatta, a
jobb a `currentIndex`-et (jelenlegit), és az alapfókusz `"jobb"` volt.

Ez a lap a sorrend-cserét rögzíti: a `viewerImageElotte` (bal/felső
Item) mostantól a `currentIndex`-hez, a `viewerImage` (jobb/alsó Item)
a `abMasikSor`-hoz kötött — az `aktivSor`/`_kijeloltSort`/`_masodikSort`
képletek és az alapértelmezett `aktivOldal` ("bal") ezzel összhangban.

A #3741 (saját keretek, `balFokusz`) és a #3756 (jelvény-helyfoglalás)
viselkedése nem sérül: a `balFokusz`/`fokuszKep` a fizikai BAL/JOBB
oldalt jelöli, függetlenül attól, melyik sorszámot mutatja épp az adott
oldal — ezt a `test_kettos_nezet_atfedo_fokusz_3741.py` és a
`test_kettos_nezet_feliratsav_jelveny_3756.py` továbbra is őrzi (a
bennük szereplő alapérték-feltételezéseket ez a jegy igazította).
"""

from __future__ import annotations

from tests.app.qml_functional.test_kettos_nezet_gombsor_helye_3663 import (
    _ab_modba,
    _gyerek,
    _klikk,
)


class TestBelepeskorABalAJelenlegi:
    def test_a_bal_a_kijelolt_belepeskor(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)

        assert nezo.property("aktivOldal") == "bal", (
            "„ab” módba lépéskor a bal oldalnak kell kijelöltnek lennie"
        )

    def test_a_kijelolt_sor_a_jelenlegi_kep(self, qml_app, qt_app):
        """`aktivSor` (a kijelölt oldal sora) a belépéskori alapállapotban
        a `currentIndex`-szel kell egyezzen — ez a bal oldal tartalma."""
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)

        assert nezo.property("aktivSor") == nezo.property("currentIndex")

    def test_a_masodik_sor_a_kovetkezo_kep(self, qml_app, qt_app):
        """A NEM kijelölt (jobb) oldal sora a `abMasikSor` — ez a
        következő kép, amíg a `masodikIndex` nincs külön választva."""
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)

        assert nezo.property("abMasikSor") == nezo.property("currentIndex") + 1


class TestABalOldalASajatSzerkesztese:
    """#3187: a KIJELÖLT oldalt a FŐ szerkesztő-vezérlő rendereli (nincs
    `@masodik` rekesz-kulcs az előnézet-URL-jében), a NEM kijelöltet a
    második rekesz (`@masodik`) — ld. `test_ab_kettos_nezet_3014.py`
    `test_a_masik_oldal_a_SAJAT_rekeszen_at_jon`-ját, a #3773 óta
    FORDÍTOTT oldalhozzárendeléssel."""

    def test_a_bal_oldal_a_FO_vezerlot_kapja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        forras = _gyerek(window, "viewerImageElotte").property("source").toString()
        assert forras.startswith("image://editpreview/"), forras
        assert "@masodik" not in forras, forras

    def test_a_jobb_oldal_a_MASODIK_rekeszt_kapja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        forras = _gyerek(window, "viewerImage").property("source").toString()
        assert forras.startswith("image://editpreview/"), forras
        assert "@masodik" in forras, forras


class TestAFokuszAtviteleNemLapoz:
    """A referencia „7 of 24" → „8 of 24" a jobb képre kattintás UTÁN —
    ez a `aktivSor` (a kijelölt sor) váltása, NEM tényleges lapozás: a
    `currentIndex` a kattintás után is a régi sorban áll, csak az
    `aktivSor` mutat immár a `abMasikSor`-ra."""

    def test_jobb_kepre_kattintva_az_aktivSor_a_kovetkezot_mutatja(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)
        eredeti_current = nezo.property("currentIndex")
        eredeti_masik = nezo.property("abMasikSor")

        _klikk(qt_app, window, _gyerek(window, "viewerImage"))

        assert nezo.property("aktivOldal") == "jobb"
        assert nezo.property("currentIndex") == eredeti_current, (
            "a jobb képre kattintás nem lapozás — a currentIndex nem "
            "mozdulhat el"
        )
        assert nezo.property("aktivSor") == eredeti_masik
