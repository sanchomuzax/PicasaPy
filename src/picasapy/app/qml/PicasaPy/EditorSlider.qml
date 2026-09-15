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

    grooveThickness: 9
    handleWidth: 16
    handleHeight: editorSlider.scaleCsalad ? 22 : 26
    handleRadius: 3
}
