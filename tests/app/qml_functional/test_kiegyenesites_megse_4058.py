"""#4058 — az Alkalmaz/Mégse szerkesztési munkamenet regressziós próbái."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QTest


ABLAK = (1280, 1005)


def _item(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a kirajzolt fában"
    return elem


def _kep_mentese(
    path: Path,
    size: int | tuple[int, int],
    *,
    szin: str,
    negyedes: bool = False,
) -> None:
    szelesseg, magassag = (size, size) if isinstance(size, int) else size
    kep = QImage(szelesseg, magassag, QImage.Format.Format_RGB32)
    kep.fill(QColor(szin))
    if negyedes:
        festo = QPainter(kep)
        fele = szelesseg // 2
        festo.fillRect(QRect(0, 0, fele, fele), QColor("red"))
        festo.fillRect(QRect(fele, 0, szelesseg - fele, fele), QColor("white"))
        festo.fillRect(QRect(0, fele, fele, magassag - fele), QColor("blue"))
        festo.fillRect(QRect(fele, fele, szelesseg - fele, magassag - fele), QColor("green"))
        festo.end()
    assert kep.save(str(path), "JPEG", 100), f"nem írható a próbakép: {path}"


def _forrasok(
    controller,
    *,
    negyedes: bool = False,
    masodik_meret: int | tuple[int, int] = 1024,
    masodik_szin: str = "white",
) -> None:
    """A két indexelt négyzetképet determinisztikus képre cseréli."""
    _kep_mentese(
        Path(str(controller.photos.filePathAt(0))),
        800,
        szin="black",
        negyedes=negyedes,
    )
    _kep_mentese(
        Path(str(controller.photos.filePathAt(1))),
        masodik_meret,
        szin=masodik_szin,
    )


def _beallit_ablak(window, qt_app, ablak: tuple[int, int] = ABLAK) -> None:
    window.setProperty("width", ablak[0])
    window.setProperty("height", ablak[1])
    for _ in range(5):
        qt_app.processEvents()


def _pont(item, x: float, y: float) -> QPoint:
    pont = item.mapToScene(QPointF(x, y))
    return QPoint(round(pont.x()), round(pont.y()))


def _kattint(window, elem, qt_app) -> None:
    assert elem.width() > 0 and elem.height() > 0, "a vezérlő nem látható"
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _pont(elem, elem.width() / 2, elem.height() / 2),
    )
    for _ in range(5):
        qt_app.processEvents()


def _nezobe_lep(window, qt_app, index: int = 0):
    window.setProperty("viewerOpen", True)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", index)
    for _ in range(8):
        qt_app.processEvents()
    return viewer


def _felvetel(window, utvonal: Path) -> QImage:
    kep = window.grabWindow()
    assert not kep.isNull(), "a néző ablaka nem rajzolódott ki"
    assert kep.save(str(utvonal), "PNG"), f"nem menthető a felvétel: {utvonal}"
    return kep


def _vezerlo_rect(elem) -> QRect:
    bal_felso = elem.mapToScene(QPointF(0, 0))
    return QRect(
        round(bal_felso.x()),
        round(bal_felso.y()),
        round(elem.width()),
        round(elem.height()),
    )


def _kulonbozo_pixelek(egy: QImage, ketto: QImage, rect: QRect) -> int:
    db = 0
    for y in range(rect.top(), rect.bottom() + 1):
        for x in range(rect.left(), rect.right() + 1):
            if egy.pixelColor(x, y) != ketto.pixelColor(x, y):
                db += 1
    return db


def _thumb_url_a_forrasbol(controller, photos, forras: Path, qt_app) -> str:
    """Megvárja, hogy a modell a felülírt próbakép friss metaadatait lássa."""
    stat = forras.stat()
    fajl_cimke = f"&m={stat.st_mtime_ns}&s={stat.st_size}"
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        url = photos.thumbUrlAt(0)
        if fajl_cimke in url:
            qt_app.processEvents()
            if photos.thumbUrlAt(0) == url:
                return url
        QTest.qWait(50)
    raise AssertionError(f"a bélyegkép URL-je nem követte a forrásfájlt: {url!r}")


def test_kiegyenesites_megse_visszaallitja_a_megnyitaskori_munkamenetet(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    """A valódi csúszka és Mégse-kattintás ne írja át a megnyitáskori állapotot."""
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller, negyedes=True)
    _beallit_ablak(window, qt_app)
    viewer = _nezobe_lep(window, qt_app)
    photos = viewer.property("photosModel")
    edit_controller = viewer.property("editCtl")
    ini_path = tmp_path / "kepek" / ".picasa.ini"
    ini_elotte = ini_path.read_bytes() if ini_path.exists() else None
    thumb_elotte = _thumb_url_a_forrasbol(
        controller, photos, Path(str(controller.photos.filePathAt(0))), qt_app
    )
    kezdo_rekord = photos.itemAt(0)
    kezdo = {
        "filters": edit_controller.property("chainValue"),
        "undo": edit_controller.property("undoAction"),
        "redo": edit_controller.property("redoAction"),
        "hasEdits": kezdo_rekord["hasEdits"],
        "thumbUrl": thumb_elotte,
        "ini": ini_elotte,
    }
    assert kezdo == {
        "filters": "",
        "undo": "",
        "redo": "",
        "hasEdits": False,
        "thumbUrl": kezdo["thumbUrl"],
        "ini": None,
    }

    image = _item(window, "viewerImage")
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    slider = _item(window, "tiltSlider")
    racs = _item(window, "straightenGridOverlay")
    slider_kozep = _pont(slider, slider.width() / 2, slider.height() / 2)
    QTest.mouseRelease(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        slider_kozep,
    )
    for _ in range(5):
        qt_app.processEvents()
    assert slider.property("pressed") is False
    slider.setProperty("value", 0.0)
    for _ in range(5):
        qt_app.processEvents()
    assert float(slider.property("value")) == 0.0

    racs.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    kep_terulet = _vezerlo_rect(image)
    eszkozsav = _vezerlo_rect(_item(window, "editorToolBar"))
    kep_terulet.setHeight(eszkozsav.top() - kep_terulet.top())
    kep_nyitaskor = _felvetel(window, tmp_path / "tilt-nyitva.png")
    racs.setProperty("visible", True)

    _tilt_huzasa_egerrel(window, qt_app, slider)

    racs.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    kep_huzas_utan = _felvetel(window, tmp_path / "tilt-huzas-utan.png")
    racs.setProperty("visible", True)

    _kattint(window, _item(window, "tiltCancelButton"), qt_app)
    for _ in range(8):
        qt_app.processEvents()
    kep_megse_utan = _felvetel(window, tmp_path / "tilt-megse-utan.png")
    ini_utana = ini_path.read_bytes() if ini_path.exists() else None
    megse_utan = {
        "filters": edit_controller.property("chainValue"),
        "undo": edit_controller.property("undoAction"),
        "redo": edit_controller.property("redoAction"),
        "hasEdits": photos.itemAt(0)["hasEdits"],
        "thumbUrl": photos.thumbUrlAt(0),
        "ini": ini_utana,
    }
    megse_utan["kep_diff"] = _kulonbozo_pixelek(kep_nyitaskor, kep_megse_utan, kep_terulet)
    huzas_diff = _kulonbozo_pixelek(kep_nyitaskor, kep_huzas_utan, kep_terulet)

    _kattint(window, _item(window, "viewerBackButton"), qt_app)
    assert window.property("viewerOpen") is False
    indexen = {
        "hasEdits": photos.itemAt(0)["hasEdits"],
        "thumbUrl": photos.thumbUrlAt(0),
    }

    _nezobe_lep(window, qt_app)
    ujranyitva = {
        "filters": edit_controller.property("chainValue"),
        "undo": edit_controller.property("undoAction"),
        "redo": edit_controller.property("redoAction"),
        "hasEdits": photos.itemAt(0)["hasEdits"],
        "ini": ini_path.read_bytes() if ini_path.exists() else None,
    }
    assert huzas_diff > 0, "a valódi csúszkahúzás nem változtatta meg a kép előnézetét"
    assert megse_utan == {**kezdo, "kep_diff": 0}, (
        "a tilt Mégse után a szerkesztési munkamenet eltér a megnyitás előttitől: "
        f"{megse_utan!r}; Index: {indexen!r}; újranyitva: {ujranyitva!r}"
    )
    assert indexen == {"hasEdits": False, "thumbUrl": kezdo["thumbUrl"]}
    assert ujranyitva == {
        "filters": "",
        "undo": "",
        "redo": "",
        "hasEdits": False,
        "ini": None,
    }, f"újranyitás után nem üres a szerkesztés: {ujranyitva!r}"


def _tilt_huzasa_egerrel(window, qt_app, slider) -> None:
    kezdo = _pont(slider, slider.width() / 2, slider.height() / 2)
    veg = _pont(slider, slider.width() * 0.78, slider.height() / 2)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kezdo)
    for _ in range(8):
        qt_app.processEvents()
    assert slider.property("pressed") is False, "az előző próba lenyomva hagyta az egeret"
    slider.setProperty("value", 0.0)
    for _ in range(8):
        qt_app.processEvents()
    assert float(slider.property("value")) == 0.0, "a csúszka nem a nulla kiindulóértéken áll"
    try:
        QTest.mouseMove(window, kezdo, 10)
        for _ in range(8):
            qt_app.processEvents()
        QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kezdo)
        for _ in range(8):
            qt_app.processEvents()
        assert slider.property("pressed") is True, "az egérlenyomás nem érte el a csúszkát"
        koztes = _pont(slider, slider.width() * 0.62, slider.height() / 2)
        QTest.mouseMove(window, koztes, 10)
        for _ in range(8):
            qt_app.processEvents()
        assert slider.property("pressed") is True, "a csúszka elengedte a köztes húzásnál"
        QTest.mouseMove(window, veg, 10)
        for _ in range(8):
            qt_app.processEvents()
        assert slider.property("pressed") is True, "a csúszka elengedte a végpont előtt"
        assert abs(float(slider.property("value"))) >= 0.2
    finally:
        QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, veg)
        for _ in range(8):
            qt_app.processEvents()


def _kepterulet_toolbar_folott(image, toolbar) -> QRect:
    rect = _vezerlo_rect(image)
    rect.setHeight(max(1, _vezerlo_rect(toolbar).top() - rect.top()))
    # A fókuszkeret és a kép szélén lévő antialias pixelek nem részei a
    # képtartalom-összehasonlításnak.
    return rect.adjusted(3, 3, -3, -3)


def test_kiegyenesites_csempe_ujrakattintasa_visszarajzolja_a_mentett_kepet(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    """#4058: a csempe bezárása dobja el az előnézetet, mentés nélkül."""
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller, negyedes=True)
    _beallit_ablak(window, qt_app)
    viewer = _nezobe_lep(window, qt_app)
    photos = viewer.property("photosModel")
    edit_controller = viewer.property("editCtl")
    ini_path = tmp_path / "kepek" / ".picasa.ini"
    ini_elotte = ini_path.read_bytes() if ini_path.exists() else None
    thumb_elotte = _thumb_url_a_forrasbol(
        controller, photos, Path(str(controller.photos.filePathAt(0))), qt_app
    )
    image = _item(window, "viewerImage")

    _kattint(window, _item(window, "editToolTilt"), qt_app)
    assert _item(window, "viewerEditorPanel").property("tiltActive") is True
    grid = _item(window, "straightenGridOverlay")
    toolbar = _item(window, "editorToolBar")
    grid.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    kep_rect = _kepterulet_toolbar_folott(image, toolbar)
    nyitaskori_1 = _felvetel(window, tmp_path / "csempe-tilt-nyitva-1.png")
    nyitaskori_2 = _felvetel(window, tmp_path / "csempe-tilt-nyitva-2.png")
    zaj = _kulonbozo_pixelek(nyitaskori_1, nyitaskori_2, kep_rect)
    assert zaj == 0, f"a változatlan render zajszintje {zaj} képpont"
    grid.setProperty("visible", True)

    slider = _item(window, "tiltSlider")
    _tilt_huzasa_egerrel(window, qt_app, slider)
    grid.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    huzas_utan = _felvetel(window, tmp_path / "csempe-tilt-huzas-utan.png")
    huzas_diff = _kulonbozo_pixelek(nyitaskori_1, huzas_utan, kep_rect)
    assert huzas_diff > 0, "a valódi csúszkahúzás nem változtatta meg a kép kimenetét"
    grid.setProperty("visible", True)

    # rontás-kontroll: javítás nélkül ezen az úton 38 943 képpont tért el;
    # az eredeti fa bezárta az eszközt, de az előnézetet nem rajzolta vissza.
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    assert _item(window, "viewerEditorPanel").property("tiltActive") is False
    grid.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    csempe_utan = _felvetel(window, tmp_path / "csempe-tilt-bezaras-utan.png")
    csempe_diff = _kulonbozo_pixelek(nyitaskori_1, csempe_utan, kep_rect)

    ini_utana = ini_path.read_bytes() if ini_path.exists() else None
    assert edit_controller.property("chainValue") == ""
    assert edit_controller.property("undoAction") == ""
    assert edit_controller.property("redoAction") == ""
    assert photos.itemAt(0)["hasEdits"] is False
    assert photos.thumbUrlAt(0) == thumb_elotte
    assert ini_utana is None and ini_elotte is None
    assert csempe_diff == 0, (
        "a csempe újrakattintása után a kép előnézete nem állt vissza "
        f"(eltérő képpontok: {csempe_diff})"
    )


