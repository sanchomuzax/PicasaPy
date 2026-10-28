"""Színmátrix-, lokális kontraszt- és fekete-fehér műveletek."""

from __future__ import annotations

from picasapy.render.nativ_blur import blur_image_operation
import numpy as np

from picasapy.render.curves import validate_image

# A SimpleColorMatrix és a bw_tint Haeberli-súlyai.
_HAEBERLI_WEIGHTS = (0.3086, 0.6094, 0.0820)


#: A Glimmer `SimpleColorMatrix` (#904) kontraszt-görbéjének (`0x008f2990`)
#: pozitív ága ZÁRT KÉPLETTEL NEM közelíthető — a natív kód egy 101 elemű,
#: kézzel hangolt táblázatból interpolál. A tábla forrása:
#: `referencia/kontraszt-tabla.csv` (a `sanchomuzax/picasapy-agent` privát
#: repóban, 101 sor, a `0x00c7d688` címről kimentve — ld. a fenti spec
#: 4.9-es szakaszát). Index = a csúszka egész része (0..100), az érték a
#: `kontraszt_gorbe(c)` visszatérési értéke `c` egész pontjaiban.
_KONTRASZT_TABLA: tuple[float, ...] = (
    0.00, 0.01, 0.02, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10, 0.11,
    0.12, 0.14, 0.15, 0.16, 0.17, 0.18, 0.20, 0.21, 0.22, 0.24,
    0.25, 0.27, 0.28, 0.30, 0.32, 0.34, 0.36, 0.38, 0.40, 0.42,
    0.44, 0.46, 0.48, 0.50, 0.53, 0.56, 0.59, 0.62, 0.65, 0.68,
    0.71, 0.74, 0.77, 0.80, 0.83, 0.86, 0.89, 0.92, 0.95, 0.98,
    1.00, 1.06, 1.12, 1.18, 1.24, 1.30, 1.36, 1.42, 1.48, 1.54,
    1.60, 1.66, 1.72, 1.78, 1.84, 1.90, 1.96, 2.00, 2.12, 2.25,
    2.37, 2.50, 2.62, 2.75, 2.87, 3.00, 3.20, 3.40, 3.60, 3.80,
    4.00, 4.30, 4.70, 4.90, 5.00, 5.50, 6.00, 6.50, 6.80, 7.00,
    7.30, 7.50, 7.80, 8.00, 8.40, 8.70, 9.00, 9.40, 9.60, 9.80,
    10.00,
)


#: `|k − 1| < eps` esetén a kontraszt-lépés TÉTLEN (a natív `0x008f1bd0`
#: korai kilépése) — #904.
_CONTRAST_EPS = 1e-6



def _telitettseg_k(saturation: float) -> float:
    """A Haeberli-mátrix `k` erősítése (#903, `0x008f1d00`) — a csúszka
    ASZIMMETRIKUS: a pozitív oldal háromszoros skálázást kap, a negatív
    nem. `+100 → k=4,0`, `-100 → k=0,0` (teljes szürke)."""
    if saturation > 0:
        return 1.0 + (saturation * 3.0) / 100.0
    return 1.0 + saturation / 100.0



def _saturation_matrix(saturation: float) -> np.ndarray:
    """A `SimpleColorMatrix` telítettség-ágának teljes 3×3 Haeberli-
    színmátrixa (#903). A luminancia-súlyok 0,3086/0,6094/0,0820 —
    NEM Rec.601 (ld. `_HAEBERLI_WEIGHTS` docstringje)."""
    k = _telitettseg_k(saturation)
    w = 1.0 - k
    red_w, green_w, blue_w = _HAEBERLI_WEIGHTS
    rw, gw, bw = w * red_w, w * green_w, w * blue_w
    return np.array(
        [
            [k + rw, gw, bw],
            [rw, k + gw, bw],
            [rw, gw, k + bw],
        ],
        dtype=np.float32,
    )



def _kontraszt_gorbe(c: float) -> float:
    """`kontraszt_gorbe` (#904, `0x008f2990`): negatív oldalon zárt képlet
    (`c/100`), pozitív oldalon a 101 elemű `_KONTRASZT_TABLA`-ból lineáris
    interpolációval — SEMMILYEN zárt képlet nem illeszkedik rá (a legjobb
    exponenciális illesztés 0,64-gyel téved), ezért a táblát kell átvenni.
    """
    if c == 0.0:
        return 0.0
    if c < 0.0:
        return c / 100.0
    if c >= 100.0:
        return _KONTRASZT_TABLA[100]
    i = int(c)
    f = c - i
    if f < 1e-9:
        return _KONTRASZT_TABLA[i]
    return (1.0 - f) * _KONTRASZT_TABLA[i] + f * _KONTRASZT_TABLA[i + 1]



