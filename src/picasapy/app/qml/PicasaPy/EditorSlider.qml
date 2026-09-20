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
    //: ✅ **A paraméter-alpanel is EZT a szélességet használja** (#710,
    //: 2026-09-18/19). A kérdés korábban nyitott volt („127 × 27 vagy
    //: 191 × 27?"), és képernyőképet kértünk rá — a tulajdonos joggal
    //: visszautasította: *„Ez nem tőlem kérdezendő adat… a forrásból pontosan
    //: kimérhető."* A FORRÁS döntött (`ui-audit-editor.md` 4.3/a):
    //:
    //: * az `editpanel.tre`-ben mind a négy `editsliderN_container`
    //:   ugyanannak az `editcontrol_well`-nek a gyermeke, `m_centerXY`-val;
    //: * a `tab3`–`tab5` nem hoz létre effekt-specifikus slider-konténert, és
    //:   a 2–4. konténer ugyanahhoz a feldolgozó címhez kötődik
    //:   (`0x007518e0`);
    //: * a **127 × 27** a KÜLÖN `scaleslider` családé (`backlight_container`,
    //:   Derítőfény) — nem a paraméter-alpanelé.
    //:
    //: ⇒ a „ugyanaz a well ⇒ ugyanaz a geometria" következtetés már NEM
    //: bizonyíték nélküli.
    readonly property int mertSzelesseg: 191
    readonly property int mertMagassag: 27
    readonly property int mertEltolas: 17
    readonly property int mertFeliratSzelesseg: 151

    grooveThickness: 9
    handleWidth: 16
    handleHeight: editorSlider.scaleCsalad ? 22 : 26
    handleRadius: 3
}
