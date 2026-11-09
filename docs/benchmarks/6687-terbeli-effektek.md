# A térbeli effektek zárómérése (#6687)

Mérés: 2026-11-09, RPi5 / aarch64, 2560×1707 RGB. A forrás mindkét kódfánál ugyanaz a repóbeli golden-kit fotó volt. A főág a `origin/main` `90feecebbcaaa3cc6b7b2d853af2413bfbab557d` commitja, az ág a zárókör munkafája. A mérő egy bemelegítés után három mintát vett, mintánként váltott sorrendben futtatva a főágat és az ágat; az érték a három futás mediánja. A mérés induló `uptime` terhelése 5,09 / 7,06 / 6,82 (1/5/15 perc), a teljes mérés alatt az 1 perces load 4,57 és 11,92 között változott. Az értékelés a páros arányokra támaszkodik, nem az abszolút időkre.

| Szűrő | Főág (ms) | Ág (ms) | Gyorsulás |
|---|---:|---:|---:|
| Holga | 5176,4 | 2998,2 | 1,73× |
| radblur | 4162,4 | 2728,1 | 1,53× |
| LocalContrast | 2803,8 | 2940,7 | 0,95× |
| PencilSketch | 3892,7 | 1897,0 | 2,05× |
| glow2 | 2642,9 | 1088,1 | 2,43× |
| Pixelate | 337,7 | 237,0 | 1,43× |
| grain2 | 1618,0 | 324,3 | 4,99× |
| DropShadow | 669,1 | 351,9 | 1,90× |

## A kétszeres gyorsulást el nem érő szűrők

- **Holga:** A kontrasztlépés eredeti fixpontos színmátrixa 256 szürkeértékre előállított LUT-tal fut; a lebegőpontos `cv2.transform` próba ebből 36 bájtot eltérően számolt. A zajkeverésnél a `base * noise // 255`, majd a súlyozás `>> 8` és az utolsó páratlan oszlop külön képlete is egész kerekítést tartalmaz, ezért lebegőpontos OpenCV-keverés nem bájtazonos.
- **radblur:** A forró rész a Picasa IIR-elmosás: minden rekurzív lépés a `((pixel << 7) - állapot) * k >> 16` fixpontos frissítést, majd `állapot >> 7` bájtra vágást végez, és a visszamenet már a vágott előremeneti képet olvassa. Egyetlen OpenCV Gaussian vagy dobozszűrő más köztes kerekítést adna.
- **LocalContrast:** A natív `BlurImageOperation` hat dobozmenete minden menet után `sum // divisor` szerint vágja a képet bájtra. Erre jön a `strength` Q11-egész szorzása, `>> 9`, majd `+2 >> 2` és a menetenkénti telítés; egy összevont OpenCV-szűrő ezt a kerekítési sorrendet megváltoztatná. A mért ág ezen a gépen 0,95× lett, tehát lassabb a főágnál.
- **Pixelate:** A kicsinyítés a Picasa `ResizeImageOperation` 14 bites fixpontos doboz-súlyait használja, a két tengely külön kerekítési szabályával és a köztes bájtképpel. Az `INTER_AREA` eltérő területi súly- és kerekítési szabálya a nem egész arányú méreteknél nem ad minden képpontra azonos eredményt.
- **DropShadow:** Az árnyék alfa-csatornáján a natív blur hat menetet végez; mindegyik a sugárból képzett egész súlyokat használja, majd a pontos osztóval lefelé kerekít és bájtra vág. Egyetlen `GaussianBlur` vagy összevont konvolúció elhagyná ezeket a köztes vágásokat, ezért eltérhetne a bájtazonos képtől.

A Holga friss páros mérése 1,73× gyorsulást mutatott, így teljesült a visszaállítást elkerülő 1,15×-ös küszöb; a LUT-os kontraszt és a gyorsítótárazott zajmező megmaradt. A grain2 gyorsítótár méret+mag kulcsa mellett a kötegfolyam képenként új magja is külön zajt ad; ezt a zárókör regressziós őre cache nélkül és cache-sel is összeveti.
