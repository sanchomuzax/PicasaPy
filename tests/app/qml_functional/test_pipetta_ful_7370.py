"""A semleges színű pipetta és a fülek VALÓDI kattintással (#7370).

Az eredeti Picasa a Hangolás fül belépőjében (`0x005d77d0`) kikapcsolja a
pipetta gombját, ha be volt kapcsolva. Nálunk a pipetta állapota fülváltáskor
érintetlen maradt, és a mintavevő felület a fültől függetlenül élt: élesített
pipettával egy másik fülre váltva a képre kattintás `finetune2` réteget írt, a
Hangolásra visszatérve pedig a gomb még lenyomva látszott.

Elvárás:
- a Hangolás fülre lépés kikapcsolja a pipettát (a gomb nincs lenyomva);
- a mintavevő felület csak a Hangolás fülön él;
- a meglévő egyszeri használat (kattintás után kikapcsol) változatlan.

Minden kattintás `QTest.mouseClick`; a teszt sosem emittál és nem hív
`clicked`-et. A mintavételt a `sample_prefix_color` lecserélt példánymetódusa
számolja: ez az egyetlen pont, amin át a `pickNeutralColor` a képhez nyúl
(#7385: a pipetta a finetune2 réteg ELŐTTI lánc képéből mintáz, nem a
megjelenített előnézetből).
"""

from __future__ import annotations

from _szerkeszto_5150_helpers import fulre, item, kattint, nyitott_panel, szerkeszto, varj


def _mintavetel_figyelese(viewer) -> list:
    """A mintavételezés hívásait számoló csonk a szerkesztő-vezérlő szolgáltatóján."""
    hivasok: list = []
    szolgaltato = szerkeszto(viewer)._provider
    eredeti = szolgaltato.sample_prefix_color

    def csonk(kulcs, ut, ops, nx, ny, **kwargs):
        hivasok.append((nx, ny))
        return eredeti(kulcs, ut, ops, nx, ny, **kwargs)

    szolgaltato.sample_prefix_color = csonk
    return hivasok


def _pipetta_elesitve_a_hangolason(window, qt_app, panel) -> None:
    fulre(window, qt_app, "editTabFinetune")
    assert varj(qt_app, lambda: panel.property("activeTab") == 1), (
        "a próba feltétele: a Hangolás fül áll"
    )
    kattint(window, item(window, "finetuneNeutralPicker"), qt_app)
    assert varj(qt_app, lambda: panel.property("neutralPickerActive") is True), (
        "a próba feltétele: a pipetta élesítve"
    )


def test_hangolasra_visszalepve_a_pipetta_ki_van_kapcsolva_es_nem_ir_reteget(
    qml_app_negyzet_kepek, qt_app
):
    window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
    hivasok = _mintavetel_figyelese(viewer)
    _pipetta_elesitve_a_hangolason(window, qt_app, panel)
    fulre(window, qt_app, "editTabEffects")
    assert varj(qt_app, lambda: panel.property("activeTab") == 2)

    fulre(window, qt_app, "editTabFinetune")

    assert varj(qt_app, lambda: panel.property("activeTab") == 1)
    assert panel.property("neutralPickerActive") is False, (
        "a Hangolás fülre lépés nem kapcsolta ki a pipettát"
    )
    assert item(window, "finetuneNeutralPicker").property("active") is False, (
        "a pipettagomb lenyomva látszik a Hangolásra visszatérve"
    )
    kattint(window, item(window, "neutralPickArea"), qt_app)
    assert hivasok == [], "az első képkattintás visszatéréskor mintát vett"
    assert szerkeszto(viewer).property("canUndo") is False, (
        "az első képkattintás visszatéréskor réteget írt a láncra"
    )


def test_masik_fulon_a_kepre_kattintas_nem_vesz_mintat(qml_app_negyzet_kepek, qt_app):
    window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
    hivasok = _mintavetel_figyelese(viewer)
    _pipetta_elesitve_a_hangolason(window, qt_app, panel)

    fulre(window, qt_app, "editTabEffects")

    assert varj(qt_app, lambda: panel.property("activeTab") == 2)
    terulet = item(window, "neutralPickArea")
    assert terulet.property("enabled") is False, (
        "az élesített pipetta mintavevő felülete él a nem Hangolás fülön"
    )
    assert terulet.property("visible") is False
    kattint(window, terulet, qt_app)
    assert hivasok == [], "a nem Hangolás fülön a képkattintás mintát vett"
    assert panel.property("neutralPickerActive") is True, (
        "a nem Hangolás fülön a képkattintás elvette a pipetta állapotát"
    )


def test_hangolason_az_elesitett_pipetta_felulete_el_es_egy_kattintas_utan_kikapcsol(
    qml_app_negyzet_kepek, qt_app
):
    window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
    hivasok = _mintavetel_figyelese(viewer)
    _pipetta_elesitve_a_hangolason(window, qt_app, panel)
    terulet = item(window, "neutralPickArea")
    assert terulet.property("enabled") is True, (
        "a Hangolás fülön az élesített pipetta mintavevő felülete nem él"
    )

    kattint(window, terulet, qt_app)

    assert len(hivasok) == 1, "a Hangolás fülön a képkattintás nem vett mintát"
    assert panel.property("neutralPickerActive") is False, (
        "az egyszeri használat után a pipetta nem kapcsolt ki"
    )
    assert terulet.property("enabled") is False


def test_kettos_nezetben_masik_fulon_a_masik_fel_kattintasa_fokuszt_valt(
    qml_app_negyzet_kepek, qt_app
):
    """Az élesített, de nem Hangolás fülön álló pipetta felülete nem takarja a
    képet, ezért a másik fél kattintása a szokott módon fókuszt vált."""
    window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
    _pipetta_elesitve_a_hangolason(window, qt_app, panel)
    fulre(window, qt_app, "editTabEffects")
    assert varj(qt_app, lambda: panel.property("activeTab") == 2)
    viewer.setProperty("layoutMode", "ab")
    viewer.setProperty("aktivOldal", "jobb")
    masik_fel = item(window, "viewerImageElotte")
    assert varj(qt_app, lambda: masik_fel.width() > 0 and masik_fel.height() > 0)

    kattint(window, masik_fel, qt_app)

    assert varj(qt_app, lambda: viewer.property("aktivOldal") == "bal"), (
        "a nem Hangolás fülön élesített pipetta elnyelte a másik fél kattintását"
    )
