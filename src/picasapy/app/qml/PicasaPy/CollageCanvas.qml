import QtQuick

// A vászon-oldal: a lap, a körülötte lévő üres terület és a húzás közbeni
// visszajelzés (#947, a #920 6/8 lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **6.**, **7.1** és **7.4**.
//
// ## A geometria NEM ezé a fájlé
//
// A vászon helyét és a lap téglalapját a `CollagePanel.qml` méretezési
// törvénye adja (#945): a bal hasáb fix, a vászon-oldal nyúlik, a lap az
// oldalformátum arányával a `previewinset`-be illesztve, középen. Ez a
// fájl azt a téglalapot KAPJA (`sheetRect`), nem számolja — így a #945
// 52 tesztje a helyén marad, és a törvény egyetlen helyen él.
//
// ## Amiért a billentyűk itt vannak
//
// A Ctrl+A / Ctrl+D / Del a vászon parancsai, de a fókusz a panelé (az
// Esc-hez kell, #945). A panel ezért `Keys.forwardTo`-val ide továbbít —
// így nincs két fókuszgazda, és az Esc továbbra is bezár.
Item {
    id: canvas

    property var controller: null

    //: A lap téglalapja a VÁSZON koordinátarendszerében (a paneltől).
    property rect sheetRect: Qt.rect(0, 0, 0, 0)

    // A kijelölés megszüntetése az ÜRES területen (`CollageDeselectHandler`,
    // spec 7.1). A legalsó rétegben ül, ezért a képek és a gyűrűk
    // elfogják előle az eseményt — csak az marad neki, amit tényleg senki
    // nem használ. A lapnak magának nincs egérterülete, tehát a lap üres
    // része is ide esik.
    MouseArea {
        objectName: "collageDeselectArea"
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onClicked: if (canvas.controller) canvas.controller.selectNoNodes()
    }

    CollageSheet {
        id: sheet
        objectName: "collageSheet"
        controller: canvas.controller
        x: canvas.sheetRect.x
        y: canvas.sheetRect.y
        width: canvas.sheetRect.width
        height: canvas.sheetRect.height
        visible: width > 0 && height > 0
    }

    // A húzás közbeni visszajelzés a vászon fölött (`collagepanel/angletext`
    // és `scaletext`). Felengedéskor mindkettő eltűnik.
    //
    // ⚠️ A szög kiírása ELŐJELET VÁLT (#921 `fchs`), és a méretarány a
    // lenyomás pillanatában 100 — mindkettőt a `collage/canvas.py` kész
    // formázói adják a vezérlőn át, itt csak a szöveg áll össze.
    Text {
        objectName: "collageAngleText"
        visible: sheet.dragFeedbackVisible
        //: A kép forgatása közben a vászon fölött megjelenő szög.
        text: qsTr("Angle: %1").arg(sheet.angleCaption)
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        x: canvas.sheetRect.x
        y: Math.max(0, canvas.sheetRect.y - height - 2)
    }
    Text {
        objectName: "collageScaleText"
        visible: sheet.dragFeedbackVisible
        //: A kép méretezése közben a vászon fölött megjelenő méretarány.
        text: qsTr("Scale: %1%").arg(sheet.scaleCaption)
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        x: canvas.sheetRect.x + canvas.sheetRect.width - width
        y: Math.max(0, canvas.sheetRect.y - height - 2)
    }

    // A vászon billentyűparancsai (spec 7.1). A buboréksúgók ki is mondják
    // őket: „Az összes kép kijelölése (Ctrl+A)", „…megszüntetése (Ctrl+D)",
    // „Kijelölt elemek eltávolítása a kollázsból (Del)".
    Keys.onPressed: function (event) {
        if (!canvas.controller)
            return
        if (event.key === Qt.Key_Delete) {
            canvas.controller.removeSelectedNodes()
            event.accepted = true
        } else if (event.key === Qt.Key_A && (event.modifiers & Qt.ControlModifier)) {
            canvas.controller.selectAllNodes()
            event.accepted = true
        } else if (event.key === Qt.Key_D && (event.modifiers & Qt.ControlModifier)) {
            canvas.controller.selectNoNodes()
            event.accepted = true
        }
    }
}