def _homogen(matrix: np.ndarray | None = None, offset: float = 0.0) -> np.ndarray:
    """4×4-es homogén float32 mátrix: bal felső 3×3 = `matrix` (alap:
    egység), a 4. oszlop első három eleme = `offset`."""
    result = np.eye(4, dtype=np.float32)
    if matrix is not None:
        result[:3, :3] = matrix
    result[:3, 3] = np.float32(offset)
    return result



def _szorzas_x87(gyujto: np.ndarray, uj: np.ndarray) -> np.ndarray:
    """`G ← G × Ú` a natív szorzó (`0x008f28d0`) módján: 4×4-es, float32-ként
    tárolt elemek, x87-FPU. Egy elem: `acc = 0,0` (`[0xcf3a60]`); `l = 0…3`:
    `acc = f32(f64(acc) + f64(G[i,l]) · f64(Ú[l,j]))` — minden részösszeg
    float32-be tárolódik (`fstp dword`), tehát a sorrend és a köztes
    kerekítés számít."""
    result = np.zeros((4, 4), dtype=np.float32)
    for i in range(4):
        for j in range(4):
            acc = np.float32(0.0)
            for n in range(4):
                acc = np.float32(float(acc) + float(gyujto[i, n]) * float(uj[n, j]))
            result[i, j] = acc
    return result



def _kontraszt_matrix(contrast: float) -> np.ndarray | None:
    """A KÜLÖN kontraszt-lépés (#904/#3735, `0x008f1bd0`) homogén mátrixa:
    skála `k`, eltolás `(1-k)·63,5` — a forgáspont **63,5**, nem 128.
    `|k-1| < eps` esetén a lépés tétlen (a natív korai kilépése): `None`."""
    c = float(np.clip(contrast, -100.0, 100.0))
    k = 1.0 + _kontraszt_gorbe(c)
    if abs(k - 1.0) < _CONTRAST_EPS:
        return None
    result = _homogen(np.eye(3, dtype=np.float32) * np.float32(k), (1.0 - k) * 127.0 * 0.5)
    return result



def _fenyero_matrix(brightness: float) -> np.ndarray:
    """A fényerő-lépés (`0x008f1af0`) homogén mátrixa: egység + a fényerő a
    4. oszlopban (KÖZVETLEN additív, nincs ×2,55 skálázás)."""
    return _homogen(None, float(np.clip(brightness, -100.0, 100.0)))



def _kontraszt_fenyero_egyuttes_matrix(contrast: float, brightness: float) -> np.ndarray:
    """A `ContrastAndBrightnessLinked` ág (#904, `0x008f2040`) homogén
    mátrixa — KÜLÖN kódút, nem a különálló kontraszt+fényerő egymás után:
    a forgáspont **127,5**, és a fényerő-tag súlya a kontraszttól függ
    (`(k+1)·127,5/100`)."""
    c = float(np.clip(contrast, -100.0, 100.0))
    b = float(np.clip(brightness, -100.0, 100.0))
    k = 1.0 + _kontraszt_gorbe(c)
    t = ((k + 1.0) * 127.5 * b) / 100.0 + (127.5 - k * 127.5)
    return _homogen(np.eye(3, dtype=np.float32) * np.float32(k), t)



def _szinmatrix_osszefuzve(
    saturation: float | None, contrast: float, brightness: float, linked: bool
) -> tuple[np.ndarray, np.ndarray]:
    """A `SimpleColorMatrix` kész `(3×3 mátrix, 3 eltolás)` párja, a natív
    összefűzés módján (#3951, `docs/specs/filterdesc-registry.md`, #3950):
    `M = S · C · B` (linked: `M = S · L`), a gyűjtő `G ← G × Ú`
    (`_szorzas_x87`: `l = 0…3`, float32 részösszegek). A `S` telítettség
    nélkül egység. A képpontra a fényerő hat előbb, a kontraszt utána, majd a
    telítettség (#3735)."""
    gyujto = _homogen(_saturation_matrix(float(saturation)) if saturation is not None else None)
    if linked:
        if contrast or brightness:
            gyujto = _szorzas_x87(gyujto, _kontraszt_fenyero_egyuttes_matrix(contrast, brightness))
    elif contrast or brightness:
        kontraszt = _kontraszt_matrix(contrast)
        if kontraszt is not None:
            gyujto = _szorzas_x87(gyujto, kontraszt)
        gyujto = _szorzas_x87(gyujto, _fenyero_matrix(brightness))
    return gyujto[:3, :3].copy(), gyujto[:3, 3].copy()



