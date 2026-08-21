# Mappakezelő: helyi súgó és importgombok

- Állapot: elfogadva
- Dátum: 2026-08-21
- Kapcsolódó jegyek: #1161, #146, #231, #543

## Döntés

A Mappakezelő **Súgó** gombja helyi magyarázó ablakot nyit. Nem próbálja
megnyitni a Picasa megszűnt Google Support-oldalát.

Az **Add folder…** és az **Adopt Picasa folders…** gomb megmarad. Ezek tudatos
PicasaPy-kiegészítések: az első akadálymentes alternatíva a fa használatához,
a második pedig a #146-ban megvalósított Picasa-migráció egyetlen belépési
pontja. A három eredeti jobb oldali gomb (OK, Cancel, Help) sorrendjét és
98×28-as méretét nem változtatják meg; a kiegészítő műveletek a gombsor bal
oldalán maradnak.

## Indoklás

Az eredeti súgó URL-je ma már nem biztosít használható terméksúgót, ezért a
böngésző megnyitása hibának tűnne. A helyi szöveg hálózat nélkül is elérhető,
és a PicasaPy tényleges működését írja le.

A két kiegészítő gomb eltávolítása elrejtené a már támogatott migrációt, és
nehezebbé tenné egy nem látható vagy még be nem töltött mappa felvételét.
Mindkettő hozzáadó művelet; az OK/Mégse tranzakciós szabály az általuk
kezdeményezett mappamódosításra is érvényes.
