import QtQuick
import QtQuick.Layouts

// Indexkép-csoport fejléce - dizajnkézikönyv 08 + #423 (a Picasa saját
// `headerpanel.tre` respack-forrása szerinti tipográfia és elrendezés):
//   - cím: Georgia 20pt, a fejléc bal szélétől 50px behúzva (a mappa-ikon
//     UTÁN), jobbról a fejléc szélétől 20px-re levágva - hosszú névnél
//     halványuló kifutással, NEM "…"-tal;
//   - dátumsor: Georgia 14pt, ugyanaz a 50px-es bal behúzás;
//   - jobb-felső sarok: „Szinkronizálás az internettel" felirat + kapcsoló
//     (letiltott, funkció nélkül - csak az elrendezés része).
ColumnLayout {
    id: header
    property string folderName: ""
    property string dateText: ""
    property string description: ""
    signal descriptionEdited(string text)
    // zöld ▸: a mappa diavetítése (#8) - a bekötés a Main.qml-ben
    signal playRequested()
    // #422: a mappa-kontextusmenü HARMADIK megnyitási pontja - a felmérés
    // szerint a fejlécre jobbklikkelve UGYANAZ a 15 tételes menü jön elő,
    // mint a rács üres területén és a bal panel mappa-során
    signal contextMenuRequested()

    //: #1823: a fejléc-gombok DARABSZÁMOT írnak ki. A bináris erőforrásai
    //: minden fejléc-gombot két alakban tartanak - `albumbutton_save` és
    //: `albumbutton_save%d` -, vagyis üres kijelölésnél a szám nélküli,
    //: kijelölésnél a számos felirat megy ki.
    //:
    //: ⚠️ A `play` gombra ez NEM igaz: a mért listában (`save`, `sstar`,
    //: `sall`, `album`, `cd`, `menu`, `pubaction`) nincs `play%d`. A
    //: diavetítés ezért ikon marad, szám nélkül - a jegy „a play is"
    //: mondata a mérésnek mond ellent.
    property int selectedCount: 0
    // #5883: csak akkor menthetők a kijelöltek, ha valamelyik képen van
    // mentetlen szerkesztési lánc.
    property bool hasPendingEdits: false

    //: „Szerkesztések mentése lemezre" (`save_edits`) - a kijelölt képek
    //: szerkesztéseit a FÁJLBA írja. A művelet maga a #444 mentés-
    //: párbeszédéé; ez a gomb csak egy újabb belépési pont hozzá.
    signal saveEditsRequested()

    //: „Csillagozottak kijelölése" (`select_star`) - ugyanaz a parancs,
    //: mint a menüsávban; itt is a jelenlegi mappára hat (#1145).
    signal selectStarredRequested()
    //: #1006: kollázs a fejléc csoportjából. Az eredetiben NÉGY belépési
    //: pont van; nálunk kettő működött (Létrehozás menü, kimeneti sáv), a
    //: két fejléc-gomb hiányzott.
    signal collageRequested()
    //: #4539: a mappa-fejléc film-gombja - ugyanaz a csoport-kép halmaz,
    //: mint a kollázsnál (a fejléc SAJÁT csoportjának képei).
    signal movieRequested()
    //: A két `faceheaderpanel` filmgomb ugyanazt a meglévő Filmkészítőt
    //: nyitja meg az aktuális személy-album képeivel.
    signal personMovieRequested()
    signal removePersonAlbumRequested()

    //: #2187: a SZEMÉLY-ALBUM módja. Az eredetiben a személy-album
    //: fejléce saját panel (`faceheaderpanel`), és rajta ül a
    //: javaslat-munkafolyamat; nálunk a személy képei ugyanebben a
    //: rácsban, ugyanezzel a fejléccel jelennek meg, ezért a vezérlők
    //: ide kerülnek, ebbe a módba. Üres név = nem személy-album.
    property string personName: ""
    property bool personAlbumHeaderMode: false
    property bool personAlbumFolderMode: false
    property string personAvatarUrl: ""
    property bool personAlbumRemoveEnabled: false
    property bool personAlbumThumbnailEnabled: false
    //: hány MÉG EL NEM DÖNTÖTT javaslat tartozik ehhez a személyhez -
    //: a gazda tölti a vezérlő `personSuggestionCount`-jából
    property int suggestionCount: 0
    //: a rács KIJELÖLÉSÉN ülő, e személyre szóló függő javaslatok száma -
    //: a gazda tölti. Ha nem nulla, a két gomb a kijelöltekre hat
    //: (`confirmsel`, `removesel`), különben az összesre (`confirmsug`).
    property int selectedSuggestionCount: 0
    readonly property bool kijeloltJavaslatHatokor:
        header.selectedSuggestionCount > 0
    //: `confirmsug` / `confirmsel` - a javaslatok jóváhagyása; a hatókört
    //: a gazda a kijelölésből dönti el
    signal confirmSuggestionsRequested()
    //: `selectsug` - a jelenlegi személy függő javaslatait tartalmazó képek
    //: kijelölése a rácsban
    signal selectSuggestionsRequested()
    //: `removesel` - a javaslatok elvetése (a kijelöltek, vagy ha nincs
    //: kijelölt javaslat, mind)
    signal removeSuggestionsRequested()
    //: `moresug` - a felismerési lépcső lazítása, hogy több javaslat jöjjön
    signal moreSuggestionsRequested()
    signal setPersonThumbnailRequested()
    //: `sug_filter` - a javaslat-szűrő állása (a gazda vezérlőjéből)
    property bool suggestionsOnly: false
    //: `sug_filter` - a szűrő átkapcsolása; az új állapotot adja át
    signal suggestionsOnlyToggled(bool csak)

    //: #2187: az arc ↔ teljes kép nagyításváltó (`face_zoom` ↔
    //: `picture_zoom`) állása - a gazda vezérlőjéből
    property bool faceZoom: false
    //: a váltó átkapcsolása; az új állapotot adja át (igaz = arc)
    signal faceZoomToggled(bool arc)

    //: a két javaslat-vezérlő együtt jelenik meg: nyitott személy-album ÉS
    //: van mit eldönteni
    readonly property bool javaslatokLatszanak:
        header.personName !== "" && header.suggestionCount > 0

    //: #2187: a javaslat-szűrő akkor van kint, ha van mit szűrni -
    //: VAGY ha már be van kapcsolva. A második fél nem díszítés: ha az
    //: utolsó javaslatot jóváhagyjuk, a darabszám nullára esik, és a
    //: gomb eltűnése bent hagyná a rácsot az üres, szűrt nézetben,
    //: visszakapcsolási lehetőség nélkül.
    readonly property bool javaslatSzuroLatszik:
        header.personName !== ""
        && (header.suggestionCount > 0 || header.suggestionsOnly)

    //: #2187: a `moresug` a jóváhagyás-pár TELJES helyét foglalja el
    //: (mérve: `confirmsug` (348,55)-(436,82), `removesel` (439,55)-(527,82),
    //: `moresug` (348,55)-(527,82)) - tehát akkor látszik, amikor nincs mit
    //: jóváhagyni. A két állapot kizárja egymást.
    readonly property bool tovabbiJavaslatLatszik:
        header.personName !== "" && header.suggestionCount === 0
        && !header.personAlbumHeaderMode

    //: A számos/szám nélküli alak választása egy helyen, hogy minden
    //: fejléc-gomb ugyanúgy viselkedjen.
    function feliratSzammal(alap) {
        return header.selectedCount > 0
            ? alap + " (" + header.selectedCount + ")" : alap
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onSingleTapped: header.contextMenuRequested()
    }
    spacing: 3

    LightboxHeaderTitle {
        header: header
    }

    Text {
        objectName: "folderDateText"
        visible: !header.personAlbumHeaderMode && header.dateText !== ""
        text: header.dateText
        color: Theme.folderDate
        font.family: "Georgia"
        font.pointSize: header.personAlbumFolderMode ? 10 : 14
        Layout.leftMargin: 50
    }

    LightboxHeaderButtons {
        header: header
    }

    LightboxHeaderDescription {
        header: header
    }

    //: a gombok közti hézag - a korábbi `RowLayout` `spacing`-je
    readonly property int gombKoz: 6
    readonly property int personHeaderExtraGap:
        header.personAlbumHeaderMode ? 2 : header.gombKoz

}