def _fixpont_egyutthato(matrix: np.ndarray) -> np.ndarray:
    """A közös színmátrix-alkalmazó (`0x008f21a0`) együtthatói:
    `c = trunc(m·2048 ± 0,5)` — a `±` az `m` előjele (nullától elfelé
    kerekítés; NEM `rint`, az a felezőpontot páros felé viszi). A szorzás
    float64-ben megy (a natív a `double` konstansokkal, `[0xcf3ba0]` =
    2048,0, `[0xc72150]` = 0,5).

    ⚠️ A natív a `c`-t int16-ként tárolja (`0x008f240f`), tehát `|c| < 32768`,
    azaz `|m| < 16`. A mai presetekben `|m| ≤ ~10,5` (a telítettség- és a
    kontraszt-csúszka szélső, egyidejű állásában — pl. `s = c = 100` — a
    mátrix ezt meghaladná; ott a natív is csonkolna, ezt NEM utánozzuk,
    és nem is `assert`-eljük, hogy egy szélső csúszkaállás ne dobjon
    kivételt)."""
    scaled = np.asarray(matrix, dtype=np.float64) * 2048.0
    return np.trunc(scaled + np.where(scaled < 0.0, -0.5, 0.5)).astype(np.int64)



def _fixpont_bias(offset: np.ndarray) -> np.ndarray:
    """A közös alkalmazó eltolása (`0x008f2448`): `b = trunc(eltolás·4 ± 0,5)
    + 2` — a `+2` a végső `>> 2` kerekítése (`add eax, 2` @ `0x008f2469`)."""
    scaled = np.asarray(offset, dtype=np.float64) * 4.0
    return np.trunc(scaled + np.where(scaled < 0.0, -0.5, 0.5)).astype(np.int64) + 2



def _fixpontos_szinmatrix(image: np.ndarray, matrix: np.ndarray, offset: np.ndarray) -> np.ndarray:
    """A közös FIXPONTOS színmátrix-alkalmazó (#3930/#3950/#3951,
    `0x008f2500` → `0x008f2640`), a `SimpleColorMatrix`, a `Tint` szürkítése
    és a `BW` közös útja. A lebegőpontos `matrix` (`n × 3`) és `offset`
    (`n`) egész együtthatókra váltva (`_fixpont_egyutthato`, `_fixpont_bias`),
    képpontonként:

        ki_i = clamp((Σ_j ((c_ij · x_j) >> 9) + b_i) >> 2, 0, 255)

    A `>> 9` MINDEN taggal külön fut (előjeles, lefelé), az összeg a
    biasszal indul. Bemenet `uint8` RGB, kimenet `uint8` `(H, W, n)`."""
    coeffs = _fixpont_egyutthato(matrix)
    bias = _fixpont_bias(offset)
    pixels = image.astype(np.int64)
    out = np.empty(image.shape[:2] + (coeffs.shape[0],), dtype=np.uint8)
    for row in range(coeffs.shape[0]):
        acc = ((pixels * coeffs[row]) >> 9).sum(axis=-1) + bias[row]
        out[..., row] = np.clip(acc >> 2, 0, 255)
    return out



def simple_color_matrix(
    image: np.ndarray,
    brightness: float = 0.0,
    contrast: float = 0.0,
    saturation: float | None = None,
    linked: bool = False,
) -> np.ndarray:
    """`SimpleColorMatrix`: telítettség (Haeberli-színmátrix, #903 —
    `saturation=None` → nem érinti), majd — `linked` szerint — VAGY egy
    közös `ContrastAndBrightnessLinked` lépés (127,5-ös forgáspont), VAGY
    a fényerő (KÖZVETLEN additív, nincs ×2,55 skálázás) és a kontraszt
    (101 elemű táblázatos görbe, 63,5-ös forgáspont, korai kilépés kis
    `k`-nál) EGYÜTT, `out = k·(x+b) + (1-k)·63,5` alakban — a képpontra a
    fényerő hat ELŐBB, a kontraszt UTÁNA (#3735, ld. `_kontraszt_matrix`
    és `_szinmatrix_osszefuzve` docstringje). A `brightness` és a `contrast` is `[-100..100]`-ra vágva,
    a natív mintájára.
    """
    validate_image(image)
    matrix, offset = _szinmatrix_osszefuzve(saturation, contrast, brightness, linked)
    return _fixpontos_szinmatrix(image, matrix, offset)



