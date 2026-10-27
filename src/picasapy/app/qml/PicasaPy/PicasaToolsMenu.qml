import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

PicasaMenu {
    property var bar: null
    readonly property var controllerRef:
        (typeof controller !== "undefined" && controller)
            ? controller : null
    objectName: "menuTools"
    title: qsTr("&Tools")
    MenuItem {
        objectName: "menuToolsFolderManager"
        text: qsTr("&Folder Manager...")
        //: #1768: ugyanaz a parancs (`0x9caa`), ugyanaz a kapu — a
        //: két belépési pont nem viselkedhet másképp.
        enabled: !bar.editorActive
        onTriggered: bar.folderManagerRequested()
    }
    // hiányzott (#324 audit) — az auditban jelzett screenshot-időpontban
    // az eredetiben is inaktív volt
    PicasaMenuItem { text: qsTr("&Upload Manager..."); placeholder: false; retired: true }  // #638
    PicasaMenuItem {
        objectName: "menuToolsPeopleManager"
        text: qsTr("People Manager...")
        placeholder: false
        onTriggered: bar.peopleManagerRequested()
    }
    MenuSeparator {}
    // #2142: a duplikátum-kereső a KÍSÉRLETI almenübe költözött (az
    // eredetiben ott a 2. tétel, `eMenuTools::ID_DUPES`) — ld. lent.
    //
    // ⚠️ #2142 — TUDATOS ELTÉRÉS: az arckeresésnek az EREDETIBEN NINCS
    // menüparancsa. A „Find Faces" felirat a teljes szövegtárban nem
    // szerepel; a #1794 kimérte az Eszközök menü teljes szerkezetét, és
    // ilyen tétel nincs benne. Mi mégis megtartjuk, a #1473 indoklása
    // szerint: ugyanaz a fajta munka, mint a duplikátum-keresés — az
    // egész könyvtárat végigolvasó, megszakítható keresés saját
    // ablakkal —, és a felhasználónak kell egy belépési pont hozzá.
    // Ez tehát nem hiány, hanem a mi döntésünk.
    //
    // #1473: a tétel MINDIG él — ha
    // ugyanaz a fajta munka: az egész könyvtárat végigolvasó, hosszú,
    // megszakítható keresés saját ablakkal. A tétel MINDIG él — ha a
    // modell hiányzik, azt a megnyíló ablak MONDJA MEG; egy szürke
    // menüpont nem tudja megmagyarázni magát (néma tiltás, #1473).
    // SAJÁT FUNKCIÓ (#1473, #4638): az eredetiben nincs arckereső
    // menüparancs (a keresés háttérszál volt) — ld. fent, #2142.
    PicasaMenuItem {
        objectName: "menuToolsFaceScan"
        placeholder: false
        sajat: true
        text: qsTr("Find Faces...")
        onTriggered: bar.faceScanRequested()
    }
    MenuSeparator {}
    // hiányzott (#324 audit)
    MenuItem {
        objectName: "menuToolsPhotoViewerSettings"
        text: qsTr("Configure Photo Viewer...")
        onTriggered: bar.configurePhotoViewerRequested()
    }
    MenuItem {
        objectName: "menuToolsScreensaver"
        text: qsTr("Configure Screensaver...")
        onTriggered: bar.configureScreensaverRequested()
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    // #440: a mentés-készletek párbeszéde. A helye MÉRT (#1774): a
    // „Képernyővédő konfigurálása…" utáni csoporthatár alatt áll.
    MenuItem {
        objectName: "menuToolsBackup"
        text: qsTr("&Back Up Pictures...")
        onTriggered: bar.backupRequested()
    }
    PicasaMenuItem { text: qsTr("Batch Upload..."); placeholder: false; retired: true }  // #638
    MenuItem {
        objectName: "menuToolsAdjustTimestamp"
        text: qsTr("Adjust &Date and Time...")
        enabled: bar.libraryPhotoActionsEnabled
        onTriggered: bar.adjustTimestampRequested()
    }
    MenuSeparator {}
    // #5570: a job-237 mérés és a 6/b-6/c specifikáció szerinti, megszűnt
    // külső szolgáltatások tételei. Csak az almenü nyitható meg; a három
    // PicasaMenuItem retired jelölése szürkén és kattinthatatlanul tartja
    // őket. A feliratokban az `&` az eredeti mnemonik helye.
    PicasaMenu {
        objectName: "menuToolsUpload"
        title: qsTr("U&pload")
        PicasaMenuItem {
            objectName: "menuToolsUploadGooglePhotos"
            text: qsTr("Upload to Google &Photos")
            placeholder: false
            retired: true
        }
        PicasaMenuItem {
            objectName: "menuToolsUploadCollaborativeAlbum"
            text: qsTr("Upload to a Collaborative Web Album")
            placeholder: false
            retired: true
        }
        PicasaMenuItem {
            objectName: "menuToolsUploadYouTube"
            text: qsTr("Upload to &YouTube")
            placeholder: false
            retired: true
        }
    }
    // #530: a Geocímke almenü élesedett — az export motorja kész
    // (export/kml.py + earth.py). A feliratok a bináris index szerint:
    // eMenuTools::Geotag = "&Geotag", ID_EXPORT_EARTH =
    // "Export to Google Earth File".
    PicasaMenu {
        title: qsTr("&Geotag")
        MenuItem {
            objectName: "menuToolsExportEarth"
            text: qsTr("Export to Google Earth File")
            onTriggered: bar.earthExportRequested()
        }
        // #1589: `eMenuTools::ID_VIEW_EARTH` = „View in Google Earth..."
        // / „Megtekintés a Google Earth programban...". Az export
        // MELLETT áll, mert az eredetiben is két külön tétel ez a
        // kettő: az egyik csak kiírja a fájlt, ez kiírja ÉS megnyitja.
        //
        // ⚠️ MÉRVE, hogy a tétel NEM szürkül el geocímke híján. Az
        // eredeti ilyenkor BESZÉL, nem tilt: `PublishToEarth::NoTagged`
        // („Nincsenek exportálható geocímkézett képek") és
        // `PublishToEarth::Tag` („Nem minden kijelölt elem tartalmaz
        // geocímke jellegű információt… Megcímkézi most a képeket?").
        // Ez egybevág a #1473 döntésével: egy szürke menüpont nem tudja
        // megmagyarázni magát.
        MenuItem {
            objectName: "menuToolsViewEarth"
            text: qsTr("View in Google Earth...")
            onTriggered: bar.earthViewRequested()
        }
        // #1404: `eMenuTools::ID_PICTURE_GEOUNTAG` = „Clear Geotags" /
        // „Geocímkék törlése" — a menüsáv-építőben (`0x00559150`) a
        // Google Earth tételek testvéreként.
        //
        // A KÉPESSÉG régóta megvolt (`GeoMixin.clearGeotagRows`), csak
        // a Helyek panelről lehetett elérni: a menü-belépési pont
        // hiányzott. ⚠️ MINDKÉT út ugyanazon a megerősítésen megy át
        // (`ClearGeoTag::warn`) — a törlés visszafordíthatatlan.
        MenuItem {
            objectName: "menuToolsClearGeotag"
            text: qsTr("Clear Geotags")
            onTriggered: bar.clearGeotagRequested()
        }
    }
    PicasaMenu {
        objectName: "menuToolsExperimental"
        title: qsTr("Experimental")
        // #5713: az eredeti menü első Kísérleti tétele (`ID_FTPWEB`),
        // most már a közös HTML-export párbeszédből FTP-re publikál.
        MenuItem {
            objectName: "menuToolsPublishFtp"
            text: qsTr("Publish via FTP...")
            onTriggered: bar.ftpPublishRequested()
        }
        // #2142: a duplikátum-kereső az eredetiben a KÍSÉRLETI almenü
        // MÁSODIK tétele (`eMenuTools::ID_DUPES`, „Show Duplicate
        // Files"), nem a felső szinté. A #1794 mérte ki az Eszközök
        // menü teljes szerkezetét.
        //
        // #1398: MÉRVE, hogy ez a parancs NEM párbeszédet nyit: a
        // keresési sáv rejtett `dupesearch` jelzőjét kapcsolja be,
        // tehát szűrt nézetbe visz. A mi kezelő-párbeszédünk (#287)
        // ezért innen elköltözött a mód eredménysávjára.
        MenuItem {
            objectName: "menuToolsDedup"
            text: qsTr("Show Duplicate Files")
            onTriggered: bar.duplicateSearchRequested()
        }
        // SAJÁT FUNKCIÓ (#287): a duplikátum-KEZELŐ párbeszéd — az
        // eredetiben nincs ilyen, ezért a #1701 szerinti jelölést kapja
        // (kék felirat + buboréksúgó), és NEM a mért parancson ül: a
        // fenti tétel a keresési módot kapcsolja, ez a kezelőt nyitja.
        PicasaMenuItem {
            objectName: "menuToolsDedupManager"
            placeholder: false
            sajat: true
            text: qsTr("Manage Duplicates...")
            onTriggered: bar.dedupRequested()
        }
        //: #1399/#4689: a hét szín-keresés almenüje — az eredetiben a KÍSÉRLETI
        //: almenü HARMADIK tétele (`eMenuTools::Searchfor ▸`), közvetlenül
        //: a „Show Duplicate Files" után. A helyet a bináris menüépítőből
        //: mérte a #1794/#2142 (`picasa-menusor-csoportok.md`, az
        //: `eMenuTools` 36 kulcsa egyetlen függvényben) — az első
        //: nekifutásom a FELSŐ szintre tette, és a menü-csoport őre
        //: joggal buktatta meg.
        //:
        //: MÉRVE (`0x005ccc41`–`0x005ccca2` + `0x0065b7b0`): a hat
        //: színtétel ugyanazt teszi más tokennel — beírja a
        //: `color:<szín>`-t a keresőmezőbe, a kurzort a szöveg végére
        //: viszi, és lefuttatja a keresést. Nincs mögötte külön
        //: szűrő-mechanizmus.
        //:
        //: #4689: a hetedik tétel az `ID_VIEW_BW` (`&Black and White`,
        //: parancs `0x9da9`). A `0x005ccca7` kezelő ugyanazt a keresési
        //: folyamatot futtatja `color:black` értékkel.
        PicasaMenu {
            title: qsTr("Search for...")
            MenuItem {
                objectName: "menuToolsSearchRed"
                text: qsTr("&Red")
                onTriggered: bar.colorSearchRequested("red")
            }
            MenuItem {
                objectName: "menuToolsSearchOrange"
                text: qsTr("&Orange")
                onTriggered: bar.colorSearchRequested("orange")
            }
            MenuItem {
                objectName: "menuToolsSearchYellow"
                text: qsTr("&Yellow")
                onTriggered: bar.colorSearchRequested("yellow")
            }
            MenuItem {
                objectName: "menuToolsSearchGreen"
                text: qsTr("&Green")
                onTriggered: bar.colorSearchRequested("green")
            }
            MenuItem {
                objectName: "menuToolsSearchBlue"
                text: qsTr("&Blue")
                onTriggered: bar.colorSearchRequested("blue")
            }
            MenuItem {
                objectName: "menuToolsSearchPurple"
                text: qsTr("&Purple")
                onTriggered: bar.colorSearchRequested("purple")
            }
            MenuItem {
                objectName: "menuToolsSearchBlack"
                text: qsTr("&Black and White")
                onTriggered: bar.colorSearchRequested("black")
            }
        }
        //: #1405: `eMenuTools::ID_SAVESEARCH` — a Kísérleti almenü
        //: NEGYEDIK tétele (a „Keresés…" almenü után), a bináris
        //: menüépítőből mérve.
        //:
        //: MÉRVE (`0x005d86a0`, 362 bájt): 1000 találat FELETT
        //: megerősítést kér („This will create an album with more than
        //: 1000 images."), a gombja „Create Album" — alatta CSENDBEN
        //: létrejön az album. A küszöb tehát nem biztonsági kérdés,
        //: hanem a nagy album miatti figyelmeztetés.
        MenuItem {
            objectName: "menuToolsSaveSearch"
            text: qsTr("Save &search results...")
            //: csak keresési nézetben, találattal — üres keresésből
            //: album sem lesz
            enabled: bar.canSaveSearch
            onTriggered: bar.saveSearchRequested()
        }
        //: #1406: `eMenuTools::ID_SEARCHTOKEN` — a Kísérleti almenü
        //: ÖTÖDIK tétele (a keresés-mentés után), a bináris menüépítőből
        //: mérve.
        //:
        //: A színkeresés (#1399) FORDÍTOTTJA: ott a menüpont a
        //: keresőmezőbe ír, itt a felhasználó megad egy címkét, és abból
        //: RENDES ALBUM lesz — nem élő szűrő. Három külön szöveg tartozik
        //: hozzá (mérve, `0x005d8330`): a menüfelirat, a párbeszéd címe
        //: (`ThumbUI::addsearchtoken`) és a beviteli felszólítás
        //: (`CAlbumState::addsearchprompt`).
        MenuItem {
            objectName: "menuToolsShowTagAsAlbum"
            text: qsTr("Show &tag as album...")
            onTriggered: bar.showTagAsAlbumRequested()
        }
        //: #1401: `eMenuTools::ID_PASSPORT` — a Kísérleti almenü HATODIK
        //: tétele (a mért kilenc: Publish via FTP… (tiltva) · Show
        //: Duplicate Files · Search for ▸ · Save search results… ·
        //: Show tag as album… · **Passport photo…** · Delete empty
        //: online albums… (hatókörön kívül) · Choose database
        //: location… · Write faces to XMP…) — a `Show &tag as album…`
        //: után, a `Write faces to XMP…` előtt, a nálunk MEGLÉVŐ
        //: szomszédok szerint (`docs/specs/picasa-menu-parancsok-
        //: viselkedes.md`, 24. szakasz).
        MenuItem {
            objectName: "menuToolsPassportPhoto"
            text: qsTr("&Passport photo...")
            //: a kijelölt képre szól
            enabled: bar.photoActionsEnabled && !bar.editorActive
            onTriggered: bar.passportPhotoRequested()
        }
        // #368: az eredeti Picasa is a Kísérleti almenüből nyitotta.
        // #4635: a mért sorrendben a Passport photo után, a Write faces
        // to XMP előtt áll (a kilencből a nyolcadik).
        MenuItem {
            objectName: "menuToolsMoveDatabase"
            //: #2142: a MÉRT felirat (`eMenuTools::ID_MOVE_DATABASE`) —
            //: nem „Move Database...". Az eredetiben ez a 8. tétel.
            text: qsTr("Choose database location...")
            onTriggered: bar.moveDatabaseRequested()
        }
        //: #1403: `eMenuTools::ID_WRITE_XMP_FACES` — a Kísérleti almenü
        //: UTOLSÓ tétele (`0xd6e838`, mérve). A MEGLÉVŐ XMP-építőt köti be
        //: (`export/xmp.py`): a motor kész volt, csak a felhasználó felől
        //: nem volt hozzá út (#1798 hibaosztálya).
        MenuItem {
            objectName: "menuToolsWriteXmpFaces"
            text: qsTr("Write faces to XMP...")
            onTriggered: bar.writeXmpFacesDialogRequested()
        }
        // #449: adatbázis-tömörítés (`compacting.fen`) — az eredetiben
        // is a Kísérleti almenüben lakott, az áthelyezés mellett
        MenuItem {
            objectName: "menuToolsCompactDatabase"
            text: qsTr("Compact Database...")
            onTriggered: bar.compactDatabaseRequested()
        }
    }
    MenuSeparator {}
    //: #1792: az album-fejlec gombsoranak testreszabasa — ketlistas
    //: valaszto (`ConfigureButtonsDialog.qml`). A gombcsomag-letoltes
    //: (`picasa.smo`) hatokoron kivul: a kiszolgalo nem letezik.
    MenuItem {
        objectName: "menuConfigureButtons"
        text: qsTr("Configure Buttons...")
        onTriggered: bar.configureButtonsRequested()
    }
    // #1774 (mérve): az eredetiben itt NINCS csoporthatár.
    // #333/#3555: nyelvválasztás — a lista első tétele a rendszer
    // szerinti, utána a konkrét nyelvek (spec A szakasz). A pipa a
    // `pendingLanguage`-et tükrözi (a KÖVETKEZŐ indításra kért
    // választást, spec D szakasz), nem a mai `language`-t — a döntés a
    // Main.qml-ben élő megerősítő kérdés UTÁN íródik, és csak a
    // következő indításkor lép érvénybe (`languageConfirmRequested`,
    // ld. Main.qml ConfirmDialog). A #305-ös null-őr kötelező: a
    // controller a QML-engine leépítésekor null lehet.
    // #1468: a valódi kattintás előbb IMPERATÍVAN átbillenti a `checked`-et,
    // és csak utána dördül el a `triggered`. Kizáró csoportban a MÁR AKTÍV
    // tételre kattintva a vezérlő állapota nem változik, tehát a kötés magától
    // soha nem értékelődik újra — a menü újranyitásakor egyik tételen sem
    // állna pipa. Ezért a jelzés után azonnal VISSZAKÖTJÜK a `checked`-et
    // (a #1464-ben bevezetett minta) — ez a megerősítés ELMARADÁSA
    // (már aktív tétel, vagy "Nem"/"Mégse") esetén is kell.
    PicasaMenu {
        id: languageMenu
        objectName: "menuToolsLanguage"
        title: qsTr("Language")
        MenuItem {
            objectName: "menuLanguageSystem"
            text: controllerRef
                ? qsTr("System Default (%1)").arg(controllerRef.systemLanguageSuffix)
                : qsTr("System Default")
            checkable: true
            checked: (controllerRef && controllerRef.systemLanguageCode !== undefined)
                ? controllerRef.pendingLanguage === controllerRef.systemLanguageCode
                : false
            onTriggered: {
                bar.requestLanguageChange(
                    controllerRef ? controllerRef.systemLanguageCode : "system")
                checked = Qt.binding(function () {
                    return (controllerRef && controllerRef.systemLanguageCode !== undefined)
                        ? controllerRef.pendingLanguage === controllerRef.systemLanguageCode
                        : false
                })
            }
        }
        MenuItem {
            objectName: "menuLanguageEnglish"
            text: controllerRef ? controllerRef.ownLanguageName("en") : "English (US)"
            checkable: true
            checked: controllerRef ? controllerRef.pendingLanguage === "en" : true
            onTriggered: {
                bar.requestLanguageChange("en")
                checked = Qt.binding(function () {
                    return controllerRef ? controllerRef.pendingLanguage === "en" : true
                })
            }
        }
        MenuItem {
            objectName: "menuLanguageHungarian"
            text: controllerRef ? controllerRef.ownLanguageName("hu") : "Magyar"
            checkable: true
            checked: controllerRef ? controllerRef.pendingLanguage === "hu" : false
            onTriggered: {
                bar.requestLanguageChange("hu")
                checked = Qt.binding(function () {
                    return controllerRef ? controllerRef.pendingLanguage === "hu" : false
                })
            }
        }
        Instantiator {
            objectName: "menuLanguageAdditionalChoices"
            model: controllerRef
                ? controllerRef.availableLanguages.filter(
                    function (code) { return code !== "en" && code !== "hu" })
                : []
            delegate: MenuItem {
                property string languageCode: modelData
                objectName: "menuLanguage" + languageCode
                text: controllerRef ? controllerRef.ownLanguageName(languageCode) : languageCode
                checkable: true
                checked: controllerRef
                    ? controllerRef.pendingLanguage === languageCode
                    : false
                onTriggered: {
                    bar.requestLanguageChange(languageCode)
                    checked = Qt.binding(function () {
                        return controllerRef
                            ? controllerRef.pendingLanguage === languageCode
                            : false
                    })
                }
            }
            onObjectAdded: function (index, object) {
                languageMenu.insertItem(
                    controllerRef.availableLanguages.indexOf(object.languageCode) + 1,
                    object)
            }
            onObjectRemoved: function (_index, object) {
                languageMenu.removeItem(object)
            }
        }
    }
    // #1774 (mérve): az eredetiben itt NINCS csoporthatár.
    // #350: az OptionsDialog.qml megépült (9/8 fülős options.fen
    // paritás) — a jelzés itt fut ki, a dialógus példányosítása és a
    // signal bekötése a Main.qml-ben (forró fájl) az integrátoré
    MenuItem {
        objectName: "menuToolsOptions"
        text: qsTr("&Options...")
        onTriggered: bar.optionsRequested()
    }
    MenuSeparator {}
    // SAJÁT FUNKCIÓ (#3132): a régi Picasa adatbázisának átvétele. Az
    // eredeti Eszközök menüjében ilyen parancs NINCS és nem is lehet — ő
    // maga a `db3` gazdája, nekünk viszont át kell vennünk tőle. Ezért
    // kapja a #1701 jelölését, mint a duplikátum-KEZELŐ.
    //
    // A MAG a #3002/#3184 óta kész; ez a tétel az, ami eddig hiányzott
    // (#3132) — nélküle az adat a felhasználónál nem mozdult.
    PicasaMenuItem {
        objectName: "menuToolsImportFromPicasa"
        placeholder: false
        sajat: true
        text: qsTr("Import from Picasa...")
        onTriggered: bar.picasaDataImportRequested()
    }
}
