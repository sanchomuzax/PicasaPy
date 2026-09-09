# ADR-011: A PicasaPy nem futtat hálózati kiszolgálót, és nem regisztrál URL-sémát

**Állapot:** eldöntve · **Dátum:** 2026-09-09 · **Jegy:** #2023
(feltárás és mérés: #2023; a teljes felület leírása:
[`picasa-beepitett-webszerver.md`](../specs/picasa-beepitett-webszerver.md))

## A helyzet

Az eredeti Picasa 3 **saját HTTP-kiszolgálót futtat** (a `0x004c0000`–
`0x004cf000` tartományban), és regisztrál egy `picasa://` URL-sémát. Ami a
binárisból kiolvasva megvan:

| felület | bizonyíték (cím) |
|---|---|
| kérés-kapu: `AllowRemoteWeb` nélkül „Not allowed, this server supports localhost only." | `0x004cbc60` |
| HTTP Basic (`realm="Picasa"`), jelszó a `LANPassword`-ből, a felhasználónév fixen `picasaserver` | `0x004cbc60`, `0x004cce10` |
| WebDAV (`OPTIONS`/`PROPFIND`, `Multi-Status` XML), a 80-as portot igényli, megosztás: `\\localhost\picasa` | `0x004cb5f0`, `0x004c8f80`, `0x005cb990` |
| **14 végpont** (`/albumlist` … `/dbdebug`) + `/repost`, `/upload` | `0x004ca660`, `0x004ca830` |
| `/dbdebug` = **adatbázis-böngésző** (album/file/cat tábla HTML-ben) | `0x004c2af0` |
| `/uidebug` = a felület csomópontfája rajzolási időmérésekkel | `0x004c8350`, `0x004c7b30` |
| LAN-hirdetés: `computer=%s`, `user=%s`, `httpport=%d`, `dbid=%s` | `0x00937800` |
| `picasa://importbutton/?url=…` — **külső URL-ről tölt bővítményt** | `0x004bbaf0`, `0x004bbed0` |

Nálunk ma **egyik sincs**: a `src/` alatt nincs hallgatózó socket (mérve, ld.
lent), a hálózati műveleteink kizárólag **kimenők** (webexport fájlba, e-mail
átadása a rendszer levelezőjének).

## A döntés

**A PicasaPy szándékosan NEM építi meg ezt a felületet:**

1. nem futtat **hallgatózó** hálózati kiszolgálót (HTTP, WebDAV, RSS,
   bélyegkép-végpont, beküldő végpont);
2. nem hirdeti magát a helyi hálózaton (gépnév/felhasználónév),
3. nem regisztrál egyedi **URL-sémát** (`picasapy://` vagy hasonló),
4. és nem épít **külső URL-ről kódot betöltő** ágat.

Ez **nem hiány, hanem tudatos eltérés.** Ezért nem is szabad a lefedettségi
rangsorban „fehér foltként" előkerülnie: a
[`feature-map.md`](../specs/feature-map.md) „Nem cél" szakasza nevesíti.

## Miért

- **A támadási felület aránytalan a haszonhoz.** Egy fotókezelő
  alapfunkciójához nem kell beérkező kapcsolat. Az eredetiben ez a felület
  hitelesítést, jelszókezelést, WebDAV-ot és egy **adatbázis-böngésző lapot**
  hozott magával — ezek mindegyike külön karbantartandó, biztonságérzékeny
  kód.
- **A funkció alapja megszűnt.** A kiszolgáló haszna a Picasa Web
  Albums-ökoszisztémához kötődött (`repl=1`, `dbid`, album-replikáció); a
  szolgáltatás halott, tehát a felület sem szolgál semmit.
- **A külső URL-ről bővítményt betöltő ág** (`picasa://importbutton/?url=…`)
  ma elfogadhatatlan minta: távoli kód futtatása egy kattintásból.
- **A megosztásra van modern út.** Aki hálózaton akar képet megosztani, azt a
  meglévő **webexporttal** (statikus lapok lemezre) és a rendszer saját
  megosztásaival teszi — nem a fotókezelőbe épített kiszolgálóval.

## Amit ez NEM zár ki

- **A kimenő** hálózati műveletek (e-mail, jövőbeli feltöltés valamilyen
  szolgáltatásba) érintetlenek: a döntés a **beérkező** oldalról szól.
- **Album-megosztás hálózaton** (`LANShareAlbums`): ha valaha kell, az
  **külön jegyben**, külön döntéssel indul — nem ennek a felületnek a
  visszaépítésével.
- **Fejlesztői/hibakereső eszközök**: a mérőszkriptjeink futtathatnak
  ideiglenes kiszolgálót a saját gépen; a döntés a **terméket** (`src/`) köti.

## Az őr, ami betartatja

`tests/test_nincs_halozati_kiszolgalo_2023.py`: a `src/` alá bekerülő
hallgatózó socket (`bind(`, `listen(`, `HTTPServer`, `socketserver`,
`aiohttp`, `flask`, `uvicorn`) és az URL-séma-regisztráció elbukik rajta. A
próba **saját magát is ellenőrzi** egy ismert pozitívval — a nulla lelet csak
így jelent valamit.

*A szándékos eltérést a teszt védje, ne a jószándék.*

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás
hamis biztonságérzetet ad.*

⚠️ Ez a döntés **nem-építésről** szól, tehát nincs modul, ami „megvalósítja".
A `Megvalósítja` mező ezért a **mért állapotot** nevezi meg: azt a csomagot,
ahol a hálózati műveleteink élnek, és ahol a hiánynak fenn kell maradnia. A
betartatás teljes egészében az `Őrzi` mezőn múlik.

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/webexport`, `src/picasapy/mailer`
- **Őrzi:** `tests/test_nincs_halozati_kiszolgalo_2023.py`
