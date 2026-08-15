"""A Visszavonás/Újra sor garanciája KIKÉNYSZERÍTVE — #703.

**Miért kellett ez a készlet a #641 tesztjei MELLÉ.** A #641 a garanciát az
ablak minimális magasságára tette (`Main.qml: minimumHeight`), a tesztje
viszont a néző elrendezésének MÁSÁT építette fel, és a panel igényéhez
méretezte az ablakot. Két dolgot nem látott ezért:

1. **A bejelentett minimum nem biztos, hogy kiadható.** Élesben — a valódi
   `Main.qml`-lel, betöltött képpel, tehát BÉLYEGKÉPES csempékkel — a panel
   igénye 887 képpont (a legmagasabb fül, a #571 „Régi effektek", egymaga
   799), az ablak minimuma ebből 962. Ez több, mint amennyi egy 768 vagy
   900 képpontos kijelzőn egyáltalán van: a garancia ilyenkor nem
   „majdnem" teljesül, hanem **egyáltalán nem** — az ablakkezelő vagy a
   képernyőnél magasabb ablakot ad (a panel alja, benne a gombsor, a
   képernyő alá kerül), vagy figyelmen kívül hagyja a kérést.
2. **A `visibleHeight` csak a KÖZVETLEN szülőt nézte.** Ha egy távolabbi ős
   nyúlik túl, a panel a saját dobozán belül rendben van, a gombsor mégis az
   ablakon kívülre kerül.

Ezért itt a mérés (a) a VALÓDI `Main.qml`-ben, az ABLAK
koordinátarendszerében történik — azon a szinten, ahol a garanciát adják —,
és (b) a túlnyúló ŐS esetét is felépíti, nem csak a szülőét.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Property, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem

_KEEPALIVE: list[object] = []


# --------------------------------------------------------------------------
# közös segédek — a #651 mintája: a VIZUÁLIS fát járjuk be, mert a
# `Repeater`/`GridLayout` delegáltjait a `findChild` nem találja meg
# --------------------------------------------------------------------------
def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _child(root: QQuickItem, name: str) -> QQuickItem:
    for item in _walk(root):
        if item.objectName() == name:
            return item
    found = root.findChild(QObject, name)
    assert found is not None, f"{name} nem található a kirajzolt fában"
    return found


def _bottom_in_window(item: QQuickItem) -> float:
    """Az elem aljának Y-koordinátája az ABLAK rendszerében."""
    return item.mapToScene(item.boundingRect().bottomLeft()).y()


def _top_in_window(item: QQuickItem) -> float:
    return item.mapToScene(item.boundingRect().topLeft()).y()


# ==========================================================================
# 1. A VALÓDI alkalmazás: a bejelentett ablak-minimumnak KIADHATÓNAK kell
#    lennie a képernyőn — különben a garancia nem garancia
# ==========================================================================
def _open_viewer(window, qt_app):
    """A néző megnyitása az első képen — így lesznek BÉLYEGKÉPES csempék.

    Bélyegkép nélkül a csempe ~24 képpont, élesben ~98; a panel igénye 481
    helyett 887. A #641 mérése pontosan azért nyugtatott meg hamisan, mert a
    kisebbik számmal dolgozott.
    """
    window.setProperty("viewerOpen", True)
    viewer = _child(window.contentItem(), "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    return viewer


class TestAzAblakMinimumaKiadhato:
    """#703/1. — a garancia csak akkor garancia, ha a kijelzőre ráfér."""

    def test_az_ablak_minimuma_belefer_a_kepernyobe(self, qml_app, qt_app) -> None:
        window, _controller, _engine = qml_app
        _open_viewer(window, qt_app)

        elerheto = qt_app.primaryScreen().availableGeometry().height()

        assert window.property("minimumHeight") <= elerheto, (
            f"az ablak bejelentett minimuma {window.property('minimumHeight'):.0f} "
            f"px, a képernyőn viszont csak {elerheto} px érhető el — az "
            "ablakkezelő ezt nem tudja teljesíteni, és a panel alja "
            "(vele a Visszavonás/Újra sor) a képernyő alá kerül (#703)"
        )

    def test_az_ablak_a_minimumara_meretezheto(self, qml_app, qt_app) -> None:
        """Nem elég kicsinek lennie: tényleg fel is kell venni azt a méretet."""
        window, _controller, _engine = qml_app
        _open_viewer(window, qt_app)

        minimum = window.property("minimumHeight")
        window.setHeight(minimum)
        qt_app.processEvents()

        assert window.property("height") <= minimum + 1

    @pytest.mark.parametrize("magassag", [900, 800, 700])
    def test_a_gombsor_az_ablakon_belul_van_elesben(
        self, qml_app, qt_app, magassag: int
    ) -> None:
        """A #703 mérése ott, ahol a garanciát adják: a valódi ablakban.

        A #641 tesztje a néző MÁSÁT mérte; ez a valódi `Main.qml`-t, a
        menüsorral, eszköztárral és az alsó tálcával együtt."""
        window, _controller, _engine = qml_app
        _open_viewer(window, qt_app)
        window.setHeight(magassag)
        qt_app.processEvents()

        sor = _child(window.contentItem(), "editorGlobalUndoRow")
        tenyleges = window.property("height")

        assert _bottom_in_window(sor) <= tenyleges + 0.5, (
            f"{tenyleges:.0f} px magas ABLAKBAN a Visszavonás/Újra sor alja "
            f"{_bottom_in_window(sor):.0f} px-nél van (#703)"
        )

    def test_a_sor_a_lathato_terulet_aljan_ul(self, qml_app, qt_app) -> None:
        """Ellenpróba: ne is ugorjon fel a panel tetejére."""
        window, _controller, _engine = qml_app
        _open_viewer(window, qt_app)

        sor = _child(window.contentItem(), "editorGlobalUndoRow")
        panel = _child(window.contentItem(), "viewerEditorPanel")

        assert _bottom_in_window(sor) >= _bottom_in_window(panel) - 12


