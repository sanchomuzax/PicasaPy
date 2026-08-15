"""A Picasa `filters=` lánc gyakori-javítás műveletei numpy/OpenCV képeken.

Minden függvény TISZTA: RGB `uint8` numpy tömböt (H, W, 3 alakú) kap, és
ÚJ tömböt ad vissza — a bemenetet sosem mutálja (immutabilitás).

Az `autolight` (Auto Contrast), `autocolor` (Auto Colour) és `enhance` (Jó
napom van) mindhárom a #535/#540 mérésekben megfejtett, hisztogram-
darabszám alapú lineáris szinthúzás egy-egy változata — de HÁROM KÜLÖN
modell (#540, 12-12 referencia-képpáron mérve):

- `autolight`: KÖZÖS (mindhárom csatornán azonos) vágás — nincs
  fehéregyensúly-hatása. A közös vágópont a csatornánkénti pontok UNIÓJA,
  a TELJES kép hisztogramjából (#539, `0x008f80c0` → `0x00a4bfd0`).
- `autocolor`: csatornánként KÜLÖN vágás, de a csatornák egy KÖZÖS
  (a csatornánkénti vágópontok átlagából számolt) kimeneti tartományra
  simulnak — nem nyújtja mindegyiket önállóan 0..255-re (az a modell
  a mérésen jóval rosszabbul illeszkedett, ld. #540).
- `enhance` ("Jó napom van"): csatornánként KÜLÖN vágás, a kép középső
  90% × 90%-áról készült hisztogramból, ÉS mindegyik csatorna önállóan a
  teljes 0..255 tartományra nyúlik (#535, `0x008f8840` → `0x009db610`).

A vágópont-keresés és a leképezés mindkét úton a natív algoritmus szerint
történik: darabszám-küszöb (`_levels_clip_threshold`), a natív keresőciklus
(`_native_clip_points`) és a natív fixpontos átvitel (`_native_levels_lut`).
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

#: A szinthúzás vágási ARÁNYA: a képpontszám fél százaléka, MINDKÉT végén
#: azonosan (#539). A natív kód két helyen mondja ki ugyanezt: a
#: `FUN_00a4be40` a hívási helyről kapott `0.005f` konstanssal
#: (`0x3ba3d70a`), a `0x009db610` pedig egész osztásként, `/200`-zal.
_LEVELS_CLIP_RATIO = 0.005

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


def _levels_clip_threshold(pixel_count: int) -> int:
    """A vágási DARABSZÁM-küszöb: `round(N · 0,005)`, de legalább 1 (#539).

    `N` a MINTAVÉTELEZETT képpontszám: a natív kód a hisztogramot `lépés`
    ritkítással is építheti, ilyenkor `N = W·H / lépés²`. Teljes felbontású
    hisztogramnál `lépés = 1`, tehát `N = W·H`. A küszöb így a képmérettel
    skálázódik — nem abszolút darabszám és nem is percentilis.

    (A két natív helyen a kerekítés csak árnyalatnyit tér el: a
    `FUN_00a4be40` `roundf`-ol, a `0x009db610` egészben oszt `200`-zal —
    egyetlen darabnyi különbség, ezért egy közös segédet használunk.)
    """
    return max(1, int(round(pixel_count * _LEVELS_CLIP_RATIO)))


def _channel_histogram(values: np.ndarray) -> np.ndarray:
    """Egy csatorna 256 rekeszes hisztogramja (uint8 értékekből)."""
    return np.bincount(values.reshape(-1), minlength=256)


def _native_clip_points(histogram: np.ndarray, threshold: int) -> tuple[int, int]:
    """Fekete-/fehérpont a natív ciklusokkal, BETŰ SZERINT (#539).

    ```c
    i = 0;   sum = 0;  do { sum += hist[i]; i++; } while (i <= 255 && sum < kuszob);
    lo = i - 1;
    i = 255; sum = 0;  do { sum += hist[i]; i--; } while (i >= 0  && sum < kuszob);
    hi = i + 1;
    ```

    A ciklus a léptetés UTÁN ellenőriz, ezért a `−1` / `+1`: a vágópont AZ a
    szint, amelyiknél a kumulált darabszám ELÉRI a küszöböt. Ha az egész
    hisztogram kevesebb a küszöbnél, a ciklus a `break`-re fut: `lo = 255`,
    `hi = 0`. A pár tehát lehet fordított is (`hi <= lo`) — a hívó dolga
    eldönteni, mit kezd vele; itt nem szépítjük meg.
    """
    low = int(np.searchsorted(np.cumsum(histogram), threshold))
    high_from_top = int(np.searchsorted(np.cumsum(histogram[::-1]), threshold))
    return min(low, 255), 255 - min(high_from_top, 255)


def _native_levels_lut(low: int, high: int, max_out: int = 255) -> np.ndarray:
    """A natív szinthúzó átvitel 256 elemű LUT-ként — FIXPONTOSAN (#539).

    A `0x009db610` egész aritmetikával dolgozik, nem lebegőponttal:

    ```c
    gain = (max << 16) / (hi - lo);            // egész osztás, lefelé kerekít
    ki   = ((be - lo) * gain) >> 16;           // aritmetikai eltolás
    ki   = min(max, max(0, ki));
    ```

    Két következménye van, ami bájtra számít: a felezőpont lefelé kerekedik
    (a lebegőpontos `rint` fölfelé vinné), és `lo = 0`, `hi = 255` esetén a
    gain pontosan 65536, tehát a leképezés **bájtra azonosság**.

    Degenerált (`hi <= lo`) párnál azonosságot adunk vissza. A natív kód
    ilyenkor 0 gaint számol (fekete képet ad) — ez a szinthúzás értelmét
    vesztett határesete, amit szándékosan nem veszünk át.
    """
    if high <= low:
        return lut_ramp()
    gain = (max_out << 16) // (high - low)
    values = ((np.arange(256, dtype=np.int64) - low) * gain) >> 16
    return np.clip(values, 0, max_out).astype(np.float64)


def _union_black_white_point(image: np.ndarray) -> tuple[int, int]:
    """Az `autolight` GLOBÁLIS vágópontja: a csatornánkénti vágópontok
    UNIÓJA (#539, `FUN_00a4bfd0`).

    ```c
    lo = min(lo_R, lo_G, lo_B);   hi = max(hi_R, hi_G, hi_B);
    ```

    A hisztogram itt a TELJES képről készül (a hívott `FUN_00a4be40` a
    képméretet és a lépésközt kapja, elemzési peremet nem — szemben a
    csatornánként vágó `0x009db610`-zel). Ezt a 12 referencia-páron a mérés
    is megerősíti: teljes képpel 0,41, a középső 90%-kal 0,76 az átlagos
    eltérés.
    """
    height, width = image.shape[:2]
    threshold = _levels_clip_threshold(height * width)
    points = [
        _native_clip_points(_channel_histogram(image[..., channel]), threshold)
        for channel in range(3)
    ]
    return min(point[0] for point in points), max(point[1] for point in points)


def apply_autolight(image: np.ndarray) -> np.ndarray:
    """Auto Contrast — KÖZÖS (mindhárom csatornára azonos) lineáris
    szinthúzás (#540), a natív vágópontokkal (#539).

    A közös `lo`/`hi` a csatornánkénti, darabszám-küszöbös vágópontok
    UNIÓJA (`_union_black_white_point`), a leképezés pedig a natív
    fixpontos átvitel. Mivel egyetlen `lo`/`hi` fut mindhárom csatornán,
    a műveletnek nincs fehéregyensúly-hatása — ez különbözteti meg a
    csatornánként vágó Auto Colourtól.

    **Azonosság-eset:** ha a kép már kihasználja a teljes tartományt
    (`lo == 0` és `hi == 255`), a kimenet bájtra azonos a bemenettel.

    Mért átlagos eltérés a valódi Picasa-kimenettől a `referencia/
    autocontrast/` 12 képpárján: **0,41** (a korábbi, összeöntött
    hisztogramú közelítés 0,62; az érintetlen kép 7,49).
    """
    _validate_image(image)
    low, high = _union_black_white_point(image)
    if high <= low or (low == 0 and high == 255):
        return image.copy()
    # pontonkénti lineáris széthúzás → 256 elemű LUT (#140): képméret-független
    return apply_lut(image, _native_levels_lut(low, high))


#: A natív CSATORNÁNKÉNTI elemzés a kép SZÉLEIT kihagyja: a hisztogram csak
#: a középső 90% × 90%-ról készül (`0x009db610`, #576 dekompiláció, #539
#: méréssel igazolva). Keretes, vignettált vagy sötét szélű képnél ez
#: érdemben más fekete-/fehérpontot ad, mint a teljes képes elemzés.
_LEVELS_MARGIN_PERCENT = 5


def _analysis_region(image: np.ndarray) -> np.ndarray:
    """A hisztogram-elemzés területe: a kép középső 90% × 90%-a."""
    height, width = image.shape[:2]
    margin = _LEVELS_MARGIN_PERCENT
    top = height * margin // 100
    left = width * margin // 100
    return image[
        top : height * (100 - margin) // 100, left : width * (100 - margin) // 100
    ]


def _channel_black_white_points(
    image: np.ndarray,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Csatornánkénti fekete-/fehérpont a natív algoritmus szerint (#539).

    A `0x009db610` geometriája: a hisztogram a kép középső 90% × 90%-áról
    készül, a vágási küszöb viszont a TELJES kép képpontszámának 0,5%-a,
    mindkét végén azonosan (a natív kódban `(W·H)/200`).
    """
    height, width = image.shape[:2]
    threshold = _levels_clip_threshold(height * width)
    region = _analysis_region(image)
    points = tuple(
        _native_clip_points(_channel_histogram(region[..., channel]), threshold)
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
#: nem illesztési fogás, hanem a natív viselkedés (a `gain` felső korlátja)
#: — a natív kódban viszont MÉG NEM TALÁLTUK MEG, hol dől el (a `0x009db610`
#: dekompilátumából a Ghidra két float paramétert elveszít; ld. a #539
#: jegyet). Amíg ez nyitva van, a korlát MÉRT viselkedés, nem visszafejtett.
_MIN_STRETCH_SPAN = 58


def apply_channel_levels_stretch(image: np.ndarray) -> np.ndarray:
    """Csatornánként KÜLÖN lineáris szinthúzás: `ki = (be − lo)·255/(hi − lo)`.

    Ez a „Jó napom van" (I'm Feeling Lucky) és az `AutoFix` megfejtett
    modellje (#535, 12 referencia-képpáron R² = 0,9995–1,0000 illesztéssel
    igazolva). **Azonosság-eset:** ha egy csatorna `lo`/`hi`-je már `0`/`255`
    (a csatorna kihasználja a teljes tartományt), azt a csatornát a Picasa
    NEM módosítja — a natív fixpontos átvitel ilyenkor pontosan 65536-os
    gaint ad, tehát a kimenet magától bájtra azonos.

    #539: a vágópontok a natív geometriával és a natív keresőciklussal
    készülnek (`_channel_black_white_points`), a leképezés pedig a natív
    fixpontos átvitel (`_native_levels_lut`). A nagyon szűk hisztogramú
    csatornát a Picasa nem feszíti ki teljesen — a bemeneti tartomány alsó
    korlátja `_MIN_STRETCH_SPAN`, a feketeponthoz horgonyozva.
    """
    _validate_image(image)
    points = _channel_black_white_points(image)
    luts = []
    for low, high in points:
        if 0 < high - low < _MIN_STRETCH_SPAN:
            # a korlát a FEKETEPONTOT tartja, a fehérpontot tolja feljebb
            high = low + _MIN_STRETCH_SPAN
        luts.append(_native_levels_lut(low, high))
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


def apply_autocontrast(image: np.ndarray) -> np.ndarray:
    """`autocontrast` („Automatikus kontraszt") — csatornánkénti szinthúzás.

    A #612 3.1 pontja szerint ez a szűrő (`0x008f89d0`) UGYANAZT a natív
    hisztogram-elemzőt hívja, mint a „Jó napom van" (`0x009db610`), csak a
    felső határt vezérlő jelzőt FIXEN 0-nak adja — vagyis a kimenet mindig a
    teljes 0..255 tartományra nyúlik, míg az `enhance` ugyanezt a
    `CarefulEnhance` beállítástól függően 252-re is korlátozhatja. Mivel mi az
    `enhance`-t is a 255-ös ággal futtatjuk (a beállítás a felhasználó gépén
    él, nem az ini-ben), a két szűrő ma AZONOS kimenetet ad — a #685
    mérőszettjén maga a Picasa is bájtra ugyanazt adta a kettőre.
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
