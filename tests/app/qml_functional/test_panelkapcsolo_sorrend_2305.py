"""#2305 — a négy panelkapcsoló IKON-gomb, és a csúszka UTÁN áll.

## A mért koordináták

A `respack.yt` rétegfejléceiből (`docs/specs/picasa-fo-ablak-elrendezes.md`):

| réteg | x-tartomány |
|---|---|
| `thumbui/loupehit` (nagyító gombja) | 366…391 |
| `thumbui/scalecontainer` (csúszka) | 398…525 |
| `thumbui/metadata_group` (a négy kapcsoló) | **545…785** |

⇒ **545 > 525**: az eredetiben a csúszka MEGELŐZI a négy kapcsolót. Nálunk
fordítva volt — a kapcsolók a csúszka elé kerültek.

## A feliratok

A gombok típusnevei (`buttcon_LS_` · `_MS_` · `_RS_`) **ikon-gombokat**
jelölnek, és a tulajdonos képernyőmentésén az eredeti négy gombja
**kizárólag ikon**. Nálunk a 60 × 24-es gombba az ikon MELLETT a felirat is
belefért volna — levágva, csúnyán. A felirat mostantól a **buborék-súgóban**
és az akadálymentesítési névben él.

⚠️ Ami NINCS ebben a jegyben: a két hiányzó ikon („Beillesztheti a fotót a
megjelenési területre", „Fotó megjelenítése tényleges méretben") — azok
erőforrása és helye bináris kutatást kíván, külön jegy.
"""

from __future__ import annotations

import time
from pathlib import Path

import picasapy.app as app_csomag
from PySide6.QtCore import QPointF
from PySide6.QtQuick import QQuickItem

_QML = (
    Path(app_csomag.__file__).parent / "qml" / "PicasaPy" / "TrayBar.qml"
).read_text(encoding="utf-8")

KAPCSOLOK = ["people", "places", "tags", "properties"]


def _kuldott_blokk() -> str:
    """A kapcsoló-küldött TELJES forrása, kapcsos zárójel szerint vágva.

    ⚠️ Rögzített karakterablakkal (`[kezd:kezd+2000]`) nem szabad: a blokk
    hossza a kommentektől függ, és egy jogos bővítés némán kivágná a
    keresett sort — a próba ilyenkor hamisan zöld vagy hamisan piros lenne.
    """
    kezd = _QML.index('objectName: "trayPanelToggle_"')
    # vissza a küldött nyitó kapcsos zárójeléig
    nyito = _QML.rindex("{", 0, kezd)
    melyseg = 0
    for i in range(nyito, len(_QML)):
        if _QML[i] == "{":
            melyseg += 1
        elif _QML[i] == "}":
            melyseg -= 1
            if melyseg == 0:
                return _QML[nyito : i + 1]
    raise AssertionError("nem záródik a küldött blokkja")


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _elem(window, nev: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == nev:
            return item
    raise AssertionError(f"nincs ilyen elem: {nev}")


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AssertionError, AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.01)
    return False


def _x(elem) -> float:
    return elem.mapToScene(QPointF(0, 0)).x()


class TestASorrend:
    """A mért x-tartományok szerint: nagyító → csúszka → négy kapcsoló."""

    def test_a_kapcsolok_a_CSUSZKA_UTAN_allnak(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: _elem(window, "trayMetadataGroup"))
        kapcsolok = _elem(window, "trayMetadataGroup")
        csuszka = _elem(window, "trayZoomGroup")
        assert _x(kapcsolok) > _x(csuszka), (
            f"a négy panelkapcsoló a csúszka ELŐTT van "
            f"(kapcsolók x={_x(kapcsolok):.0f}, csúszka x={_x(csuszka):.0f}) "
            f"— az eredetiben 545 > 525, tehát utána"
        )

    def test_a_nagyito_gombja_a_csuszka_ELOTT_marad(self, qml_app, qt_app):
        """`loupehit` 366…391 < `scalecontainer` 398…525 — ez a rész eddig
        is helyes volt, és nem romolhat el a sorrend cseréjétől."""
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: _elem(window, "trayLoupeButton"))
        nagyito = _elem(window, "trayLoupeButton")
        csuszka = _elem(window, "trayZoomGroup")
        assert _x(nagyito) >= _x(csuszka), (
            "a nagyító gombja kikerült a csúszka csoportjából"
        )


class TestNincsFelirat:
    def test_a_gombok_NEM_mutatnak_szoveget(self, qml_app, qt_app):
        """A 60 × 24-es gombba a felirat belelógott/levágódott."""
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: _elem(window, "trayPanelToggle_people"))
        for nev in KAPCSOLOK:
            gomb = _elem(window, f"trayPanelToggle_{nev}")
            szovegek = [
                gy
                for gy in _walk(gomb)
                if gy.metaObject().className().startswith("QQuickText")
                and gy.property("text")
            ]
            assert not szovegek, (
                f"a(z) {nev} kapcsolón felirat van: "
                f"{[gy.property('text') for gy in szovegek]}"
            )

    def test_a_forras_nem_rak_Text_et_a_kapcsolora(self):
        """Forrás-szintű őr: a küldött tartalma csak ikon."""
        blokk = _kuldott_blokk()
        assert "contentItem:" in blokk
        tartalom = blokk[blokk.index("contentItem:"):]
        assert "Text {" not in tartalom, (
            "a kapcsoló tartalmában megint van `Text` — az eredeti gombjai "
            "ikon-gombok"
        )


class TestAFeliratMEGMARAD:
    """A szöveg nem vész el: buborék-súgó és akadálymentesítési név lesz.

    ⚠️ Mindkettő CSATOLT tulajdonság, a delegáltról Pythonból nem
    olvasható (`QQmlProperty.read` `None`-t ad rájuk) — ezért forrásból
    mérjük, a küldött TELJES blokkjában."""

    def test_a_buboreksugo_megvan(self):
        blokk = _kuldott_blokk()
        assert "ToolTip.text: modelData.sugo" in blokk, (
            "eltűnt a buboréksúgó — a felirat helyére ennek kell lépnie"
        )
        assert "ToolTip.visible:" in blokk, "a súgó soha nem jelenne meg"

    def test_az_akadalymentesitesi_nev_a_FELIRAT(self):
        blokk = _kuldott_blokk()
        assert "Accessible.name: modelData.felirat" in blokk, (
            "a felirat nyomtalanul eltűnt — legalább az akadálymentesítési "
            "névben meg kell maradnia"
        )
