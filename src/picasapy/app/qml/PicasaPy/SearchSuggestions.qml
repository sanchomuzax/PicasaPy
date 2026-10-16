import QtQuick

// Kereső-javaslatok legördülője (#7) — 150933-as referencia: gépelés közben
// fehér panel a kereső alatt, soronként mappa-/album-ikon, a név a beírt
// résszel félkövéren kiemelve, mögötte a darabszám zárójelben.
// A Main.qml-bekötés az integrátoré: a szülő adja a query/suggestions
// értékeket, és a chosen jelzésre indítja a keresést/ugrást.
Rectangle {
    id: box

    property string query: ""
    // [{kind: "folder"|"album", name, count, param}] — a controller
    // search_suggestions() eredménye
    property var suggestions: []
    property int selectedIndex: -1
    signal chosen(string kind, string name, string param)

    visible: suggestions.length > 0
    width: 300
    height: column.height + 2
    color: Theme.contentPanel
    border.color: Theme.chromeBorder

    onQueryChanged: selectedIndex = -1
    onSuggestionsChanged: selectedIndex = -1

    // A beírt rész félkövér kiemelése (casefold-os, HTML-escape-elt).
    function highlighted(name, query) {
        function esc(s) {
            return s.replace(/&/g, "&amp;").replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
        }
        var idx = query
                ? name.toLowerCase().indexOf(query.toLowerCase().trim()) : -1
        if (idx < 0)
            return esc(name)
        var end = idx + query.trim().length
        return esc(name.slice(0, idx)) + "<b>" + esc(name.slice(idx, end))
                + "</b>" + esc(name.slice(end))
    }

    // Kiválasztás sorindex szerint (a TapHandler és a tesztek hívják).
    function choose(row) {
        var s = suggestions[row]
        if (s)
            chosen(s.kind, s.name, s.param)
    }

    function moveSelection(direction) {
        if (suggestions.length === 0)
            return
        if (selectedIndex < 0) {
            selectedIndex = direction > 0 ? 0 : suggestions.length - 1
            return
        }
        selectedIndex = Math.max(
            0, Math.min(suggestions.length - 1, selectedIndex + direction))
    }

    function chooseSelected() {
        if (selectedIndex >= 0)
            choose(selectedIndex)
    }

    function dismiss() {
        suggestions = []
        selectedIndex = -1
    }

    Column {
        id: column
        x: 1; y: 1
        width: parent.width - 2

        Repeater {
            model: box.suggestions

            Rectangle {
                objectName: "suggestionRow"
                required property var modelData
                required property int index
                readonly property color keyboardSelectionColor: Theme.thumbHover
                width: column.width
                height: 22
                color: index === box.selectedIndex || rowHover.hovered
                    ? keyboardSelectionColor : "transparent"

                FolderIcon {
                    id: rowIcon
                    visible: modelData.kind === "folder"
                    anchors.verticalCenter: parent.verticalCenter
                    x: 6
                    size: 13
                }
                Item {   // rajzolt album-ikon: kék „fotókupac"
                    visible: modelData.kind === "album"
                    anchors.verticalCenter: parent.verticalCenter
                    x: 6
                    width: 13; height: 11
                    Rectangle {
                        x: 2; y: 0; width: 10; height: 8; radius: 1
                        color: Theme.contentPanel
                        border.color: Theme.selectionBlue; border.width: 1
                    }
                    Rectangle {
                        x: 0; y: 3; width: 10; height: 8; radius: 1
                        color: Theme.selectionBlue
                        border.color: "#5f8299"; border.width: 1
                    }
                }
                Text {
                    objectName: "suggestionLabel"
                    anchors.verticalCenter: parent.verticalCenter
                    x: 24
                    width: parent.width - x - countText.width - 12
                    elide: Text.ElideRight
                    textFormat: Text.StyledText
                    text: box.highlighted(modelData.name, box.query)
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize
                }
                Text {
                    id: countText
                    objectName: "suggestionCount"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: 6
                    text: "(" + modelData.count + ")"
                    color: Theme.placeholderText
                    font.pixelSize: Theme.fontSize
                }
                HoverHandler { id: rowHover }
                TapHandler { onTapped: box.choose(index) }
            }
        }
    }
}
