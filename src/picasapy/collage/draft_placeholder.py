"""A piszkozat HELYKITÖLTŐ képe (#1072) — ettől látszik a Kollázsok albumban.

## Miért van egyáltalán

A tulajdonos jelentése a v0.8.20-ról: *„A friss képkollázs piszkozat
mentése nem jelenik meg a PicasaPy és Picasa alatt sem."*

Az eredeti Picasa a piszkozat mentésekor **azonnal** ír egy képet a
`.cxf` mellé, és ettől jelenik meg a piszkozat az albumban — nem kell
hozzá újraindítás. A tulajdonos képernyőképe ezt megerősítette:

```
Kollázsok > AI10.jpg   2026. 08. 20. 11:56:44   640x453 képpont   46 KB   (11/11)
```

Három dolog olvasható ki belőle, és mindhárom mérés, nem következtetés:

1. **a fájl a kollázs VÉGLEGES nevén áll** (`AI10.jpg`), nem `autosave.jpg`
   néven — a binárisban `autosave.jpg` string nincs is;
2. **640 képpont a HOSSZABB élen**, a lap oldalarányával (640 × 453 =
   1,4128 ≈ A4 fekvő). Nem fix 640 × 480, ahogy korábban feltettük;
3. a **„PISZKOZAT" felirat MAGÁBA A KÉPBE** van rajzolva — a státuszsor a
   sima fájlnevet mutatja, a felirat viszont a bélyegképen is ott van.

## ⚠️ Amit korábban tévesen „ismeretlen illusztrációnak" hittünk

Első olvasatra a képernyőképen egy rajzolt grafika látszott (halványlila
alap, minta-polaroidok), és eltérést jelentettem be helyette. **A
tulajdonos helyreigazított, és igaza volt:**

> „A screenshot közepére bekicsinyedett a kollázs piszkozata a »PISZKOZAT«
> felirattal, és **a kollázs beállításaiban állítottam be azt a színt**."

Vagyis a helykitöltőben **semmi kitalálandó nincs**:

* a „halványlila alap" = a projekt **saját háttérszíne**,
* a „minta-polaroidok" = **maga a piszkozat**, kicsiben,
* a „kicsinyítés" = egyszerűen a **640 képpontos** kimenet az 5120 helyett;
  a Képkupac magától hagy margót a lap szélén.

Ezért ez a modul **ugyanazzal a rajzolóval és ugyanazokkal a
beállításokkal** dolgozik, mint a végleges mentés — csak kisebb lappal.

⚠️ **Feltételes marad:** a kicsinyítés pontos mértékét, a betűméretet és a
felirat helyét a tulajdonos `AI10.jpg`-jéből kell megmérni. Amíg az nincs
meg, ezek a mi értékeink.
"""

from __future__ import annotations

import cv2
import numpy as np

#: A helykitöltő HOSSZABB éle képpontban (mérve: 640 × 453).
PLACEHOLDER_LONG_EDGE = 640

#: A felirat színe: fehér, ahogy a képernyőképen.
_TEXT_BGR = (255, 255, 255)

#: ⚠️ Sötétítő sáv a felirat mögött NINCS. Az első változatomban volt egy —
#: „hogy világos kollázson is olvasható legyen" —, de az a tulajdonos
#: képernyőképén NEM látszik, tehát KITALÁLT elem volt. A tulajdonos
#: kifejezett utasítása (2026-08-20): „Minden UGYANÚGY működjön a kollázs
#: kapcsán, ahogy az eredeti Picasa tette. Semmi »kitaláljuk« funkció."


def placeholder_size(page_ratio: float) -> tuple[int, int]:
    """A helykitöltő mérete (szélesség, magasság) a lap arányából.

    A hosszabb él mindig `PLACEHOLDER_LONG_EDGE`. Fekvő lapon a szélesség,
    állón a magasság a korlát — ugyanaz a szabály, mint a végleges kimeneten
    (`collage_output.output_width`), csak kisebb számmal."""
    if page_ratio <= 0.0:
        raise ValueError(f"Érvénytelen laparány: {page_ratio}")
    if page_ratio <= 1.0:
        szeles = PLACEHOLDER_LONG_EDGE
        magas = max(1, round(PLACEHOLDER_LONG_EDGE * page_ratio))
    else:
        magas = PLACEHOLDER_LONG_EDGE
        szeles = max(1, round(PLACEHOLDER_LONG_EDGE / page_ratio))
    return (szeles, magas)


def draw_draft_label(image: np.ndarray, text: str) -> np.ndarray:
    """A „PISZKOZAT" felirat a kép KÖZEPÉRE, nagy fehér betűkkel.

    A `text` a honosítási táblából jön (`projectutils::draft`) — nem itt
    fogalmazzuk meg."""
    if image.size == 0:
        raise ValueError("Üres kép")
    magas, szeles = image.shape[:2]
    betu = cv2.FONT_HERSHEY_DUPLEX
    # a felirat a szélesség ~70%-át töltse ki
    meret = 1.0
    vastag = max(1, round(szeles / 220))
    (sz, ma), _alap = cv2.getTextSize(text, betu, meret, vastag)
    if sz > 0:
        meret *= (szeles * 0.7) / sz
        vastag = max(1, round(szeles / 220))
        (sz, ma), _alap = cv2.getTextSize(text, betu, meret, vastag)

    kimenet = image.copy()
    cv2.putText(
        kimenet,
        text,
        ((szeles - sz) // 2, (magas + ma) // 2),
        betu,
        meret,
        _TEXT_BGR,
        vastag,
        cv2.LINE_AA,
    )
    return kimenet


__all__ = [
    "PLACEHOLDER_LONG_EDGE",
    "draw_draft_label",
    "placeholder_size",
]
