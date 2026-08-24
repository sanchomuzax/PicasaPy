"""Az „Exportálás mappába" párbeszéd FELÜLETE (#1138).

Az eredeti levezetése: `docs/specs/export-parbeszed.md` 1. (a `.fen`
leíró szó szerint), 3. (a kötések), 7. (a képminőség öt fokozata) és 9.
(a képernyőképről mért elrendezés) szakasza. A #1166 a MŰKÖDÉST már
bevitte; ez a fájl azt őrzi, ami a felületről maradt ki:

- a képméret **2 rádió + számmező + 7 fogásos csúszka**, a sor letiltva,
  amíg az „Eredeti méret használata" az aktív
  (`<bind attr="enabled" source="sizeradio"/>`);
- a képminőség **öt fokozat**, és a szám helyén **magyarázó szöveg**, ami
  a választással együtt vált (`<multi>`); csak az „Egyéni" alatt jelenik
  meg a **21 fogásos** csúszka (`min=0 max=20`);
- a vízjel **csoportcím + mező + kis betűs magyarázat**, a mező csak
  bejelölt jelölő mellett aktív;
- a hely `pathbox`-ként az ÚTVONALAT mutatja;
- a mappanév-mező fájlnév-szűrt, a méretmező csak számjegy.

A vezérlőkre HATUNK (kötött property / `toggle()`), nem a metódusokat
hívjuk: a közvetlen metódushívás akkor is zöld, ha a vezérlő
kattinthatatlan.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtGui import QValidator


def _elem(window, nev):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _megnyit(window, qt_app, sor=0):
    window.setProperty("selectedIndexes", [sor])
    window.setProperty("selectedIndex", sor)
    qt_app.processEvents()
    parbeszed = _elem(window, "exportDialog")
    QMetaObject.invokeMethod(
        parbeszed, "openForSelection", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    return parbeszed


def _valt(vezerlo, qt_app):
    """A jelölő/rádió ÁTKAPCSOLÁSA a saját vezérlőjén át."""
    QMetaObject.invokeMethod(vezerlo, "toggle", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


class TestKepmeret:
    """Spec 3.2: két rádió + `filter="digits"` mező + 7 fogásos csúszka."""

    def test_ket_radio_van_es_az_eredeti_meret_az_alapertelmezett(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)

        assert _elem(window, "exportSizeOriginalRadio").property("checked") is True
        assert _elem(window, "exportSizeResizeRadio").property("checked") is False

    def test_az_atmeretezo_sor_le_van_tiltva_amig_az_eredeti_az_aktiv(
        self, qml_app, qt_app
    ):
        """`<bind attr="enabled" source="sizeradio"/>` — a mező, a
        „képpont" felirat és a csúszka EGYÜTT szürkül."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)

        for nev in ("exportSizeField", "exportSizePixelsLabel", "exportSizeSlider"):
            assert _elem(window, nev).property("enabled") is False, nev

        _valt(_elem(window, "exportSizeResizeRadio"), qt_app)

        for nev in ("exportSizeField", "exportSizeSlider"):
            assert _elem(window, nev).property("enabled") is True, nev

    def test_a_csuszkanak_het_fogasa_van(self, qml_app, qt_app):
        """`<slider min="0" max="6" ticks="7" name="size"/>`."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)
        csuszka = _elem(window, "exportSizeSlider")

        assert csuszka.property("from") == 0
        assert csuszka.property("to") == 6
        assert csuszka.property("stepSize") == 1

    def test_a_csuszka_a_het_elobeallitast_irja_a_mezobe(self, qml_app, qt_app):
        """`<bind source="size" attr="title" list="320|480|…|1600"/>` — a
        csúszka mozgatása a HÉT előbeállítás egyikét teszi a mezőbe."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)
        csuszka = _elem(window, "exportSizeSlider")
        mezo = _elem(window, "exportSizeField")

        varhato = ["320", "480", "640", "800", "1024", "1200", "1600"]
        for index, ertek in enumerate(varhato):
            csuszka.setProperty("value", index)
            qt_app.processEvents()
            assert str(mezo.property("text")) == ertek

    def test_a_mezo_szabadon_irhato_es_a_csuszka_nem_korlatozza(
        self, qml_app, qt_app
    ):
        """Spec 9.3/4: a képernyőképen 1100 áll a mezőben, ami NINCS a hét
        előbeállítás között."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)
        mezo = _elem(window, "exportSizeField")

        mezo.setProperty("text", "1100")
        qt_app.processEvents()

        assert str(mezo.property("text")) == "1100"

    def test_a_meretmezo_csak_szamjegyet_fogad(self, qml_app, qt_app):
        """`filter="digits"` — betű nem írható be.

        A szűrőt a mező VALIDÁTORÁN mérjük: a `TextInput` a gépelést
        ezen engedi át (`finishChange` → `validate`). A `text` property
        PROGRAMOZOTT beállítása kikerüli a validátort, tehát azzal a
        szűrő hiánya sem látszana — néma őr lenne."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)
        mezo = _elem(window, "exportSizeField")

        szuro = mezo.property("validator")
        assert szuro is not None, "a méretmezőn nincs számjegy-szűrő"
        assert szuro.validate("12ab34", 0)[0] == QValidator.State.Invalid
        assert szuro.validate("1100", 0)[0] == QValidator.State.Acceptable


