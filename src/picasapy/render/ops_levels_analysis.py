"""Hisztogram-elemzés és szinthúzási segédek a régi `ops` API mögött."""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import lut_ramp
from picasapy.render.ops import _channel_histograms

_CAREFUL_BLACK_SCALE = 0.5

#: A szinthúzás vágási ARÁNYA: a képpontszám fél százaléka, MINDKÉT végén
#: azonosan (#539). A natív kód két helyen mondja ki ugyanezt: a
#: `FUN_00a4be40` a hívási helyről kapott `0.005f` konstanssal
#: (`0x3ba3d70a`), a `0x009db610` pedig egész osztásként, `/200`-zal.
_LEVELS_CLIP_RATIO = 0.005

#: A natív CSATORNÁNKÉNTI elemzés nem a teljes képet nézi: az ablak
#: 90% × 90% méretű (`0x009db610`, #576 dekompiláció). Keretes, vignettált
#: vagy sötét szélű képnél ez érdemben más fekete-/fehérpontot ad, mint a
#: teljes képes elemzés.
_LEVELS_MARGIN_PERCENT = 5

#: Az Auto Colour „semleges pixel"-szűrője (#541): a telítettségi és
#: fényességi küszöbök mérésből származnak.

_AUTOCOLOR_MAX_SATURATION = 0.40

#: A túl sötét képpontok kizárása, a mérés alapján.

_AUTOCOLOR_MIN_LEVEL = 30.0

#: Ennyi semleges képpont alatt nincs mire alapozni a becslést.

_AUTOCOLOR_MIN_PIXELS = 1000

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
    histograms = _channel_histograms(image)
    points = [
        _native_clip_points(histograms[channel], threshold) for channel in range(3)
    ]
    return min(point[0] for point in points), max(point[1] for point in points)

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
    histograms = _channel_histograms(region)
    points = tuple(
        _native_clip_points(histograms[channel], threshold) for channel in range(3)
    )
    return points[0], points[1], points[2]

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
