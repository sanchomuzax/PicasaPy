"""#3573 — 25 megerősítő/figyelmeztető üzenet a HIVATALOS Picasa-szöveget
mondja (#2921 lelete, `docs/specs/ui-tobblet-besorolas.tsv`, `kategoria
= elteres`).

A `test_hivatalos_feliratok_3358.py` mintáját követi, de nem oda kerül:
azok a sorok rövid, EGY darabban írt `qsTr("...")` hívások, itt viszont a
legtöbb üzenet több `qsTr("a" + "b" + "c")` darabból áll össze (Main.qml és
a legtöbb párbeszéd-fájl konvenciója) — a `qsTr("{felirat}")` szó szerinti
keresés ezekre nem alkalmazható. Ehelyett a `.ts`-t nézzük: az dönti el,
mit LÁT a felhasználó, a QML-oldali összefűzés helyességét pedig a
meglévő funkcionális tesztek (pl. `test_qml_fileops_export.py`) fedik.

Egy sor — a CollageDialogs.qml „Would you like to replace the existing
one…" — NEM szerepel itt: a jegy „mi tér el" oszlopa a hivatalos magyar
szöveget „…"-tel rövidítve idézi, a teljes betűre pontos fordítás sehol
nincs leírva (sem a jegyben, sem a `docs/specs/`-ben) — kitalálni ide
tilos, ezért ez a sor változatlan maradt (ld. a jegy kommentjét).
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

QML = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "qml"
TS = QML.parent / "i18n" / "picasapy_hu.ts"

#: felirat → (hivatalos magyar, a `stringres` azonosítója)
HIVATALOS = {
    "Want to Cancel?": ("Kilép?", "IBackgroundNotify::canceltitle"),
    "Do you want to cancel this operation?": (
        "Megszakítja ezt a műveletet?", "IBackgroundNotify::cancel"),
    "This will create an album with more than 1000 images.  Do you want to continue?": (
        "Ezzel a művelettel létrehoz egy több mint 1000 képből álló albumot. Folytatja?",
        "CThumbUI::SaveSearchBig"),
    "WARNING! This will DELETE all people albums, and move all the faces to "
    "the unnamed album. This can REMOVE name tags on synced web albums also. "
    "Do you want to do this?": (
        "FIGYELMEZTETÉS! Ez a művelet TÖRLI az összes személyi albumot, és a "
        "Név nélküliek albumba helyezi át az arcokat. A művelet a "
        "szinkronizált webalbumokból is ELTÁVOLÍTHATJA a névcímkéket. Ezt "
        "szeretné tenni?",
        "CThumbUI::ResetAllFaces"),
    "Red eye fixes have been applied. If you remove all edits, your red eye "
    "fixes cannot be recovered with redo. Are you sure you want to remove "
    "the fixes forever?": (
        "Vörösszemjavítások történtek. Ha eltávolít minden szerkesztést, a "
        "vörösszemjavításokat később nem lehet újra alkalmazni. Biztos, "
        "hogy végleg eltávolítja a javításokat?",
        "IDS_CONFIRM_REDEYE_REVERT"),
    "This will remove all edits you have made to ALL of the selected "
    "pictures. Do you want to continue?": (
        "Ezzel a művelettel eltávolít minden módosítást, amelyet az ÖSSZES "
        "kijelölt képre alkalmazott. Folytatja?",
        "IDS_CONFIRMREVERT_MULTIPLE"),
    "This will remove all edits you have made to the current picture. Do "
    "you want to continue?": (
        "Ezzel a művelettel eltávolít minden módosítást, amelyet eddig az "
        "aktuális képre alkalmazott. Folytatja?",
        "IDS_CONFIRMREVERT"),
    "Picasa had a problem loading this file(s). Would you like to hide the "
    "files on disk?": (
        "A Picasa problémába ütközött a fájl(ok) betöltése során. El "
        "szeretné rejteni a lemezen található fájlokat?",
        "CThumbUI::GetBadImages"),
    "Updating similarity database (will be fast next time)": (
        "Hasonlósági adatbázis frissítése (legközelebb gyors lesz)",
        "CSimSearch::updating"),
    "PicasaPy is compacting its database to save disk space. This may take "
    "several minutes.": (
        "A PicasaPy tömöríti az adatbázisát, hogy takarékoskodjon a "
        "lemezterülettel. Ez percekig is tarthat.",
        "compacting/label5.title"),
    "This file is read only. In order to edit this file, Picasa needs to "
    "copy the file's folder. Would you like to make a copy now?": (
        "A fájl írásvédett; szerkesztéséhez a Picasának másolatot kell "
        "készítenie a fájl mappájáról. Szeretne most másolatot készíteni?",
        "CThumbUI::ReadOnlyPrompt"),
    "Remember this setting, don't display this dialog again.": (
        "Jegyezze meg ezt a beállítást, ne jelenítse meg a párbeszédpanelt "
        "újra.",
        "choose_mail/remember"),
    "Include in filename:": ("Befoglalás a fájlnévbe:", "rename/labelgroup8.title"),
    "Please enter a new name for these files:": (
        "Kérjük, adjon új nevet ezeknek a fájloknak:", "rename/label5.title"),
    "This file cannot be moved to the Trash and will be deleted "
    "immediately. Are you sure you want to continue?": (
        "A fájl nem helyezhető át a Kukába, a program azonnal törölni "
        "fogja. Biztosan folytatja a műveletet?",
        "CThumbUI::ConfirmImmediateDeletion::Message"),
    "If you remove a watched folder, new items that you add to that folder "
    "on disk will not be automatically added to Picasa. Are you sure you "
    "want to do this?": (
        "Ha egy figyelt mappát eltávolít, a lemezen oda mentett új "
        "fájlokat a Picasa nem veszi fel automatikusan. Biztosan ezt "
        "szeretné?",
        "IDS_HOTFOLDER_CONFIRM"),
    "Watching an entire drive can slow down the system. It would be "
    "better to select several sub-folders. Are you sure you want to do "
    "this?": (
        "Egy teljes meghajtó figyelése lelassíthatja a rendszert. Jobb "
        "lenne több almappát kiválasztani. Biztosan ezt kívánja tenni?",
        "IDS_ROOT_WATCH_WARNING"),
    "Redeye fixes cannot be recovered with redo. Are you sure you want to "
    "undo?": (
        "A vörösszemjavítások nem állíthatók helyre ismételt "
        "alkalmazással. Biztosan visszavonja a műveletet?",
        "IDS_CONFIRM_UNDO_REDEYE"),
    "Retouch fixes cannot be recovered with redo. Are you sure you want "
    "to undo?": (
        "A retusálási javítások nem állíthatók helyre ismételt "
        "alkalmazással. Biztosan visszavonja a műveletet?",
        "IDS_CONFIRM_UNDO_RETOUCH"),
    "Please review before printing.": (
        "Nézze át nyomtatás előtt.", "ThumbUIPrint::ReviewPrompt"),
    "This cannot be undone and all changes will be lost.": (
        "Ez a művelet nem vonható vissza, és az összes módosítás elvész.",
        "CThumbUI::FileRevert::message2"),
    "To undo the last save and keep edits click 'Undo Save'.": (
        "Az utolsó mentés visszavonásához és a szerkesztések "
        "megtartásához kattintson a „Mentés visszavonása” gombra.",
        "CThumbUI::FileRevert::message1undo"),
    "Undo Save": ("Mentés visszavonása", "CThumbUI::FileRevert::undosave"),
    "Backup Complete": ("A mentés elkészült", "il_BurnPanel::BackupCopy::3"),
}

#: amit a rossz alakból SEHOL nem szabad `<translation>`-ben látni — a
#: `.ts`-t nézzük, mert a régi angol `qsTr()`-forrás több sornál már
#: eltűnt (megváltozott az összefűzött darabokból), a régi MAGYAR fordítás
#: viszont könnyen visszamaradhatna egy el nem ért ágon
ELAVULT_FORDITAS = (
    # "A háttérművelet leállítása" NEM szerepel itt: az ActivityBadge.qml
    # egy MÁSIK, önálló felirata is pont ezt mondja (nem #3573 tárgya) —
    # csak a Main.qml `activityCancelConfirm` címét cseréltük „Kilép?”-re.
    "Leállítja a háttérben futó műveletet?",
    "Ez több mint 1000 képet tartalmazó albumot hoz létre.  Folytatja?",
    "FIGYELMEZTETÉS! Ez a művelet minden arcot visszahelyez a Névtelenek "
    "albumba, és törli az arc-csoportokat. A fotókba írt névcímkékhez NEM "
    "nyúl. Ezt szeretné tenni?",
    "A képen vörösszem-javítás van. Ha eltávolítja az összes szerkesztést, "
    "a vörösszem-javítás nem állítható vissza.",
    "Ezzel az ÖSSZES kijelölt képen eltávolít minden szerkesztést.",
    "Ezzel a jelenlegi képen eltávolít minden szerkesztést.",
    "A Picasa nem tudta betölteni ezt/ezeket a fájlt/fájlokat. Szeretné "
    "elrejteni a fájlokat a lemezen?",
    "A hasonlósági adatbázis épül (legközelebb gyors lesz)",
    "A PicasaPy tömöríti az adatbázisát, hogy lemezhelyet szabadítson fel. "
    "Ez több percig is eltarthat.",
    "Ez a fájl csak olvasható. A szerkesztéshez a Picasának le kellene "
    "másolnia a fájl mappáját. Szeretné, ha most készítenénk egy "
    "másolatot?",
    "Jegyezze meg ezt a beállítást, és ne kérdezze meg újra",
    "A fájlnévben szerepeljen:",
    "Adjon új nevet ezeknek a fájloknak:",
    "Ez a fájl nem helyezhető át a Lomtárba, ezért azonnal, véglegesen "
    "törlődik. Ez nem vonható vissza.",
    "Ha eltávolítja ezt a mappát, a lemezen később bele tett új képek nem "
    "kerülnek automatikusan a könyvtárba.",
    "Egy teljes meghajtó figyelése lelassíthatja a rendszert. Érdemesebb "
    "néhány almappát kiválasztani.",
    "A vörösszem-javítás az Újra paranccsal nem állítható vissza. "
    "Biztosan visszavonja?",
    "A retusálás az Újra paranccsal nem állítható vissza. Biztosan "
    "visszavonja?",
    "Nyomtatás előtt ellenőrizze őket.",
    "Ez nem vonható vissza, és minden változtatás elvész.",
    "Az utolsó mentés visszavonásához a szerkesztések megtartásával "
    "kattintson az „Utolsó mentés visszavonása” gombra.",
    "Törlöd ezt a mentés-készletet? Az elmentett fájlok a helyükön "
    "maradnak.",
)


def test_a_magyar_forditas_a_hivatalos_szoveg() -> None:
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


def test_a_regi_forditas_sehol_nem_maradt() -> None:
    ts_szoveg = TS.read_text(encoding="utf-8")
    hibak = [regi for regi in ELAVULT_FORDITAS if regi in ts_szoveg]
    assert not hibak, "a régi fordítás még él a .ts-ben: " + "; ".join(
        f"„{h}”" for h in hibak)


def test_a_qm_ujraforditva_frissebb_mint_a_ts() -> None:
    qm = TS.with_suffix(".qm")
    assert qm.exists(), "hiányzik a lefordított .qm"
    adat = qm.read_bytes()
    for _felirat, (magyar, _azon) in HIVATALOS.items():
        assert magyar.encode("utf-16-be") in adat, (
            f"a .qm nem tartalmazza a „{magyar}” fordítást — "
            "újrafordítás kell (lrelease)")


class TestBackupCloseMessage:
    """A mentés-készlet törlésének és a záró üzenetnek a QML-oldali
    változása: itt a `qsTr()` szó szerinti keresése is működik, mert a
    két hívás EGY darabban van írva."""

    _BACKUP_QML = QML / "PicasaPy" / "BackupDialog.qml"

    def test_a_backup_complete_a_zaro_uzenet(self) -> None:
        forras = self._BACKUP_QML.read_text(encoding="utf-8")
        assert forras.count('qsTr("Backup Complete")') >= 3, (
            "az eredeti EGYETLEN záró üzenetet ismer — a „nincs mit "
            "másolni” ágnak is „Backup Complete”-et kell mutatnia (#3573)")

    def test_a_delete_set_a_keszlet_nevet_idezi(self) -> None:
        forras = self._BACKUP_QML.read_text(encoding="utf-8")
        assert (
            'qsTr("Are you sure you want to delete the backup set \\"%1\\"?")'
            in forras
        ), "a törlés-megerősítés nem a hivatalos, névvel ellátott szöveget mondja (#3573)"