class TestKepminoseg:
    """Spec 3.3: öt fokozat, `<multi>` a legördülő MELLETT (spec 9.3/1)."""

    def test_ot_fokozat_van(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)
        legordulo = _elem(window, "exportQualityPreset")

        assert legordulo.property("count") == 5

    def test_a_magyarazo_szoveg_a_valasztassal_egyutt_valt(self, qml_app, qt_app):
        """A négy magyarázat a `.fen` `<multi>` gyerekeiből, szó szerint."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)
        legordulo = _elem(window, "exportQualityPreset")
        hint = _elem(window, "exportQualityHint")

        varhato = [
            "Preserves original image quality",
            "Good balance of quality and size",
            "Very large file size, preserves fine detail",
            "Smallest file size, some quality loss",
        ]
        for index, szoveg in enumerate(varhato):
            legordulo.setProperty("currentIndex", index)
            qt_app.processEvents()
            assert str(hint.property("text")) == szoveg
            assert hint.property("visible") is True

    def test_csak_az_egyeni_alatt_van_csuszka(self, qml_app, qt_app):
        """➡️ A minőség száma CSAK az „Egyéni" alatt állítható, és
        CSÚSZKÁVAL, nem számmezővel."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)
        legordulo = _elem(window, "exportQualityPreset")
        csuszka = _elem(window, "exportQualitySlider")

        legordulo.setProperty("currentIndex", 1)  # Normál
        qt_app.processEvents()
        assert csuszka.property("visible") is False

        legordulo.setProperty("currentIndex", 4)  # Egyéni
        qt_app.processEvents()
        assert csuszka.property("visible") is True
        assert _elem(window, "exportQualityHint").property("visible") is False

    def test_a_csuszkanak_21_fogasa_van(self, qml_app, qt_app):
        """`<slider min="0" max="20" ticks="21" name="qualslider"/>`."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)
        csuszka = _elem(window, "exportQualitySlider")

        assert csuszka.property("from") == 0
        assert csuszka.property("to") == 20
        assert csuszka.property("stepSize") == 1

    def test_nincs_kulon_minoseg_szammezo(self, qml_app, qt_app):
        """A tulajdonos kifogása: „a tömörítés mértéke (85) nem is
        állítható" — a régi, mindig látszó SpinBox-nak nem szabad
        léteznie."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)

        assert window.findChild(QObject, "exportQuality") is None, (
            "a régi, nem állítható minőség-számmező még mindig ott van"
        )

    def test_az_egyeni_felirata_a_csuszka_szamat_mutatja(self, qml_app, qt_app):
        """`„Custom (%d)"` (`0x00cafa98`, formázó `0x0073a0c0`) — a szám a
        csúszka mozgatásakor AZONNAL frissül; minőség = állás × 5."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)
        legordulo = _elem(window, "exportQualityPreset")
        csuszka = _elem(window, "exportQualitySlider")

        legordulo.setProperty("currentIndex", 4)
        csuszka.setProperty("value", 17)
        qt_app.processEvents()

        assert "85" in str(legordulo.property("currentText")), (
            legordulo.property("currentText")
        )

        csuszka.setProperty("value", 12)
        qt_app.processEvents()

        assert "60" in str(legordulo.property("currentText"))
        assert legordulo.property("currentIndex") == 4, (
            "a felirat frissítése átállította a kiválasztott fokozatot"
        )


class TestVizjel:
    """Spec 3.5: csoportcím + jelölő + mező + KIS BETŰS magyarázat."""

    def test_a_mezo_csak_bejelolt_jelolo_mellett_aktiv(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)
        mezo = _elem(window, "exportWatermarkField")

        assert mezo.property("enabled") is False

        _valt(_elem(window, "exportWatermarkCheck"), qt_app)

        assert mezo.property("enabled") is True

    def test_van_csoportcim_es_kis_betus_magyarazat(self, qml_app, qt_app):
        """`labelgroup39.title` = „Vízjel:" + `label44` `size="small"`."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)

        cimke = _elem(window, "exportWatermarkLabel")
        assert str(cimke.property("text")) == "Watermark:"

        magyarazat = _elem(window, "exportWatermarkHint")
        assert str(magyarazat.property("text")) == (
            "Stamp photos with your name, a web domain, or a copyright notice."
        )
        assert magyarazat.property("font").pixelSize() < cimke.property(
            "font"
        ).pixelSize(), 'a magyarázat nem kisebb betűs (`size="small"`)'


