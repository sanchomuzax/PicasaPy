"""QML-funkcionális tesztek: a vágás-eszköz #448-as képarány-listája —
a beépített preset-lista a javított KULCSLISTÁT követi (ld. #448 jegy
2026-08-07-es kommentje), az egyéni arány felvétele/törlése a
`CustomAspectRatiosMixin`-en át a valódi AppControllerbe kötve (a mixin
`controller.py`-ba már be van drótozva, nincs szükség stub-controllerre,
a `test_folder_pane_collections_320.py` #320-as mintájával ellentétben,
ahol a bekötés még nem volt kész).

Az egyéni képarányok és az utolsó vágási arány beállításállapotot módosít,
ezért a fájl szándékosan funkció-szintű `qml_app` fixture-t használ."""

from __future__ import annotations

from PySide6.QtCore import QObject


def _open_viewer(window, qt_app, index=0):
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", index)
    qt_app.processEvents()
    return viewer


def _list_property(obj, name):
    """A QML `var`-tömb property Python-oldali olvasása — a
    `panel.property(...)` egy `QJSValue`-t ad vissza, amit explicit
    `.toVariant()` alakít Python listává (a `test_search.py` mintája)."""
    value = obj.property(name)
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return value


class TestAspectPresetKeys:
    """A VÁGÓ kulcskészlete — a #876 mérése szerint PONTOSAN 13 tétel.

    ⚠️ Ez az osztály korábban 19 kulcsot állított. Az a lista NEM tévedésből
    hízott meg: a #448 a `Picasa3i18n.dll` szövegtáblájából dolgozott, és a
    LEÍRÁS-sorok kulcsneveit külön tételnek olvasta. A #876 az erőforrás
    kulcs↔felirat tábláját (`Picasa3.exe`, 9143180–9144420. fájloffszet) vetette
    össze a `stringres-en-hu.tsv`-vel, és ebből derült ki, hogy hat tétel
    máshova tartozik:

    * `CurrentDisplay` — a KOLLÁZS „Oldalformátum" menüjéé;
    * `4x4` — a `Desktop4x3` leírás-kulcsa, ráadásul 1:1 (a `Square` mása);
    * `4x6`, `5x7`, `8x10`, `8.5x11` — a NYOMTATÁS méretlistájáé.

    A `20x25` viszont MARAD: azt három független forrás igazolja.
    """

    _EXPECTED_KEYS = [
        "Manual",
        "CurrentRatio",
        "5x8m",
        "9x13m",
        "10x15m",
        "Crop13x18m",
        "::Crop20x25m",
        "::A4",
        "Square",
        "Desktop4x3",
        "Widescreen",
        "HDTV16x9",
        "WideFrame",
    ]

    def test_builtin_preset_keys_match_the_corrected_list(self, qml_app, qt_app):
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None, "viewerEditorPanel nem található"
        presets = _list_property(panel, "aspectPresets")
        keys = [item["key"] for item in presets]
        assert keys == self._EXPECTED_KEYS

    def test_pontosan_tizenharom_tetel_es_a_hetedik_a_20x25(
        self, qml_app, qt_app
    ):
        """A darabszám és a SORREND is mérve — a 7. hely a `20x25`-é."""
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        presets = _list_property(panel, "aspectPresets")

        assert len(presets) == 13, [item["key"] for item in presets]
        assert presets[6]["key"] == "::Crop20x25m"
        assert presets[6]["label"] == "20x25"

    def test_a_20x25_aranya(self, qml_app, qt_app):
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        presets = {
            item["key"]: item for item in _list_property(panel, "aspectPresets")
        }
        assert presets["::Crop20x25m"]["ratio"] == 25 / 20 == 1.25

    def test_a_kepernyo_aranyok_felirata_KETTOSPONTOS(self, qml_app, qt_app):
        """A hivatalos magyar oszlop szerint a négy képernyő-arány
        kettősponttal áll, a nyomat-méretek `x`-szel — nálunk mind `x` volt."""
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        presets = {
            item["key"]: item for item in _list_property(panel, "aspectPresets")
        }
        assert presets["Desktop4x3"]["label"] == "4:3"
        assert presets["Widescreen"]["label"] == "16:10"
        assert presets["HDTV16x9"]["label"] == "16:9"
        assert presets["WideFrame"]["label"] == "5:3"
        # a nyomat-méretek viszont maradnak `x`-esek
        assert presets["9x13m"]["label"] == "9x13"
        assert presets["::Crop20x25m"]["label"] == "20x25"

    def test_az_A4_felirata_es_leirasa(self, qml_app, qt_app):
        """Nálunk „Full page (A4)" volt — az eredetiben a FELIRAT `A4`, és
        a „Teljes oldal" a LEÍRÁS-sor."""
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        presets = {
            item["key"]: item for item in _list_property(panel, "aspectPresets")
        }
        assert presets["::A4"]["label"] == "A4"
        assert presets["::A4"]["note"] == "Full page"
        assert presets["::A4"]["ratio"] == 297 / 210

    def test_a_hat_torolt_tetel_NINCS_a_vagoban(self, qml_app, qt_app):
        """Negatív állítás, névvel — hogy a visszacsúszás is kiderüljön."""
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        kulcsok = {
            item["key"] for item in _list_property(panel, "aspectPresets")
        }
        for torolt in ("CurrentDisplay", "4x4", "4x6", "5x7", "8x10",
                       "8.5x11", "FullPage"):
            assert torolt not in kulcsok, (
                f"a(z) {torolt!r} visszakerült a vágó listájába — "
                "az a nyomtatásé vagy a kollázsé, nem a vágóé"
            )

    def test_the_resolved_keys_carry_the_documented_ratio(self, qml_app, qt_app):
        """A leírás-sorok a HELYES tételekhez tartoznak (#876): a
        `16x10`/`5x3`/`16x9`/`4x4` kulcsnevek a `Widescreen`, `WideFrame`,
        `HDTV16x9`, `Desktop4x3` LEÍRÁSAI — nem külön tételek."""
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        presets = {
            item["key"]: item for item in _list_property(panel, "aspectPresets")
        }
        assert presets["Widescreen"]["note"] == "Widescreen monitor"
        assert presets["WideFrame"]["note"] == "Widescreen Photo Frame"
        assert presets["Square"]["note"] == "CD Cover"
        assert presets["Desktop4x3"]["note"] == "Standard screen"
        # az `Other` továbbra sem tétel: nálunk az egyéni arány felvétele
        # tölti be ezt a szerepet (AddCustomAspectRatio)
        assert "Other" not in presets

    def test_full_list_starts_with_the_builtin_presets(self, qml_app, qt_app):
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        full_list = _list_property(panel, "aspectFullList")
        assert [item["key"] for item in full_list] == self._EXPECTED_KEYS


