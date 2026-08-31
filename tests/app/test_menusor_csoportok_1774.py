"""#1774 — a menüsor szerkezete a MÉRT eredetit kövesse.

**A bejelentés (tulajdonos, 2026-08-31):** „A Picasa 3 felső
menüszerkezete eltérő, mint a PicasaPy-jé."

**A bizonyíték.** A tulajdonos nyolc képernyőmentést készített a magyar
Picasa 3.9 mind a nyolc menüjéről (`Picasa-3-menuk`). A mentésekből a
tételek sorrendje ÉS az elválasztók helye hiánytalanul kiolvasható — az
inaktív tételek is látszanak rajtuk, tehát nincs rejtett csoport. A mérés
a `docs/specs/picasa-menusor-csoportok.md`-ben van, tételesen.

**Amit MÉRTÜNK nálunk (a javítás előtt):** a nyolc menüből ötben tért el a
csoportosztás — a Fájl menüben hiányzott két elválasztó és volt egy
fölösleges, a Létrehozás menü egyetlen csoport volt a mért három helyett,
a Kép menüből hiányzott három elválasztó és a „Megjelenítés” tétel.

Az őr **forrásszöveg-alapú**, mint a `test_qml_menubar_audit.py` második
rétege: az elválasztó nem kap `objectName`-t, és az élő QML-fából a
sorrendje nem olvasható ki megbízhatóan (a `menuAt`/`itemAt` visszatérési
típusa PySide6-ból nem hívható). A forrás viszont pontosan azt írja le,
amit a felhasználó lát.

**Az őr foga.** Ha valaki elválasztót vesz ki vagy tesz be, vagy tételt
mozgat egy másik csoportba, a teszt megnevezi a menüt és kiírja mindkét
alakot. A „mienk-e vagy az eredetié” kérdést az `ELTERESEK` tábla
válaszolja meg: ami ott szerepel, az TUDOTT és INDOKOLT eltérés — ami nem,
az hiba.
"""

from __future__ import annotations

import re
from pathlib import Path

_MENU_QML = (
    Path(__file__).resolve().parents[2]
    / "src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml"
)

#: Elválasztó a várt alakokban.
SZ = "---"

#: A menüsor sorrendje — mind a nyolc mentés menüsávja ezt mutatja.
MENUSOR = [
    "&File",
    "&Edit",
    "&View",
    "F&older",
    "&Picture",
    "&Create",
    "&Tools",
    "&Help",
]

