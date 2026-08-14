# A Picasa 3.9 beépített nyílt forráskódú könyvtárai

**Miért fontos ez a lap:** minden olyan viselkedés, amit ezek a könyvtárak
adnak, **nem visszafejtési feladat**. A forrásuk nyilvános, tehát az
algoritmus szó szerint kiolvasható — és ami még fontosabb: a Picasa
kimenetének reprodukálása ezeken a területeken azt jelenti, hogy **ugyanazt a
könyvtárat (vagy annak pontos algoritmusát) kell használni**, nem tippelni.

A megállapítások a `Picasa3.exe` RTTI- és string-táblájából származnak
(`referencia/binary-index/picasa3-index.sqlite`).

| könyvtár | bizonyíték | mit fed le |
|---|---|---|
| **Skia** | 46 `Sk*` RTTI-osztály (`SkCanvas`, `SkBitmapProcShader`, `SkBlitter`, `SkProcCoeffXfermode`, `SkScalerContext_Windows`) | a teljes rajzoló réteg: **mintavételezés** (forgatás, átméretezés), blitterek, shaderek, gradiensek, **keverési módok**, vágás/régió, **szövegrajzolás** |
| **dcraw** | `dcraw`, `UFRaw`, `Bibble`, `Phase One`, `Sinar`, `Rollei`, `Imacon`, `Ixpress %d-Mp`, `Sarnoff`, `**Buffer**` egyetlen 9227 bájtos függvényben (`0x008c07e0`) | **RAW-dekódolás** (#528) |
| **libtiff** | `ThunderDecodeRow`, `Fax3DecodeRLE`, `JPEGDecodeRaw` | TIFF olvasás/írás |
| **libpng + zlib** | `Application was compiled with png.h from libpng-%.20s`, `zlib version error` | PNG |
| **libjpeg** | `Independent JPEG Group` | JPEG kódolás/dekódolás — a **minőségi szintek** és kvantálási táblák is |
| **Expat** | `Failure creating Expat parser`, `Unknown URI in Expat full name` | XML: `filterdesc.xml`, `.cxf`, a honosítási erőforrások |
| **ICU** | 10 találat | Unicode-kezelés, rendezés |

## Következmények a PicasaPy-ra

1. **Geometria** (#626): a forgatás/átméretezés mintavételezője a Skia
   `SkBitmapProcState`-je. Egyszer, **központilag** kell megfeleltetni —
   nem effektenként. A Skia bilineárisa 4 bites (16 lépcsős) részpixel-
   súlyokkal dolgozik, ami mérhetően eltér a naiv lebegőpontostól.
2. **Keverési módok**: a `SkProcCoeffXfermode` együtthatós módjai. A korábban
   kézzel megfejtett `Softlight`/`Hardlight` képleteket érdemes ehhez
   igazítani.
3. **RAW** (#528): a feladat nem dekóder-visszafejtés, hanem **dcraw/LibRaw
   bekötése**. A Picasa is ezt tette.
4. **JPEG-mentés**: ha a kimeneti fájlnak bájtra hasonlítania kell, a
   libjpeg kvantálási tábláit kell használni, nem tetszőleges kódolót.
5. **Szövegrajzolás** (#450): a Skia glyph-cache-e és a Windows scaler
   context — a betűrajzolás platformfüggő volt.

## Amit ez NEM old meg

A Picasa **saját** logikája — az effekt-csővezetékek, a `.picasa.ini`
életciklusa, a kollázs-elrendezések, az arcfelismerő — továbbra is csak
visszafejtéssel érhető el. A könyvtárak a *hogyan rajzol*, nem a *mit rajzol*
kérdésre válaszolnak.
