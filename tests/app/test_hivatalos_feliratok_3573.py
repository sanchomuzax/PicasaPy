"""#3573 — 25 megerősítő/figyelmeztető üzenet a HIVATALOS Picasa-szöveget
mondja (#2921 lelete, `docs/specs/ui-tobblet-besorolas.tsv`, `kategoria
= elteres`).

A `test_hivatalos_feliratok_3358.py` mintáját követi, de nem oda kerül:
azok a sorok rövid, EGY darabban írt `qsTr("...")` hívások, itt viszont a
legtöbb üzenet több `qsTr("a" + "b" + "c")` darabból áll össze (Main.qml és
a legtöbb párbeszéd-fájl konvenciója) — a `qsTr("{felirat}")` szó szerinti
keresés ezekre nem alkalmazható. Ehelyett a `.ts`-t nézzük, és a LEFORDÍTOTT
`.qm`-et `QTranslator`-ral kérdezzük meg: az dönti el, mit LÁT a
felhasználó. Hogy a QML-ben összefűzött forrásszöveg betűre egyezik-e a
`.ts` kulcsával, azt a `test_i18n_completeness.py` méri (a valódi
`lupdate`-tel).

A hivatalos szöveg forrása a `stringres` szövegtár (`CCollageUI::ConfirmMsg`
stb.). Az eredeti a sortörést `\\n`-nel (vagy `\\r\\n`-nel) írja, az
idézőjel ASCII `"` — ezt mindkét nyelven megtartjuk.

Amit ez az őr NEM mér: hogy az üzenet a képernyőn jól tördelődik-e.
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
    # a képnévvel és a hivatalos sortörésekkel — a második sor végén az
    # eredetiben is áll egy szóköz a sortörés előtt
    "Red eye fixes have been applied to %1.\nIf you remove all edits, your "
    "red eye fixes cannot be recovered with redo. \nAre you sure you want "
    "to remove the fixes forever?": (
        "A(z) %1 képen vörösszemjavítások történtek.\nHa eltávolít minden "
        "szerkesztést, a vörösszemjavításokat később nem lehet újra "
        "alkalmazni. \nBiztos, hogy végleg eltávolítja a javításokat?",
        "IDS_CONFIRM_REDEYE_REVERT"),
    # a hivatalos angolban két szóköz áll a mondatok között
    "This will remove all edits you have made to ALL of the selected "
    "pictures.  Do you want to continue?": (
        "Ezzel a művelettel eltávolít minden módosítást, amelyet az ÖSSZES "
        "kijelölt képre alkalmazott. Folytatja?",
        "IDS_CONFIRMREVERT_MULTIPLE"),
    "This will remove all edits you have made to the current picture.  Do "
    "you want to continue?": (
        "Ezzel a művelettel eltávolít minden módosítást, amelyet eddig az "
        "aktuális képre alkalmazott. Folytatja?",
        "IDS_CONFIRMREVERT"),
    # az eredeti KÉT erőforrásból rakja össze, közéjük a fájllistát
    "Picasa had a problem loading this file(s)\n": (
        "A Picasa problémába ütközött a fájl(ok) betöltése során\n",
        "CThumbUI::GetBadImages"),
    "\nWould you like to hide the files on disk?": (
        "\nEl szeretné rejteni a lemezen található fájlokat?",
        "CThumbUI::GetBadImages2"),
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
    "Redeye fixes cannot be recovered with redo.\nAre you sure you want to "
    "undo?": (
        "A vörösszemjavítások nem állíthatók helyre ismételt "
        "alkalmazással.\nBiztosan visszavonja a műveletet?",
        "IDS_CONFIRM_UNDO_REDEYE"),
    "Retouch fixes cannot be recovered with redo.\nAre you sure you want "
    "to undo?": (
        "A retusálási javítások nem állíthatók helyre ismételt "
        "alkalmazással.\nBiztosan visszavonja a műveletet?",
        "IDS_CONFIRM_UNDO_RETOUCH"),
    # a hivatalos sorrend: előbb a felszólítás, új sorban a darabszám
    "Please review before printing.\n%1 small %2 found.": (
        "Nézze át nyomtatás előtt.\n%1 kis %2 van.", "ThumbUIPrint::ReviewPrompt"),
    "This cannot be undone and all changes will be lost.": (
        "Ez a művelet nem vonható vissza, és az összes módosítás elvész.",
        "CThumbUI::FileRevert::message2"),
    "To undo the last save and keep edits click 'Undo Save'.": (
        "Az utolsó mentés visszavonásához és a szerkesztések "
        'megtartásához kattintson a "Mentés visszavonása" gombra.',
        "CThumbUI::FileRevert::message1undo"),
    "Undo Save": ("Mentés visszavonása", "CThumbUI::FileRevert::undosave"),
    "Backup Complete": ("A mentés elkészült", "il_BurnPanel::BackupCopy::3"),
    'Are you sure you want to delete the backup set "%1"?': (
        'Biztosan törli a(z) "%1" mentési készletet?', "il_NewBkDialog_delete"),
    "You have been editing a previously created collage.\n\nWould you like "
    "to replace the existing collage or create an entirely new one?  (Note: "
    'All collages are saved in the "Collages" album).\n\nPress Cancel to '
    "continue editing the collage without saving.": (
        "Eddig egy korábban készült kollázst szerkesztett.\n\nLecseréli a "
        "meglévő kollázst, vagy teljesen újat hoz létre? (Megjegyzés: a "
        'program az összes kollázst a "Kollázsok" albumban tárolja.)\n\nA '
        "Mégse gombra kattintva mentés nélkül folytathatja a kollázs "
        "szerkesztését.",
        "CCollageUI::ConfirmMsg"),
}

#: (kontextus, felirat) → (hivatalos magyar, azonosító) — azok a rövid
#: szavak és a nyomtatási minőségsor szomszédjai, amelyek más kontextusban
#: mást is jelenthetnek, ezért csak a saját kontextusukban kötjük meg őket
KONTEXTUSOS = {
    ("PrintDialog", "picture"): ("kép", "ThumbUIPrint::picture"),
    ("PrintDialog", "pictures"): ("kép", "ThumbUIPrint::pictures"),
    ("PrintDialog", "Smallest picture: %1 pixels/inch."): (
        "Legkisebb kép: %1 képpont/hüvelyk", "ThumbUIPrint::Smallest"),
    ("PrintDialog", "You are ready to print."): (
        "Készen áll a nyomtatásra.", "ThumbUIPrint::ReadyPrompt"),
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
    # a #3677 első változata: képnév és sortörés nélkül
    "<translation>Vörösszemjavítások történtek.",
    "Ezzel az ÖSSZES kijelölt képen eltávolít minden szerkesztést.",
    "Ezzel a jelenlegi képen eltávolít minden szerkesztést.",
    "A Picasa nem tudta betölteni ezt/ezeket a fájlt/fájlokat. Szeretné "
    "elrejteni a fájlokat a lemezen?",
    "betöltése során. El szeretné rejteni",
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
    "alkalmazással. Biztosan visszavonja a műveletet?",
    "Nyomtatás előtt ellenőrizze őket.",
    "kis méretű kép található",
    "Ez nem vonható vissza, és minden változtatás elvész.",
    "Az utolsó mentés visszavonásához a szerkesztések megtartásával "
    "kattintson az „Utolsó mentés visszavonása” gombra.",
    # a hivatalos szöveg ASCII idézőjelet használ, nem „…”-t
    "kattintson a „Mentés visszavonása” gombra.",
    "Biztosan törli a(z) „%1” mentési készletet?",
    "Törlöd ezt a mentés-készletet? Az elmentett fájlok a helyükön "
    "maradnak.",
    # a kollázs-csere régi, a hivatalos CÍMET üzenetként mondó törzse
    "<source>Would you like to replace the existing one, or create a new one?",
)


def _uzenetek() -> list[tuple[str, str, str]]:
    """A `.ts` összes üzenete: (kontextus, forrás, fordítás)."""
    fa = ElementTree.parse(TS)
    sorok = []
    for kontextus in fa.iter("context"):
        nev = kontextus.findtext("name") or ""
        for uzenet in kontextus.iter("message"):
            sorok.append((nev, uzenet.findtext("source") or "",
                          uzenet.findtext("translation") or ""))
    return sorok


def test_a_magyar_forditas_a_hivatalos_szoveg() -> None:
    talalt: dict[str, set[str]] = {}
    for _kontextus, forras, forditas in _uzenetek():
        if forras in HIVATALOS:
            talalt.setdefault(forras, set()).add(forditas)
    for felirat, (magyar, _azonosito) in HIVATALOS.items():
        assert felirat in talalt, f"nincs fordítási bejegyzés: „{felirat}”"
        assert talalt[felirat] == {magyar}, (
            f"„{felirat}” fordítása {sorted(talalt[felirat])}, "
            f"a hivatalos „{magyar}”")


def test_a_kontextusos_forditas_a_hivatalos_szoveg() -> None:
    uzenetek = {(k, f): t for k, f, t in _uzenetek()}
    for kulcs, (magyar, _azonosito) in KONTEXTUSOS.items():
        assert kulcs in uzenetek, f"nincs fordítási bejegyzés: {kulcs}"
        assert uzenetek[kulcs] == magyar, (
            f"{kulcs} fordítása „{uzenetek[kulcs]}”, a hivatalos „{magyar}”")


def test_a_regi_forditas_sehol_nem_maradt() -> None:
    ts_szoveg = TS.read_text(encoding="utf-8")
    hibak = [regi for regi in ELAVULT_FORDITAS if regi in ts_szoveg]
    assert not hibak, "a régi fordítás még él a .ts-ben: " + "; ".join(
        f"„{h}”" for h in hibak)


def test_a_leforditott_qm_a_hivatalos_szoveget_adja(qt_app) -> None:
    """Az ÉLES `.qm`-et kérdezzük: amit a `QTranslator` a futó alkalmazásban
    visszaad, azt látja a felhasználó — a `.ts` önmagában nem elég, ha az
    újrafordítás (`lrelease`) elmaradt."""
    from PySide6.QtCore import QTranslator

    fordito = QTranslator()
    assert fordito.load("picasapy_hu", str(TS.parent)), (
        "a picasapy_hu.qm nem tölthető be")
    kontextusok: dict[str, set[str]] = {}
    for kontextus, forras, _forditas in _uzenetek():
        kontextusok.setdefault(forras, set()).add(kontextus)
    vart = {
        **{(k, f): m for f, (m, _a) in HIVATALOS.items()
           for k in kontextusok.get(f, ())},
        **{kulcs: m for kulcs, (m, _a) in KONTEXTUSOS.items()},
    }
    assert vart
    hibak = [
        (kontextus, forras, fordito.translate(kontextus, forras), magyar)
        for (kontextus, forras), magyar in vart.items()
        if fordito.translate(kontextus, forras) != magyar
    ]
    assert not hibak, "a .qm nem a hivatalos szöveget adja — lrelease kell: " + (
        "; ".join(f"{k}/„{f}” → „{t}” (várt: „{m}”)" for k, f, t, m in hibak))


class TestQmlOldal:
    """Ahol a hivatalos alakhoz a QML-nek is változnia kellett (név, lista,
    sorrend) — ezt a `.ts` nem mutatja meg."""

    def test_a_nyomtatasi_sor_a_hivatalos_sorrendet_koveti(self) -> None:
        forras = (QML / "PicasaPy" / "PrintDialog.qml").read_text(encoding="utf-8")
        assert 'qsTr("Please review before printing.\\n%1 small %2 found.")' in forras
        assert 'qsTr("picture")' in forras and 'qsTr("pictures")' in forras
        assert "small picture found." not in forras, (
            "a régi, darabszámmal kezdődő mondat még él")

    def test_a_vorosszem_figyelmeztetes_a_kepnevet_mondja(self) -> None:
        forras = (QML / "Main.qml").read_text(encoding="utf-8")
        assert "controller.redeyeNamesInSelection(" in forras
        assert '"Red eye fixes have been applied to %1.\\n"' in forras

    def test_a_serult_fajl_uzenet_a_fajllistat_is_mondja(self) -> None:
        forras = (QML / "Main.qml").read_text(encoding="utf-8")
        assert 'qsTr("Picasa had a problem loading this file(s)\\n")' in forras
        assert 'qsTr("\\nWould you like to hide the files on disk?")' in forras
        assert "pendingNames" in forras

    def test_a_kollazs_csere_a_hivatalos_uzenetet_mondja(self) -> None:
        forras = (QML / "PicasaPy" / "CollageDialogs.qml").read_text(encoding="utf-8")
        assert '"You have been editing a previously created collage.\\n\\n"' in forras
        assert "Would you like to replace the existing one, or " not in forras


class TestBackupCloseMessage:
    """A mentés-készlet törlésének és a záró üzenetnek a QML-oldali
    változása: itt a `qsTr()` szó szerinti keresése is működik, mert a
    két hívás EGY darabban van írva."""

    _BACKUP_QML = QML / "PicasaPy" / "BackupHost.qml"

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
