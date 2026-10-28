import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

// Létrehozás menü (#29): képkollázs és mozgófilm a kijelölt képekből.
// Az ExportDialogs.qml mintája szerint: beállítás-dialógus → fájlválasztó
// → háttérszálas munka → eredmény-dialógus (controller-jelzésekre).
Item {
    id: dialogs
    anchors.fill: parent
    // a főablak (a kijelölt sorok forrása)
    required property var appWindow

    // #455: van-e a KÉPTÁLCÁN tartott kép — ilyenkor a műveletek a tálca
    // tartalmán futnak (a vezérlő dönt, ld. `_sources_for`), és a
    // párbeszédek kijelölés nélkül is megnyílnak
    readonly property bool trayHasPictures:
        (typeof controller !== "undefined" && controller)
            ? controller.heldCount > 0 : false

    // #431: a HAT Picasa-elrendezés, a FELÜLETI sorrendben (a kulcsok a
    // `.cxf` téma-azonosítói — egy betű eltérés olvashatatlan projektfájlt
    // adna). ⚠️ A „Mozaik" kulcsa `picturegrid`, a „Rács"-é `regulargrid`.
    readonly property var collageKinds: ["picturepile", "picturegrid", "framegrid",
                                         "regulargrid", "contactsheet", "multiexp"]
    // a három képkeret ugyanígy, a ComboBox sorrendjében
    readonly property var collageBorders: ["noborder", "whiteborder", "polaroid"]
    // #923: a keretválasztó CSAK a Képkupacnál és az Indexképnél létezik az
    // eredetiben (a téma képesség-maszkjának 9. bitje) — a többi témánál a
    // renderelő úgyis figyelmen kívül hagyja, ezért ne is kínáljuk fel.
    // A panelen ugyanezt a helyet a térköz-csúszka foglalja el.
    readonly property var collageBorderCapable: [true, false, false, false, true, false]

    function openCollage() { collageDialogs.openForSelection() }
    function openMovie() { movieDialog.openForSelection() }
    //: #4331 / `ID_FACES`: a 30. szakasz szerinti kijelölt képeket adja át
    //: a meglévő filmkészítőnek az arc-kivágáshoz.
    function openFaceMovie() {
        var rows = dialogs.appWindow.selectedIndexes
        if (!rows || rows.length === 0) return
        movieDialog.openForRows(rows, false, false)
        movieDialog.personMovieMode = true
        movieDialog.applyDefaultSize()
    }
    function openPoster(sourcePath) { posterDialog.openForSource(sourcePath) }
    function openTimestamp(rows) { timestampDialog.openForRows(rows) }

    AdjustTimestampDialog {
        id: timestampDialog
        timestampController: (typeof controller !== "undefined") ? controller : null
    }
    // #4391: az eredeti People-film szűrt, sorrendtartó képsora kerül
    // közvetlenül a meglévő Filmkészítőbe.
    function openMovieForRows(rows) {
        // Sorindexet fogadó, korábbi nyitási út; People-filmhez a forrás-URL
        // listát fogadó openMovieForSources tartozik.
        movieDialog.openForRows(rows, false, false)
    }
    function openMovieForSources(sources) {
        movieDialog.openForSources(sources)
    }
    //: #2114: a film ÚJRANYITÁSA a projektfájljából — a diaidő onnan
    //: jön, a kijelölés a hívó oldalán már a projekt képeire áll.
    //: ⛔ A FELBONTÁS nincs a projektfájlban (`curresolution` nálunk
    //: kitöltetlen), ezért az marad az alapértelmezésen — a párbeszéd
    //: felirata ezt ki is mondja.
    function openMovieProject(masodperc, burstmodethresh, moviePath) {
        movieDialog.personMovieMode = false
        movieDialog.applyDefaultSize()
        movieDialog.projektbolNyilt = true
        if (moviePath)
            movieDialog.previousMoviePath = String(moviePath)
        if (masodperc > 0)
            movieDialog.setSeconds(Math.round(masodperc * 10))
        if (burstmodethresh !== undefined && burstmodethresh >= 0)
            movieDialog.movieBurstFactor = Math.sqrt(
                Math.min(86400, burstmodethresh) / 86400)
        movieDialog.open()
    }


    PosterCreateDialog {
        id: posterDialog
        appWindow: dialogs.appWindow
    }
    CollageCreateDialog {
        id: collageDialogs
        anchors.fill: parent
        appWindow: dialogs.appWindow
        trayHasPictures: dialogs.trayHasPictures
        collageKinds: dialogs.collageKinds
        collageBorders: dialogs.collageBorders
        collageBorderCapable: dialogs.collageBorderCapable
    }
    MovieMakerDialog {
        id: movieDialog
        appWindow: dialogs.appWindow
        movieDialogs: movieDialogs
        trayHasPictures: dialogs.trayHasPictures
    }
    MovieMakerDialogs {
        id: movieDialogs
        anchors.fill: parent
        movieDialog: movieDialog
    }
    CreateResultDialog {
        id: createResultDialog
    }

    // #1743: a filmátmenet előnézetének készenléti jelzése.
    function jelezdAFilmAtmenetElonezetet(source, generation) {
        movieDialog.jelezdAFilmAtmenetElonezetet(source, generation)
    }

    // #459/3: a hiányzó fájl KÜLÖN mondatot kap az eredeti Picasa
    // szövegével — az megmondja, mi történhetett, és a munka a maradékkal
    // elkészül. Az olvashatatlan (de meglévő) fájlok a régi, semleges
    // „kihagyva" mondatban maradnak.
    function _skippedSuffix(skipped, missing) {
        var text = ""
        if (missing > 0)
            text += "\n" + qsTr("%1 picture(s) could not be found and will not be shown. (The missing files must have been moved, renamed or deleted)").arg(missing)
        var unreadable = skipped - missing
        if (unreadable > 0)
            text += "\n" + qsTr("%1 pictures were skipped.").arg(unreadable)
        return text
    }

    // #2096: a vezérlő jelzéseit NEM itt fogadjuk. Ez a komponens a #1612 óta
    // HALASZTOTT (`DeferredDialog`), tehát amíg a felhasználó meg nem
    // nyitotta, egy itteni `Connections` NEM LÉTEZNE — a jelzés senkihez nem
    // érne el, és a visszajelzés némán elmaradna. A kollázs a Kollázs
    // PANELRŐL is indítható, tehát ez nem elméleti eset (#1743 őre fogta meg).
    //
    // A `Main.qml` mindig álló `Connections`-e hívja az alábbi függvényeket,
    // az `ensure()` után. A logika változatlan; csak a HALLGATÓ került ki.
    // Ugyanez a minta, mint a `SaveDialogs.qml`-nél.

    //: A kollázs élő előnézetének új változata (a panel jelzi).
    function frissitsdAzElonezetet(revision) {
        collageDialogs.previewRevision = revision
    }

    //: A kollázs elkészült — az összegző párbeszéd megnyitása.
    function jelezdAKollazsSikert(path, used, skipped, missing) {
        createResultDialog.message =
            qsTr("Collage saved: %1").arg(path)
            + "\n" + qsTr("%1 pictures used.").arg(used)
            + dialogs._skippedSuffix(skipped, missing)
        createResultDialog.open()
    }

    //: A kollázs nem készült el.
    function jelezdAKollazsHibajat(message) {
        createResultDialog.message =
            qsTr("The collage could not be created.") + "\n" + message
        createResultDialog.open()
    }

    //: A film haladása.
    function frissitsdAFilmHaladast(done, total) {
        movieDialogs.movieProgressDialog.done = done
        movieDialogs.movieProgressDialog.total = total
    }

    //: A film elkészült.
    function jelezdAFilmSikert(path, used, skipped, missing) {
        movieDialogs.movieProgressDialog.close()
        movieDialog.previousMoviePath = path
        createResultDialog.message =
            qsTr("Movie saved: %1").arg(path)
            + "\n" + qsTr("%1 pictures used.").arg(used)
            + dialogs._skippedSuffix(skipped, missing)
        createResultDialog.open()
    }

    //: A film nem készült el.
    function jelezdAFilmHibajat(message) {
        movieDialogs.movieProgressDialog.close()
        createResultDialog.message =
            qsTr("The movie could not be created.") + "\n" + message
        createResultDialog.open()
    }

    //: #4268: a poszterlapok a forráskép mellett készültek el.
    function jelezdAPoszterSikert(paths) {
        createResultDialog.message = qsTr("Poster tiles saved.")
            + "\n" + paths.join("\n")
        createResultDialog.open()
    }

    //: #4268: a poszterlapok írási hibája a párbeszédben jelenik meg.
    function jelezdAPoszterHibajat(message) {
        createResultDialog.message =
            qsTr("The poster tiles could not be created.") + "\n" + message
        createResultDialog.open()
    }
}