def test_kiegyenesites_aa_fokuszcsere_visszarajzolja_a_mentett_fokepet(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    """#4058: azonos láncú A/B-cserénél is frissüljön a főfél képe."""
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller, negyedes=True)
    _beallit_ablak(window, qt_app)
    viewer = _nezobe_lep(window, qt_app)
    photos = viewer.property("photosModel")
    edit_controller = viewer.property("editCtl")
    ini_path = tmp_path / "kepek" / ".picasa.ini"
    ini_elotte = ini_path.read_bytes() if ini_path.exists() else None
    thumb_elotte = _thumb_url_a_forrasbol(
        controller, photos, Path(str(controller.photos.filePathAt(0))), qt_app
    )
    panel = _item(window, "viewerEditorPanel")
    image_bal = _item(window, "viewerImageElotte")
    image_jobb = _item(window, "viewerImage")

    _kattint(window, _item(window, "viewerLayoutAa"), qt_app)
    assert viewer.property("layoutMode") == "aa"
    assert viewer.property("aaMunkamenet") is True

    # Kattintásos, húzás nélküli kontroll: ugyanabba a fókuszállapotba váltunk,
    # amelyben a húzás utáni képet mérjük. A keret így nem torzítja a mérést.
    _kattint(window, _item(window, "viewerSwapFocus"), qt_app)
    assert viewer.property("aktivOldal") == "jobb"
    cel_rect = _vezerlo_rect(image_jobb).adjusted(3, 3, -3, -3)
    fokusz_kontroll_1 = _felvetel(window, tmp_path / "aa-fokusz-kontroll-1.png")
    fokusz_kontroll_2 = _felvetel(window, tmp_path / "aa-fokusz-kontroll-2.png")
    zaj = _kulonbozo_pixelek(fokusz_kontroll_1, fokusz_kontroll_2, cel_rect)
    assert zaj == 0, f"az aa-változatlan render zajszintje {zaj} képpont"

    _kattint(window, _item(window, "viewerSwapFocus"), qt_app)
    assert viewer.property("aktivOldal") == "bal"
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    assert panel.property("tiltActive") is True
    grid = _item(window, "straightenGridOverlay")
    toolbar = _item(window, "editorToolBar")
    grid.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    bal_rect = _kepterulet_toolbar_folott(image_bal, toolbar)
    bal_eszkoz_nyitva = _felvetel(window, tmp_path / "aa-bal-eszkoz-nyitva.png")
    grid.setProperty("visible", True)

    _tilt_huzasa_egerrel(window, qt_app, _item(window, "tiltSlider"))
    grid.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    bal_huzas_utan = _felvetel(window, tmp_path / "aa-bal-huzas-utan.png")
    bal_huzas_diff = _kulonbozo_pixelek(bal_eszkoz_nyitva, bal_huzas_utan, bal_rect)
    assert bal_huzas_diff > 0, "az aa-fél képe nem változott a valódi húzásra"
    grid.setProperty("visible", True)

    # rontás-kontroll: javítás nélkül ezen az úton 16 082 képpont tért el;
    # az azonos mentett láncok miatt a swapAaFocus korai no-opja nem rajzolt.
    _kattint(window, _item(window, "viewerSwapFocus"), qt_app)
    assert panel.property("tiltActive") is False
    assert viewer.property("aktivOldal") == "jobb"
    fokusz_utan = _felvetel(window, tmp_path / "aa-fokuszcsere-utan.png")
    fokusz_diff = _kulonbozo_pixelek(fokusz_kontroll_1, fokusz_utan, cel_rect)

    ini_utana = ini_path.read_bytes() if ini_path.exists() else None
    assert edit_controller.property("chainValue") == ""
    assert edit_controller.property("undoAction") == ""
    assert edit_controller.property("redoAction") == ""
    assert photos.itemAt(0)["hasEdits"] is False
    assert photos.thumbUrlAt(0) == thumb_elotte
    assert ini_utana is None and ini_elotte is None
    assert fokusz_diff == 0, (
        "az aa-fókuszcsere után a főfél képe eltér a húzás nélküli "
        f"fókuszcsere kimenetétől (eltérő képpontok: {fokusz_diff})"
    )


