"""#4540 — a szerkesztő eszközei és effektcsempéi az eredeti súgót mutatják."""

from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import picasapy.app
from PySide6.QtCore import QObject, QPoint, QPointF, Property, QTranslator, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_TS_PATH = Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
_TS = ET.parse(_TS_PATH).getroot()
_KEEPALIVE: list[QObject] = []

# objectName -> (az eredeti angol súgó, a hivatalos magyar fordítás)
_ESZKOZ_SUGOK = {
    "editToolCrop": (
        "Crop this Photo to a different format",
        "Vágja ezt a fotót más alakúra",
    ),
    "editToolTilt": ("Fix a crooked Photo", "Elrontott fotó kijavítása"),
    "editToolRedeye": (
        "Repair Red-Eye flaws in this Photo",
        "A vörösszem-effektusok eltávolítása a fotóról",
    ),
    "editToolEnhance": (
        "One-click fix for lighting and color",
        "Egy gombnyomásos megvilágítás- és színjavítás",
    ),
    "editToolAutolight": (
        "Fix exposure without affecting color",
        "Kijavítja a megvilágítást a szín befolyásolása nélkül",
    ),
    "editToolAutocolor": (
        "Remove color casts automatically",
        "Automatikusan eltávolítja a túlzott színárnyalatokat",
    ),
    "editToolRetouch": (
        "Repair blemishes, dust and scratches",
        "Szennyeződések, porszemcsék és karcolások eltávolítása",
    ),
    "editToolText": (
        "Add/Edit Text on a photo",
        "Szöveg fotóra helyezése/szerkesztése",
    ),
    "fixesFillLightIcon": (
        "Fill Light: Adjust the ambient light in the Photo",
        "Derítőfény: beállíthatja a fotó szórt háttérvilágítását",
    ),
}

_GOMB_SUGOK = {
    "EditorUndoRow": {
        "editUndoButton": (
            "Remove the latest fix or edit",
            "A legutóbbi javítás vagy szerkesztés visszavonása",
        ),
        "editRedoButton": (
            "Reapply a removed fix or edit",
            "Visszavont javítás vagy szerkesztés ismételt alkalmazása",
        ),
    },
    "EditorParamPanel": {
        "effectParamApplyButton": (
            "Apply Changes",
            "Módosítások alkalmazása",
        ),
        "effectParamCancelButton": (
            "Cancel Changes",
            "Változások visszavonása",
        ),
    },
}

