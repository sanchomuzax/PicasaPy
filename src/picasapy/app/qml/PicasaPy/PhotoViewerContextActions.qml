import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: viewerContextActions
    anchors.fill: parent
    property var hostViewer: null
    readonly property var viewer: hostViewer
    readonly property var editorPanel: viewer.editorPanel
    readonly property var editController: viewer.editCtl
    property alias hostMovieResetConfirmLoader: movieResetConfirmLoader
    property alias hostCopyCaptionConfirmLoader: copyCaptionConfirmLoader
    property alias hostUndoDataLossDialogLoader: undoDataLossDialogLoader

    //: #2566: a fiók ürítésének EGYETLEN útja a nézőből. A négy fiók-jelző
    //: SZÁRMAZTATOTT (#1773), közvetlenül nem írható - az ablak függvénye
    //: üríti. A `!== undefined` a #1572-őr mintája: a próbák stub-ablakán
    //: nincs rajta a függvény.
    function zarjaAFiokot() {
        if (viewer.appWindow && viewer.appWindow.ureseidAFiokot !== undefined)
            viewer.appWindow.ureseidAFiokot()
    }

    // -- #422: jobbklikk-menü a nagy képen ---------------------------------
    // A nézőben eddig egyáltalán nem volt kontextusmenü (a Picasa `OneUp`
    // menüosztálya, 17 tétel - ld. ViewerContextMenu.qml). A parancsok a
    // globális context property-ken (controller, fileOpsController) át
    // futnak, a törlés dialógusa pedig jelként megy a Main.qml-nek - így a
    // forró Main.qml csak egyetlen bekötést kap.

    readonly property string currentPath: viewer.photosModel
        && viewer.currentIndex >= 0
        ? viewer.photosModel.filePathAt(viewer.currentIndex) : ""

    //: #4621: az AKTÍV (kijelölt) fél képének útja - A|B módban jobb
    //: fókusszal nem a `currentPath` (bal kép). A helyi menü minden tétele
    //: ezt használja, hogy az egész menü EGY képre vonatkozzon, a törlés
    //: (`_kijeloltSort()`) is. FÜGGVÉNY, mert imperatív kezelők hívják (#218).
    function _aktivUt() {
        var sor = viewer._kijeloltSort()
        return viewer.photosModel && sor >= 0
            ? viewer.photosModel.filePathAt(sor) : ""
    }

    //: #1612: a menü HALASZTOTT - az `ensure()` az első jobbklikkre építi
    //: fel. Mérve: a `viewerContextMenu` 360 QObject, és a legtöbb
    //: munkamenetben a felhasználó egyszer sem jobbklikkel a nagy képen.
    function openContextMenu(x, y) { viewerMenuLoader.ensure().popupForPhoto(viewer, x, y, viewer._aktivUt(), typeof fileOpsController !== "undefined" ? fileOpsController : null) }

    //: #4566: a `movieeditpanel/reset_trim` megerősítése - az eredeti
    //: `CThumbUI::UndomovieEdits` kérdése és `IDS_CONFIRMREVERT_YES_BUTTON`
    //: igen-gombja (`docs/specs/ui-audit-editor.md`, a `reset_trim` szakasza)
    DeferredDialog {
        id: movieResetConfirmLoader
        objectName: "movieResetConfirmDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "movieResetConfirmDialog"
                namePrefix: "movieResetConfirm"
                property int row: -1
                yesText: qsTr("Remove Edits")
                function askFor(sor) {
                    row = sor
                    ask("", qsTr("Remove all movie edits?"))
                }
                onConfirmed: {
                    if (controller && controller.resetMovieTrim !== undefined)
                        controller.resetMovieTrim(row)
                }
            }
        }
    }

    DeferredDialog {
        id: viewerMenuLoader
        objectName: "viewerContextMenuLoader"
        sourceComponent: Component {
        ViewerContextMenu {
        id: viewerMenu
        removesFromAlbum: viewer.deleteRemovesFromAlbum
        // a revision-nel együtt kötve, hogy a menü újranyitáskor friss
        // rejtett-állapotot mutasson (a PhotoContextMenu mintája)
        hidden: viewer.photosModel && viewer.currentIndex >= 0
            ? (viewer.photosModel.revision,
               viewer.photosModel.itemAt(viewer.currentIndex).hidden === true)
            : false
        // #305: null-őr - a controller a leépítéskor átmenetileg null lehet
        albums: typeof controller !== "undefined" && controller
            ? controller.albums : []

        // #422: a mentés-parancsok aktív állapota a NÉZETT képre
        hasEdits: viewer.photosModel && viewer.currentIndex >= 0
            ? (viewer.photosModel.revision,
               viewer.photosModel.itemAt(viewer.currentIndex).hasEdits === true)
            : false
        hasBackup: typeof controller !== "undefined" && controller
                   && viewer.currentIndex >= 0
            ? (controller.savedBackupRevision,
               controller.hasSavedBackup([viewer.currentIndex])) : false
        // #7017: az Undo all Edits a NÉZETT kép eredeti szerkesztettségi
        // állapotából él; a modell revíziója a láncváltás és a tükrözés
        // után újraértékelteti
        canUndoAllEdits: typeof controller !== "undefined" && controller
                         && viewer.photosModel && viewer.currentIndex >= 0
            ? (viewer.photosModel.revision,
               controller.undoAllEditsEnabled([viewer.currentIndex])) : false

        onSaveRequested: viewer.saveRequested(viewer.currentIndex)
        onRevertRequested: viewer.revertRequested(viewer.currentIndex)
        onUndoAllEditsRequested: viewer.undoAllEditsRequested(viewer.currentIndex)
        onResetFacesRequested: viewer.resetFacesRequested()

        onBackToLibraryRequested: viewer.kerBezaras()
        //: #3014: a KIJELÖLT oldal képe megy az albumba - ez a kettős
        //: nézet válogató munkafolyamata (a jobbik képet egy lépéssel
        //: albumba tenni). Egy kép módban változatlanul a jelenlegi.
        //:
        //: ⚠️ A jegy `TwoUpAddToAlbum` néven külön vezérlőt említett; a
        //: binárisban ilyen sztring NINCS (a `TwoUp` minta mind a hat
        //: találata a `swap_2up_*`/`Confirm2up*` család). Az eredetiben
        //: tehát nincs külön gomb: a MEGLÉVŐ albumba tétel hat a
        //: kijelölt oldalra, amit a „Kijelölve" jelvény mutat.
        onAddToAlbumRequested: function(token) {
            if (typeof controller !== "undefined" && controller)
                controller.addRowsToAlbum([viewer.aktivSor], token)
        }
        //: #7100: az almenü további három sora a NÉZETT (aktív oldali) képre
        //: hat, ahogy a `0x00536a90` az aktuális egy képet kapja (`+0xe64`).
        //: A főablak `photoActionRows()`-a nézőben ugyanezt a sort adja
        //: (`_kijeloltSort()`), ezért a három sor UGYANARRA a képre hat.
        onStarredPhotosRequested: {
            var sor = viewer._kijeloltSort()
            if (typeof controller !== "undefined" && controller && sor >= 0)
                controller.addStarMany([sor])
        }
        onScreensaverRequested: {
            // #7131: a nézett képet kérdés nélkül adjuk a képernyővédőhöz.
            if (viewer.appWindow
                && viewer.appWindow.photoActionPaths !== undefined
                && viewer.appWindow.addPhotosToScreensaver !== undefined)
                viewer.appWindow.addPhotosToScreensaver(
                    viewer.appWindow.photoActionPaths())
        }
        onNewAlbumRequested: {
            if (viewer.appWindow && viewer.appWindow.fileOpsDialogs !== undefined
                && viewer.appWindow.photoActionRows !== undefined)
                viewer.appWindow.fileOpsDialogs.ensure().openAddToNewAlbum(
                    viewer.appWindow.photoActionRows())
        }
        onRotateRightRequested: {
            if (typeof controller !== "undefined" && controller
                && viewer.currentIndex >= 0)
                controller.rotateRight(viewer.currentIndex)
        }
        onRotateLeftRequested: {
            if (typeof controller !== "undefined" && controller
                && viewer.currentIndex >= 0)
                controller.rotateLeft(viewer.currentIndex)
        }
        // #7019: a felirat szerinti irányba hat (Megjelenítésnél megjelenít,
        // Elrejtésnél elrejt).
        onHideToggleRequested: {
            if (viewer.appWindow && viewer.appWindow.hideSelection !== undefined
                && viewer.appWindow.unhideHiddenSelection !== undefined) {
                if (viewerMenu.hidden)
                    viewer.appWindow.unhideHiddenSelection()
                else
                    viewer.appWindow.hideSelection()
                return
            }
            if (typeof controller !== "undefined" && controller
                && viewer.currentIndex >= 0) {
                var photo = viewer.photosModel
                    ? viewer.photosModel.itemAt(viewer.currentIndex) : null
                var isHidden = photo ? photo.hidden === true : viewerMenu.hidden
                if (viewerMenu.hidden ? isHidden : !isHidden)
                    controller.toggleHiddenRows([viewer.currentIndex])
            }
        }
        onOpenFileRequested: {
            if (typeof fileOpsController !== "undefined" && fileOpsController
                && viewer._aktivUt().length > 0)
                fileOpsController.openPhoto(viewer._aktivUt())
        }
        onLocateRequested: function(original) {
            if (typeof fileOpsController !== "undefined" && fileOpsController && viewer._aktivUt().length > 0)
                original ? fileOpsController.revealOriginal(viewer._aktivUt())
                    : fileOpsController.revealPhoto(viewer._aktivUt())
        }
        onCopyFullPathRequested: {
            if (typeof fileOpsController !== "undefined" && fileOpsController
                && viewer._aktivUt().length > 0)
                fileOpsController.copyFullPath(viewer._aktivUt())
        }
        onDeleteRequested: {
            if (viewer._aktivUt().length > 0)
                viewer.deleteRequested()
        }
        onPropertiesRequested: {
            // #1773: a helyi menü a fiók Tulajdonságok lapjára VÁLT (az
            // eredetiben a négy lap kizáró csoport); ha már az látszik, a
            // nézőben a billentyűhöz hasonlóan zárja a fiókot.
            if (viewer.appWindow
                && viewer.appWindow.valtsFiokLapot !== undefined)
                viewer.appWindow.propertiesPanelOpen
                    ? viewer.appWindow.ureseidAFiokot()
                    : viewer.appWindow.valtsFiokLapot("properties")
        }
    }
        }
    }

    // jobbklikk BÁRHOL a nézőn - a Picasában a nagy kép és a körülötte lévő
    // szürke háttér is ugyanezt a menüt nyitja
    TapHandler {
        acceptedButtons: Qt.RightButton
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onSingleTapped: function(point) {
            viewer.openContextMenu(point.position.x, point.position.y)
        }
    }

    // #465 4. pont: a felirat-bemásolás megerősítése (ld.
    // `onTextCopyCaptionRequested`)
    //: #1612: halasztva - a felirat-átvétel megerősítése csak akkor kell, ha
    //: a felhasználó tényleg átveszi a feliratot (mérve: 74 QObject).
    DeferredDialog {
        id: copyCaptionConfirmLoader
        sourceComponent: Component {
            ConfirmDialog {
                namePrefix: "copyCaptionConfirm"
                onConfirmed: editorPanel.textDraftContent = editorPanel.captionText
            }
        }
    }

    // #465: a retus/vörösszem visszavonása ADATOT dob el (nincs „Újra") -
    // az eredeti Picasa két külön szövegével kérdez rá. A döntés-kulcs
    // eszközönként külön, hogy a „Ne kérdezze meg újra" a másikra ne hasson.
    //: #1612: halasztva - a retus/vörösszem visszavonásának megerősítése csak
    //: akkor kell, ha a felhasználó ilyet vissza is von (mérve: 76 QObject).
    DeferredDialog {
        id: undoDataLossDialogLoader
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "undoDataLossDialog"
                namePrefix: "undoDataLoss"
                // #7379: a retusálás visszavonásának megerősítője az eredeti natív
                // „Confirm" ablak alakját ölti (job-838 __36): „Confirm" cím, Picasa-
                // logó, „Undo" / „No" fehér gombok, a fókusz a „No"-n, nincs Cancel és
                // „Do not ask again", és a háttér nem halványul. A Vörösszem ága a régi
                // alakot tartja: az eredeti Vörösszem-megerősítő alakja nincs mérve
                // (7327-10). A tulajdonságok kötések, így nem ragad át állapot egyik
                // nyitásról a másikra.
                property bool retouchLook: false
                title: retouchLook ? qsTr("Confirm") : qsTr("Undo")
                iconType: retouchLook ? "picasa" : "none"
                yesText: retouchLook ? qsTr("Undo") : qsTr("Yes")
                noText: qsTr("No")
                cancelVisible: !retouchLook
                rememberVisible: !retouchLook
                focusNoOnOpen: retouchLook
                dimBackground: !retouchLook
                nativeButtons: retouchLook
                function askFor(key, text) {
                    retouchLook = key === "retouch"
                    // a retusálás megerősítőjén nincs „Do not ask again", ezért kulcs nélkül
                    // (üres decisionKey) nyílik: egy korábbi verzióban elmentett
                    // `undo-retouch` elnyomás ne némíthassa el.
                    ask(retouchLook ? "" : "undo-" + key, text)
                }
                onConfirmed: editController.undo()
            }
        }
    }

    // #2480: a MODÁLIS párbeszédek elhomályosító rétege. Az eredetiben ez
    // az `editpanel/modaldialogblur` (`editpanel.tre:1362`): a `root`
    // közvetlen gyereke (tehát a TELJES szerkesztő fölé kerül, nem a bal
    // panelen belülre), `m_scaleXY` (a teljes vászonra feszül) és
    // `m_hidden` (alapból rejtett - a modális párbeszéd kapcsolja be).
    //
    // A fájl UTOLSÓ gyereke, hogy a rétegrendben minden fölé kerüljön: a
    // bal panel, az előnézet és a felső sáv is alá esik. A Qt maga a
    // párbeszédet még ennél is fölé rajzolja (külön `QQuickOverlay`), tehát
    // a párbeszéd nem homályosodik el.
    //
    // ⚠️ A MÉRTÉK és a SZÍN a MI döntésünk: a `.tre` csak a réteg létét és
    // kiterjedését adja meg, a rajzot a `respack.yt` rétege adná - az nincs
    // kimérve. A választott érték a vászon-háttér 45%-a: elég ahhoz, hogy a
    // fókusz a párbeszédre kerüljön, de a szerkesztő tartalma átlátszik
    // (a felhasználónak látnia kell, mire válaszol).
    //
    // `enabled: false` - a réteg CSAK látvány: a modalitást a Qt biztosítja
    // (a párbeszéd `modal: true`), egy eseményt elnyelő réteg viszont a
    // párbeszéd bezárása utáni első kattintást is elvinné.
    Rectangle {
        objectName: "editorModalDialogBlur"
        anchors.fill: parent
        z: 1000
        enabled: false
        visible: editorPanel.modalDialogOpen
        color: Theme.canvasBg
        opacity: 0.45
    }
}
