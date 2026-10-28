"""A Glimmer fixpontos, szeparálható képméretező primitívjei."""

from __future__ import annotations

from picasapy.render.curves import validate_image
import numpy as np



#: A Mitchell–Netravali mag paraméterei: **B = C = 0,4** (#2227). Az eredeti
#: `ResizeImageOperation` alkalmazója (`0x00bc3650`) a `0x00bcb5e0`
#: segédfüggvényt hívja, az pedig a `ytResampler`-t explicit móddal: a
#: vízszintes cél/forrás lépték `≤ 1` → 0-s (doboz), egyébként 3-as
#: (Mitchell–Netravali). Spec: `filterdesc-registry.md`, 5/c (#3805).
_MITCHELL_B = 0.4

_MITCHELL_C = 0.4


#: A fixpontos súlyok egysége: a súlyok összege mindig ennyi, a kimenet
#: `(Σ w·p + 255) >> 14` (`0x00a4031f`: 1,0 × `[0x00cf3b70]` = 16383,0).
_RESIZE_EGYSEG = 16383

_RESIZE_ELTOLAS = 14

_RESIZE_KEREKITO = 255

#: Az alkalmazó a `0x3fffff` fölötti összeget vágja (`0x00a427b0`–`0x00a4283a`).
_RESIZE_FELSO = 0x3FFFFF



def mitchell_netravali(x: np.ndarray) -> np.ndarray:
    """A Mitchell–Netravali rekonstrukciós mag `B = C = 0,4`-gyel.

    A klasszikus alak (Mitchell & Netravali, 1988), `|x|` szerint:

        |x| < 1:  ((12−9B−6C)|x|³ + (−18+12B+6C)|x|² + (6−2B)) / 6
        1 ≤ |x| < 2:  ((−B−6C)|x|³ + (6B+30C)|x|² + (−12B−48C)|x| + (8B+24C)) / 6
        egyébként: 0

    `B = C = 0,4` mellett az **oldallebeny negatív** (1 és 2 között) — ez a
    mag azonosító jegye: éles élen enyhe alul-/túllövést ad, amit a doboz
    nem produkál. A határ kizáró: `|x| ≥ 2` → 0 (`0x00a3fcde`).
    """
    tav = np.abs(np.asarray(x, dtype=np.float64))
    b, c = _MITCHELL_B, _MITCHELL_C
    belso = (
        (12 - 9 * b - 6 * c) * tav**3
        + (-18 + 12 * b + 6 * c) * tav**2
        + (6 - 2 * b)
    ) / 6.0
    kulso = (
        (-b - 6 * c) * tav**3
        + (6 * b + 30 * c) * tav**2
        + (-12 * b - 48 * c) * tav
        + (8 * b + 24 * c)
    ) / 6.0
    return np.where(tav < 1, belso, np.where(tav < 2, kulso, 0.0))



def lanczos3(x: np.ndarray) -> np.ndarray:
    """A Lanczos-3 mag (`ytResampler` 5-ös mód, `0x00a3fdf5`, #3998):
    `|x| >= 3` → 0, egyébként `sinc(π|x|) · sinc(π|x|/3)`. Az oldallebenyek
    negatívak (1 és 2 között), a sugár 3."""
    tav = np.abs(np.asarray(x, dtype=np.float64))
    return np.where(tav < 3.0, np.sinc(tav) * np.sinc(tav / 3.0), 0.0)



