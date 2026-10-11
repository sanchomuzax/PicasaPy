# Képernyővédő

A képernyővédő a képeidből teljes képernyős vetítést indít. Linuxon a
PicasaPy-n belül állítod be és nézed meg, és ha az asztali környezeted
támogatja, a gép tétlenségekor magától is elindul (lásd lent: *Indítás
a gép tétlenségekor*).

## Képek hozzáadása

Jelölj ki képeket, majd **Létrehozás ▸ Hozzáadás a képernyővédőhöz…**. A
program a képeket a képernyővédő saját **Kijelölt képek** listájához
fűzi, és a felület tetején kiírja: „*N* kép hozzáadva a
képernyővédőhöz." Ugyanaz a kép nem kerül kétszer a listába.

Ha ezt egy **album** megnyitott nézetében teszed, a program előbb
rákérdez: „Biztosan hozzá szeretné adni a kijelölt album összes képét?"
Az **Igen** után kerülnek a képek a listába; a **Nem** és a **Mégse**
nem ad hozzá semmit.

Az üzenet akkor is megjelenik, ha egyetlen új kép sem került a listába —
például mert mind szerepelt már benne; ilyenkor „0 kép hozzáadva a
képernyővédőhöz." áll rajta.

## Beállítás

**Eszközök ▸ Képernyővédő konfigurálása…** nyitja meg az ablakot:

- **Képek megjelenítése innen:** — jelölőnégyzetes lista a mappákkal és
  albumokkal, valamint a **Kijelölt képek** tétellel (a fent
  hozzáadott képek). Ami be van jelölve, abból válogat a vetítés. Ha
  nincs egyetlen képet tartalmazó mappa vagy album sem, ezt írja:
  „Nincs képet tartalmazó mappa vagy album."
- **Vizuális effektus:** — **Kivágás**, **Szétoszlás**, **Szétoszlás
  feketén át**, **Szétoszlás fehéren át** vagy **Pásztázás és
  nagyítás**.
- **Képek váltása:** — 1 és 30 másodperc között.
- **Feliratok megjelenítése** — a képfelirat is látszik.
- **Indítás, ha a gép ennyi ideig tétlen:** *N* **perc** — bekapcsolva
  a képernyővédő magától elindul, ha ennyi ideig nem nyúlsz se az
  egérhez, se a billentyűzethez (1 és 120 perc között). Lásd lent.
- **Előnézet** — elindítja a vetítést. A gomb szürke, amíg nincs
  bejelölt forrásban kép.

Az **OK** és a **Mégse** bezárja az ablakot; a választásaid már a
beállítás közben megmaradnak.

## Az előnézet

Az **Előnézet** teljes képernyőre vált, és a bejelölt forrásokból
körbe-körbe, megállás nélkül vetíti a képeket. **Bármilyen billentyű
vagy egérmozdulat vagy kattintás kilép** belőle, és visszatérsz a
korábbi ablakmérethez. Zene a képernyővédő alatt nem szól. Ha a
bejelölt források egyikében sincs elérhető kép, a program szól: „A
kiválasztott képernyővédő-forrásokban nincs elérhető kép."

## Indítás a gép tétlenségekor

A **Képernyővédő konfigurálása…** ablakban az **Indítás, ha a gép ennyi
ideig tétlen:** jelölőnégyzet kapcsolja be. A beállítás azonnal érvényes,
újra bejelentkezni nem kell, és a következő bejelentkezéskor is megmarad.
A vetítés ugyanaz, mint az Előnézeté: a bejelölt forrásokból, a
beállított effektussal és képidővel megy, és **bármilyen billentyű,
egérmozdulat vagy kattintás kilép** belőle. A PicasaPy főablakának ehhez
nem kell futnia.

**Hol működik.** A wlroots-alapú Wayland-asztalokon — **labwc** (a
Raspberry Pi OS alapértelmezése), **sway**, **Wayfire**, river, Hyprland,
niri —, ha a **swayidle** program telepítve van (Raspberry Pi OS-en
alapból ott van; máshol a `swayidle` csomag). Más környezetben a
jelölőnégyzet szürke, és alatta olvasható, miért:

- **GNOME, KDE és az X11-es asztalok** saját képernyővédő-kezelést
  használnak, amelybe a PicasaPy nem tud megbízhatóan beépülni — itt
  „Ezen az asztali környezeten (…) nem támogatott” áll.
- Ha a **swayidle** hiányzik, a program a telepítését kéri.

**Mit állít be a program.** Egyetlen fájlt ír, a saját beállításaid közé:
`~/.config/autostart/picasapy-screensaver.desktop`. Ez bejelentkezéskor
egy `swayidle` figyelőt indít, amely a megadott tétlenség után a
`picasapy --screensaver` parancsot futtatja. Bekapcsoláskor a figyelő
rögtön el is indul. Kikapcsoláskor a program ezt a fájlt törli, és a
saját figyelőjét leállítja; a rendszer más `swayidle` beállításaihoz
(például a képernyő kikapcsolásához) nem nyúl.

Az automatikus indítást a Raspberry Pi OS labwc-asztala és a legtöbb
teljes asztali környezet elvégzi. Ha a te asztalod nem futtatja az
`~/.config/autostart` bejegyzéseit (például a puszta sway), a figyelő az
adott munkamenetben működik, a következő bejelentkezéskor viszont neked
kell elindítanod — a parancs a fenti fájl `Exec=` sorában áll.

A vetítés kézzel is indítható a parancssorból: `picasapy --screensaver`.
Ha a bejelölt forrásokban nincs kép, ablak nem nyílik, a program pedig
kiírja, miért.
