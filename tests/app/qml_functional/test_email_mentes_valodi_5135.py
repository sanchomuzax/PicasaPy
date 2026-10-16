"""Az „E-mail" és a „Mentés" tételei VALÓDI egérkattintással (#5135, 4. rész).

A főablakban kattintunk: a tálca e-mail gombjára, az Eszközök menüpontjára,
a párbeszédek gombjaira. A hatást a felhasználó felől nézzük: bezárul-e a
párbeszéd, kiesik-e a melléklet, nyílik-e a tallózó, és indul-e levél.

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()` a tesztelt vezérlőkön. A csatolmány-mappát és a
levelezőprogram indítását a meglévő tesztek mintájára helyettesítjük
(`_mkdtemp`, `_which`, `_popen`).

Lefedve (E-mail):
- `emailChoiceCancelButton` - a választó Mégse: bezárul, nem indul levél;
- `emailComposeDiscardButton` - a levélszerkesztő Elvetés: bezárul, nem indul;
- `emailComposeDiscardImageButton` - a csatolt kép „×": kiesik a mellékletből.

Nincs teszt: `emailChoiceSignupLink` - a `Qt.openUrlExternally`-t hívja, ami
böngészőt indítana a tesztgépen, és Pythonból nem helyettesíthető.

Lefedve (Mentés):
- `backupSetFilter` - a készlet-űrlap fájlszűrő legördülője;
- `backupFormCancel` - a készlet-űrlap Mégse: bezárul, nincs új készlet;
- `backupRestoreCancel` - a visszaállítás Mégse: bezárul;
- `backupRestoreChooseFolder`, `backupRestoreChooseIso`,
  `backupRestoreChooseTarget` - a három tallózó gomb megnyitja a tallózót.
  A tallózó maga nem fut le (nincs `accepted`), a takarításban `close`-zal zárjuk.

⚠️ A Mentés-panel és az Ajándék-CD-panel ugyanazt a `PublishPanel`-t
ágyazza be, ezért a közös objectName-ek (pl. `publishNewBackupSet`) az
ablakon végigkeresve az Ajándék-CD példányát adnák. A Mentés gyerekeit
ezért a `backupHost` alatt keressük.

⚠️ A menüsor QML-wrapperét a tesztnek életben kell tartania: a helper
eldobott lokális változója Pythonból megsemmisíti a C++ objektumot, és az
ablak később „already deleted" hibát ad.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.app.qml_functional._fomenu_4420_menu import _megnyit


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _gyerek(gyoker, nev: str):
    elem = _objektum(gyoker, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(window, qt_app, elem) -> None:
    assert elem.property("visible") is True, f"{elem.objectName()} nem látszik"
    assert elem.property("enabled") is True, f"{elem.objectName()} tiltott"
    pont = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )
    qt_app.processEvents()


def _lista(ertek):
    """A QML-ből érkező tömb: a `QJSValue`-t Python-listává alakítjuk."""
    return ertek.toVariant() if hasattr(ertek, "toVariant") else ertek


def _zar(qt_app, objektum) -> None:
    """Takarítás: a nyitva maradt párbeszédet bezárjuk."""
    QMetaObject.invokeMethod(objektum, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _vizualis_bejaras(item):
    for gyerek in item.childItems():
        yield gyerek
        yield from _vizualis_bejaras(gyerek)


def _felirat_szerint(window, felirat: str) -> QQuickItem | None:
    """Az első LÁTHATÓ elem, amelynek a szövege `felirat` (pl. legördülő sora)."""
    for item in _vizualis_bejaras(window.contentItem()):
        if (
            item.property("text") == felirat
            and item.isVisible()
            and item.width() > 0
            and item.height() > 0
        ):
            return item
    return None


# ---------------------------------------------------------------- E-mail

@pytest.fixture
def mail_app(qml_app_email, monkeypatch, tmp_path):
    """A főablak e-mail-vezérlővel; a levél-indítás és a mappa helyettesítve."""
    import picasapy.app.email_controller as email_module

    kimenet = tmp_path / "csatolmanyok"
    monkeypatch.setattr(
        email_module,
        "_mkdtemp",
        lambda prefix: str(kimenet.mkdir(exist_ok=True) or kimenet),
    )
    indult: list[list[str]] = []
    monkeypatch.setattr(email_module, "_which", lambda _nev: "/usr/bin/xdg-email")
    monkeypatch.setattr(
        email_module, "_popen", lambda argv: indult.append(list(argv))
    )
    window, _controller, engine = qml_app_email
    return window, engine, indult


def _nyisd_emailt(window, qt_app, engine):
    """A tálca e-mail gombjával nyitja a választót (valódi kattintás)."""
    window.show()
    window.requestActivate()
    engine.rootContext().contextProperty("emailController").setUseDefaultClient(False)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    _kattints(window, qt_app, _gyerek(window, "trayEmailButton"))
    dialog = _gyerek(window, "emailChoiceDialog")
    assert _varj(qt_app, lambda: dialog.property("opened") is True), (
        "a tálca e-mail gombja nem nyitotta meg a választót"
    )
    return dialog


class TestEmail:
    def test_a_valasztó_megse_bezarja_es_nem_indit_levelet(
        self, mail_app, qt_app
    ):
        window, engine, indult = mail_app
        dialog = _nyisd_emailt(window, qt_app, engine)

        _kattints(window, qt_app, _gyerek(window, "emailChoiceCancelButton"))

        assert _varj(qt_app, lambda: dialog.property("opened") is False), (
            "a választó Mégse nem zárta be a párbeszédet"
        )
        assert indult == [], "a Mégse mégis levelezőt indított"

    def test_a_level_elvetese_bezarja_es_nem_indit_levelet(
        self, mail_app, qt_app
    ):
        window, engine, indult = mail_app
        dialog = _nyisd_emailt(window, qt_app, engine)
        _kattints(window, qt_app, _gyerek(window, "emailChoiceDefaultButton"))
        assert _gyerek(window, "emailComposePanel").property("visible") is True, (
            "a próba feltétele: a levélszerkesztőnek nyitva kell lennie"
        )

        _kattints(window, qt_app, _gyerek(window, "emailComposeDiscardButton"))

        assert _varj(qt_app, lambda: dialog.property("opened") is False), (
            "a levél Elvetése nem zárta be a párbeszédet"
        )
        assert indult == [], "az Elvetés mégis elindította a levelezőt"

    def test_a_csatolt_kep_x_gombja_kiveszi_a_mellekletet(self, mail_app, qt_app):
        window, engine, _indult = mail_app
        dialog = _nyisd_emailt(window, qt_app, engine)
        _kattints(window, qt_app, _gyerek(window, "emailChoiceDefaultButton"))
        melleklet = _lista(dialog.property("attachmentPaths"))
        assert len(melleklet) == 1, "a próba feltétele: egy csatolt kép legyen"
        gomb = _gyerek(window, "emailComposeDiscardImageButton")
        assert gomb.property("enabled") is True, "a × gomb tiltott a kijelölt képnél"

        _kattints(window, qt_app, gomb)

        assert _varj(
            qt_app, lambda: len(_lista(dialog.property("attachmentPaths"))) == 0
        ), "a × gomb nem vette ki a képet a mellékletből"
        assert dialog.property("selectedAttachmentIndex") == -1


# ----------------------------------------------------------------- Mentés

@pytest.fixture
def mentes_app(qt_app, tmp_path):
    """A főablak; a Mentés-panelt az Eszközök ▸ Back Up Pictures... nyitja."""
    for window, controller, engine in _build_qml_app(qt_app, tmp_path):
        window.show()
        window.requestActivate()
        controller.selectFolder(str(Path(str(controller.watchedFolders[0]))))
        qt_app.processEvents()
        yield window, controller, engine


def _mentes_panel(window, qt_app):
    """Valódi kattintás az Eszközök ▸ Back Up Pictures... pontján.

    Visszaadja a menüsort és a panelt is: a hívónak életben kell tartania
    őket (lásd a modul-dokumentáció ⚠️ megjegyzését).
    """
    menu_bar = window.property("menuBar")
    _megnyit(menu_bar, qt_app, "&Tools")
    _kattints(window, qt_app, _gyerek(window, "menuToolsBackup"))
    host = _gyerek(window, "backupHost")
    assert _varj(qt_app, lambda: host.property("visible") is True), (
        "az Eszközök ▸ Back Up Pictures... nem nyitotta meg a Mentést"
    )
    return menu_bar, host


def _urlap_megnyitasa(window, qt_app, host):
    """Valódi kattintás az „Új készlet" gombon: megnyílik az űrlap."""
    _kattints(window, qt_app, _gyerek(host, "publishNewBackupSet"))
    urlap = _gyerek(host, "backupSetDialog")
    assert _varj(qt_app, lambda: urlap.property("opened") is True), (
        "az Új készlet gomb nem nyitotta meg az űrlapot"
    )
    return urlap


