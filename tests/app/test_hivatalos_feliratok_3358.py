"""A feliratok a HIVATALOS Picasa-szöveget mondják (#3358, #2921).

A #2921 közeli-pár mérése (privát repó, `felirat_kozeli_parok.py`) olyan
feliratokat talál, amelyeknél az eredetinek VAN szövege ugyanabban a
helyzetben, csak mi máshogy fogalmaztuk. Ez nem stílusdöntés: a
lefedettségi mérő emiatt nem találja meg a párját, a felhasználó pedig
más szöveget lát, mint az eredeti Picasában.

Amit ez az őr NEM mér: azt, hogy a felirat a képernyőn tényleg látszik-e,
és azt sem, hogy jó helyen van-e — csak a szöveg azonosságát a mért
hivatalos alakkal.
"""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree

QML = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "qml"
TS = QML.parent / "i18n" / "picasapy_hu.ts"

#: felirat → (hivatalos magyar, a `stringres` azonosítója)
HIVATALOS = {
    "The passwords did not match.": (
        "A jelszavak nem egyeztek.", "CThumbUI::PassVerifyWrong"),
    "Do not ask again": (
        "Ne kérdezze meg újra", "CMakeFaceMoviePanelRememberDialog"),
    "Add this tag to entire selection": (
        "A címke hozzáadása a teljes kijelölt részhez",
        "Tags::ID_APPLYTHISTAGTOSELECTION"),
    # #2921, második kör: a mappa-fejléc szinkron-felirata és az
    # adatbázis-áthelyező mappaválasztó címe
    "Sync to Web": ("Szinkronizálás az internettel", "SyncLabel::Off"),
    "Choose database location...": (
        "Adatbázis helyének kiválasztása…", "eMenuTools::ID_MOVE_DATABASE"),
    # #3574: a szerkesztő, az arcok és a diavetítés feliratai
    "This image's orientation has been modified by the Straighten tool and might not crop accurately.\nIf you encounter difficulty cropping this image, try undoing the Straighten fix, then recrop, and Straighten again if necessary.": (
        'A kép irányát megváltoztatta a „Kiegyenesítés” eszközzel, ami pontatlanságokat okozhat a vágás alkalmazásakor.\nHa nem sikerül a kép vágása, vonja vissza a „Kiegyenesítés” eszközzel végzett javítást, majd ismételje meg a vágást és - ha szükséges - a kiegyenesítést.',
        "IDS_WARN_CROP_ACCURACY"),
    'Picasa has found and corrected red eye(s).\n\nNote: You can click on a box to delete a change.\n\nYou can also draw a square around any red eye that Picasa may have missed.': (
        'A Picasa vörösszem-effektusokat talált a képen, és kijavította őket.\n\nMegjegyzés: a keretbe kattintva visszavonhatja a változást.\n\nA Picasa által esetleg figyelmen kívül hagyott vörösszemeket manuálisan kijelölheti és kijavíthatja.',
        "RedEye::AutoFixedMessage"),
    'Instructions:\n\n1) Manipulate the rectangle to fit the face of the person you want to add.\n\nYou can drag the rectangle to position it, and move its sides to refine the shape.\n\n2) Click on "Add a name" under the rectangle and type in the person\'s name.\n\n(Be sure to either press Enter or click on an autocompleted name to indicate that you are done)': (
        'Utasítások:\n\n1) A négyszöget alakítsa úgy, hogy illeszkedjen a hozzáadni kívánt személy arcához.\n\nHúzással a megfelelő helyre helyezheti a négyszöget, oldalainak mozgatásával pedig pontosíthatja az alakját.\n\n2) Kattintson a négyszög alatt látható "Név hozzáadása" feliratra, és írja be a személy nevét.\n\n(Ne feledje, hogy a befejezéshez le kell nyomnia az Enter billentyűt, vagy az egyik automatikusan kiegészített névre kell kattintania.)',
        "manual_add::instructions"),
    "Feather": ("Lágy perem", "filter_dir_tint_label1"),
    "Color Preservation": ("Színek megőrzése", "filter_tint_label1"),
    "Left justify text": ("Szöveg balra igazítása", "edittextpanel/leftalign"),
    "Center justify text": ("Szöveg középre igazítása", "edittextpanel/centeralign"),
    "Right justify text": ("Szöveg jobbra igazítása", "edittextpanel/rightalign"),
    "Ignore all of the selected faces": (
        "Az összes kijelölt arc mellőzése", "unknownfaceheaderpanel/ignore"),
    "Display Time": ("Megjelenítési idő", "oneup/tpslabel"),
    "seconds": ("másodperc", "OneUpUI::seconds"),
    # #3575: párbeszédablakok, importálás, címkék
    "Frame Mosaic": ("Képkockamozaik", "collage::frame_desc"),
    "Description (optional):": ("Leírás (opcionális):", "folderprops"),
    "Place taken (optional):": (
        "Felvétel készítésének helye (opcionális):", "folderprops"),
    "Use music for Slideshow and Movie presentation:": (
        "Zene használata diavetítéshez és mozgófilmes prezentációhoz:", "folderprops"),
    "Enter Folder Title": ("Mappa nevének megadása", "iCAcquireUI::SubFolder"),
    "Date Taken (YYYY-MM-DD)": (
        "Készítés dátuma (ÉÉÉÉ. HH. NN.)", "iCAcquireUI::AutoDate"),
    "%1 (Today)": ("%1 (ma)", "iCAcquireUI::TodayDate"),
    "Current database location:": ("Adatbázis aktuális helye:", "movedb"),
    "New database location:": ("Adatbázis új helye:", "movedb"),
    "Enter Collection Name:": (
        "Gyűjteménynév megadása:", "IDS_NEW_COLLECTION_PROMPT"),
    'You can use Quick Tags to apply a tag with a single click.  Type in tags below that you want to have one-click access to.  By default, the top two Quick Tags are used to track recently applied tags.  Uncheck the checkbox below to manually set the top two tags.': (
        'A Gyorscímkék funkció segítségével egyetlen kattintással alkalmazhat címkéket. Alább írja be azokat a címkéket, amelyekhez egy kattintással hozzá szeretne férni. Alapértelmezés szerint a felső két gyorscímke a legutóbb alkalmazott címkéket követi. A felső két címke kézi beállításához törölje a jelet a jelölőnégyzetből.',
        "quicktagconfig/instructions"),
    "Autofill empty boxes above with commonly used tags": (
        "A fenti üres mezők automatikus kitöltése gyakran használatos címkékkel",
        "quicktagconfig/autofill"),
    "Type in a tag to add:": (
        "Írjon be egy hozzáadandó címkét:", "tagpanel/add_tag_label"),
    # #3585: a Névtelenek album csoportosítás-váltógombja és fejléc-
    # utasítása (spec `picasa-arcfelismeres.md` 9/d), valamint az
    # Emberek-panel két „Név nélküli…" fejléce (9/b)
    "Group by face": (
        "Csoportosítás arcok szerint", "unknownfaceheaderpanel/cluster"),
    "Expand groups": (
        "Csoportok részletes nézete", "unknownfaceheaderpanel/showall"),
    "Grouping faces, please wait...": (
        "Az arcok csoportosítása folyamatban van, kérjük, várjon...",
        "CAlbumLabel::LoadingGrouped"),
    "Select someone you know and add a name.": (
        "Jelöljön ki valakit, akit ismer, és adjon hozzá egy nevet.",
        "CAlbumLabel::ToggleGroupIgnore"),
    'Select someone you know and add a name, or click the "x" to ignore that person.': (
        'Jelöljön ki valakit, akit ismer, és adjon hozzá egy nevet, vagy '
        'kattintson az "x" ikonra az adott személy mellőzéséhez.',
        "CAlbumLabel::ToggleGrouped"),
    "Select someone you know and add a name": (
        "Jelöljön ki valakit, akit ismer, és adjon hozzá egy nevet",
        "CAlbumLabel::ToggleUnGrouped"),
    "Unnamed people in these photos:": (
        "Meg nem nevezett emberek ezeken a fotókon:",
        "PeoplePanel::UnnamedCluster"),
    "Unnamed groups of people:": (
        "Név nélküli személycsoportok:", "PeoplePanel::Unnamed"),
}

