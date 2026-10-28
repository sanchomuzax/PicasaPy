import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: printPreviewBlock
    property var printWindow
    objectName: "printPreviewBlock"
    Layout.fillWidth: true
    spacing: 4
    visible: printWindow.previewPageCount > 0

    Image {
        objectName: "printPreviewImage"
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredHeight: 150
        Layout.preferredWidth: 150
        fillMode: Image.PreserveAspectFit
        source: printWindow.previewSource
        asynchronous: true
        //: A gyorstár KIKAPCSOLVA: ugyanaz a fájlnév kap új
        //: tartalmat minden lapozáskor.
        cache: false
    }
    RowLayout {
        Layout.alignment: Qt.AlignHCenter
        spacing: 8
        PicasaButton {
            objectName: "printPreviewPrevButton"
            text: "◀"
            Layout.preferredWidth: 26
            Layout.preferredHeight: 22
            //: Az első lapon nincs hova visszalépni.
            enabled: printWindow.previewPage > 0
            onClicked: {
                printWindow.previewPage -= 1
                printWindow.frissitsdAzElonezetet()
            }
        }
        Text {
            objectName: "printPreviewPageText"
            //: #1960: a SORREND a fordításé, nem a kódé. Az
            //: eredeti angol erőforrása `%1$d of %2$d`
            //: (aktuális / összes), a magyar `%2$d / %1$d`
            //: (összes / aktuális) — `ThumbUIPrint::PrintCount`,
            //: `stringres` 2287. Ezért összefűzés helyett
            //: pozíció-argumentumos sablon: a `.ts` dönti el,
            //: melyik nyelv melyik sorrendet kapja.
            text: qsTr("%1 / %2")
                  .arg(printWindow.previewPage + 1)
                  .arg(printWindow.previewPageCount)
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        PicasaButton {
            objectName: "printPreviewNextButton"
            text: "▶"
            Layout.preferredWidth: 26
            Layout.preferredHeight: 22
            enabled: printWindow.previewPage < printWindow.previewPageCount - 1
            onClicked: {
                printWindow.previewPage += 1
                printWindow.frissitsdAzElonezetet()
            }
        }
    }
}
