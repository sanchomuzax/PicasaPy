"""A vetett árnyék CSEMPÉJE az élő vászonhoz (#1021).

A #977 az árnyékot a magba építette be, így a **mentett kép** témánként
helyes árnyékot kap. Az **élő vászon** viszont QML jelenetgráf, ott
`cv2.GaussianBlur` nem fut. Ez a modul azt a hidat adja, amin a
jelenetgráf UGYANAZT az árnyékot tudja kirajzolni.

## Miért nem `MultiEffect`

A kézenfekvő út a `QtQuick.Effects.MultiEffect` (`shadowEnabled`,
`shadowBlur`) volna. **Mérve nem járható:** a felhasználó gépén a modul
nincs telepítve —

    <Unknown File>:2:1: module "QtQuick.Effects" is not installed

— (Debian, disztribúciós PySide6 6.8.2 a rendszer Qt 6.8.2-je fölött), a CI
viszont `pip install PySide6`-ot használ, ahol a modul MEGVAN. Egy
shader-alapú megoldás tehát **zöld CI mellett** hagyta volna árnyék nélkül
azt a gépet, amelyikről a bejelentés jött. A `shadowBlur` normalizált
skálájának megfejtése ezért tárgytalanná vált: nincs mit skálázni.

## A csempe geometriája — miért PONTOS, és nem közelítés

A spec 9/b.1 szerint a raszterizáló „külön X és Y irányú lecsengés
**szorzatát**" adja: az árnyék tehát **szeparábilis** elmosás egy
téglalapon. Egy ilyen kép kilenc szeletre bontva **pontosan** újraépíthető:

* a **sarkok** a kétirányú lecsengés szorzatát viselik — ezeket változtatás
  nélkül kell kitenni;
* az **élek** egy tengely mentén állandók — ott a nyújtás nem torzít;
* a **közép** telített (1,0) — ott a nyújtás végképp nem torzít.

Ezt csinálja a QML `BorderImage` `Stretch` módban. A csempe tehát nem
„elég jó közelítés": a `tests/collage/test_shadow_sprite_1021.py` a
visszaépített képet a mag `draw_shadow`-jához méri, és az eltérés
**2/255 alatt** marad — annyi, amennyi a 3·szórásos támasz csonkolásából
adódik.

## A két méret, amit el lehet rontani

| név | érték | miért |
|---|---|---|
| `sprite_support` (haló) | `ceil(elmosás · 1,5)` | UGYANAZ, mint a mag `draw_shadow` `növekmény`-e |
| `sprite_border` (szegély) | `2 · haló` | az átmenet a csempe éle KÖRÜL zajlik: befelé is, kifelé is egy haló |

Ha a szegély csak egyszeres volna, a nyújtott középső sáv nem telített
képpontokat nyújtana — a nagy csempéken elmosódott csík keletkezne.

A csempe **`data:` URL-ként** megy a QML-nek, nem képszolgáltatón: így
bármelyik motorban működik (a teszt-`QQuickView`-ban is, ahol nincs
regisztrált szolgáltató), és a Qt a képet az URL szövege alapján gyorsítja
— 350 csomópont EGY textúrát oszt meg.
"""

from __future__ import annotations

import base64
import math
from functools import lru_cache

import cv2
import numpy as np

from .shadow import BLUR_TO_SIGMA, BOUNDS_GROWTH_FACTOR

#: A csempe nyújtott közepe képpontban. Kettő elég: a `BorderImage` ezt a
#: sávot húzza szét a csempe teljes belsejére, és a sáv telített.
SPRITE_MIDDLE = 2

#: A `data:` URL előtagja — egy helyen, hogy a teszt is ezt lássa.
DATA_URL_PREFIX = "data:image/png;base64,"

#: Az elmosás rasztere. Az ablak átméretezésekor az elmosás folytonosan
#: változna, és minden képpontnyi elmozdulás új PNG-t (és új textúra-betöltést)
#: szülne. Huszad-képpontos raszter mellett a gyorstár értelmes marad, a
#: geometria eltérése pedig egy képpont huszada — láthatatlan.
#:
#: ⚠️ A raszter MINDEN nyilvános függvényre érvényes, nem csak az URL-re: ha
#: a haló a nyers elmosásból, a kép a kerekítettből születne, a `BorderImage`
#: szegélye nem illeszkedne a saját csempéjéhez, és az árnyék eltorzulna.
BLUR_QUANTUM = 0.05

