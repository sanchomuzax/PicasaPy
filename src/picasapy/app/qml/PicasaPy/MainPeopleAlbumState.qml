import QtQml

// A személyalbum javaslat- és képműveleteinek állapota.
QtObject {
    id: root

    required property var hostWindow
    required property var hostController
    required property var hostFaceScanController
    required property var hostRemovePeopleFacesDialog
    required property var hostCreateDialogs

    // A személyalbum-fejléc kötései ezt a revíziót figyelik. A nézetváltás
    // és a saját műveletek után újraértékelődnek a származtatott értékek.
    property int _javaslatRevizio: 0
    readonly property string personAlbumName:
        hostController && hostController.currentPersonName
            ? hostController.currentPersonName : ""
    readonly property string personAlbumAvatarUrl: {
        if (!hostController || root.personAlbumName === "") return ""
        var people = hostController.people || []
        for (var i = 0; i < people.length; ++i) {
            if (String(people[i].name).toLocaleLowerCase()
                    === root.personAlbumName.toLocaleLowerCase())
                return String(people[i].headerThumbUrl
                              || people[i].thumbUrl || "")
        }
        return ""
    }
    readonly property bool personAlbumCanRemoveSelection: {
        if (!hostController || root.personAlbumName === "") return false
        var rows = hostWindow.selectedRows()
        if (rows.length === 0) return false
        if (root.personSelectedSuggestionIds.length > 0) return true
        var people = hostController.peopleOfRows(rows)
        for (var i = 0; i < people.length; ++i) {
            if (String(people[i].name).toLocaleLowerCase()
                    === root.personAlbumName.toLocaleLowerCase())
                return true
        }
        return false
    }
    readonly property bool personAlbumCanSetThumbnail: {
        if (!hostController || root.personAlbumName === "") return false
        var rows = hostWindow.selectedRows()
        for (var i = 0; i < rows.length; ++i) {
            var photoId = Number(hostController.photos.idAt(Number(rows[i])))
            if (hostController.canSetPersonThumbnail(
                    photoId, root.personAlbumName)) return true
        }
        return false
    }

    function removePersonAlbumSelection() {
        if (!hostController || !root.personAlbumCanRemoveSelection) return
        if (root.personSelectedSuggestionIds.length > 0) {
            root.removePersonSuggestions()
            return
        }
        hostRemovePeopleFacesDialog.ensure().openFor(
            hostWindow.selectedRows(), root.personAlbumName)
    }

    function setPersonAlbumThumbnailFromSelection() {
        if (!hostController || !root.personAlbumCanSetThumbnail) return
        var rows = hostWindow.selectedRows()
        for (var i = 0; i < rows.length; ++i) {
            var photoId = Number(hostController.photos.idAt(Number(rows[i])))
            if (hostController.setPersonThumbnail(
                    photoId, root.personAlbumName)) {
                hostWindow.peopleFaceRevision++
                return
            }
        }
    }

    // A People-filmet a személyalbum-modell nem üres albumai adják, annak
    // tárolt sorrendjében; nem csak az éppen nyitott album sorai.
    function openPersonAlbumMovie() {
        if (!hostController || root.personAlbumName === "") return
        root.openPeopleAlbumsMovie()
    }

    // ID_FACESRANDOM ugyanazt a forráslistát használja, de a Létrehozás
    // menüből személyalbum nézet nélkül is indul.
    function openPeopleAlbumsMovie() {
        if (!hostController) return
        var forrasok = hostController.personMovieSourceUrls()
        if (forrasok.length === 0) return
        hostCreateDialogs.ensure().openMovieForSources(forrasok)
    }

    readonly property int personSuggestionCount: {
        root._javaslatRevizio
        if (!hostFaceScanController || root.personAlbumName === "")
            return 0
        return hostFaceScanController.personSuggestionCount(
            root.personAlbumName)
    }

    // A jelenlegi személy függő javaslatait tartalmazó fotósorokat jelöli ki.
    function selectPersonSuggestions() {
        if (!hostFaceScanController || root.personAlbumName === ""
                || !hostController || !hostController.photos)
            return
        var utak = hostFaceScanController.personSuggestionPaths(
            root.personAlbumName)
        var javaslatSorok = ({})
        for (var j = 0; j < utak.length; ++j) {
            // A vezérlő natív Windows-elválasztót is adhat; a modell
            // rowOfPath API-ja végzi az útvonal platformfüggő egyeztetését.
            var sor = Number(hostController.photos.rowOfPath(String(utak[j])))
            if (sor >= 0)
                javaslatSorok[sor] = true
        }
        var sorok = []
        var darab = Number(hostController.photos.rowCount())
        for (var i = 0; i < darab; ++i) {
            if (javaslatSorok[i])
                sorok.push(i)
        }
        hostWindow.selectedIndexes = sorok
        hostWindow.selectedIndex = sorok.length > 0 ? sorok[0] : -1
    }

    // A kijelölt fotókon ülő, e személyhez tartozó függő javaslatok arcai.
    readonly property var personSelectedSuggestionIds: {
        root._javaslatRevizio
        var sorok = hostWindow.selectedIndexes
        if (!hostFaceScanController || root.personAlbumName === ""
                || !sorok || sorok.length === 0)
            return []
        var utak = []
        for (var k = 0; k < sorok.length; ++k) {
            var ut = hostController.photos.filePathAt(Number(sorok[k]))
            if (ut !== "")
                utak.push(ut)
        }
        return hostFaceScanController.personSuggestionIdsForPaths(
            root.personAlbumName, utak)
    }

    function confirmPersonSuggestions() {
        if (!hostFaceScanController || root.personAlbumName === "")
            return
        var arcok = root.personSelectedSuggestionIds
        if (arcok.length > 0)
            hostFaceScanController.confirmPersonSuggestions(
                root.personAlbumName, arcok)
        else
            hostFaceScanController.confirmPersonSuggestions(
                root.personAlbumName)
        root._javaslatFrissult()
    }

    function removePersonSuggestions() {
        if (!hostFaceScanController || root.personAlbumName === "")
            return
        var arcok = root.personSelectedSuggestionIds
        if (arcok.length > 0)
            hostFaceScanController.removePersonSuggestions(
                root.personAlbumName, arcok)
        else
            hostFaceScanController.removePersonSuggestions(
                root.personAlbumName)
        root._javaslatFrissult()
    }

    // A vezérlő tartja a javaslatszűrő állását; a revízió a kötés horgonya.
    readonly property bool personSuggestionsOnly: {
        root._javaslatRevizio
        return hostController && hostController.personSuggestionsOnly !== undefined
            ? hostController.personSuggestionsOnly : false
    }
    function setPersonSuggestionsOnly(csak) {
        if (!hostController || !hostController.setPersonSuggestionsOnly)
            return
        hostController.setPersonSuggestionsOnly(csak)
        root._javaslatRevizio += 1
    }

    // Az arc ↔ teljes kép nagyításváltó állását a vezérlő tárolja.
    readonly property bool personFaceZoom: {
        root._javaslatRevizio
        return hostController && hostController.personFaceZoom !== undefined
            ? hostController.personFaceZoom : false
    }
    function setPersonFaceZoom(arc) {
        if (!hostController || !hostController.setPersonFaceZoom)
            return
        hostController.setPersonFaceZoom(arc)
        root._javaslatRevizio += 1
    }

    // A javaslatlépcsőt tízzel lazítja, a beállítást nem írja vissza.
    function findMoreSuggestions() {
        if (!hostFaceScanController)
            return
        hostFaceScanController.moreSuggestions()
        root._javaslatFrissult()
    }

    // A jóváhagyott arcok az album újratöltése után kerülnek a személy képei közé.
    function _javaslatFrissult() {
        if (hostController && root.personAlbumName !== "") {
            if (hostController.refreshPersonAlbum)
                hostController.refreshPersonAlbum()
            else
                hostController.showPerson(root.personAlbumName)
        }
        root._javaslatRevizio += 1
    }
}
