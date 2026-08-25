"""#1468: a kizáró (rádió) menücsoportokban a MÁR AKTÍV tételre kattintva
eltűnt a pipa.

A `MenuItem { checkable: true; checked: <kötés> }` mintánál a valódi
kattintás előbb `toggle()`-t hív — ez IMPERATÍVAN írja a `checked`-et —, és
csak utána dördül el a `triggered`.

A mechanizmust MEGMÉRTÜK (a probe eredménye a #1468 zárójelentésében): a
`toggle()` C++ oldali írása NEM öli meg a QML-kötést, az a következő
FÜGGŐSÉG-VÁLTOZÁSKOR újraértékelődik. Ebből következik a hiba pontos alakja
és a határa is:

* **Kizáró csoport** (több tétel ugyanarra a forrás-tulajdonságra köt): a
  már aktív tételre kattintva a vezérlő állapota NEM változik, tehát a
  kötés soha nem értékelődik újra — a menü újranyitásakor a csoport
  EGYIK tételén sem áll pipa. Ez a jegy hibája.
* **Önálló ki-be kapcsoló** (egyetlen tétel köt a tulajdonságra): az
  állapot minden kattintásra változik, a kötés újraértékelődik, a pipa
  helyreáll. Ezek NEM érintettek — és az itteni forrásszintű őr ezt
  szerkezetileg, allow-lista nélkül különbözteti meg.

A javítás a #1464-ben bevezetett mintát követi: a jelzés után a `checked`
azonnal VISSZAKÖTŐDIK (`checked = Qt.binding(...)`), ami a kötést nyomban
ki is értékeli, így a pipa akkor is helyreáll, ha az állapot nem változott.

Az itteni funkcionális tesztek a VALÓDI kattintás mindkét lépését elvégzik
(`toggle()` + `triggered`), és a pipákat a menü ÚJRANYITÁSA után nézik —
köztük UGYANARRA a tételre kétszer kattintva, mert épp ez a hiba lényege.
"""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

_QML_ROOT = (
    Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml"
)

# A forrásszintű őr ALSÓ KORLÁTAI. Egy „a rossz minta előfordulása legyen 0"
# alakú őr üresen is igaz: elgépelt minta, elmozdult mappa vagy elromlott
# elemző mellett is zöld marad, miközben semmit nem mér. Ezért a mérés
# terjedelmét is állítjuk.
_MIN_QML_FAJL = 50
_MIN_RADIO_CSOPORT = 5

# Fenntartott szavak: ezek nem tulajdonság-útvonalak a `checked` kifejezésben.
_KULCSSZAVAK = frozenset(
    {"true", "false", "null", "undefined", "typeof", "function", "return", "var"}
)


# ---------------------------------------------------------------------------
# forrás-elemzés
# ---------------------------------------------------------------------------


def _qml_fajlok() -> list[Path]:
    return sorted(_QML_ROOT.rglob("*.qml"))


def _menuitem_blokkok(text: str):
    """A `MenuItem` / `PicasaMenuItem` blokkok — kiegyensúlyozott zárójelig.

    Sor-alapú regexszel nem lehetne: a tétel törzse maga is tartalmaz
    kapcsos zárójelet (`onTriggered: { … }`).
    """
    for m in re.finditer(r"\b(MenuItem|PicasaMenuItem)\s*\{", text):
        melyseg = 0
        for j in range(m.end() - 1, len(text)):
            if text[j] == "{":
                melyseg += 1
            elif text[j] == "}":
                melyseg -= 1
                if melyseg == 0:
                    yield text[: m.start()].count("\n") + 1, text[m.start() : j + 1]
                    break


def _checked_kifejezes(body: str) -> str | None:
    """A tétel `checked:` kötésének jobb oldala — egysoros alakban is."""
    m = re.search(r"\bchecked\s*:\s*(.+)", body)
    if m is None:
        return None
    # egysoros blokk (`… ; checked: true }`): a lezáró `}` és az esetleges
    # további property-k levágása
    return m.group(1).split(";")[0].strip().rstrip("}").strip()