class TestCustomAspectRatioAdd:
    def test_add_dialog_is_present(self, qml_app, qt_app):
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        dialog = panel.findChild(QObject, "addCustomAspectRatioDialog")
        assert dialog is not None, "addCustomAspectRatioDialog nem található"

    def test_created_signal_adds_ratio_via_controller(
        self, qml_app, qt_app
    ):
        window, controller, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        dialog = panel.findChild(QObject, "addCustomAspectRatioDialog")
        assert dialog is not None

        dialog.created.emit(4.0, 6.0, "Small print")
        qt_app.processEvents()

        assert controller.customAspectRatios == [
            {"name": "Small print", "width": 4.0, "height": 6.0}
        ]
        # a panel is látja az újonnan felvett arányt a beépítettek UTÁN
        full_list = _list_property(panel, "aspectFullList")
        assert full_list[-1]["label"] == "4 x 6   Small print"
        assert full_list[-1]["isCustom"] is True

    def test_created_ratio_becomes_selected_and_persists_as_last_crop_ratio(
        self, qml_app, qt_app
    ):
        window, controller, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        dialog = panel.findChild(QObject, "addCustomAspectRatioDialog")

        dialog.created.emit(4.0, 6.0, "Small print")
        qt_app.processEvents()

        full_list = _list_property(panel, "aspectFullList")
        assert panel.property("aspectIndex") == len(full_list) - 1
        assert controller.lastCropRatio == full_list[-1]["key"]


