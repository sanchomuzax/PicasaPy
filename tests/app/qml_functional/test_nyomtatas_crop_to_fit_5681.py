"""#5681: az első valódi Nyomtatás párbeszéd Crop to Fit módban indul."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QImage

from support.varakozas import var_feltetelre
from tests.app.qml_functional.test_nyomtatas_bekotes_1472 import (
    _elem,
    _kijelol,
    _menubol_nyit,
)
from tests.app.qml_functional.test_nyomtatas_egyseges_meretlista_3712 import (
    _kattints_kozepere,
)


def _lista(ertek):
    return ertek.toVariant() if hasattr(ertek, "toVariant") else ertek


def _forras_url(dialog):
    ertek = _elem(dialog, "printPreviewImage").property("source")
    return ertek.toString() if isinstance(ertek, QUrl) else str(ertek)


def _kepmod_azonos_a_valasztottal(
    dialog, qt_app, print_controller, tmp_path, mode
):
    """A QML tényleges előnézeti PNG-je egyezzen a kiválasztott móddal rajzoltéval."""
    expected_path = tmp_path / f"elvart-{mode}.png"
    assert print_controller.renderPreviewPage(
        _lista(dialog.property("rows")),
        mode,
        str(dialog.property("orientation")),
        int(dialog.property("copies")),
        int(dialog.property("previewPage")),
        str(expected_path),
        str(dialog.property("printerName")),
    ), f"a vezérlő nem készített {mode} előnézeti oldalt"
    expected = QImage(str(expected_path))
    assert not expected.isNull()

    assert var_feltetelre(
        qt_app,
        lambda: _forras_url(dialog)
        == str(dialog.property("previewSource")),
    ), (
        "a nyomtatási előnézet nem követte a párbeszéd képforrását"
    )

    assert dialog.property("fitMode") == mode
    for object_name, expected_checked in (
        ("printFillRadio", "fill"),
        ("printFitRadio", "fit"),
    ):
        assert _elem(dialog, object_name).property("checked") is (
            expected_checked == mode
        )

    source = QUrl(_forras_url(dialog))
    assert source.isLocalFile(), (
        f"az előnézet nem helyi kép: {source}; "
        f"previewPageCount={dialog.property('previewPageCount')}, "
        f"printPageCount={dialog.property('printPageCount')}, "
        f"rows={_lista(dialog.property('rows'))}, "
        f"printSize={dialog.property('printSize')}, "
        f"quality={_lista(dialog.property('quality'))}"
    )
    actual = QImage(source.toLocalFile())
    assert not actual.isNull(), "az előnézet PNG-je nem olvasható"

    assert actual == expected, (
        f"a megjelenített előnézet nem a kiválasztott {mode} illesztést használja"
    )
    return actual


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_elso_megnyitas_crop_to_fit_es_az_elonezet_a_valasztast_koveti(
    qml_app, qt_app, tmp_path, monkeypatch, magassag_elteres
):
    window, _controller, engine = qml_app
    # A Qt-előnézet gyorsítótára a teszt írható, elkülönített területén éljen.
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "qt-cache"))
    _kijelol(window, qt_app, [0])
    dialog = _menubol_nyit(window, qt_app)
    assert var_feltetelre(
        qt_app,
        lambda: dialog.property("visible") is True
        and not dialog.property("meretezesFuggoben"),
    ), "a valódi Nyomtatás párbeszéd nem épült fel"

    celmagassag = round(dialog.height()) + magassag_elteres
    dialog.setProperty("height", celmagassag)
    assert var_feltetelre(qt_app, lambda: round(dialog.height()) == celmagassag), (
        "a párbeszéd nem vette fel a próbamagasságot"
    )

    assert dialog.property("fitMode") == "fill", (
        "az első Nyomtatás párbeszéd nem Crop to Fit módban indult"
    )
    assert _elem(dialog, "printFillRadio").property("checked") is True
    assert _elem(dialog, "printFitRadio").property("checked") is False

    print_controller = engine.rootContext().contextProperty("printController")
    assert print_controller is not None
    assert var_feltetelre(
        qt_app, lambda: bool(dialog.property("previewSource"))
    ), "a látható párbeszéd nem készített előnézeti képforrást"
    fill_preview = _kepmod_azonos_a_valasztottal(
        dialog, qt_app, print_controller, tmp_path, "fill"
    )

    # A teljes kép továbbra is választható, és a valódi kattintás után az
    # előnézet is ugyanazt az új módot rajzolja.
    fit_radio = _elem(dialog, "printFitRadio")
    _kattints_kozepere(dialog, qt_app, fit_radio)
    assert var_feltetelre(qt_app, lambda: dialog.property("fitMode") == "fit"), (
        "a Whole picture rádió nem váltható ki"
    )
    assert var_feltetelre(
        qt_app,
        lambda: _forras_url(dialog)
        == str(dialog.property("previewSource")),
    ), "az előnézet nem követte az illesztésváltást"
    fit_preview = _kepmod_azonos_a_valasztottal(
        dialog, qt_app, print_controller, tmp_path, "fit"
    )
    assert fill_preview != fit_preview, (
        "a tesztkép nem különbözteti meg a Crop to Fit és Whole picture illesztést"
    )

    fill_radio = _elem(dialog, "printFillRadio")
    _kattints_kozepere(dialog, qt_app, fill_radio)
    assert var_feltetelre(qt_app, lambda: dialog.property("fitMode") == "fill"), (
        "a Crop to Fit rádió nem váltható ki"
    )
    visszaallitott_fill = _kepmod_azonos_a_valasztottal(
        dialog, qt_app, print_controller, tmp_path, "fill"
    )
    assert visszaallitott_fill == fill_preview

    _kattints_kozepere(dialog, qt_app, _elem(dialog, "printCloseButton"))
    assert var_feltetelre(qt_app, lambda: not dialog.property("visible")), (
        "a párbeszéd nem zárult be"
    )
