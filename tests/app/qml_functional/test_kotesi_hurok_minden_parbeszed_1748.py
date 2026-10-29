"""#1748 — kötési hurok MINDEN párbeszéd-tárolóban, Fusionnel.

A #1599 egyetlen tárolót (`ExportDialogs`) vizsgál. A forrás-szintű söprés
szerint 38 párbeszéd hordozza ugyanazt a mintát (`Dialog` belsejében szabad
szélességű `Text`), de a minta **önmagában nem hiba** — a #1599-nél is a
megnyitás + hosszú szöveg + Fusion együttese hozta elő a hurkot.

Ez az őr ezért **megméri**, nem feltételezi: EGY gyerekprocesszben felépíti a
projekt ÖSSZES párbeszéd-tárolóját, mindegyikben megnyit minden `message`
tulajdonságú párbeszédet hosszú szöveggel, és összegyűjti a hurkokat.

**Miért külön processz.** A `QT_QUICK_CONTROLS_STYLE`-t a Qt a
`QGuiApplication` létrehozásakor olvassa be; a tesztkészletben addigra már áll
az alkalmazás. A hurok viszont KIZÁRÓLAG Fusionnel jön elő — ezért maradt a
#1599-é hónapokig észrevétlen.

**A mérés eredménye (2026-09-03):** 48 tárolóból 48 felépült, 32 párbeszéd
nyílt meg, és a 38-as forrás-mintából **egyetlen** valódi hurok volt
(`SaveDialogs.qml` `saveResultDialog`) — ott a tördelő `Text` már rögzített
szélességű volt, de a `Dialog`-nak nem volt `implicitWidth`-e. Javítva.

⚠️ **A „nem épült fel" eset is bukás.** Egy tároló, amit a próba nem tud
példányosítani, NEM vizsgált tároló — némán kimaradna, és az őr zölden
hazudna. Ezért a próba a kötelező tulajdonságokat sorra kipróbálja, és ha
valamelyik tároló így sem áll fel, az eset elbukik.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

#: Az új, külön QML-típusok kötelező tulajdonságai. A régi tárolóknál
#: maradnak az általános próbaváltozatok; az új komponenseknél csak a saját
#: tulajdonságaikat adjuk át, különben a próba nem létező `panel`-t ír rájuk.
_KOTELEZO_VALTOZATOK = {
    "CollageCreateDialog": (
        "appWindow: ({ selectedIndexes: [] }); trayHasPictures: false; "
        "collageKinds: []; collageBorders: []; collageBorderCapable: []",
    ),
    "MovieMakerDialog": (
        "appWindow: ({}); movieDialogs: ({}); trayHasPictures: false",
    ),
    "MovieMakerActions": (
        "movieDialog: ({}); tabs: ({}); confirmDialog: ({}); previewTimer: ({})",
    ),
    "MovieMakerDialogs": ("movieDialog: ({})",),
    "MovieMakerFilmstrip": (
        "movieDialog: ({}); tabs: ({}); previewPanel: ({ x: 0, width: 0 })",
    ),
    "MovieMakerOptions": ("movieDialog: ({}); pagesWidth: 0",),
    "MovieMakerPreview": (
        "movieDialog: ({}); resizeTimer: ({}); "
        "moviePreviewMusicLoader: ({}); moviePreviewTransition: ({})",
    ),
    "MovieMakerPreviewLogic": (
        "movieDialog: ({}); tabs: ({}); previewComponent: ({}); previewTimer: ({}); "
        "transition: ({}); transitionFallbackTimer: ({}); itemsRefreshTimer: ({}); frameTimer: ({})",
    ),
    "MovieMakerPreviewRuntime": ("movieDialog: ({}); tabs: ({})",),
    "MovieMakerSlideLogic": ("movieDialog: ({}); tabs: ({})",),
    "MovieMakerTabs": ("movieDialog: ({}); options: ({})",),
    # #6216: a nyomtatási nézet és állapotobjektum kötelező gazdát kap.
    "PrintDialogContent": (
        "hostWindow: ({ quality: ({ ready: true, total: 0, small: 0 }), "
        "rows: [], copies: 1, keretMargo: 12, contactSheet: false, "
        "printCtl: null, reviewList: [], reviewOpen: false, printSize: '', "
        "printSizeIds: [], printSizeLabels: [], printSizeOptions: [], "
        "printSizePresetIds: [], orientation: '', fitMode: '', "
        "optimizedPrintMode: false, passport: false, contactColumns: 4, "
        "pdfSelected: true, pdfTarget: '', printerName: '', printerIndex: 0, "
        "printers: [], printDonePages: 0, printTotalPages: 0, "
        "printPageCount: 0, previewPage: 0, previewPageCount: 0, "
        "previewSource: '', lastError: '', lastResult: '', lastSkipped: [], "
        "papiradat: '', frissitsdAzElonezetet: function() {} }); "
        "hostWindowHelp: ({}); hostOptionsPanel: ({}); "
        "hostPdfTargetDialog: ({}); hostReviewPanel: ({ currentIndex: -1 })",
    ),
    "PrintDialogLogic": (
        "hostWindow: ({}); printController: null; "
        "settingsPanel: ({ sizeBox: ({}) }); "
        "reviewPanel: ({ currentIndex: -1 }); "
        "removeAllDialog: ({ open: function() {} }); optionsPanel: ({})",
    ),
    # #6225: az EditorPanel belső állapot- és blur-komponensei a gazdájukat
    # és a szükséges host objektumokat required property-ként kapják.
    "EditorPanelCropState": (
        "editorPanel: ({}); hostController: null; hostEditController: null",
    ),
    "EditorPanelEffectState": (
        "editorPanel: ({}); hostEditController: null",
    ),
    "EditorPanelFinetuneState": ("editorPanel: ({})",),
    "EditorPanelTextState": ("editorPanel: ({})",),
    "EditorPanelToolsState": ("editorPanel: ({})",),
    "EditorPanelBlurEffects": (
        "editorPanel: ({}); tabs: null; tabArea: null; undoRow: null",
    ),
    # #6136: a főablak jobb oldali fiókja kötelező gazda-tulajdonságokat kér
    "MainRightDrawer": (
        "hostWindow: ({}); hostController: null; hostToolbar: ({}); "
        "hostPhotoViewer: ({}); hostMainSplit: ({}); "
        "hostMainLibraryCanvas: ({ unnamedFacesView: ({}) }); hostMainDialogs: ({})",
    ),
    # #6136: a FolderPane főablakbeli bekötése önálló, kötelező gazda-propokat kér.
    "MainFolderPane": (
        "hostWindow: ({}); hostController: null; hostToolbar: ({}); "
        "hostBackupHost: ({}); hostFileOpsDialogs: ({}); "
        "hostCollectionPasswordDialog: ({}); hostFileOpsController: null; "
        "hostFaceScanController: null; hostFolderHierarchyController: null",
    ),
    # #6136: a hibasáv a főablak vezérlő-, párbeszéd- és időzítőobjektumait várja.
    "MainErrorBanner": (
        "hostController: ({}); hostTestLogDialog: ({}); hostBrokenPhotoDialog: ({}); "
        "hostBrokenPhotoBatchTimer: ({})",
    ),
    # #6136: a gyorsbillentyűk külön komponensbe kerültek; a 12 gazda-prop
    # közül azok kapnak minimális alakot, amelyek felépítéskor kiolvasódnak.
    "MainKeyboardShortcuts": (
        "hostWindow: ({}); hostController: null; "
        "hostDocumentTabStrip: ({ libraryActive: false, keyboardShortcutSequences: [] }); "
        "hostExportDialogs: ({}); hostFileOpsController: null; "
        "hostFileOpsDialogs: ({}); hostHelpDialog: ({}); "
        "hostPhotoViewer: ({ keyboardShortcutSequences: [] }); "
        "hostPicasaMenuBar: ({ "
        "keyboardShortcutGroupTitles: ({ file: '', edit: '', view: '', "
        "folder: '', picture: '', help: '' }), "
        "keyboardShortcutSequences: ({ file: [], view: [], folder: [] }), "
        "photoActionsEnabled: false }); "
        "hostSaveDialogs: ({}); hostSlideshow: ({ visible: false }); "
        "hostTrayBar: ({ keyboardShortcutSequences: [] })",
    ),
}
_ALTALANOS_VALTOZATOK = (
    "", "appWindow: null", "panel: null", "appWindow: null; panel: null"
)
#: A menüforrásokat nem példányosítjuk párbeszéd-tárolóként: két belső
#: menü csak kommentben említi a Dialog szót, és a modulon kívülről nem
#: érhető el közvetlen QML-típusként.
_NEM_PARBESZED_TAROLOK = frozenset({"PicasaFileMenu", "PicasaToolsMenu"})

_GYEREK = textwrap.dedent(
    '''
    import os, sys
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from pathlib import Path
    from PySide6.QtCore import QObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent, QQmlEngine
    from PySide6.QtQuick import QQuickItem  # a QQuickItem* konverterhez
    import picasapy.app

    VALTOZATOK = %(valtozatok)r
    ALTALANOS_VALTOZATOK = %(altalanos_valtozatok)r

    uzenetek = []
    qInstallMessageHandler(lambda t, ctx, msg: uzenetek.append(msg))
    app = QGuiApplication(sys.argv[:1])
    qml = Path(picasapy.app.__file__).parent / "qml"
    # A qmldir `internal` típusai a modulon kívülről nem példányosíthatók;
    # ezek egy-egy tároló részei, és a tárolójukkal együtt épülnek fel (#6083).
    belso = {
        sor.split()[1]
        for sor in (qml / "PicasaPy" / "qmldir").read_text(encoding="utf-8").splitlines()
        if sor.startswith("internal ")
    }
    nem_parbeszed_tarolok = set(%(kizaras)r) | belso
    motor = QQmlEngine()
    motor.addImportPath(str(qml))

    tarolok = sorted(
        p.stem for p in (qml / "PicasaPy").glob("*.qml")
        if ("Dialog" in p.read_text(encoding="utf-8") or p.stem in VALTOZATOK)
        and p.stem not in nem_parbeszed_tarolok
    )
    hosszu = ("Unable to save all files due to a disk error. "
              "IMG_20260827_183045_nyaralas_horvatorszag.jpg — "
              "error(28): No space left on device") * 3

    megnyitott = 0
    for nev in tarolok:
        uzenetek.clear()
        ablak = None
        hiba = ""
        for extra in VALTOZATOK.get(nev, ALTALANOS_VALTOZATOK):
            k = QQmlComponent(motor)
            k.setData((
                "import QtQuick\\n"
                "import QtQuick.Controls\\n"
                "import PicasaPy 1.0\\n"
                "ApplicationWindow { width: 900; height: 600; visible: true\\n"
                "  " + nev + " { objectName: \\"proba\\"; " + extra + " } }"
            ).encode(), QUrl())
            ablak = k.create()
            if ablak is not None:
                break
            hiba = k.errorString().replace(chr(10), " ")[:160]
        if ablak is None:
            print("NEM-EPULT-FEL:", nev, "::", hiba)
            continue
        QQmlEngine.setObjectOwnership(ablak, QQmlEngine.ObjectOwnership.CppOwnership)
        app.processEvents()
        for gy in ablak.findChildren(QObject):
            mo = gy.metaObject()
            if not any(mo.property(i).name() == "message" for i in range(mo.propertyCount())):
                continue
            gy.setProperty("message", hosszu)
            gy.setProperty("visible", True)
            app.processEvents()
            megnyitott += 1
            gy.setProperty("visible", False)
            app.processEvents()
        for m in uzenetek:
            if "Binding loop" in m:
                print("HUROK:", nev, "::", m.replace(chr(10), " | "))
        ablak.deleteLater()
        app.processEvents()

    print("TAROLOK", len(tarolok))
    print("MEGNYITOTT", megnyitott)
    print("STILUS", os.environ.get("QT_QUICK_CONTROLS_STYLE"))
    print("VEGE")
    '''
) % {
    "valtozatok": _KOTELEZO_VALTOZATOK,
    "altalanos_valtozatok": _ALTALANOS_VALTOZATOK,
    "kizaras": tuple(_NEM_PARBESZED_TAROLOK),
}


@pytest.fixture(scope="module")
def gyerek_kimenet(tmp_path_factory):
    gyoker = Path(__file__).resolve().parents[3]
    szkript = tmp_path_factory.mktemp("hurok1748") / "minden_parbeszed.py"
    szkript.write_text(_GYEREK, encoding="utf-8")

    kornyezet = dict(os.environ)
    kornyezet["QT_QUICK_CONTROLS_STYLE"] = "Fusion"
    kornyezet["QT_QPA_PLATFORM"] = "offscreen"
    kornyezet["PYTHONPATH"] = os.pathsep.join(
        [str(gyoker / "src"), kornyezet.get("PYTHONPATH", "")]
    )
    eredmeny = subprocess.run(
        [sys.executable, str(szkript)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        cwd=str(gyoker),
        env=kornyezet,
    )
    assert eredmeny.returncode == 0, (
        f"a Fusion-próba {eredmeny.returncode} kóddal állt le\n"
        f"{eredmeny.stdout[-2000:]}\n{eredmeny.stderr[-2000:]}"
    )
    return eredmeny.stdout


def _szam(kimenet: str, cimke: str) -> int:
    for sor in kimenet.splitlines():
        if sor.startswith(cimke + " "):
            return int(sor.split()[1])
    raise AssertionError(f"hiányzó „{cimke}” sor:\n{kimenet[-1500:]}")


class TestMindenParbeszedFusionnel:
    def test_a_proba_tenyleg_lefutott_fusionnel(self, gyerek_kimenet):
        """Pozitív kontroll: üres kimenetre minden állítás zölden hazudna."""
        assert "VEGE" in gyerek_kimenet, gyerek_kimenet[-1500:]
        assert "STILUS Fusion" in gyerek_kimenet, (
            "a gyerekprocessz nem Fusion stílussal futott — a hurok ezzel a "
            "próbával nem is jönne elő"
        )

    def test_MINDEN_tarolo_felepult(self, gyerek_kimenet):
        """A nem példányosítható tároló NEM vizsgált tároló — némán kimaradna."""
        kimaradt = [
            sor for sor in gyerek_kimenet.splitlines()
            if sor.startswith("NEM-EPULT-FEL:")
        ]
        assert kimaradt == [], (
            "ezek a párbeszéd-tárolók nem épültek fel, tehát NEM lettek "
            "megvizsgálva. Vedd fel a hiányzó kötelező tulajdonságot a "
            "`_KOTELEZO_VALTOZATOK`-ba:\n" + "\n".join(kimaradt)
        )

    def test_a_proba_erdemi_mennyisegu_parbeszedet_nyitott(self, gyerek_kimenet):
        """A mérés 2026-09-03-án 48 tárolót és 32 párbeszédet ért el. Ha ez
        érdemben CSÖKKEN, a próba elveszítette a fogát — akkor is, ha zöld."""
        assert _szam(gyerek_kimenet, "TAROLOK") >= 45
        assert _szam(gyerek_kimenet, "MEGNYITOTT") >= 30

    def test_nincs_kotesi_hurok(self, gyerek_kimenet):
        hurkok = [
            sor for sor in gyerek_kimenet.splitlines() if sor.startswith("HUROK:")
        ]
        assert hurkok == [], (
            "kötési hurok Fusion stílussal — a `Dialog` szélessége "
            "kiszámíthatatlan lesz. A #1599/#1748 mintája: a tördelő `Text`-nek "
            "rögzített `width`, a `Dialog`-nak rögzített `implicitWidth` "
            "(`<szélesség> + leftPadding + rightPadding`).\n" + "\n".join(hurkok)
        )