class TestHelyEsNev:
    def test_a_hely_pathboxkent_az_utvonalat_mutatja(self, qml_app, qt_app):
        """Spec 5: nálunk „(nincs kiválasztva)" szöveg állt; a `.fen`-ben
        `pathbox`, ami az ÚTVONALAT mutatja."""
        window, _controller, _engine = qml_app
        parbeszed = _megnyit(window, qt_app)
        doboz = _elem(window, "exportLocationBox")

        assert str(doboz.property("text")), "a hely mezője üres"
        assert str(parbeszed.property("targetFolder")).endswith(
            str(doboz.property("text")).replace("\\", "/").split("/")[-1]
        )

    def test_a_mappanev_mezo_kap_fokuszt_kijelolt_tartalommal(
        self, qml_app, qt_app
    ):
        """`focus="name"` + a képernyőkép: a szöveg kék, azaz kijelölt."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)
        mezo = _elem(window, "exportFolderNameField")

        assert mezo.property("activeFocus") is True
        assert str(mezo.property("selectedText")) == str(mezo.property("text"))

    def test_a_mappanev_fajlnev_szurt(self, qml_app, qt_app):
        """`filter="filename"` — a Windows tiltott halmaza
        (`0x009946f0`: `\\ / : * ? " < > |`) nem írható be.

        A validátoron mérünk, nem a `text` programozott beállításán —
        ld. a méretmező tesztjének indoklását."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)
        mezo = _elem(window, "exportFolderNameField")

        szuro = mezo.property("validator")
        assert szuro is not None, "a mappanév-mezőn nincs fájlnév-szűrő"
        for tiltott in '\\/:*?"<>|':
            assert szuro.validate(f"a{tiltott}b", 0)[0] == QValidator.State.Invalid, (
                f"a {tiltott!r} átment a fájlnév-szűrőn"
            )
        assert szuro.validate("nyaralas 2026", 0)[0] == QValidator.State.Acceptable


