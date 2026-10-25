"""Az „Egyéb" maradék párbeszédei VALÓDI egérkattintással (#5150, 11. rész, 2. fájl).

Az első fájl (`test_parbeszedek2_valodi_5150.py`) párja. Lefedve:
- `HelpDialog`: `helpResultRow` - a fejezetlista sorára kattintás átvált, keresés nélkül és keresve is (#5172).
- `TextFieldContextMenu` a súgó keresőmezején: `textMenuSelectAll`, `textMenuCopy`,
  `textMenuCut`, `textMenuPaste`, `textMenuDelete`, `textMenuUndo`. A `textMenuAutoComplete`
  csak a címzett-mezőn van: `test_email_autocomplete_context_menu_4636.py` fedi.
- `HiddenPasswordDialog`: `hiddenPasswordModern`; `AdjustTimestampDialog`: `adjustTimestampRelative`.
- `SaveDialogs`: `saveConfirmRememberCheck`; `SplashScreen`: `splashOkButton`;
  `PublishPanel`: `publishDeleteBackupSet`.

Nincs itt: `publishUploadAllSize`, `publishUploadAllAccess` (nincs kezelőjük, a feltöltés
online művelete megszűnt); `FaceScanDialog.faceScanDownloadCancelButton` (hálózat).

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated` hívás és
nincs `.emit()` a tesztelt vezérlőn.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPointF, QUrl, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent

import picasapy.app.application as app_module
from tests.support.qt_wait import wait_for_photo_op
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    kattints,
    kijelol,
)
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135 import (
    _menupont_kattintasa,
)
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
    _gyerek,
    _klikk_ablakban,
    _latszik,
    _varj,
    _vizualis_bejaras,
)
from tests.app.qml_functional.test_parbeszedek2_valodi_5150 import (
    _aktival,
    _bool,
    _lista,
    parbeszed_app,  # noqa: F401 - pytest fixture
)
from tests.app.qml_functional.test_mentes_gomb_felirat_3713 import (  # noqa: F401
    gazda,
)
from tests.app.qml_functional.test_rejtett_jelszo_menu_3461 import (
    REJTETT_FEJLEC,
    _kattint as _kattint_rejtett,
    _rejtett_mappaval,
    _vizualis_elem,
)

_SZOVEG = "alfa beta"


def _sugo_nyit(window, qt_app):
    """Súgó ▸ Help Contents and Index, valódi kattintásokkal."""
    menu_bar = window.property("menuBar")
    _megnyit(menu_bar, qt_app, "&Help")
    _menupont_kattintasa(window, qt_app, "menuHelpContents")
    assert _varj(qt_app, lambda: _latszik(window, "helpDialog")), "a Súgó nem nyílt meg"
    return _gyerek(window, "helpDialog")


def _fejezetsor(lista, index: int):
    """Az `index`. látható fejezetsor (a delegátum) felülről lefelé, a VIZUÁLIS fában."""
    sorok = [
        elem
        for elem in _vizualis_bejaras(lista)
        if elem.objectName() == "helpResultRow" and elem.isVisible()
    ]
    sorok.sort(key=lambda elem: elem.mapToScene(QPointF(0, 0)).y())
    return sorok[index] if len(sorok) > index else None


def _cime(sor) -> str | None:
    """A fejezetsor címsora, a látható szöveg (a VIZUÁLIS fából)."""
    for elem in _vizualis_bejaras(sor):
        if elem.objectName() == "helpResultTitle":
            return elem.property("text")
    return None


class TestSugoFejezetlista:
    def test_a_fejezetsorra_kattintva_a_nezo_a_sor_fejezetet_valasztja(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, _controller, _engine = parbeszed_app
        sugo = _sugo_nyit(window, qt_app)
        lista = _gyerek(window, "helpTopicList")
        assert _varj(qt_app, lambda: _fejezetsor(lista, 1) is not None), "nincs fejezetsor"
        # a második sor fejezete: a súgó a főoldallal (az első sorral) nyílik
        masodik = _lista(lista.property("model"))[1]
        elvart = masodik.get("fejezet") or masodik.get("nev")
        assert sugo.property("topic") != elvart, "a próba feltétele: a fejezet még nem a célé"

        # a súgó a saját ablakában él (HelpWindow.qml): a kattintást annak küldjük
        sor = _fejezetsor(lista, 1)
        sugo_ablak = sor.window()
        _aktival(qt_app, sugo_ablak)
        _klikk_ablakban(qt_app, sugo_ablak, sor)

        assert _varj(qt_app, lambda: sugo.property("topic") == elvart), (
            "a fejezetsorra kattintás nem állította a nézett fejezetet"
        )

    def test_a_kereses_nelkuli_sor_cime_latszik_es_a_kattintas_atvalt(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        """#5172: keresés nélkül a Python-lista dict-jeiből a cím és a fejezet is látszik."""
        window, controller, _engine = parbeszed_app
        sugo = _sugo_nyit(window, qt_app)
        lista = _gyerek(window, "helpTopicList")
        assert _varj(qt_app, lambda: _fejezetsor(lista, 2) is not None), "nincs harmadik fejezetsor"
        harmadik = controller.helpTopics[2]
        sor = _fejezetsor(lista, 2)
        assert _cime(sor) == harmadik["cim"], (
            f"a keresés nélküli sor címe nem látszik: {_cime(sor)!r}"
        )
        assert sugo.property("topic") != harmadik["nev"], "a próba feltétele: a fejezet még nem a célé"

        sugo_ablak = sor.window()
        _aktival(qt_app, sugo_ablak)
        _klikk_ablakban(qt_app, sugo_ablak, sor)

        assert _varj(qt_app, lambda: sugo.property("topic") == harmadik["nev"]), (
            "a keresés nélküli sorra kattintás nem váltott fejezetet"
        )

    def test_a_talalatsorra_kattintva_a_nezo_a_talalat_fejezetet_valasztja(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        """#5172: keresve a ListModel sorára valódi kattintás is átvált."""
        window, controller, _engine = parbeszed_app
        sugo = _sugo_nyit(window, qt_app)
        lista = _gyerek(window, "helpTopicList")
        fejezetlista_db = lista.property("count")
        talalatok = controller.helpSearch("effekt")
        assert talalatok, "az »effekt« keresés nem ad találatot"
        assert fejezetlista_db != len(talalatok), "a próba feltétele: a két lista darabszáma különbözzön"

        _gyerek(window, "helpSearchField").setProperty("text", "effekt")
        assert _varj(qt_app, lambda: lista.property("count") == len(talalatok)), (
            "a keresés nem váltotta a találatlistára a fejezetlistát"
        )

        # a kiinduló fejezet (főoldal) NEM lehet a cél: az első találat épp a főoldal
        idx = next(i for i, t in enumerate(talalatok) if t["fejezet"] != sugo.property("topic"))
        cel = talalatok[idx]["fejezet"]

        def _talalat_sor_felépült():
            talalat_sor = _fejezetsor(lista, idx)
            return (
                talalat_sor is not None
                and talalat_sor.width() > 0
                and talalat_sor.height() > 0
                and talalatok[idx]["cim"] in (_cime(talalat_sor) or "")
            )

        assert _varj(qt_app, _talalat_sor_felépült), "a találatsor nem kapott méretet és címet"
        sor = _fejezetsor(lista, idx)
        assert sor is not None, "nincs találatsor"

        sugo_ablak = sor.window()
        _aktival(qt_app, sugo_ablak)
        _klikk_ablakban(qt_app, sugo_ablak, sor)

        assert _varj(qt_app, lambda: sugo.property("topic") == cel), (
            f"a találatsorra kattintva nem a {cel!r} fejezet nyílt meg"
        )


def _keresomezo(window, qt_app):
    """A súgó keresőmezője, benne a beállított szöveggel (előkészítés)."""
    _sugo_nyit(window, qt_app)
    mezo = _gyerek(window, "helpSearchField")
    mezo.setProperty("text", _SZOVEG)
    qt_app.processEvents()
    return mezo


def _jobbklikk_menu(window, qt_app, mezo):
    """Valódi jobbklikk a mezőn; visszaadja a megnyílt szövegmező-menüt."""
    terulet = next(
        (
            elem
            for elem in mezo.findChildren(QObject)
            if "TextFieldContextArea" in elem.metaObject().className()
        ),
        None,
    )
    assert terulet is not None, "a keresőmezőn nincs jobbklikk-terület"
    kattints(window, qt_app, mezo, Qt.MouseButton.RightButton)
    menu = terulet.property("contextMenu")
    assert _varj(qt_app, lambda: menu is not None and menu.property("opened") is True), (
        "a jobbklikk nem nyitotta meg a szövegmező-menüt"
    )
    return menu


def _menutetel(window, qt_app, menu, nev: str):
    """A menü `nev` tétele, valódi kattintáshoz: látszik és kattintható."""
    tetel = menu.findChild(QObject, nev)
    assert tetel is not None, f"{nev} nincs a menüben"
    assert _varj(qt_app, lambda: tetel.property("enabled") is True), f"{nev} tiltott"
    return tetel


def _kijelol_szoveget(mezo, qt_app, kezdet: int, veg: int) -> None:
    """Előkészítés: a mező kijelölése (a tesztelt tétel a menü, nem ez)."""
    QMetaObject.invokeMethod(
        mezo, "select", Qt.ConnectionType.DirectConnection,
        Q_ARG(int, kezdet), Q_ARG(int, veg),
    )
    qt_app.processEvents()


class TestSzovegMenu:
    def test_az_osszes_kijelolese_valodi_kattintassal_kijeloli_a_szoveget(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, _controller, _engine = parbeszed_app
        mezo = _keresomezo(window, qt_app)
        menu = _jobbklikk_menu(window, qt_app, mezo)

        kattints(window, qt_app, _menutetel(window, qt_app, menu, "textMenuSelectAll"))

        assert _varj(qt_app, lambda: mezo.property("selectedText") == _SZOVEG), (
            "az Összes kijelölése kattintás nem jelölte ki a teljes szöveget"
        )

    def test_a_masolas_valodi_kattintassal_a_vagolapra_teszi_a_kijelolest(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, _controller, _engine = parbeszed_app
        mezo = _keresomezo(window, qt_app)
        QGuiApplication.clipboard().setText("")
        _kijelol_szoveget(mezo, qt_app, 0, 4)
        menu = _jobbklikk_menu(window, qt_app, mezo)

        kattints(window, qt_app, _menutetel(window, qt_app, menu, "textMenuCopy"))

        assert _varj(qt_app, lambda: QGuiApplication.clipboard().text() == "alfa"), (
            "a Másolás kattintás nem tette a kijelölést a vágólapra"
        )
        assert mezo.property("text") == _SZOVEG, "a Másolás megváltoztatta a szöveget"

    def test_a_kivagas_valodi_kattintassal_kiveszi_es_a_vagolapra_teszi(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, _controller, _engine = parbeszed_app
        mezo = _keresomezo(window, qt_app)
        QGuiApplication.clipboard().setText("")
        _kijelol_szoveget(mezo, qt_app, 0, 4)
        menu = _jobbklikk_menu(window, qt_app, mezo)

        kattints(window, qt_app, _menutetel(window, qt_app, menu, "textMenuCut"))

        assert _varj(qt_app, lambda: mezo.property("text") == " beta"), (
            "a Kivágás kattintás nem vette ki a kijelölt részt"
        )
        assert _varj(qt_app, lambda: QGuiApplication.clipboard().text() == "alfa")

    def test_a_beillesztes_valodi_kattintassal_beteszi_a_vagolap_szoveget(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, _controller, _engine = parbeszed_app
        mezo = _keresomezo(window, qt_app)
        QGuiApplication.clipboard().setText("xyz")
        menu = _jobbklikk_menu(window, qt_app, mezo)

        kattints(window, qt_app, _menutetel(window, qt_app, menu, "textMenuPaste"))

        assert _varj(qt_app, lambda: "xyz" in mezo.property("text")), (
            "a Beillesztés kattintás nem írta be a vágólap szövegét"
        )

    def test_a_torles_valodi_kattintassal_a_kijelolest_torli_a_vagolap_nelkul(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, _controller, _engine = parbeszed_app
        mezo = _keresomezo(window, qt_app)
        QGuiApplication.clipboard().setText("maradjon")
        _kijelol_szoveget(mezo, qt_app, 0, 4)
        menu = _jobbklikk_menu(window, qt_app, mezo)

        kattints(window, qt_app, _menutetel(window, qt_app, menu, "textMenuDelete"))

        assert _varj(qt_app, lambda: mezo.property("text") == " beta"), (
            "a Törlés kattintás nem a kijelölést törölte"
        )
        assert QGuiApplication.clipboard().text() == "maradjon", (
            "a Törlés a vágólapra másolt"
        )

    def test_a_visszavonas_valodi_kattintassal_visszaallitja_a_torlest(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, _controller, _engine = parbeszed_app
        mezo = _keresomezo(window, qt_app)
        _kijelol_szoveget(mezo, qt_app, 0, 4)
        menu = _jobbklikk_menu(window, qt_app, mezo)
        kattints(window, qt_app, _menutetel(window, qt_app, menu, "textMenuDelete"))
        assert _varj(qt_app, lambda: mezo.property("text") == " beta")

        menu = _jobbklikk_menu(window, qt_app, mezo)
        kattints(window, qt_app, _menutetel(window, qt_app, menu, "textMenuUndo"))

        assert _varj(qt_app, lambda: mezo.property("text") == _SZOVEG), (
            "a Visszavonás kattintás nem állította vissza a törölt szöveget"
        )


class TestRejtettJelszo:
    def test_az_erosebb_vedelem_jelolo_valodi_kattintassal_atallitja_a_kerest(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, _controller, _engine = parbeszed_app
        _rejtett_mappaval(parbeszed_app, qt_app)
        _kattint_rejtett(
            qt_app, window, _vizualis_elem(window, REJTETT_FEJLEC), Qt.MouseButton.RightButton
        )
        menu = _gyerek(window, "collectionContextMenu")
        assert _varj(qt_app, lambda: menu.property("opened") is True)
        _kattint_rejtett(qt_app, window, _gyerek(window, "collectionMenuPassword"))
        assert _varj(qt_app, lambda: _latszik(window, "collectionPasswordDialog")), (
            "a jelszó-párbeszéd nem nyílt meg"
        )
        parbeszed = _gyerek(window, "collectionPasswordDialog")
        jelolo = _gyerek(parbeszed, "collectionPasswordModern")
        assert parbeszed.property("modernRequested") is False

        _kattint_rejtett(qt_app, window, jelolo)

        assert _varj(qt_app, lambda: parbeszed.property("modernRequested") is True), (
            "a jelölő kattintása nem kérte az erős védelmet"
        )
        assert jelolo.property("checked") is True


class TestDatumAtallitas:
    def test_a_relativ_mod_valodi_kattintassal_az_abszolutrol_visszavalt(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        _megnyit(menu_bar, qt_app, "&Tools")
        _menupont_kattintasa(window, qt_app, "menuToolsAdjustTimestamp")
        assert _varj(qt_app, lambda: _latszik(window, "adjustTimestampDialog")), (
            "a dátum-átállító párbeszéd nem nyílt meg"
        )
        relativ = _gyerek(window, "adjustTimestampRelative")
        absolut = _gyerek(window, "adjustTimestampAbsolute")
        assert relativ.property("checked") is True

        _klikk_ablakban(qt_app, window, absolut)
        assert _varj(qt_app, lambda: absolut.property("checked") is True)

        _klikk_ablakban(qt_app, window, relativ)

        assert _varj(qt_app, lambda: relativ.property("checked") is True), (
            "a Relatív kattintás nem kapcsolt relatív módra"
        )
        assert absolut.property("checked") is False, "az abszolút mód bent maradt"


class TestMentesMegerosites:
    def test_a_ne_kerdezd_jelolo_valodi_kattintassal_beallitja_a_beallitast(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        wait_for_photo_op(
            controller,
            lambda: controller.applyEffectMany([0], "enhance"),
            qt_app=qt_app,
        )
        menu_bar = window.property("menuBar")
        _megnyit(menu_bar, qt_app, "&File")
        _menupont_kattintasa(window, qt_app, "menuFileSave")
        assert _varj(qt_app, lambda: _latszik(window, "saveConfirmDialog")), (
            "a Fájl ▸ Save nem kérdezett rá a mentésre"
        )
        dialog = _gyerek(window, "saveConfirmDialog")
        jelolo = _gyerek(window, "saveConfirmRememberCheck")

        _klikk_ablakban(qt_app, window, jelolo)

        assert _varj(qt_app, lambda: jelolo.property("checked") is True), (
            "a Ne kérdezd újra jelölő nem vált be"
        )
        assert dialog.property("rememberChecked") is True

        mentes = _gomb_szovege(dialog, ("Save", "Mentés"))
        _aktival(qt_app, window)
        _klikk_ablakban(qt_app, window, mentes)

        assert _varj(
            qt_app,
            lambda: _bool(controller._settings.value("confirm/DoNotAskFileSave/remember")),
        ), "a Mentés nem írta be a Ne kérdezd újra beállítást"


def _gomb_szovege(dialog, szovegek: tuple[str, ...]):
    """A párbeszéd láblécének gombja a megadott felirattal (valódi, látható elem)."""
    lab = dialog.property("footer")
    assert lab is not None, "a párbeszédnek nincs lábléce"
    for elem in _vizualis_bejaras(lab):
        if elem.property("text") in szovegek and elem.isVisible():
            return elem
    raise AssertionError(f"a láblécen nincs gomb: {szovegek}")


class TestIndulasiFigyelmeztetes:
    def test_az_ok_valodi_kattintassal_bezarja_a_figyelmeztetest(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, _controller, engine = parbeszed_app
        komponens = QQmlComponent(
            engine,
            QUrl.fromLocalFile(
                str(app_module._APP_DIR / "qml" / "PicasaPy" / "SplashScreen.qml")
            ),
        )
        splash = komponens.createWithInitialProperties({
            "version": "v0.0.0 (teszt)",
            "statusText": "kész",
            "ready": True,
            "confirmationRequired": True,
            "parent": window.contentItem(),
        })
        assert komponens.errors() == [], komponens.errors()
        assert splash is not None
        gomb = splash.findChild(QObject, "splashOkButton")
        assert _varj(qt_app, lambda: gomb is not None and gomb.isVisible()), (
            "a figyelmeztetés OK gombja nem látszik"
        )

        _klikk_ablakban(qt_app, window, gomb)

        assert _varj(qt_app, lambda: splash.property("confirmed") is True), (
            "az OK valódi kattintás nem erősítette meg a figyelmeztetést"
        )
        assert _varj(qt_app, lambda: splash.property("visible") is False), (
            "az OK után a figyelmeztetés nem záródott be"
        )


class TestKeszletTorles:
    def test_a_keszlet_torlese_valodi_kattintassal_megerositest_ker(
        self, gazda, qt_app, tmp_path  # noqa: F811
    ):
        view, ablak, vezerlo = gazda
        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")
        vezerlo.ujKeszlet("Második", str(tmp_path / "cel2"), "minden")
        QMetaObject.invokeMethod(ablak, "frissitsd")
        qt_app.processEvents()
        ablak.setProperty("kivalasztott", 0)  # előkészítés: a készlet kijelölése
        torles = ablak.findChild(QObject, "publishDeleteBackupSet")
        assert _varj(qt_app, lambda: torles.property("enabled") is True), (
            "a Készlet törlése kijelölés után sem aktív"
        )

        _klikk_ablakban(qt_app, view, torles)

        dialog = ablak.findChild(QObject, "backupDeleteDialog")
        assert _varj(qt_app, lambda: dialog is not None and dialog.property("visible") is True), (
            "a Készlet törlése nem kért megerősítést"
        )
        uzenet = ablak.findChild(QObject, "backupDeleteMessageLabel")
        assert "Külső" in str(uzenet.property("text")), "a megerősítő nem a kijelölt készletet nevezi meg"
