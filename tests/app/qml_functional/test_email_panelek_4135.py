"""#4135 — a valódi főablakban választás, levélírás és mellékletküldés.

A vezérlőkhöz az ablak tényleges geometriájából kattintunk. A kitöltő
hátterének egy szövegmentes pontját a renderelt képen ellenőrizzük, majd az
ablakmagasságot −5/0/+5 képponttal eltérítve is végigjárjuk a folyamatot.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import (
    QObject,
    QPoint,
    QPointF,
    QSettings,
    QTranslator,
    QUrl,
    Qt,
)
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

_QML = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy"
    / "EmailChoiceDialog.qml"
)
_I18N = _QML.parents[2] / "i18n"

_EMAIL_FORRASOK = {
    'qsTr("Send pictures by email")': 1,
    'qsTr("Select Email")': 1,
    'qsTr("Select how you want to e-mail your photos.")': 1,
    'qsTr("MAIL CLIENT")': 1,
    'qsTr("Use my default email program.")': 1,
    'qsTr("Google Mail")': 1,
    'qsTr("Use my Gmail or Google account.")': 1,
    'qsTr("Don\'t have Gmail? Get a free account.")': 1,
    'qsTr("Remember this setting, don\'t display this dialog again.")': 1,
    'qsTr("The pictures will be attached to a new message in your default email program.")': 1,
    'qsTr("Help")': 2,
    'qsTr("Cancel")': 2,
    'qsTr("New message")': 1,
    'qsTr("Change User")': 2,
    'qsTr("Google account sending is not available in this version.")': 1,
    'qsTr("To:")': 1,
    'qsTr("Subject:")': 1,
    'qsTr("Remove selected image from attachment")': 1,
    'qsTr("Discard")': 2,
    'qsTr("Send")': 2,
}

_EMAIL_MAGYAR = {
    "Send pictures by email": "Képek küldése e-mailben",
    "Select Email": "Válasszon levelezőprogramot",
    "Select how you want to e-mail your photos.": (
        "Válassza ki, hogyan szeretné e-mailben elküldeni fotóit."
    ),
    "MAIL CLIENT": "LEVELEZŐPROGRAM",
    "Use my default email program.": "Az alapértelmezett levelezőprogram használata",
    "Google Mail": "Google Mail",
    "Use my Gmail or Google account.": (
        "A Gmail-fiók vagy a Google Fiók használata"
    ),
    "Don't have Gmail? Get a free account.": (
        "Nincs Gmail-fiókja? Nyisson egy fiókot ingyen."
    ),
    "Remember this setting, don't display this dialog again.": (
        "Jegyezze meg ezt a beállítást, ne jelenítse meg a párbeszédpanelt újra."
    ),
    "The pictures will be attached to a new message in your default email program.": (
        "A képek az alapértelmezett levelezőprogram új üzenetéhez csatolva nyílnak meg."
    ),
    "Help": "Súgó",
    "Cancel": "Mégse",
    "New message": "Új üzenet",
    "Change User": "Felhasználóváltás",
    "Google account sending is not available in this version.": (
        "A Google-fiókos küldés ebben a változatban nem érhető el."
    ),
    "To:": "Címzett:",
    "Subject:": "Tárgy:",
    "Remove selected image from attachment": (
        "Kijelölt elemek eltávolítása a mellékletből"
    ),
    "Discard": "Elvetés",
    "Send": "Küldés",
}

def _elem(root, nev):
    elem = root.findChild(QQuickItem, nev)
    assert elem is not None, f"hiányzó, kirajzolt vezérlő: {nev}"
    return elem


def _var(root, nev, qt_app, *, lathato=True, ido=5.0):
    lejar = time.monotonic() + ido
    elem = None
    while time.monotonic() < lejar:
        qt_app.processEvents()
        elem = root.findChild(QObject, nev)
        if elem is not None and (
            not lathato or bool(elem.property("visible"))
        ):
            return elem
        QTest.qWait(10)
    assert elem is not None and (
        not lathato or bool(elem.property("visible"))
    ), (
        f"a várt QML-elem nem vált láthatóvá: {nev}"
    )
    return elem


def _gyermek_item(root_item, nev):
    """A ListView delegate-jeit a QQuickItem-vizualis fában keresi."""
    vizsgalando = [root_item]
    while vizsgalando:
        item = vizsgalando.pop()
        if item.objectName() == nev:
            return item
        vizsgalando.extend(item.childItems())
    return None


def _kattint(window, elem, qt_app):
    assert elem.isEnabled(), f"a vezérlő le van tiltva: {elem.objectName()}"
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    assert 0 <= pont.x() < window.width() and 0 <= pont.y() < window.height()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _gepel(window, szoveg):
    """Karakterenként küld valódi QWindow billentyűeseményeket."""
    for karakter in szoveg:
        assert ord(karakter) < 128, "a QTest QWindow billentyűútja ASCII-t kezel"
        QTest.keyEvent(QTest.KeyAction.Click, window, ord(karakter))


def _kitoltes_latszik(window, felulet, dialog):
    kep = window.grabWindow()
    assert not kep.isNull(), "a főablak nem adott renderelt kimenetet"
    szin = QColor(felulet.property("color"))
    tartalom = dialog.property("contentItem")
    assert isinstance(tartalom, QQuickItem)
    tartalom_teteje = tartalom.mapToItem(felulet, QPointF(0, 0)).y()
    fejléc = dialog.property("header")
    fejléc_alja = 0.0
    if isinstance(fejléc, QQuickItem) and fejléc.isVisible():
        fejléc_alja = fejléc.mapToItem(
            felulet, QPointF(0, fejléc.height())
        ).y()
    if tartalom_teteje > fejléc_alja + 1:
        helyi_y = (tartalom_teteje + fejléc_alja) / 2
    else:
        helyi_y = min(tartalom_teteje + 5, felulet.height() - 2)
    pont = felulet.mapToScene(QPointF(felulet.width() / 2, helyi_y))
    meret_x = kep.width() / window.width()
    meret_y = kep.height() / window.height()
    pixel_x = round(pont.x() * meret_x)
    pixel_y = round(pont.y() * meret_y)
    pixel = kep.pixelColor(pixel_x, pixel_y)
    assert pixel == szin, (
        "a párbeszéd szövegmentes felső kitöltése nem jelent meg a képen: "
        f"várt {szin.name()}, mért {pixel.name()} at ({pixel_x}, {pixel_y}); "
        f"scene=({pont.x()}, {pont.y()}), grab={kep.width()}x{kep.height()}, "
        f"window={window.width()}x{window.height()}"
    )


def test_email_feliratok_eredeti_angol_qstr_forrasbol_fordulnak():
    qml_forras = _QML.read_text(encoding="utf-8")
    for forras, darab in _EMAIL_FORRASOK.items():
        assert qml_forras.count(forras) == darab, forras


def test_email_feliratok_hivatalos_forditasa_benne_van_a_betoltott_qm(qt_app):
    translator = QTranslator(qt_app)
    assert translator.load(str(_I18N / "picasapy_hu.qm"))
    for forras, magyar in _EMAIL_MAGYAR.items():
        assert translator.translate("EmailChoiceDialog", forras) == magyar


def test_fooldali_kattintas_osszeallitja_es_atadja_a_levelet(
    qml_app_email, qt_app, tmp_path, monkeypatch
):
    import picasapy.app.email_controller as email_module

    window, _app_controller, engine = qml_app_email
    eredeti_magassag = window.height()

    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    settings.setValue("mail/useDefaultClient", False)
    levelezovezerlo = engine.rootContext().contextProperty("emailController")
    levelezovezerlo.setUseDefaultClient(False)

    # Az exportált melléklet is a teszt ideiglenes könyvtárában marad.
    kimenet = tmp_path / "csatolmanyok"
    monkeypatch.setattr(
        email_module.tempfile,
        "mkdtemp",
        lambda prefix: str(kimenet.mkdir(exist_ok=True) or kimenet),
    )
    inditott_parancsok = []
    monkeypatch.setattr(email_module, "_which", lambda _nev: "/usr/bin/xdg-email")
    monkeypatch.setattr(
        email_module, "_popen", lambda argv: inditott_parancsok.append(list(argv))
    )

    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    email_gomb = _elem(window, "trayEmailButton")
    _kattint(window, email_gomb, qt_app)

    dialog = _var(window, "emailChoiceDialog", qt_app)
    try:
        assert dialog.property("title") == "Képek küldése e-mailben"
        valaszto = _elem(dialog, "emailChoicePicker")
        assert valaszto.isVisible()
        for magassag_elteres in (-5, 0, 5):
            window.setHeight(eredeti_magassag + magassag_elteres)
            qt_app.processEvents()
            assert window.height() == eredeti_magassag + magassag_elteres
            _kitoltes_latszik(
                window, _elem(dialog, "emailDialogSurface"), dialog
            )
        for nev, felirat in (
            ("emailChoiceTitleLabel", "Válasszon levelezőprogramot"),
            (
                "emailChoiceSelectText",
                "Válassza ki, hogyan szeretné e-mailben elküldeni fotóit.",
            ),
            ("emailChoiceMailClientLabel", "LEVELEZŐPROGRAM"),
            (
                "emailChoiceMailClientDescription",
                "Az alapértelmezett levelezőprogram használata",
            ),
            (
                "emailChoiceSignupLabel",
                "Nincs Gmail-fiókja? Nyisson egy fiókot ingyen.",
            ),
            ("emailChoiceGoogleLabel", "Google Mail"),
            (
                "emailChoiceGoogleDescription",
                "A Gmail-fiók vagy a Google Fiók használata",
            ),
            (
                "emailChoiceRemember",
                "Jegyezze meg ezt a beállítást, ne jelenítse meg a párbeszédpanelt újra.",
            ),
        ):
            assert _elem(dialog, nev).property("text") == felirat
        assert _elem(dialog, "emailChoiceHelpLabel").property("text") == "Súgó"
        assert _elem(dialog, "emailChoiceCancelLabel").property("text") == "Mégse"
        _kattint(window, _elem(dialog, "emailChoiceHelpButton"), qt_app)
        seged = _elem(dialog, "emailChoiceHelpText")
        assert seged.isVisible()
        assert seged.property("text") == (
            "A képek az alapértelmezett levelezőprogram új üzenetéhez "
            "csatolva nyílnak meg."
        )
        _kattint(window, _elem(dialog, "emailChoiceHelpButton"), qt_app)
        _kattint(window, _elem(dialog, "emailChoiceRemember"), qt_app)
        _kattint(window, _elem(dialog, "emailChoiceDefaultButton"), qt_app)
        szerkeszto = _elem(dialog, "emailComposePanel")
        assert szerkeszto.isVisible()
        assert _elem(dialog, "emailComposeChangeUser").property("text") == (
            "Felhasználóváltás"
        )
        assert _elem(dialog, "emailComposeToLabel").property("text") == "Címzett:"
        assert _elem(dialog, "emailComposeSubjectLabel").property("text") == "Tárgy:"
        assert _elem(dialog, "emailComposeDiscard").property("text") == "Elvetés"
        assert _elem(dialog, "emailComposeSend").property("text") == "Küldés"
        lista = _elem(dialog, "emailComposePreview")
        kep_elonezet = _gyermek_item(lista.property("contentItem"), "emailComposePreviewImage")
        assert kep_elonezet is not None, (
            "a képelőnézet nem épült fel; "
            f"mellékletek={dialog.property('attachmentPaths')!r}; "
            f"lista={lista.property('count')}"
        )
        vart_kep = str(dialog.property("attachmentPaths")[0])
        assert QUrl(kep_elonezet.property("source")).toLocalFile() == vart_kep

        for magassag_elteres in (-5, 0, 5):
            window.setHeight(eredeti_magassag + magassag_elteres)
            qt_app.processEvents()
            assert window.height() == eredeti_magassag + magassag_elteres
            _kitoltes_latszik(
                window, _elem(dialog, "emailDialogSurface"), dialog
            )

        cimzett = _elem(dialog, "emailComposeRecipientField")
        _kattint(window, cimzett, qt_app)
        _gepel(window, "anna@example.test")
        targy = _elem(dialog, "emailComposeSubjectField")
        _kattint(window, targy, qt_app)
        _gepel(window, "Summer photos")
        torzs = _elem(dialog, "emailComposeBodyField")
        _kattint(window, torzs, qt_app)
        _gepel(window, "Hello! Photos attached.")

        _kattint(window, _elem(dialog, "emailComposeSendButton"), qt_app)

        assert len(inditott_parancsok) == 1, "a Küldés nem indította el a levelet"
        argv = inditott_parancsok[0]
        assert argv[argv.index("--to") + 1] == "anna@example.test"
        assert argv[argv.index("--subject") + 1] == "Summer photos"
        assert argv[argv.index("--body") + 1] == "Hello! Photos attached."
        csatolasok = [
            argv[i + 1] for i, elem in enumerate(argv) if elem == "--attach"
        ]
        assert len(csatolasok) == 1 and Path(csatolasok[0]).is_file()
        assert settings.value("mail/useDefaultClient") in (True, "true")
    finally:
        if bool(dialog.property("visible")):
            dialog.setProperty("visible", False)