def _forras_tulajdonsag(kifejezes: str) -> str | None:
    """A `checked` kifejezés LEGMÉLYEBB tulajdonság-útvonala.

    Ez a csoportosítás kulcsa: `bar.ctl && bar.ctl.folderSort === "date"`
    és `bar.ctl && bar.ctl.folderSort === "name"` ugyanarra a
    `bar.ctl.folderSort`-ra köt, tehát ugyanannak a KIZÁRÓ csoportnak a
    tagjai. A `bar.ctl` puszta null-őr, azt a mélység zárja ki.
    """
    csupasz = re.sub(r'"[^"]*"|\'[^\']*\'', " ", kifejezes)
    utak = [
        u
        for u in re.findall(r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*", csupasz)
        if u not in _KULCSSZAVAK
    ]
    if not utak:
        return None
    return max(utak, key=lambda u: (u.count("."), len(u)))


def _kotott_tetelek() -> list[dict]:
    """Minden `checkable: true` menütétel, amelynek KÖTÖTT a `checked`-je."""
    tetelek = []
    for p in _qml_fajlok():
        text = p.read_text(encoding="utf-8")
        for sor, body in _menuitem_blokkok(text):
            if not re.search(r"\bcheckable\s*:\s*true", body):
                continue
            kif = _checked_kifejezes(body)
            if kif is None or kif in ("true", "false"):
                continue  # nincs pipa-kötés, vagy állandó — ld. külön őr
            forras = _forras_tulajdonsag(kif)
            if forras is None:
                continue
            nev = re.search(r'objectName\s*:\s*"([^"]+)"', body)
            tetelek.append(
                {
                    "fajl": p.relative_to(_QML_ROOT).as_posix(),
                    "sor": sor,
                    "nev": nev.group(1) if nev else f"(névtelen, {sor}. sor)",
                    "forras": forras,
                    "visszakot": "Qt.binding" in body,
                }
            )
    return tetelek


def _radio_csoportok() -> dict[tuple[str, str], list[dict]]:
    """A KIZÁRÓ csoportok: fájlonként ugyanarra a forrásra kötő tételek.

    Két tétel már csoportot alkot — a kizárólagosság ebből következik, és
    ez a szerkezeti ismérv váltja ki az allow-listát: az önálló kapcsolók
    (egyetlen tétel a forráson) maguktól kimaradnak.
    """
    csoportok: dict[tuple[str, str], list[dict]] = {}
    for t in _kotott_tetelek():
        csoportok.setdefault((t["fajl"], t["forras"]), []).append(t)
    return {k: v for k, v in csoportok.items() if len(v) >= 2}


class TestForrasszintuOr:
    """A rossz minta előfordulása 0 — ÉS az őr bizonyítja, hogy tud találni."""

    def test_a_meres_terjedelme_nem_ures(self):
        """Alsó korlát: a számláló őr üresen is igaz volna."""
        fajlok = _qml_fajlok()
        assert len(fajlok) >= _MIN_QML_FAJL, (
            f"csak {len(fajlok)} QML-fájlt találtam a {_QML_ROOT} alatt — "
            "elmozdult a mappaszerkezet, az őr vakon mérne"
        )
        nevek = {p.name for p in fajlok}
        assert "PicasaMenuBar.qml" in nevek
        assert _kotott_tetelek(), "egyetlen kötött pipájú menütételt sem találtam"

    def test_az_elemzo_megtalalja_a_kizaro_csoportokat(self):
        """Alsó korlát: a csoportosító legalább ennyi csoportot lát."""
        csoportok = _radio_csoportok()
        assert len(csoportok) >= _MIN_RADIO_CSOPORT, (
            f"csak {len(csoportok)} kizáró csoportot találtam: "
            f"{sorted(csoportok)} — az elemző elromlott"
        )

    def test_az_or_a_HELYES_mintat_is_megtalalja(self):
        """Pozitív kontroll: a #1464-ben MÁR javított csoport.

        Enélkül az őr akkor is zöld volna, ha a `Qt.binding` felismerése
        romlik el — hiszen olyankor MINDENT hibásnak látna… vagy épp
        semmit. Ez a teszt kimondja: van olyan csoport, amelynek MINDEN
        tagja visszaköt.
        """
        javitott = [
            kulcs
            for kulcs, tagok in _radio_csoportok().items()
            if all(t["visszakot"] for t in tagok)
        ]
        assert javitott, (
            "egyetlen olyan kizáró csoportot sem találtam, amelynek minden "
            "tagja visszaköti a `checked`-et — az őr nem tud helyeset találni"
        )

    def test_az_elemzo_kulon_kezeli_az_onallo_kapcsolokat(self):
        """A szerkezeti ismérv csak akkor ér valamit, ha DISZKRIMINÁL.

        Ha az elemző minden kötött pipájú tételt egy csoportba söpörne, az
        őr az önálló kapcsolókat is hibásnak látná — a mérés szerint
        viszont azok NEM érintettek (a kötés újraértékelődik).
        """
        csoportositott = {
            (t["fajl"], t["forras"]) for tagok in _radio_csoportok().values() for t in tagok
        }
        onalloak = [
            t
            for t in _kotott_tetelek()
            if (t["fajl"], t["forras"]) not in csoportositott
        ]
        assert onalloak, "egyetlen önálló ki-be kapcsolót sem különböztetett meg az elemző"

    def test_minden_kizaro_tetel_visszakoti_a_pipat(self):
        """A tulajdonképpeni őr: kitett tétel ne maradjon."""
        kitett = [
            f"{t['fajl']}:{t['sor']} {t['nev']} (forrás: {t['forras']})"
            for tagok in _radio_csoportok().values()
            for t in tagok
            if not t["visszakot"]
        ]
        assert kitett == [], (
            "kizáró menücsoport tagja `Qt.binding` visszakötés nélkül — a már "
            "aktív tételre kattintva eltűnik a pipa:\n  " + "\n  ".join(sorted(kitett))
        )

    def test_az_allando_pipaju_tetelnek_van_kezeloje(self):
        """`checked: true` állandóval: a kattintás LEVESZI a pipát, és

        semmi nem teszi vissza (kötés sincs, amit újra lehetne értékelni).
        Ilyen tételhez tehát kötelező `onTriggered`, ami helyreállítja.
        """
        kitett = []
        for p in _qml_fajlok():
            for sor, body in _menuitem_blokkok(p.read_text(encoding="utf-8")):
                if not re.search(r"\bcheckable\s*:\s*true", body):
                    continue
                if _checked_kifejezes(body) != "true":
                    continue
                if "onTriggered" not in body:
                    kitett.append(f"{p.relative_to(_QML_ROOT).as_posix()}:{sor}")
        assert kitett == [], (
            "állandóan pipált menütétel kezelő nélkül — egyetlen kattintás "
            "véglegesen leveszi a pipát:\n  " + "\n  ".join(kitett)
        )


# ---------------------------------------------------------------------------
# funkcionális őrök
# ---------------------------------------------------------------------------


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _trigger(root, name):
    """A menütétel aktiválása — a VALÓDI kattintás MINDKÉT lépése.

    Csak a `triggered` kibocsátása méretlenül hagyná épp a hibás lépést: a
    `toggle()` imperatív `checked`-írását (#1464 `_trigger`).
    """
    item = _child(root, name)
    if item.property("checkable"):
        QMetaObject.invokeMethod(item, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)


def _ujranyit(root, menu_name, qt_app):
    """A menü becsukása és ÚJRANYITÁSA — a pipákat így nézi a felhasználó."""
    menu = _child(root, menu_name)
    QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    QMetaObject.invokeMethod(menu, "open", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _pipak(root, nevek) -> dict[str, bool]:
    return {n: bool(_child(root, n).property("checked")) for n in nevek}


def _egyetlen_pipa(root, nevek, vart) -> None:
    pipak = _pipak(root, nevek)
    assert pipak == {n: (n == vart) for n in nevek}, (
        f"a csoportban nem pontosan a(z) {vart} tételen áll pipa: {pipak}"
    )


class _KizaroCsoportProba:
    """Közös menet: váltás → újranyitás → UGYANARRA mégegyszer → újranyitás.

    A második kattintás a lényeg: ott nem változik az állapot, tehát a
    kötés magától soha nem értékelődne újra.
    """

    nevek: tuple[str, ...] = ()
    menu: str = ""
    cel: str = ""

    def test_a_valtas_utan_pontosan_egy_pipa_all(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _trigger(window, self.cel)
        qt_app.processEvents()
        _ujranyit(window, self.menu, qt_app)
        _egyetlen_pipa(window, self.nevek, self.cel)

    def test_a_mar_aktiv_tetelre_ujra_kattintva_marad_a_pipa(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _trigger(window, self.cel)
        qt_app.processEvents()
        _ujranyit(window, self.menu, qt_app)

        _trigger(window, self.cel)  # MÁSODSZOR — az állapot már nem változik
        qt_app.processEvents()
        _ujranyit(window, self.menu, qt_app)

        _egyetlen_pipa(window, self.nevek, self.cel)


class TestIndexkepFelirat(_KizaroCsoportProba):
    """Nézet ▸ Indexkép-felirat — öt kizáró tétel (`thumbCaptionMode`).

    ŐSZINTE CÍMKE: ez a két teszt a javítás VISSZAVÉTELEKOR is zöld marad.
    A `setThumbCaptionMode` ugyanis FELTÉTEL NÉLKÜL emit-el
    (`statusChanged`), így a kötés a fölösleges hívásra is újraértékelődik
    — a csoportot ma a setter véletlen mellékhatása védi, nem a QML. Ezek
    tehát REGRESSZIÓS őrök: ha a setter valaha „azonos értéknél ne jelezz"
    optimalizációt kap (mint a `setLanguage`), itt azonnal kiderül.
    """

    nevek = (
        "menuViewThumbCaptionNone",
        "menuViewThumbCaptionFilename",
        "menuViewThumbCaptionCaption",
        "menuViewThumbCaptionTags",
        "menuViewThumbCaptionResolution",
    )
    menu = "menuViewThumbnailCaption"
    cel = "menuViewThumbCaptionTags"


class TestMappaRendezes(_KizaroCsoportProba):
    """Mappa ▸ Rendezés — négy kizáró tétel (`folderSort`).

    A „Fordított sorrend" SZÁNDÉKOSAN nincs a névsorban: az önálló
    kapcsoló (`folderSortReverse`), minden kattintásra változik az állapot.

    ŐSZINTE CÍMKE: a `setFolderSort` → `_refresh_view()` szintén feltétel
    nélkül jelez, ezért — ld. `TestIndexkepFelirat` — ez a két teszt a
    javítás visszavételekor is zöld marad. Regressziós őr.
    """

    nevek = (
        "menuFolderSortByDate",
        "menuFolderSortByChanged",
        "menuFolderSortBySize",
        "menuFolderSortByName",
    )
    menu = "menuFolderSortBy"
    cel = "menuFolderSortBySize"


class TestNyelvvalasztas(_KizaroCsoportProba):
    """Eszközök ▸ Nyelv — kizáró pár (`language`)."""

    nevek = ("menuLanguageEnglish", "menuLanguageHungarian")
    menu = "menuToolsLanguage"
    # SZÁNDÉKOSAN a magyar (nem az alapértelmezett angol): az első
    # kattintásnak VALÓDI váltásnak kell lennie, hogy a második legyen a
    # „már aktív tételre kattintás". Ha a cél az alapértelmezés volna, a
    # két kattintás párosan kioltaná egymást, és a teszt hibás kód mellett
    # is zöld maradna (ezen a párosságon MÉRVE bukott meg az első változat).
    cel = "menuLanguageHungarian"


class TestKonyvtarNezetAllandoPipaja:
    """A `Nézet ▸ Könyvtár` pipája ÁLLANDÓ — a kattintás nem veheti le."""

    def test_kattintasra_is_marad_a_pipa(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        item = _child(window, "menuViewLibraryView")
        assert item.property("checked") is True

        _trigger(window, "menuViewLibraryView")
        qt_app.processEvents()

        assert item.property("checked") is True, (
            "a Könyvtár nézet pipája egyetlen kattintásra véglegesen eltűnt"
        )


class TestBalHasabHelyiMenuje:
    """`FolderListContextMenu` — a rendezés négy kizáró tétele (`paneSort`).

    Itt a menü újranyitása a HOST valódi útján történik
    (`openFolderListContextMenu`), ami a `sortMode` pillanatfelvételt is
    frissen átveszi a vezérlőből — épp az a lépés, ami a hibát elfedhetné.
    """

    nevek = (
        "folderListMenuSortByDate",
        "folderListMenuSortByName",
        "folderListMenuSortBySize",
        "folderListMenuSortByChanged",
    )

    @staticmethod
    def _ujranyit(window, qt_app):
        QMetaObject.invokeMethod(
            _child(window, "folderPane"),
            "openFolderListContextMenu",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

    def test_a_mar_aktiv_tetelre_ujra_kattintva_marad_a_pipa(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        self._ujranyit(window, qt_app)

        _trigger(window, "folderListMenuSortByName")
        qt_app.processEvents()
        self._ujranyit(window, qt_app)
        _egyetlen_pipa(window, self.nevek, "folderListMenuSortByName")

        _trigger(window, "folderListMenuSortByName")  # MÁSODSZOR
        qt_app.processEvents()
        self._ujranyit(window, qt_app)
        _egyetlen_pipa(window, self.nevek, "folderListMenuSortByName")


class TestMappaHelyiMenuje:
    """`FolderContextMenu` — a mappa KÉPEINEK rendezése (`folderPhotoSort`)."""

    nevek = (
        "folderMenuSortByDate",
        "folderMenuSortByName",
        "folderMenuSortBySize",
    )

    @staticmethod
    def _ujranyit(window, qt_app, path):
        QMetaObject.invokeMethod(
            _child(window, "folderPane"),
            "openFolderContextMenu",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", path),
        )
        qt_app.processEvents()

    def test_a_mar_aktiv_tetelre_ujra_kattintva_marad_a_pipa(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        path = controller.property("currentFolder") or ""
        self._ujranyit(window, qt_app, path)

        _trigger(window, "folderMenuSortByName")
        qt_app.processEvents()
        self._ujranyit(window, qt_app, path)
        _egyetlen_pipa(window, self.nevek, "folderMenuSortByName")

        _trigger(window, "folderMenuSortByName")  # MÁSODSZOR
        qt_app.processEvents()
        self._ujranyit(window, qt_app, path)
        _egyetlen_pipa(window, self.nevek, "folderMenuSortByName")