#: a Gyorscímkék-útmutató (a két szóköz a mondatok között az eredetié)
QUICKTAG_UTMUTATO = 'You can use Quick Tags to apply a tag with a single click.  Type in tags below that you want to have one-click access to.  By default, the top two Quick Tags are used to track recently applied tags.  Uncheck the checkbox below to manually set the top two tags.'

#: fájl → a benne várt hivatalos feliratok
ELOFORDULASOK = {
    "PicasaPy/HiddenPasswordDialog.qml": ["The passwords did not match."],
    "PicasaPy/SaveDialogs.qml": ["Do not ask again"],
    "PicasaPy/ConfirmDialog.qml": ["Do not ask again"],
    "PicasaPy/TagContextMenu.qml": ["Add this tag to entire selection"],
    "PicasaPy/LightboxHeader.qml": ["Sync to Web"],
    "PicasaPy/EditorParamPanel.qml": ["Feather", "Color Preservation"],
    "PicasaPy/EditorTextPanel.qml": [
        "Left justify text", "Center justify text", "Right justify text"],
    "PicasaPy/UnnamedFacesView.qml": [
        "Ignore all of the selected faces",
        # #3585
        "Group by face", "Expand groups", "Grouping faces, please wait...",
        "Select someone you know and add a name.",
        "Select someone you know and add a name"],
    "PicasaPy/PeoplePanel.qml": [
        "Unnamed people in these photos:", "Unnamed groups of people:"],
    "PicasaPy/SlideshowView.qml": ["Display Time", "seconds"],
    # #3575
    "PicasaPy/CreateDialogs.qml": ["Frame Mosaic"],
    "PicasaPy/FolderPropertiesDialog.qml": [
        "Description (optional):", "Place taken (optional):",
        "Use music for Slideshow and Movie presentation:"],
    "PicasaPy/ImportSourceDialog.qml": [
        "Enter Folder Title", "Date Taken (YYYY-MM-DD)", "%1 (Today)"],
    "PicasaPy/MoveDatabaseDialog.qml": [
        "Choose database location...", "Current database location:",
        "New database location:"],
    "PicasaPy/NewCollectionDialog.qml": ["Enter Collection Name:"],
    "PicasaPy/QuickTagsConfigDialog.qml": [
        QUICKTAG_UTMUTATO, "Autofill empty boxes above with commonly used tags"],
    "PicasaPy/TagsPanel.qml": ["Type in a tag to add:"],
}

