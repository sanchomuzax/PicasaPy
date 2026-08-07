import QtQuick
import QtQuick.Controls

// #416: helyfoglaló (még be nem kötött) menüpont — a menü HELYE megvan, de
// funkció nincs mögötte. Ránézésre is látszódjon, mi működik és mi nem:
// - a felirat halványabb (Theme.textGray, a meglévő "letiltott" tokent
//   használjuk — a Theme.qml forró fájl, új tokent nem veszünk fel),
// - a sor jobb szélén egy kicsi, világosszürke pont jelenik meg.
//
// Csak a placeholder tételeknél használjuk — a MŰKÖDŐ menüpontok
// változatlanul a sima QtQuick.Controls `MenuItem`-et használják, ezért a
// kinézetük ettől a komponenstől nem változhat.
MenuItem {
    id: control

    // a szándék explicit jelölése (#416) — mindig true-val hívjuk a
    // PicasaMenuBar.qml-ben, hogy a forrásban is egyértelmű legyen, mely
    // tételek csak helyfoglalók
    property bool placeholder: true

    // a helyfoglaló tétel sosem kattintható — a `placeholder: true` a
    // korábbi explicit `enabled: false`-t váltja ki
    enabled: !placeholder

    contentItem: Text {
        text: control.text
        font: control.font
        color: control.placeholder ? Theme.textGray : Theme.ink
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
        // hely a jobb szélen a placeholder-pontnak, hogy ne fedjék egymást
        rightPadding: control.placeholder ? placeholderDot.width + 8 : 0
    }

    Rectangle {
        id: placeholderDot
        objectName: "placeholderDot"
        visible: control.placeholder
        width: 5
        height: 5
        radius: width / 2
        color: Theme.textGray
        anchors.right: control.right
        anchors.rightMargin: 8
        anchors.verticalCenter: control.verticalCenter
    }
}
