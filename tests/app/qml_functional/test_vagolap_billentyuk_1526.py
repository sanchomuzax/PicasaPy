"""#1526: a Ctrl+X / Ctrl+C / Ctrl+V VALÓDI billentyűként — és az, hogy nem
veszik el a szövegmezőktől.

## Miért kellett ez a kör

A menü eddig is HIRDETTE a Ctrl+X/C/V-t, de a három tétel helyfoglaló volt,
tehát a hazug felirat senkit nem zavart. Az élővé tételükkel a
`test_qml_menubar_audit.TestMukodoTetelekBillentyui` őre kibukott: *működő
menüpont nem ígérhet olyan billentyűt, ami nem él.*

## A mérés, ami eldöntötte (2026-08-27, offscreen, valódi `QTest.keyClick`)

A kézenfekvő feltevés — „egy ablak-hatókörű `Shortcut` elvenné a Ctrl+C-t a
szövegmezőktől, tehát nem szabad bekötni" — **HAMIS**:

| fókusz | tüzel-e a `Shortcut` | a mező saját művelete |
|---|---|---|
| szerkeszthető `TextField` / `TextArea` | **nem** | lefut |
| `readOnly: true` mező | **igen** ⚠️ | elmarad |
| rács (nem szövegelem) | igen | – |

A Qt tehát magától megvédi a SZERKESZTHETŐ mezőt (a fókuszált szövegelem a
`ShortcutOverride` eseményen elveszi a szabványos szerkesztő-billentyűket),
a CSAK-OLVASHATÓT viszont nem. Négy ilyen mezőnk van — mind útvonal-kijelző
a Beállítások és az Export párbeszédben —, és ott a Ctrl+C a képfájlokat
tenné a vágólapra a kijelölt útvonal helyett. Ezt zárja ki a menüsáv
`textInputHasFocus` őre.

Ez a fájl **mind a három fókuszállapotra** mér, valódi billentyűeseménnyel,
és a hatást a vágólapon, illetve a mező tartalmán nézi — nem a jelzésen.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QMimeData, QObject, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest

from picasapy.fileops.clipboard import (
    COPY,
    CUT,
    GNOME_COPIED_FILES,
    URI_LIST,
    parse_gnome_payload,
    paths_from_uri_list,
)


def _elem(root, nev: str) -> QObject:
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _fokusz(window, qt_app, nev: str) -> QObject:
    elem = _elem(window, nev)
    QMetaObject.invokeMethod(
        elem, "forceActiveFocus", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    assert elem.property("activeFocus") is True, (
        f"a(z) {nev} nem kapta meg a fókuszt — a mérés értelmetlen volna"
    )
    return elem


def _billentyu(window, qt_app, kulcs) -> None:
    QTest.keyClick(window, kulcs, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()


def _vagolap_utak() -> list[Path]:
    adat = QGuiApplication.clipboard().mimeData()
    if adat is None or not adat.hasFormat(URI_LIST):
        return []
    return paths_from_uri_list(bytes(adat.data(URI_LIST)))


def _vagolap_muvelet() -> str:
    adat = QGuiApplication.clipboard().mimeData()
    if adat is None or not adat.hasFormat(GNOME_COPIED_FILES):
        return ""
    return parse_gnome_payload(bytes(adat.data(GNOME_COPIED_FILES)))[0]


def _vagolapra_fajl(utak, muvelet: str) -> None:
    csomag = QMimeData()
    csomag.setUrls([QUrl.fromLocalFile(str(u)) for u in utak])
    sorok = [muvelet, *(QUrl.fromLocalFile(str(u)).toString() for u in utak)]
    csomag.setData(GNOME_COPIED_FILES, "\n".join(sorok).encode("utf-8"))
    QGuiApplication.clipboard().setMimeData(csomag)


def _mappa(controller) -> Path:
    return Path(str(controller.photos.filePathAt(0))).parent


class TestARacsonAzKEPEKREHat:
    """Nem szövegmezőn állva a három billentyű a KÉPEKRE hat."""

    def test_ctrl_c_a_kepfajlokat_teszi_a_vagolapra(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        QGuiApplication.clipboard().clear()
        _kijelol(window, qt_app, [0])
        _fokusz(window, qt_app, "photoGrid")
        vart = Path(str(controller.photos.filePathAt(0)))

        _billentyu(window, qt_app, Qt.Key.Key_C)

        assert _vagolap_utak() == [vart]
        assert _vagolap_muvelet() == COPY

    def test_ctrl_x_mozgatas_jelzest_ad(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        QGuiApplication.clipboard().clear()
        _kijelol(window, qt_app, [0])
        _fokusz(window, qt_app, "photoGrid")

        _billentyu(window, qt_app, Qt.Key.Key_X)

        assert _vagolap_muvelet() == CUT

    def test_ctrl_v_beilleszti_a_fajlt_a_mappaba(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        cel = _mappa(controller)
        idegen = tmp_path / "billentyuvel.jpg"
        idegen.write_bytes(b"\xff\xd8\xff\xd9")
        _vagolapra_fajl([idegen], COPY)
        _fokusz(window, qt_app, "photoGrid")

        _billentyu(window, qt_app, Qt.Key.Key_V)

        assert (cel / "billentyuvel.jpg").exists()


class TestSzerkesztehetoMezonAMEZORHat:
    """Szerkeszthető szövegmezőn állva a billentyűk a MEZŐÉI maradnak."""

    def test_ctrl_c_a_mezo_szoveget_masolja_nem_a_kepeket(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        QGuiApplication.clipboard().clear()
        _kijelol(window, qt_app, [0])  # van kijelölés: a parancs ÉLNE
        mezo = _fokusz(window, qt_app, "searchField")
        mezo.setProperty("text", "keresett szoveg")
        QMetaObject.invokeMethod(
            mezo, "selectAll", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        _billentyu(window, qt_app, Qt.Key.Key_C)

        assert QGuiApplication.clipboard().text() == "keresett szoveg"
        assert _vagolap_utak() == [], "a Ctrl+C elvette a szövegmezőtől!"

    def test_ctrl_x_a_mezobol_vag_ki(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        mezo = _fokusz(window, qt_app, "searchField")
        mezo.setProperty("text", "kivagando")
        QMetaObject.invokeMethod(
            mezo, "selectAll", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        _billentyu(window, qt_app, Qt.Key.Key_X)

        assert mezo.property("text") == ""
        assert QGuiApplication.clipboard().text() == "kivagando"
        assert _vagolap_utak() == []

    def test_ctrl_v_a_mezobe_illeszt_es_nem_hoz_fajlt(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        cel = _mappa(controller)
        elotte = sorted(p.name for p in cel.iterdir())
        QGuiApplication.clipboard().setText("beillesztett")
        mezo = _fokusz(window, qt_app, "searchField")
        mezo.setProperty("text", "")
        qt_app.processEvents()

        _billentyu(window, qt_app, Qt.Key.Key_V)

        assert mezo.property("text") == "beillesztett"
        assert sorted(p.name for p in cel.iterdir()) == elotte


class TestCsakOlvashatoMezo:
    """A csak-olvasható mező VÉGEREDMÉNYE: a Ctrl+C az ÚTVONALAT másolja.

    ⚠️ Ez a teszt a felhasználói viselkedést rögzíti, **nem a
    `textInputHasFocus` őr bizonyítéka** — azt a
    `test_szovegmezo_fokuszban_MIND_A_HAROM_tiltott` méri (mutációval
    igazolva). A különbséget mérés derítette ki (2026-08-27):

    * bare `readOnly` mezőn (mérőpad) a `Shortcut` TÜZEL, tehát a
      képfájlok mennének a vágólapra az útvonal helyett — ez a valódi
      kockázat, amit az őr kizár;
    * a termékben viszont MIND A NÉGY csak-olvasható mező takarásban van:
      három a Beállítások önálló `Window`-jában (oda a főablak
      `Shortcut`-jai el sem érnek), a negyedik — ez itt — MODÁLIS `Dialog`
      popupban, ami szintén elnyeli a billentyűt. Mérve: az őr KIVÉTELÉVEL
      is az útvonal került a vágólapra.

    Az őr tehát ma VÉDEKEZŐ: a mérőpadon bizonyítottan valódi hibaosztályt
    zár ki, a mai felületen viszont nincs olyan út, ahol hatna. Ezért marad
    benne — egy jövőbeli, nem-modális csak-olvasható mező (pl. egy panelbe
    tett útvonal-kijelző) azonnal a hibás ágra futna nélküle."""

    def test_ctrl_c_a_MEZO_szoveget_masolja_nem_a_kepeket(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        QGuiApplication.clipboard().clear()
        _kijelol(window, qt_app, [0])
        # az export-párbeszédet a VALÓDI menüponton át nyitjuk meg
        QMetaObject.invokeMethod(
            _elem(window, "menuFileExport"),
            "triggered",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        mezo = _fokusz(window, qt_app, "exportLocationBox")
        assert mezo.property("readOnly") is True
        QMetaObject.invokeMethod(
            mezo, "selectAll", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        szoveg = mezo.property("text")
        assert szoveg, "a célmappa-mező üres — a mérés értelmetlen volna"

        _billentyu(window, qt_app, Qt.Key.Key_C)

        assert _vagolap_utak() == [], (
            "csak-olvasható mezőn a Ctrl+C a képfájlokat tette a vágólapra"
        )
        assert QGuiApplication.clipboard().text() == szoveg


class TestABillentyukAllapota:
    """A `Shortcut` objektumok engedélyezettsége ugyanazon a feltételen áll,
    mint a menüpontoké — plusz a fókusz-őrön."""

    def test_kijeloles_nelkul_a_masolas_es_kivagas_TILTOTT(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [])
        _fokusz(window, qt_app, "photoGrid")
        assert _elem(window, "shortcutCut").property("enabled") is False
        assert _elem(window, "shortcutCopy").property("enabled") is False

    def test_szovegmezo_fokuszban_MIND_A_HAROM_tiltott(self, qml_app, qt_app,
                                                       tmp_path):
        window, _controller, _engine = qml_app
        idegen = tmp_path / "van.jpg"
        idegen.write_bytes(b"\xff\xd8\xff\xd9")
        _vagolapra_fajl([idegen], COPY)
        _kijelol(window, qt_app, [0])
        _fokusz(window, qt_app, "searchField")
        for nev in ("shortcutCut", "shortcutCopy", "shortcutPaste"):
            assert _elem(window, nev).property("enabled") is False, nev

    def test_racs_fokuszban_MIND_A_HAROM_elo(self, qml_app, qt_app, tmp_path):
        """Kontroll-mérés: az előző teszt tiltása csak ehhez képest bizonyít."""
        window, _controller, _engine = qml_app
        idegen = tmp_path / "van.jpg"
        idegen.write_bytes(b"\xff\xd8\xff\xd9")
        _vagolapra_fajl([idegen], COPY)
        _kijelol(window, qt_app, [0])
        _fokusz(window, qt_app, "photoGrid")
        for nev in ("shortcutCut", "shortcutCopy", "shortcutPaste"):
            assert _elem(window, nev).property("enabled") is True, nev

    def test_a_hirdetett_billentyu_es_a_bekotes_egyezik(self, qml_app, qt_app):
        """A menüfelirat és a `Shortcut` nem csúszhat el egymástól."""
        window, _controller, _engine = qml_app
        for nev, sorozat, tetel in (
            ("shortcutCut", "Ctrl+X", "menuEditCut"),
            ("shortcutCopy", "Ctrl+C", "menuEditCopy"),
            ("shortcutPaste", "Ctrl+V", "menuEditPaste"),
        ):
            assert str(_elem(window, nev).property("sequence")) == sorozat
            assert sorozat in _elem(window, tetel).property("text")
