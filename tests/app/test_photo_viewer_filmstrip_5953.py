"""A #5953 a filmszalag QML-blokkját önálló komponensbe emeli.

Ez a forrásőr szándékosan követi a jegy szerinti komponenshatárt. A külön
fájl a gazda `viewer` azonosítóját explicit propertyn kapja, hogy a kiemelt
QML ne oldjon fel véletlenül egy gazdaazonosítót saját névtérben.
"""

from pathlib import Path
import xml.etree.ElementTree as ET


GYOKER = Path(__file__).resolve().parents[2]
QML = GYOKER / "src/picasapy/app/qml/PicasaPy"


def test_filmstrip_onallo_qml_tipus_es_megmarad_a_neve() -> None:
    """A QML-modul regisztrálja a külön fájlt, a régi objektumnévvel."""
    gazda = (QML / "PhotoViewer.qml").read_text(encoding="utf-8")
    komponens_ut = QML / "PhotoViewerFilmstrip.qml"
    qmldir = (QML / "qmldir").read_text(encoding="utf-8")

    assert komponens_ut.is_file(), "a filmszalag blokkja külön QML-fájlba került"
    komponens = komponens_ut.read_text(encoding="utf-8")
    assert "PhotoViewerFilmstrip {" in gazda
    assert "hostViewer: viewer" in gazda
    assert 'objectName: "viewerFilmstrip"' in komponens
    assert "property var hostViewer" in komponens
    assert "PhotoViewerFilmstrip 1.0 PhotoViewerFilmstrip.qml" in qmldir


def test_zoom_allapot_az_uj_aliasfelulet_elott_epul_fel() -> None:
    """A tálca nagyításkötése a gyökér stabil értékforrására iratkozik fel.

    A kiemelt komponensekhez adott aliasok nem előzhetik meg a `zoomValue`
    forrást: a teljes képernyős alsó sáv a `Main.qml`-en át erre a gyökér-
    tulajdonságra köt. A deklarációs sorrend megőrzi az eredeti inicializálási
    sorrendet a PhotoViewer komponenshatárának bevezetése után is.
    """
    viewer = (QML / "PhotoViewer.qml").read_text(encoding="utf-8")
    main = (GYOKER / "src/picasapy/app/qml/Main.qml").read_text(encoding="utf-8")
    tray = (QML / "TrayBar.qml").read_text(encoding="utf-8")

    assert viewer.index("property real zoomValue: 0") < viewer.index(
        "property alias editorPanel: leftDrawer.hostEditorPanel"
    )
    assert "viewerZoomValue: photoViewer.zoomValue" in main
    assert "value: tray.viewerZoomValue" in tray


def test_editor_panel_kulon_tipus_es_forditasi_kontextus() -> None:
    """A kiemelt panel explicit host-kapcsolatokat és saját TS-kontextust kap."""
    gazda = (QML / "PhotoViewer.qml").read_text(encoding="utf-8")
    komponens_ut = QML / "PhotoViewerEditorPanel.qml"
    fiok_ut = QML / "PhotoViewerLeftDrawer.qml"
    qmldir = (QML / "qmldir").read_text(encoding="utf-8")
    ts = ET.parse(GYOKER / "src/picasapy/app/i18n/picasapy_hu.ts").getroot()

    assert komponens_ut.is_file(), "az editorPanel blokk külön QML-fájlba került"
    komponens = komponens_ut.read_text(encoding="utf-8")
    assert fiok_ut.is_file()
    assert "PhotoViewerEditorPanel {" in fiok_ut.read_text(encoding="utf-8")
    assert 'objectName: "viewerEditorPanel"' in komponens
    assert "hostViewer: viewer" in gazda
    assert "hostPhotoArea: photoArea" in gazda
    assert "editorPanel.hostViewer." in komponens
    assert "PhotoViewerEditorPanel 1.0 PhotoViewerEditorPanel.qml" in qmldir
    contexts = {
        context.findtext("name"): context for context in ts.findall("context")
    }
    assert any(
        message.findtext("source")
        == "The caption will replace the text you have typed. (This operation is not undoable)"
        for message in contexts["PhotoViewerEditorPanel"].findall("message")
    )
    for context_name in (
        "PhotoViewerPhotoArea",
        "PhotoViewerLeftDrawer",
        "PhotoViewerEditorPanel",
    ):
        for message in contexts[context_name].findall("message"):
            translation = message.find("translation")
            assert translation is not None and translation.text
            assert translation.get("type") != "unfinished", (
                f"a {context_name} kontextusban a magyar fordítás nem kész: "
                f"{message.findtext('source')}"
            )


