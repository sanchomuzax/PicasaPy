"""#4456: a mappatulajdonságok elrendezése az eredeti Picasa szerint."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QPointF, QTranslator, QUrl, Qt
from PySide6.QtGui import QFont
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre

import picasapy.app.application as app_module

app_module.allitsd_be_a_stilust()

_KEEPALIVE = []


def _ablak(qt_app, magassag: int, datum: str = "2026-01-01"):
    qt_app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(engine)
    component.setData(
        f"""
        import QtQuick
        import QtQuick.Controls
        import QtQuick.Window
        import PicasaPy 1.0
        ApplicationWindow {{
            objectName: "tesztAblak"
            visible: true
            width: 1920
            height: {magassag}
            color: "#eaeaea"
            palette {{
                window: "#eaeaea"
                windowText: "#1c1b19"
                base: "#ffffff"
                alternateBase: "#f3f3f3"
                text: "#1c1b19"
                button: "#f0f0f0"
                buttonText: "#1c1b19"
                mid: "#cdcdcd"
            }}
            FolderPropertiesDialog {{ objectName: "folderPropertiesDialog" }}
        }}
        """.encode("utf-8"),
        QUrl(),
    )
    ablak = component.create()
    assert [error.toString() for error in component.errors()] == []
    assert ablak is not None
    QQmlEngine.setObjectOwnership(ablak, QQmlEngine.ObjectOwnership.CppOwnership)
    dialog = ablak.findChild(QObject, "folderPropertiesDialog")
    assert dialog is not None
    _KEEPALIVE.extend((engine, component, ablak))
    assert QTest.qWaitForWindowExposed(ablak)
    dialog.setProperty("folderName", "2026-xx-xx screen")
    dialog.setProperty("currentDate", datum)
    dialog.open()
    assert varj_feltetelre(
        qt_app,
        lambda: dialog.property("opened"),
        3.0,
    )
    assert varj_feltetelre(
        qt_app,
        lambda: dialog.property("width") > 0
        and dialog.property("height") > 0,
        3.0,
    ), (
        "üres párbeszéd-geometria: "
        f"{dialog.property('width')}×{dialog.property('height')}"
    )
    return ablak, dialog


def _scenebox(elem):
    bal_felso = elem.mapToScene(QPointF(0, 0))
    jobb_also = elem.mapToScene(QPointF(elem.width(), elem.height()))
    return bal_felso.x(), bal_felso.y(), jobb_also.x(), jobb_also.y()


def _betumeret_beallitasa(dialog, pixel_meret: int) -> int:
    """A dialog összes betűt hordozó QML-elemén szimulál platform-metrikát."""
    darab = 0
    for elem in (dialog, *dialog.findChildren(QObject)):
        if elem.metaObject().indexOfProperty("font") < 0:
            continue
        betu = elem.property("font")
        if not isinstance(betu, QFont):
            continue
        betu.setPixelSize(pixel_meret)
        if elem.setProperty("font", betu):
            darab += 1
    return darab


def test_gombsor_alja_22px_betunel_is_14px_re_marad(qt_app):
    """A lábléc alját a dialógus rögzítse, ne a tartalom természetes mérete."""
    forras = (
        Path(__file__).resolve().parents[2]
        / "src/picasapy/app/qml/PicasaPy/FolderPropertiesDialog.qml"
    ).read_text(encoding="utf-8")
    dialog_tulajdonsagok = forras.split("Dialog {", 1)[1].split(
        "    //: #3173", 1
    )[0]
    assert "bottomPadding: 0" in dialog_tulajdonsagok, (
        "a Dialog stílusfüggő alsó kitöltését explicit nullázni kell"
    )
    footer = forras.split("    footer:", 1)[1].split(
        "    // A hosszú magyar feliratok", 1
    )[0]
    assert "DialogButtonBox {" in footer
    assert "anchors.bottom: parent.bottom" in footer, (
        "a gombsor alja nincs a rögzített lábléc aljához horgonyozva"
    )
    assert "anchors.bottomMargin: 14" in footer, (
        "a gombsor alsó margóját konstrukcióból 14 px-re kell rögzíteni"
    )

    ablak, dialog = _ablak(qt_app, 1075)
    assert _betumeret_beallitasa(dialog, 22) > 0, (
        "a 22 px-es betűmetrika-próba egyetlen QML-elemet sem módosított"
    )
    assert varj_feltetelre(
        qt_app,
        lambda: dialog.findChild(
            QObject, "folderPropertiesNameLabel"
        ).property("font").pixelSize() == 22,
        3.0,
    ), "a 22 px-es betűmetrika-próba nem lépett életbe"

    ok = dialog.findChild(QObject, "folderPropertiesOkButton")
    assert ok is not None
    _x, _y, _right, ok_bottom = _scenebox(ok)
    also_margo = dialog.property("y") + dialog.property("height") - ok_bottom
    assert abs(also_margo - 14) <= 3, (
        f"22 px-es betűnél a gombsor alsó margója {also_margo:.1f}px, "
        "a referencia 14±3px"
    )


def test_dialog_egyezik_a_referenciaval_harom_ablakmagassagon(
    qt_app, tmp_path
):
    """A QML-t kirajzolja, elmenti, és a sorok elhelyezését méri.

    A referencia (1920×1080) ablakmagasság-próbája 1075/1080/1085 px.
    A sorvégek és a vezérlők közötti referenciahézag 5 px. A betűk
    pixelméretét nem rögzítjük: a zene feliratánál a QML fontInfo adja a
    tényleges pixelSize értéket, a felirat teljes szélességét mérjük.
    """
    translator = QTranslator(qt_app)
    assert translator.load(
        str(app_module._APP_DIR / "i18n" / "picasapy_hu.qm")
    ), "a picasapy_hu.qm nem tölthető be"
    assert qt_app.installTranslator(translator)

    hibak = []
    dobozok = []
    elvart_sorok = (
        ("folderPropertiesNameLabel", "folderPropertiesNameField"),
        ("folderPropertiesDateLabel", "folderPropertiesDateField"),
        ("folderPropertiesMusicLabel", "folderPropertiesUseMusic"),
        ("folderPropertiesLocationLabel", "folderPropertiesLocation"),
        ("folderPropertiesDescriptionLabel", "folderPropertiesDescription"),
    )
    forras = (
        Path(__file__).resolve().parents[2]
        / "src/picasapy/app/qml/PicasaPy/FolderPropertiesDialog.qml"
    ).read_text(encoding="utf-8")
    zene_mezo = forras.split(
        'objectName: "folderPropertiesUseMusic"', 1
    )[1].split("}", 1)[0]
    if "font.pixelSize: Theme.fontSize" not in zene_mezo:
        hibak.append("a zene jelölő feliratának Theme.fontSize beállítása hiányzik")
    if "HorizontalFit" in zene_mezo:
        hibak.append("a zene jelölő felirata zsugorítható betűméretet használ")
    for label_nev, _ in elvart_sorok:
        if label_nev not in forras:
            hibak.append(f"forrás-őr: hiányzik a(z) {label_nev} címke")
        else:
            label_blokk = forras.split(
                f'objectName: "{label_nev}"', 1
            )[1].split("}", 1)[0]
            if "horizontalAlignment: Text.AlignRight" not in label_blokk:
                hibak.append(f"forrás-őr: a(z) {label_nev} nem jobbra zárt")
    for mezo_nev in (
        "folderPropertiesNameField",
        "folderPropertiesDateField",
        "folderPropertiesUseMusic",
        "folderPropertiesMusicPath",
        "folderPropertiesLocation",
        "folderPropertiesDescription",
    ):
        mezo_blokk = forras.split(f'objectName: "{mezo_nev}"', 1)[1].split("}", 1)[0]
        if "font.pixelSize: Theme.fontSize" not in mezo_blokk:
            hibak.append(f"forrás-őr: hiányzik a Theme.fontSize a(z) {mezo_nev} mezőről")
    try:
        for magassag in (1075, 1080, 1085):
            ablak, dialog = _ablak(qt_app, magassag)
            assert varj_feltetelre(
                qt_app, lambda a=ablak: a.isExposed(), 3.0
            )
            kep = ablak.grabWindow()
            assert not kep.isNull(), "a párbeszéd képernyőképe üres"
            assert kep.save(str(tmp_path / f"mappa-tulajdonsagai-{magassag}.png"))
            dobozok.append(
                (
                    dialog.property("x"),
                    dialog.property("y"),
                    dialog.property("width"),
                    dialog.property("height"),
                )
            )
            if abs(dialog.property("width") - 585) > 3:
                hibak.append(
                    f"{magassag}px: ablak szélessége {dialog.property('width')}px, "
                    "a referencia 585±3px"
                )
            if abs(dialog.property("height") - 315) > 3:
                hibak.append(
                    f"{magassag}px: ablakmagasság {dialog.property('height')}px, "
                    "a referencia 315±3px"
                )

            leiras = dialog.findChild(QObject, "folderPropertiesDescription")
            if leiras is not None:
                bal, felso, jobb, _ = _scenebox(leiras)
                x = round((bal + jobb) / 2)
                keret = kep.pixelColor(x, round(felso))
                kitoltes = kep.pixelColor(x, round(felso + 3))
                if keret == kitoltes:
                    hibak.append(
                        f"{magassag}px: a leírásmező kerete nem látszik a képen"
                    )

            if dialog.property("title") != "Mappa tulajdonságai":
                hibak.append(
                    f"{magassag}px: cím={dialog.property('title')!r}, "
                    "elvárt='Mappa tulajdonságai'"
                )
            megsse = dialog.findChild(QObject, "folderPropertiesCancelButton")
            if megsse is None:
                hibak.append(f"{magassag}px: hiányzik a Mégse gomb azonosítója")
            elif megsse.property("text") != "Mégse":
                hibak.append(
                    f"{magassag}px: Mégse felirata={megsse.property('text')!r}"
                )

            sor_geometria = {}
            zene_jelolo = dialog.findChild(QObject, "folderPropertiesUseMusic")
            if zene_jelolo is None:
                hibak.append(f"{magassag}px: hiányzik a zene jelölő")
            else:
                nev_mezo = dialog.findChild(QObject, "folderPropertiesNameField")
                if nev_mezo is not None and abs(
                    zene_jelolo.property("width") - nev_mezo.property("width") - 7
                ) > 3:
                    hibak.append(
                        f"{magassag}px: a zene jelölő nem használja ki a teljes jobb oszlopot "
                        f"(jelölő={zene_jelolo.property('width')}px, "
                        f"mező={nev_mezo.property('width')}px, elvárt különbség=7px)"
                    )
                zene_felirat = zene_jelolo.property("contentItem")
                if zene_felirat is None:
                    hibak.append(f"{magassag}px: hiányzik a zene jelölő felirata")
                else:
                    if zene_felirat.property("truncated") is not False:
                        hibak.append(
                            f"{magassag}px: a zene jelölő felirata le van vágva "
                            f"(truncated={zene_felirat.property('truncated')!r}, "
                            f"szélesség={zene_felirat.property('width')!r})"
                        )
                    music_size = zene_felirat.property(
                        "fontInfo"
                    ).property("pixelSize").toVariant()
                    name_label = dialog.findChild(
                        QObject, "folderPropertiesNameLabel"
                    )
                    name_size = (
                        name_label.property("fontInfo")
                        .property("pixelSize")
                        .toVariant()
                        if name_label is not None
                        else None
                    )
                    if music_size != name_size:
                        hibak.append(
                            f"{magassag}px: a zene felirat betűmérete {music_size}px, "
                            f"a többi feliraté {name_size}px"
                        )
                    szoveghely = (
                        zene_felirat.property("width")
                        - zene_felirat.property("leftPadding")
                        - zene_felirat.property("rightPadding")
                    )
                    if zene_felirat.property("contentWidth") > szoveghely + 1:
                        hibak.append(
                            f"{magassag}px: a teljes zene-felirat nem fér el "
                            f"(szöveg={zene_felirat.property('contentWidth'):.1f}px, "
                            f"hely={szoveghely:.1f}px)"
                        )
                    if (
                        zene_felirat.property("implicitHeight")
                        > zene_felirat.property("height") + 1
                    ):
                        hibak.append(
                            f"{magassag}px: a zene-felirat renderelt magassága "
                            "nagyobb a rendelkezésre álló helyénél"
                        )
            for label_nev, vezerlo_nev in elvart_sorok:
                label = dialog.findChild(QObject, label_nev)
                vezerlo = dialog.findChild(QObject, vezerlo_nev)
                if label is None or vezerlo is None:
                    hibak.append(
                        f"{magassag}px: hiányzó sor: {label_nev}/{vezerlo_nev}"
                    )
                    continue
                label_bal, label_felso, label_jobb, label_also = _scenebox(label)
                vezerlo_bal, vezerlo_felso, _, vezerlo_also = _scenebox(vezerlo)
                sor_geometria[vezerlo_nev] = (vezerlo_bal, vezerlo_felso)
                tartalom_bal = dialog.property("x") + dialog.property(
                    "leftPadding"
                )
                rajzolt_felirat_bal = (
                    label_jobb - label.property("implicitWidth")
                )
                if rajzolt_felirat_bal < tartalom_bal - 0.5:
                    hibak.append(
                        f"{magassag}px: {label_nev} felirata a tartalmi bal szél "
                        f"elé lóg ({rajzolt_felirat_bal:.1f}px < {tartalom_bal:.1f}px; "
                        f"a címke geometriája {label_bal:.1f}px-től indul)"
                    )
                if label_bal < tartalom_bal - 0.5:
                    hibak.append(
                        f"{magassag}px: {label_nev} címkeeleme a tartalmi bal "
                        f"szél elé lóg ({label_bal:.1f}px < {tartalom_bal:.1f}px)"
                    )
                vizualis_vezerlo_bal = vezerlo_bal
                if vezerlo_nev == "folderPropertiesUseMusic":
                    jelolo = vezerlo.property("indicator")
                    if jelolo is not None:
                        vizualis_vezerlo_bal = _scenebox(jelolo)[0]
                res = vizualis_vezerlo_bal - label_jobb
                if abs(res - 5) > 3:
                    hibak.append(
                        f"{magassag}px: {label_nev}→{vezerlo_nev} hézag="
                        f"{res:.1f}px, a referencia 5±3px"
                    )
                if label_nev == "folderPropertiesDescriptionLabel":
                    eltolas = label_felso - vezerlo_felso
                    if abs(eltolas - 7) > 2:
                        hibak.append(
                            f"{magassag}px: a Leírás felirat teteje "
                            f"{eltolas:.1f}px-re van a mezőétől (ref. 7±2px)"
                        )
                else:
                    label_kozep = (label_felso + label_also) / 2
                    vezerlo_kozep = (vezerlo_felso + vezerlo_also) / 2
                    if abs(label_kozep - vezerlo_kozep) > 2:
                        hibak.append(
                            f"{magassag}px: {label_nev} függőleges középpontja "
                            f"{abs(label_kozep - vezerlo_kozep):.1f}px-re van"
                        )
            # A referenciaképen, a párbeszéd tetejétől mérve. A helyi
            # koordináta megőrzi a geometriai összevetést a címsor és a
            # platform ablakkeretének eltérő magassága mellett is.
            referencia_felso_elek = (
                ("folderPropertiesNameField", 40),
                ("folderPropertiesDateField", 74),
                ("folderPropertiesUseMusic", 108),
                ("folderPropertiesMusicPath", 128),
                ("folderPropertiesLocation", 160),
                ("folderPropertiesDescription", 192),
            )
            # A címsor magassága betűkészletfüggő (gépenként 5 px is lehet),
            # ezért a sorokat a Név mező tetejéhez mérjük: a referencia
            # különbségei változatlanok, csak a címsor esik ki a mérésből.
            nev_mezo = dialog.findChild(QObject, "folderPropertiesNameField")
            nev_felso = _scenebox(nev_mezo)[1] if nev_mezo is not None else None
            for vezerlo_nev, referencia in referencia_felso_elek:
                vezerlo = dialog.findChild(QObject, vezerlo_nev)
                if vezerlo is None or nev_felso is None:
                    continue
                _, felso, _, _ = _scenebox(vezerlo)
                mert = felso - nev_felso
                if abs(mert - (referencia - 40)) > 3:
                    hibak.append(
                        f"{magassag}px: {vezerlo_nev} teteje {mert:.1f}px-re "
                        f"van a Név mező tetejétől, referencia {referencia - 40}±3px"
                    )
            path = dialog.findChild(QObject, "folderPropertiesMusicPath")
            if path is not None:
                bal, felso, _, _ = _scenebox(path)
                sor_geometria["folderPropertiesMusicPath"] = (bal, felso)
            tavolsagok = (
                ("folderPropertiesDateField", "folderPropertiesNameField", 35),
                ("folderPropertiesUseMusic", "folderPropertiesDateField", 33),
                ("folderPropertiesMusicPath", "folderPropertiesUseMusic", 21),
                ("folderPropertiesLocation", "folderPropertiesMusicPath", 31),
                ("folderPropertiesDescription", "folderPropertiesLocation", 33),
            )
            for cel, elozo, referencia in tavolsagok:
                if cel not in sor_geometria or elozo not in sor_geometria:
                    hibak.append(f"{magassag}px: hiányzó vezérlő a sorrendhez: {elozo}/{cel}")
                    continue
                mert = sor_geometria[cel][1] - sor_geometria[elozo][1]
                if abs(mert - referencia) > 3:
                    hibak.append(
                        f"{magassag}px: {elozo}→{cel} függőleges távolság "
                        f"{mert:.1f}px, a referencia {referencia}±3px"
                    )

            ok = dialog.findChild(QObject, "folderPropertiesOkButton")
            megsse = dialog.findChild(QObject, "folderPropertiesCancelButton")
            if ok is not None and megsse is not None:
                ok_x, ok_y, ok_jobb, ok_also = _scenebox(ok)
                megsse_x, _megsse_y, megsse_jobb, megsse_also = _scenebox(megsse)
                if ok_x >= megsse_x:
                    hibak.append(f"{magassag}px: a gombok nem OK · Mégse sorrendűek")
                if abs((megsse_x - ok_jobb) - 7) > 3:
                    hibak.append(
                        f"{magassag}px: a gombköz {megsse_x - ok_jobb:.1f}px, "
                        "a referencia 7±3px"
                    )
                jobb_margó = (
                    dialog.property("x") + dialog.property("width") - megsse_jobb
                )
                if abs(jobb_margó - 14) > 3:
                    gombdoboz = ok.parent()
                    hibak.append(
                        f"{magassag}px: a gombsor jobb margója {jobb_margó:.1f}px, "
                        "a referencia 14±3px; "
                        f"gomb szülője={gombdoboz.metaObject().className()} "
                        f"({gombdoboz.objectName()}), "
                        f"doboz x/y/w/h={tuple(gombdoboz.property(n) for n in ('x','y','width','height'))}"
                    )
                # A gombsor az eredetiben is a párbeszéd aljához tapad: az
                # alsó margót mérjük (315 − 277 − 24 = 14 px a referencián),
                # mert a címsor magassága gépenként eltér.
                also_margo = (
                    dialog.property("y") + dialog.property("height") - ok_also
                )
                if abs(also_margo - 14) > 3:
                    hibak.append(
                        f"{magassag}px: a gombsor alsó margója "
                        f"{also_margo:.1f}px, a referencia 14±3px"
                    )
                if abs((ok_jobb - ok_x) - 85) > 3 or abs((ok_also - ok_y) - 24) > 3:
                    hibak.append(
                        f"{magassag}px: OK méret {ok_jobb - ok_x:.1f}×"
                        f"{ok_also - ok_y:.1f}px, a referencia 85×24±3px"
                    )
                if abs((megsse_jobb - megsse_x) - 85) > 3 or abs(
                    (megsse_also - _megsse_y) - 24
                ) > 3:
                    hibak.append(
                        f"{magassag}px: Mégse méret {megsse_jobb - megsse_x:.1f}×"
                        f"{megsse_also - _megsse_y:.1f}px, a referencia 85×24±3px"
                    )

            name = dialog.findChild(QObject, "folderPropertiesNameField")
            if name is not None and name.property("enabled") is not False:
                hibak.append(f"{magassag}px: a szándékosan letiltott Név mező aktív")
            music_path = dialog.findChild(QObject, "folderPropertiesMusicPath")
            if music_path is not None:
                path_bal, path_felso, path_jobb, path_also = _scenebox(music_path)
                path_szin = kep.pixelColor(
                    round((path_bal + path_jobb) / 2),
                    round((path_felso + path_also) / 2),
                )
                if (
                    max(path_szin.red(), path_szin.green(), path_szin.blue()) >= 250
                    or max(path_szin.red(), path_szin.green(), path_szin.blue())
                    - min(path_szin.red(), path_szin.green(), path_szin.blue())
                    > 5
                ):
                    hibak.append(
                        f"{magassag}px: a letiltott zene-fájlmező nem szürke "
                        f"({path_szin.name()})"
                    )
            for mezo_nev, referencia in (
                ("folderPropertiesNameField", 347),
                ("folderPropertiesLocation", 347),
                ("folderPropertiesMusicPath", 240),
                ("folderPropertiesDescription", 347),
            ):
                mezo = dialog.findChild(QObject, mezo_nev)
                if mezo is not None and abs(mezo.property("width") - referencia) > 3:
                    hibak.append(
                        f"{magassag}px: {mezo_nev} szélessége "
                        f"{mezo.property('width')}px, a referencia "
                        f"{referencia}±3px"
                    )

        if len(dobozok) == 3:
            _, kozep_y, _, kozep_m = dobozok[1]
            _, alacsony_y, _, alacsony_m = dobozok[0]
            _, magas_y, _, magas_m = dobozok[2]
            magassagok = (kozep_m, alacsony_m, magas_m)
            if max(magassagok) - min(magassagok) > 1:
                hibak.append(f"az ablakmagasság változására módosult a párbeszéd: {dobozok}")
            if abs((alacsony_y - kozep_y) + 2.5) > 1.5:
                hibak.append(f"1075px-es ablaknál a középre igazítás eltért: {dobozok}")
            if abs((magas_y - kozep_y) - 2.5) > 1.5:
                hibak.append(f"1085px-es ablaknál a középre igazítás eltért: {dobozok}")

        ervenytelen_ablak, ervenytelen_dialog = _ablak(
            qt_app, 1080, datum="nem-dátum"
        )
        assert varj_feltetelre(
            qt_app, lambda: ervenytelen_ablak.isExposed(), 3.0
        )
        ervenytelen_kep = ervenytelen_ablak.grabWindow()
        assert not ervenytelen_kep.isNull(), "a hibás dátum képernyőképe üres"
        assert ervenytelen_kep.save(
            str(tmp_path / "mappa-tulajdonsagai-ervenytelen.png")
        )
        date_hint = ervenytelen_dialog.findChild(
            QObject, "folderPropertiesDateHint"
        )
        ok_button = ervenytelen_dialog.findChild(
            QObject, "folderPropertiesOkButton"
        )
        cancel_button = ervenytelen_dialog.findChild(
            QObject, "folderPropertiesCancelButton"
        )
        assert date_hint is not None and date_hint.property("visible") is True
        assert ok_button is not None and cancel_button is not None
        hint_left, hint_top, hint_right, hint_bottom = _scenebox(date_hint)
        _ok_left, ok_top, ok_right, _ok_bottom = _scenebox(ok_button)
        _cancel_left, cancel_top, cancel_right, _cancel_bottom = _scenebox(
            cancel_button
        )
        content_left = (
            ervenytelen_dialog.property("x")
            + ervenytelen_dialog.property("leftPadding")
        )
        content_right = (
            ervenytelen_dialog.property("x")
            + ervenytelen_dialog.property("width")
            - ervenytelen_dialog.property("rightPadding")
        )
        if hint_left < content_left - 0.5 or hint_right > content_right + 0.5:
            hibak.append(
                "1080px: az érvénytelen dátum hibaüzenete kilóg a párbeszéd "
                f"tartalmából ({hint_left:.1f}..{hint_right:.1f}, "
                f"elvárt {content_left:.1f}..{content_right:.1f})"
            )
        if hint_bottom >= min(ok_top, cancel_top):
            hibak.append(
                "1080px: az érvénytelen dátum hibaüzenete eléri vagy takarja "
                "a gombsor tetejét"
            )
        if max(ok_right, cancel_right) > content_right + 3:
            hibak.append("1080px: a gombsor kilóg a párbeszéd jobb szélén")
        for name in (
            "folderPropertiesUseMusic",
            "folderPropertiesMusicPath",
            "folderPropertiesLocation",
            "folderPropertiesDescription",
        ):
            field = ervenytelen_dialog.findChild(QObject, name)
            if field is None:
                continue
            field_left, field_top, field_right, field_bottom = _scenebox(field)
            if (
                max(hint_left, field_left) < min(hint_right, field_right)
                and max(hint_top, field_top) < min(hint_bottom, field_bottom)
            ):
                hibak.append(
                    f"1080px: a dátumhiba takarja a(z) {name} vezérlőt"
                )
    finally:
        qt_app.removeTranslator(translator)

    assert not hibak, "\n".join(hibak)
