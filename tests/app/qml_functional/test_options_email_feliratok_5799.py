"""Az Opciók E-mail fülének eredeti Picasa-feliratai (#5799)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QTranslator
from PySide6.QtQuick import QQuickItem

import picasapy.app
from tests.app.qml_functional.test_parbeszedek_valodi_5150_b import (
    _beallitasok_megnyit,
    _fulre_kattint,
    _varj,
    _zar,
)

_I18N_DIR = Path(picasapy.app.__file__).parent / "i18n"
_ELVART_FELIRATOK = {
    "E-mail program:",
    "Size for multiple pictures:",
    "Size for single pictures:",
    "Send movies as:",
    "Full movie",
}


def _lathato_szovegek(gyoker: QObject) -> set[str]:
    return {
        str(szoveg)
        for elem in gyoker.findChildren(QQuickItem)
        if elem.isVisible()
        and (szoveg := elem.property("text")) is not None
        and str(szoveg)
    }


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_email_ful_valodi_kattintassal_az_eredeti_feliratokat_mutatja(
    qml_app, qt_app, magassageltolas
):
    window, _controller, engine = qml_app
    translator = QTranslator(qt_app)
    assert translator.load("picasapy_en", str(_I18N_DIR)), "az angol fordítás nem tölthető be"
    qt_app.installTranslator(translator)
    engine.retranslate()

    options = _beallitasok_megnyit(window, qt_app)
    alapmagassag = options.height()
    options.setProperty("height", alapmagassag + magassageltolas)
    assert _varj(
        qt_app, lambda: options.height() == alapmagassag + magassageltolas
    ), f"az Opciók ablak magassága nem vette fel a {magassageltolas:+d} px eltérést"

    _fulre_kattint(qt_app, options, "optionsTabEmail", 1)
    lathato = _lathato_szovegek(options)
    assert _ELVART_FELIRATOK <= lathato, (
        "az E-mail fül nem az eredeti Picasa-feliratokat mutatja; "
        f"hiányzik: {sorted(_ELVART_FELIRATOK - lathato)}; "
        f"látható szövegek: {sorted(lathato)}"
    )

    kep_utvonal = os.environ.get("PICASAPY_5799_SCREENSHOT")
    if kep_utvonal and magassageltolas == 0:
        cel = Path(kep_utvonal)
        cel.parent.mkdir(parents=True, exist_ok=True)
        kep = options.grabWindow()
        assert not kep.isNull(), "az E-mail fül kiadásképe üres"
        assert kep.save(str(cel)), f"az E-mail fül kiadásképe nem menthető: {cel}"

    _zar(qt_app, options)
    qt_app.removeTranslator(translator)
