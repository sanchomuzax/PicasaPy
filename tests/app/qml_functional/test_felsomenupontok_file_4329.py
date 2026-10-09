"""#4329: felső menüpontok — file."""

from pathlib import Path

import pytest

from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _ABLAKMAGASSAG_ELTOLASOK,
    _kattints,
    _kijeloles,
    _magassag,
    _nyisd_meg_felso_menut,
    _objektum,
    _varj,
)


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_file_email_kattintas_a_meglevo_kuldesi_utvonalat_hivja(
    qml_app_email, qt_app, height_offset
):
    window, controller, engine = qml_app_email
    _magassag(window, height_offset)
    _menu_bar, _menu, _fejléc, item = _nyisd_meg_felso_menut(
        qt_app, window, "file", "menuFileEmail"
    )
    assert item.property("enabled") is False
    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: item.property("enabled") is True)

    _kattints(qt_app, item)

    assert _varj(
        qt_app,
        lambda: (
            _objektum(window, "emailChoiceDialog") is not None
            and _objektum(window, "emailChoiceDialog").property("visible")
        ),
    ), "a Fájl ▸ E-Mail nem jutott el a meglévő e-mail választóig"
    dialog = _objektum(window, "emailChoiceDialog")
    attachments = list(dialog.property("attachmentPaths"))
    assert len(attachments) == 1
    assert Path(attachments[0]).name == Path(
        controller.photos.filePathAt(0)
    ).name


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_file_open_in_editor_kattintas_minden_kijelolt_fajlt_elindit(
    qml_app, qt_app, monkeypatch, height_offset
):
    import picasapy.app.fileops_controller as fileops_module

    opened = []
    monkeypatch.setattr(
        fileops_module,
        "_open_url",
        lambda url: opened.append(url.toLocalFile()) or True,
        raising=False,
    )
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    _menu_bar, _menu, _fejléc, item = _nyisd_meg_felso_menut(
        qt_app, window, "file", "menuFileOpenInEditor"
    )
    assert item.property("enabled") is False

    _kijeloles(window, qt_app, [0, 1])
    assert _varj(qt_app, lambda: item.property("enabled") is True)
    vart = [controller.photos.filePathAt(row) for row in (0, 1)]

    _kattints(qt_app, item)

    assert _varj(qt_app, lambda: len(opened) == len(vart))
    assert [Path(path) for path in opened] == [Path(path) for path in vart]
