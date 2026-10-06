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
    property int selectedPhotoCount: 0
    property bool settingFields: false
    property int nextDraftNumber: 0
    readonly property int personRowHeight: Math.max(16, Theme.fontSize + 3)
    readonly property var filteredEntries: {
        var needle = searchField.text.trim().toLocaleLowerCase()
        return manager.entries.filter(function(entry) {
            return entry.name.toLocaleLowerCase().indexOf(needle) >= 0
        })
    }

    function _copy(entry) {
        return {
            key: entry.key,
            name: entry.name,
            email: entry.email,
            contactIds: entry.contactIds.slice(),
            localContactIds: entry.localContactIds.slice(),
            photoCount: entry.photoCount,
            isNew: entry.isNew
        }
    }

    function beginSession() {
        var loaded = controller ? controller.peopleManagerContacts() : []
        var copied = []
        for (var i = 0; i < loaded.length; ++i) {
            copied.push({
                key: "contact:" + loaded[i].name,
                name: loaded[i].name,
                email: loaded[i].email,
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
        nameField.text = ""
        emailField.text = ""
        manager.settingFields = false
        contactList.currentIndex = -1
        if (copied.length > 0)
            manager.selectContact(copied[0])
    }

    function selectContact(entry) {
        manager.selectedKey = entry.key
        manager.selectedContactIds = entry.contactIds || []
        manager.selectedLocalContactIds = entry.localContactIds || []
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
        manager.nextDraftNumber += 1
        searchField.text = ""
        var entry = {
            key: "draft:" + manager.nextDraftNumber,
            name: "",
            email: "",
            contactIds: [],
            localContactIds: [],
            photoCount: 0,
            isNew: true
        }
        manager.entries = manager.entries.concat([entry])
        manager.selectedKey = entry.key
        manager.selectedLocalContactIds = []
        manager.settingFields = true
        nameField.text = ""
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
        contactList.currentIndex = -1
        if (manager.entries.length === 0) {
            manager.settingFields = true
            nameField.text = ""
            emailField.text = ""
            manager.settingFields = false
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

    function canCommit() {
        for (var i = 0; i < manager.entries.length; ++i) {
            var entry = manager.entries[i]
            if (!entry.name.trim() || /[;\r\n]/.test(entry.name)
                || /[;\r\n]/.test(entry.email))
                return false
        }
        return true
    }

    function commitChanges() {
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
        manager.close()
    }

    onOpened: beginSession()

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
                    Layout.fillWidth: true
                    visible: manager.selectedKey !== ""
                    Label {
                        objectName: "peopleManagerPhotoCount"
                        text: String(manager.selectedPhotoCount)
                    }
                    Item { Layout.fillWidth: true }
                    Label { text: qsTr("Contact ID:") }
                    Label {
                        objectName: "peopleManagerContactId"
                        Layout.maximumWidth: 280
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
                text: qsTr("OK")
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
