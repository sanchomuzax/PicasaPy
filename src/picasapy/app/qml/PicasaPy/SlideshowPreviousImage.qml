import QtQuick

//: #433: a KIMENŐ dia — az átmenet alatt ez halványul el. A fő kép
//: ALATT rajzolódik (előbb szerepel), tehát az áttűnés végén a bejövő
//: kép van fölül.
Image {
    id: elozoSlide
    property var slideshow: null
    objectName: "slideshowPrevImage"
    property real transitionOffsetX: 0
    property real transitionOffsetY: 0
    property bool exactPanZoomGeometry: false
    property real capturedPanZoomX: 0
    property real capturedPanZoomY: 0
    //: a méretet/elfordulást a váltáskor a `_geometriatAtvesz` írja —
    //: ezek csak a kezdőértékek (első dia, még nincs mit másolni)
    width: parent.width
    height: parent.height
    x: exactPanZoomGeometry
       ? capturedPanZoomX + transitionOffsetX
       : (parent.width - width) / 2 + transitionOffsetX
    y: exactPanZoomGeometry
       ? capturedPanZoomY + transitionOffsetY
       : (parent.height - height) / 2 + transitionOffsetY
    opacity: 0
    fillMode: Image.PreserveAspectFit
    asynchronous: false
    autoTransform: true
    //: #3832: a kimenő dia a KIMENŐ kép forrásméretét kapja (az
    //: `_atmenetIndit` írja a forrással együtt) — ez csak a kezdőérték
    sourceSize: slideshow.forrasMeret(-1)
}
