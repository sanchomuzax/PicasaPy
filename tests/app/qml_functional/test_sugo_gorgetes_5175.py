"""#5175: a Súgóban témaváltáskor a tartalom a tetejéről indul.

A `HelpDialog.qml` témaváltáskor `szovegGorgeto.contentY = 0`-t állított, de a
`ScrollView`-nak nincs `contentY`-ja: a QML elutasította az értékadást, és a
naplóba hiba került.

A görgetés visszaállását a szövegcserénél a `TextArea` maga is elvégzi (a
kurzor 0-ra áll, a nézet ahhoz igazodik), ezért a próbák két dolgot néznek:
a QML-napló tiszta, és a görgetés a témaváltás után 0. A görgetéshez hosszú
fejezetpárt használunk (a `changelog-user.md` és a `faq.md`, a fejezetlista
1. és 2. sora), hogy a váltás előtt valóban legyen mit visszaállítani.

Minden próba valódi egérrel dolgozik: a görgetés `QWheelEvent`, a témaváltás
`QTest.mouseClick` (a fejezetlista sorára, a Vissza, illetve a Tartalom
gombra). A `contentY`-t nem állítjuk közvetlenül, és a parancsokat sem hívjuk.

A QML-napló: a próba a figyelmeztetéseket és hibákat is rögzíti. A meglévő
őr (`qml_warnings`) csak a `support/qml_warning_filter.py` mintáira figyel,
a „non-existent property" hiba ezek között nincs, ezért itt szó szerint
nézzük a `contentY` említését.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QPoint, QPointF, QtMsgType, Qt, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QWheelEvent

from support.qml_warning_filter import is_qml_script_error
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import _elem_ablaka
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _gyerek,
    _klikk_ablakban,
    _varj,
)
from tests.app.qml_functional.test_parbeszedek2_valodi_5150 import _aktival
from tests.app.qml_functional.test_parbeszedek2_valodi_5150_b import (
    _fejezetsor,
    _sugo_nyit,
)

#: A fejezetlista sorai (a nyitólap a 0.): a hosszú `changelog-user.md` és a `faq.md`.
_HOSSZU_SOR = 1
_MASIK_HOSSZU_SOR = 2


@pytest.fixture
def qml_naplo():
    """A próba alatti Qt-figyelmeztetések és hibák (a QML-hibák is ide kerülnek)."""
    uzenetek: list[str] = []

    def _kezelo(msg_type, context, message):
        if msg_type in (
            QtMsgType.QtWarningMsg,
            QtMsgType.QtCriticalMsg,
            QtMsgType.QtFatalMsg,
        ):
            uzenetek.append(message)

    elozo = qInstallMessageHandler(_kezelo)
    try:
        yield uzenetek
    finally:
        qInstallMessageHandler(elozo)


def _gorgeto(window):
    """A súgó szövegének görgetője: a ScrollView belső Flickable-je (ezen van a `contentY`)."""
    elem = _gyerek(window, "helpTopicText")
    while elem is not None and elem.metaObject().className() != "QQuickFlickable":
        elem = elem.parentItem()
    assert elem is not None, "a súgó szövege nincs görgethető Flickable-ben"
    return elem


def _gorgeto_y(window) -> float:
    return float(_gorgeto(window).property("contentY"))


def _gorgeto_max(window) -> float:
    """A görgetés felső határa: a tartalom magassága mínusz a látható rész."""
    gorgeto = _gorgeto(window)
    return float(gorgeto.property("contentHeight")) - float(gorgeto.property("height"))


def _listasor_kattint(window, qt_app, controller, sugo, sor: int) -> str:
    """Valódi kattintás a fejezetlista `sor`. során; visszaadja a fejezet nevét."""
    lista = _gyerek(window, "helpTopicList")
    assert _varj(qt_app, lambda: _fejezetsor(lista, sor) is not None), (
        f"nincs látható fejezetsor ({sor})"
    )
    elem = _fejezetsor(lista, sor)
    ablak = _elem_ablaka(window, elem)
    _aktival(qt_app, ablak)
    _klikk_ablakban(qt_app, ablak, elem)
    nev = controller.helpTopics[sor]["nev"]
    assert _varj(qt_app, lambda: sugo.property("topic") == nev), (
        "a fejezetsorra kattintás nem váltott témát"
    )
    return nev


def _gorgetes_le(window, qt_app, lepes: int = 3) -> float:
    """Valódi egérgörgővel lefelé görget, és megvárja, míg a tartalom meg nem áll.

    Visszaadja az új görgetési pozíciót.
    """
    gorgeto = _gorgeto(window)
    kozep = gorgeto.mapToScene(QPointF(gorgeto.width() / 2, gorgeto.height() / 2))
    ablak = _elem_ablaka(window, gorgeto)
    for _ in range(lepes):
        esemeny = QWheelEvent(
            kozep,
            kozep,
            QPoint(0, 0),
            QPoint(0, -120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False,
        )
        # valódi görgetőnek van időbélyege; az időbélyeg nélküli esemény után
        # a Flickable a következő görgetéseket elnyelte (szintetikus eseményen)
        esemeny.setTimestamp(int(time.monotonic() * 1000))
        QGuiApplication.sendEvent(ablak, esemeny)
        qt_app.processEvents()
    # a görgetés animált: a tartalom akkor áll, ha már nem mozog
    assert _varj(
        qt_app,
        lambda: _gorgeto_y(window) > 0
        and _gorgeto(window).property("moving") is False,
    ), "a valódi görgetés nem mozdította meg a szöveget"
    return _gorgeto_y(window)


def _qml_hiba(uzenetek: list[str]) -> list[str]:
    """A `contentY` említése és minden QML-szkripthiba a naplóban."""
    return [m for m in uzenetek if "contentY" in m or is_qml_script_error(m)]


class TestTemavaltasGorgetesVisszaall:
    def test_a_listabol_valasztott_hosszu_tema_a_tetejerol_indul(
        self, qml_app, qt_app, qml_naplo
    ):
        window, controller, _engine = qml_app
        sugo = _sugo_nyit(window, qt_app)
        _listasor_kattint(window, qt_app, controller, sugo, _HOSSZU_SOR)
        y_elotte = _gorgetes_le(window, qt_app)

        masodik = _listasor_kattint(window, qt_app, controller, sugo, _MASIK_HOSSZU_SOR)
        assert _varj(qt_app, lambda: _gorgeto_max(window) > y_elotte), (
            "a próba feltétele: az új fejezet görgetési tartománya nem fedi a "
            "régi helyzetet, így a tartalom lekorlátozná a görgetést"
        )
        assert sugo.property("topic") == masodik
        assert not _qml_hiba(qml_naplo), f"QML-hiba a naplóban: {_qml_hiba(qml_naplo)}"
        assert _varj(qt_app, lambda: _gorgeto_y(window) == 0), (
            f"témaváltás után a görgetés a(z) {_gorgeto_y(window)} ponton maradt, "
            "nem a tetején"
        )


class TestVisszaGombGorgetes:
    def test_a_vissza_gomb_az_elozo_hosszu_temara_a_tetejere_gorgeti(
        self, qml_app, qt_app, qml_naplo
    ):
        window, controller, _engine = qml_app
        sugo = _sugo_nyit(window, qt_app)
        elso = _listasor_kattint(window, qt_app, controller, sugo, _HOSSZU_SOR)
        _gorgetes_le(window, qt_app)

        _listasor_kattint(window, qt_app, controller, sugo, _MASIK_HOSSZU_SOR)
        # a második fejezetet is legörgetjük: így a Vissza után a régi helyzet látszana
        _gorgetes_le(window, qt_app)

        vissza = _gyerek(window, "helpBackButton")
        assert vissza.property("enabled") is True, "a próba feltétele: a Vissza aktív"
        ablak = _elem_ablaka(window, vissza)
        _aktival(qt_app, ablak)
        _klikk_ablakban(qt_app, ablak, vissza)

        assert _varj(qt_app, lambda: sugo.property("topic") == elso), (
            "a Vissza gomb nem lépett az előző témára"
        )
        assert not _qml_hiba(qml_naplo), f"QML-hiba a naplóban: {_qml_hiba(qml_naplo)}"
        assert _varj(qt_app, lambda: _gorgeto_y(window) == 0), (
            f"a Vissza után a görgetés a(z) {_gorgeto_y(window)} ponton maradt"
        )


class TestTartalomGombGorgetes:
    def test_a_tartalom_gomb_a_nyitolapra_visz_es_nincs_qml_hiba(
        self, qml_app, qt_app, qml_naplo
    ):
        """A nyitólap rövid, ezért ezen az úton a görgetés 0-ra áll akkor is, ha
        a hiba nincs javítva. A QML-napló ellenőrzése így is fogja a hibát."""
        window, controller, _engine = qml_app
        sugo = _sugo_nyit(window, qt_app)
        _listasor_kattint(window, qt_app, controller, sugo, _HOSSZU_SOR)
        _gorgetes_le(window, qt_app)

        tartalom = _gyerek(window, "helpHomeButton")
        ablak = _elem_ablaka(window, tartalom)
        _aktival(qt_app, ablak)
        _klikk_ablakban(qt_app, ablak, tartalom)

        assert _varj(
            qt_app, lambda: sugo.property("topic") == controller.helpHomeTopic
        ), "a Tartalom gomb nem a nyitólapra lépett"
        assert not _qml_hiba(qml_naplo), f"QML-hiba a naplóban: {_qml_hiba(qml_naplo)}"
        assert _varj(qt_app, lambda: _gorgeto_y(window) == 0), (
            f"a Tartalom után a görgetés a(z) {_gorgeto_y(window)} ponton maradt"
        )
