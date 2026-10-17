"""Az utolsó maradék vezérlők VALÓDI bemenettel (#5150, utolsó rész, R. fájl).

Lefedve (valódi egérrel vagy billentyűvel, a hatást állapoton mérve):
- Mentés-panel (`BackupHost`): `backupSetName`, `backupSetTarget` (az új készlet
  űrlapja), `backupRestoreSource`, `backupRestoreTarget` (a visszaállítás űrlapja).
- Ajándék-CD és mentés-kimenet (`PublishPanel`): `publishCdName` (a név a
  lemezírás kérésébe kerül), `publishBackupOutputMode` (a CD/DVD-választó a
  mentés indításán át).
- Gyűjtemény-menü (`FolderPane`): `collectionMenuRename`, `collectionMenuRemove`,
  és az átnevező párbeszéd mezője: `newCollectionNameField`.
- Címkeszerkesztő (`KeywordsDialog`): `keywordAddField` (Enterrel a címke bekerül).
- Film-szövegdialógus (`MovieTitleDialog`): `titledialog/captiontext`.
- Rejtett-jelszó párbeszéd (`HiddenPasswordDialog`): `hiddenPasswordField`,
  `hiddenPasswordVerify` (egyezés: elfogadás; eltérés: nem fogadja el).
- E-mail címzett környezeti menü: `textMenuAutoComplete` (a valódi
  EmailController beállítása a lemezre íródik).

Nincs itt, mert a felületen nincs elérhető kattintás (ld. a jelentést):
`unnamedNameField`, `addNameButton`, `ignoreFacesButton`,
`moreSuggestionsButton`, `optionsFaceUploadContactPhotosCheck`,
`publishUploadAllSize`, `publishUploadAllAccess`, `unnamedWelcomeLearnMoreButton`.

A felugró menük és párbeszédek a kattintás célját a saját ablakukban is
kaphatják; a `kattints` (5150-es segéd) ezt az ablakot keresi meg. Az e-mail-teszt
az `EmailController`-t valódi QSettings-szel használja, a `tmp_path` alatt.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QSettings, Qt, Slot
from PySide6.QtTest import QTest

import picasapy.app
from picasapy.app.backup_controller import BackupController
from picasapy.app.email_controller import EmailController
from picasapy.index import open_index
from support.backup_host_harness import epits_ablakot
from tests.app.qml_functional._racs_maradek_5150_helpers import keres
from tests.app.qml_functional._utolso_maradek_5150_helpers import (
    gepel,
    keszit_ablakot,
    keszit_motort,
    kattint,
    kattint_elemre,
    kijelol_mindent,
    lista,
    szoveges_elem,
    varj,
)
from tests.app.qml_functional.test_folder_pane_custom_collections_476 import (  # noqa: F401
    _StubController,
    shown_view,  # noqa: F401
)

_QML = Path(picasapy.app.__file__).parent / "qml"

_PUBLISH_QML = """
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0

ApplicationWindow {
    id: w
    width: 1024
    height: 212
    visible: true
    property var kerult: []
    PublishPanel {
        objectName: "publishPanel"
        elemekSzama: 3
        onLemezreIrasKert: function(meret, nev) {
            w.kerult = w.kerult.concat([nev])
        }
    }
}
"""

_MENTES_QML = """
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0

ApplicationWindow {
    id: w
    width: 1024
    height: 212
    visible: true
    property var kerult: []
    PublishPanel {
        objectName: "publishPanel"
        uzemmod: "backup"
        mentesKeszletek: [{ nev: "Mentes", cel: "/tmp/mentes", tipus: "cddvd" }]
        mentesKivalasztottIndex: 0
        mentesPipaltMappak: ["/tmp/mentes/a"]
        onMentesFuttatasKert: function(media) {
            w.kerult = w.kerult.concat([media])
        }
    }
}
"""

_KEYWORDS_QML = """
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0

ApplicationWindow {
    id: w
    width: 700
    height: 500
    visible: true
    property var hozzaadott: []
    KeywordsDialog {
        objectName: "keywordsDialog"
        controller: ({
            photos: { revision: 0 },
            selectionReadOnly: function(sorok) { return false },
            keywordsOfRows: function(sorok) { return [] },
            photoDateAt: function(sor) { return "" },
            addKeywordToRows: function(sorok, szo) {
                w.hozzaadott = w.hozzaadott.concat([szo])
            },
            removeKeywordFromRows: function(sorok, szo) { }
        })
        Component.onCompleted: openFor([0], 0, {})
    }
}
"""

_FILM_QML = """
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0

ApplicationWindow {
    id: w
    width: 640
    height: 480
    visible: true
    property string kepfelirat: dialogus.currentSlide().text
    MovieTitleDialog {
        id: dialogus
        Component.onCompleted: openForCaption("", {})
    }
}
"""

_JELSZO_QML = """
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0

