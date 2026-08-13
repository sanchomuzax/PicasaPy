# Az effekt-vezérlők feliratai — a Picasa saját szótára

Az eredeti Picasa `Picasa3i18n.dll`-jének `ImageFilters` osztálya. **69 felirat**,
41 nyelven; itt az angol kulcsszöveg és az eredeti magyar fordítás.

## Hogyan kapcsolódik a `filterdesc.xml`-hez

A `filterdesc.xml`-ben minden vezérlő azonosítója `_sldrXxx` (csúszka),
`_cpkrXxx` (színválasztó), `_clrsw` (színminta), `_chkXxx` (jelölő) alakú.
Az `Xxx` **közvetlenül** az alábbi táblázat kulcsa:

| azonosító-előtag | mire | példa |
|---|---|---|
| `_sldr` | csúszka | `_sldrImpact` → `Impact` → **Hatás** |
| `_cpkr` | színválasztó | `_cpkrOuter` → `OuterColor` → **Külső szín** |
| `_clrsw` | színminta | effektfüggő (`Vignette` → `VignetteColor`) |
| `_chk` | jelölő | `_chkReverse` → `Reverse` → **Megfordítás** |
| `_msk` | festhető maszk | nincs saját felirat |

Két eltérés a szabálytól: `_sldrStr` → `Strength`, `_sldrHardness` → `EdgeHardness`.

## A teljes szótár

| kulcs | angol | magyar |
|---|---|---|
| `Amount` | Amount | **Mennyiség** |
| `Angle` | Angle | **Szög** |
| `BackgroundColor` | Background Color | **Háttérszín** |
| `BlackColor` | First Color | **Első szín** |
| `Blacks` | Darkness | **Sötétség** |
| `BlendMode` | Blend Mode | **Keverési mód** |
| `Bloom` | Bloom | **Hamvasság** |
| `Blur` | Size | **Méret** |
| `Blur1` | Glow | **Ragyogás** |
| `BlurEdges` | Blur Edges | **Élhomályosítás** |
| `BlurX` | Horizontal Blur | **Vízszintes homályosítás** |
| `BlurXY` | Color Brush | **Színes ecset** |
| `BlurY` | Vertical Blur | **Függőleges homályosítás** |
| `BorderAmount` | Border Amount | **Szegély mennyisége** |
| `Brightness` | Brightness | **Fényerő** |
| `BrushSize` | Brush Size | **Ecsetméret** |
| `CaptionHeight` | Caption Height | **Képfelirat magassága** |
| `ColorOverride` | Color Override | **Színfelülírás** |
| `ColorStrength` | Color Strength | **Színerő** |
| `Contrast` | Contrast | **Kontraszt** |
| `CornerRadius` | Corner Radius | **Sarok sugara** |
| `Darken` | Darken | **Sötétítés** |
| `Definition` | Definition | **Maszatolás** |
| `Distance` | Distance | **Távolság** |
| `DotContrast` | Dot Density | **Pontsűrűség** |
| `DotFade` | Dot Fade | **Ponthalványítás** |
| `EdgeHardness` | Edge Hardness | **Élkeménység** |
| `Eraser` | Eraser | **Radír** |
| `Exposure` | Exposure | **Exponálás** |
| `Fade` | Fade | **Fokozat** |
| `Filter` | Number of Stars | **Csillagok száma** |
| `FocalSize` | Focal Size | **Fókuszméret** |
| `Grain` | Grain | **Szemcsésség** |
| `Hue` | Hue | **Színezet** |
| `Impact` | Impact | **Hatás** |
| `InnerColor` | Inner Color | **Belső szín** |
| `InnerThickness` | Inner Thickness | **Belső keret** |
| `Intensity` | Intensity | **Intenzitás** |
| `Letterbox` | Letterbox | **Postaláda** |
| `Lighten` | Lighten | **Világosítás** |
| `MatteColor` | Matte Color | **Matt szín** |
| `NeonColor` | Neon Color | **Neonszín** |
| `OuterColor` | Outer Color | **Külső szín** |
| `OuterThickness` | Outer Thickness | **Külső keret** |
| `PickColor` | Pick Color | **Színválasztás** |
| `Pinkness` | Pink-ness | **Rózsaszín hatás** |
| `PixelSize` | Pixel Size | **Képpontméret** |
| `Radius` | Radius | **Sugár** |
| `Reverse` | Reverse | **Megfordítás** |
| `Rotate` | Rotate | **Forgatás** |
| `Rotation` | Rotation | **Forgatás** |
| `RoundedCorners` | Rounded Corners | **Sarkok lekerekítése** |
| `Screen` | Lighten | **Világosítás** |
| `Selected` | Selected | **Kijelölve** |
| `ShadowColor` | Shadow Color | **Árnyékszín** |
| `Smoothing` | Detail | **Részletek** |
| `Softness` | Softness | **Lágyítás** |
| `Steps` | Number of Colors | **Színek száma** |
| `Strength` | Strength | **Erősség** |
| `Thin` | Thin | **Vékony** |
| `Threshold` | Threshold | **Küszöbérték** |
| `TintColor` | Tint Color | **Tinta színe** |
| `Tone` | Tone | **Tónus** |
| `TransparentBackground` | Transparent Background | **Átlátszó háttér** |
| `TransparentCorners` | Transparent Corners | **Átlátszó sarkok** |
| `Vibrance` | Vibrance | **Vibrálás** |
| `VignetteColor` | Vignette Color | **Vignetta színe** |
| `WhiteColor` | Second Color | **Második szín** |
| `Zoominess` | Zoominess | **Suhanás** |

## Miért ez az igazságforrás

A vezérlő-feliratokat **nem szabad kitalálni**: több eredeti elnevezés nem
magától értetődő, és a felhasználó a régi programból ezeket ismeri. Néhány
jellegzetes eset:

- `Blur` felirata **Méret**, nem „homályosítás" — a méretet állítja.
- `Smoothing` felirata **Részletek** — a nagyobb érték több részletet jelent.
- `Steps` felirata **Színek száma**, `Filter`-é **Csillagok száma**.
- `Fade` felirata **Fokozat** — ez a legtöbb Glimmer-effekt erősség-csúszkája.
- `Bloom` → **Hamvasság**, `Definition` → **Maszatolás**,
  `Zoominess` → **Suhanás**, `Letterbox` → **Postaláda**.

Forrás: a Picasa 3.9 `Picasa3i18n.dll` `stringres` szekciója.
