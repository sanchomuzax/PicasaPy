import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #4332: dátum- és időmódosítás a kijelölt képeken, az eredeti két móddal.
Dialog {
    id: root
    objectName: "adjustTimestampDialog"
    property var timestampController
    property var photoRows: []
    property var previewInfo: ({})
    readonly property bool thumbnailLoaded:
        previewThumbnail.status === Image.Ready
    property string currentDateTime: ""
    property bool relativeMode: true
    property int selectedYear: 2000
    property int selectedMonth: 1
    property int selectedDay: 1
    property int calendarYear: 2000
    property int calendarMonth: 0

    title: qsTr("Adjust Photo Date - %1 items").arg(photoRows.length)
    modal: true
    width: 540
    parent: Overlay.overlay
    anchors.centerIn: parent
    standardButtons: Dialog.Ok | Dialog.Cancel

    function ketjegyu(value) {
        return (value < 10 ? "0" : "") + value
    }

    function ujDatumSzoveg() {
        return selectedYear + "-" + ketjegyu(selectedMonth) + "-"
            + ketjegyu(selectedDay)
    }

    function datumSzoveg(ev, honap, nap) {
        return ev + "-" + ketjegyu(honap) + "-" + ketjegyu(nap)
    }

    function naptarHonapja(delta) {
        var uj = new Date(calendarYear, calendarMonth + delta, 1)
        calendarYear = uj.getFullYear()
        calendarMonth = uj.getMonth()
    }

    function openForRows(rows) {
        if (!timestampController || !rows || rows.length === 0)
            return
        photoRows = rows.slice()
        previewInfo = timestampController.adjustTimestampPreview(photoRows[0])
        currentDateTime = previewInfo.dateTime
        var reszek = currentDateTime.split(" ")
        var datum = reszek[0].split("-")
        var ido = reszek[1].split(":")
        selectedYear = Number(datum[0])
        selectedMonth = Number(datum[1])
        selectedDay = Number(datum[2])
        calendarYear = selectedYear
        calendarMonth = selectedMonth - 1
        ujIdo.value = Number(ido[0]) * 3600
            + Number(ido[1]) * 60 + Number(ido[2])
        relativeMode = true
        relativeButton.checked = true
        open()
    }

    Component.onCompleted: {
        standardButton(Dialog.Ok).objectName = "adjustTimestampAccept"
        standardButton(Dialog.Cancel).objectName = "adjustTimestampCancel"
    }

    onAccepted: timestampController.adjustPhotoDates(
        photoRows,
        currentDateTime,
        ujDatumSzoveg() + " " + ujIdo.textFromValue(ujIdo.value, Qt.locale()),
        relativeButton.checked)

    contentItem: ColumnLayout {
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 14

            Image {
                id: previewThumbnail
                objectName: "adjustTimestampThumbnail"
                Layout.preferredWidth: 128
                Layout.preferredHeight: 96
                source: root.previewInfo.thumbnailUrl || ""
                fillMode: Image.PreserveAspectFit
                asynchronous: true
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                Text {
                    objectName: "adjustTimestampCurrentDate"
                    Layout.fillWidth: true
                    text: qsTr("Current photo date") + ": " + root.currentDateTime
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize
                }

                Text {
                    Layout.fillWidth: true
                    text: qsTr("New photo date")
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Button {
                        id: newDateButton
                        objectName: "adjustTimestampNewDate"
                        Layout.fillWidth: true
                        text: root.ujDatumSzoveg()
                        onClicked: calendarPopup.open()
                    }

                    SpinBox {
                        id: ujIdo
                        objectName: "adjustTimestampTime"
                        from: 0
                        to: 86399
                        stepSize: 60
                        editable: true
                        implicitWidth: 126
                        validator: RegularExpressionValidator {
                            regularExpression: /^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$/
                        }
                        textFromValue: function(value, locale) {
                            var seconds = Number(value)
                            var hour = Math.floor(seconds / 3600)
                            var minute = Math.floor((seconds % 3600) / 60)
                            var second = seconds % 60
                            return root.ketjegyu(hour) + ":"
                                + root.ketjegyu(minute) + ":"
                                + root.ketjegyu(second)
                        }
                        valueFromText: function(text, locale) {
                            var match = /^(\d{2}):(\d{2}):(\d{2})$/.exec(text)
                            if (!match)
                                return value
                            return Number(match[1]) * 3600
                                + Number(match[2]) * 60 + Number(match[3])
                        }
                        ToolTip.visible: hovered
                        ToolTip.delay: Theme.tooltipDelay
                        ToolTip.text: qsTr("New photo time")
                    }
                }
            }
        }

        ButtonGroup { id: modeGroup }

        RadioButton {
            id: relativeButton
            objectName: "adjustTimestampRelative"
            text: qsTr("Adjust all photo dates by the amount")
            checked: true
            ButtonGroup.group: modeGroup
            font.pixelSize: Theme.fontSize
        }

        RadioButton {
            id: absoluteButton
            objectName: "adjustTimestampAbsolute"
            text: qsTr("Set all photos to the same date and time")
            ButtonGroup.group: modeGroup
            font.pixelSize: Theme.fontSize
        }
    }

    Popup {
        id: calendarPopup
        objectName: "adjustTimestampCalendar"
        parent: root.contentItem
        x: 0
        y: newDateButton.mapToItem(
            root.contentItem, 0, newDateButton.height).y + 4
        width: 320
        height: 326
        modal: false
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        contentItem: ColumnLayout {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 4

            RowLayout {
                Layout.fillWidth: true

                Button {
                    objectName: "adjustTimestampPreviousMonth"
                    text: "‹"
                    onClicked: root.naptarHonapja(-1)
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    ToolTip.text: qsTr("Previous month")
                }

                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: Qt.formatDate(
                        new Date(root.calendarYear, root.calendarMonth, 1),
                        "MMMM yyyy")
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize
                }

                Button {
                    objectName: "adjustTimestampNextMonth"
                    text: "›"
                    onClicked: root.naptarHonapja(1)
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    ToolTip.text: qsTr("Next month")
                }
            }

            GridLayout {
                id: monthGrid
                objectName: "adjustTimestampMonthGrid"
                Layout.fillWidth: true
                Layout.fillHeight: true
                columns: 7
                rowSpacing: 2
                columnSpacing: 2
                property int year: root.calendarYear
                property int month: root.calendarMonth
                readonly property int firstWeekday:
                    (new Date(year, month, 1).getDay() + 6) % 7

                Text {
                    text: qsTr("Mon")
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize - 2
                }
                Text {
                    text: qsTr("Tue")
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize - 2
                }
                Text {
                    text: qsTr("Wed")
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize - 2
                }
                Text {
                    text: qsTr("Thu")
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize - 2
                }
                Text {
                    text: qsTr("Fri")
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize - 2
                }
                Text {
                    text: qsTr("Sat")
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize - 2
                }
                Text {
                    text: qsTr("Sun")
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize - 2
                }

                Repeater {
                    model: 42
                    delegate: ItemDelegate {
                        required property int index
                        readonly property var calendarDate: new Date(
                            monthGrid.year,
                            monthGrid.month,
                            1 - monthGrid.firstWeekday + index)
                        objectName: "adjustTimestampCalendarDay_"
                            + root.datumSzoveg(
                                calendarDate.getFullYear(),
                                calendarDate.getMonth() + 1,
                                calendarDate.getDate())
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        implicitWidth: 38
                        implicitHeight: 32
                        text: String(calendarDate.getDate())
                        enabled: calendarDate.getMonth() === monthGrid.month
                        onClicked: {
                            root.selectedYear = calendarDate.getFullYear()
                            root.selectedMonth = calendarDate.getMonth() + 1
                            root.selectedDay = calendarDate.getDate()
                            calendarPopup.close()
                        }
                    }
                }
            }
        }
    }
}