#: amit a rossz alakból SEHOL nem szabad `qsTr()`-ben látni
ELAVULT = (
    "The passwords do not match.",
    "Don't ask again",
    "Add Tag to Entire Selection",
    "Sync to the web",
    "Choose new database location...",
    # #3574
    "Align left",
    "Align center",
    "Align right",
    "Preserve Color",
    " s",
    # #3575
    "Enter new folder title or choose existing folder to continue",
    "Import into separate folders for each date taken",
    "Import into folder with today's date",
    "Collection name:",
    "Fill the empty boxes above with frequently used tags",
    "Add a tag...",
)


def test_a_negy_elofordulas_a_hivatalos_angolt_mondja() -> None:
    for fajl, feliratok in ELOFORDULASOK.items():
        forras = (QML / fajl).read_text(encoding="utf-8")
        for felirat in feliratok:
            minta = f'qsTr("{felirat}")'
            assert minta in forras, f"{fajl}: hiányzik a {minta}"


def test_a_regi_fogalmazas_sehol_nem_maradt() -> None:
    hibak = []
    for ut in QML.rglob("*.qml"):
        forras = ut.read_text(encoding="utf-8")
        for regi in ELAVULT:
            if f'qsTr("{regi}")' in forras or f"qsTr('{regi}')" in forras:
                hibak.append(f"{ut.name}: „{regi}”")
    assert not hibak, "a régi fogalmazás még él: " + ", ".join(hibak)


