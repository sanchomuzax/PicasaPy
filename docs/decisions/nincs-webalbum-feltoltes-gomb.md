# ADR-012: A szerkesztő fejlécébe NEM kerül webalbum-feltöltő gomb

**Állapot:** eldöntve · **Dátum:** 2026-09-10 · **Jegy:** #1935
(mérés és teljes geometria:
[`szerkeszto-felso-sav.md`](../specs/szerkeszto-felso-sav.md) 2. és 4. szakasz)

## A helyzet

Az eredeti Picasa 3 szerkesztő-fejlécében a „Vissza a könyvtárhoz" és a
„Lejátszás" közt **két, egymást kizáró gomb** ül ugyanazon a helyen:

| elem | méret | ikon | buboréksúgó (eredeti) |
|---|---|---|---|
| `editpanel/quickupload` | 34 × 22 | 23 × 15 | „Upload to your Web Albums Drop Box" |
| `editpanel/uploadchanges` | 34 × 22 | 24 × 17 | „Update online copy with this version" |

Mindkettő `m_hidden` az `upload_buttons_container`-ben
(`editpanel.tre:1143–1155`), a parancsazonosító `OneUp::ID_QUICKUPLOAD`
(`0x00cae564`). A mérés két független forrásból egyezik: a `respack.yt`
rétegei és a tulajdonos képernyőfelvétele (`x 1222…1256` = 34 képpont).

A gombok mögötti szolgáltatás — a **Google Web Albums** és annak „Drop Box"
mappája — **megszűnt.**

## A döntés

**A két gombot nem építjük meg — se élőn, se letiltott (szürke) állapotban.**

A tulajdonos szava (2026-09-10, #1935, képernyőképpel):

> „Ez egy nem működő, hibás funkcióra vezető gomb. Jelenleg ne implementáljuk,
> csak dokumentáljuk, ha majd lesz újra bármiféle »Feltöltés a Webalbumok
> Főalbum mappájába« szerű funkció."

⚠️ Ez **felülírja** a 2026-09-05-i korábbi döntést („legyenek ott szürkén").
A szürke gomb is ígéret: ott áll a felületen egy vezérlő, ami nem működő
funkcióra vezet.

## Amit ez NEM jelent

* **A mérés nem vész el.** Az elemnevek, a méretek, az ikonméretek, a
  sávon belüli hely, a buboréksúgók és a parancsazonosító a specben állnak —
  ha egyszer lesz megint feltöltés-jellegű funkció, a gomb egy kör alatt
  megépíthető.
* **Nem lefedettségi hiány.** A `szerkeszto-felso-sav.md` a két elemet
  feltártként tartja; a hiány itt kimondott döntés, nem elmaradás.
* **Nem érinti a meglévő kimenő utakat:** a webes export fájlba dolgozik
  (`webexport/`), az e-mail a rendszer levelezőjének adja át a képeket — azok
  nem online szolgáltatások, és változatlanok.

## Ha visszatér a funkció

Akkor **új jegy** nyílik magára a feltöltés-funkcióra, és a gomb annak a
jegynek a felületi része lesz — a sorrend nem fordítható meg: előbb a
működő funkció, utána a belépési pont (#936 elve: a semmit nem tevő vezérlő
rosszabb a hiányzónál).

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás hamis
biztonságérzetet ad.*

⚠️ Ez a döntés **nem-építésről** szól, tehát nincs modul, ami „megvalósítja".
A `Megvalósítja` mező ezért a **mért állapotot** nevezi meg: azt a fájlt,
ahol a szerkesztő felső sávja épül, és ahol a hiánynak fenn kell maradnia. A
betartatás teljes egészében az `Őrzi` mezőn múlik.

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/app/qml/PicasaPy/PhotoViewer.qml`
- **Őrzi:** `tests/app/test_nincs_webalbum_feltolto_gomb_1935.py`