#: Ennyi (elmosás, alfa) párt tartunk. A vászon egyszerre EGY párt használ;
#: a tartalék az átméretezés közbeni ide-oda váltásra és a téma-cserére kell.
_CACHE_SIZE = 32


def quantize_blur(blur: float) -> float:
    """Az elmosás rasztere — MINDEN nyilvános függvény ezen kezdi."""
    return round(float(blur) / BLUR_QUANTUM) * BLUR_QUANTUM


def sprite_support(blur: float) -> int:
    """A haló szélessége képpontban — a mag `növekmény`-ével AZONOS szám.

    A `draw_shadow` a sziluettet `ceil(elmosás · 1,5)` képponttal keretezi
    ki minden élen; a vászon halója ugyanennyi. Aki itt más kerekítést ír,
    az árnyékot más messzire viszi, mint a mentett képen."""
    return max(1, math.ceil(quantize_blur(blur) * BOUNDS_GROWTH_FACTOR))


def sprite_border(blur: float) -> int:
    """A `BorderImage.border` értéke: a haló KÉTSZERESE.

    Az átmenet a csempe éle körül zajlik — a haló befelé és kifelé is
    ennyi —, tehát a szegélynek mindkét felét le kell fednie."""
    return 2 * sprite_support(blur)


def sprite_side(blur: float) -> int:
    """A csempe éle: két szegély és a nyújtott közép."""
    return 2 * sprite_border(blur) + SPRITE_MIDDLE


def sprite_alpha_map(blur: float, alpha: int) -> np.ndarray:
    """A csempe alfa-csatornája — elmosott téglalap, `uint8`.

    A téglalap a csempébe egy halónyival beljebb kerül, és a mag
    szórásával (`elmosás / 2`) mosódik el; így a csempe SZÉLEIN a lecsengés
    éppen elhal, azaz a nyújtás állandó sávokat nyújt."""
    tamasz = sprite_support(blur)
    oldal = sprite_side(blur)
    maszk = np.zeros((oldal, oldal), dtype=np.float32)
    maszk[tamasz : oldal - tamasz, tamasz : oldal - tamasz] = 1.0
    szoras = quantize_blur(blur) * BLUR_TO_SIGMA
    if szoras > 0.0:
        maszk = cv2.GaussianBlur(
            maszk,
            (0, 0),
            sigmaX=szoras,
            sigmaY=szoras,
            borderType=cv2.BORDER_CONSTANT,
        )
    return np.clip(maszk * int(alpha), 0.0, 255.0).astype(np.uint8)


def sprite_png(blur: float, alpha: int) -> bytes:
    """A csempe PNG-ként: FEKETE kép, az információ az alfában.

    Ugyanaz a keverés, amit a mag végez (`vászon · (1 − alfa)`): a QML a
    csempét `source-over` módon rajzolja, tehát fekete szín + képpontonkénti
    alfa pontosan ezt adja."""
    a = sprite_alpha_map(blur, alpha)
    bgra = np.zeros((a.shape[0], a.shape[1], 4), dtype=np.uint8)
    bgra[..., 3] = a
    sikeres, puffer = cv2.imencode(".png", bgra)
    if not sikeres:  # pragma: no cover — a PNG-kódolás nem hibázhat
        raise RuntimeError("Az árnyék-csempe nem kódolható PNG-be.")
    return puffer.tobytes()


@lru_cache(maxsize=_CACHE_SIZE)
def _data_url(blur: float, alpha: int) -> str:
    return DATA_URL_PREFIX + base64.b64encode(sprite_png(blur, alpha)).decode("ascii")


def sprite_data_url(blur: float, alpha: int) -> str:
    """A csempe `data:` URL-je, gyorstárazva.

    A 350 csomópont UGYANEZT az egy URL-t kapja: a Qt a képet az URL
    szövege alapján gyorsítja, tehát egyetlen textúra születik."""
    return _data_url(quantize_blur(blur), int(alpha))


__all__ = [
    "BLUR_QUANTUM",
    "DATA_URL_PREFIX",
    "SPRITE_MIDDLE",
    "quantize_blur",
    "sprite_alpha_map",
    "sprite_border",
    "sprite_data_url",
    "sprite_png",
    "sprite_side",
    "sprite_support",
]
