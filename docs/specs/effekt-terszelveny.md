# Effekt-térszelvény

**SAJÁT FUNKCIÓ (#6522):** Az Effekt-térszelvény a PicasaPy saját vizualizációja; az eredeti Picasa 3.9-ben nincs ilyen nézet, ezért a bináris-egyezés vizsgálata nem vonatkozik rá.

## Megjelenítés

A néző bal fiókjában, a hisztogram fölött jelenik meg egy 238 × 144 képpontos doboz 4 képpont réssel. A Nézet ▸ Effekt-térszelvény almenü kizáró módjai: Mindig, Szerkesztés közben (alapérték) és Soha. A módot a `view/effectSlice` QSettings-kulcs őrzi. A doboz forgása a `view/effectSliceSpin` kulccsal marad meg.

Mindig módban a teljes `filters=` láncot mutatja; üres láncnál az azonossági átlót és a „Nincs alkalmazott effekt” feliratot. Szerkesztés közben módban csak akkor látszik, amikor egy effektparaméter-panel vagy a Finomhangolás fül nyitva van; a Finomhangolás fül a finetune2 effekt négy csúszkája (Derítőfény, Csúcsfények, Árnyékok, Színhőmérséklet). Soha módban a doboz rejtett, a hisztogram elrendezése változatlan.

## Mérés és nézettípusok

A megjelenített felületet a tényleges renderlánc méri memóriabeli próbaképeken. A tónusnézet szürke rámpa kimenetét mutatja; a mélységtengelyen az utoljára mozgatott effektcsúszka teljes tartománya fut végig, a többi érték és lánctag változatlan. A narancs jelölő az aktuális csúszkaállás (a 12 mért sor között lineárisan interpolálva, ezért a mélységtengely csúszkájának húzása nem mér újra); ha a lánc kimenetében a csatornák legalább 1%-kal szétválnak, külön piros, zöld és kék vonal jelzi. A lánc többi nézettípusa:

- **Színkocka:** az 5³ pontos RGB-rács minden pontja oda kerül és olyan színű lesz, ahová és amilyenre az effekt viszi; a szaggatott kocka és a szürke átló az eredeti színtér.
- **Képsík-térkép:** az effekt által megváltoztatott képpontok helye és mértéke. A próba a hatás fajtája szerint egyenletes szürke (fokozatos fényerő), telített mező (telítettség-jellegű effektek) vagy sakktábla (szerkezetet módosító effektek, köztük a Picasa „Vignette” lágyító effektje, amely egyenletes mezőn nem változtat).
- **Pontválasz:** egyetlen világos pont hatása a szomszédos pixelekre.
- **Szemcse-domborzat:** rögzített véletlenmagú szürke próbakép eltérése.
- **Nincs térszelvény:** az adott effekt nem tartozik a fenti vizuális típusok egyikébe.

Vegyes láncnál a fejléc gombjával a láncban előforduló nézettípusok között lehet váltani. A helyi tónusleképezések és automatikus effektek kicsinyített fotón alapulnak; a nézet ezeknél közelítés.

## Forgatás és teljesítmény

A felület lassan, körülbelül 12 fok/másodperc sebességgel forog. Kattintással megállítható vagy újraindítható, vízszintes húzással kézzel forgatható. A 3D gomb kizárólag a forgást állítja. Rejtett ablaknál vagy doboznál az animáció szünetel. A csúszka teljes tartományának mérése háttérszálon történik és a mélységtengelyen kívüli paraméterek szerint gyorsítótárazódik.

## Rajz

A rajz a tulajdonossal végigiterált minta szerint készül: 28°-os rálátás, a keret 8 sarka minden forgási szögben kitölti a 212 × 105-ös rajzterületet; a hátsó falak folytonosak és szintvonalasak, az elülső alapél szaggatott. A felület világostól sötétkékig színezett, fénnyel árnyalt négyszögekből áll, hátulról előre rajzolva. Nézettípusonkénti doboz-arány (szélesség, mélység, magasság): tónus 1 × 0,7 × 0,5, képsík 1 × 0,7 × 0,4, pontválasz 1 × 1 × 0,5, szemcse 1 × 0,7 × 0,35, színkocka 1 × 1 × 0,85. A pontválasz narancs vonala a középen átmenő metszet.