def test_kiegyenesites_alkalmazasig_nem_ment_es_utana_visszavonhato(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    """Az Alkalmaz gomb mentse a csúszka elengedésekor még előnézeti értéket."""
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller, negyedes=True)
    _beallit_ablak(window, qt_app)
    viewer = _nezobe_lep(window, qt_app)
    edit_controller = viewer.property("editCtl")
    ini_path = tmp_path / "kepek" / ".picasa.ini"
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    # A QML Row csak az első kirajzoláskor rendezi át a frissen megjelent
    # csúszka/gomb sort. Képkocka nélkül a következő szintetikus lenyomás
    # még az előző helyén álló Mégse-gombot találhatja el.
    assert not window.grabWindow().isNull(), "a néző ablaka nem rajzolódott ki"
    slider = _item(window, "tiltSlider")
    _tilt_huzasa_egerrel(window, qt_app, slider)

    assert edit_controller.property("chainValue") == ""
    assert edit_controller.property("undoAction") == ""
    assert not ini_path.exists()

    _kattint(window, _item(window, "tiltApplyButton"), qt_app)
    assert edit_controller.property("chainValue").startswith("tilt=1,")
    assert edit_controller.property("undoAction") == "tilt"
    assert "filters=".encode() in ini_path.read_bytes()