class TestCustomAspectRatioDelete:
    def test_delete_confirm_dialog_is_present_with_unique_name_prefix(
        self, qml_app, qt_app
    ):
        """A #448/#422 szabálya: minden ConfirmDialog-példány EGYEDI
        namePrefix-et kap — itt "deleteCustomAspectConfirm"."""
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        confirm = panel.findChild(QObject, "deleteCustomAspectConfirmDialog")
        assert confirm is not None, "deleteCustomAspectConfirmDialog nem található"

    def test_confirmed_signal_deletes_the_pending_ratio(self, qml_app, qt_app):
        window, controller, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        dialog = panel.findChild(QObject, "addCustomAspectRatioDialog")
        dialog.created.emit(4.0, 6.0, "Small print")
        qt_app.processEvents()
        assert controller.customAspectRatios != []

        confirm = panel.findChild(QObject, "deleteCustomAspectConfirmDialog")
        assert confirm is not None
        confirm.setProperty("pendingName", "Small print")
        confirm.setProperty("pendingWidth", 4.0)
        confirm.setProperty("pendingHeight", 6.0)
        confirm.confirmed.emit()
        qt_app.processEvents()

        assert controller.customAspectRatios == []


class TestElmentettToroltKulcs:
    """#876: a hat kikerült tétel valamelyikét MÁR ELMENTETTE valaki.

    A beállítás a QSettingsben marad, tehát a visszatöltés ismeretlen
    kulccsal fut le. A korábbi kód ilyenkor csak visszatért — az
    `aspectIndex` az ELŐZŐ képen használt értéken maradt, és a vágó egy
    néma, a listában nem látszó aránnyal nyílt volna.
    """

    def _open_crop(self, window, qt_app):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        return window.findChild(QObject, "viewerEditorPanel")

    def test_a_torolt_kulcs_Kezire_all_vissza(self, qml_app, qt_app):
        window, controller, _ = qml_app
        panel = self._open_crop(window, qt_app)
        panel.setProperty("aspectIndex", 5)  # bármi más, mint a Kézi

        controller.setLastCropRatio("4x6")  # a hat kikerült egyike
        panel.setProperty("cropActive", True)
        qt_app.processEvents()

        assert panel.property("aspectIndex") == 0, (
            "elmentett, azóta törölt kulcs után a vágónak »Kézi«-re kell "
            "állnia — nem az előző kép arányán maradnia"
        )

    def test_az_ervenyes_kulcs_valtozatlanul_visszaall(self, qml_app, qt_app):
        """A tartalék nem nyelheti el a MŰKÖDŐ visszatöltést."""
        window, controller, _ = qml_app
        panel = self._open_crop(window, qt_app)

        controller.setLastCropRatio("::Crop20x25m")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()

        presets = _list_property(panel, "aspectPresets")
        vart = [i["key"] for i in presets].index("::Crop20x25m")
        assert panel.property("aspectIndex") == vart


