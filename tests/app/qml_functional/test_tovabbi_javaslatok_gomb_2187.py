"""A „További javaslatok keresése" gomb a személy-album fejlécén (#2187).

## A mérés

A `faceheaderpanel` javaslat-vezérlői egyetlen sorban ülnek, és a
`respack.yt` szerint **osztoznak a helyen**
(`docs/specs/picasa-arcfelismeres.md` 15.3):

| réteg | téglalap | méret |
|---|---|---|
| `confirmsug` / `confirmsel` | (348,55)–(436,82) | 88 × 27 |
| `removesel` | (439,55)–(527,82) | 88 × 27 |
| **`moresug`** | (348,55)–(527,82) | **179 × 27** |

⇒ A `moresug` a jóváhagyás-pár TELJES helyét elfoglalja, tehát akkor
látszik, amikor nincs mit jóváhagyni — a felirata mérve
„Find more suggestions" / **„További javaslatok keresése"**
(`faceheaderpaneltext.tre:53`, spec 15.4).

A működése a `FaceScanController.moreSuggestions()`: a javaslat-lépcsőt
tízzel lazítja, és a beállítást **nem írja vissza** (`moresug` kezelője,
`0x00602890` — mechanikusan ellenőrizve). Ezt a #3237 őre méri.

## Amit ez az őr NEM mér

A LÁTVÁNYT: hogy a gomb képpontra ott van-e, ahol az eredetiben — a
`respack.yt` a saját 800 pontos vásznához ad koordinátát, a mi fejlécünk
szélessége a mai ablakhoz igazodik. A MÉRETET (179 × 27) és a helyi
sorrendet viszont állítja.
"""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QObject

QML = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml"
FEJLEC = QML / "PicasaPy" / "LightboxHeader.qml"


def test_a_gomb_MERT_merete_179x27() -> None:
    forras = FEJLEC.read_text(encoding="utf-8")
    kezd = forras.index('objectName: "headerMoreSuggestionsButton"')
    blokk = forras[kezd:kezd + 900]
    assert re.search(r"width:\s*179;\s*height:\s*27", blokk), blokk[:400]


def test_a_felirat_a_MERT_szoveg() -> None:
    forras = FEJLEC.read_text(encoding="utf-8")
    assert 'qsTr("Find more suggestions")' in forras


def test_a_gomb_a_jovahagyas_par_HELYEN_all() -> None:
    """A mért téglalap ugyanott indul, mint a `confirmsug` (x = 348)."""
    forras = FEJLEC.read_text(encoding="utf-8")
    kezd = forras.index('objectName: "headerMoreSuggestionsButton"')
    blokk = forras[kezd:kezd + 900]
    assert "x: header.gombSorVege" in blokk, (
        "a gombnak a jóváhagyás-pár kezdőpontján kell állnia")


def test_a_ket_allapot_KIZARJA_egymast() -> None:
    """Javaslat van → jóváhagyás-pár; nincs → „További javaslatok"."""
    forras = FEJLEC.read_text(encoding="utf-8")
    kezd = forras.index('objectName: "headerMoreSuggestionsButton"')
    blokk = forras[kezd:kezd + 900]
    assert "visible: header.tovabbiJavaslatLatszik" in blokk
    assert re.search(
        r"readonly property bool tovabbiJavaslatLatszik:\s*\n?\s*"
        r'header\.personName !== ""\s*&&\s*header\.suggestionCount === 0',
        forras), "a feltétel nem a mért kizárás"


#: a #2187 meglévő UI-próbájának mintája: a fejléc ÖNÁLLÓ komponensként
#: áll fel, mert a rácsban csak valódi személy-albummal jelenne meg
_KEEP_ALIVE: list = []


def _fejlec(engine, **props):
    import picasapy.app.application as app_module
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent

    comp = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml")
        ),
    )
    _KEEP_ALIVE.append(comp)
    fejlec = comp.createWithInitialProperties(props)
    assert comp.errors() == [], comp.errors()
    assert fejlec is not None
    _KEEP_ALIVE.append(fejlec)
    return fejlec


def test_altalanos_albumon_egyik_sem_latszik(qml_app) -> None:
    """Általános album: sem a jóváhagyás-pár, sem a „További javaslatok"."""
    _, _, engine = qml_app
    fejlec = _fejlec(engine, folderName="Nyaralás", personName="")
    for nev in ("headerMoreSuggestionsButton",
                "headerConfirmSuggestionsButton"):
        gomb = fejlec.findChild(QObject, nev)
        assert gomb is not None, f"{nev} nem található"
        assert gomb.property("visible") is False


def test_javaslat_NELKULI_szemely_albumon_a_kereses_latszik(qml_app) -> None:
    """A mért kizárás: nincs mit jóváhagyni → „További javaslatok keresése"."""
    _, _, engine = qml_app
    fejlec = _fejlec(engine, personName="Anna", suggestionCount=0)
    assert fejlec.findChild(
        QObject, "headerMoreSuggestionsButton").property("visible") is True
    assert fejlec.findChild(
        QObject, "headerConfirmSuggestionsButton").property("visible") is False


def test_javaslattal_a_jovahagyas_par_latszik(qml_app) -> None:
    """És a keresés-gomb ilyenkor NEM — ugyanazt a téglalapot foglalnák."""
    _, _, engine = qml_app
    fejlec = _fejlec(engine, personName="Anna", suggestionCount=3)
    assert fejlec.findChild(
        QObject, "headerMoreSuggestionsButton").property("visible") is False
    assert fejlec.findChild(
        QObject, "headerConfirmSuggestionsButton").property("visible") is True


def test_a_gomb_MERT_merete_elo_elemen(qml_app) -> None:
    """Nem forrásszöveg: a kirajzolt gomb mérete."""
    _, _, engine = qml_app
    fejlec = _fejlec(engine, personName="Anna", suggestionCount=0)
    gomb = fejlec.findChild(QObject, "headerMoreSuggestionsButton")
    assert gomb.property("width") == 179
    assert gomb.property("height") == 27


def test_a_hivas_a_vezerlo_slotjara_megy() -> None:
    """A Main.qml hídja a mért vezérlőt hívja, nem saját logikát."""
    forras = (QML / "Main.qml").read_text(encoding="utf-8")
    assert "function findMoreSuggestions()" in forras
    kezd = forras.index("function findMoreSuggestions()")
    blokk = forras[kezd:kezd + 700]
    assert "_faceScanController.moreSuggestions()" in blokk
