import QtQuick

// elő-betöltés a következő fotóra (DoD): mire a timer lép, a kép
// már dekódolva van
Image {
    id: elobetoltoSlide
    property var slideshow: null
    objectName: "slideshowPreloadImage"
    visible: false
    // #1640 + #3832: a forrást és a forrásméretet a `_diakBetolt` írja
    // — ugyanazt a párt, amit a dia kér majd erre a képre, így a lépéskor
    // a Qt gyorstárából jön
    //: #3832: a kitöltési mód is a gyorstár kulcsának része (a Qt a
    //: betöltőnek átadja) — eltérő `fillMode`-dal az elő-betöltött kép
    //: nem volt a diáé, és lépéskor újra dekódolódott (MÉRVE: minden
    //: lépés kétszer kérte ugyanazt a képet a szolgáltatótól)
    fillMode: Image.PreserveAspectFit
    asynchronous: Qt.platform.pluginName !== "offscreen"
    autoTransform: true
    sourceSize: slideshow.forrasMeret(-1)
}
