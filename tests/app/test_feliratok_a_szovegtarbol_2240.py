"""#2240: a Visszavonás-feliratok az EREDETI szövegtárat kövessék.

## Honnan jön az elvárt tábla

Az eredeti Picasa `filter_<kulcs>_label0` erőforrásaiból, a
`picasapy-agent` privát repó `referencia/stringres-en-hu.tsv` fájljából
kimérve (2026-09-04, mind a 83 bejegyzés). A tábla ITT, adatként áll, mert
a nyilvános tesztkészlet nem éri el a referencia-fájlt — ugyanaz a
gyakorlat, mint a `render/registry_data.py`-nál, ami a `filterdesc.xml`-ből
származó adatot tart a kódban.

## Amit ez az őr NEM állít

Nem állítja, hogy a névtár MINDEN bejegyzése helyes — csak azt, hogy a
lemért kulcsokon nem csúszik el a szövegtártól. A `KIVETELEK` szótár
nevesíti, hol térünk el SZÁNDÉKOSAN, és miért; indoklás nélküli eltérést
nem enged.
"""

from __future__ import annotations

import pytest

from picasapy.app.edit_action_names import ACTION_LABELS

#: kulcs -> az eredeti `filter_<kulcs>_label0` angol felirata.
SZOVEGTAR: dict[str, str] = {
    "ansel": "Filtered B&W",
    "bw": "B&W",
    "boost": "Boost",
    "border": "Border",
    "cinemascope": "Cinemascope",
    "comicize": "Comic Book",
    "crop": "Crop",
    "crossprocess": "Cross Process",
    "dir_tint": "Graduated Tint",
    "dropshadow": "Drop Shadow",
    "enhance": "I'm Feeling Lucky",
    "finetune": "Tuning",
    "focalzoom": "Focal Zoom",
    "glow": "Glow (Old)",
    "glow2": "Glow",
    "grain": "Film Grain (Old)",
    "grain2": "Film Grain",
    "hdr": "HDR-ish",
    "heatmap": "Heat Map",
    "holga": "Holga-ish",
    "invert": "Invert Colors",
    "ir": "Infrared Film",
    "localcontrast": "Local Contrast",
    "lomo": "Lomo-ish",
    "matte": "Matte",
    "museummatte": "Museum Matte",
    "neon": "Neon",
    "nightvision": "Night Vision",
    "orton": "Orton-ish",
    "pencilsketch": "Pencil Sketch",
    "picnikgrain": "Film Grain",
    "picniktint": "Tint",
    "pixelate": "Pixelate",
    "polaroid": "Polaroid",
    "quantizepalette": "Posterize",
    "radblur": "Soft Focus",
    "radsat": "Focal B&W",
    "redeye": "Red Eye",
    "retouch": "Retouches",
    "roundededges": "Rounded Edges",
    "sat": "Saturation",
    "sepia": "Sepia",
    "sixties": "1960's",
    "soften": "Soften",
    "tilt": "Straighten",
    "tint": "Tint (Old)",
    "twotone": "Duo-Tone",
    "unsharp": "Sharpen (Old)",
    "unsharp2": "Sharpen",
    "vignette": "Vignette",
    "warm": "Warmify",
}

#: Ahol SZÁNDÉKOSAN eltérünk — kulcs -> indoklás. Üres szótár = nincs
#: kivétel; új tétel csak kimondott okkal kerülhet ide.
KIVETELEK: dict[str, str] = {
    # A „Régi effektek" fül katalógusa (`render/legacy_effects.py`) külön
    # modul és külön felület; ott az eredeti HÁROM párt/hármast azonos
    # felirattal hagy (`autobacklight`/`fill`, `focalpixelate`/
    # `picnikfocalpixelate`, `triple`/`triple2`/`triple3`), ami egy
    # LISTÁBAN megkülönböztethetetlen tételeket adna. Az ottani feliratok
    # átvétele önálló döntés, önálló jeggyel — ez az őr ezért csak a
    # szerkesztő-panel (`EditorPanel`) feliratait méri.
}


@pytest.mark.parametrize("kulcs", sorted(SZOVEGTAR))
def test_a_felirat_a_szovegtarat_koveti(kulcs: str) -> None:
    if kulcs in KIVETELEK:
        pytest.skip(f"nevesített kivétel: {KIVETELEK[kulcs]}")
    assert kulcs in ACTION_LABELS, f"a névtárból hiányzik a(z) {kulcs!r} kulcs"
    assert ACTION_LABELS[kulcs][0] == SZOVEGTAR[kulcs], (
        f"{kulcs}: nálunk {ACTION_LABELS[kulcs][0]!r}, "
        f"az eredeti szövegtárban {SZOVEGTAR[kulcs]!r} — ha az eltérés "
        f"szándékos, vedd fel a KIVETELEK közé INDOKLÁSSAL"
    )


def test_az_or_foga_meglegyen() -> None:
    """Ha a `KIVETELEK` mindent kitakarna, az őr semmit nem őrizne."""
    merve = set(SZOVEGTAR) - set(KIVETELEK)
    assert len(merve) >= 40, (
        f"csak {len(merve)} kulcsot mér az őr — a kivétel-lista kiürítette"
    )