#: A várt szerkezet menünként. Az almenük `"… >"` alakban szerepelnek, a
#: tartalmuk nem ennek az őrnek a dolga (a Rendezés almenüre a #1595 és a
#: #1766 fut külön).
VART: dict[str, list[str]] = {
    "&File": [
        "New Album...",
        SZ,
        "Add Folder to Picasa...",
        "Add File to Picasa...",
        "Import From...",
        "Import From Google Photos...",
        SZ,
        "Open File(s) in Editor",
        SZ,
        "Move to New Folder...",
        "Rename...",
        SZ,
        "Save",
        "Revert",
        "Undo Save",
        SZ,
        "Save As...",
        "Save a Copy",
        "Export Picture to Folder...",
        SZ,
        "Locate on Disk",
        "deleteCommandText",
        SZ,
        "Print...",
        "E-Mail...",
        "Order Prints...",
        SZ,
        "E&xit",
    ],
    "&Edit": [
        "Undo Paste All Effects",
        "Undo Batch Edit",
        SZ,
        "Cut",
        "Copy",
        "Paste",
        SZ,
        "Copy All Effects",
        "Paste All Effects",
        SZ,
        "Copy Text",
        "Paste Text",
        SZ,
        "Select All",
        "Select Starred",
        "Invert Selection",
        "Clear Selection",
    ],
    "&View": [
        "Library View",
        SZ,
        "Small Thumbnails",
        "Normal Thumbnails",
        "Edit View",
        SZ,
        "Properties",
        "Tags",
        "People",
        "Places",
        SZ,
        "Show Editing Controls",
        SZ,
        "Slideshow",
        "Timeline",
        SZ,
        "Search Options",
        "Thumbnails Only",
        "Hidden Pictures",
        SZ,
        "Use Color Management",
        "Dark Theme",
        "Display Mode >",
        SZ,
        "Thumbnail Caption >",
        "Folder View >",
    ],
    "F&older": [
        "Edit Description...",
        "View Slideshow",
        SZ,
        "Refresh Thumbnails",
        "Sort By >",
        SZ,
        "Hide",
        "Show",
        SZ,
        "Print Thumbnails...",
        "Export as HTML Page...",
        SZ,
        "Locate on Disk",
        "Remove from Picasa...",
        SZ,
        "Move...",
        "Delete...",
    ],
    "&Picture": [
        "View and Edit",
        "Batch Edit >",
        SZ,
        "Undo All Edits",
        SZ,
        "Hide",
        "Show",
        SZ,
        "Reset Face Positions",
        SZ,
        "Properties",
    ],
    "&Create": [
        "Set as Desktop Background...",
        "Make a Poster...",
        SZ,
        "Picture Collage...",
        "Add to Screensaver...",
        "Make a Gift CD...",
        "Movie >",
        SZ,
        "Publish to Blogger...",
    ],
    "&Tools": [
        "Folder Manager...",
        "Upload Manager...",
        "People Manager...",
        SZ,
        "Find Duplicates...",
        "Find Faces...",
        SZ,
        "Configure Photo Viewer...",
        "Configure Screensaver...",
        SZ,
        "Back Up Pictures...",
        "Batch Upload...",
        "Adjust Date and Time...",
        SZ,
        "Upload >",
        "Geotag >",
        "Experimental >",
        SZ,
        "Configure Buttons...",
        "Language >",
        "Options...",
    ],
    "&Help": [
        "Help Contents and Index",
        "Keyboard Shortcuts",
        SZ,
        "Picasa Forums",
        "Online Information",
        "Product Release Notes",
        "Privacy Policy",
        "Terms of Service",
        SZ,
        "Check for Updates",
        SZ,
        "Performance Monitor",
        "Test Mode (logs the next startup)",
        "Send Log...",
        "About PicasaPy",
    ],
}

#: TUDOTT és INDOKOLT eltérések a mért eredetitől. Ami itt nincs benne, az
#: a mérés szerint egyezik — ha eltér, az hiba. A tábla azért van a
#: tesztben, hogy a szerkezet és az indoka EGY helyen legyen olvasható.
ELTERESEK = {
    "&File · Undo Save": (
        "Az eredetiben az „Undo Save” nem menütétel, hanem a "
        "Visszaállítás párbeszéd gombja (`CThumbUI::FileRevert::undosave`) "
        "és a szerkesztősáv tippje (`CFilterStackUI::savetip`). Nálunk "
        "a #444 óta menütétel; az áthelyezés külön jegy, mert a "
        "párbeszédünkben ma nincs meg a gomb, tehát a tétel törlése "
        "elvágná az egyetlen elérési utat."
    ),
    "&Edit · Undo Paste All Effects + Undo Batch Edit": (
        "A mentésen a Szerkesztés menü NEM kezdődik visszavonás-"
        "csoporttal, pedig az inaktív tételei látszanak. A szövegtárban "
        "viszont van `eMenuEdit::ID_UNDO` és `ID_REDO`. A mi két tételünk "
        "élő funkció; amíg nem tudjuk, mikor jelenik meg az eredetiben, "
        "nem vesszük ki."
    ),
    "&View · Dark Theme": (
        "Sötét téma — nálunk van, az eredetiben nincs. A mért 7. csoport "
        "(Színkezelés + Megjelenítési mód) végére került, mert "
        "megjelenítési beállítás, nem nézetváltó."
    ),
    "&Tools · Find Duplicates... + Find Faces...": (
        "Az eredeti Eszközök menü felső szintjén egyik sincs. A "
        "szövegtárban `eMenuTools::ID_DUPES` („Show Duplicate Files”) "
        "megvan — valószínűleg a Kísérleti almenüben, amit a mentés nem "
        "nyit ki. Az áthelyezés bizonyíték nélkül találgatás lenne."
    ),
    "&Tools · Language >": (
        "Nyelvváltó almenü. Az eredetiben nincs: a Picasa nyelvét a "
        "windowsos telepítő rögzítette, futásidőben nem volt váltható. "
        "Nálunk a #333 óta futásidejű, ezért kell menütétel."
    ),
    "&Help · fejlesztői tételek": (
        "Teljesítménymérő, tesztmód, naplóküldés — a mi eszközeink; az "
        "eredeti Súgó menü utolsó csoportja csak a névjegy. Az eredeti "
        "„A Picasa eltávolítása” tételének nálunk nincs megfelelője "
        "(nincs Windows-telepítőnk)."
    ),
}


