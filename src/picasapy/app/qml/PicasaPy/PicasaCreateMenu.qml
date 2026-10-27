import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

PicasaMenu {
    property var bar: null
    objectName: "menuCreateRoot"
    title: qsTr("&Create")
    //: #1775: `eMenuCreate::ID_WALLPAPER` (`0x9cd2`). Az eredeti MÁSOLATOT
    //: ír (`picasabackground.bmp` a `Picasa/Backgrounds` mappába), nem az
    //: eredeti fájlra mutat, és KÖZÉPRE teszi (`WallpaperStyle=0`,
    //: `TileWallpaper=0`) — mérve, `0x0057aa10`. A motor közös a Kollázs
    //: „Asztali háttérkép" gombjáéval (#1005).
    //:
    //: Kijelölés kell hozzá: a parancs EGY képet tesz háttérképnek, ezért
    //: kijelölés nélkül szürke (a néma kattintás helyett).
    MenuItem {
        objectName: "menuCreateWallpaper"
        text: qsTr("Set as &Desktop...")
        enabled: bar.libraryPhotoActionsEnabled
        onTriggered: bar.wallpaperRequested()
    }
    MenuItem {
        objectName: "menuCreatePoster"
        text: qsTr("Make a &Poster...")
        enabled: bar.libraryPhotoActionsEnabled
        onTriggered: bar.posterRequested()
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    MenuItem {
        objectName: "menuCreateCollage"
        text: qsTr("&Picture Collage...")
        enabled: bar.createActionsEnabled
        onTriggered: bar.collageRequested()
    }
    // hiányzott (#324 audit): OS-integrációs funkciók
    MenuItem {
        objectName: "menuCreateAddScreensaver"
        text: qsTr("Add to &Screensaver...")
        enabled: bar.libraryPhotoActionsEnabled
        onTriggered: bar.addToScreensaverRequested()
    }
    //: #3503: a kiadás-panelt Ajándék-CD üzemmódban nyitja; a tálcáról
    //: dolgozik, ezért ugyanaz a kapu, mint a kollázsé és a filmé
    MenuItem {
        objectName: "menuCreateGiftCd"
        text: qsTr("Create a &Gift CD...")
        enabled: bar.createActionsEnabled
        onTriggered: bar.giftCdRequested()
    }
    // Az általános filmkészítő belépő mellé a #4331 visszahozza az
    // eredeti eMenuCreateMovie::ID_FACES kijelöléses parancsát.
    PicasaMenu {
        objectName: "menuCreateMovieMenu"
        title: qsTr("&Movie")
        // #922: az ALMENÜ is kapuz — a benne lévő tétel hiába él, ha a
        // szülő szürke. A People-filmnek nincs kijelölési előfeltétele
        // (#4633), a többi filmút továbbra is a tálcáról dolgozik (#455).
        enabled: bar.createActionsEnabled || bar.hasPeopleAlbumMovieSources
        MenuItem {
            objectName: "menuCreateMovie"
            text: qsTr("New Movie...")
            enabled: bar.createActionsEnabled
            onTriggered: bar.movieRequested()
        }
        MenuItem {
            objectName: "menuCreateMovieFromFaces"
            text: qsTr("From Faces in Selection...")
            enabled: bar.libraryPhotoActionsEnabled
            onTriggered: bar.faceMovieRequested()
        }
        MenuItem {
            objectName: "menuCreateMovieFromPeopleAlbums"
            text: qsTr("From People Albums...")
            enabled: bar.hasPeopleAlbumMovieSources
            onTriggered: bar.peopleAlbumsMovieRequested()
        }
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    // hiányzott (#324 audit)
    PicasaMenuItem { text: qsTr("Publish to &Blogger..."); placeholder: false; retired: true }  // #638
}
