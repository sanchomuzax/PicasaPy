# Mentés, visszaállítás, visszavonás

A PicasaPy alapból nem nyúl a fájljaidhoz: a szerkesztéseket a képek
melletti `.picasa.ini` fájlban tartja. Ha viszont a **fájlba** is bele
akarod égetni a változtatásokat — mert máshol nyitod meg, vagy elküldöd
—, ezek a parancsok állnak rendelkezésre.

## Mentés

**Fájl ▸ Mentés** (Ctrl+S) a kijelölt képeket a szerkesztésekkel együtt
kiírja a lemezre.

A program **biztonsági másolatot készít** a fájlokról, és ezt a
megerősítő ablakban ki is írja. A másolat az eredeti mappában marad, így
később még visszaléphetsz.

Ha valamelyik képen olyan szerkesztés van, amit a program még nem tud
megjeleníteni (például egy régi Picasa-változat effektje), a mentés előtt
figyelmeztet: „A mentés ezek nélkül írja ki a képet, és a beállítások
elvesznek. Ez nem vonható vissza."

## Utolsó mentés visszavonása

A mentés után megjelenő üzenetben az **Utolsó mentés visszavonása**
gombbal visszahozod a fájl mentés előtti állapotát — a szerkesztéseid
közben megmaradnak. Csak a legutóbbi mentésre hat.

## Mentés másként és Másolat mentése

- **Fájl ▸ Mentés másként…** — a szerkesztett képet más néven, más helyre
  írja ki. JPEG és WebP formátumot kínál.
- **Fájl ▸ Másolat mentése** — az eredeti mellé ír egy szerkesztett
  másolatot, magától adott névvel.

Ha a választott név foglalt, a program szól: „A fájl mentése nem
lehetséges. Már van ilyen nevű fájl."

## Visszaállítás

**Fájl ▸ Visszaállítás** a fájlt az eredeti változatára állítja vissza.
Ez a mentéskor készült biztonsági másolatot használja, ezért csak akkor
kapcsolható be, ha van ilyen másolat.

A program rákérdez: „Visszaállítja ezeket a fájlokat az eredeti
változatra? Ez nem vonható vissza, és minden változtatás elvész."

## Összes szerkesztés visszavonása

**Kép ▸ Összes szerkesztés visszavonása** nem a fájlt, hanem a
szerkesztések listáját törli. A fájl érintetlen marad; a kép egyszerűen
újra úgy néz ki, mint eredetileg.

## Melyik mit csinál?

| parancs | mire hat | elvész-e a szerkesztés |
|---|---|---|
| Mentés | a fájlra a lemezen | nem, csak beleég |
| Utolsó mentés visszavonása | az utolsó lemezre írásra | nem |
| Visszaállítás | a fájlra a lemezen | igen |
| Összes szerkesztés visszavonása | csak a szerkesztéslistára | igen (a fájl ép) |

## Ha nem sikerül a mentés

- **„Fájlformázási hiba miatt a fájl nem menthető."** — a fájl formátumát
  a program nem tudja kiírni.
- **„A képet nem lehet kicserélni. Próbálja újra másik fájlnévvel."** — a
  cél fájl épp foglalt vagy nem írható.
- Ha a lemez megtelt vagy csak olvasható, a program erről is szól, és
  megnevezi az érintett fájlt.
