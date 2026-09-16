import QtQuick

// #710: a szerkesztő csúszkáinak KÖZÖS komponense — a mért geometria EGY
// helyen él. Eddig három panel írta le ugyanazokat a számokat
// (`EditorFinetunePanel`, `EditorParamPanel`, `EditorTabCommonFixes`), és a
// #2626 felirat-javítása épp azért ment át csak kettőn, mert három helyen
// kellett volna.
//
// ⚠️ KÉT MÉRT CSALÁD van, és a különbség nem elírás:
//
//   editslider   (`editpanel/clip(editslider,editsliderN)`) — a finomhangoló
//                négy csúszkája ÉS a csúszkás paraméter-alpanel:
//                sáv 9, fogantyú 16 × **26**, sarok 3
//   scaleslider  (`editpanel/clip(scaleslider,flightslider1)`) — a Gyakori
//                javítások Derítőfénye:
//                sáv 9, fogantyú 16 × **22**, sarok 3
//
// A `respack.yt`-ból mérve (#2627): `editslider/sliderbase` 121 × 9 és
// `editslider/thumb` 16 × 26 (ebből 22 tömör + 3 lágy árnyék);
// `scaleslider/sliderbase` 121 × 9, `scaleslider/thumb` 16 × 22.
//
// ⚠️ A SZÍN nem itt dől el: a `PicasaSlider` sávja ma semleges
// (`Theme.chromeBg`), az eredetié kékes — az a #2627 másik fele, és az egész
// alkalmazás csúszkáit érinti.
PicasaSlider {
    id: editorSlider

    //: melyik mért családba tartozik: "editslider" (alap) vagy "scaleslider"
    property string csalad: "editslider"

    readonly property bool scaleCsalad: editorSlider.csalad === "scaleslider"

    //: ⭐ #710: az `editcontrol_well` MÉRT elrendezése — a spec szerint a
    //: Finomhangolás fül ÉS a csúszkás paraméter-alpanel UGYANAZ a
    //: vezérlőkészlet (`editpanel/tab2 → showtarget editpanel/editcontrol_well`,
    //: és minden csúszka/jelölő/korong/pipetta/radír, valamint az
    //: Alkalmaz/Mégse ennek a gyermeke — `ui-audit-editor.md` 4.4).
    //:
    //: A geometria (`szerkeszto-panel-meretek.md` 4.): a négy csúszka
    //: **191 × 27**, mind az **x 30**-on (a fül 13 képpontos bal margójához
    //: képest **17** képpont eltolás), a feliratuk **151 × 12** a csúszka
    //: FÖLÖTT, középre zárva.
    //:
    //: Itt, a KÖZÖS komponensen élnek, hogy egy helyen legyenek — eddig a
    //: `EditorFinetunePanel` írta le őket a saját fájljában.
    //:
    //: ⚠️ **A paraméter-alpanel NEM ezt a szélességet használja ma**, hanem
    //: panel-közepű, teljes szélességű csúszkát (#700). Hogy az eredetiben a
    //: két hely tényleg azonos elrendezésű-e, az **nyitott**: a mért tábla
    //: (`szerkeszto-panel-meretek.md` 4.) a FINOMHANGOLÁS négy csúszkáját
    //: adja meg (`editslider1..4_container`, x 30..221), a paraméter-alpanel
    //: konténere pedig ugyanott **127 × 27 vagy 191 × 27** alakban szerepel —
    //: tehát a „ugyanaz a well ⇒ ugyanaz a szélesség" következtetés
    //: BIZONYÍTÉK NÉLKÜLI. A kérdés a #710-en áll, képernyőképpel dönthető.
    readonly property int mertSzelesseg: 191
    readonly property int mertMagassag: 27
    readonly property int mertEltolas: 17
    readonly property int mertFeliratSzelesseg: 151

    grooveThickness: 9
    handleWidth: 16
    handleHeight: editorSlider.scaleCsalad ? 22 : 26
    handleRadius: 3
}
