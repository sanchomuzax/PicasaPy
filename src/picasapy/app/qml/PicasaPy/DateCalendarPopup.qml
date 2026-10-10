import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Lenyíló naptár a dátummezőhöz (#4494, a Mappa tulajdonságai Dátum mezőjéhez).
// Az eredeti Picasa dátumválasztója a mező jobb szélén nyílik. Az értéket
// ISO-alakban (ÉÉÉÉ-HH-NN) kapja és adja; a hónap- és napneveket a nyelvi
// beállítás adja, így magyarul a Qt magyar nevei jelennek meg.
Popup {
    id: root

    // a kijelölt nap ISO-alakban ("" = nincs kijelölt nap)
    property string isoDate: ""
    // a látott hónap (a hónap 0-tól számolt, mint a JS Date-ben)
    property int viewYear: 2000
    property int viewMonth: 0

    signal dateChosen(string isoDate)

    function ketjegyu(ertek) {
        return (ertek < 10 ? "0" : "") + ertek
    }

    function isoOf(ev, honap, nap) {
        return ev + "-" + root.ketjegyu(honap) + "-" + root.ketjegyu(nap)
    }

    // a megadott ISO-nap hónapját mutatja; üres vagy hibás értéknél a mai hónap
    function openOn(iso) {
        var reszek = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
        var alap = reszek
            ? new Date(Number(reszek[1]), Number(reszek[2]) - 1, 1)
            : new Date()
        root.isoDate = reszek ? iso : ""
        root.viewYear = alap.getFullYear()
        root.viewMonth = alap.getMonth()
        root.open()
    }

    // a horgony alá nyílik; a helyzetet nyitáskor számoljuk, mert a dátummező
    // az elrendezés után kerül a helyére
    function openBelow(horgony, iso) {
        var pont = horgony.mapToItem(root.parent, 0, horgony.height)
        root.x = pont.x
        root.y = pont.y + 2
        root.openOn(iso)
    }

    function shiftMonth(delta) {
        var uj = new Date(root.viewYear, root.viewMonth + delta, 1)
        root.viewYear = uj.getFullYear()
        root.viewMonth = uj.getMonth()
    }

    // a windowsos dátumválasztó naptára kompakt (≈ 230 × 200 képpont)
    width: 236
    height: 206
    padding: 6
    modal: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        RowLayout {
            Layout.fillWidth: true

            Button {
                objectName: "datePickerPreviousMonth"
                text: "‹"
                implicitWidth: 28
                implicitHeight: 22
                onClicked: root.shiftMonth(-1)
                ToolTip.visible: hovered
                ToolTip.delay: Theme.tooltipDelay
                ToolTip.text: qsTr("Previous month")
            }

            Text {
                objectName: "datePickerMonthTitle"
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                // a QML Locale a hónapot 0-tól számolja
                text: Qt.locale().standaloneMonthName(root.viewMonth)
                    + " " + root.viewYear
                color: Theme.ink
                font.pixelSize: Theme.fontSize
            }

            Button {
                objectName: "datePickerNextMonth"
                text: "›"
                implicitWidth: 28
                implicitHeight: 22
                onClicked: root.shiftMonth(1)
                ToolTip.visible: hovered
                ToolTip.delay: Theme.tooltipDelay
                ToolTip.text: qsTr("Next month")
            }
        }

        GridLayout {
            id: monthGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 7
            rowSpacing: 0
            columnSpacing: 0
            readonly property int firstWeekday:
                (new Date(root.viewYear, root.viewMonth, 1).getDay() + 6) % 7

            Repeater {
                // a QML Locale a napot Qt szerint számolja: 1 = hétfő … 7 = vasárnap
                model: 7
                delegate: Text {
                    required property int index
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: Qt.locale().standaloneDayName(
                        index + 1, Locale.ShortFormat)
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize - 2
                }
            }

            Repeater {
                model: 42
                delegate: ItemDelegate {
                    id: dayCell
                    required property int index
                    readonly property var dayDate: new Date(
                        root.viewYear,
                        root.viewMonth,
                        1 - monthGrid.firstWeekday + index)
                    readonly property string iso: root.isoOf(
                        dayDate.getFullYear(),
                        dayDate.getMonth() + 1,
                        dayDate.getDate())
                    objectName: "calendarDay_" + iso
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    implicitWidth: 30
                    implicitHeight: 20
                    padding: 0
                    text: String(dayDate.getDate())
                    contentItem: Text {
                        text: dayCell.text
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: Theme.fontSize - 1
                        color: dayCell.enabled ? Theme.ink : Theme.textGray
                    }
                    enabled: dayDate.getMonth() === root.viewMonth
                    highlighted: iso === root.isoDate
                    onClicked: {
                        root.dateChosen(iso)
                        root.close()
                    }
                }
            }
        }
    }
}
