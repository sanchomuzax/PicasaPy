import QtQuick

// Mappa-fejléc a kereső-rács csoportosított nézetéhez (#7): a GridView
// section.delegate-jeként betöltve, minden mappaváltásnál egy teljes
// szélességű sáv a mappanévvel.
Rectangle {
    id: header
    objectName: "photoGridSectionHeader"
    required property string section
    height: 24
    color: Theme.panelHeaderBg
    border.color: Theme.chromeBorder

    Text {
        objectName: "photoGridSectionLabel"
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left; anchors.leftMargin: 8
        text: header.section.split(/[\\/]/).pop()
        font.pixelSize: Theme.fontSize; font.bold: true
        color: Theme.panelHeaderText
    }
}
