import QtQuick

// #7075: a könyvtári rács billentyűi a keresés felé. Az `Esc` a rácson
// kilép a keresésből (`0x005c42f8`-`0x005c4342`), a módosító nélkül gépelt
// `0x21`-`0x7f` karakter a keresőmezőbe kerül (`0x005c3fe0`). A keresési
// javaslatok Esc-útja a mezőn marad; a rács Esc-je csak ezután lép ki.
// A Colab-mérésig nem mentjük és nem állítjuk vissza a keresés előtti
// kijelölést, görgetést, mappát vagy fókuszt.
QtObject {
    id: keys

    property var host: null
    property var searchField: null
    property var ownerWindow: null

    function kilep() {
        searchField.clear()
        host.searchCleared()
        host.closeSearchOptions()
    }

    //: #2163: a `Ctrl+F` (`searchcontainer/searchbutton`, `0x005e63bb`) a
    //: mezőre viszi a fókuszt és megnyitja a keresési beállításokat; aktív
    //: keresésnél (#7075) a második `Ctrl+F` kilép a keresésből.
    function fokusz() {
        if (typeof controller !== "undefined" && controller
                && controller.searchActive) {
            keys.kilep()
            return
        }
        searchField.forceActiveFocus()
        searchField.selectAll()
        host.openSearchOptions()
    }

    //: #1399: a menüből indított keresés. MÉRVE (`0x0065b7b0`, hat lépés): az
    //: eredeti a mező SZÖVEGÉT állítja, a kurzort a szöveg VÉGÉRE viszi
    //: kijelölés nélkül (`EM_SETSEL 0xFFFF,0xFFFF`), majd lefuttatja a
    //: keresést, vagyis pontosan az történik, mintha a felhasználó beírta volna.
    function beir(szoveg) {
        searchField.text = szoveg
        searchField.cursorPosition = searchField.text.length
        host.searchEdited(searchField.text)
    }

    function handle(event) {
        if (!host || !searchField)
            return false
        if (event.key === Qt.Key_Escape)
            return keys._esc(event)
        return keys._gepeles(event)
    }

    function _esc(event) {
        var suggestions = ownerWindow ? ownerWindow.searchSuggestionsBox : null
        if (suggestions && suggestions.visible) {
            suggestions.dismiss()
            event.accepted = true
            return true
        }
        var searchIsActive = typeof controller !== "undefined"
            && controller
            && (controller.searchActive || controller.filterActive)
        if (searchIsActive || searchField.text.length > 0) {
            keys.kilep()
            event.accepted = true
            return true
        }
        return false
    }

    function _gepeles(event) {
        var character = event.text
        if (event.modifiers !== Qt.NoModifier || character.length !== 1)
            return false
        var code = character.charCodeAt(0)
        if (code < 0x21 || code > 0x7f)
            return false
        searchField.forceActiveFocus()
        var start = searchField.selectionStart
        var end = searchField.selectionEnd
        if (start !== end) {
            searchField.remove(start, end)
            searchField.cursorPosition = start
        }
        searchField.insert(searchField.cursorPosition, character)
        searchField.cursorPosition = searchField.text.length
        host.searchEdited(searchField.text)
        event.accepted = true
        return true
    }
}
