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
- `enhance` ("Jó napom van") és `autocontrast`: csatornánkénti vágás a kép
  90% × 90%-os, vízszintesen BALRA IGAZÍTOTT ablakáról (#721,
  `_analysis_region`), majd a vágópontok KEVERÉSE a közös `[loMin, hiMax]`
  felé. A keverés arányát a hívó adja: az `enhance` 0,30-at
  (`0x008f8840`), az `autocontrast` 1,0-et (`0x008f89d0`) — a kettő tehát
  KÜLÖN szűrő, nem azonos (#721, `0x009db610` utasításszintű olvasata).

A vágópont-keresés és a leképezés mindkét úton a natív algoritmus szerint
történik: darabszám-küszöb (`_levels_clip_threshold`), a natív keresőciklus
(`_native_clip_points`) és a natív fixpontos átvitel (`_native_levels_lut`).
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.ini.rect64 import Rect64
from picasapy.render.autocolor_matrix import (
    apply_autocolor_matrix,
    autocolor_matrix_16_16,
    estimate_illuminant,
)
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


#: A natív CSATORNÁNKÉNTI elemzés nem a teljes képet nézi: az ablak
#: 90% × 90% méretű (`0x009db610`, #576 dekompiláció). Keretes, vignettált
#: vagy sötét szélű képnél ez érdemben más fekete-/fehérpontot ad, mint a
#: teljes képes elemzés.
_LEVELS_MARGIN_PERCENT = 5


def _analysis_region(image: np.ndarray) -> np.ndarray:
    """A hisztogram-elemzés ablaka: 90% magas, 90% széles — de BALRA IGAZÍTVA.

    A natív ciklus (`0x009db610`) függőlegesen tényleg beljebb kezd, a
    VÍZSZINTES eltolás viszont hiányzik belőle: a sor-mutatót a peremmel
    lépteti, a soron BELÜL viszont a 0. oszlopról indul, és a vízszintes
    peremet csak a képpontok DARABSZÁMÁHOZ használja:

    ```c
    uVar12 = (W * 5) / 100;   uVar10 = (W * 95) / 100;   // csak a darabhoz
    pbVar11 = base + stride * ((H * 5) / 100) * 4;       // sor-eltolás: megvan
    do {
      iVar8  = uVar10 - uVar12;   // 0,9·W képpont…
      pbVar2 = pbVar11;           // …de a sor ELEJÉRŐL, nem a peremtől
    ```

    Az ablak tehát `[0 .. 0,9·W)`: a bal perem BENNE van, a jobb 10% marad
    ki. Ez a Picasa saját, elejtett eltolása, nem a mi egyszerűsítésünk —
    a #721 két, egymástól független oldalról igazolja:

    1. **A #685 szürke rámpája.** A Picasa `enhance`-e ott 6,5-nél vág
       feketét, miközben a rámpa (az ugyanott mért `autolight` szerint)
       4,5-től indul — vagyis a rámpa hosszának ~1%-ánál. Egy KÖZÉPRE
       igazított 90%-os ablak az 5%-nál kezdődik, tehát ezt geometriailag
       nem tudja kiadni; a mi mérésünk pontosan ott, **18,4**-nél vágott.
       A fehér végén ugyanez fordítva: a Picasa 235,4-nél vág (az ablak a
       világos oldalon rövidebb), mi 240,4-nél.
    2. **A `referencia/imfeellucky/` 12 valódi Picasa-képpárja.** Négy
       ablak-változatot végigmérve a valódi kimenethez vett átlagos
       csatorna-eltérés: balra igazított **2,48**, középre igazított 2,61,
       teljes kép 2,68, bal felső sarok 2,74 (az érintetlen kép 10,35).
       A balra igazított a legjobb — és ez a dekompilátum betű szerinti
       olvasata is.
    """
    height, width = image.shape[:2]
    margin = _LEVELS_MARGIN_PERCENT
    top = height * margin // 100
    bottom = height * (100 - margin) // 100
    columns = width * (100 - margin) // 100 - width * margin // 100
    return image[top:bottom, 0:columns]


def _channel_black_white_points(
    image: np.ndarray,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Csatornánkénti fekete-/fehérpont a natív algoritmus szerint (#539).

    A `0x009db610` geometriája: a hisztogram a kép 90% × 90%-os,
    vízszintesen BALRA IGAZÍTOTT ablakáról készül (`_analysis_region`), a
    vágási küszöb viszont a TELJES kép képpontszámának 0,5%-a, mindkét
    végén azonosan (a natív kódban `(W·H)/200`).
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
    """Auto Colour — `M · diag(g) · M⁻¹` SZÍNMÁTRIX (#759).

    **A #541-es, csatornánkénti modell le lett váltva.** A natív alkalmazó
    (`0x0090eda0`) egy 3×3-as mátrixszal szoroz 16.16 fixpontban, amibe a
    becsült erősítések a mátrix TERÉBEN épülnek be — ezért nem ment 2,35
    alá semmilyen csatornánkénti közelítés: hiányoztak a kereszt-tagok.

    A részletek, a mérés és a két csapda (float32; a csonkoló egész-osztás)
    a `picasapy.render.autocolor_matrix` modul-docstringjében. Mért átlagos
    csatorna-eltérés a 12 golden páron:

        érintetlen kép ............................ 5,287
        a korábbi modellünk (#541) ................ 2,352
        EZ a modell ............................... 0,614

    A 0,614 a JPEG-újratömörítés zajszintje (~0,69) ALATT van.

    **Azonosság-eset:** semleges becslésnél (`kR = kB = 128`) a mátrix
    pontosan az egységmátrix, tehát a kimenet bájtra a bemenet. A korábbi
    modell ezt NEM tudta: egy semleges mérőképen 0,812-nyit elmozdított,
    pedig a Picasa hozzá sem nyúlt.
    """
    _validate_image(image)
    red_gain, blue_gain = estimate_illuminant(image)
    matrix = autocolor_matrix_16_16(red_gain, 128, blue_gain)
    if np.array_equal(matrix, np.diag([65536, 65536, 65536])):
        return image.copy()
    return apply_autocolor_matrix(image, matrix)

_ENHANCE_BLEND = 0.30
_AUTOCONTRAST_BLEND = 1.0
_CAREFUL_BLACK_SCALE = 0.5
_CAREFUL_MAX_OUT = 252

def _blend_clip_points(
    points: tuple[tuple[int, int], ...],
    blend: float,
    careful: bool,
) -> tuple[tuple[int, int], ...]:
    """A csatornánkénti vágópontokat a KÖZÖS érték felé keveri (#721).

    A natív `0x009db610` (`0x009db876`–`0x009db935`) betű szerint:

    ```c
    hiMax = max(hi_R, hi_G, hi_B);
    loMin = min(lo_R*skala, lo_G*skala, lo_B*skala);   // skala: 1,0 vagy 0,5
    hi_ch' = hi_ch + keveres * (hiMax - hi_ch);
    lo_ch' = lo_ch + keveres * (loMin - lo_ch);
    ```

    `keverés = 0` → tiszta csatornánkénti · `keverés = 1` → teljesen közös.

    A kevert pontok floatok, a rájuk épülő gain viszont fixpontos egész
    (`_native_levels_lut`), tehát valahol egész-konverzió történik. A C
    `float → int` cast CSONKOL, és a 12 referencia-páron ez mérhetően a
    legjobb is: csonkolással **0,572**, kerekítéssel 0,727 az átlagos
    csatorna-eltérés (float tartományból számolt gainnel 0,624).
    """
    scale = _CAREFUL_BLACK_SCALE if careful else 1.0
    high_max = max(high for _, high in points)
    low_min = min(low * scale for low, _ in points)
    return tuple(
        (
            int(low + blend * (low_min - low)),
            int(high + blend * (high_max - high)),
        )
        for low, high in points
    )


def apply_channel_levels_stretch(
    image: np.ndarray,
    blend: float = _ENHANCE_BLEND,
    careful: bool = False,
) -> np.ndarray:
    """Lineáris szinthúzás a natív `0x009db610` szerint — KEVERT vágóponttal.

    A vágópontok csatornánként készülnek (`_channel_black_white_points`), de
    a függvény nem itt áll meg: a `blend` arányban a KÖZÖS `[loMin, hiMax]`
    tartomány felé húzza őket (`_blend_clip_points`, #721). A hívó adja meg
    az arányt — az `enhance` 0,30-at, az `autocontrast` 1,0-et. A leképezés a
    natív fixpontos átvitel (`_native_levels_lut`).

    A `careful` a `CarefulEnhance` beállítás ága: felezett feketepontok a
    közös minimum képzése előtt, és 252-es kimeneti korlát. A valódi
    Picasa-exportunk NEM ezzel készült (a 12 páron 2,366 kontra 0,572),
    ezért az alapértelmezés `False` — a beállítás a felhasználó gépén él,
    nem az ini-ben.

    **Azonosság-eset:** ha egy csatorna kevert `lo`/`hi`-je `0`/`255`, a
    natív fixpontos átvitel pontosan 65536-os gaint ad, tehát a kimenet
    bájtra azonos a bemenettel.

    Mért átlagos csatorna-eltérés a `referencia/imfeellucky/` 12 valódi
    Picasa-képpárján: **0,572** — a #721 előtti kód (keverés nélkül, de a
    `_MIN_STRETCH_SPAN = 58` korláttal) 2,480, az érintetlen kép 10,346.
    A 0,30 MÉRT optimum is: 0,25-nél 0,795, 0,30-nál 0,572, 0,35-nél
    0,884 — vagyis a visszafejtett konstanst a mérés önállóan megerősíti.

    #721: a korábbi `_MIN_STRETCH_SPAN = 58` korlát ITT SZŰNT MEG. Az az
    58 nem a natív kód korlátja volt, hanem épp ennek a keverésnek a
    lenyomata: a „Utopic Unicorn" két szűk csatornáján a kevert tartomány
    **58,7** és **58,7** (a Picasából mért 58,1 és 59,2), a zöld kevert
    pontjai `18,0…76,7` (mérve `18,2…76,3`). A keveréssel a korlát a 12
    páron EGYETLEN csatornán sem lépne működésbe (visszatéve mind a 12 kép
    kimenete bájtra azonos), a kiugró képé pedig 13,035-ről 0,521-re esik.
    """
    _validate_image(image)
    points = _blend_clip_points(_channel_black_white_points(image), blend, careful)
    max_out = _CAREFUL_MAX_OUT if careful else 255
    luts = [_native_levels_lut(low, high, max_out) for low, high in points]
    return apply_channel_luts(image, (luts[0], luts[1], luts[2]))


def apply_enhance(image: np.ndarray) -> np.ndarray:
    """„Jó napom van" (I'm Feeling Lucky) — `0x008f8840` → `0x009db610`.

    Hisztogram-darabszám alapú lineáris szinthúzás, a vágópontokat **30%-ban
    a közös érték felé keverve** (#721): a hívó a `-1,0` jelzőt adja át,
    amire a natív függvény a `0,30`-as alapértéket használja. Nincs benne
    gamma, S-görbe, helyi kontraszt vagy külön árnyék-/csúcsfény-emelés
    (#535).

    A `CarefulEnhance` bool ágat itt nem kapcsoljuk be — a beállítás a
    felhasználó gépén él, nem az ini-ben, és a referencia-exportunk is a
    kikapcsolt ággal készült (ld. `apply_channel_levels_stretch`).
    """
    _validate_image(image)
    return apply_channel_levels_stretch(image, _ENHANCE_BLEND)


def apply_autocontrast(image: np.ndarray) -> np.ndarray:
    """`autocontrast` („Automatikus kontraszt") — `0x008f89d0` → `0x009db610`.

    Ugyanaz a natív szinthúzó, mint az `enhance`-é, de a hívó **`1,0`**
    keverést ad át (`fld1`, `0x008f89fd`) és fixen 0 boolt (`push 0`,
    `0x008f8a03`). A vágópont tehát TELJESEN közös (`[loMin, hiMax]`),
    vagyis — az `enhance`-szel ellentétben — a művelet **nem mozdítja el a
    fehéregyensúlyt**, csak a kontrasztot húzza szét (#721).

    A két szűrő a #685 szürke rámpáján azonos kimenetet adott — ott
    `lo_ch = loMin` és `hi_ch = hiMax`, tehát a keverés elvileg sem
    látszhat. Színes képen viszont eltérnek.
    """
    _validate_image(image)
    return apply_channel_levels_stretch(image, _AUTOCONTRAST_BLEND)


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
