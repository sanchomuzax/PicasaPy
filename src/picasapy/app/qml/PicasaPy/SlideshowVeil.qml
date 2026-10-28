import QtQuick

//: #433: az áttűnés FÁTYLA (fekete vagy fehér) — a `dissolveblack` és a
//: `dissolvewhite` ezen megy át. A diák FÖLÖTT, a vezérlősáv ALATT.
Rectangle {
    id: fatyol
    objectName: "slideshowVeil"
    anchors.fill: parent
    color: "#000000"
    opacity: 0
    visible: opacity > 0
}