#: A `LocalContrast` Gauss-szigmája a `Radius` csúszka FELE (#545). A
#: `referencia/hdrish/` négy Radius-állása egymástól függetlenül ezt adta
#: (a 2560 széles képen mérve, a legkisebb vödrön-belüli szórásra
#: illesztve):
#:
#:     Radius =  1,3 (min)  ->  szigma  1,6
#:     Radius = 20   (alap) ->  szigma  9,6
#:     Radius = 40   (mid)  ->  szigma 19,2
#:     Radius = 80   (max)  ->  szigma 38,4
#:
#: Ugyanaz a 2-es szorzó, mint a Vignette/MuseumMatte/Orton elmosásainál
#: (#317) — a Flash-örökségű sugár-paraméter és a Gauss-szigma között.
#:
#: ⚠️ #3520: a `HDR` és a `LocalContrast` MÁR NEM Gauss-szal mos, hanem a
#: natív `BlurImageOperation`-nel (`quality = 3`,
#: `render/nativ_blur.blur_image_operation`). A felezés
#: (`σ² = 3(w²−1)/12`, nagy `w`-re `σ ≈ w/2`) abból magától adódik; ez a
#: megjegyzés a #545 mérésének dokumentuma.


def _szorzott_resz(kulonbseg: np.ndarray, strength: float) -> np.ndarray:
    """A telítő `Blend … Subtract` 8 bites kimenetének natív Q11-szorzója.

    A MultiplyColorMatrix az aktuális 8 bites pixelt kapja; a LocalContrast
    láncában ez már a 0…255-re vágott különbségkép. A natív út a float32
    szorzót Q11-re kerekíti, majd előjeles egész eltolásokkal számol
    (`filterdesc-registry.md`, 4.10)."""
    m32 = np.float32(strength)
    q_float = np.float32(m32 * np.float32(2048.0))
    q = int(np.trunc(q_float + np.float32(0.5 if q_float >= 0 else -0.5)))

    pixel = np.clip(kulonbseg, 0.0, 255.0).astype(np.int32)
    szorzat = pixel * np.int32(q)
    sar9 = np.right_shift(szorzat, 9)
    return np.clip(np.right_shift(sar9 + 2, 2), 0, 255)



def _elmosott(image: np.ndarray, radius: float) -> np.ndarray:
    return blur_image_operation(image, radius, radius, quality=3).astype(np.float32)



def hdr_local_contrast(image: np.ndarray, radius: float, strength: float) -> np.ndarray:
    """A natív `glimmer::LocalContrastImageOperation` (lánc-építő
    `0x00bc41e0`, #3520) — a `HDR` motorja. A lánc az EREDETIBŐL indul::

        a  = sat(be + sat(C · sat(be − elm)))
        ki = sat(a  − sat(C · sat(elm − be)))

    azaz `ki = be + C·(be − elm)`, 8 biten lépésenként vágva. `C = 1`-nél
    sem azonosság. Az elmosás a natív `BlurImageOperation(R, R, 3)`, ami az
    1,3-as sugárral is mos. Bemenet és kimenet `uint8` RGB.
    """
    be = image.astype(np.float32)
    elm = _elmosott(image, radius)
    a = np.clip(be + _szorzott_resz(be - elm, strength), 0.0, 255.0)
    ki = np.clip(a - _szorzott_resz(elm - be, strength), 0.0, 255.0)
    return ki.astype(np.uint8)



def xml_local_contrast(image: np.ndarray, radius: float, strength: float) -> np.ndarray:
    """A `filterdesc.xml` `LocalContrast` lánca (#3520) — az ELMOSOTTBÓL
    indul::

        a  = sat(elm − sat(C · sat(elm − be)))
        ki = sat(a   + sat(C · sat(be − elm)))

    azaz `ki = elm + C·(be − elm)`; `C = 1`-nél bitre azonosság (#688).
    Az elmosás a natív `BlurImageOperation(R, R, 3)`. `uint8` RGB be és ki.
    """
    be = image.astype(np.float32)
    elm = _elmosott(image, radius)
    a = np.clip(elm - _szorzott_resz(elm - be, strength), 0.0, 255.0)
    ki = np.clip(a + _szorzott_resz(be - elm, strength), 0.0, 255.0)
    return ki.astype(np.uint8)



