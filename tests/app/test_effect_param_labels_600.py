"""#600: az effekt-vezérlők feliratai a Picasa SAJÁT szótárából valók.

A csúszka-feliratok korábban részben kitalált angol nevek voltak („Blur",
„Steps", „Smoothing", „Black Color"…). Az eredeti programnak zárt szótára
volt erre: a `Picasa3i18n.dll` `ImageFilters` osztálya 69 vezérlő-feliratot
tartalmaz, mind a 41 nyelven — magyarul is. A szótár a repóban:
`docs/specs/picasa-effekt-feliratok.md`.

Ez a teszt három dolgot őriz:

1. a katalógus (`app/effect_params.py`) az EREDETI angol feliratot használja
   ott, ahol a vezérlőnek van eredeti megfelelője;
2. minden katalógus-felirathoz tartozik `case` ág a QML fordító-segédben
   (`EditorParamPanel.paramLabel`) — enélkül a felirat némán angolul
   maradna a magyar felületen is;
3. a magyar fordítás a szótár SZERINTI szó, nem a mi találgatásunk.

A 3. pont a lényeg: a felhasználó a régi programból ezeket a szavakat
ismeri, és több eredeti elnevezés nem magától értetődő (`Fade` = „Fokozat",
`Bloom` = „Hamvasság", `Blur` = „Méret").
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from picasapy.app.effect_params import effect_params

_REPO_ROOT = Path(__file__).resolve().parents[2]
_QML_PATH = (
    _REPO_ROOT
    / "src"
    / "picasapy"
    / "app"
    / "qml"
    / "PicasaPy"
    / "EditorParamPanel.qml"
)
_TS_PATH = _REPO_ROOT / "src" / "picasapy" / "app" / "i18n" / "picasapy_hu.ts"

#: A QML fordító-segéd kontextusa a `.ts`-ben (a fájlnév adja).
_QML_CONTEXT = "EditorParamPanel"

#: Effekt → (vezérlő-kulcs, EREDETI angol felirat). Forrás: a #600 jegy
#: effektenkénti táblázata, illetve a `picasa-effekt-feliratok.md` szótára.
#: Csak azok a vezérlők szerepelnek, amelyeknek az eredetiben egyértelmű
#: megfelelőjük van — ahol a vezérlő-készletünk maga tér el az eredetitől
#: (pl. `pencilsketch`, `comicize`), ott a felirat sem vezethető le, azt a
#: jegy külön rögzíti.
_EREDETI_FELIRATOK: tuple[tuple[str, str, str], ...] = (
    ("dropshadow", "blur", "Size"),
    ("vignette", "blur", "Size"),
    ("vignette", "color", "Vignette Color"),
    ("matte", "blur", "Size"),
    ("matte", "color", "Matte Color"),
    ("holga", "blur", "Size"),
    ("lomo", "blur", "Size"),
    ("quantizepalette", "steps", "Number of Colors"),
    ("quantizepalette", "smoothing", "Detail"),
    ("twotone", "black_color", "First Color"),
    ("twotone", "white_color", "Second Color"),
    ("sixties", "rounded", "Rounded Corners"),
    ("boost", "strength", "Impact"),
)

#: A szótár magyar oldala — csak az általunk ténylegesen használt feliratok.
#: Forrás: `docs/specs/picasa-effekt-feliratok.md` (a `Picasa3i18n.dll`
#: `ImageFilters` osztálya). Ahol a korábbi fordításunk mást mondott, az
#: ELTÉRÉS a lényeg: `Fade` nem „Elhalványítás", hanem „Fokozat".
_EREDETI_MAGYAR: dict[str, str] = {
    "Amount": "Mennyiség",
    "Angle": "Szög",
    "Background Color": "Háttérszín",
    "Blend Mode": "Keverési mód",
    "Bloom": "Hamvasság",
    "Brightness": "Fényerő",
    "Caption Height": "Képfelirat magassága",
    "Contrast": "Kontraszt",
    "Corner Radius": "Sarok sugara",
    "Detail": "Részletek",
    "Distance": "Távolság",
    "Fade": "Fokozat",
    "First Color": "Első szín",
    "Grain": "Szemcsésség",
    "Hue": "Színezet",
    "Impact": "Hatás",
    "Inner Color": "Belső szín",
    "Inner Thickness": "Belső keret",
    "Intensity": "Intenzitás",
    "Lighten": "Világosítás",
    "Matte Color": "Matt szín",
    "Number of Colors": "Színek száma",
    "Outer Color": "Külső szín",
    "Outer Thickness": "Külső keret",
    "Radius": "Sugár",
    "Rotate": "Forgatás",
    "Rounded Corners": "Sarkok lekerekítése",
    "Second Color": "Második szín",
    "Shadow Color": "Árnyékszín",
    "Size": "Méret",
    "Strength": "Erősség",
    "Vignette Color": "Vignetta színe",
}


def _katalogus_feliratok() -> set[str]:
    """Minden felirat, ami a vezérlő-katalógusból a felületre kerülhet."""
    nevek = (
        "unsharp sat glow2 radblur radsat tint dir_tint boost soften focalzoom "
        "pencilsketch neon comicize border dropshadow museummatte polaroid "
        "pixelate vignette matte hdr localcontrast orton holga lomo ir "
        "crossprocess nightvision heatmap quantizepalette twotone roundededges "
        "sixties picnikgrain"
    ).split()
    return {param.label for nev in nevek for param in effect_params(nev)}


def _qml_case_feliratok() -> set[str]:
    """A `paramLabel()` switch-ágai a QML-ből, forrásszöveg szerint."""
    forras = _QML_PATH.read_text(encoding="utf-8")
    return set(re.findall(r'case "([^"]+)": return qsTr\("[^"]+"\)', forras))


def _magyar_forditasok() -> dict[str, str]:
    """A `.ts` befejezett magyar bejegyzései a QML-segéd kontextusában."""
    gyoker = ET.parse(_TS_PATH).getroot()
    talalt: dict[str, str] = {}
    for kontextus in gyoker.findall("context"):
        if kontextus.findtext("name") != _QML_CONTEXT:
            continue
        for uzenet in kontextus.findall("message"):
            forditas = uzenet.find("translation")
            if forditas is None or forditas.get("type") == "unfinished":
                continue
            talalt[uzenet.findtext("source")] = forditas.text or ""
    return talalt


@pytest.mark.parametrize(("effekt", "kulcs", "felirat"), _EREDETI_FELIRATOK)
def test_a_katalogus_az_eredeti_feliratot_hasznalja(effekt, kulcs, felirat):
    """A kitalált angol nevek helyén az eredeti Picasa-felirat áll."""
    vezerlok = {param.key: param for param in effect_params(effekt)}
    assert kulcs in vezerlok, f"a(z) {effekt!r} effektnek nincs {kulcs!r} vezérlője"
    assert vezerlok[kulcs].label == felirat


def test_minden_katalogus_felirathoz_van_qml_ag():
    """Ami a katalógusban felirat, azt a QML-segédnek fordítania kell.

    Enélkül a `default: return key` ág angolul engedné ki a szöveget a
    magyar felületre — némán, hibaüzenet nélkül.
    """
    hianyzo = sorted(_katalogus_feliratok() - _qml_case_feliratok())
    assert not hianyzo, f"nincs qsTr-ág ezekre a feliratokra: {hianyzo}"


@pytest.mark.parametrize(("angol", "magyar"), sorted(_EREDETI_MAGYAR.items()))
def test_a_magyar_felirat_a_picasa_sajat_szava(angol, magyar):
    """A fordítás a `Picasa3i18n.dll` `ImageFilters` szótárából való."""
    forditasok = _magyar_forditasok()
    assert angol in forditasok, f"nincs befejezett magyar fordítás: {angol!r}"
    assert forditasok[angol] == magyar