class TestFilmCsoport:
    def test_a_csoportcimke_is_szurkul_film_nelkul(self, qml_app, qt_app):
        """Spec 13.10: a korábbi „a címke fekete marad" megfigyelés TÉVES
        volt — a csoport a címkéjével EGYÜTT tiltott."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)

        cimke = _elem(window, "exportMovieLabel")
        assert cimke.property("enabled") is False


class TestMegorzottBeallitasok:
    def test_a_parbeszed_a_mentett_allapotbol_indul(self, qml_app, qt_app):
        """Spec 4.: a párbeszéd MEGJEGYZI az előző választást."""
        window, controller, _engine = qml_app
        controller.saveExportSettings({
            "size": 6,
            "customSize": 1100,
            "resize": True,
            "qualityType": 3,
            "quality": 40,
            "addNumbers": True,
            "watermark": True,
            "watermarkText": "© PicasaPy",
        })

        _megnyit(window, qt_app)

        assert _elem(window, "exportSizeResizeRadio").property("checked") is True
        assert str(_elem(window, "exportSizeField").property("text")) == "1100"
        assert _elem(window, "exportSizeSlider").property("value") == 6
        assert _elem(window, "exportQualityPreset").property("currentIndex") == 3
        assert _elem(window, "exportQualitySlider").property("value") == 8  # 40/5
        assert _elem(window, "exportAddNumbersCheck").property("checked") is True
        assert _elem(window, "exportWatermarkCheck").property("checked") is True
        assert str(_elem(window, "exportWatermarkField").property("text")) == (
            "© PicasaPy"
        )

    def test_az_elfogadas_kiirja_a_beallitasokat(self, qml_app, qt_app, tmp_path):
        """Spec 13.7: EGYETLEN menetben, az elfogadáskor."""
        window, controller, _engine = qml_app
        parbeszed = _megnyit(window, qt_app)
        parbeszed.setProperty("targetFolder", str(tmp_path / "ki"))
        _valt(_elem(window, "exportSizeResizeRadio"), qt_app)
        _elem(window, "exportSizeSlider").setProperty("value", 0)
        _elem(window, "exportQualityPreset").setProperty("currentIndex", 2)
        _valt(_elem(window, "exportAddNumbersCheck"), qt_app)
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            parbeszed, "accept", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert controller.waitForBackgroundWorkers(30.0)

        mentett = controller.exportSettings()
        assert mentett["resize"] is True
        assert mentett["size"] == 0
        assert mentett["customSize"] == 320
        assert mentett["qualityType"] == 2
        assert mentett["addNumbers"] is True

    def test_a_megse_nem_ir_ki_semmit(self, qml_app, qt_app):
        """Spec 13.7: a Mégse ága az üres tő — sem nem ment, sem nem
        állít vissza."""
        window, controller, _engine = qml_app
        parbeszed = _megnyit(window, qt_app)
        _valt(_elem(window, "exportAddNumbersCheck"), qt_app)

        QMetaObject.invokeMethod(
            parbeszed, "reject", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert controller.exportSettings()["addNumbers"] is False


class TestAtmeretezesVegponttolVegpontig:
    def test_a_mezobe_irt_meret_ervenyesul_az_exportban(
        self, qml_app, qt_app, tmp_path
    ):
        """A hét előbeállításon KÍVÜLI, kézzel írt méret is hasson —
        különben a csúszka csak látszatvezérlő lenne."""
        window, controller, _engine = qml_app
        parbeszed = _megnyit(window, qt_app)
        cel = tmp_path / "ki"
        parbeszed.setProperty("targetFolder", str(cel))
        _valt(_elem(window, "exportSizeResizeRadio"), qt_app)
        _elem(window, "exportSizeField").setProperty("text", "48")
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            parbeszed, "accept", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert controller.waitForBackgroundWorkers(30.0)
        qt_app.processEvents()

        from PIL import Image

        nev = str(_elem(window, "exportFolderNameField").property("text"))
        kimenetek = sorted((cel / nev).glob("*.jpg"))
        assert kimenetek, f"nem született kimenet: {list(cel.rglob('*'))}"
        with Image.open(kimenetek[0]) as kep:
            assert max(kep.size) == 48