# A tooltip-szöveg a filter_<kulcs>_tooltip0 erőforrás. Shiftre a csempe
# a második kulcs saját szövegére vált, ahogy a felirat és a művelet is.
_EFFEKTEK = {
    "EditorEffectsTab1": {
        "effectUnsharp": (
            ("Sharpen", "Sharpens edges in your photo", "A fotó széleinek élesítése"),
            ("Sharpen (Old)", "Sharpens edges in your photo", "A fotó széleinek élesítése"),
        ),
        "effectSepia": (("Sepia", "Converts photo to sepia tone", "Átalakítja a fotót szépia tónusúvá"),),
        "effectBw": (("B&W", "Makes your photo black and white", "Fekete-fehérré változtatja a fotót"),),
        "effectWarm": (("Warmify", "Improves skintones by boosting warm tones", "A meleg tónusok erősítésével javítja a bőr tónusait"),),
        "effectGrain2": (
            ("Film Grain", "Simulate film grain", "Filmszemcse szimulálása"),
            ("Film Grain (Old)", "Adds film grain", "Filmszemcse hozzáadása"),
        ),
        "effectTint": (
            ("Tint", "Change the color of your photo", "A fotó színének megváltoztatása"),
            ("Tint (Old)", "Makes a tinted look", "Árnyalt megjelenést ad"),
        ),
        "effectSat": (("Saturation", "Increases or decreases saturation", "Telítettség növelése vagy csökkentése"),),
        "effectRadblur": (("Soft Focus", "Softens focus around a center point", "Lágyítja a fókuszt egy középpont körül"),),
        "effectGlow2": (
            ("Glow", "Gives your photo a gauzy glow", "Áttetsző ragyogást ad a fotónak"),
            ("Glow (Old)", "Gives your photo a gauzy glow", "Áttetsző ragyogást ad a fotónak"),
        ),
        "effectAnsel": (("Filtered B&W", "Makes a photo that looks like it was taken with B&W film and a color filter", "Olyan képet készít, amely úgy néz ki, mintha fekete-fehér filmmel és színes szűrővel készült volna"),),
        "effectRadsat": (("Focal B&W", "Desaturates around a center point", "Telítetlen egy középpont körül"),),
        "effectDirTint": (
            ("Graduated Tint", "A graduated filter, useful for skies", "Fokozatos szűrő, hasznos az egeknél"),
            ("Radial Tint", "Tints around a central point", "Árnyalás egy középpont körül"),
        ),
    },
    "EditorEffectsTab2": {
        "effectIr": (("Infrared Film", "Simulate black-and-white infrared film", "A fekete-fehér infravörös filmet szimulálja"),),
        "effectLomo": (("Lomo-ish", "Imitate the Lomo toy camera", "A Lomo játék fényképezőgépet imitálja"),),
        "effectHolga": (("Holga-ish", "Make your photo look like it was taken with a plastic camera", "Olyanná alakítja a fotót, mintha műanyag fényképezőgéppel készítették volna"),),
        "effectHdr": (("HDR-ish", 'Emulate that "high dynamic range" look', '"Nagy dinamikatartományú" hatás emulálása'),),
        "effectCinemascope": (("Cinemascope", "Add a little classic movie magic", "A klasszikus filmekhez hasonlóvá teszi a fotót"),),
        "effectOrton": (("Orton-ish", "Mimic Michael Orton's effect", "A Michael Orton-féle hatás utánzása"),),
        "effectSixties": (("1960's", "Rounded corners and a warm, aged glow", "Lekerekített sarkok és meleg, régies ragyogás"),),
        "effectInvert": (("Invert Colors", "Make your photo look like a negative", "Negatívhoz hasonlóvá alakítja a fotót"),),
        "effectHeatMap": (
            ("Heat Map", "Simulate heat vision", "A hőtérképszerű megjelenítést szimulálja"),
            ("Night Vision", "Mimics infrared night-vision cameras", "Az infravörös éjjellátó kamerák képét utánzó hatás"),
        ),
        "effectCrossProcess": (("Cross Process", "Mimics film cross-processing", "Film keresztfeldolgozásának utánzása"),),
        "effectQuantizePalette": (("Posterize", "Reduce the number of colors in your photo", "A színek számának csökkentése a fotón"),),
        "effectTwoTone": (("Duo-Tone", "Convert your photo to two colors", "Kétszínűvé konvertálja a fotót"),),
    },
    "EditorEffectsTab3": {
        "effectBoost": (("Boost", "Bring out colors and increase contrast", "Színek kiemelése és a kontraszt növelése"),),
        "effectSoften": (("Soften", "Makes your photo soft and glowy", "Lággyá és ragyogóvá alakítja a fotót"),),
        "effectVignette": (
            ("Vignette", "Darken the edges of your photo", "Besötétíti a fotó széleit"),
            ("Matte", "Add a light glow to the edges of your photo", "A fotó széleinek világosítása"),
        ),
        "effectPixelate": (
            ("Pixelate", "Make your photo look blocky and low-res", 'A fotót "kockássá" és alacsony felbontásúvá alakítja'),
            ("Focal Pixelate", "Pixelate everything inside or outside a central area", "Egy központi területen kívüli vagy belüli részek képpontnövelése"),
        ),
        "effectFocalZoom": (("Focal Zoom", "Zoom everything outside a central area", "Egy központi területen kívül eső részek nagyítása"),),
        "effectPencilSketch": (("Pencil Sketch", "Make your photo look like it was drawn with a pencil", "Ceruzarajzhoz hasonlóvá teszi a fotót"),),
        "effectNeon": (("Neon", "Make your photo look like neon", "Neonhoz hasonlóvá alakítja a fotót"),),
        "effectComicize": (("Comic Book", "Comic book style half-toning", "Képregényszerű stílus féltónussal"),),
        "effectBorder": (
            ("Border", "Add a frame to your photo", "Keret hozzáadása a fotóhoz"),
            ("Rounded Edges", "Give your photo rounded corners", "A fotó sarkainak lekerekítése"),
        ),
        "effectDropShadow": (("Drop Shadow", "Make your photo appear to be floating slightly above the background", "A fotó megjelenítése úgy, mintha a háttér előtt lebegne"),),
        "effectMuseumMatte": (("Museum Matte", "Add a shadowed matte frame to your photo", "Árnyékos matt keretet ad a fotónak"),),
        "effectPolaroid": (("Polaroid", "Give your photo that instant-film look", "A fotót az azonnali előhívásúakhoz hasonló kinézetűvé alakítja"),),
    },
    "EditorEffectsTab4": {
        "effectMatte": (("Matte", "Add a light glow to the edges of your photo", "A fotó széleinek világosítása"),),
        "effectNightVision": (("Night Vision", "Mimics infrared night-vision cameras", "Az infravörös éjjellátó kamerák képét utánzó hatás"),),
        "effectLocalContrast": (("Local Contrast", "Brings out image details", "A képrészletek kiemelése"),),
        "effectRoundedEdges": (("Rounded Edges", "Give your photo rounded corners", "A fotó sarkainak lekerekítése"),),
        "effectPicnikGrain": (
            ("Film Grain", "Simulate film grain", "Filmszemcse szimulálása"),
            ("Film Grain (Old)", "Adds film grain", "Filmszemcse hozzáadása"),
        ),
    },
}