class TestCropSuggestionButtons:
    """#448: a vágás-panel HÁROM automatikus javaslat-gombja."""

    def _open_crop(self, window, qt_app):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        return viewer, panel

    def test_three_buttons_appear_with_labels(self, qml_app, qt_app):
        window, _, _ = qml_app
        _viewer, panel = self._open_crop(window, qt_app)
        row = window.findChild(QObject, "cropSuggestionRow")
        assert row is not None
        assert row.property("visible") is True
        for index in range(3):
            button = window.findChild(QObject, f"cropSuggestion{index}")
            assert button is not None, index
            assert str(button.property("label")), f"{index}. javaslat felirat nélkül"

    def test_choosing_a_suggestion_fills_the_selection(self, qml_app, qt_app):
        """A javaslat a KIJELÖLÉSBE kerül — nem alkalmazódik azonnal, hogy a
        felhasználó még igazíthasson rajta (Alkalmaz/Mégse változatlan)."""
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        _viewer, panel = self._open_crop(window, qt_app)
        overlay = window.findChild(QObject, "cropOverlay")
        assert overlay.property("hasSelection") is False

        QMetaObject.invokeMethod(
            window.findChild(QObject, "cropSuggestion0"),
            "buttonClicked", Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        assert overlay.property("hasSelection") is True

    def test_unknown_key_falls_back_to_the_key_itself(self, qml_app, qt_app):
        """A felirat-feloldás sosem ad üres gombot."""
        window, _, _ = qml_app
        _viewer, panel = self._open_crop(window, qt_app)
        assert panel.property("cropSuggestions") is not None


class TestCropSuggestionPreviews:
    """#448: minden javaslat-gomb a SAJÁT előnézeti bélyegképét mutatja.

    A bináris három javaslat-gombot ÉS három előnézetet ad
    (`editpanel/cropsug1..3` + `editpanel/cropsug_preview%d`) — a jegy
    2026-08-12-i kommentje szó szerint: „Három javaslat-gomb, mindegyikhez
    saját előnézeti kép". Felirat nélkül a felhasználó a kattintás előtt nem
    látja, mit kap; ez volt a #448 utolsó érdemi hiánya.

    Az előnézet NEM új képszolgáltató: a vágó-eszközben az `editpreview`
    amúgy is a VÁGATLAN képet mutatja (`enterCropTool` `clear_crop`-ot
    regisztrál), tehát a nagy előnézet URL-je pontosan az a kép, amire a
    javaslatok számoltak — a gomb ugyanezt az (URL szerint gyorsítótárazott)
    képet vágja a javasolt téglalapra."""

    def _open_crop(self, window, qt_app):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        return viewer, panel

    def test_every_suggestion_button_has_a_thumbnail(self, qml_app, qt_app):
        window, _, _ = qml_app
        _viewer, panel = self._open_crop(window, qt_app)
        suggestions = _list_property(panel, "cropSuggestions")
        assert suggestions, "javaslat nélkül a teszt nem mond semmit"

        for index in range(len(suggestions)):
            button = window.findChild(QObject, f"cropSuggestion{index}")
            assert button is not None, index
            source = str(button.property("thumbSource"))
            assert source.startswith("image://editpreview/"), (
                f"{index}. javaslat-gomb bélyegkép nélkül: {source!r}"
            )

    def test_the_thumbnail_shows_the_suggested_region(self, qml_app, qt_app):
        """A bélyegkép a JAVASOLT téglalapot mutatja, nem a teljes képet —
        különben mindhárom gomb ugyanazt a képet mutatná, és az előnézet
        semmit nem árulna el."""
        window, _, _ = qml_app
        _viewer, panel = self._open_crop(window, qt_app)
        suggestions = _list_property(panel, "cropSuggestions")
        assert suggestions

        for index, suggestion in enumerate(suggestions):
            button = window.findChild(QObject, f"cropSuggestion{index}")
            rect = button.property("thumbSourceRect")
            assert rect is not None, f"{index}. gombon nincs thumbSourceRect"
            assert rect.x() == suggestion["x"], index
            assert rect.y() == suggestion["y"], index
            assert rect.width() == suggestion["w"], index
            assert rect.height() == suggestion["h"], index

    def test_the_full_image_element_stays_unloaded_when_cropped(
        self, qml_app, qt_app
    ):
        """A vágott gombon a TELJES képet mutató elem nem tölt be semmit.

        A két bélyegkép-elem (`…Thumb` / `…ThumbCrop`) közül mindig csak az
        egyik kap forrást. Enélkül a több ezer pixeles szerkesztő-előnézet
        gombonként KÉTSZER töltődne be — háromszor három helyett hatszor."""
        window, _, _ = qml_app
        _viewer, panel = self._open_crop(window, qt_app)
        assert _list_property(panel, "cropSuggestions")

        full = window.findChild(QObject, "cropSuggestion0Thumb")
        cropped = window.findChild(QObject, "cropSuggestion0ThumbCrop")
        assert full is not None and cropped is not None
        # az Image.source egy QUrl, nem string — explicit toString() kell
        assert full.property("source").toString() == ""
        assert cropped.property("source").toString().startswith(
            "image://editpreview/"
        )

    def test_plain_buttons_keep_the_whole_image(self, qml_app, qt_app):
        """Visszalépés-védelem a 36 effekt-csempére (#338): a `thumbSourceRect`
        alapértéke a TELJES kép, tehát minden más PanelButton-hívó útja
        változatlan marad."""
        window, _, _ = qml_app
        self._open_crop(window, qt_app)
        button = window.findChild(QObject, "cropRotateButton")
        rect = button.property("thumbSourceRect")
        assert (rect.x(), rect.y(), rect.width(), rect.height()) == (0, 0, 1, 1)
