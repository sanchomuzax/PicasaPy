import QtQuick
import QtQuick.Controls
import QtQuick.Window
import QtQml
import PicasaPy

// SAJÁT FUNKCIÓ (#6522): mini 3D nézetet ad az effekt teljes láncra mért hatásáról.
Rectangle {
    id: box
    required property var hostViewer
    required property var hostEditCtl
    required property var hostEditorPanel
    readonly property var sliceController:
        (typeof effectSliceController !== "undefined" && effectSliceController)
            ? effectSliceController : fallbackController
    readonly property bool paramEditing: hostEditorPanel
        && hostEditorPanel.paramPanelActive
    // a Finomhangolás fül négy csúszkája a finetune2 effekt beállító panele
    readonly property bool tuningEditing: hostEditorPanel !== null
        && hostEditorPanel.activeTab === 1 && !hostEditorPanel.paramPanelActive
    readonly property var tuningValues: tuningEditing && hostEditorPanel.finetunePanel
        ? [hostEditorPanel.finetunePanel.fillSlider.value,
           hostEditorPanel.finetunePanel.highlightsSlider.value,
           hostEditorPanel.finetunePanel.shadowsSlider.value,
           hostEditorPanel.finetunePanel.tempSlider.value]
        : []
    // új beállító panel nyílásakor a mélységtengely az első csúszka
    onParamEditingChanged: if (paramEditing) hostEditorPanel.effectSliceDepthIndex = 0
    onTuningEditingChanged: if (tuningEditing) hostEditorPanel.effectSliceDepthIndex = 0
    readonly property bool editingEffect: paramEditing || tuningEditing
    readonly property string activeEffectName: paramEditing
        ? hostEditorPanel.paramEffectName : (tuningEditing ? "finetune2" : "")
    readonly property var activeEffectValues: paramEditing
        ? hostEditorPanel.paramEffectValues
        : tuningValues
    readonly property int depthIndex: hostEditorPanel
        ? hostEditorPanel.effectSliceDepthIndex : 0
    readonly property string photoPath: hostViewer ? hostViewer.currentFilePath : ""
    readonly property string chainValue: {
        if (editingEffect && hostEditCtl)
            return hostEditCtl.chainValue
        var model = hostViewer ? hostViewer.photosModel : null
        if (!model || typeof model.filtersAt !== "function") return ""
        return (model.revision, model.filtersAt(hostViewer.currentIndex))
    }
    readonly property string effectTitle: paramEditing
        ? hostEditorPanel.paramEffectTitle
        : tuningEditing ? qsTranslate("EditorTabBar", "Fine Tuning")
        : qsTr("Chain · %1 steps").arg(sliceController.chainLength)
    readonly property string activeSliderLabel: {
        if (tuningEditing)
            return qsTranslate("EditorFinetunePanel", sliceController.sliderLabel)
        if (paramEditing && hostEditorPanel.paramEffectParams
                && depthIndex >= 0
                && depthIndex < hostEditorPanel.paramEffectParams.length) {
            var label = hostEditorPanel.paramEffectParams[depthIndex].label
            return hostEditorPanel.paramLabel(label)
        }
        return hostEditorPanel.paramLabel(sliceController.sliderLabel)
    }
    property real angle: 0
    property real pressX: 0
    property real lastX: 0
    property bool wasSpinning: true

    QtObject {
        id: fallbackController
        property string mode: "never"
        property bool spinning: false
        property var surfaceData: ({kind: "none", rows: []})
        property var availableViewTypes: ["tone"]
        property string selectedViewType: "tone"
        property int chainLength: 0
        property string sliderLabel: ""
        property real sliderValue: 0
        function request() {}
        function cycleViewType() {}
        function setSpinning(_spinning) {}
        function toggleSpinning() {}
    }

    objectName: "viewerEffectSliceBox"
    width: 238
    height: 144
    //: a gazda fiók számolja: van-e hely a szerkesztőpanel tartalma alatt
    property bool hasRoom: true
    visible: hostViewer !== null && !hostViewer.isCurrentVideo && hasRoom
        && (sliceController.mode === "always"
            || (sliceController.mode === "editing" && editingEffect))
    radius: 3
    color: Theme.chromeBg
    border.width: 1
    border.color: Theme.chromeBorder
    clip: true

    function requestCurrent() {
        if (!visible || !sliceController) return
        sliceController.request(
            activeEffectName,
            activeEffectValues,
            depthIndex,
            sliceController.selectedViewType,
            photoPath,
            chainValue)
    }

    onVisibleChanged: if (visible) requestCurrent()
    onActiveEffectNameChanged: requestCurrent()
    onActiveEffectValuesChanged: requestCurrent()
    onDepthIndexChanged: requestCurrent()
    onPhotoPathChanged: requestCurrent()
    onChainValueChanged: requestCurrent()
    Component.onCompleted: requestCurrent()

    // a szerkesztés-munkamenet később indulhat, mint a panel: a revízió újrakér
    Connections {
        target: box.hostEditCtl
        ignoreUnknownSignals: true
        function onRevisionChanged() { if (box.editingEffect) box.requestCurrent() }
    }

    Text {
        id: headerText
        objectName: "effectSliceHeader"
        x: 13
        y: 3
        width: box.width - 13 - 70
        height: 11
        text: box.effectTitle
        color: Theme.ink
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 9
    }

    ToolButton {
        id: cycleViewButton
        objectName: "effectSliceCycleView"
        x: box.width - 63
        y: 1
        width: 19
        height: 15
        visible: sliceController.availableViewTypes.length > 1
        text: "↻"
        padding: 0
        font.pixelSize: 11
        onClicked: sliceController.cycleViewType()
        ToolTip.text: qsTr("Switch the view type")
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
    }

    ToolButton {
        id: spinButton
        objectName: "effectSliceSpinButton"
        x: box.width - 42
        y: 1
        width: 34
        height: 15
        text: qsTr("3D") + (sliceController.spinning ? " Ⅱ" : " ▶")
        padding: 0
        font.pixelSize: 8
        onClicked: sliceController.toggleSpinning()
        ToolTip.text: sliceController.spinning
            ? qsTr("Pause the 3D rotation") : qsTr("Resume the 3D rotation")
        ToolTip.visible: hovered
        ToolTip.delay: Theme.tooltipDelay
    }

    // A festett elem csak valódi vezérlő mellett töltődik be: a típusát ugyanaz a
    // lépés regisztrálja, amelyik a vezérlőt létrehozza (application_startup_qml).
    Loader {
        id: surface
        x: 13
        y: 17
        width: box.width - 26
        height: 105
        active: box.sliceController !== fallbackController
        source: "EffectSliceSurfaceHost.qml"
        Binding {
            target: surface.item
            property: "surfaceData"
            value: box.sliceController.surfaceData
            when: surface.item !== null
        }
        Binding {
            target: surface.item
            property: "angle"
            value: box.angle
            when: surface.item !== null
        }
    }

    Text {
        objectName: "effectSliceUnavailable"
        anchors.centerIn: surface
        width: surface.width - 16
        visible: box.editingEffect && sliceController.selectedViewType === "none"
        text: qsTr("This effect has no slice")
        color: Theme.textGray
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 9
        wrapMode: Text.WordWrap
    }

    Text {
        id: axisLabel
        objectName: "effectSliceAxisLabel"
        x: 13
        y: 124
        width: box.width - 74
        height: 13
        text: {
            if (!box.editingEffect && sliceController.chainLength === 0)
                return qsTr("No applied effect")
            switch (sliceController.selectedViewType) {
            case "tone":
                return box.activeSliderLabel.length > 0
                    ? qsTr("x: input · depth: %1 · z: output").arg(box.activeSliderLabel)
                    : qsTr("x: input · z: output")
            case "color": return qsTr("RGB cube · point = output color")
            case "image": return qsTr("x-y: image plane · z: effect strength")
            case "point": return qsTr("x-y: neighborhood · z: weight")
            case "grain": return qsTr("x-y: image plane · z: deviation")
            default: return ""
            }
        }
        color: Theme.ink
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 9
    }

    Text {
        objectName: "effectSliceSliderValue"
        x: box.width - 58
        y: 124
        width: 45
        height: 13
        text: sliceController.sliderLabel.length > 0
            ? Number(sliceController.sliderValue).toLocaleString(Qt.locale(), "f", 2) : ""
        color: "#b23c0a"
        font.bold: true
        horizontalAlignment: Text.AlignRight
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 9
    }

    HoverHandler {
        id: hoverHandler
    }

    MouseArea {
        id: rotateArea
        objectName: "effectSliceRotateArea"
        x: surface.x
        y: surface.y
        width: surface.width
        height: surface.height
        acceptedButtons: Qt.LeftButton
        hoverEnabled: true
        cursorShape: Qt.SizeHorCursor
        onPressed: function(mouse) {
            box.pressX = mouse.x
            box.lastX = mouse.x
            box.wasSpinning = sliceController.spinning
            sliceController.setSpinning(false)
        }
        onPositionChanged: function(mouse) {
            if (!pressed || Math.abs(mouse.x - box.pressX) < 3) return
            box.angle = (box.angle + (mouse.x - box.lastX) * 0.8) % 360
            box.lastX = mouse.x
        }
        onReleased: function(mouse) {
            if (Math.abs(mouse.x - box.pressX) < 3)
                sliceController.setSpinning(!box.wasSpinning)
            else
                sliceController.setSpinning(false)
        }
    }

    Timer {
        objectName: "effectSliceSpinTimer"
        interval: 33
        repeat: true
        running: box.visible
            && box.Window.window !== null
            && box.Window.window.visible
            && box.Window.window.visibility !== Window.Hidden
            && box.Window.window.visibility !== Window.Minimized
            && sliceController.spinning
        onTriggered: box.angle = (box.angle + 0.4) % 360
    }

    ToolTip.text: {
        var description = ""
        switch (sliceController.selectedViewType) {
        case "tone":
            description = qsTr(
                "Horizontally: input brightness; in depth: the full range of the %1 slider; vertically: output brightness. The orange line marks its current position.").arg(box.activeSliderLabel)
            break
        case "color":
            description = qsTr(
                "The RGB color-space grid: each point lands where the effect takes that color, and takes on the new color. The dashed cube is the original color space.")
            break
        case "image":
            description = qsTr(
                "A top view of the image: height shows where and how strongly the effect changes it.")
            break
        case "point":
            description = qsTr(
                "The effect's response to one bright pixel: a blur spreads into a mound; sharpening may add a dark ring.")
            break
        case "grain":
            description = qsTr(
                "The effect's deviation on an even gray field with a fixed random seed.")
            break
        default:
            description = qsTr("This effect has no slice.")
        }
        return description + "\n" + qsTr("Click: pause or resume spin. Drag: rotate.")
    }
    ToolTip.visible: hoverHandler.hovered
    ToolTip.delay: Theme.tooltipDelay

    Timer {
        objectName: "effectSliceRequestTimer"
        interval: 0
        onTriggered: box.requestCurrent()
    }
}
