"""A Picasa `filters=` lánc gyakori-javítás műveletei numpy/OpenCV képeken.

Minden függvény TISZTA: RGB `uint8` numpy tömböt (H, W, 3 alakú) kap, és
ÚJ tömböt ad vissza — a bemenetet sosem mutálja (immutabilitás).

Az `autolight` (Auto Contrast), `autocolor` (Auto Colour) és `enhance` (Jó
napom van) mindhárom a #535/#540 mérésekben megfejtett, hisztogram-
darabszám alapú lineáris szinthúzás egy-egy változata — de HÁROM KÜLÖN
modell (#540, 12-12 referencia-képpáron mérve):

- `autolight`: KÖZÖS (mindhárom csatornán azonos) vágás — nincs
  fehéregyensúly-hatása.
- `autocolor`: csatornánként KÜLÖN vágás, de a csatornák egy KÖZÖS
  (a csatornánkénti vágópontok átlagából számolt) kimeneti tartományra
  simulnak — nem nyújtja mindegyiket önállóan 0..255-re (az a modell
  a mérésen jóval rosszabbul illeszkedett, ld. #540).
- `enhance` ("Jó napom van"): csatornánként KÜLÖN vágás, ÉS mindegyik
  önállóan a teljes 0..255 tartományra nyúlik (#535).
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.ini.rect64 import Rect64
from picasapy.render.curves import (
    apply_channel_luts,
    apply_lut,
    lut_ramp,
    validate_image,
)

_REDEYE_DOMINANCE_RATIO = 1.4
_REDEYE_MIN_RED = 60
#: A `count_redeye_spots` zajszűrése: ennél kevesebb ÖSSZEFÜGGŐ pixelből
#: álló folt nem számít külön „szemnek". Szándékosan ABSZOLÚT (nem a
#: képmérethez arányosított) küszöb: a szűrendő jelenség — a JPEG-tömörítés
#: néhány pixeles vörös szórványa — szintén abszolút méretű, egy arányos
#: küszöb pedig nagy képen a távolabbi arcok valódi pupilláit is kidobná.
_REDEYE_MIN_SPOT_PIXELS = 6

# Vágási arányok az autolight/autocolor/enhance hisztogram-darabszám alapú
# szinthúzásához — a valódi Picasa a hisztogramban DARABSZÁM-küszöbbel
# keresi a fekete/fehér pontot (#535), nem fix percentilissel; ez a két
# konstans egy MÉRÉSSEL igazolt közelítés, és a #540 szerint MINDHÁROM
# művelet ugyanezt használja (az összemérhetőség kedvéért — a pontos
# küszöbérték finomítása a #539 dolga). Ld. `sanchomuzax/picasapy-agent`
# privát repó `referencia/imfeellucky/`, `referencia/autocontrast/`,
# `referencia/autocolor/`.
_LEVELS_LOW_FRACTION = 0.005
_LEVELS_HIGH_FRACTION = 0.002

_validate_image = validate_image


def _rect_to_pixels(rect: Rect64, width: int, height: int) -> tuple[int, int, int, int]:
    """Relatív [0..1] Rect64 → pixel-koordináták (left, top, right, bottom)."""
    left = round(rect.left * width)
    top = round(rect.top * height)
    right = round(rect.right * width)
    bottom = round(rect.bottom * height)
    return left, top, right, bottom


def apply_crop(image: np.ndarray, rect: Rect64) -> np.ndarray:
    """Kivágás a relatív [0..1] `rect` koordináták alapján, pixelre pontosan.

    Üres (nulla szélességű/magasságú) kivágásnál ValueError.
    """
    _validate_image(image)
    height, width = image.shape[:2]
    left, top, right, bottom = _rect_to_pixels(rect, width, height)
    if right <= left or bottom <= top:
        raise ValueError(
            f"Üres kivágás: rect={rect} -> pixel=({left}, {top}, {right}, {bottom})"
        )
    return image[top:bottom, left:right].copy()


def apply_tilt(image: np.ndarray, angle: float, scale: float) -> np.ndarray:
    """Döntés (forgatás) a kép közepe körül + skálázás, bilineáris mintavétellel.

    `angle` radiánban értendő (a hívó felelőssége a Picasa nyers
    szög-paraméterének radiánra váltása). A kimenet mérete megegyezik a
    bemenetével (levágás/kitöltés a warpAffine perem-viselkedése szerint).
    """
    _validate_image(image)
    if scale <= 0:
        raise ValueError(f"A skála pozitív kell legyen, nem {scale}")
    height, width = image.shape[:2]
    center = (width / 2.0, height / 2.0)
    angle_deg = np.degrees(angle)
    matrix = cv2.getRotationMatrix2D(center, angle_deg, scale)
    return cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


def _histogram_black_white_point(
    values: np.ndarray, total: int, low_fraction: float, high_fraction: float
) -> tuple[int, int]:
    """Fekete-/fehérpont a hisztogram DARABSZÁMA alapján (#549).

    A fekete pont az a legkisebb érték, aminél a kumulált darabszám már
    eléri a `low_fraction`·`total` küszöböt; a fehérpont ugyanígy, felülről
    számolva `high_fraction`-nel.

    **Invariáns: a visszaadott párra MINDIG `low < high`.** Ha a küszöbök
    nem hagynának érdemi tartományt, `(0, 255)` — az azonosság-eset. A hívók
    erre a garanciára építenek (nem ellenőrzik újra).

    Args:
        values: A hisztogramba öntendő értékek (a teljes kép vagy egy
            csatorna) — az alakja közömbös.
        total: A küszöbök viszonyítási darabszáma. Csatornánkénti hívásnál
            a képpontok száma, közösnél a csatorna-értékeké (`image.size`).
    """
    low_count = total * low_fraction
    high_count = total * high_fraction
    histogram, _ = np.histogram(values, bins=256, range=(0, 256))
    low = int(np.searchsorted(np.cumsum(histogram), low_count))
    high_from_top = int(np.searchsorted(np.cumsum(histogram[::-1]), high_count))
    high = 255 - high_from_top
    if high <= low:
        return 0, 255
    return low, high


def _common_black_white_point(
    image: np.ndarray, low_fraction: float, high_fraction: float
) -> tuple[int, int]:
    """KÖZÖS (mindhárom csatornára egyenlő) fekete-/fehérpont — a három
    csatorna képpontjait EGY közös hisztogramba összeöntve (#540: az Auto
    Contrast mind a 12 referencia-képen azonos meredekséget adott
    mindhárom csatornán, szórás 0,001).
    """
    return _histogram_black_white_point(
        image, image.size, low_fraction, high_fraction
    )


def apply_autolight(image: np.ndarray) -> np.ndarray:
    """Auto Contrast — megfejtett algoritmus (#540).

    KÖZÖS (mindhárom csatornára azonos) lineáris szinthúzás, a fekete-/
    fehérpontot a hisztogram DARABSZÁMA alapján keresve (ugyanaz a
    közelítés, mint a #535 „Jó napom van"-nál, `_LEVELS_LOW_FRACTION`/
    `_LEVELS_HIGH_FRACTION` küszöbbel): `ki = (be − lo)·255/(hi − lo)`,
    egyetlen `lo`/`hi` az egész képre. **Azonosság-eset:** ha a kép már
    kihasználja a teljes tartományt (`lo == 0` és `hi == 255`), a kimenet
    bájtra azonos a bemenettel.
    """
    _validate_image(image)
    low, high = _common_black_white_point(
        image, _LEVELS_LOW_FRACTION, _LEVELS_HIGH_FRACTION
    )
    if low == 0 and high == 255:
        return image.copy()
    scale = 255.0 / (high - low)
    # pontonkénti lineáris széthúzás → 256 elemű LUT (#140): képméret-független
    return apply_lut(image, (lut_ramp() - low) * scale)


#: A natív elemzés a kép SZÉLEIT kihagyja: a hisztogram csak a középső
#: 90% × 90%-ról készül (`0x009db610`, #576 dekompiláció, #539 méréssel
#: igazolva). Keretes, vignettált vagy sötét szélű képnél ez érdemben más
#: fekete-/fehérpontot ad, mint a teljes képes elemzés.
_LEVELS_MARGIN_PERCENT = 5

#: A vágási küszöb DARABSZÁM, nem percentilis: a TELJES kép képpontszámának
#: 1/200-a (0,5%), és — a natív kód szerint — mindkét végén UGYANANNYI.
#: A #539 mérése ezt megerősítette: az aszimmetrikus (alul 0,5% / felül
#: 0,2%) közelítésnél minden aszimmetrikus variáns rosszabb lett.
_LEVELS_CLIP_DIVISOR = 200


def _analysis_region(image: np.ndarray) -> np.ndarray:
    """A hisztogram-elemzés területe: a kép középső 90% × 90%-a."""
    height, width = image.shape[:2]
    margin = _LEVELS_MARGIN_PERCENT
    top = height * margin // 100
    left = width * margin // 100
    return image[top : height * (100 - margin) // 100, left : width * (100 - margin) // 100]


def _channel_black_white_points(
    image: np.ndarray,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Csatornánkénti fekete-/fehérpont a natív algoritmus szerint (#539).

    A `0x009db610` natív függvény geometriája: a hisztogram a kép középső
    90% × 90%-áról készül, a vágási küszöb pedig a TELJES kép
    képpontszámának `1/_LEVELS_CLIP_DIVISOR`-a, mindkét végén azonosan.
    Az azonosság-esetet (nincs érdemi tartomány) `(0, 255)` jelzi.
    """
    height, width = image.shape[:2]
    clip = max(1, (height * width) // _LEVELS_CLIP_DIVISOR)
    region = _analysis_region(image)
    # a `total`-nak magát a vágási darabszámot adjuk 1,0-s aránnyal: így a
    # küszöb pontosan `clip`, kerekítési hiba nélkül
    points = tuple(
        _histogram_black_white_point(region[..., channel], clip, 1.0, 1.0)
        for channel in range(3)
    )
    return points[0], points[1], points[2]


#: Az Auto Colour „semleges pixel"-szűrője (#541): csak azok a képpontok
#: számítanak bele a fehéregyensúlyba, ahol a telítettség
#: (`(max−min)/max`) ez alatt marad. A `referencia/autocolor/` 12 képén
#: mért optimum — a hiba 0,36-nál 2,89, 0,40-nél **2,35**, 0,44-nél 2,53,
#: 0,8-nál már 8,3 (ott a telített képrészletek elhúzzák a becslést).
_AUTOCOLOR_MAX_SATURATION = 0.40

#: A túl sötét képpontok kizárása: ott a csatorna-arányok a JPEG-zajtól
#: bizonytalanok. A pontos érték alig számít (0/15/30/60 mellett a hiba
#: 2,37 / 2,36 / 2,35 / 2,34), ezért a középső, józan értéket használjuk.
_AUTOCOLOR_MIN_LEVEL = 30.0

#: Ennyi semleges képpont alatt nincs mire alapozni a becslést — a kép
#: változatlan marad.
_AUTOCOLOR_MIN_PIXELS = 1000


def autocolor_gains(image: np.ndarray) -> tuple[float, float, float]:
    """Az Auto Colour csatorna-erősítései (#541).

    A SEMLEGES képpontokra (telítettség < `_AUTOCOLOR_MAX_SATURATION`,
    világosság > `_AUTOCOLOR_MIN_LEVEL`) számolt szürkevilág-becslés: a
    három csatorna átlaga a saját átlagához viszonyítva. Ezek a képpontok
    az eredetiben is szürkék lennének, tehát az eltérésük tiszta
    színinger — a telített képrészletek (virág, égbolt) viszont nem, ezért
    maradnak ki.
    """
    values = image.astype(np.float32)
    maximum = values.max(axis=2)
    minimum = values.min(axis=2)
    saturation = (maximum - minimum) / np.maximum(maximum, 1.0)
    mask = (saturation < _AUTOCOLOR_MAX_SATURATION) & (maximum > _AUTOCOLOR_MIN_LEVEL)
    if int(mask.sum()) < _AUTOCOLOR_MIN_PIXELS:
        return (1.0, 1.0, 1.0)
    channel_means = np.array(
        [float(values[..., channel][mask].mean()) for channel in range(3)]
    )
    if float(channel_means.min()) <= 0.0:
        return (1.0, 1.0, 1.0)
    gains = channel_means.mean() / channel_means
    return (float(gains[0]), float(gains[1]), float(gains[2]))


def apply_autocolor(image: np.ndarray) -> np.ndarray:
    """Auto Colour — csatornánkénti ERŐSÍTÉS a semleges képpontokra
    számolt szürkevilág-becslés szerint (#541).

    A `referencia/autocolor/` 12 kép-párja három dolgot mondott ki:

    1. **Tiszta csatornánkénti LINEÁRIS leképezés.** A bemeneti értékek
       vödrein belül a kimenet szórása 0,7–3,7 — vagyis JPEG-zaj, semmi
       más: nincs se térbeli, se kereszt-csatornás összetevő.
    2. **A feketepont NEM mozdul.** Mind a 36 csatorna-esetben az
       illesztett `lo` 0 körül van (−4,5 … +4,2), tehát ez NEM
       szinthúzás, hanem tiszta erősítés: `ki = be · gain`.
    3. **Az erősítés a semleges képpontok szürkevilág-becslése.** A
       telített képrészleteket kizárva a becslés a 12 képen jól illeszkedik.

    Mért átlagos csatorna-eltérés a valódi Picasa-kimenettől:

        a korábbi (közös célsávra simító) modell ....... 7,45
        az ÉRINTETLEN kép ............................. 5,29
        EZ a modell ................................... 2,35
        a MÉRT erősítésekkel (elméleti alsó korlát) ... 1,08

    Vagyis a modell alakja bizonyítottan helyes (az „orákulum" 1,08 a
    JPEG-újratömörítés zaja), és a becslő is a felét hozza a maradéknak.
    A pontos becslő-képlet (miért épp ennyire tér el 12 képből 3-nál)
    továbbra is nyitott — de a modell már **kétszer jobb az azonosságnál**,
    nem rosszabb nála.

    **Azonosság-eset:** szürkeárnyalatos képen a három csatorna-átlag
    megegyezik, így mindhárom erősítés pontosan 1,0 — a kimenet bájtra
    azonos a bemenettel (a mérésben két ilyen kép van, mindkettőt a Picasa
    is változatlanul hagyta).
    """
    _validate_image(image)
    gains = autocolor_gains(image)
    if gains == (1.0, 1.0, 1.0):
        return image.copy()
    ramp = lut_ramp()
    luts = tuple(ramp * gain for gain in gains)
    return apply_channel_luts(image, (luts[0], luts[1], luts[2]))


#: A szinthúzás legkisebb bemeneti tartománya (#539). Egy nagyon szűk
#: hisztogramú csatornát a Picasa NEM feszít ki a teljes 0..255-re: a
#: `referencia/imfeellucky/` „Utopic Unicorn" képén (az egyetlen szélső eset
#: a 12-ből) a két szűk csatorna kimért bemeneti tartománya **58,1** és
#: **59,2** — gyakorlatilag ugyanaz a szám, holott a nyers tartományuk 35 és
#: 41 volt. A korlát a FEKETEPONTOT tartja és a fehérpontot tolja feljebb
#: (`lo`-hoz horgonyozva): a három lehetséges horgony közül ez illeszkedik,
#: a középre igazítás 5,30-at, a fehérponthoz igazítás 8,4-et adna.
#:
#: Hatás a 12 referencia-páron: az átlagos eltérés **5,48 → 2,68**, és
#: kizárólag a kiugró kép változik (46,0 → 12,4) — a többi tizenegy kép
#: eltérése bájtra ugyanaz marad. A pontos érték széles optimum (52-nél
#: 2,65, 64-nél 2,70), ezért a KÖZVETLENÜL MÉRT 58-at használjuk.
#:
#: #539 megerősítés: mind a 36 csatornán (12 kép × 3) kimérve a Picasa
#: által ALKALMAZOTT bemeneti tartomány LEGKISEBB értéke **58,1** — soha
#: nem megy alá, holott a nyers vágópontok 26-ig lemennek. A korlát tehát
#: nem illesztési fogás, hanem a natív viselkedés (a `gain` felső korlátja).
_MIN_STRETCH_SPAN = 58.0


def apply_channel_levels_stretch(image: np.ndarray) -> np.ndarray:
    """Csatornánként KÜLÖN lineáris szinthúzás: `ki = (be − lo)·255/(hi − lo)`.

    Ez a „Jó napom van" (I'm Feeling Lucky) és az `AutoFix` megfejtett
    modellje (#535, 12 referencia-képpáron R² = 0,9995–1,0000 illesztéssel
    igazolva). **Azonosság-eset:** ha egy csatorna `lo`/`hi`-je már `0`/`255`
    (a csatorna kihasználja a teljes tartományt), azt a csatornát a Picasa
    NEM módosítja — itt sem változik semmi (bájtra azonos marad).

    #539: a vágópontok a natív geometriával készülnek
    (`_channel_black_white_points`), a nagyon szűk hisztogramú csatornát
    pedig a Picasa nem feszíti ki teljesen — a bemeneti tartomány alsó
    korlátja `_MIN_STRETCH_SPAN`.
    """
    _validate_image(image)
    points = _channel_black_white_points(image)
    ramp = lut_ramp()
    luts = []
    for low, high in points:
        if low == 0 and high == 255:
            luts.append(ramp)
            continue
        span = max(float(high - low), _MIN_STRETCH_SPAN)
        luts.append((ramp - low) * 255.0 / span)
    return apply_channel_luts(image, (luts[0], luts[1], luts[2]))


def apply_enhance(image: np.ndarray) -> np.ndarray:
    """„Jó napom van" (I'm Feeling Lucky) — megfejtett modell (#535):

    csatornánként KÜLÖN, hisztogram-darabszám alapú lineáris szinthúzás
    (`apply_channel_levels_stretch`) — nincs benne gamma, S-görbe, helyi
    kontraszt vagy külön árnyék-/csúcsfény-emelés (ld. az adott függvény
    docstringjét a bizonyítékért).
    """
    _validate_image(image)
    return apply_channel_levels_stretch(image)


def apply_redeye(
    image: np.ndarray, regions: tuple[Rect64, ...] = ()
) -> np.ndarray:
    """Vörösszem-eltávolítás a megadott régiókban (üres esetén az egész képen).

    Konzervatív színküszöb: a pixel akkor "vörösszem", ha a piros csatorna
    dominál a zöld és a kék felett (`R > _REDEYE_DOMINANCE_RATIO * G` és
    `R > _REDEYE_DOMINANCE_RATIO * B`) és `R >= _REDEYE_MIN_RED` — ez a
    küszöb a normál bőrtónusokat (ahol R, G, B közel esik egymáshoz)
    szándékosan nem érinti. A találati pixeleknél a piros csatornát a
    zöld/kék átlagára csillapítjuk.
    """
    _validate_image(image)
    height, width = image.shape[:2]
    result = image.copy()

    if regions:
        mask = np.zeros((height, width), dtype=bool)
        for rect in regions:
            left, top, right, bottom = _rect_to_pixels(rect, width, height)
            mask[max(top, 0) : max(bottom, 0), max(left, 0) : max(right, 0)] = True
    else:
        mask = np.ones((height, width), dtype=bool)

    green = image[..., 1].astype(np.int32)
    blue = image[..., 2].astype(np.int32)
    red_eye_mask = mask & _redeye_pixel_mask(image)

    average_green_blue = ((green + blue) / 2).astype(np.uint8)
    result[..., 0] = np.where(red_eye_mask, average_green_blue, result[..., 0])
    return result


def _redeye_pixel_mask(image: np.ndarray) -> np.ndarray:
    """A vörösszem-színküszöb bool maszkja (ld. `apply_redeye` docsztring)."""
    red = image[..., 0].astype(np.int32)
    green = image[..., 1].astype(np.int32)
    blue = image[..., 2].astype(np.int32)
    return (
        (red >= _REDEYE_MIN_RED)
        & (red > _REDEYE_DOMINANCE_RATIO * green)
        & (red > _REDEYE_DOMINANCE_RATIO * blue)
    )


def count_redeye_spots(image: np.ndarray) -> int:
    """Hány KÜLÖNÁLLÓ vörösszem-folt van a képen (#445).

    Az `apply_redeye` maszkjának összefüggő komponensei, a
    `_REDEYE_MIN_SPOT_PIXELS`-nél kisebb (jellemzően zaj- vagy tömörítési
    eredetű) foltok kihagyásával. Csak a felhasználói
    visszajelzéshez („Picasa has found and corrected red eye(s)") kell — a
    javítás maga továbbra is pixel-maszkkal dolgozik, nem foltonként.
    """
    _validate_image(image)
    mask = _redeye_pixel_mask(image).astype(np.uint8)
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    # a 0. komponens a háttér (a maszkon kívüli pixelek) — kihagyva
    return int(
        sum(
            1
            for i in range(1, count)
            if stats[i, cv2.CC_STAT_AREA] >= _REDEYE_MIN_SPOT_PIXELS
        )
    )