def _visszaallitas_megnyitasa(window, qt_app, host):
    """Valódi kattintás a Visszaállítás gombon: megnyílik a párbeszéd."""
    _kattints(window, qt_app, _gyerek(host, "publishBackupRestore"))
    visszaallitas = _gyerek(host, "backupRestoreDialog")
    assert _varj(qt_app, lambda: visszaallitas.property("opened") is True), (
        "a Visszaállítás gomb nem nyitotta meg a párbeszédet"
    )
    return visszaallitas


def _tallozo_cim_szerint(host, cim: str):
    """A tallózó (FolderDialog / FileDialog) a címe szerint.

    A tallózóknak nincs objectName-je, csak `id`-jük, de a `title` egyedi.
    """
    for elem in host.findChildren(QObject):
        if elem.property("title") == cim:
            return elem
    raise AssertionError(f"a(z) „{cim}” tallózó nem található")


class TestMentes:
    def test_a_fajlszuro_legorduloje_valasztja_a_szurot(self, mentes_app, qt_app):
        window, _controller, _engine = mentes_app
        menu_bar, host = _mentes_panel(window, qt_app)
        urlap = _urlap_megnyitasa(window, qt_app, host)
        szurok = host.property("szuroKulcsok").toVariant()
        feliratok = host.property("szuroFeliratok").toVariant()
        masodik_kulcs, masodik_felirat = szurok[1], feliratok[1]
        assert host.property("urlapSzuro") != masodik_kulcs

        _kattints(window, qt_app, _gyerek(urlap, "backupSetFilter"))
        sor = _felirat_szerint(window, masodik_felirat)
        assert sor is not None, "a szűrő legördülője nem nyílt meg a második sorral"
        _kattints(window, qt_app, sor)

        assert _varj(qt_app, lambda: host.property("urlapSzuro") == masodik_kulcs), (
            "a legördülő valódi kattintása nem állította át a szűrőt"
        )
        assert menu_bar is not None

    def test_az_urlap_megse_bezarja_es_nem_hoz_letre_keszletet(
        self, mentes_app, qt_app
    ):
        window, _controller, _engine = mentes_app
        _menu_bar, host = _mentes_panel(window, qt_app)
        urlap = _urlap_megnyitasa(window, qt_app, host)
        keszletek_elotte = len(_lista(host.property("keszletek")))

        _kattints(window, qt_app, _gyerek(urlap, "backupFormCancel"))

        assert _varj(qt_app, lambda: urlap.property("opened") is False), (
            "az űrlap Mégse nem zárta be a párbeszédet"
        )
        assert host.property("szerkesztes") is False
        assert len(_lista(host.property("keszletek"))) == keszletek_elotte, (
            "a Mégse mégis létrehozott egy készletet"
        )

    def test_a_visszaallitas_megse_bezarja_a_parbeszedet(self, mentes_app, qt_app):
        window, _controller, _engine = mentes_app
        _menu_bar, host = _mentes_panel(window, qt_app)
        visszaallitas = _visszaallitas_megnyitasa(window, qt_app, host)

        _kattints(window, qt_app, _gyerek(visszaallitas, "backupRestoreCancel"))

        assert _varj(qt_app, lambda: visszaallitas.property("opened") is False), (
            "a visszaállítás Mégse nem zárta be a párbeszédet"
        )
        assert host.property("visszaallitasNyitva") is False

    @pytest.mark.parametrize(
        ("gomb", "tallozo_cim"),
        (
            ("backupRestoreChooseFolder", "Choose backup folder"),
            ("backupRestoreChooseIso", "Choose the first disc image"),
            ("backupRestoreChooseTarget", "Choose restore folder"),
        ),
    )
    def test_a_visszaallitas_tallozo_gombja_megnyitja_a_tallozot(
        self, mentes_app, qt_app, gomb, tallozo_cim
    ):
        window, _controller, _engine = mentes_app
        _menu_bar, host = _mentes_panel(window, qt_app)
        visszaallitas = _visszaallitas_megnyitasa(window, qt_app, host)
        _kattints(window, qt_app, _gyerek(visszaallitas, gomb))

        valaszto = _tallozo_cim_szerint(host, tallozo_cim)
        try:
            assert _varj(qt_app, lambda: valaszto.property("visible") is True), (
                f"a(z) {gomb} gomb nem nyitotta meg a(z) „{tallozo_cim}” tallózót"
            )
        finally:
            _zar(qt_app, valaszto)