ApplicationWindow {
    width: 700
    height: 500
    visible: true
    HiddenPasswordDialog {
        objectName: "hiddenPasswordDialog"
        Component.onCompleted: openSet()
    }
}
"""

_EMAIL_QML = """
import QtQuick
import QtQuick.Controls
import QtQuick.Window
import PicasaPy 1.0

Window {
    width: 360
    height: 360
    visible: true
    TextField {
        objectName: "recipientField"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        TextFieldContextArea {
            objectName: "recipientContextArea"
            autoCompleteSupported: true
            autoCompleteController: emailController
        }
    }
}
"""


def _ablak_lista(ablak, nev: str) -> list:
    return lista(ablak.property(nev))


@pytest.fixture
def mentes_host(qt_app, tmp_path, monkeypatch):
    """A mentés-panel valódi ablakban, üres készlet-listával.

    A `_kepek_mappaja` a tmp-re mutat, így a valódi képmappa nem érintett."""
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    db = tmp_path / "index.db"
    with open_index(db):
        pass
    vezerlo = BackupController(db, ())
    view, host = epits_ablakot(_QML, {"backupController": vezerlo})
    QMetaObject.invokeMethod(host, "nyisd")
    qt_app.processEvents()
    return view, host


@pytest.fixture
def motor(qt_app):
    return keszit_motort(qt_app)


class _GyujtemenyVezerlo(_StubController):
    """A 476-os stub kiegészítve a névellenőrzéssel.

    Az átnevező párbeszéd megnyitáskor a `validateCollectionName`-et hívja; az
    üres válasz azt jelenti, hogy a név érvényes."""

    @Slot(str, str, result=str)
    def validateCollectionName(self, uj_nev, regi_nev):
        return ""


@pytest.fixture
def controller(qt_app):
    return _GyujtemenyVezerlo()


def _ujkeszlet_urlap(view, host, qt_app) -> None:
    """Az „Új készlet" gombbal nyitja az űrlapot (valódi kattintás)."""
    kattint(view, qt_app, "publishNewBackupSet")
    assert varj(qt_app, lambda: host.property("szerkesztes") is True)


def test_a_keszlet_neve_valodi_billentyuzetrol_mentodik(mentes_host, qt_app):
    view, host = mentes_host
    _ujkeszlet_urlap(view, host, qt_app)
    kattint(view, qt_app, "backupSetName")
    kijelol_mindent(view, qt_app)
    gepel(view, qt_app, "Nyaralas")
    assert host.property("urlapNev") == "Nyaralas"


def test_a_cel_mappa_mezo_szerkesztheto_es_a_hostba_irodik(mentes_host, qt_app):
    view, host = mentes_host
    _ujkeszlet_urlap(view, host, qt_app)
    assert keres(view, "backupSetTarget").property("enabled") is True
    kattint(view, qt_app, "backupSetTarget")
    kijelol_mindent(view, qt_app)
    gepel(view, qt_app, "celmappa")
    assert host.property("urlapCel") == "celmappa"


def test_a_visszaallitas_forras_mezo_valodi_gepeleessel_irodik(mentes_host, qt_app):
    view, host = mentes_host
    kattint(view, qt_app, "publishBackupRestore")
    assert varj(qt_app, lambda: host.property("visszaallitasNyitva") is True)
    kattint(view, qt_app, "backupRestoreSource")
    kijelol_mindent(view, qt_app)
    gepel(view, qt_app, "forras")
    assert host.property("visszaallitasForras") == "forras"


def test_a_visszaallitas_cel_mezo_valodi_gepeleessel_irodik(mentes_host, qt_app):
    view, host = mentes_host
    kattint(view, qt_app, "publishBackupRestore")
    assert varj(qt_app, lambda: host.property("visszaallitasNyitva") is True)
    kattint(view, qt_app, "backupRestoreTarget")
    kijelol_mindent(view, qt_app)
    gepel(view, qt_app, "cel")
    assert host.property("visszaallitasCel") == "cel"


def test_a_cd_nev_valodi_gepeleessel_a_lemezirasba_kerul(motor, qt_app):
    ablak = keszit_ablakot(qt_app, motor, _PUBLISH_QML)
    kattint(ablak, qt_app, "publishCdName")
    kijelol_mindent(ablak, qt_app)
    gepel(ablak, qt_app, "Csalad")
    kattint(ablak, qt_app, "publishPresentCdGo")
    assert varj(qt_app, lambda: len(_ablak_lista(ablak, "kerult")) == 1)
    assert _ablak_lista(ablak, "kerult") == ["Csalad"]


def test_a_kimeneti_mod_valodi_valasztassal_dvd_lesz_a_mentesbol(motor, qt_app):
    ablak = keszit_ablakot(qt_app, motor, _MENTES_QML)
    kattint(ablak, qt_app, "publishBackupOutputMode")
    kattint_elemre(ablak, qt_app, szoveges_elem(ablak, "To DVD image (ISO)"))
    assert keres(ablak, "publishBackupOutputMode").property("currentIndex") == 1
    kattint(ablak, qt_app, "publishBackupGo")
    assert varj(qt_app, lambda: len(_ablak_lista(ablak, "kerult")) == 1)
    assert _ablak_lista(ablak, "kerult") == ["dvd"]


