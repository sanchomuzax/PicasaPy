"""#4456: a mappatulajdonságok elrendezése az eredeti Picasa szerint."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QPointF, QTranslator, QUrl, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre

import picasapy.app.application as app_module

app_module.allitsd_be_a_stilust()

_KEEPALIVE = []


def _ablak(qt_app, magassag: int):
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
    dialog.setProperty("currentDate", "2026-01-01")
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


def test_dialog_egyezik_a_referenciaval_harom_ablakmagassagon(
    qt_app, tmp_path
):
    """A QML-t kirajzolja, elmenti, és a sorok elhelyezését méri.

    A referencia (1920×1080) ablakmagasság-próbája 1075/1080/1085 px.
    A sorvégek és a vezérlők közötti referenciahézag 5 px; betűképet pixelre
    nem mérünk, a zene feliratánál a vágás hiányát ellenőrizzük.
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
    if (
        'property: "fontSizeMode"' not in zene_mezo
        or "value: Text.HorizontalFit" not in zene_mezo
    ):
        hibak.append("a zene jelölő felirata nem igazodik a rendelkezésre álló szélességhez")
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
                    zene_jelolo.property("width") - nev_mezo.property("width")
                ) > 3:
                    hibak.append(
                        f"{magassag}px: a zene sor nem használja ki a mezőoszlopot "
                        f"(jelölő={zene_jelolo.property('width')}px, "
                        f"mező={nev_mezo.property('width')}px)"
                    )
                zene_felirat = zene_jelolo.property("contentItem")
                if zene_felirat is None:
                    hibak.append(f"{magassag}px: hiányzik a zene jelölő felirata")
                elif zene_felirat.property("truncated") is not False:
                    hibak.append(
                        f"{magassag}px: a zene jelölő felirata le van vágva "
                        f"(truncated={zene_felirat.property('truncated')!r}, "
                        f"szélesség={zene_felirat.property('width')!r})"
                    )
            for label_nev, vezerlo_nev in elvart_sorok:
                label = dialog.findChild(QObject, label_nev)
                vezerlo = dialog.findChild(QObject, vezerlo_nev)
                if label is None or vezerlo is None:
                    hibak.append(
                        f"{magassag}px: hiányzó sor: {label_nev}/{vezerlo_nev}"
                    )
                    continue
                _, label_felso, label_jobb, label_also = _scenebox(label)
                vezerlo_bal, vezerlo_felso, _, vezerlo_also = _scenebox(vezerlo)
                sor_geometria[vezerlo_nev] = (vezerlo_bal, vezerlo_felso)
                res = vezerlo_bal - label_jobb
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
    finally:
        qt_app.removeTranslator(translator)

    assert not hibak, "\n".join(hibak)
