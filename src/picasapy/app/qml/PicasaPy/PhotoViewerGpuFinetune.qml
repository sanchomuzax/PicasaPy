import QtQuick
import PicasaPy.Gpu

//: #3755: a GPU-réteg a `fokuszKeret` geometriáját és
//: VÁGÁSÁT követő tartóban ül. A `photoArea` közvetlen
//: gyerekeként nagyításnál (ab, bal fókusz, zoom 0,8)
//: átlógott a másik fél képére, mert a keret `clip`-je
//: csak a keret SAJÁT gyerekeit vágja. Egyképes nézetben
//: a `fokuszKeret` a `photoKeret` (a teljes `photoArea`,
//: `clip: false`), tehát ott semmi nem változik.
Item {
    required property var photoArea
    required property var gpuPrefixImage
    required property var gpuLutImage
    id: gpuFinetuneVago
    objectName: "gpuFinetuneVago"
    x: photoArea.fokuszKeret.x
    y: photoArea.fokuszKeret.y
    width: photoArea.fokuszKeret.width
    height: photoArea.fokuszKeret.height
    clip: photoArea.fokuszKeret.clip
    GpuPointFilterPreview {
        id: gpuFinetunePreview
        objectName: "gpuFinetunePreview"
        // #415: NEM `anchors.fill: photo` — az a `photo`
        // TELJES befoglaló dobozára igazítana (a
        // rendelkezésre álló terület, `photo.width`/
        // `photo.height`), nem a `PreserveAspectFit`
        // fillMode által ténylegesen kirajzolt, letterboxolt
        // téglalapra. Álló képnél a doboz szélesebb, mint a
        // kirajzolt kép — a húzás alatt ez a réteg (a
        // `fokuszKep` fölött) a doboz teljes szélességére
        // nyúlt, majd
        // elrejtésekor (elengedéskor) a helyesen illesztett
        // `photo` vált újra láthatóvá: ez okozta a
        // bejelentett "kiugrást". A helyes geometria a
        // `cropOverlay`/`facesOverlay` mintáját követi —
        // `paintedWidth`/`paintedHeight`, középre igazítva.
        //: #3755: fixen a `photo`-ra volt kötve — bal
        //: fókusznál (`photoArea.fokuszKep === photoElotte`)
        //: ezért a jobb, NEM kijelölt félre rajzolt a húzás
        //: alatt. A `fokuszKeret`/`fokuszKep` ugyanaz a
        //: leképezés, mint a `frameContentArea`/`cropOverlay`
        //: párjáé fent. Az `x`/`y` a `gpuFinetuneVago`-hoz
        //: (= a `fokuszKeret`-hez) relatív.
        x: photoArea.fokuszKep.x
           + (photoArea.fokuszKep.width
              - photoArea.fokuszKep.paintedWidth) / 2
        y: photoArea.fokuszKep.y
           + (photoArea.fokuszKep.height
              - photoArea.fokuszKep.paintedHeight) / 2
        width: photoArea.fokuszKep.paintedWidth
        height: photoArea.fokuszKep.paintedHeight
        rotation: photoArea.fokuszKep.rotation
        scale: photoArea.fokuszKep.scale
        transformOrigin: Item.Center
        // #402: shader-hibánál (shaderOk=false) némán a
        // CPU-előnézet marad
        visible: photoArea.hostViewer.gpuFinetuneActive && photoArea.hostViewer.gpuFinetuneEligible
                 && photoArea.hostViewer.gpuFinetunePointSafe
                 && gpuFinetunePreview.shaderOk
        sourceItem: gpuPrefixImage
        lutItem: gpuLutImage
        satGain: 1.0
        bwMix: 0.0
    }
}