def _read_qml(name: str) -> str:
    return (_QML / name).read_text(encoding="utf-8")


def _object_block(source: str, object_name: str) -> str:
    match = re.search(
        r'^([ \t]*)objectName: "' + re.escape(object_name) + r'"$',
        source,
        re.M,
    )
    assert match, f"nincs ilyen QML-elem: {object_name}"
    indent = len(match.group(1))
    block = []
    for line in source[match.end():].splitlines()[1:]:
        stripped = line.strip()
        nested_property = ":" in stripped.split("{")[0]
        if (
            stripped.endswith("{")
            and not nested_property
            and len(line) - len(line.lstrip()) <= indent
        ):
            break
        block.append(line)
    return "\n".join(block)


def _tooltip_expression(block: str) -> str:
    match = re.search(r"^([ \t]*)tooltip:\s*(.*)$", block, re.M)
    assert match, "a QML-elemnek nincs tooltip tulajdonsága"
    indent = len(match.group(1))
    expression = [match.group(2)]
    for line in block[match.end():].splitlines():
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        expression.append(line.strip())
    return " ".join(expression)


def _qml_literal(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _assert_translation(context: str, english: str, hungarian: str) -> None:
    for ctx in _TS.findall("context"):
        name = ctx.findtext("name")
        if name != context:
            continue
        for message in ctx.findall("message"):
            if message.findtext("source") == english:
                assert message.findtext("translation") == hungarian, (
                    f"{context}/{english}: "
                    f"{message.findtext('translation')!r} != {hungarian!r}"
                )
                return
    raise AssertionError(f"hiányzó magyar fordítás: {context}/{english}")


def test_a_kozos_eszkoscsempek_es_a_deritofeny_az_eredeti_sugot_adjak():
    common = _read_qml("EditorTabCommonFixes.qml")
    for object_name, (english, hungarian) in _ESZKOZ_SUGOK.items():
        block = _object_block(common, object_name)
        if object_name == "fixesFillLightIcon":
            match = re.search(r"ToolTip\.text:\s*qsTr\(\"(.*?)\"\)", block)
            assert match, f"{object_name}: nincs lefordítható ToolTip.text"
            expression = f'qsTr("{match.group(1)}")'
        else:
            expression = _tooltip_expression(block)
        assert f'qsTr("{_qml_literal(english)}")' in expression, object_name
        _assert_translation("EditorTabCommonFixes", english, hungarian)

    tool_tile = _read_qml("ToolTile.qml")
    assert "ToolTip.text: tile.tooltip" in tool_tile
    assert (
        "ToolTip.visible: tile.tooltip.length > 0 && tileMouse.containsMouse"
        in tool_tile
    )
    assert "ToolTip.delay: Theme.tooltipDelay" in tool_tile


def test_undo_redo_apply_cancel_buttons_have_original_tooltips():
    for context, buttons in _GOMB_SUGOK.items():
        source = _read_qml(f"{context}.qml")
        for object_name, (english, hungarian) in buttons.items():
            expression = _tooltip_expression(_object_block(source, object_name))
            assert f'qsTr("{english}")' in expression, object_name
            _assert_translation(context, english, hungarian)


def test_minden_effektcsempe_mindket_valtozatanak_sugoja_eredeti_es_forditott():
    for context, objects in _EFFEKTEK.items():
        source = _read_qml(f"{context}.qml")
        for object_name, variants in objects.items():
            expression = _tooltip_expression(_object_block(source, object_name))
            shift_changes_tooltip = len({variant[1] for variant in variants}) > 1
            assert not shift_changes_tooltip or "panel.shiftMasodlagos" in expression, (
                f"{context}/{object_name}: a Shift-változat súgója nem vált"
            )
            for _label, english, hungarian in variants:
                assert f'qsTr("{_qml_literal(english)}")' in expression, (
                    f"{context}/{object_name}: {english}"
                )
                _assert_translation(context, english, hungarian)


class _EditControllerStub(QObject):
    @Property(str, constant=True)
    def previewSource(self):
        return "image://editpreview/42?rev=1"

    @Property("QVariantList", constant=True)
    def legacyEffectsInChain(self):
        return []


def _varj(qt_app, predicate, seconds: float = 3.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(predicate())


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _find(root: QQuickItem, object_name: str) -> QQuickItem:
    for item in _walk(root):
        if item.objectName() == object_name:
            return item
    raise AssertionError(f"{object_name} nem található a kirajzolt QML-fában")


def _tooltip_probe(engine, target: QQuickItem) -> QObject:
    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQuick
import QtQuick.Controls
Item {
    property var targetItem
    readonly property bool tooltipVisible:
        targetItem && targetItem.ToolTip.toolTip
            ? targetItem.ToolTip.toolTip.visible : false
    readonly property string tooltipText:
        targetItem && targetItem.ToolTip.toolTip
            ? String(targetItem.ToolTip.toolTip.text) : ""
    readonly property string attachedText:
        targetItem ? String(targetItem.ToolTip.text) : ""
}""",
        QUrl(),
    )
    assert component.isReady(), [error.toString() for error in component.errors()]
    probe = component.createWithInitialProperties({"targetItem": target})
    assert probe is not None, [error.toString() for error in component.errors()]
    _KEEPALIVE.extend((component, probe))
    return probe


def test_valodi_hover_minden_eredeti_es_extra_effektfulon_megjeleniti_a_magyar_sugot(
    qt_app,
):
    import picasapy.app.application as app_module

    translator = QTranslator(qt_app)
    assert translator.load(
        "picasapy_hu", str(app_module._APP_DIR / "i18n")
    ), "a magyar fordítás nem tölthető be"
    qt_app.installTranslator(translator)

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    controller = _EditControllerStub()
    view.engine().rootContext().setContextProperty("editController", controller)
    qml = b"""import QtQuick
import PicasaPy 1.0
Item {
    id: root
    property int selectedTab: 0
    EditorPanel {
        id: editorPanel
        anchors.fill: parent
        activeTab: root.selectedTab
    }
}"""
    component = QQmlComponent(view.engine())
    component.setData(qml, QUrl())
    assert component.isReady(), [error.toString() for error in component.errors()]
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]
    root.setParentItem(view.contentItem())
    view.resize(1200, 900)
    root.setWidth(1200)
    root.setHeight(900)
    view.show()

    # A fülek száma és a csempe helye a kirajzolt QML-fából jön. A
    # magasságpróbák a gépenként eltérő ablakgeometriát is lefedik.
    mintak = (
        (0, "editToolCrop", "Vágja ezt a fotót más alakúra"),
        (2, "effectSepia", "Átalakítja a fotót szépia tónusúvá"),
        (3, "effectIr", "A fekete-fehér infravörös filmet szimulálja"),
        (4, "effectBoost", "Színek kiemelése és a kontraszt növelése"),
        (5, "effectMatte", "A fotó széleinek világosítása"),
    )
    try:
        for tab, object_name, expected in mintak:
            root.setProperty("selectedTab", tab)
            for offset in (-5, 0, 5):
                view.resize(1200, 900 + offset)
                root.setWidth(1200)
                root.setHeight(900 + offset)
                assert _varj(
                    qt_app,
                    lambda expected_height=900 + offset: (
                        view.height() == expected_height
                    ),
                ), f"az ablakmagasság nem állt be: {900 + offset}"
                target = _find(root, object_name)
                assert _varj(
                    qt_app,
                    lambda target=target: target.isVisible()
                    and target.width() > 0
                    and target.height() > 0,
                ), f"{object_name} nem látható a {tab}. fülön"
                probe = _tooltip_probe(view.engine(), target)
                assert probe.property("attachedText") == expected, (
                    f"{object_name}: a csatolt súgó "
                    f"{probe.property('attachedText')!r}, várt: {expected!r}"
                )
                point = target.mapToScene(
                    QPointF(target.width() / 2, target.height() / 2)
                ).toPoint()
                QTest.mouseMove(view, point, 10)
                assert _varj(
                    qt_app,
                    lambda probe=probe: probe.property("tooltipVisible"),
                ), (
                    f"{object_name}: a rámutatásra nem jelent meg a buborék; "
                    f"pont={point}, szöveg={probe.property('tooltipText')!r}"
                )
                assert probe.property("tooltipText") == expected
                QTest.mouseMove(view, QPoint(1, 1), 10)
                assert _varj(
                    qt_app,
                    lambda probe=probe: not probe.property("tooltipVisible"),
                ), f"{object_name}: a buborék az egér elmozdítása után is látható"
    finally:
        view.close()
        view.deleteLater()
        qt_app.processEvents()
        qt_app.removeTranslator(translator)
