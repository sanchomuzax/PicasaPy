import QtQuick

// A vetítő képrétege és áttűnés-animációi. A képek a vetítő közvetlen
// QObject- és vizuális gyerekei, hogy a meglévő hívók ugyanazt az objektumfát lássák.
QtObject {
    id: imageLayer

    property var slideshow: null
    property var previousImage: null
    property var currentImage: null
    property var veil: null
    property var preloadImage: null
    property var panZoomAnimation: null
    property var panZoomFaceAnimation: null
    property SequentialAnimation transitionAnimation: SequentialAnimation {
        id: atmenetAnimacio
        objectName: "slideshowTransition"
        //: a wipe a kimenő képet kicsúsztatja, a push mindkét képet mozgatja,
        //: a kör/négyszög nagyítással nyit, az időgyorsítás rövid zoommal
        //: vált. Az Időrend Dissolve-ja a #6920 görbét (#6926), a többi a korábbi átmenetet tartja.
        ParallelAnimation {
            NumberAnimation {
                target: slideshow._gorbesDissolve
                        ? null : imageLayer.previousImage
                property: "opacity"
                to: slideshow._kilepoKepMozog() ? 1 : 0
                duration: slideshow.transitionMs
            }
            NumberAnimation {
                target: imageLayer.previousImage; property: "transitionOffsetX"
                to: slideshow._kilepoKepMozog() ? slideshow._atmenetIrany().x : 0
                duration: slideshow.transitionMs
            }
            NumberAnimation {
                target: imageLayer.previousImage; property: "transitionOffsetY"
                to: slideshow._kilepoKepMozog() ? slideshow._atmenetIrany().y : 0
                duration: slideshow.transitionMs
            }
            NumberAnimation {
                target: slideshow._gorbesDissolve
                        ? null : imageLayer.currentImage
                property: "opacity"; to: 1
                duration: slideshow.transitionKind === "timelapse"
                          ? slideshow.transitionMs * 0.35 : slideshow.transitionMs
            }
            NumberAnimation {
                target: slideshow._gorbesDissolve ? slideshow : null
                property: "dissolveProgress"
                from: 0
                to: 1
                duration: slideshow._gorbesDissolve
                          ? slideshow.dissolveTransitionMs : 0
                easing.type: Easing.Linear
            }
            NumberAnimation {
                target: imageLayer.currentImage; property: "transitionOffsetX"; to: 0
                duration: slideshow.transitionMs
            }
            NumberAnimation {
                target: imageLayer.currentImage; property: "transitionOffsetY"; to: 0
                duration: slideshow.transitionMs
            }
            NumberAnimation {
                target: slideshow._atmenetTipus === "kenburns"
                        || slideshow._atmenetTipus === "kenburnsaoi" ? null : imageLayer.currentImage
                property: "scale"; to: 1
                duration: slideshow.transitionKind === "timelapse"
                          ? slideshow.transitionMs * 0.35
                          : (slideshow._atmenetTipus === "kenburns"
                             || slideshow._atmenetTipus === "kenburnsaoi" ? 1
                                                                        : slideshow.transitionMs)
                easing.type: slideshow._atmenetTipus === "timelapse"
                             ? Easing.OutExpo : Easing.OutCubic
            }
            NumberAnimation {
                target: imageLayer.veil; property: "opacity"
                to: slideshow._atmenetTipus === "dissolveblack"
                        || slideshow._atmenetTipus === "dissolvewhite" ? 1 : 0
                duration: slideshow._atmenetTipus === "dissolveblack"
                          || slideshow._atmenetTipus === "dissolvewhite"
                          ? slideshow.transitionMs / 2 : 1
            }
        }
        NumberAnimation {
            target: imageLayer.veil; property: "opacity"; to: 0
            duration: slideshow._atmenetTipus === "dissolveblack"
                      || slideshow._atmenetTipus === "dissolvewhite"
                      ? slideshow.transitionMs / 2 : 1
        }
        ScriptAction { script: slideshow._atmenetVege() }
    }
}