def test_kiegyenesites_elonezet_elveszik_lapozaskor_es_bezaraskor(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    """A néző bezárása mentés nélkül dobja el a húzott tilt-előnézetet."""
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller, negyedes=True)
    _beallit_ablak(window, qt_app)
    viewer = _nezobe_lep(window, qt_app)
    photos = viewer.property("photosModel")
    edit_controller = viewer.property("editCtl")
    ini_path = tmp_path / "kepek" / ".picasa.ini"
    thumb_elotte = _thumb_url_a_forrasbol(
        controller, photos, Path(str(controller.photos.filePathAt(0))), qt_app
    )
    image = _item(window, "viewerImage")

    _kattint(window, _item(window, "editToolTilt"), qt_app)
    grid = _item(window, "straightenGridOverlay")
    toolbar = _item(window, "editorToolBar")
    grid.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    kep_rect = _kepterulet_toolbar_folott(image, toolbar)
    megnyitaskori = _felvetel(window, tmp_path / "tilt-nezo-bezaras-elott.png")
    grid.setProperty("visible", True)

    _tilt_huzasa_egerrel(window, qt_app, _item(window, "tiltSlider"))
    grid.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    huzas_utan = _felvetel(window, tmp_path / "tilt-nezo-bezaras-huzas-utan.png")
    assert _kulonbozo_pixelek(megnyitaskori, huzas_utan, kep_rect) > 0
    assert edit_controller.property("chainValue") == ""
    assert edit_controller.property("undoAction") == ""
    assert edit_controller.property("redoAction") == ""
    assert not ini_path.exists()

    viewer.setProperty("currentIndex", 1)
    for _ in range(8):
        qt_app.processEvents()
    assert viewer.property("currentIndex") == 1
    assert _item(window, "viewerEditorPanel").property("tiltActive") is False
    assert edit_controller.property("chainValue") == ""
    assert edit_controller.property("undoAction") == ""
    assert not ini_path.exists()

    viewer.setProperty("currentIndex", 0)
    for _ in range(8):
        qt_app.processEvents()
    assert viewer.property("currentIndex") == 0
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    grid.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    lapozas_utan = _felvetel(window, tmp_path / "tilt-lapozas-vissza-utan.png")
    lapozas_diff = _kulonbozo_pixelek(megnyitaskori, lapozas_utan, kep_rect)
    assert lapozas_diff == 0, (
        f"lapozás után az alkalmazatlan tilt-előnézet megmaradt ({lapozas_diff} eltérő képpont)"
    )
    assert edit_controller.property("chainValue") == ""
    assert edit_controller.property("undoAction") == ""
    assert edit_controller.property("redoAction") == ""
    assert not ini_path.exists()

    grid.setProperty("visible", True)
    _tilt_huzasa_egerrel(window, qt_app, _item(window, "tiltSlider"))
    grid.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    masodik_huzas = _felvetel(window, tmp_path / "tilt-bezaras-masodik-huzas.png")
    assert _kulonbozo_pixelek(megnyitaskori, masodik_huzas, kep_rect) > 0

    _kattint(window, _item(window, "viewerBackButton"), qt_app)
    assert window.property("viewerOpen") is False
    assert photos.itemAt(0)["hasEdits"] is False
    assert photos.thumbUrlAt(0) == thumb_elotte
    assert not ini_path.exists()

    _nezobe_lep(window, qt_app)
    assert _item(window, "viewerEditorPanel").property("tiltActive") is False
    grid.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    bezaras_utan = _felvetel(window, tmp_path / "tilt-nezo-bezaras-ujranyitas-utan.png")
    kep_diff = _kulonbozo_pixelek(megnyitaskori, bezaras_utan, kep_rect)

    assert kep_diff == 0, (
        f"a néző bezárása után az alkalmazatlan tilt-előnézet megmaradt ({kep_diff} eltérő képpont)"
    )
    assert edit_controller.property("chainValue") == ""
    assert edit_controller.property("undoAction") == ""
    assert edit_controller.property("redoAction") == ""
    assert photos.itemAt(0)["hasEdits"] is False
    assert not ini_path.exists()