# ==========================================================================
# 2. A túlnyúló ŐS esete — a `visibleHeight` nem állhat meg a szülőnél
# ==========================================================================
#: A panel doboza rendben van a SZÜLŐJÉN belül; a túlnyúlás egy szinttel
#: feljebb történik. A #641 `visibleHeight`-je (min(height, parent.height))
#: ezt nem látja, mert a szülő ugyanolyan túlnyúló, mint a panel.
_TULNYULO_OS_QML = """
import QtQuick
import PicasaPy 1.0
Item {
    objectName: "gyoker"
    Item {
        objectName: "tulnyuloOs"
        anchors.top: parent.top
        anchors.left: parent.left
        width: 280
        height: 2000            // szándékosan több, mint az ablak
        Rectangle {
            objectName: "panelDoboz"
            anchors.fill: parent
            EditorPanel {
                objectName: "panel"
                anchors.fill: parent
                activeTab: 2
            }
        }
    }
}
"""


class _EditControllerStub(QObject):
    """Annyi az EditControllerből, amennyitől a csempék BÉLYEGKÉPESEK.

    Nem kényelmi részlet: bélyegkép nélkül a csempe ~24 képpont magas,
    élesben ~98 — a 3. fül igénye 158 helyett 432. Enélkül a szűk panelre
    írt állítások hamisan megnyugtatnak (a #651 tanulsága).
    """

    @Property(str, constant=True)
    def previewSource(self):
        return "image://editpreview/42?rev=1"

    @Property("QVariantList", constant=True)
    def legacyEffectsInChain(self):
        return []


