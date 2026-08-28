"""Öt hirdetett-de-néma menü-gyorsbillentyű (#1616).

## A mai állapot MÉRVE (nem a jegy szövege alapján készpénznek véve)

A jegy öt billentyűt sorolt fel. Két közülük már megoldódott, MIELŐTT ez a
jegy sorra került:

- `Ctrl+M` (Importálás forrása…) — a #1615 kötötte be;
- `Ctrl+O` (Fájl felvétele a Picasába…) — a #1633 kötötte be.

A maradék három közül a jegy szövege **tévesen** állította, hogy a
`Ctrl+N` (Új album…) menütétele már ÉLŐ, csak a billentyű néma — MÉRVE
(`git log -S'menuFileNewAlbum' -- .../PicasaMenuBar.qml`) a tétel MINDIG
`PicasaMenuItem { placeholder: true }` volt, a menüsáv legelső verziója
(#416) óta. A funkció maga viszont NEM hiányzott: a „Új album…" dialógus
(`newAlbumDialog`, `FileOpsDialogs.qml`) és a `controller.createAlbum`
már éles és tesztelt úton működik a rács helyi menüjéből
(`test_album_context_menu.py::TestNewAlbumDialog`) — csak a Fájl-menü és a
`Ctrl+N` nem vezetett hozzá. Ugyanaz a hibaosztály, mint a #1615/#1633:
hiányzó BEKÖTÉS, nem hiányzó funkció — ezért itt a `Ctrl+N`-t is
BEKÖTÖTTÜK, ugyanarra a belépőre.

A másik két maradék tételnél (`Ctrl+Shift+O` — Fájl(ok) megnyitása
szerkesztőben; `Ctrl+E` — E-mail…) a mérés megerősítette, hogy a
mögöttes funkció TELJESEN hiányzik (a `TrayBar.emailRequested()` jelzés
sehova nincs kötve, az „Open File(s) in Editor" funkciónak pedig nyoma
sincs a kódban) — ezekben a `\\t`-tal jelölt gyorsbillentyű LEKERÜLT a
feliratról, a jegy saját szabálya szerint („ha a funkció nincs kész, a
feliratból vedd ki a gyorsbillentyűt — ne hirdessünk olyat, ami nincs").

## Miért ilyenek ezek a tesztek

A `TestUjAlbumMenupontEsCtrlN` osztály a #1615/#1616 mintáját követi: a
tényleges felületi vezérlőn megy végig (`onTriggered` kiváltása +
`QTest.keyClick` a billentyűre), nem a jelzés közvetlen kibocsátásával —
a helyfoglaló tételen a `triggered` metódus közvetlen hívása „sikerülne"
úgy is, hogy a felhasználó rá sem tud kattintani (ld. `MEMORY.md`:
„a vezérlőre KATTINTS, ne a metódust hívd").

A `TestSweepOr` osztály a jegy 6. pontja: egy ÁLTALÁNOS őr, ami a teljes
menüsávot végigjárja, és minden ÉLŐ (nem helyfoglaló, nem nyugdíjazott)
menütételnél megköveteli, hogy a feliratban hirdetett gyorsbillentyűhöz
tartozzon élő `Shortcut` valahol az app QML-fáján (a `Shortcut` gyakran
MÁSIK fájlban él, pl. `Main.qml`, ezért az egész `qml/` fát nézi, nem csak
a menüsávot). A helyfoglaló tételek (a spec 472–480. sorának kilenc
további esete: `Ctrl+X/C/V/I/3`, `F1`, stb.) SZÁNDÉKOSAN nem számítanak
bele — azok külön jegy hatókörébe tartoznak (ld. a #1616 jegy „Nyitott
kérdések mérlege" szakasza).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest

import picasapy.app

_APP_DIR = Path(picasapy.app.__file__).parent
_QML_DIR = _APP_DIR / "qml"
_MENU_QML = _QML_DIR / "PicasaPy" / "PicasaMenuBar.qml"


def _elem(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _select_row(window, qt_app, row):
    window.setProperty("selectedIndexes", [row])
    window.setProperty("selectedIndex", row)
    qt_app.processEvents()


def _clear_selection(window, qt_app):
    window.setProperty("selectedIndexes", [])
    window.setProperty("selectedIndex", -1)
    qt_app.processEvents()


class TestUjAlbumMenupontEsCtrlN:
    """A Fájl ▸ Új album… tétel és a `Ctrl+N` ÉLŐ, kijelöléshez kötve."""

    def test_a_tetel_nem_helyfoglalo_kijeloles_mellett(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _select_row(window, qt_app, 0)

        tetel = _elem(window, "menuFileNewAlbum")
        # sima `MenuItem`-nek nincs `placeholder` tulajdonsága — a
        # `property()` ilyenkor érvénytelen (None) `QVariant`-ot ad
        assert not tetel.property("placeholder"), (
            "az Új album… menüpont még mindig helyfoglaló (#1616)"
        )
        assert tetel.property("enabled") is True

    def test_kijeloles_nelkul_a_tetel_letiltott(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _clear_selection(window, qt_app)

        tetel = _elem(window, "menuFileNewAlbum")
        assert tetel.property("enabled") is False, (
            "kijelölés nélkül a createAlbum úgysem hoz létre semmit — "
            "a tétel maradjon szürke, mint a többi kijelölés-függő tétel"
        )

    def test_a_felirat_a_hirdetett_billentyut_is_tartalmazza(self, qml_app):
        window, _controller, _engine = qml_app
        # kiírt literál — nem a termékből származtatva (#1576 tanulsága)
        assert str(_elem(window, "menuFileNewAlbum").property("text")) == (
            "New Album...\tCtrl+N"
        )

    def test_a_menupontra_kattintva_megnyilik_a_dialog(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _select_row(window, qt_app, 0)
        dialog = _elem(window, "newAlbumDialog")
        assert dialog.property("visible") is False

        tetel = _elem(window, "menuFileNewAlbum")
        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert dialog.property("visible") is True, (
            "a Fájl ▸ Új album… nem nyitotta meg a dialógust"
        )

    def test_a_ctrl_n_valodi_billentyuvel_megnyitja_a_dialogot(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        _select_row(window, qt_app, 0)
        dialog = _elem(window, "newAlbumDialog")
        assert dialog.property("visible") is False

        QTest.keyClick(window, Qt.Key_N, Qt.ControlModifier)
        qt_app.processEvents()

        assert dialog.property("visible") is True, (
            "a Ctrl+N nem nyitotta meg az Új album… dialógust"
        )

    def test_kijeloles_nelkul_a_ctrl_n_nem_csinal_semmit(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _clear_selection(window, qt_app)
        dialog = _elem(window, "newAlbumDialog")

        QTest.keyClick(window, Qt.Key_N, Qt.ControlModifier)
        qt_app.processEvents()

        assert dialog.property("visible") is False, (
            "a Ctrl+N kijelölés nélkül is megnyitotta a dialógust"
        )

    def test_a_gyorsbillentyu_elo_es_a_sorozata_a_hirdetett(self, qml_app):
        window, _controller, _engine = qml_app
        rovidites = _elem(window, "shortcutNewAlbum")
        # kiírt literál — nem a menüfeliratból származtatva
        assert str(rovidites.property("sequence")) == "Ctrl+N"

    def test_a_ctrl_n_a_keresomezoben_allva_is_hat(self, qml_app, qt_app):
        """⚠️ MÉRT, nem feltevés (#1526/#1571 hibaosztálya, ugyanúgy, mint
        a #1615 `Ctrl+M`-nél): a `Ctrl+N` nem szerkesztő-billentyű, tehát a
        `QQuickTextInput` a `ShortcutOverride`-ban nem tartja vissza — az
        ablak-szintű `Shortcut` a mezőben állva is győz."""
        window, _controller, _engine = qml_app
        _select_row(window, qt_app, 0)
        mezo = _elem(window, "searchField")
        mezo.setProperty("focus", True)
        qt_app.processEvents()
        assert mezo.property("activeFocus") is True, (
            "a keresőmező nem kapott fókuszt — a mérés nem érvényes"
        )

        QTest.keyClick(window, Qt.Key_N, Qt.ControlModifier)
        qt_app.processEvents()

        dialog = _elem(window, "newAlbumDialog")
        assert dialog.property("visible") is True, (
            "a Ctrl+N a keresőmezőben állva elveszett"
        )
        assert str(mezo.property("text")) == "", (
            "a Ctrl+N karaktert írt a keresőmezőbe"
        )

    def test_a_puszta_n_a_mezobe_kerul_es_nem_nyit_semmit(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _select_row(window, qt_app, 0)
        mezo = _elem(window, "searchField")
        mezo.setProperty("focus", True)
        qt_app.processEvents()
        assert mezo.property("activeFocus") is True

        QTest.keyClick(window, Qt.Key_N, Qt.KeyboardModifier.NoModifier)
        qt_app.processEvents()

        assert str(mezo.property("text")) == "n"
        assert _elem(window, "newAlbumDialog").property("visible") is False

    def test_a_menupont_nem_placeholder_a_forrasban(self):
        forras = _MENU_QML.read_text(encoding="utf-8")
        tetel = re.search(
            r"MenuItem\s*\{[^}]*?menuFileNewAlbum[^}]*?\}", forras, re.S
        )
        assert tetel is not None, (
            "a menuFileNewAlbum tétel nem MenuItem a forrásban"
        )
        blokk = tetel.group(0)
        assert "placeholder" not in blokk, (
            "a tétel visszakerült helyfoglalóra (#1616)"
        )
        assert "newAlbumRequested()" in blokk

    @pytest.mark.parametrize(
        "nev", ["menuFileNewAlbum", "shortcutNewAlbum", "newAlbumDialog"]
    )
    def test_a_lanc_minden_szeme_megvan(self, qml_app, nev):
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, nev) is not None, nev


class TestNemaCimkekLekerultBillentyuvel:
    """A `Ctrl+Shift+O` és a `Ctrl+E` — a funkció hiányzik, a felirat
    ezért többé NEM hirdet billentyűt. A tétel helyfoglaló MARAD (a
    funkció megvalósítása külön jegy — ld. a spec 472–480. sora)."""

    @pytest.mark.parametrize(
        ("szoveg_resz", "vart_szoveg"),
        [
            ("Open File(s) in Editor", "Open File(s) in Editor"),
            ("E-Mail...", "E-Mail..."),
        ],
    )
    def test_a_felirat_mar_nem_hirdet_billentyut(
        self, qml_app, szoveg_resz, vart_szoveg
    ):
        window, _controller, _engine = qml_app
        talalat = None
        for obj in window.findChildren(QObject):
            try:
                szoveg = obj.property("text")
            except Exception:  # pragma: no cover - defenzív
                continue
            if szoveg is not None and str(szoveg) == vart_szoveg:
                talalat = obj
                break
        assert talalat is not None, f"nincs '{vart_szoveg}' feliratú tétel"
        assert "\t" not in str(talalat.property("text")), (
            f"a(z) '{vart_szoveg}' felirat még mindig hirdet gyorsbillentyűt"
        )
        # a tétel a funkció hiánya miatt továbbra is helyfoglaló
        assert talalat.property("placeholder") is True

    def test_sem_a_ctrl_shift_o_sem_a_ctrl_e_nem_elo_billentyu(self):
        """Forrás-alapú ellenőrzés: az app teljes QML-fáján SEHOL nem él
        `Shortcut { sequence: "Ctrl+Shift+O" }` vagy `"Ctrl+E"` — a
        felirat eltávolítása nem hagyott árva `Shortcut`-ot sem."""
        elo = _osszes_elo_billentyu_szekvencia()
        assert "Ctrl+Shift+O" not in elo
        assert "Ctrl+E" not in elo


# ---------------------------------------------------------------------------
# TestSweepOr — a jegy 6. pontja: a HIBAOSZTÁLY generikus őre.
#
# Tisztán szöveg-/regex-alapú (nem tölt be QML-motort), hogy a mutációkat
# BIZTONSÁGOSAN, a valódi fájlok módosítása nélkül lehessen bemutatni: a
# forrást stringként olvassuk be, majd a mutált MÁSOLATOT adjuk a
# ellenőrző függvénynek — a lemezen lévő fájl változatlan marad.
# ---------------------------------------------------------------------------

_ITEM_RE = re.compile(
    r"(?P<kind>MenuItem|PicasaMenuItem)\s*\{(?P<body>(?:[^{}]|\{[^{}]*\})*)\}",
    re.S,
)
_TEXT_TAB_RE = re.compile(r'text:\s*.*?\+\s*"\\t([^"]+)"', re.S)
_OBJNAME_RE = re.compile(r'objectName:\s*"([^"]+)"')
_SHORTCUT_RE = re.compile(r"Shortcut\s*\{(?P<body>(?:[^{}]|\{[^{}]*\})*)\}", re.S)
_SEQ_RE = re.compile(r'sequence:\s*"([^"]+)"')


def _normalizal_billentyu(sequencia: str) -> str:
    """A Qt az `Enter`-t és a `Return`-t ugyanannak a fizikai billentyűnek
    veszi — a menüfelirat hagyományosan „Enter"-t ír (`Ctrl+Enter`,
    `Alt+Enter`), a `Shortcut.sequence` viszont `Return`-t (ld. a meglévő
    `shortcutLocateOnDisk` / Main.qml `Alt+Return`)."""
    return sequencia.replace("Enter", "Return")


def _menu_tetelek(menu_forras: str):
    """A menüsáv `\\t`-tal gyorsbillentyűt hirdető tételei — objectName,
    hirdetett szekvencia, helyfoglaló/nyugdíjazott jelölés."""
    for talalat in _ITEM_RE.finditer(menu_forras):
        blokk = talalat.group("body")
        szoveg_m = _TEXT_TAB_RE.search(blokk)
        if not szoveg_m:
            continue
        objnev_m = _OBJNAME_RE.search(blokk)
        yield {
            "objectName": objnev_m.group(1) if objnev_m else None,
            "sequence": szoveg_m.group(1),
            "placeholder": bool(re.search(r"placeholder:\s*true", blokk)),
            "retired": bool(re.search(r"retired:\s*true", blokk)),
        }


def _elo_billentyu_szekvenciak(qml_forrasok: dict) -> set:
    """Minden `Shortcut { sequence: ... }` szekvenciája az ÖSSZES átadott
    QML-forrásból, normalizálva."""
    szekvenciak = set()
    for forras in qml_forrasok.values():
        for talalat in _SHORTCUT_RE.finditer(forras):
            szm = _SEQ_RE.search(talalat.group("body"))
            if szm:
                szekvenciak.add(_normalizal_billentyu(szm.group(1)))
    return szekvenciak


def _igeretszegesek(menu_forras: str, qml_forrasok: dict) -> list:
    """Az ÉLŐ (nem helyfoglaló, nem nyugdíjazott) menütételek, amelyek
    hirdetnek egy gyorsbillentyűt, de ahhoz SEHOL nem tartozik élő
    `Shortcut`. Üres lista = a hibaosztály nem fordul elő."""
    elo = _elo_billentyu_szekvenciak(qml_forrasok)
    hibak = []
    for tetel in _menu_tetelek(menu_forras):
        if tetel["placeholder"] or tetel["retired"]:
            continue
        szekvencia = _normalizal_billentyu(tetel["sequence"])
        if szekvencia not in elo:
            hibak.append((tetel["objectName"], tetel["sequence"]))
    return hibak


def _valos_qml_forrasok() -> dict:
    return {str(p): p.read_text(encoding="utf-8") for p in _QML_DIR.rglob("*.qml")}


def _osszes_elo_billentyu_szekvencia() -> set:
    return _elo_billentyu_szekvenciak(_valos_qml_forrasok())


class TestSweepOr:
    """A teljes menüsáv seprő ellenőrzése — a mai kódon NULLA ígéretszegés."""

    def test_eles_menusav_minden_hirdetett_billentyuje_kotve_van(self):
        forrasok = _valos_qml_forrasok()
        menu_forras = forrasok[str(_MENU_QML)]
        hibak = _igeretszegesek(menu_forras, forrasok)
        assert not hibak, (
            "hirdetett, de sehol nem kötött gyorsbillentyű(k) a menüsávban: "
            f"{hibak}"
        )

    def test_helyfoglalo_tetel_nem_szamit_igeretszegesnek(self):
        """Nehogy az őr a spec 472–480. sorának KILENC, tudottan
        hatókörön kívüli helyfoglaló tételén (Ctrl+X/C/V/I/3, F1, …)
        magától bukjon el — azok NEM ennek a jegynek a hatóköre."""
        forrasok = _valos_qml_forrasok()
        menu_forras = forrasok[str(_MENU_QML)]
        tetelek = list(_menu_tetelek(menu_forras))
        helyfoglalo_hirdetok = [t for t in tetelek if t["placeholder"]]
        # ⚠️ #1686: 8 → 7. A „Kijelölés megfordítása" (Ctrl+I) tétele ÉLŐVÉ
        # vált — a billentyű már régóta működött, csak a menüpont volt
        # helyfoglaló. Ez a kontroll pontosan úgy viselkedett, ahogy kell:
        # megszólalt, és a hibaüzenete kérdezte meg, hogy „tényleg javult
        # valami". Igen, javult; ezért csökken a szám, nem a mérés tört el.
        assert len(helyfoglalo_hirdetok) >= 7, (
            "a mérésnek meg kell találnia a spec szerinti kilenc "
            "hatókörön-kívüli helyfoglaló tételt — ha ez a szám lecsökkent, "
            "vagy a regex tört el, vagy tényleg javult valami (ellenőrizd!)"
        )
        # egyik helyfoglaló sem jelenik meg az ígéretszegések közt
        hibak = _igeretszegesek(menu_forras, forrasok)
        hibas_nevek = {nev for nev, _ in hibak}
        for tetel in helyfoglalo_hirdetok:
            assert tetel["objectName"] not in hibas_nevek

    def test_hamis_felirat_megbuktatja_az_ort(self):
        """MUTÁCIÓ: egy szándékosan bevezetett ÉLŐ tétel, ami hirdet egy
        soha nem létező billentyűt — az őrnek ezt el KELL kapnia. A
        forrást csak STRINGKÉNT mutáljuk, a lemezen lévő fájl változatlan."""
        forrasok = _valos_qml_forrasok()
        menu_forras = forrasok[str(_MENU_QML)]
        hamis = menu_forras.replace(
            'MenuItem {\n            objectName: "menuFileNewAlbum"',
            'MenuItem {\n            objectName: "menuHamisTeszt1616"\n'
            '            text: qsTr("Hamis tétel") + "\\tCtrl+Zzzz"\n'
            "        }\n"
            '        MenuItem {\n            objectName: "menuFileNewAlbum"',
            1,
        )
        assert hamis != menu_forras, "a mutáció mintája nem talált semmit"
        hibak = _igeretszegesek(hamis, {**forrasok, str(_MENU_QML): hamis})
        hibas_nevek = {nev for nev, _ in hibak}
        assert "menuHamisTeszt1616" in hibas_nevek, (
            "az őr NEM buktatta meg a szándékosan hamis feliratot"
        )

    @pytest.mark.parametrize(
        ("objectname_minta", "erintett_tetel"),
        [
            ('objectName: "shortcutNewAlbum"', "menuFileNewAlbum"),
            ('objectName: "shortcutImportFrom"', "menuFileImportFrom"),
            ('objectName: "shortcutAddFile"', "menuFileAddFile"),
            ('objectName: "shortcutPrint"', "menuFilePrint"),
            ('objectName: "shortcutPrintContactSheet"', "menuFolderPrintContactSheet"),
        ],
    )
    def test_shortcut_torlese_megbuktatja_a_megfelelo_tetelt(
        self, objectname_minta, erintett_tetel
    ):
        """MUTÁCIÓS TÁBLA: minden ÉLŐ `Shortcut` elem, ha eltűnik a
        forrásból, a HOZZÁ TARTOZÓ menütételt ígéretszegésként kell hogy
        megjelölje az őr. A `Shortcut { ... }` blokkot a teljes tartalmával
        együtt távolítjuk el a menüsáv-forrás egy MÁSOLATÁBÓL."""
        forrasok = _valos_qml_forrasok()
        menu_forras = forrasok[str(_MENU_QML)]

        blokk_minta = re.compile(
            r"Shortcut \{[^{}]*" + re.escape(objectname_minta) + r"[^{}]*\}\n",
            re.S,
        )
        mutalt_menu = blokk_minta.sub("", menu_forras, count=1)
        assert mutalt_menu != menu_forras, (
            f"a mutáció mintája ({objectname_minta}) nem talált Shortcut-ot"
        )

        hibak = _igeretszegesek(mutalt_menu, {**forrasok, str(_MENU_QML): mutalt_menu})
        hibas_nevek = {nev for nev, _ in hibak}
        assert erintett_tetel in hibas_nevek, (
            f"a(z) {objectname_minta} törlése nem buktatta meg a(z) "
            f"{erintett_tetel} tételt — az őr foga nem harap"
        )

    def test_sequence_elrontasa_megbuktatja_a_tetelt(self):
        """MUTÁCIÓ: a `shortcutPrint` szekvenciája elcsúszik — a `Ctrl+P`-t
        hirdető menütételnek ígéretszegésként kell megjelennie."""
        forrasok = _valos_qml_forrasok()
        menu_forras = forrasok[str(_MENU_QML)]
        mutalt_menu = menu_forras.replace(
            'objectName: "shortcutPrint"\n        sequence: "Ctrl+P"',
            'objectName: "shortcutPrint"\n        sequence: "Ctrl+Shift+9"',
            1,
        )
        assert mutalt_menu != menu_forras, "a mutáció mintája nem talált semmit"

        hibak = _igeretszegesek(mutalt_menu, {**forrasok, str(_MENU_QML): mutalt_menu})
        hibas_nevek = {nev for nev, _ in hibak}
        assert "menuFilePrint" in hibas_nevek
