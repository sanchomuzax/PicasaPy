import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: printSelectionPanel
    property var printWindow
    spacing: 10

    Text {
        objectName: "printSelectionText"
        Layout.fillWidth: true
        //: #3712: a felirat NEM ígéri, hogy hány kép kerül egy lapra —
        //: azt a tényleges lapszám mondja meg (méret szerinti
        //: nyomtatásnál a rácselrendező, indexképnél a
        //: `contactPageCount()` adja, ld. `frissitsdAzElonezetet()`).
        //: #3712-review: a lapszám `%n`-es TÖBBES SZÁM — korábban a
        //: szó szerinti "pages" mindig többes számban állt, tehát egy
        //: lapnál is "(1 pages)" jelent meg.
        text: qsTr("Pictures to print: %1 (%n page(s))", "",
                   printSelectionPanel.printWindow.printPageCount)
              .arg(printSelectionPanel.printWindow.rows.length)
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }

    // #5684: az eredeti párbeszéd Normál/Optimalizált módválasztója.
    // Kizárólag az eredeti nyers állapotpárt menti; a renderelési hatás
    // nincs bekötve, amíg az eredeti és a PicasaPy kimenet nincs mérve.
    RowLayout {
        objectName: "printQualityModeRow"
        Layout.fillWidth: true
        spacing: 8

        ButtonGroup { id: printQualityModeGroup }

        RadioButton {
            objectName: "printModeNormalRadio"
            Layout.fillWidth: true
            ButtonGroup.group: printQualityModeGroup
            text: qsTr("Normal")
            checked: !printSelectionPanel.printWindow.optimizedPrintMode
            onClicked: printSelectionPanel.printWindow.valasszNyomtatasiModot(false)
        }
        RadioButton {
            objectName: "printModeOptimizedRadio"
            Layout.fillWidth: true
            ButtonGroup.group: printQualityModeGroup
            text: qsTr("Optimized")
            checked: printSelectionPanel.printWindow.optimizedPrintMode
            onClicked: printSelectionPanel.printWindow.valasszNyomtatasiModot(true)
        }
    }

    // #4608: nyomtató nélküli gépen kimondja, mit kell tenni. Az
    // eredeti őre (`IDS_MUST_INSTALL_PRINTER`) ugyanezt mondja. A
    // PDF-cél a választóban marad, ezért ez tájékoztat, nem tilt.
    // A tartalom tetején van: kis ablakban a nyomtatóválasztóhoz
    // görgetni kell, a figyelmeztetésnek viszont azonnal látszania kell.
    Text {
        objectName: "printNoPrinterText"
        Layout.fillWidth: true
        visible: !!printSelectionPanel.printWindow.printCtl
                 && printSelectionPanel.printWindow.printers.length === 0
        //: IDS_MUST_INSTALL_PRINTER — a nyomtató-őr üzenete
        text: qsTr("A printer must be installed in order to print.")
        font.pixelSize: Theme.fontSize
        color: Theme.textGray
        wrapMode: Text.WordWrap
    }
}