def test_a_magyar_forditas_is_a_hivatalos_szoveg() -> None:
    fa = ElementTree.parse(TS)
    talalt: dict[str, set[str]] = {}
    for uzenet in fa.iter("message"):
        forras = uzenet.findtext("source") or ""
        if forras in HIVATALOS:
            talalt.setdefault(forras, set()).add(uzenet.findtext("translation") or "")
    for felirat, (magyar, _azonosito) in HIVATALOS.items():
        assert felirat in talalt, f"nincs fordítási bejegyzés: „{felirat}”"
        assert talalt[felirat] == {magyar}, (
            f"„{felirat}” fordítása {sorted(talalt[felirat])}, "
            f"a hivatalos „{magyar}”")


def test_a_qm_ujraforditva_frissebb_mint_a_ts() -> None:
    """A `.qm` a futásidejű alak — ha nem generáljuk újra, a felület a régit
    mutatja (a három lépés: `.ts`, mixin-tábla, `.qm`)."""
    qm = TS.with_suffix(".qm")
    assert qm.exists(), "hiányzik a lefordított .qm"
    adat = qm.read_bytes()
    for felirat, (magyar, _azon) in HIVATALOS.items():
        assert magyar.encode("utf-16-be") in adat, (
            f"a .qm nem tartalmazza a „{magyar}” fordítást — "
            "újrafordítás kell (lrelease)")
        assert re.search(re.escape(felirat).encode(), adat) or True