def _tengely_sulyok(
    be_meret: int, ki_meret: int, doboz: bool, lanczos: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """Egy tengely csapindexei és EGÉSZ súlyai, a `ytResampler` szerint.

    Spec 5/b–5/c (`0x00a3f660`): a csap helye `j + 0,5`. A natív dobozág
    előbb float32-ben tárolja a cél/forrás arányt, majd ennek külön float32
    reciprokával számítja a középpontot (`0x00a3f711`–`0x00a3f717`,
    `0x00a3f8af`–`0x00a3f8bd`). A tapeltolást a cél/forrás aránnyal szorozza,
    és float32-ben veti össze a `0,5` határral (`0x00a3faf6`–`0x00a3fb20`).
    Ez a kétlépcsős kerekítés matematikailag határra eső alsó tapot is
    beengedhet, ezért a közvetlen forrás/cél osztás nem bitpontos.

    * **doboz** (0-s mód): súly 1, ha a tárolt `|x| < 0,5`;
    * **Mitchell** (3-as mód): `B = C = 0,4`, `|x| < 2`;
    * **Lanczos-3** (5-ös mód, `lanczos=True`, #3998): `|x| < 3`.

    Az egész súly `csonk(w · 16383 / Σw)` (`0x00a4035d`), a maradékot
    (`16383 − Σ`) a `csonk(c)` indexű csap kapja, a csaptartományba
    szorítva (`0x00a40462`–`0x00a4049f`). A képen kívüli csap nem kerül a
    listába. Visszaad: `(indexek, sulyok)`, mindkettő `(ki_meret, ablak)`
    alakú; a lista végét 0 súlyú, érvényes indexű csapok töltik ki.

    ⚠️ Ha a dobozban egyetlen csap sincs (nagyításnál `c` pontosan egy
    képponthatárra esik), a teljes súly a `csonk(c)` csapé. Ezt az esetet a
    bináris nem mérte ki; a maradék-szabály folytatása.
    """
    cel_forras = np.float32(ki_meret) / np.float32(be_meret)
    forras_cel = np.float32(be_meret) / np.float32(ki_meret)
    if doboz:
        # A natív előbb cél/forrás float32 arányt tárol, majd külön veszi a
        # reciprokát. Egyes méreteknél ez eltér a közvetlen forrás/cél
        # osztástól (például 7→4: 1,74999988, nem 1,75).
        skala = np.float32(np.float32(1.0) / cel_forras)
        nyujtas = max(1.0, float(skala))
        sugar = float(np.float32(np.float32(0.5) / cel_forras))
        kozep = (
            (np.arange(ki_meret, dtype=np.float32) + np.float32(0.5)) * skala
        ).astype(np.float32).astype(np.float64)
    else:
        skala = forras_cel
        nyujtas = max(1.0, float(skala))
        sugar = (3.0 if lanczos else 2.0) * nyujtas
        kozep = (
            (np.arange(ki_meret, dtype=np.float32) + np.float32(0.5)) * skala
        ).astype(np.float64)
    elso = np.floor(kozep - sugar - 0.5).astype(np.int64)
    ablak = int(np.ceil(2 * sugar)) + 2
    indexek = elso[:, None] + np.arange(ablak)[None, :]
    if doboz:
        tap_kozep = (indexek.astype(np.float32) + np.float32(0.5)).astype(np.float32)
        tav = (
            (tap_kozep - kozep.astype(np.float32)[:, None]).astype(np.float32)
            * cel_forras
        ).astype(np.float32)
        ervenyes = (
            (np.abs(tav) < np.float32(0.5))
            & (indexek >= 0)
            & (indexek < be_meret)
        )
        nyers = ervenyes.astype(np.float64)
    else:
        tav = indexek + 0.5 - kozep[:, None]
        ervenyes = (np.abs(tav) < sugar) & (indexek >= 0) & (indexek < be_meret)
        mag = lanczos3 if lanczos else mitchell_netravali
        nyers = np.where(ervenyes, mag(tav / nyujtas), 0.0)
    osszeg = nyers.sum(axis=1, keepdims=True)
    osztott = np.divide(
        nyers * _RESIZE_EGYSEG, osszeg, out=np.zeros_like(nyers), where=osszeg != 0
    )
    sulyok = np.trunc(osztott).astype(np.int32)
    # a maradék a `csonk(c)` csapé, az érvényes csaptartományba szorítva
    van = ervenyes.any(axis=1)
    also = np.where(van, np.argmax(ervenyes, axis=1), 0)
    felso = np.where(van, ablak - 1 - np.argmax(ervenyes[:, ::-1], axis=1), ablak - 1)
    cel = np.trunc(kozep).astype(np.int64)
    cel = np.where(van, cel, np.clip(cel, 0, be_meret - 1)) - elso
    cel = np.clip(np.where(van, np.clip(cel, also, felso), cel), 0, ablak - 1)
    sorok = np.arange(ki_meret)
    sulyok[sorok, cel] += _RESIZE_EGYSEG - sulyok.sum(axis=1)
    return np.clip(indexek, 0, be_meret - 1), sulyok



def _tengely_menten(
    kep: np.ndarray,
    ki_meret: int,
    tengely: int,
    doboz: bool,
    lanczos: bool = False,
    kerekito_oszlopok: np.ndarray | None = None,
    _sulyok_fuggveny=None,
) -> np.ndarray:
    """Fixpontos tengelymenet; a függőleges `W mod 4` farkat a #4004 szerint számolja."""
    be_meret = kep.shape[tengely]
    if (doboz or lanczos) and ki_meret == be_meret:
        # 1:1-es menet: a középső csap súlya 16383 (a Lanczos többi csapja az
        # egész távolságokon 0) — `(16383·p + 255) >> 14 = p`
        return kep
    sulyok_fuggveny = _tengely_sulyok if _sulyok_fuggveny is None else _sulyok_fuggveny
    indexek, sulyok = sulyok_fuggveny(be_meret, ki_meret, doboz, lanczos)
    alak = [1] * kep.ndim
    alak[tengely] = ki_meret
    gyujto = np.zeros(
        kep.shape[:tengely] + (ki_meret,) + kep.shape[tengely + 1:], dtype=np.int32
    )
    for k in range(sulyok.shape[1]):
        oszlop = sulyok[:, k]
        if not oszlop.any():
            continue
        gyujto += np.take(kep, indexek[:, k], axis=tengely).astype(np.int32) * oszlop.reshape(alak)
    if tengely == 0:
        # A ytResampler függőleges főciklusa négy oszloponként indul, és itt
        # kapja meg a +255-öt. A sor végén maradó W mod 4 oszlop skalár
        # farkában a Picasa nem ad hozzá kerekítőtagot.
        if kerekito_oszlopok is None:
            kerekito_oszlopok = np.arange(gyujto.shape[1]) < (gyujto.shape[1] & ~3)
        elif kerekito_oszlopok.shape != (gyujto.shape[1],):
            raise ValueError("A függőleges kerekítőmaszk szélessége eltér a bemenetétől")
        alak_kerekito = (1, gyujto.shape[1]) + (1,) * (gyujto.ndim - 2)
        kerekito = np.where(kerekito_oszlopok, _RESIZE_KEREKITO, 0).reshape(alak_kerekito)
        gyujto += kerekito
    else:
        gyujto += _RESIZE_KEREKITO
    np.clip(gyujto, 0, _RESIZE_FELSO, out=gyujto)
    return (gyujto >> _RESIZE_ELTOLAS).astype(np.uint8)



def resize_image(
    image: np.ndarray,
    width: int,
    height: int,
    smoothing: bool = True,
    lanczos3: bool = False,
) -> np.ndarray:
    """`Resize`: a kép átméretezése.

    `smoothing=True` (az alapérték, mérve: `0x00bc36ac`) a `ytResampler`-t
    futtatja (spec `filterdesc-registry.md`, 5/c, #3805):

    * **A mód a VÍZSZINTES cél/forrás léptékből** (`0x00bcb629`–`0x00bcb659`):
      `≤ 1` (kicsinyítés vagy 1:1) → **doboz**, egyébként
      **Mitchell–Netravali B = C = 0,4**. Ugyanaz a mód fut MINDKÉT
      tengelyen — a függőleges nagyítás kicsinyítő szélesség mellett is
      dobozzal, a függőleges kicsinyítés nagyító szélesség mellett is
      Mitchell-lel.
    * **Fixpontos súlyok**: `csonk(w · 16383 / Σw)`, a maradék a `csonk(c)`
      csapé (`_tengely_sulyok`).
    * **Kimenet**: a vízszintes menetben csatornánként `(Σ w·p + 255) >> 14`;
      a függőleges menet négyes főciklusa ugyanezt használja, a sor utolsó
      `W mod 4` oszlopa viszont `(Σ w·p) >> 14` szerint készül (#4004). Az
      értékek 0..255-re szorítódnak. Előbb a vízszintes menet fut, 8 bites köztes
      képpel, utána a függőleges.

    `lanczos3=True` a 5-ös mód (#3998, spec 16. H) 3.): mindkét tengelyen
    Lanczos-3 (`lanczos3`), a többi lépés ugyanaz. Az EXIF-bélyegkép használja.

    `smoothing=False` a 9-es, legközelebbi-szomszéd ág (spec 5/d): a célpixel
    középpontját float32 aránnyal vetíti vissza, majd 16.16 fixpontban
    csonkol. Vízszintesen a fixpontos lépés ismételt egész összeadással halad.
    """
    validate_image(image)
    width = max(1, int(round(width)))
    height = max(1, int(round(height)))
    if not smoothing:
        source_height, source_width = image.shape[:2]
        scale_x = np.float32(source_width / width)
        scale_y = np.float32(source_height / height)
        fixed_scale = np.float32(65536.0)

        # A natív ciklus kiszámítja a kezdő koordinátát és a lépést, majd a
        # vízszintes fixpontos koordinátát minden oszlopnál egészben lépteti.
        start_x = np.float32(np.float32(0.5) * scale_x)
        q0 = int(np.trunc(start_x * fixed_scale))
        dx = int(np.trunc(scale_x * fixed_scale))
        q_x = q0 + np.arange(width, dtype=np.int64) * dx
        source_x = q_x >> 16

        # A függőleges koordináta a célpixel középpontjából készül minden sorra.
        target_centers_y = np.arange(height, dtype=np.float32) + np.float32(0.5)
        source_centers_y = target_centers_y * scale_y
        q_y = np.trunc(source_centers_y * fixed_scale).astype(np.int64)
        source_y = q_y >> 16
        return image[source_y[:, None], source_x[None, :]]
    return _ytresampler(image, width, height, lanczos3)



def resize_plane(plane: np.ndarray, width: int, height: int) -> np.ndarray:
    """Egyetlen `HxW` uint8 sík átméretezése ugyanazzal a `ytResampler`-rel.

    A belső ragyogás a súlyát így nagyítja vissza (#3827): a natív kód a
    négy bájtot egymástól függetlenül, azonos súlyokkal méretezi, és a
    ragyogás színe állandó, tehát csak az alfa változik.
    """
    if plane.ndim != 2 or plane.dtype != np.uint8:
        raise ValueError("resize_plane: HxW uint8 tömb kell")
    return _ytresampler(plane, max(1, int(round(width))), max(1, int(round(height))))



def _csap_alairas(oszlop_index: np.ndarray, sulyok: np.ndarray) -> np.ndarray:
    """A kimeneti oszlopok `(oszlop, súly)` aláírása; az egyetlen oszlopra
    eső csapok kanonikus alakot kapnak (`[c, −1, …] + [16383, 0, …]`)."""
    van = sulyok != 0
    index = np.where(van, oszlop_index, -1)
    elso = index[np.arange(index.shape[0]), np.argmax(van, axis=1)]
    egyforma = np.all((index == elso[:, None]) | ~van, axis=1)
    kanon_index = np.full_like(index, -1)
    kanon_index[:, 0] = elso
    kanon_suly = np.zeros_like(sulyok)
    kanon_suly[:, 0] = _RESIZE_EGYSEG
    index = np.where(egyforma[:, None], kanon_index, index)
    suly = np.where(egyforma[:, None], kanon_suly, sulyok)
    return np.concatenate([index, suly], axis=1)



def resize_column_plane(
    oszlopok: np.ndarray, vissza: np.ndarray, width: int, height: int
) -> np.ndarray:
    """`resize_plane(oszlopok[:, vissza], width, height)` — bitre ugyanaz, gyorsabban.

    A sík kevés különböző oszlopból áll (`oszlopok`, `H×n`; `vissza` a `W`
    hosszú oszlopindex). Egy kimeneti oszlopot a vízszintes menet csapjainak
    `(oszlop, súly)` párjai határoznak meg; az azonos párú kimeneti oszlopok
    azonosak, ezért mindkét menet csak a különböző párokra fut, és a teljes
    méretű síkot egyetlen indexelés adja (#3827). Ha egy kimeneti oszlop
    minden nem nulla súlyú csapja ugyanarra az oszlopra esik, a kimenet maga
    az az oszlop (a súlyok összege 16383, `(16383·p + 255) >> 14 = p`), ezért
    ezek egy közös párt kapnak. A #4004 függőleges sorvégi maradékát a teljes
    kimeneti szélességhez igazítja, ezért két kerekítési változatot is tárol.
    """
    magas, be_szeles = oszlopok.shape[0], vissza.size
    width = max(1, int(round(width)))
    height = max(1, int(round(height)))
    doboz = width <= be_szeles
    if width == be_szeles:
        kulonbozo, kimeneti = oszlopok, vissza
    else:
        indexek, sulyok = _tengely_sulyok(be_szeles, width, doboz)
        alairas = _csap_alairas(vissza[indexek], sulyok)
        parok, kimeneti = np.unique(alairas, axis=0, return_inverse=True)
        csapok = indexek.shape[1]
        gyujto = np.full((magas, parok.shape[0]), _RESIZE_KEREKITO, dtype=np.int32)
        for k in range(csapok):
            sor_suly = parok[:, csapok + k].astype(np.int32)
            gyujto += oszlopok[:, parok[:, k]].astype(np.int32) * sor_suly
        np.clip(gyujto, 0, _RESIZE_FELSO, out=gyujto)
        kulonbozo = (gyujto >> _RESIZE_ELTOLAS).astype(np.uint8)
    kimeneti = np.asarray(kimeneti).reshape(-1)
    # A sorvégi szabály a teljes kimeneti W-hez igazodik, nem a tömör
    # oszloppárok darabszámához. Egy pár belső és maradék oszlopban is
    # megjelenhet, ezért a két kerekítési változatot külön tartjuk.
    teljes_kerekites = _tengely_menten(
        kulonbozo,
        height,
        0,
        doboz,
        kerekito_oszlopok=np.ones(kulonbozo.shape[1], dtype=bool),
    )
    kimenet = teljes_kerekites[:, kimeneti].copy()
    maradek = width % 4
    if maradek:
        maradek_kerekites = _tengely_menten(
            kulonbozo,
            height,
            0,
            doboz,
            kerekito_oszlopok=np.zeros(kulonbozo.shape[1], dtype=bool),
        )
        kimenet[:, -maradek:] = maradek_kerekites[:, kimeneti[-maradek:]]
    return kimenet



def _ytresampler(kep: np.ndarray, width: int, height: int, lanczos: bool = False) -> np.ndarray:
    """A mód a vízszintes léptékből (`lanczos`: az 5-ös mód, mindkét tengelyen);
    előbb vízszintes, aztán függőleges menet."""
    if width == kep.shape[1] and height == kep.shape[0]:
        return kep.copy()
    doboz = width <= kep.shape[1] and not lanczos
    vizszintes = _tengely_menten(kep, width, 1, doboz, lanczos)
    kimenet = _tengely_menten(vizszintes, height, 0, doboz, lanczos)
    return kimenet.copy() if kimenet is kep else kimenet