def _alak() -> dict[str, list[str]]:
    """A `PicasaMenuBar.qml` felső szintű menüi és tételeik, sorrendben."""
    forras = re.sub(r"//[^\n]*", "", _MENU_QML.read_text(encoding="utf-8"))
    melyseg = 0
    verem: list[int] = []
    menuk: list[tuple[str, list[str]]] = []
    minta = (
        r"((?:Picasa)?Menu\s*\{|PicasaMenuItem\s*\{|MenuItem\s*\{"
        r"|MenuSeparator\s*\{\s*\}|\{|\})"
    )
    for talalat in re.finditer(minta, forras):
        jel = talalat.group(1)
        if jel.startswith("MenuSeparator"):
            if len(verem) == 1:
                menuk[-1][1].append(SZ)
            continue
        if jel.endswith("{") and jel != "{":
            fajta = jel.split()[0]
            reszlet = forras[talalat.end() : talalat.end() + 700]
            if fajta in ("Menu", "PicasaMenu"):
                cim = re.search(r'title:\s*qsTr\("([^"]*)"\)', reszlet)
                felirat = cim.group(1) if cim else "?"
                if not verem:
                    menuk.append((felirat, []))
                elif len(verem) == 1:
                    menuk[-1][1].append(felirat + " >")
                verem.append(melyseg)
            else:
                if len(verem) == 1:
                    szoveg = re.search(
                        r'text:\s*(?:qsTr\("([^"]*)"\)|bar\.(\w+))', reszlet
                    )
                    menuk[-1][1].append(
                        (szoveg.group(1) or szoveg.group(2))
                        if szoveg
                        else "?"
                    )
            melyseg += 1
        elif jel == "{":
            melyseg += 1
        else:
            melyseg -= 1
            if verem and verem[-1] == melyseg:
                verem.pop()
    return dict(menuk)


def test_a_menusor_sorrendje_a_mert_eredetit_koveti():
    assert list(_alak()) == MENUSOR, (
        "a menüsor sorrendje eltér a mért eredetitől "
        "(docs/specs/picasa-menusor-csoportok.md, 1. szakasz)"
    )


def test_minden_menu_szerkezetet_ellenoriz_a_tabla():
    """Az őr foga: ne lehessen új menüt hozzáadni tábla nélkül."""
    assert set(VART) == set(MENUSOR)
    assert len(_alak()) == 8


def test_a_csoportok_a_mert_eredetit_kovetik():
    kapott = _alak()
    elteres: list[str] = []
    for cim in MENUSOR:
        if kapott.get(cim) != VART[cim]:
            elteres.append(
                f"\n[{cim}]\n  mért eredeti: {' | '.join(VART[cim])}"
                f"\n  nálunk:       {' | '.join(kapott.get(cim, ['—']))}"
            )
    assert elteres == [], (
        "a menük csoportosztása eltér a mért eredetitől (#1774; "
        "docs/specs/picasa-menusor-csoportok.md, 2. szakasz):"
        + "".join(elteres)
    )


def test_az_elteresek_indoka_le_van_irva():
    """Minden tudott eltéréshez tartozzon érdemi magyarázat."""
    for kulcs, indok in ELTERESEK.items():
        assert len(indok) > 60, f"{kulcs}: az indok túl szűkszavú"