def test_a_gyujtemeny_atnevezese_valodi_menuvel_es_mezovel_tortenik(
    shown_view, controller, qt_app  # noqa: F811
):
    controller.set_collections([{"name": "Nyaralások", "folders": []}])
    qt_app.processEvents()
    kattint(shown_view, qt_app, "customCollection_Nyaralások", Qt.MouseButton.RightButton)
    kattint(shown_view, qt_app, "collectionMenuRename")
    kattint(shown_view, qt_app, "newCollectionNameField")
    kijelol_mindent(shown_view, qt_app)
    gepel(shown_view, qt_app, "Nyaralasok 2024")
    QTest.keyClick(shown_view, Qt.Key.Key_Return)
    assert varj(
        qt_app, lambda: controller.renamed == [("Nyaralások", "Nyaralasok 2024")]
    )


def test_a_gyujtemeny_eltavolitasa_csak_megerositessel_torol(
    shown_view, controller, qt_app  # noqa: F811
):
    controller.set_collections([{"name": "Nyaralások", "folders": []}])
    qt_app.processEvents()
    kattint(shown_view, qt_app, "customCollection_Nyaralások", Qt.MouseButton.RightButton)
    kattint(shown_view, qt_app, "collectionMenuRemove")
    assert controller.deleted == [], "megerősítés nélkül törölt"
    kattint(shown_view, qt_app, "removeCollectionConfirmYesButton")
    assert varj(qt_app, lambda: controller.deleted == ["Nyaralások"])


def test_a_cimke_mezo_enterrel_hozzaadja_a_cimkét(motor, qt_app):
    ablak = keszit_ablakot(qt_app, motor, _KEYWORDS_QML)
    kattint(ablak, qt_app, "keywordAddField")
    gepel(ablak, qt_app, "nyaralas")
    QTest.keyClick(ablak, Qt.Key.Key_Return)
    assert varj(qt_app, lambda: _ablak_lista(ablak, "hozzaadott") == ["nyaralas"])


def test_a_film_felirat_mezo_valodi_gepeleessel_a_diakepbe_kerul(motor, qt_app):
    ablak = keszit_ablakot(qt_app, motor, _FILM_QML)
    kattint(ablak, qt_app, "titledialog/captiontext")
    kijelol_mindent(ablak, qt_app)
    gepel(ablak, qt_app, "Nyaralas")
    assert varj(qt_app, lambda: ablak.property("kepfelirat") == "Nyaralas")


def test_a_jelszo_egyezo_mezokkel_enterrel_elfogadodik(motor, qt_app):
    ablak = keszit_ablakot(qt_app, motor, _JELSZO_QML)
    parbeszed = keres(ablak, "hiddenPasswordDialog")
    kattint(ablak, qt_app, "hiddenPasswordField")
    gepel(ablak, qt_app, "titok")
    kattint(ablak, qt_app, "hiddenPasswordVerify")
    gepel(ablak, qt_app, "titok")
    QTest.keyClick(ablak, Qt.Key.Key_Return)
    assert varj(qt_app, lambda: parbeszed.property("opened") is False)


def test_a_jelszo_eltero_mezokkel_enterre_sem_fogadodik_el(motor, qt_app):
    ablak = keszit_ablakot(qt_app, motor, _JELSZO_QML)
    parbeszed = keres(ablak, "hiddenPasswordDialog")
    kattint(ablak, qt_app, "hiddenPasswordField")
    gepel(ablak, qt_app, "titok")
    kattint(ablak, qt_app, "hiddenPasswordVerify")
    gepel(ablak, qt_app, "masik")
    assert varj(
        qt_app,
        lambda: keres(ablak, "hiddenPasswordMismatch").property("visible") is True,
    )
    QTest.keyClick(ablak, Qt.Key.Key_Return)
    qt_app.processEvents()
    assert parbeszed.property("opened") is True, "eltérő jelszót elfogadott"


def test_az_automatikus_kiegeszites_valodi_menuvel_kikapcsolhato(
    motor, qt_app, tmp_path
):
    beallitas = QSettings(str(tmp_path / "picasapy.ini"), QSettings.Format.IniFormat)
    emailvezerlo = EmailController(photo_source=lambda: [], settings=beallitas)
    motor.rootContext().setContextProperty("emailController", emailvezerlo)
    ablak = keszit_ablakot(qt_app, motor, _EMAIL_QML)
    assert emailvezerlo.emailAutocompleteEnabled is True
    kattint(ablak, qt_app, "recipientContextArea", Qt.MouseButton.RightButton)
    kattint(ablak, qt_app, "textMenuAutoComplete")
    assert varj(qt_app, lambda: emailvezerlo.emailAutocompleteEnabled is False)
    beallitas.sync()
    assert beallitas.value("mail/EmailAutocomplete") is False
