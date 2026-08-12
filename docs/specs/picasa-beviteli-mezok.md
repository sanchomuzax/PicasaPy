# Beviteli mezők és párbeszédpanelek a Picasában

A `respack.yt` **140 `.tre` elrendezésforrásából** és a réteg-névindexből.
A számok és a szerkezet a program saját forrásából valók, nem
képernyőkép-becslésből.

## A vezérlő-készlet (a teljes szótár)

A `.tre` rétegnevek zárójeles/kettőspontos előtagja adja meg a típust:

| típus | előfordulás | mi |
|---|---|---|
| `superbutton(sablon, id)` | 259 | a fő gombtípus, sablonnal |
| `text(id)` | 235 | szövegcímke (statikus) |
| `rect:` | 196 | színes/keretes téglalap |
| `button(...)` / `button:` | 145 | egyszerű gomb |
| `buttcon(...)` | 84 | ikonos gomb, három állapotképpel (`_n`, `_p`, `_h`) |
| `static(id)` | 71 | statikus felirat-tároló |
| `decrect(stílus)` | 43 | **süllyesztett/kiemelt keret** (`softbevel`, `flatbevel`) |
| **`window:`** | **37** | **natív, operációs rendszer szintű vezérlő** |
| `clip:` | 128 | vágókeret (görgethető tartalom) |
| `popuplist:` | 41 | **legördülő lista** |
| `vbutton:` | 25 | függőleges/összetett gomb |
| `buttcontainer:` | 21 | **rádiógomb-csoport** (egymást kizáró) |
| `listbox:` | 13 | listadoboz |
| `butlink(...)` | 11 | hivatkozásként viselkedő gomb |
| `colorpickerpanel(...)` | 7 | színválasztó panel |
| `colorwheel(...)` | 3 | színkorong |

**Nincs saját „szövegmező" típus.** A Picasa a beviteli mezőket **natív
vezérlőként** ágyazza be — ez a `window:` réteg.

## A beviteli mező mintája

Minden szövegbeviteli hely ugyanígy épül fel:

```
<panel>/rect(SZÍN): <nev>_base      ← a KERET (ARGB szín)
<panel>/window: <nev>               ← a natív beviteli vezérlő
[ <panel>/buttcon: <nev>_icon ]     ← opcionális ikon
[ <panel>/button: <nev>_clr ]       ← opcionális törlő gomb
[ <panel>/listbox: <nev>autocomplete ] ← opcionális kiegészítés
```

Példa — a keresőmező (`searchcontainer`):

```
rect(FF7F9DB9): searchbase     ← keret, #7F9DB9 (halvány kékesszürke)
window: search                 ← a mező maga
search_icon                    ← nagyító ikon
button: searchclr              ← törlő X (alapból rejtett!)
listbox: searchautocomplete    ← automatikus kiegészítés
```

A `searchclr` `m_hidden` alapállapotban — **csak akkor jelenik meg, ha van
beírt szöveg**.

## A program ÖSSZES beviteli mezője

| panel | mező | mire |
|---|---|---|
| `searchcontainer` | `search` | keresés (kiegészítéssel) |
| `tagpanel` | `taginput` | címke beírása |
| `keywords` | `addkeyword`, `keywordlist` | kulcsszó hozzáadása + lista |
| `quicktagconfig` | `edit_0` … `edit_9` | **a tíz gyorscímke** |
| `acquirepanel` | `subfolder` | importálás célmappája |
| `titledialog` | `line1` | szövegdia felirata |
| `publish` | `cdname`, `uploadaccount` | lemeznév, fiók |
| `geopanel` | `searchinput` | helykeresés a térképen |
| `makemoviepanel` | `inputtext` | szövegdia a filmben |
| `compose_mail` / `compose_share` | `to`, `subject`, `content` | e-mail |
| `buzzupload` | `title`, `description`, `comments` | feltöltés |
| `upload` | `title`, `description`, `contact_edit` | webalbum |
| `collab` | `contact_edit` | megosztás |

Ebből **PicasaPy-releváns**: `search`, `taginput`, `addkeyword`,
`edit_0…9` (gyorscímkék), `subfolder` (import), `line1` (szövegdia),
`searchinput` (geo). A többi a halott online szolgáltatásokhoz tartozik.

## A párbeszédpanelek szerkezeti mintája

A `foldermgr` (ld. #543) példáján, ami az összesre jellemző:

```
base: root                       ← m_offsetB + m_scaleX (alul rögzít, vízszintesen nyúlik)
├── left_side   x: 4 … 50%
├── right_side  x: 50% … jobb−4
│   ├── <magyarázó szöveg>       (14-es font)
│   ├── decrect(softbevel)       ← SÜLLYESZTETT csoportkeret
│   │   ├── static: <cím>
│   │   ├── buttcontainer        ← rádiógomb-csoport
│   │   └── line                 ← elválasztó vonal (m_scaleX)
│   └── listbox
├── size                         ← ÁTMÉRETEZŐ SAROK (Property winsize 1)
└── ok / cancel / help           ← m_offsetRB (jobb alsó sarok)
```

**Négy visszatérő elem, amit nálunk általában nem használunk:**

1. **`decrect(softbevel/flatbevel)`** — süllyesztett csoportkeret a logikailag
   összetartozó vezérlők körül.
2. **`line`** — vízszintes elválasztó a csoporton belül, `m_scaleX`-szel.
3. **`size`** — átméretező sarok, `Property winsize 1`.
4. **Súgó gomb** az OK/Mégse mellett, jobb alsó sarokban.

## Rádiógombok és jelölőnégyzetek

- **Rádiógomb**: `buttcontainer:` a csoport, benne `buttcon(...)` elemek a
  közös `globalbuttons/rb2_n|p|h` képekkel. Az alapértelmezettre
  `Property setpressed 1` kerül.
- **Jelölőnégyzet**: `buttcon_checkbox` sablonnal.
- **A felirat is kattintható**: `m_hit_childlabel` — a címke a gomb
  gyermeke, és a rákattintás a gombot nyomja.

## Legördülő listák

`popuplist:` (41 előfordulás). A tételek térközét
`Property itempadding <bal> <fent> <jobb> <lent>` adja meg — a
`titledialog`-ban pl. `2 2 10 2` a betűtípus-választónál és `2 2 5 2` a
méretnél.

## Teendő

Ez a lap a **szerkezetet** rögzíti. A konkrét eltérések panelenkénti
végigvezetése külön munka; a `foldermgr` már megvan (#543), a többi
párbeszédpanel `.tre`-je ugyanígy kiolvasható:

`acquirepanel` · `keywords` · `quicktagconfig` · `titledialog` ·
`printoptions` · `printpanel` · `outputlayout` · `publish` ·
`searchoptions` · `propertiespanel` · `peoplepanel` · `tagpanel`
