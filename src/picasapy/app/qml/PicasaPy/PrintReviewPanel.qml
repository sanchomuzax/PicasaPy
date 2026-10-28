import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: printReviewPanel
    property var printWindow
    property alias currentIndex: printReviewList.currentIndex
    objectName: "printReviewPanel"
    anchors.fill: parent
    visible: printReviewPanel.printWindow.reviewOpen
    color: Theme.canvasBg
    z: 100

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8
        Text {
            //: `printpanel/reviewnowbutton` felirata — a lap címe is ez
            text: qsTr("Review")
            font.pixelSize: Theme.fontSize + 3
            font.bold: true
            color: Theme.ink
        }
        Text {
            objectName: "printReviewWarningText"
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            //: `CPrintDlg::toosmall`; eredeti figyelmeztetés a
            //: `picasa-nyomtatas.md` 40.7 szerint.
            visible: printReviewPanel.printWindow.reviewList.length > 0
            text: qsTr("Some of your pictures are too small to print well.  You can remove these pictures, print them anyway, or cancel and change the print size.")
        }
        ListView {
            objectName: "printReviewList"
            id: printReviewList
            Layout.fillWidth: true
            Layout.fillHeight: printReviewPanel.printWindow.reviewList.length > 0
            clip: true
            model: printReviewPanel.printWindow.reviewList
            currentIndex: printReviewPanel.printWindow.reviewList.length > 0 ? 0 : -1
            delegate: Item {
                required property var modelData
                required property int index
                objectName: "printReviewListRow"
                width: ListView.view.width
                height: reviewListRowText.implicitHeight + 8
                Rectangle {
                    anchors.fill: parent
                    color: ListView.isCurrentItem ? Theme.surfaceAlt : "transparent"
                }
                Text {
                    id: reviewListRowText
                    objectName: "printReviewListRowText"
                    anchors.fill: parent
                    anchors.margins: 4
                    elide: Text.ElideMiddle
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                    //: A `CPrintDlg::bestqual` / `goodqual` / `badqual`
                    //: hivatalos angol feliratai a fordításból jönnek.
                    text: {
                        var label = modelData.qualityCode === 2
                            ? qsTr("Best quality (%1 pixels/inch)")
                            : modelData.qualityCode === 1
                                ? qsTr("Good quality (%1 pixels/inch)")
                                : qsTr("Bad quality (%1 pixels/inch)")
                        return modelData.name + "   —   "
                               + label.arg(modelData.dpi)
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: printReviewList.currentIndex = index
                }
            }
        }
        Text {
            objectName: "printReviewEmptyText"
            Layout.fillWidth: true
            visible: printReviewPanel.printWindow.reviewList.length === 0
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            text: printReviewPanel.printWindow.rows.length > 0
                  && Number(printReviewPanel.printWindow.quality.total || 0) > 0
                  ? qsTr("All of your pictures are ready to print.")
                  : qsTr("There are no pictures left to print.")
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PicasaButton {
                objectName: "printReviewRemoveSelectedButton"
                Layout.fillWidth: true
                enabled: printReviewList.currentIndex >= 0
                text: qsTr("Remove Selected Items")
                onClicked: printReviewPanel.printWindow.removeSelectedReviewPicture()
            }
            PicasaButton {
                objectName: "printReviewRemoveLowButton"
                Layout.fillWidth: true
                enabled: printReviewPanel.printWindow.reviewList.length > 0
                text: qsTr("Remove Low Quality Pictures")
                onClicked: printReviewPanel.printWindow.removeLowQualityReviewPictures()
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "printReviewAcceptButton"
                text: qsTr("OK")
                enabled: Number(printReviewPanel.printWindow.quality.total || 0) > 0
                onClicked: printReviewPanel.printWindow.acceptReviewAndPrint()
            }
            PicasaButton {
                objectName: "printReviewCancelButton"
                text: qsTr("Cancel")
                onClicked: printReviewPanel.printWindow.cancelReview()
            }
        }
    }
}