def _bw_coefficients(color: tuple[int, int, int]) -> tuple[int, int, int]:
    """A `bw_tint` fixpontos csatornaegyütthatói (`c = trunc(w·2048 + 0,5)`,
    int16) a `color` szűrőszínre. `0xff6666`-tal `c = 1080 / 853 / 115`
    (#3930, #3931 „Kész, ha")."""
    red_w, green_w, blue_w = _HAEBERLI_WEIGHTS
    raw_weights = np.array(
        [red_w * color[0], green_w * color[1], blue_w * color[2]], dtype=np.float64
    )
    total = float(raw_weights.sum())
    if total > 0:
        weights = raw_weights / total
    else:
        weights = np.array([red_w, green_w, blue_w], dtype=np.float64)
    coeffs = _fixpont_egyutthato(weights)
    return int(coeffs[0]), int(coeffs[1]), int(coeffs[2])



def bw_tint(image: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    """`BW(filtercolor=...)`: **valódi szürkeárnyalat** (R=G=B minden
    képponton) — a `filtercolor` NEM színezi be a kimenetet, hanem a
    szürkítéshez használt HAEBERLI csatornasúlyokat modulálja, mint egy
    színszűrő a fekete-fehér film előtt, majd a natív FIXPONTOS
    színmátrix-alkalmazóval számol.

    **Bizonyíték (#504), mérve az eredeti windowsos Picasa Holga-kimenetéhez
    (a privát `picasapy-agent` repó `referencia/holga/` hét mappás
    készlete):** mind a hat effektes exportban `R = G = B` **minden
    képponton**. A korábbi implementáció (`ki = luma/255 · color`) ezzel
    szemben SZÍNES kimenetet adott (`0xff6666`-tal R/G/B = 70/17/17) — ez
    volt a hiba, nem a csatornák sorrendje (#510 tévedett) és nem is
    „minden rendben" (#515 is tévedett).

    **A pontos képlet (#3930, utasításszintű bináris-kutatás, a `BW`
    közös színmátrix-alkalmazójára — `0x00bc16b0`/`0x00bbdd80`/`0x008f2500`):**

        w_c = haeberli_c · szín_c / Σ_k(haeberli_k · szín_k)
        c_c = trunc(w_c · 2048 + 0,5)                         (int16)
        Y   = clamp(((Σ_c (c_c · pixel_c) >> 9) + 2) >> 2, 0, 255)

    ahol `haeberli_c` a Haeberli-súly (`_HAEBERLI_WEIGHTS`, NEM Rec.601 —
    a #504 mérésből illesztett lebegőpontos modell ezt tévesen feltételezte,
    #3931). `0xff6666`-tal `c = 1080 / 853 / 115` (`_bw_coefficients`). A
    kettő a hetedes fixpontos kvantálás miatt NEM ugyanaz, mint a
    lebegőpontos `rint(Σ w·x)`: a teljes RGB-kockán 27%-ban eltérnek (pl.
    `(0,0,98)` fixpontosan 6, lebegőpontosan 5).

    Nulla összegnél (fekete szűrőszín) a natív kód a Haeberli-súlyokat
    használja módosítatlanul — ez az ág egyetlen hívónál sem fordul elő
    (a `color` mindig `0xff6666`), és a natív viselkedést erre az esetre
    **nem olvastuk ki** a bináris-kutatás során; a `0x00cf3a00` fallback
    egyenértékűsége a Haeberli-súlyokkal feltételezés, nem igazolt tény.
    `R = G = B = Y` — NEM a képen belüli (a `color`-tól független) lumát
    színezzük, hanem a `color`-ral modulált, fixpontosított súlyokkal
    újraszámoljuk a szürkét.

    `color` csatornasorrendje **RGB** (megegyezik a `image` tömb saját
    sorrendjével) — ld. `tint_multiply` docstringjét a #510-es tanulságról.
    """
    validate_image(image)
    coeffs = np.array([_bw_coefficients(color)], dtype=np.float64)
    # A `_bw_coefficients` már egész `c`; a közös alkalmazó a `c / 2048`
    # mátrixot pontosan ugyanerre az egészre váltja vissza.
    gray = _fixpontos_szinmatrix(image, coeffs / 2048.0, np.zeros(1))[..., 0]
    return np.repeat(gray[..., np.newaxis], 3, axis=-1)