def test_left_drawer_onallo_tipus_es_megtartja_a_panel_hivatkozasat() -> None:
    """A kiemelt fiók átadja a gazdát, és kivezeti a korábbi panel-azonosítót."""
    gazda = (QML / "PhotoViewer.qml").read_text(encoding="utf-8")
    komponens_ut = QML / "PhotoViewerLeftDrawer.qml"
    qmldir = (QML / "qmldir").read_text(encoding="utf-8")
    ts = ET.parse(GYOKER / "src/picasapy/app/i18n/picasapy_hu.ts").getroot()

    assert komponens_ut.is_file(), "a leftDrawer blokk külön QML-fájlba került"
    komponens = komponens_ut.read_text(encoding="utf-8")
    assert "PhotoViewerLeftDrawer {" in gazda
    assert "property alias editorPanel: leftDrawer.hostEditorPanel" in gazda
    assert 'objectName: "viewerLeftDrawer"' in komponens
    assert "hostViewer: viewer" in gazda
    assert "leftDrawer.hostViewer." in komponens
    assert "PhotoViewerLeftDrawer 1.0 PhotoViewerLeftDrawer.qml" in qmldir
    contexts = {
        context.findtext("name"): context for context in ts.findall("context")
    }
    assert any(
        message.findtext("source") == "This feature is not supported for Linux"
        for message in contexts["PhotoViewerLeftDrawer"].findall("message")
    )


def test_photo_area_onallo_tipus_es_a_kulso_azonositoi_megmaradnak() -> None:
    """A kiemelt képterület a régi, kívülről használt QML-neveket kivezeti."""
    gazda = (QML / "PhotoViewer.qml").read_text(encoding="utf-8")
    komponens_ut = QML / "PhotoViewerPhotoArea.qml"
    qmldir = (QML / "qmldir").read_text(encoding="utf-8")
    ts = ET.parse(GYOKER / "src/picasapy/app/i18n/picasapy_hu.ts").getroot()

    assert komponens_ut.is_file(), "a photoArea blokk külön QML-fájlba került"
    komponens = komponens_ut.read_text(encoding="utf-8")
    assert "PhotoViewerPhotoArea {" in gazda
    assert "hostViewer: viewer" in gazda
    assert "hostViewerPanArea: viewerPanArea" in gazda
    assert "hostEditorPanel: editorPanel" in gazda
    assert 'objectName: "viewerPhotoArea"' in komponens
    assert "photoArea.hostViewer." in komponens
    assert "PhotoViewerPhotoArea 1.0 PhotoViewerPhotoArea.qml" in qmldir
    exported = {
        "cropOverlay": "hostCropOverlay",
        "editorToolBar": "hostEditorToolBar",
        "effectColorPickArea": "hostEffectColorPickArea",
        "facesOverlay": "hostFacesOverlay",
        "gpuPrefixImage": "hostGpuPrefixImage",
        "kepkockaJelzes": "hostKepkockaJelzes",
        "neutralPickArea": "hostNeutralPickArea",
        "paintMaskArea": "hostPaintMaskArea",
        "photo": "hostPhoto",
        "photoElotte": "hostPhotoElotte",
        "photoElotteKeret": "hostPhotoElotteKeret",
        "photoKeret": "hostPhotoKeret",
        "redeyeDragArea": "hostRedeyeDragArea",
        "retouchClickArea": "hostRetouchClickArea",
        "textClickArea": "hostTextClickArea",
        "videoLoader": "hostVideoLoader",
    }
    for name, host_name in exported.items():
        assert f"property alias {name}: photoArea.{host_name}" in gazda
        assert f"property alias {host_name}: {name}" in komponens
    contexts = {
        context.findtext("name"): context for context in ts.findall("context")
    }
    assert any(
        message.findtext("source") == "Failed to capture frame"
        for message in contexts["PhotoViewerPhotoArea"].findall("message")
    )


def test_atszallitott_szerkesztoforditasok_minden_nyelven_megmaradnak() -> None:
    """A kontextusváltás nem vesztheti el a meglévő fordítást vagy kulcsot."""
    vart_forditasok = {
        "Undo": "Visszavonás",
        "Redo": "Újra",
        "Retouch fixes cannot be recovered with redo.\n"
        "Are you sure you want to undo?":
        "A retusálási javítások nem állíthatók helyre ismételt alkalmazással.\n"
        "Biztosan visszavonja a műveletet?",
        "Redeye fixes cannot be recovered with redo.\n"
        "Are you sure you want to undo?":
        "A vörösszemjavítások nem állíthatók helyre ismételt alkalmazással.\n"
        "Biztosan visszavonja a műveletet?",
        "The caption will replace the text you have typed. "
        "(This operation is not undoable)":
        "A felirat felülírja a beírt szöveget. "
        "(Ez a művelet nem vonható vissza.)",
    }

    for ts_ut in sorted((GYOKER / "src/picasapy/app/i18n").glob("picasapy_*.ts")):
        ts = ET.parse(ts_ut).getroot()
        kontextus = next(
            context
            for context in ts.findall("context")
            if context.findtext("name") == "PhotoViewerEditorPanel"
        )
        uzenetek = {
            message.findtext("source"): message
            for message in kontextus.findall("message")
        }
        assert set(vart_forditasok) <= uzenetek.keys(), ts_ut.name
        for source, magyar in vart_forditasok.items():
            uzenet = uzenetek[source]
            fordítás = uzenet.find("translation")
            assert fordítás is not None and fordítás.text, (ts_ut.name, source)
            assert fordítás.get("type") != "unfinished", (ts_ut.name, source)
            if ts_ut.name == "picasapy_hu.ts":
                assert fordítás.text == magyar, source
