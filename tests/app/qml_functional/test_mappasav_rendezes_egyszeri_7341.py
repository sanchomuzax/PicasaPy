"""#7341: a Mappa menü négy eredeti rendezése a kijelölt mappa képeit írja."""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.ini import load_document
from picasapy.ini.priority import olvasd_a_prioritasokat
from picasapy.scanner import PICASA_INI_NAME
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints,
    _objektum,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    KEPEK,
    app_epitese,
    elokeszit,
    keszits_konyvtarat,
    varj,
)
from tests.app.qml_functional._nezet_menu_5150_helpers import almenu_sora


@pytest.fixture
def mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path, kepeket_keszit=keszits_konyvtarat)


def _sorrend(mappa: Path) -> list[str]:
    prioritasok = olvasd_a_prioritasokat(load_document(mappa / PICASA_INI_NAME))
    return [nev for nev, _hely in sorted(prioritasok.items(), key=lambda item: item[1])]


def _rendezesi_almenu_nyitasa(window, qt_app):
    menu_bar = window.property("menuBar")
    folder_menu = _megnyit(menu_bar, qt_app, "F&older")
    sor, almenu = almenu_sora(window, folder_menu, "menuFolderSortBy")
    _kattints(qt_app, sor)
    assert varj(qt_app, lambda: almenu.property("opened") is True), (
        "a Mappa ▸ Sort By almenü nem nyílt meg"
    )
    return almenu


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_a_negy_eredeti_tetel_egyszeri_keprendezest_vegez(
    mappa_app, qt_app, magassag_elteres
):
    window, controller, _engine = mappa_app
    window.show()
    window.resize(window.width(), window.height() + magassag_elteres)
    window.requestActivate()
    qt_app.processEvents()
    mappa = elokeszit(window, qt_app, controller)

    controller.setFolderSort("name")
    folder_sort = controller.folderSort
    folder_sort_reverse = controller.folderSortReverse

    actions = (
        ("menuFolderSortByName", "name"),
        ("menuFolderSortByDate", "date"),
        ("menuFolderSortBySize", "size"),
    )
    for nev, mod in actions:
        _rendezesi_almenu_nyitasa(window, qt_app)
        tetel = _objektum(window, nev)
        assert tetel is not None, f"{nev} nem található"
        assert tetel.property("checkable") is False, (
            f"{nev} tartós, pipálható beállítás maradt"
        )

        _kattints(qt_app, tetel)

        rendezett = _sorrend(mappa)
        assert set(rendezett) == set(KEPEK), f"a {mod} rendezés nem írta ki a teljes sorrendet"
        assert controller.folderSort == folder_sort
        assert controller.folderSortReverse is folder_sort_reverse
        if mod == "name":
            assert rendezett == sorted(KEPEK)

    meret_sorrend = _sorrend(mappa)
    _rendezesi_almenu_nyitasa(window, qt_app)
    reverse_tetel = _objektum(window, "menuFolderSortReverse")
    assert reverse_tetel is not None, "a Reverse order tétel nem található"
    assert reverse_tetel.property("checkable") is False, (
        "a Reverse order tartós, pipálható beállítás maradt"
    )
    _kattints(qt_app, reverse_tetel)
    menu_forditott = _sorrend(mappa)
    assert menu_forditott == meret_sorrend[::-1]
    assert controller.folderSort == folder_sort
    assert controller.folderSortReverse is folder_sort_reverse

    # A mappasor helyi menüje ugyanezt a `sortFolderBy` parancsot hívja.
    # Ugyanarról a Size-alapról a két út azonos kézi sorrendet ír ki.
    _rendezesi_almenu_nyitasa(window, qt_app)
    meret_tetel = _objektum(window, "menuFolderSortBySize")
    assert meret_tetel is not None
    _kattints(qt_app, meret_tetel)
    assert controller.sortFolderBy(str(mappa), "reverse") is True
    assert _sorrend(mappa) == menu_forditott

    # A menü újbóli megnyitásakor az eredeti négy tétel egyikén sincs pipa.
    _rendezesi_almenu_nyitasa(window, qt_app)
    for nev, _mod in (*actions, ("menuFolderSortReverse", "reverse")):
        tetel = _objektum(window, nev)
        assert tetel is not None
        assert tetel.property("checkable") is False
        assert tetel.property("checked") is False

    changed = _objektum(window, "menuFolderSortByChanged")
    assert changed is not None
    assert changed.property("checkable") is True
    assert changed.property("sajat") is True
    _kattints(qt_app, changed)
    assert controller.folderSort == "changed"
