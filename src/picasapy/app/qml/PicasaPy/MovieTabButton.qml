import QtQuick
import QtQuick.Controls

// Egy fül a Mozgófilm bal hasábjának fülsávjában (#5264).
//
// A Windows-os mérce szerint a kijelölt fül világos, és az alja a lapba
// nyílik (nincs alsó szegélye); a nem kijelölt fül kékes átmenetű, kék
// szegéllyel. A színek a Theme mért tokenjei.
//
// TabButton, nem AbstractButton: AbstractButton-nal a Klipek fülre kattintva
// a teszt szerint összeomlott a főablak; a TabButton-nal nem.
TabButton {
    id: control
    topPadding: control.down ? 1 : 0

    contentItem: Text {
        text: control.text
        font: control.font
        color: Theme.ink
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        border.width: 2
        border.color: Theme.movieTabBorder
        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: control.down
                       ? Qt.darker(control.checked ? Theme.movieTabSelected : Theme.movieTabFillTop, 1.16)
                       : (control.checked ? Theme.movieTabSelected : Theme.movieTabFillTop)
            }
            GradientStop {
                position: 1.0
                color: control.down
                       ? Qt.darker(control.checked ? Theme.movieTabSelected : Theme.movieTabFillBottom, 1.16)
                       : (control.checked ? Theme.movieTabSelected : Theme.movieTabFillBottom)
            }
        }
        // A kijelölt fül alja a lap felé nyílik: a szegélyt egy azonos színű
        // csík takarja el.
        Rectangle {
            visible: control.checked
            color: Theme.movieTabSelected
            height: 2
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
        }
    }
}
