import QtQml

// A kereső-javaslatból végzett navigáció a főablak parancs-QML-jétől külön él.
QtObject {
    required property var hostWindow
    required property var hostController
    required property var toolbar
    required property var suggestionsTimer

    function choose(kind, name, param) {
        if (kind !== "folder" && kind !== "word" && kind !== "album")
            return
        if (kind === "album") {
            hostWindow.clearSelection()
            hostWindow.unnamedFacesOpen = false
        }
        toolbar.keresesSzoveggel(name + " ")
        suggestionsTimer.stop()
        hostController.search(name + " ")
        if (kind === "folder")
            hostController.selectFolderKeepSearch(param)
        else if (kind === "album")
            hostController.selectAlbumKeepSearch(param)
    }
}
