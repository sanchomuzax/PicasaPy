"""A #985 ÁLLAPOTMENTES bekötés-őrei — EGY közös alkalmazáson (#2653).

A #985 tesztfájlja eredetileg mind a 34 esetet egyetlen fájlban vitte,
tesztenként friss `qml_app`-pal. Ez MÉRVE 2233 MiB csúcsot ért el a
futtató 2400 MiB-os memóriaplafonja alatt (93%) — a plafonhoz érve a
kernel visszanyerésbe fordul, és a fájl 94 mp helyett sokszor annyi ideig
fut. (Kontroll: 1600 MiB-os plafonnal ugyanez a 34 teszt négyszer lassabb.)

Ez a fájl azt a 15 esetet viszi, amely **semmilyen tartós állapotot nem
ír**: csak a vezérlő meta-objektumát, egy zárt `collageOpen` property-t és
az ÜRES fülsáv elrendezését olvassa. Ezeknek nem kell tesztenként új app —
a modul-szintű `qml_app_module` egyetlen példánya elég (a mintát a
`test_library_frame_hidden_1026.py` hozta).

⚠️ Ami tartós állapotot ír (lapnyitás, fülváltás, mentés), az a
`test_collage_panel_wiring_985.py`-ban maradt, tesztenkénti appal. A közös
segédek a `support.collage_wiring_985` modulban élnek.
"""

from __future__ import annotations

import pytest

from support.collage_wiring_985 import _elem, _keres, _var


@pytest.fixture(scope="module")
def qml_app(qml_app_module):
    """Egyetlen app a teljes modulra — a tesztjei állapotmentesek.

    A fájl egyetlen tesztje sem nyit lapot, nem vált fült és nem ír
    beállítást; a fülsáv végig ÜRES marad. Aki ide állapotot író tesztet
    tesz, a szomszédjait rontja el — annak a helye a
    `test_collage_panel_wiring_985.py`.
    """
    return qml_app_module


@pytest.fixture(autouse=True)
def _eredeti_ablakmeret(qml_app):
    """A közös ablak mérete minden teszt után visszaáll.

    A `test_ures_fulsavnal_a_tartalom_a_terulet_TETEJEN_kezdodik` három
    mérete `resize()`-zal dolgozik. Tesztenkénti appnál ez magától elmúlt;
    közös appnál a következő tesztre is ráragadna."""
    window = qml_app[0]
    meret = (window.width(), window.height())
    yield
    window.resize(*meret)


# --------------------------------------------------------------------------
# 1. A vezérlő bekötése (`controller.py`)
# --------------------------------------------------------------------------
class TestAVezerloBekotese:
    """A `CollageMixin` (és vele a `CollageSaveMixin`) az `AppController`-ben."""

    def test_az_appcontroller_ismeri_a_kollazs_mixint(self, qml_app):
        from picasapy.app.collage_controller import CollageMixin

        controller = qml_app[1]
        assert isinstance(controller, CollageMixin), (
            "az AppController nem örökli a CollageMixin-t — a QML-ből "
            "egyetlen kollázs-slot sem érhető el"
        )

    def test_az_appcontroller_ismeri_a_mentes_mixint(self, qml_app):
        from picasapy.app.collage_save import CollageSaveMixin

        assert isinstance(qml_app[1], CollageSaveMixin), (
            "a mentes szelete (#949) nincs bekotve - a Kollazs letrehozasa "
            "gomb nem talál slotot"
        )

    @pytest.mark.parametrize(
        "slot",
        [
            "openCollage",
            "closeCollage",
            "createCollage",
            "saveCollageDraft",
            "addClips",
            "setCollageTheme",
            "setCollageBorder",
        ],
    )
    def test_a_slot_a_QML_felol_is_meghivhato(self, qml_app, slot):
        """A QML nem Python-metódust hív, hanem Qt-slotot — ezt kell állítani."""
        meta = qml_app[1].metaObject()
        nevek = {
            meta.method(i).name().data().decode()
            for i in range(meta.methodCount())
        }
        assert slot in nevek, f"a(z) {slot} nem látszik a QML meta-objektumban"

    def test_a_collageOpen_property_letezik_es_zart(self, qml_app):
        assert qml_app[1].property("collageOpen") is False


# --------------------------------------------------------------------------
# 2. A fülsáv ÜRESEN — és a regresszió-mentesség
# --------------------------------------------------------------------------
class TestFulsavUresen:
    """Üres fülsávnál a MAI elrendezés egyetlen képponttal sem csúszhat el.

    A nyitott lapra vonatkozó két állítás a testvérfájlban van: az a
    kettő lapot nyit, tehát állapotot ír."""

    def test_a_fulsav_ott_van_a_jelenetben(self, qml_app, qt_app):
        window = qml_app[0]
        assert _var(qt_app, lambda: _keres(window, "documentTabStrip") is not None)

    def test_ures_fulsavnal_a_savmagassag_nulla(self, qml_app, qt_app):
        window = qml_app[0]
        sav = _elem(window, "documentTabStrip")
        assert _var(qt_app, lambda: sav.height() == 0), (
            f"a fülsáv üresen {sav.height()} px magas — lejjebb tolja a "
            "tartalomterületet, tehát a mai felület megváltozott"
        )

    @pytest.mark.parametrize("meret", [(800, 534), (1280, 800), (1920, 1080)])
    def test_ures_fulsavnal_a_tartalom_a_terulet_TETEJEN_kezdodik(
        self, qml_app, qt_app, meret
    ):
        """A bekötés ELŐTT a `SplitView` `anchors.fill: parent` volt.

        A négy horgonyra bontás után ugyanoda kell esnie: a szülő tetejére
        és a szülő teljes magasságára. Beégetett képpont-küszöb helyett a
        SZÜLŐHÖZ mérünk (a menüsor és az eszköztár magassága platformfüggő,
        a betűméret Linuxon 14, Windowson 12 px volt ugyanarra a szövegre)."""
        window = qml_app[0]
        window.resize(*meret)
        oszto = _elem(window, "mainSplit")
        assert _var(qt_app, lambda: oszto.height() > 0)
        szulo = oszto.parentItem()
        assert _var(qt_app, lambda: oszto.height() == szulo.height()), (
            f"a tartalomterület {oszto.height():.0f} px magas, a szülő "
            f"{szulo.height():.0f} — az üres fülsáv helyet foglal"
        )
        assert round(oszto.y()) == 0, (
            f"a tartalomterület a szülőn belül {oszto.y():.0f} px-nél "
            "kezdődik, nem a 0. soron"
        )
