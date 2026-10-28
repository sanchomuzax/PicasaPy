import QtQuick

// gumikeret-vizualizáció
Rectangle {
    id: lassoBand
    visible: false
    z: 10
    color: "#33009eff"
    border.color: Theme.thumbSelection
    border.width: 1
    function update(a, b) {
        x = Math.min(a.x, b.x); y = Math.min(a.y, b.y)
        width = Math.abs(a.x - b.x)
        height = Math.abs(a.y - b.y)
        visible = true
    }
}
