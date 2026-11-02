"""#6381: a QML-gombok leltára és a lenyomott állapot renderelt ellenőrzése."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest

_QML = Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml"


@pytest.fixture(scope="module", autouse=True)
def _qt_button_style(qt_app):
    """A termékben használt Fusion tartalékot rögzíti a képpróbákhoz.

    A Qt alapértelmezett stílusa platformonként változik; a Windows stílus
    offscreen megjelenítője a `Button.down` állapotot is rajzolhatja azonos
    képkockával. Az alkalmazás Fusion tartalékstílust használ, ezért a
    pixeles próba is ezt állítja be az első QML-motor előtt.
    """
    QQuickStyle.setStyle("Fusion")


_QML_TIPUSOK = (
    "PicasaButton",
    "Button",
    "ToolButton",
    "RoundButton",
    "CheckBox",
    "RadioButton",
    "MouseArea",
    "TapHandler",
    "PressFeedbackMouseArea",
    "PressFeedbackTapHandler",
)
_TIPUS_MINTA = re.compile(
    r"(?<![\w.])(" + "|".join(_QML_TIPUSOK) + r")\s*\{"
)


def _commentok_nelkul(forras: str) -> str:
    """A QML-megjegyzéseket szó szerinti karakterek megőrzésével kiveszi."""
    kimenet = list(forras)
    i = 0
    quote = None
    escape = False
    while i < len(forras):
        char = forras[i]
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = None
            i += 1
            continue
        if char in "\"'":
            quote = char
            i += 1
            continue
        if forras.startswith("//", i):
            vege = forras.find("\n", i)
            vege = len(forras) if vege < 0 else vege
            for j in range(i, vege):
                kimenet[j] = " "
            i = vege
            continue
        if forras.startswith("/*", i):
            vege = forras.find("*/", i + 2)
            vege = len(forras) if vege < 0 else vege + 2
            for j in range(i, vege):
                if kimenet[j] != "\n":
                    kimenet[j] = " "
            i = vege
            continue
        i += 1
    return "".join(kimenet)


def _zarodoboz(forras: str, nyito: int) -> int:
    melyseg = 1
    i = nyito + 1
    quote = None
    escape = False
    while i < len(forras):
        char = forras[i]
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "{":
            melyseg += 1
        elif char == "}":
            melyseg -= 1
            if melyseg == 0:
                return i
        i += 1
    raise AssertionError("pár nélküli kapcsos zárójel a QML-ben")


def _kozvetlen_object_name(blokk: str) -> str:
    melyseg = 0
    sorok = blokk.splitlines()
    for sor in sorok:
        if melyseg == 0:
            match = re.match(r"\s*objectName\s*:\s*(.*)", sor)
            if match:
                return match.group(1).strip()
        quote = None
        escape = False
        for char in sor:
            if quote:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == quote:
                    quote = None
            elif char in "\"'":
                quote = char
            elif char == "{":
                melyseg += 1
            elif char == "}":
                melyseg -= 1
    return ""


def _qml_gombleltar() -> list[dict[str, object]]:
    leltar = []
    for path in sorted(_QML.rglob("*.qml")):
        if path.name in {"PressFeedbackMouseArea.qml", "PressFeedbackTapHandler.qml"}:
            continue
        raw = path.read_text(encoding="utf-8")
        forras = _commentok_nelkul(raw)
        for match in _TIPUS_MINTA.finditer(forras):
            nyito = forras.find("{", match.start(), match.end())
            zar = _zarodoboz(forras, nyito)
            blokk = forras[nyito + 1 : zar]
            line = forras.count("\n", 0, match.start()) + 1
            nev = _kozvetlen_object_name(blokk)
            leltar.append(
                {
                    "file": path.relative_to(_QML).as_posix(),
                    "type": match.group(1),
                    "objectName": nev or f"<nincs>@{line}",
                    "line": line,
                    "body": blokk,
                    "source": forras,
                }
            )
    return leltar


def _gombkent_hasznalt(elem: dict[str, object]) -> bool:
    tipus = elem["type"]
    blokk = str(elem["body"])
    if tipus not in {"MouseArea", "TapHandler"}:
        return False
    bal_kattintas = not re.search(r"acceptedButtons\s*:\s*Qt\.RightButton", blokk)
    if not bal_kattintas:
        return False
    return bool(
        re.search(
            r"\bon(?:Clicked|Tapped|SingleTapped|DoubleTapped|PressedChanged)\s*:",
            blokk,
        )
    )


def _van_sajat_lenyomas_kep(elem: dict[str, object]) -> bool:
    if elem["type"] in {"PressFeedbackMouseArea", "PressFeedbackTapHandler"}:
        return True
    blokk = str(elem["body"])
    source = str(elem["source"])
    if "PressFeedbackOverlay" in blokk:
        return True
    azonosito = re.search(r"\bid\s*:\s*([A-Za-z_]\w*)", blokk)
    if not azonosito:
        return False
    azon = azonosito.group(1)
    return bool(
        re.search(rf"\b{re.escape(azon)}\.pressed\b", source)
        or re.search(rf"pressSource\s*:\s*{re.escape(azon)}\b", source)
    )


def test_minden_gombszeru_qml_elem_fajl_es_objectname_szerint_leltarban_van():
    leltar = _qml_gombleltar()
    assert len(leltar) >= 600, f"a leltár váratlanul kicsi: {len(leltar)} elem"
    assert {str(elem["type"]) for elem in leltar} >= {
        "PicasaButton",
        "Button",
        "ToolButton",
        "CheckBox",
        "RadioButton",
        "MouseArea",
        "TapHandler",
    }

    lista = [
        {
            "file": elem["file"],
            "objectName": elem["objectName"],
            "type": elem["type"],
            "line": elem["line"],
        }
        for elem in leltar
    ]
    cel = Path.cwd() / ".tmp" / "6381-qml-gombleltar.json"
    cel.parent.mkdir(parents=True, exist_ok=True)
    cel.write_text(json.dumps(lista, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    hianyzo = [
        f"{elem['file']}:{elem['line']} ({elem['objectName']})"
        for elem in leltar
        if _gombkent_hasznalt(elem) and not _van_sajat_lenyomas_kep(elem)
    ]
    if hianyzo:
        felsorolas = ", ".join(hianyzo[:15])
        tovabbi = len(hianyzo) - min(15, len(hianyzo))
        if tovabbi:
            felsorolas += f"; további {tovabbi} elem"
        pytest.fail(
            "új vagy meglévő kattintható MouseArea/TapHandler nem kap lenyomott "
            f"képet ({len(hianyzo)} elem): {felsorolas}"
        )


def _wait_for(qt_app, condition, message: str) -> None:
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return
        time.sleep(0.01)
    qt_app.processEvents()
    assert condition(), message


def _renderelt_lenyomas(qt_app, control_type: str, height_offset: int = 0) -> int:
    view = QQuickView()
    view.engine().addImportPath(str(_QML))
    component = QQmlComponent(view.engine())
    forras = (
        "import QtQuick\n"
        "import QtQuick.Controls\n"
        "import PicasaPy\n"
        f"Item {{ width: 220; height: {60 + height_offset};\n"
        f"    {control_type} {{ objectName: 'proba'; x: 20; y: 10; "
        "width: 180; height: 40; text: ''; checked: false }\n"
        "}\n"
    )
    component.setData(
        forras.encode("utf-8"), QUrl.fromLocalFile(str(_QML / "PicasaPy") + "/")
    )
    assert component.status() == QQmlComponent.Status.Ready, component.errorString()
    root = component.create()
    assert root is not None, component.errorString()
    view.setContent(QUrl(), component, root)
    view.show()
    _wait_for(qt_app, view.isExposed, f"a {control_type} próbaablak nem jelent meg")
    control = root.findChild(type(root), "proba")
    assert control is not None, f"a {control_type} próbaelem nem épült fel"
    view.requestUpdate()
    qt_app.processEvents()
    idle = view.grabWindow()
    assert not idle.isNull(), f"a {control_type} nyugalmi képe üres"

    center = control.mapToScene(
        QPointF(control.property("width") / 2, control.property("height") / 2)
    )
    QTest.mousePress(
        view,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    _wait_for(qt_app, lambda: bool(control.property("down")), f"{control_type}.down nem indult")
    view.requestUpdate()
    qt_app.processEvents()
    pressed = view.grabWindow()
    assert not pressed.isNull(), f"a {control_type} lenyomott képe üres"

    dpr = pressed.width() / view.width()
    left = round((center.x() - control.property("width") / 2 + 1) * dpr)
    right = round((center.x() + control.property("width") / 2 - 1) * dpr)
    top = round((center.y() - control.property("height") / 2 + 1) * dpr)
    bottom = round((center.y() + control.property("height") / 2 - 1) * dpr)
    kulonbozo = sum(
        idle.pixelColor(x, y) != pressed.pixelColor(x, y)
        for y in range(top, bottom + 1)
        for x in range(left, right + 1)
    )
    QTest.mouseRelease(
        view,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    view.close()
    view.deleteLater()
    component.deleteLater()
    qt_app.processEvents()
    return kulonbozo


def _renderelt_kezeloterulet_lenyomas(
    qt_app, handler_type: str, height_offset: int = 0
) -> int:
    view = QQuickView()
    view.engine().addImportPath(str(_QML))
    component = QQmlComponent(view.engine())
    if handler_type == "MouseArea":
        handler = (
            "MouseArea { id: aktiv; objectName: 'aktiv'; anchors.fill: parent; "
            "onClicked: {} "
            "PressFeedbackOverlay { pressSource: parent } }"
        )
    else:
        handler = (
            "TapHandler { id: aktiv; objectName: 'aktiv' } "
            "PressFeedbackOverlay { pressSource: aktiv }"
        )
    source = (
        "import QtQuick\nimport PicasaPy\n"
        f"Item {{ width: 180; height: {40 + height_offset}; "
        "Rectangle { objectName: 'proba'; anchors.fill: parent; "
        "color: '#d0d0d0'; " + handler + " } }"
    )
    component.setData(source.encode(), QUrl.fromLocalFile(str(_QML / "PicasaPy") + "/"))
    assert component.status() == QQmlComponent.Status.Ready, component.errorString()
    root = component.create()
    assert root is not None, component.errorString()
    view.setContent(QUrl(), component, root)
    view.show()
    _wait_for(qt_app, view.isExposed, f"a {handler_type} próbaablak nem jelent meg")
    view.requestUpdate()
    qt_app.processEvents()
    idle = view.grabWindow()
    target = root.findChild(QQuickItem, "proba")
    assert target is not None, f"a {handler_type} próbacél nem épült fel"
    center = target.mapToScene(
        QPointF(target.width() / 2, target.height() / 2)
    )
    kattintasi_pont = QPoint(round(center.x()), round(center.y()))
    QTest.mousePress(
        view, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier, kattintasi_pont
    )
    control = root.findChild(QObject, "aktiv")
    _wait_for(
        qt_app,
        lambda: bool(control and control.property("pressed")),
        f"a {handler_type} nem lett lenyomva",
    )
    view.requestUpdate()
    qt_app.processEvents()
    pressed = view.grabWindow()
    dpr = pressed.width() / view.width()
    left = round((center.x() - target.width() / 2 + 1) * dpr)
    right = round((center.x() + target.width() / 2 - 1) * dpr)
    top = round((center.y() - target.height() / 2 + 1) * dpr)
    bottom = round((center.y() + target.height() / 2 - 1) * dpr)
    kulonbozo = sum(
        idle.pixelColor(x, y) != pressed.pixelColor(x, y)
        for y in range(top, bottom + 1)
        for x in range(left, right + 1)
    )
    QTest.mouseRelease(
        view, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier, kattintasi_pont
    )
    view.close()
    view.deleteLater()
    component.deleteLater()
    qt_app.processEvents()
    return kulonbozo


@pytest.mark.parametrize(
    "control_type", ["Button", "ToolButton", "RoundButton", "CheckBox", "RadioButton"]
)
@pytest.mark.parametrize("height_offset", (-5, 0, 5))
def test_a_szabvanyos_qt_gomb_lenyomasa_renderelt_pixelt_valtoztat(
    qt_app, control_type, height_offset
):
    assert _renderelt_lenyomas(qt_app, control_type, height_offset) > 0, (
        f"a {control_type} lenyomott renderképe nem tér el a nyugalmitól "
        f"({height_offset:+d} px ablakmagasság-eltolás)"
    )


@pytest.mark.parametrize("handler_type", ["MouseArea", "TapHandler"])
@pytest.mark.parametrize("height_offset", (-5, 0, 5))
def test_a_kattinthato_kezeloterulet_lenyomasa_renderelt_pixelt_valtoztat(
    qt_app, handler_type, height_offset
):
    assert _renderelt_kezeloterulet_lenyomas(
        qt_app, handler_type, height_offset
    ) > 0, (
        f"a {handler_type} lenyomott renderképe nem tér el a nyugalmitól "
        f"({height_offset:+d} px ablakmagasság-eltolás)"
    )