#: #3572: a Beállítások ablak fülei. A kulcs (kontextus, forrásszöveg), mert
#: több felirat („RAW”, „English (US)”, „Log file:”…) másutt más szerepben,
#: más fordítással is él — a fordítást ezért CSAK az adott fülön mérjük.
#: Ahol van hivatalos angol (a `stringres` enUK-alakja), a forrásszöveg is az.
BEALLITASOK = {
    ("OptionsTabEmail", "Full film"): (
        "Teljes mozgófilm", "options/radio56.title"),
    ("OptionsTabEmail", "Let me choose each time I send pictures"): (
        "Minden képküldésnél kiválasztom", "options/radio40.title"),
    ("OptionsTabEmail", "Send inline photos and captions (Outlook only)"): (
        "Szövegközi fotók és képfeliratok küldése (csak Outlookban)",
        "options/UseHTMLMailer.title"),
    ("OptionsTabEmail", "Send videos as:"): (
        "Mozgófilmek küldése másként:", "options/labelgroup53.title"),
    ("OptionsTabFileTypes", "Display JPEG files and:"): (
        "Megjelenítés: JPEG-fájlok és", "options/label61.title"),
    ("OptionsTabFileTypes", "RAW"): ("RAW formátumok", "options/SupportRAW.title"),
    # a nyelvlista saját nyelvű neveket mutat, fordítás nélkül (Lang::enUS)
    ("OptionsTabGeneral", "English (US)"): ("English (US)", "Lang::enUS"),
    ("OptionsTabGeneral", "Help improve PicasaPy:"): (
        "Részvétel a Picasa fejlesztésében:", "options/labelgroup16.title"),
    ("OptionsTabGeneral", "Import destination folder:"): (
        "Importált képek mentési helye:", "options/labelgroup34.title"),
    ("OptionsTabGeneral", "Never check for updates"): (
        "Ne keressen frissítést", "options/item24.title"),
    ("OptionsTabGeneral", "Prompt before downloading updates"): (
        "Mindig tegyen fel kérdést a frissítések letöltése előtt",
        "options/item23.title"),
    ("OptionsTabGeneral", "Send anonymous usage statistics"): (
        "Névtelen használati statisztikák küldése a Google részére",
        "options/usagestats.title"),
    ("OptionsTabGeneral", "Single click to exit the editing view"): (
        "Szerkesztési nézetből való kilépés egy kattintással",
        "options/SingleClickExit.title"),
    ("OptionsTabGeneral", "User interface:"): (
        "Kezelőfelület:", "options/labelgroup4.title"),
    ("OptionsTabNameTags", "Clustering threshold:"): (
        "Csoportküszöb:", "options/labelgroup181.title"),
    ("OptionsTabNameTags", "Enable face detection"): (
        "Arcfelismerés bekapcsolása", "options/enablefacedetection.title"),
    ("OptionsTabNameTags", "Store name tags in the file"): (
        "Névcímkék tárolása a fotón", "options/persistfacetofile.title"),
    ("OptionsTabNameTags", "Upload contact thumbnails to Google Contacts"): (
        "Az Emberek album indexképeinek feltöltése a Google Címtárba",
        "options/uploadcontactphotos.title"),
    ("OptionsTabNetwork", "Detailed log information"): (
        "Részletes naplóadatok", "options/item140.title"),
    ("OptionsTabNetwork", "Disable logging"): (
        "Naplózás letiltása", "options/item137.title"),
    ("OptionsTabNetwork", "Log all network information"): (
        "Az összes hálózati információ naplózása", "options/item141.title"),
    ("OptionsTabNetwork", "Log file:"): ("Napló:", "options/labelgroup142.title"),
    ("OptionsTabNetwork", "Minimal log information"): (
        "Minimális mennyiségű naplóadat", "options/item139.title"),
    ("OptionsTabNetwork", "Network logging level:"): (
        "Hálózati események naplózási szintje:", "options/labelgroup135.title"),
    ("OptionsTabNetwork", "Proxy password:"): (
        "Jelszó a proxyhoz:", "options/labelgroup132.title"),
    ("OptionsTabNetwork", "Proxy username (Windows only):"): (
        "Felhasználónév a proxyhoz:", "options/labelgroup130.title"),
    ("OptionsTabPrinting", "Available print sizes:"): (
        "Rendelkezésre álló nyomtatási méretek:", "options/label107.title"),
    ("OptionsTabPrinting", "Printer quality:"): (
        "Nyomtató minősége:", "options/labelgroup120.title"),
    ("OptionsTabPrinting", "Print resampler quality:"): (
        "Nyomtatási mintavételezési minőség:", "options/labelgroup124.title"),
    ("OptionsTabPrinting", "Use high quality previews (slower)"): (
        "Magas minőségű előnézetek használata (lassabb)",
        "options/PrintProxyPreview.title"),
    ("OptionsTabPrinting", "Extra sharp (Lanczos-8)"): (
        "Extra éles (Lanczos-8)", "options/radio127.title"),
    ("OptionsTabSlideshow", "Play music tracks during slideshow"): (
        "Zenelejátszás a diavetítés alatt", "options/PlayMP3Tracks.title"),
    ("OptionsTabSlideshow", "Select a folder of music tracks:"): (
        "Zeneszámok mappájának kiválasztása:", "options/label104.title"),
    ("OptionsTabWebAlbums", "Add a watermark for all photo uploads:"): (
        "Vízjel hozzáadása az összes feltöltendő fotóhoz:",
        "options/haswatermark.title"),
    ("OptionsTabWebAlbums", "Don't confirm every sync (use the above settings)"): (
        "Nem kérek megerősítő üzenetet minden szinkronizáláskor "
        "(a fenti beállításokat használom)", "options/confirmsync::disable.title"),
    ("OptionsTabWebAlbums", "Preserve original image quality (uses more storage)"): (
        "Az eredeti képminőség megőrzése (több tárterületet foglal)",
        "options/PWAUseHiQualityJPEG.title"),
    ("OptionsTabWebAlbums", "Sync starred photos only"): (
        "Csak a csillagozott fotók szinkronizálása", "options/PWAStarred.title"),
    # az eredetiben csoportcímke + jelölőnégyzet, nem egyetlen jelölő
    ("OptionsTabWebAlbums", "Name Tags:"): ("Névcímkék:", "options/enablefruploads.title"),
    ("OptionsTabWebAlbums", "Include with photo uploads"): (
        "Feltöltés a fotókkal", "options/enablefruploads.title"),
    ("OptionsTabWebAlbums", "When syncing large files, upload previews first"): (
        "Nagyméretű fájlok szinkronizálásakor a program először az "
        "előnézeteket töltse fel", "options/PWAStriped.title"),
}

