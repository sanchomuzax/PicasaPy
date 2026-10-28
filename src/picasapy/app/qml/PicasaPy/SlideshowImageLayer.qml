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
        //: vált. A dissolve és a színfátyol a korábbi átmenetet tartja.
        ParallelAnimation {
            NumberAnimation {
                target: imageLayer.previousImage; property: "opacity"
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
                target: imageLayer.currentImage; property: "opacity"; to: 1
                duration: slideshow.transitionKind === "timelapse"
                          ? slideshow.transitionMs * 0.35 : slideshow.transitionMs
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
                target: slideshow.transitionKind === "kenburns"
                        || slideshow.transitionKind === "kenburnsaoi" ? null : imageLayer.currentImage
                property: "scale"; to: 1
                duration: slideshow.transitionKind === "timelapse"
                          ? slideshow.transitionMs * 0.35
                          : (slideshow.transitionKind === "kenburns"
                             || slideshow.transitionKind === "kenburnsaoi" ? 1
                                                                        : slideshow.transitionMs)
                easing.type: slideshow.transitionKind === "timelapse"
                             ? Easing.OutExpo : Easing.OutCubic
            }
            NumberAnimation {
                target: imageLayer.veil; property: "opacity"
                to: slideshow.transitionKind === "dissolveblack"
                        || slideshow.transitionKind === "dissolvewhite" ? 1 : 0
                duration: slideshow.transitionKind === "dissolveblack"
                          || slideshow.transitionKind === "dissolvewhite"
                          ? slideshow.transitionMs / 2 : 1
            }
        }
        NumberAnimation {
            target: imageLayer.veil; property: "opacity"; to: 0
            duration: slideshow.transitionKind === "dissolveblack"
                      || slideshow.transitionKind === "dissolvewhite"
                      ? slideshow.transitionMs / 2 : 1
        }
        ScriptAction { script: slideshow._atmenetVege() }
    }
}
