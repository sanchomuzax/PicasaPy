"""`Nézet ▸ Megjelenítési mód` — a tizenegy tagú kizáró csoport — #1575.

A menü **váza**: a tételek, a sorrend, a négy elválasztó és a kizáró
(rádió) viselkedés. Az egyes módok képpont-hatását külön jegyek adják
(#1576/#1577/#1578) — itt az a szerződés, hogy a tétel **pipázódik és a
módot beállítja a vezérlőn**.

A bizonyíték: `docs/specs/picasa-megjelenitesi-modok.md` (a #1409
feltárása). A sorrend és az elválasztók az 1., a kizárólagosság a 2.
szakaszból valók, mindkettő MÉRVE a `Picasa3.exe`-ből.

⚠️ **A rádió-csapda** (2. szakasz, `0x00575689`). Az eredetiben a MÁR
AKTÍV tételre kattintva a pipa marad: a beállító a pipázó ciklust akkor is
lefuttatja, ha a mód nem változott. A mi `checkable` + kötött `checked`
mintánk ilyenkor **magától soha nem értékelődne újra** — a valódi kattintás
előbb imperatívan átbillenti a `checked`-et (`toggle()`), és mivel a
vezérlő állapota nem változik, a kötés nem éled újra. Ezért a QML a jelzés
után **visszaköti** a `checked`-et (a #1464/#1468 mintája).

Ez a fájl a VALÓDI kattintást végzi (`toggle()` + `triggered`), és a
pipákat a menü ÚJRANYITÁSA után nézi — a metódus közvetlen hívása épp a
hibás lépést hagyná méretlenül.

Az őrnek foga is van: a `setDisplayMode` azonos értéknél NEM jelez (ld.
`tests/app/test_display_mode_controller_1575.py`), ezért a visszakötés
eltávolítása ezeket a teszteket megbuktatja — nem úgy, mint a #1468
„őszinte címkével" ellátott, feltétel nélkül jelző csoportjainál.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtQml import QQmlExpression, qmlContext

#: Az almenü `objectName`-je.
MENU = "menuViewDisplayMode"

#: A tizenegy tétel — a spec 1. szakaszának SORRENDJÉBEN, `objectName` →
#: vezérlő-módazonosító.
TETELEK: tuple[tuple[str, str], ...] = (
    ("menuViewDisplayModeAuto", "auto"),
    ("menuViewDisplayModeNormal", "normal"),
    ("menuViewDisplayMode16Bit", "dither16"),
    ("menuViewDisplayModeRemoteDesktop", "rdesk"),
    ("menuViewDisplayModeLcd", "lcd"),
    ("menuViewDisplayModeProjector", "projector"),
    ("menuViewDisplayModeOverflow", "overflow"),
    ("menuViewDisplayModeMacGamma", "mac"),
    ("menuViewDisplayModeLinearGamma", "linear"),
    ("menuViewDisplayModeSepia", "sepia"),
    ("menuViewDisplayModeBlackWhite", "bw"),
)

NEVEK: tuple[str, ...] = tuple(nev for nev, _ in TETELEK)

#: ⚠️ #1658 — EZ A JEGY MEGVÁLTOZTATTA A #1575 SZERZŐDÉSÉT.
#:
#: A #1575 eredetileg azt kötötte ki, hogy „kattinthatatlan helyfoglalót nem
#: hagyunk", mert „a kizáró csoport épp attól kizáró, hogy minden tagja
#: választható". A tulajdonos kétszer is hiába próbálta a módokat (#1598, majd
#: RPi5-ön a 0.8.127-tel): a menü olyat kínált, ami nem csinál semmit, és
#: **semmi nem jelezte**. A #1658 ezért megfordította a döntést — a
#: választhatóság kevesebbet ér, mint az őszinteség arról, mi működik.
#:
#: Ez a három tétel MA nincs megvalósítva, tehát jelölt és letiltott:
NEM_MEGVALOSITOTT: frozenset[str] = frozenset(
    {"menuViewDisplayMode16Bit", "menuViewDisplayModeRemoteDesktop",
     "menuViewDisplayModeMacGamma"}
)

#: A 15 rekord: 11 tétel + 4 elválasztó, a spec 1. szakasza szerint.
VART_SZERKEZET: tuple[str, ...] = (
    "menuViewDisplayModeAuto",
    "<elvalaszto>",
    "menuViewDisplayModeNormal",
    "menuViewDisplayMode16Bit",
    "<elvalaszto>",
    "menuViewDisplayModeRemoteDesktop",
    "menuViewDisplayModeLcd",
    "menuViewDisplayModeProjector",
    "<elvalaszto>",
    "menuViewDisplayModeOverflow",
    "menuViewDisplayModeMacGamma",
    "menuViewDisplayModeLinearGamma",
    "<elvalaszto>",
    "menuViewDisplayModeSepia",
    "menuViewDisplayModeBlackWhite",
)

#: A menü rekordjainak felsorolása a menü SAJÁT névterében kiértékelve.
#: A `count`/`itemAt()` páros a Qt hivatalos útja; Pythonból a `contentModel`
#: és a `QQmlListProperty` nem konvertálható, az `itemAt` visszatérési
#: értékéhez pedig nincs `QQuickItem*` konverter — ezért JS-kifejezés, ami
#: már SZTRINGET ad vissza. Az elválasztón nincs `checkable`, ez különbözteti
#: meg a tételtől.
_SZERKEZET_JS = (
    "(function () {"
    "  var r = [];"
    "  for (var i = 0; i < count; ++i) {"
    "    var it = itemAt(i);"
    "    r.push(!it ? '<null>'"
    "      : (typeof it.checkable === 'undefined' ? '<elvalaszto>'"
    "         : (it.objectName || '<nevtelen>')));"
    "  }"
    "  return r.join('|');"
    "})()"
)


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _trigger(root, name):
    """A menütétel aktiválása — a VALÓDI kattintás MINDKÉT lépése.

    Csak a `triggered` kibocsátása méretlenül hagyná épp a hibás lépést: a
    `toggle()` imperatív `checked`-írását (#1464/#1468).
    """
    item = _child(root, name)
    if item.property("checkable"):
        QMetaObject.invokeMethod(item, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)


def _ujranyit(root, qt_app):
    """A menü becsukása és ÚJRANYITÁSA — a pipákat így nézi a felhasználó."""
    menu = _child(root, MENU)
    QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    QMetaObject.invokeMethod(menu, "open", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _pipak(root) -> dict[str, bool]:
    return {n: bool(_child(root, n).property("checked")) for n in NEVEK}


def _egyetlen_pipa(root, vart) -> None:
    pipak = _pipak(root)
    assert pipak == {n: (n == vart) for n in NEVEK}, (
        f"a csoportban nem pontosan a(z) {vart} tételen áll pipa: "
        f"{sorted(n for n, p in pipak.items() if p)}"
    )


def _szerkezet(root) -> tuple[str, ...]:
    menu = _child(root, MENU)
    kifejezes = QQmlExpression(qmlContext(menu), menu, _SZERKEZET_JS)
    ertek, hiba = kifejezes.evaluate()
    assert not hiba, f"a szerkezet-lekérdezés hibára futott: {kifejezes.error()}"
    return tuple(str(ertek).split("|")) if ertek else ()


class TestSzerkezet:
    """A menü VÁZA — a spec 1. szakasza."""

    def test_az_almenu_nem_letiltott(self, qml_app):
        window, _controller, _engine = qml_app
        assert _child(window, MENU).property("enabled") is True, (
            "az almenü letiltott maradt — a #1575 előtt üres és szürke volt"
        )

    def test_tizenot_rekord_a_spec_sorrendjeben(self, qml_app):
        window, _controller, _engine = qml_app
        szerkezet = _szerkezet(window)
        assert szerkezet == VART_SZERKEZET
        assert len(szerkezet) == 15
        assert szerkezet.count("<elvalaszto>") == 4

    def test_a_megvalositott_tetelek_kattinthatok(self, qml_app):
        """Ami MŰKÖDIK, az kattintható és pipázható.

        ⚠️ #1658: ez a teszt korábban MINDEN tételre ezt állította. A
        megfordítás indoklása a `NEM_MEGVALOSITOTT` melletti megjegyzésben áll.
        """
        window, _controller, _engine = qml_app
        for nev in NEVEK:
            if nev in NEM_MEGVALOSITOTT:
                continue
            item = _child(window, nev)
            assert item.property("enabled") is True, f"{nev} letiltott"
            assert item.property("checkable") is True, f"{nev} nem pipázható"
            assert not item.property("placeholder"), f"{nev} helyfoglalónak jelölt"

    def test_a_meg_nem_valositott_tetelek_jeloltek_es_tiltottak(self, qml_app):
        """#1658: ami nem működik, azt a felhasználó LÁSSA is annak."""
        window, _controller, _engine = qml_app
        for nev in NEM_MEGVALOSITOTT:
            item = _child(window, nev)
            assert item.property("enabled") is False, f"{nev} kattintható maradt"
            jelolt = bool(item.property("placeholder")) or bool(item.property("retired"))
            assert jelolt, f"{nev} letiltott, de JELÖLETLEN — a felhasználó nem érti, miért"


class TestKizaroCsoport:
    """Mindig PONTOSAN egy pipa — és a mód beáll a vezérlőn."""

    def test_indulaskor_az_automatikus_az_aktiv(self, qml_app):
        window, controller, _engine = qml_app
        assert controller.property("displayMode") == "auto"
        _egyetlen_pipa(window, "menuViewDisplayModeAuto")

    @pytest.mark.parametrize(
        "nev,mode",
        # #1658: a letiltott tételekre kattintani sem lehet, tehát módot
        # sem állítanak — őket a fenti szerkezeti teszt fedi.
        [t for t in TETELEK if t[1] != "auto" and t[0] not in NEM_MEGVALOSITOTT],
    )
    def test_a_valtas_beallitja_a_modot_es_egyetlen_pipat_hagy(
        self, qml_app, qt_app, nev, mode
    ):
        window, controller, _engine = qml_app
        _trigger(window, nev)
        qt_app.processEvents()
        assert controller.property("displayMode") == mode
        _ujranyit(window, qt_app)
        _egyetlen_pipa(window, nev)

    def test_a_valtasok_lanca_nem_halmoz_pipat(self, qml_app, qt_app):
        """Több váltás után sem maradhat két pipa a csoportban."""
        window, _controller, _engine = qml_app
        for nev in ("menuViewDisplayModeSepia", "menuViewDisplayModeLcd",
                    "menuViewDisplayModeBlackWhite"):
            _trigger(window, nev)
            qt_app.processEvents()
            _ujranyit(window, qt_app)
            _egyetlen_pipa(window, nev)


class TestRadioCsapda:
    """A jegy MAGJA: a már aktív tételre kattintva a pipa NEM tűnhet el."""

    @pytest.mark.parametrize(
        "nev",
        [
            "menuViewDisplayModeProjector",  # nem az alapértelmezés: valódi váltás
            "menuViewDisplayModeBlackWhite",
        ],
    )
    def test_a_mar_aktiv_tetelre_ujra_kattintva_marad_a_pipa(
        self, qml_app, qt_app, nev
    ):
        window, _controller, _engine = qml_app
        _trigger(window, nev)
        qt_app.processEvents()
        _ujranyit(window, qt_app)
        _egyetlen_pipa(window, nev)

        _trigger(window, nev)  # MÁSODSZOR — az állapot már nem változik
        qt_app.processEvents()
        _ujranyit(window, qt_app)
        _egyetlen_pipa(window, nev)

    def test_az_alapertelmezett_tetelre_kattintva_is_marad(self, qml_app, qt_app):
        """Az `Automatikus` indulásból AKTÍV — rákattintva sem tűnhet el.

        Ez a legszigorúbb eset: itt az első kattintás sem változtat
        állapotot, tehát csak a visszakötés tarthatja meg a pipát.
        """
        window, controller, _engine = qml_app
        _trigger(window, "menuViewDisplayModeAuto")
        qt_app.processEvents()
        _ujranyit(window, qt_app)
        assert controller.property("displayMode") == "auto"
        _egyetlen_pipa(window, "menuViewDisplayModeAuto")