def _render(qt_app, qml: str, width: int, height: int):
    import picasapy.app.application as app_module
    from PySide6.QtQuick import QQuickView

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    stub = _EditControllerStub()
    view.engine().rootContext().setContextProperty("editController", stub)
    view.engine().rootContext().setContextProperty("controller", None)
    _KEEPALIVE.append(stub)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

    component = QQmlComponent(view.engine())
    component.setData(qml.encode("utf-8"), QUrl())
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(width, height)
    root.setWidth(width)
    root.setHeight(height)
    QQmlEngine.setObjectOwnership(root, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((view, root, component))
    view.show()
    # a jelenetgyökér magassága csak az elrendezés lefutása után áll be —
    # e nélkül a mérés egy még ki nem alakult képet néz
    qt_app.processEvents()
    return root


class TestATulnyuloOsEseteIs:
    """#703/1. — „ha egy ős túlnyúlik, a mai `visibleHeight` sem véd"."""

    @pytest.mark.parametrize("magassag", [800, 600, 480])
    def test_a_sor_a_tulnyulo_os_alatt_is_az_ablakban_marad(
        self, qt_app, magassag: int
    ) -> None:
        gyoker = _render(qt_app, _TULNYULO_OS_QML, 400, magassag)

        sor = _child(gyoker, "editorGlobalUndoRow")

        assert _bottom_in_window(sor) <= magassag + 0.5, (
            f"a gombsor alja {_bottom_in_window(sor):.0f} px-nél van egy "
            f"{magassag} px magas ablakban — a túlnyúló ŐS levitte magával "
            "(#703)"
        )

    def test_a_sor_nem_ugrik_a_panel_tetejere(self, qt_app) -> None:
        """Ellenpróba: a korlátozás nem tolhatja fel a sort a rács közé."""
        gyoker = _render(qt_app, _TULNYULO_OS_QML, 400, 800)

        sor = _child(gyoker, "editorGlobalUndoRow")

        assert _top_in_window(sor) > 400, (
            "a gombsor a látható terület felső felébe került — a korlátozás "
            "túl szigorú"
        )


# ==========================================================================
# 3. A szükség-ág: ha a hely tényleg kevés, a FÜL TARTALMA veszít — és ez
#    MÉRHETŐ állapot, nem „valahogy működik"
# ==========================================================================
_SZUK_PANEL_QML = """
import QtQuick
import PicasaPy 1.0
Item {
    objectName: "gyoker"
    Rectangle {
        objectName: "panelDoboz"
        anchors.fill: parent
        EditorPanel {
            objectName: "panel"
            anchors.fill: parent
            activeTab: 2
        }
    }
}
"""


class TestASzuksegAgMerheto:
    """#703/3–4. — vágás KIZÁRÓLAG a szükség-ágon, és kimutathatóan."""

    def test_a_belyegkepes_csempek_hajtjak_a_merest(self, qt_app) -> None:
        """A csonk tényleg bekapcsolja a bélyegképeket — az őrnek foga van.

        Ha ez elromlik, a fenti szűk-panel-állítások észrevétlenül
        elveszítik az élüket (24 px-es csempékkel minden „elfér")."""
        gyoker = _render(qt_app, _SZUK_PANEL_QML, 280, 900)
        panel = _child(gyoker, "panel")

        assert panel.property("tallestTabHeight") > 400, (
            "a csempék bélyegkép nélkül alacsonyak — a csonk nem ér el a "
            "panelig, és a szűk-panel-tesztek értelmüket vesztették"
        )

    def test_bo_helyen_nincs_vagas(self, qt_app) -> None:
        gyoker = _render(qt_app, _SZUK_PANEL_QML, 280, 900)
        panel = _child(gyoker, "panel")

        assert panel.property("tabContentTruncated") is False, (
            "bő helyen is vágottnak jelenti magát a fülterület — a #422 "
            "kifejezetten visszavonta, hogy a vágás/görgetés alapállapot legyen"
        )
        assert _child(gyoker, "editorTabArea").property("clip") is False

    def test_szuk_helyen_a_vagas_bekapcsol(self, qt_app) -> None:
        gyoker = _render(qt_app, _SZUK_PANEL_QML, 280, 300)
        panel = _child(gyoker, "panel")

        assert panel.property("tabContentTruncated") is True, (
            "szűk panelen sem jelzi a vágást — a szükség-ág nem mérhető (#703)"
        )
        assert _child(gyoker, "editorTabArea").property("clip") is True

    @pytest.mark.parametrize("magassag", [300, 360, 420])
    def test_a_fulterulet_sosem_er_a_gombsor_ala(
        self, qt_app, magassag: int
    ) -> None:
        """A szabály iránya: a gombsor SOHA nem veszít, a rács igen."""
        gyoker = _render(qt_app, _SZUK_PANEL_QML, 280, magassag)

        fulterulet = _child(gyoker, "editorTabArea")
        sor = _child(gyoker, "editorGlobalUndoRow")

        assert _bottom_in_window(fulterulet) <= _top_in_window(sor) + 0.5, (
            f"{magassag} px-en a fülterület alja "
            f"{_bottom_in_window(fulterulet):.0f} px, a gombsor teteje "
            f"{_top_in_window(sor):.0f} px — a rács a gombsor alá ér (#703)"
        )


# ==========================================================================
# 4. A nyitott csúszkás alpanel — a #703/2. pont; ma egyáltalán nincs rá teszt
# ==========================================================================
class TestANyitottAlpanelMellettIs:
    #: A Holga katalógus-bejegyzése (`effect_params.py`) — három csúszka.
    _HOLGA = [
        {
            "key": "blur", "label": "Blur", "kind": "slider",
            "minimum": 0, "maximum": 100, "step": 1, "default": 70,
        },
        {
            "key": "grain", "label": "Grain", "kind": "slider",
            "minimum": 0, "maximum": 100, "step": 1, "default": 30,
        },
        {
            "key": "fade", "label": "Fade", "kind": "slider",
            "minimum": 0, "maximum": 100, "step": 1, "default": 0,
        },
    ]

    @pytest.mark.parametrize("magassag", [900, 560, 400, 300])
    def test_a_sor_nyitott_alpanellel_is_az_ablakban_marad(
        self, qt_app, magassag: int
    ) -> None:
        gyoker = _render(qt_app, _SZUK_PANEL_QML, 280, magassag)
        panel = _child(gyoker, "panel")
        # az állapot FUTÁSIDŐBEN kapcsolódik (az `onActiveTabChanged` a
        # létrehozáskori értéket elvetné) — a #651 tesztje ugyanezt teszi
        panel.setProperty("paramEffectName", "holga")
        panel.setProperty("paramEffectParams", self._HOLGA)
        panel.setProperty("paramPanelActive", True)
        qt_app.processEvents()

        sor = _child(gyoker, "editorGlobalUndoRow")

        assert _bottom_in_window(sor) <= magassag + 0.5, (
            f"{magassag} px-en, NYITOTT csúszkás alpanellel a gombsor alja "
            f"{_bottom_in_window(sor):.0f} px-nél van (#703)"
        )


# ==========================================================================
# 5. Nem elég a helyén lennie: LÁTSZANIA is kell
# ==========================================================================
class TestATiltottGombokIsLatszanak:
    """A sor a képen akkor is ott van, ha nincs mit visszavonni.

    Ez nem elméleti: a panel háttere `Theme.chromeBg`, és a tiltott
    `PanelButton` kitöltése UGYANEZ a szín volt — frissen megnyitott képen
    (nincs mit visszavonni, nincs mit újrázni) a sor helyén két, a háttértől
    megkülönböztethetetlen folt maradt. A felhasználó jelentése — „az
    effektek alatt nincsenek gombok" — ezt is jelenti, nem csak a lecsúszást.
    """

    def test_a_tiltott_gomb_kitoltese_elter_a_panel_hatteretol(
        self, qt_app
    ) -> None:
        gyoker = _render(qt_app, _SZUK_PANEL_QML, 280, 900)
        panel = _child(gyoker, "panel")
        gomb = _child(gyoker, "editUndoButton")

        assert gomb.property("enabled") is False, (
            "a próba feltevése dőlt meg: a gomb engedélyezett, így nem a "
            "tiltott állapot színét méri"
        )
        assert gomb.property("color") != panel.property("color"), (
            "a tiltott Visszavonás gomb pontosan olyan színű, mint a panel "
            "háttere — a felhasználó számára nincs ott gomb (#703)"
        )

    def test_a_tiltott_gomb_felirata_olvashato_marad(self, qt_app) -> None:
        gyoker = _render(qt_app, _SZUK_PANEL_QML, 280, 900)
        felirat = _child(gyoker, "editUndoButtonLabel")

        assert felirat.property("text") != ""
        assert felirat.isVisible()