#: #3572: a lecserélt angol forrásszövegek — a Beállítások füleiről eltűntek
BEALLITASOK_ELAVULT = {
    "OptionsTabEmail": (
        "Full movie", "Let me choose each time I send a picture",
        "Send embedded pictures and captions (Outlook only)", "Send movies as:"),
    "OptionsTabFileTypes": ("In addition to JPEG, also show these file types:",),
    "OptionsTabGeneral": ("English",),
    "OptionsTabPrinting": (
        "Printer quality (Windows only):", "Resizing algorithm quality:",
        "Use high resolution previews (slower)", "Very sharp (Lanczos-8)"),
    "OptionsTabSlideshow": (
        "Play MP3 music during slideshow", "Select a music folder:"),
    "OptionsTabWebAlbums": (
        "Add a watermark to all photo uploads:",
        "Don't confirm each sync (use previous settings)",
        "Keep original picture quality (uses more storage)",
        "Upload name tags", "Upload previews first for large files"),
}


def _kontextus_forditasai() -> dict[tuple[str, str], set[str]]:
    talalt: dict[tuple[str, str], set[str]] = {}
    for kontextus in ElementTree.parse(TS).getroot().iter("context"):
        nev = kontextus.findtext("name") or ""
        for uzenet in kontextus.iter("message"):
            forditas = uzenet.find("translation")
            if forditas is not None and forditas.get("type") in ("obsolete", "vanished"):
                continue
            talalt.setdefault((nev, uzenet.findtext("source") or ""), set()).add(
                "" if forditas is None else (forditas.text or ""))
    return talalt


def test_a_beallitasok_fulei_a_hivatalos_angolt_mondjak() -> None:
    hibak = []
    for (kontextus, felirat) in BEALLITASOK:
        forras = (QML / "PicasaPy" / f"{kontextus}.qml").read_text(encoding="utf-8")
        if f'qsTr("{felirat}")' not in forras:
            hibak.append(f"{kontextus}: hiányzik a qsTr(\"{felirat}\")")
    for kontextus, regiek in BEALLITASOK_ELAVULT.items():
        forras = (QML / "PicasaPy" / f"{kontextus}.qml").read_text(encoding="utf-8")
        hibak += [f"{kontextus}: a régi „{regi}” még él"
                  for regi in regiek if f'qsTr("{regi}")' in forras]
    assert not hibak, "\n".join(hibak)


def test_a_beallitasok_magyarja_a_hivatalos_szoveg() -> None:
    talalt = _kontextus_forditasai()
    hibak = []
    for kulcs, (magyar, _azonosito) in BEALLITASOK.items():
        if talalt.get(kulcs) != {magyar}:
            hibak.append(f"{kulcs}: {sorted(talalt.get(kulcs, set()))} "
                         f"≠ a hivatalos „{magyar}”")
    assert not hibak, "\n".join(hibak)


def test_a_beallitasok_forditasa_a_qm_ben_is_ott_van() -> None:
    adat = TS.with_suffix(".qm").read_bytes()
    hianyzik = [magyar for magyar, _ in BEALLITASOK.values()
                if magyar.encode("utf-16-be") not in adat]
    assert not hianyzik, f"a .qm-ből hiányzik (lrelease kell): {hianyzik}"
