pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy 1.0

Dialog {
    id: manager
    objectName: "peopleManagerDialog"
    parent: Overlay.overlay
    anchors.centerIn: parent
    title: qsTr("People")
    modal: true
    width: 632
    height: 372
    padding: 10

    property var controller: null
    property var entries: []
    property var originalEntries: []
    property string selectedKey: ""
    property var selectedContactIds: []
    property var selectedLocalContactIds: []
    property string selectedThumbUrl: ""
    property int selectedPhotoCount: 0
    property bool settingFields: false
    property int nextDraftNumber: 0
    property int pendingFaceId: -1
    property string pendingFaceName: ""
    property string pendingPersonName: ""
    property var faceScanController: null
    readonly property int personRowHeight: Math.max(16, Theme.fontSize + 3)
    readonly property var filteredEntries: {
        var needle = searchField.text.trim().toLocaleLowerCase()
        return manager.entries.filter(function(entry) {
            return entry.name.toLocaleLowerCase().indexOf(needle) >= 0
        })
    }

    function syncSelectionToFilteredEntries() {
        var selectedIndex = manager.filteredEntries.findIndex(function(entry) {
            return entry.key === manager.selectedKey
        })
        if (selectedIndex < 0) {
            manager.selectedKey = ""
            manager.selectedContactIds = []
            manager.selectedLocalContactIds = []
            manager.selectedThumbUrl = ""
            manager.selectedPhotoCount = 0
            manager.settingFields = true
            nameField.text = ""
            emailField.text = ""
            manager.settingFields = false
            if (contactList.currentIndex !== -1)
                contactList.currentIndex = -1
            return
        }
        if (contactList.currentIndex !== selectedIndex)
            contactList.currentIndex = selectedIndex
    }

    onFilteredEntriesChanged: manager.syncSelectionToFilteredEntries()

    function _copy(entry) {
        return {
            key: entry.key,
            name: entry.name,
            email: entry.email,
            thumbUrl: entry.thumbUrl || "",
            contactIds: entry.contactIds.slice(),
            localContactIds: entry.localContactIds.slice(),
            photoCount: entry.photoCount,
            isNew: entry.isNew
        }
    }

    function beginSession() {
        var initialSearch = manager.pendingFaceId >= 0
            ? manager.pendingFaceName : manager.pendingPersonName
        var loaded = controller ? controller.peopleManagerContacts() : []
        var copied = []
        for (var i = 0; i < loaded.length; ++i) {
            copied.push({
                key: "contact:" + loaded[i].name,
                name: loaded[i].name,
                email: loaded[i].email,
                thumbUrl: loaded[i].thumbUrl || "",
                contactIds: loaded[i].contactIds,
                localContactIds: loaded[i].localContactIds,
                photoCount: loaded[i].photoCount,
                isNew: false
            })
        }
        manager.settingFields = true
        manager.entries = copied
        manager.originalEntries = copied.map(manager._copy)
        manager.selectedKey = ""
        manager.selectedLocalContactIds = []
        manager.selectedThumbUrl = ""
        manager.selectedPhotoCount = 0
        searchField.text = initialSearch
        nameField.text = ""
        emailField.text = ""
        manager.settingFields = false
        contactList.currentIndex = -1
        if (initialSearch) {
            var target = copied.find(function(entry) {
                return entry.name.toLocaleLowerCase()
                    === initialSearch.toLocaleLowerCase()
            })
            if (target) {
                manager.selectContact(target)
                if (manager.pendingFaceId >= 0) {
                    searchField.forceActiveFocus()
                    searchField.selectAll()
                }
            }
        } else if (copied.length > 0) {
            manager.selectContact(copied[0])
        }
        manager.pendingPersonName = ""
    }

    function openForPerson(name) {
        manager.pendingPersonName = String(name || "").trim()
        manager.open()
    }

    function openForFace(name, faceId) {
        manager.pendingFaceName = String(name || "").trim()
        manager.pendingFaceId = Number(faceId)
        manager.open()
    }

    function selectContact(entry) {
        manager.selectedKey = entry.key
        manager.selectedContactIds = entry.contactIds || []
        manager.selectedLocalContactIds = entry.localContactIds || []
        manager.selectedThumbUrl = entry.thumbUrl || ""
        manager.selectedPhotoCount = entry.photoCount || 0
        manager.settingFields = true
        nameField.text = entry.name
        emailField.text = entry.email
        manager.settingFields = false
        var visibleIndex = manager.filteredEntries.findIndex(function(item) {
            return item.key === entry.key
        })
        if (visibleIndex >= 0 && contactList.currentIndex !== visibleIndex)
            contactList.currentIndex = visibleIndex
    }

    function _updateSelected(field, value) {
        if (manager.settingFields || manager.selectedKey === "")
            return
        var selectedKey = manager.selectedKey
        manager.entries = manager.entries.map(function(entry) {
            if (entry.key !== manager.selectedKey)
                return entry
            var copy = manager._copy(entry)
            copy[field] = value
            return copy
        })
        var selectedIndex = manager.filteredEntries.findIndex(function(entry) {
            return entry.key === selectedKey
        })
        if (selectedIndex >= 0)
            contactList.currentIndex = selectedIndex
    }

    function addPerson() {
        var draftName = searchField.text.trim()
        manager.nextDraftNumber += 1
        var entry = {
            key: "draft:" + manager.nextDraftNumber,
            name: draftName,
            email: "",
            thumbUrl: "",
            contactIds: [],
            localContactIds: [],
            photoCount: 0,
            isNew: true
        }
        manager.entries = manager.entries.concat([entry])
        manager.selectedKey = entry.key
        manager.selectedLocalContactIds = []
        manager.selectedThumbUrl = ""
        manager.selectedPhotoCount = 0
        manager.settingFields = true
        nameField.text = draftName
        emailField.text = ""
        manager.settingFields = false
        contactList.currentIndex = manager.filteredEntries.length - 1
        nameField.forceActiveFocus()
    }

    function deleteSelected() {
        if (manager.selectedKey === "")
            return
        manager.entries = manager.entries.filter(function(entry) {
            return entry.key !== manager.selectedKey
        })
        manager.selectedKey = ""
        manager.selectedLocalContactIds = []
        manager.selectedThumbUrl = ""
        contactList.currentIndex = -1
        if (manager.entries.length === 0) {
            manager.settingFields = true
            nameField.text = ""
            emailField.text = ""
            manager.settingFields = false
            manager.selectedPhotoCount = 0
        } else {
            manager.selectContact(manager.entries[0])
        }
    }

    function revertSelected() {
        if (manager.selectedKey === "")
            return
        var original = manager.originalEntries.find(function(entry) {
            return entry.key === manager.selectedKey
        })
        if (original) {
            manager.entries = manager.entries.map(function(entry) {
                return entry.key === manager.selectedKey
                    ? manager._copy(original) : entry
            })
            manager.selectContact(original)
        } else {
            manager.entries = manager.entries.map(function(entry) {
                if (entry.key !== manager.selectedKey)
                    return entry
                var copy = manager._copy(entry)
                copy.name = ""
                copy.email = ""
                return copy
            })
            manager.selectContact(manager.entries.find(function(entry) {
                return entry.key === manager.selectedKey
            }))
        }
    }

    function selectedEntry() {
        return manager.entries.find(function(entry) {
            return entry.key === manager.selectedKey
        }) || null
    }

    function canCommit() {
        for (var i = 0; i < manager.entries.length; ++i) {
            var entry = manager.entries[i]
            if (!entry.name.trim() || /[;\r\n]/.test(entry.name)
                || /[;\r\n]/.test(entry.email))
                return false
        }
        if (manager.pendingFaceId >= 0) {
            var selected = manager.selectedEntry()
            if (!selected || !selected.name.trim())
                return false
        }
        return true
    }

    function commitChanges() {
        var personToAssign = null
        if (manager.pendingFaceId >= 0) {
            personToAssign = manager.selectedEntry()
            if (!personToAssign || !personToAssign.name.trim())
                return
        }
        var changes = []
        for (var i = 0; i < manager.originalEntries.length; ++i) {
            var original = manager.originalEntries[i]
            var updated = manager.entries.find(function(entry) {
                return entry.key === original.key
            })
            if (!updated) {
                changes.push({action: "delete", oldName: original.name})
            } else if (updated.name.trim() !== original.name
                       || updated.email !== original.email) {
                changes.push({
                    action: "update",
                    oldName: original.name,
                    name: updated.name.trim(),
                    email: updated.email.trim()
                })
            }
        }
        for (var j = 0; j < manager.entries.length; ++j) {
            var created = manager.entries[j]
            if (created.isNew && created.name.trim()) {
                changes.push({
                    action: "create",
                    name: created.name.trim(),
                    email: created.email.trim()
                })
            }
        }
        if (!controller || !controller.savePeopleManagerChanges(changes))
            return
        if (manager.pendingFaceId >= 0) {
            var personName = personToAssign.name.trim()
            if (!manager.faceScanController
                    || !manager.faceScanController.assignNameToFaces(
                        [manager.pendingFaceId], personName))
                return
            if (controller && controller.refreshCollections)
                controller.refreshCollections()
            manager.pendingFaceId = -1
            manager.pendingFaceName = ""
        }
        manager.close()
    }

    onOpened: beginSession()
    onClosed: {
        manager.pendingFaceId = -1
        manager.pendingFaceName = ""
        manager.pendingPersonName = ""
    }

    contentItem: ColumnLayout {
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12

            ColumnLayout {
                Layout.preferredWidth: 310
                Layout.fillHeight: true
                spacing: 5

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: qsTr("Search:") }
                    TextField {
                        id: searchField
                        objectName: "peopleManagerSearchField"
                        Layout.fillWidth: true
                        font.pixelSize: Theme.fontSize
                        TextFieldContextArea {}
                    }
                }

                ListView {
                    id: contactList
                    objectName: "peopleManagerContactList"
                    Layout.fillWidth: true
                    Layout.preferredHeight: manager.personRowHeight * 17
                    Layout.fillHeight: true
                    clip: true
                    model: manager.filteredEntries
                    delegate: ItemDelegate {
                        required property var modelData
                        required property int index
                        objectName: "peopleManagerContact_" + modelData.name
                        width: ListView.view.width
                        height: ListView.view.height / 17
                        text: modelData.name
                        highlighted: ListView.isCurrentItem
                        contentItem: RowLayout {
                            spacing: 6
                            Image {
                                Layout.preferredWidth: visible ? 24 : 0
                                Layout.preferredHeight: 24
                                source: modelData.thumbUrl || ""
                                visible: source !== ""
                                fillMode: Image.PreserveAspectCrop
                                smooth: true
                                mipmap: true
                                asynchronous: true
                            }
                            Label {
                                Layout.fillWidth: true
                                text: modelData.name
                                elide: Text.ElideRight
                            }
                        }
                        onClicked: {
                            ListView.view.currentIndex = index
                            manager.selectContact(modelData)
                        }
                    }
                }

                RowLayout {
                    Layout.alignment: Qt.AlignRight
                    Button {
                        objectName: "peopleManagerDeleteButton"
                        text: qsTr("Delete Person")
                        enabled: manager.selectedKey !== ""
                        onClicked: manager.deleteSelected()
                    }
                    Button {
                        objectName: "peopleManagerNewButton"
                        text: qsTr("New Person")
                        onClicked: manager.addPerson()
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 5

                Item { Layout.fillHeight: true }

                RowLayout {
                    objectName: "peopleManagerPhotoStatus"
                    Layout.fillWidth: true
                    visible: manager.selectedKey !== ""
                    Item { Layout.fillWidth: true }
                    Image {
                        objectName: "peopleManagerPhotoCountIcon"
                        Layout.preferredWidth: visible ? 36 : 0
                        Layout.preferredHeight: 36
                        visible: manager.pendingFaceId >= 0
                        source: manager.selectedThumbUrl !== ""
                            ? manager.selectedThumbUrl
                            : Qt.resolvedUrl("icons/person-silhouette.svg")
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                    }
                    Label {
                        objectName: "peopleManagerPhotoCount"
                        text: manager.pendingFaceId >= 0
                            ? (manager.selectedPhotoCount === 1
                               ? qsTr("%d Photo in Picasa")
                               : qsTr("%d Photos in Picasa"))
                                .replace("%d", String(manager.selectedPhotoCount))
                            : String(manager.selectedPhotoCount)
                    }
                    Item { Layout.fillWidth: true }
                    Label {
                        text: qsTr("Contact ID:")
                        visible: manager.pendingFaceId < 0
                    }
                    Label {
                        objectName: "peopleManagerContactId"
                        Layout.maximumWidth: 280
                        visible: manager.pendingFaceId < 0
                        wrapMode: Text.Wrap
                        text: manager.selectedContactIds.join(", ")
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: qsTr("Name:") }
                    TextField {
                        id: nameField
                        objectName: "peopleManagerNameField"
                        Layout.fillWidth: true
                        enabled: manager.selectedKey !== ""
                        font.pixelSize: Theme.fontSize
                        onTextEdited: manager._updateSelected("name", text)
                        TextFieldContextArea {}
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: qsTr("Email(s):") }
                    TextArea {
                        id: emailField
                        objectName: "peopleManagerEmailField"
                        Layout.fillWidth: true
                        Layout.preferredHeight: manager.personRowHeight * 3
                        enabled: manager.selectedKey !== ""
                            && manager.selectedLocalContactIds.length > 0
                        wrapMode: TextEdit.Wrap
                        font.pixelSize: Theme.fontSize
                        onTextChanged: manager._updateSelected("email", text)
                        TextFieldContextArea {}
                    }
                }

                CheckBox {
                    objectName: "peopleManagerSyncCheck"
                    text: qsTr("Sync Face Tags with Web Albums")
                    enabled: false
                }

                RowLayout {
                    Layout.fillWidth: true
                    Item { Layout.fillWidth: true }
                    Button {
                        objectName: "peopleManagerRevertButton"
                        text: qsTr("Revert")
                        enabled: manager.selectedKey !== ""
                        onClicked: manager.revertSelected()
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Theme.buttonBorder
        }

        RowLayout {
            Layout.fillWidth: true
            Button {
                objectName: "peopleManagerOnlineButton"
                text: qsTr("Manage Online Contacts")
                enabled: false
            }
            Button {
                objectName: "peopleManagerRefreshButton"
                text: qsTr("Refresh Contacts")
                enabled: false
            }
            Item { Layout.fillWidth: true }
            Button {
                objectName: "peopleManagerOkButton"
                text: manager.pendingFaceId >= 0
                      && manager.selectedEntry()
                      && !manager.selectedEntry().isNew
                      ? qsTr("Choose") : qsTr("OK")
                enabled: manager.canCommit()
                onClicked: manager.commitChanges()
            }
            Button {
                objectName: "peopleManagerCancelButton"
                text: qsTr("Cancel")
                onClicked: manager.close()
            }
        }
    }
}
