"""#4073 — a Kiegyenesítés sávformája renderelt pixeleken mérve.

Mérce: picasa-colab-jobs job-69, 4. kép. A PNG nincs a repóba másolva;
belőle a sáv 267×28 px mérete és a 7 px-es saroksugár lett kimérve.
A screenshoton a teljes sáv x=557…823, y=850…877; a felső határ
y=850-es pásztázásán x=561…563 között részleges, x=564-től teljes keretfedés
látszik; a sáv y=857-től a teljes x=557…823 szélességet használja. Az ív
képpontfedettségének illesztése a teljes szélességű szakaszhoz 7 px sugarat ad.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from PySide6.QtCore import QObject, QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
import pytest


ABLAK = (1280, 1029)
FOTO_MERET = 800
SAV_SZELESSEG = 267
SAV_MAGASSAG = 28
SAROKSUGAR = 7
ALFA = 206 / 255
KITOLTES = (80, 80, 80)
KERET = (203, 202, 202)
KITOLTES_RGB = (202, 213, 229)
JELOLO_RGB = (243, 245, 249)


def _color_patches(lib: Path) -> None:
    """A #4036 tesztjének 800×800-as, egyszínű mezőkből álló tesztfotója."""
    lilamezo = (119, 60, 140)
    sorok = (
        ((254, 0, 0), (0, 255, 1), (0, 0, 254), (255, 255, 0)),
        ((0, 255, 255), (255, 0, 254), (255, 255, 255), (0, 0, 0)),
        ((128, 128, 128), (200, 151, 121), (60, 90, 150), (91, 140, 59)),
        ((229, 200, 60), lilamezo, (240, 240, 240), (30, 30, 30)),
    )
    kep = Image.new("RGB", (FOTO_MERET, FOTO_MERET))
    festo = ImageDraw.Draw(kep)
    for y, sor in enumerate(sorok):
        for x, szin in enumerate(sor):
            festo.rectangle(
                (x * 200, y * 200, (x + 1) * 200 - 1, (y + 1) * 200 - 1),
                fill=szin,
            )
    kep.save(lib / "color_patches.jpg", "JPEG", quality=100, subsampling=0)


def _item(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a valódi főablakban"
    return elem


def _ablak_meretezese(window, qt_app, magassag: int, szelesseg: int = ABLAK[0]) -> None:
    window.setProperty("width", szelesseg)
    window.setProperty("height", magassag)
    for _ in range(5):
        qt_app.processEvents()


def _egyes_nezetre_hangol(window, qt_app) -> None:
    foto = _item(window, "viewerImage")
    for _ in range(4):
        elteres = float(foto.property("paintedWidth")) - FOTO_MERET
        if abs(elteres) <= 1:
            return
        window.setProperty("height", round(float(window.property("height")) - elteres))
        for _ in range(8):
            qt_app.processEvents()


def _kattint(window, elem, qt_app) -> None:
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    for _ in range(5):
        qt_app.processEvents()


def _rgb(kep: QImage, x: int, y: int) -> tuple[int, int, int]:
    szin = kep.pixelColor(x, y)
    return szin.red(), szin.green(), szin.blue()


def _rgb_tomb(kep: QImage) -> np.ndarray:
    rgb = kep.convertToFormat(QImage.Format.Format_RGB888)
    adat = np.frombuffer(
        rgb.constBits(),
        dtype=np.uint8,
        count=rgb.bytesPerLine() * rgb.height(),
    )
    return adat.reshape(rgb.height(), rgb.bytesPerLine())[:, : rgb.width() * 3].reshape(
        rgb.height(), rgb.width(), 3
    ).copy()


def _vezerlo_rect(elem) -> QRect:
    bal_felso = elem.mapToScene(QPointF(0, 0))
    return QRect(
        round(bal_felso.x()),
        round(bal_felso.y()),
        round(elem.width()),
        round(elem.height()),
    )


def _pont_scene(elem, x: float, y: float) -> QPoint:
    pont = elem.mapToScene(QPointF(x, y))
    return QPoint(round(pont.x()), round(pont.y()))


def _kulonbozo_pixelek(egy: QImage, ketto: QImage, rect: QRect) -> int:
    return sum(
        egy.pixelColor(x, y) != ketto.pixelColor(x, y)
        for y in range(rect.top(), rect.bottom() + 1)
        for x in range(rect.left(), rect.right() + 1)
    )


def _fedettseg(
    aktiv: QImage,
    rejtett: QImage,
    x: int,
    y: int,
    teljes_x: int,
    szin: tuple[int, int, int],
) -> float:
    """A teljes réteghez képest mért pixelfedettség a rejtett képből."""
    alap = np.asarray(_rgb(rejtett, x, y), dtype=np.float64)
    kapott = np.asarray(_rgb(aktiv, x, y), dtype=np.float64) - alap
    referencia_alap = np.asarray(_rgb(rejtett, teljes_x, y), dtype=np.float64)
    referencia_valtozas = np.asarray(_rgb(aktiv, teljes_x, y), dtype=np.float64)
    referencia_valtozas -= referencia_alap
    szin_np = np.asarray(szin, dtype=np.float64)
    referencia_teljes = szin_np - referencia_alap
    referencia_negyzet = float(np.dot(referencia_teljes, referencia_teljes))
    assert referencia_negyzet > 100, f"a {teljes_x},{y} pixelből nem mérhető a kitöltés"
    teljes_alfa = float(np.dot(referencia_valtozas, referencia_teljes) / referencia_negyzet)
    teljes = (szin_np - alap) * teljes_alfa
    teljes_negyzet = float(np.dot(teljes, teljes))
    assert teljes_negyzet > 100, f"a {x},{y} pixelből nem mérhető a fedettség"
    return float(np.dot(kapott, teljes) / teljes_negyzet)


def _pixelfutasok(maszk: np.ndarray, max_hezag: int = 2) -> list[tuple[int, int]]:
    """Összefüggő futások; legfeljebb `max_hezag` képpontnyi rés nem szakítja meg.

    A gombfeliratok betűi (platformfüggő betűtípus, élsimítás) a gomb közepén
    1-2 képpontos lyukat hagyhatnak a változásmaszkban; a valódi köz a sáv és
    a gomb között 11, a két gomb között 5 képpont."""
    xs = np.flatnonzero(maszk)
    if not len(xs):
        return []
    futasok = []
    kezdet = elozo = int(xs[0])
    for x in xs[1:]:
        x = int(x)
        if x > elozo + 1 + max_hezag:
            futasok.append((kezdet, elozo + 1))
            kezdet = x
        elozo = x
    futasok.append((kezdet, elozo + 1))
    return futasok


def test_a_pixelfutas_a_felirat_okozta_kis_hezagot_atugorja_a_valodi_kozt_nem():
    maszk = np.zeros(40, dtype=bool)
    maszk[2:12] = True  # elem
    maszk[14:20] = True  # 2 képpontos rés után folytatódik: ugyanaz az elem
    maszk[26:36] = True  # 6 képpontos rés: új elem
    assert _pixelfutasok(maszk) == [(2, 20), (26, 36)]
    assert _pixelfutasok(maszk, max_hezag=0) == [(2, 12), (14, 20), (26, 36)]


def _eszkozsav_pixeles_meresei(aktiv: QImage, rejtett: QImage) -> dict[str, object]:
    """A sávot és a gombokat a valódi főablak két renderelt képéből méri."""
    aktiv_rgb = _rgb_tomb(aktiv)
    rejtett_rgb = _rgb_tomb(rejtett)
    valtozott = np.max(
        np.abs(aktiv_rgb.astype(np.int16) - rejtett_rgb.astype(np.int16)), axis=2
    ) > 4

    # A legnagyobb változású sor az eszközsáv képpontjain fut keresztül; itt
    # mindhárom lekerekített elem eléri a teljes szélességét.
    sorszamok = valtozott.sum(axis=1)
    max_sorszam = int(sorszamok.max())
    maximalis_sorok = np.flatnonzero(sorszamok == max_sorszam)
    sor = int(maximalis_sorok[len(maximalis_sorok) // 2])
    futasok = _pixelfutasok(valtozott[sor])
    assert len(futasok) == 3, (
        f"a renderelt eszközsáv középső sorában három külön képpontfutást "
        f"vártunk, ezeket mértük: {futasok}"
    )
    savon, alkalmaz, megse = futasok

    # A középállású fogantyú világos pixelei a sötét, áttetsző sáv fölött
    # különülnek el. A teljes, kivágott 24 px magas belső sorozaton mérjük,
    # hogy egy-egy fotó-/rácspixel ne tolja el a középpontot.
    oldalpontok = np.any(
        valtozott[:, savon[0] : savon[0] + 18]
        | valtozott[:, savon[1] - 18 : savon[1]],
        axis=1,
    )
    y_pontok = np.flatnonzero(oldalpontok)
    y0, y1 = int(y_pontok[0]) + 2, int(y_pontok[-1]) - 1
    fogantyu_regio = aktiv_rgb[y0:y1, savon[0] : savon[1]]
    szurke_fenyes = (fogantyu_regio.min(axis=2) >= 175) & (
        fogantyu_regio.max(axis=2) - fogantyu_regio.min(axis=2) <= 40
    )
    fogantyu_oszlopok = np.flatnonzero(szurke_fenyes.sum(axis=0) >= 6)
    assert len(fogantyu_oszlopok), "a középen álló fogantyú világos képpontjai nem találhatók"
    fogantyu_kozepe = (
        savon[0] + fogantyu_oszlopok[0] + savon[0] + fogantyu_oszlopok[-1] + 1
    ) / 2

    return {
        "sor": sor,
        "sav": savon,
        "alkalmaz": alkalmaz,
        "megse": megse,
        "sav_alkalmaz_res": alkalmaz[0] - savon[1],
        "savtol_alkalmaz": alkalmaz[0] - savon[0],
        "teljes_sor": megse[1] - savon[0],
        "fogantyu_kozepe": fogantyu_kozepe,
    }


def _foto_bal_szele_pixelegbol(kep: QImage, foto_item) -> int:
    """A szintetikus fotó vörös mezőjének bal szélét keresi a renderelt soron."""
    kezdet = foto_item.mapToScene(QPointF(0, 0))
    y = round(kezdet.y() + 100)
    rgb = _rgb_tomb(kep)
    sor = rgb[y]
    voros = np.flatnonzero(
        (sor[:, 0] > 180) & (sor[:, 1] < 40) & (sor[:, 2] < 40)
    )
    assert len(voros), "a renderelt fotó vörös mezője nem található"
    return int(voros[0])


def _sarok_kivagasok(
    aktiv: QImage, rejtett: QImage, sav: tuple[int, int]
) -> tuple[tuple[int, ...], tuple[tuple[int, ...], ...]]:
    """A négy lekerekített sarok pixelmaszkjának hiányzó területét méri."""
    aktiv_rgb = _rgb_tomb(aktiv)
    rejtett_rgb = _rgb_tomb(rejtett)
    valtozott = np.max(
        np.abs(aktiv_rgb.astype(np.int16) - rejtett_rgb.astype(np.int16)), axis=2
    ) > 4
    bal, jobb = sav
    sarokszelesseg = 18
    oldalpontok = np.any(
        valtozott[:, bal : bal + sarokszelesseg]
        | valtozott[:, jobb - sarokszelesseg : jobb],
        axis=1,
    )
    ys = np.flatnonzero(oldalpontok)
    assert len(ys), "a renderelt sáv sarkai nem találhatók a képen"
    fent, lent = int(ys[0]), int(ys[-1]) + 1

    sarokmeret = 8
    dobozok = (
        (bal, fent),
        (jobb - sarokmeret, fent),
        (bal, lent - sarokmeret),
        (jobb - sarokmeret, lent - sarokmeret),
    )
    hianyok = tuple(
        sarokmeret**2
        - int(valtozott[y : y + sarokmeret, x : x + sarokmeret].sum())
        for x, y in dobozok
    )

    profilok = []
    for felul in (True, False):
        y0 = fent if felul else lent - 1
        lepes = 1 if felul else -1
        balprofil = []
        jobbprofil = []
        for sorindex in range(sarokmeret):
            y = y0 + lepes * sorindex
            balxs = np.flatnonzero(valtozott[y, bal : bal + sarokszelesseg])
            jobbxs = np.flatnonzero(valtozott[y, jobb - sarokszelesseg : jobb])
            assert len(balxs) and len(jobbxs), "hiányos sarokpixel-profilt mértünk"
            balprofil.append(int(balxs[0]))
            jobbprofil.append(int(sarokszelesseg - 1 - jobbxs[-1]))
        profilok.extend((tuple(balprofil), tuple(jobbprofil)))
    return hianyok, tuple(profilok)


def _kompozit(hatter, eloter, alfa: float) -> tuple[int, int, int]:
    return tuple(round(h * (1 - alfa) + e * alfa) for h, e in zip(hatter, eloter, strict=True))


def _lekerekitett_pont_benne(
    x: float, y: float, szelesseg: float, magassag: float, sugar: float
) -> bool:
    cx = min(max(x, sugar), szelesseg - sugar)
    cy = min(max(y, sugar), magassag - sugar)
    return (x - cx) ** 2 + (y - cy) ** 2 <= sugar**2


def _masik_csuszka_pixelei(kep: QImage, csuszka) -> tuple[tuple[int, int, int], ...]:
    """A Derítőfény csúszkájának kitöltése és középső jelölője a képen."""
    kezdet = csuszka.mapToScene(QPointF(0, 0))
    szelesseg = round(csuszka.width())
    x_kitoltes = round(szelesseg / 4)
    x_jelolo = round(1 + 0.5 * (szelesseg - 3))
    y_kozep = math.floor(kezdet.y() + csuszka.height() / 2)
    return (
        _rgb(kep, math.floor(kezdet.x()) + x_kitoltes, y_kozep),
        _rgb(kep, math.floor(kezdet.x()) + x_jelolo, y_kozep),
    )


def _sav_pixel_eltetesek(
    kep: QImage,
    foto: Image.Image,
    racs: Image.Image,
    roi_kezdete: QPointF,
    foto_kezdete: QPointF,
    racs_kezdete: QPointF,
    fogantyu,
) -> tuple[int, int, list[str]]:
    """A referencia alakjának pixeleit veti össze a főablak renderelt képével."""
    hibak: list[str] = []
    fogantyu_kezdet = fogantyu.mapToScene(QPointF(0, 0))
    fogantyu_teglalap = (
        fogantyu_kezdet.x() - 3,
        fogantyu_kezdet.y() - 3,
        fogantyu_kezdet.x() + fogantyu.width() + 4,
        fogantyu_kezdet.y() + fogantyu.height() + 5,
    )
    vizsgalt = hibas = 0

    for y in range(SAV_MAGASSAG):
        for x in range(SAV_SZELESSEG):
            px, py = x + 0.5, y + 0.5
            sx = math.floor(roi_kezdete.x() + px)
            sy = math.floor(roi_kezdete.y() + py)
            if (
                fogantyu_teglalap[0] <= sx < fogantyu_teglalap[2]
                and fogantyu_teglalap[1] <= sy < fogantyu_teglalap[3]
            ):
                continue

            benne = _lekerekitett_pont_benne(
                px, py, SAV_SZELESSEG, SAV_MAGASSAG, SAROKSUGAR
            )
            belso = _lekerekitett_pont_benne(
                px - 2,
                py - 2,
                SAV_SZELESSEG - 4,
                SAV_MAGASSAG - 4,
                SAROKSUGAR - 2,
            )

            # Az élsimított határon és annak közvetlen szomszédján a
            # raszterező platformonként eltérhet; a belső és külső pixelek
            # viszont a képpontos geometriát mérik.
            outer_edge = any(
                _lekerekitett_pont_benne(
                    px + dx,
                    py + dy,
                    SAV_SZELESSEG,
                    SAV_MAGASSAG,
                    SAROKSUGAR,
                )
                != benne
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            inner_edge = any(
                _lekerekitett_pont_benne(
                    px - 2 + dx,
                    py - 2 + dy,
                    SAV_SZELESSEG - 4,
                    SAV_MAGASSAG - 4,
                    SAROKSUGAR - 2,
                )
                != belso
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            if outer_edge or (benne and inner_edge):
                continue

            foto_x = math.floor(roi_kezdete.x() + px - foto_kezdete.x())
            foto_y = math.floor(roi_kezdete.y() + py - foto_kezdete.y())
            if not (0 <= foto_x < foto.width and 0 <= foto_y < foto.height):
                continue
            if foto_x % 200 < 8 or foto_x % 200 > 191:
                continue
            if foto_y % 200 < 8 or foto_y % 200 > 191:
                continue

            racs_x = math.floor(roi_kezdete.x() + px - racs_kezdete.x()) % racs.width
            racs_y = math.floor(roi_kezdete.y() + py - racs_kezdete.y()) % racs.height
            racs_rgb = racs.getpixel((racs_x, racs_y))
            alap = foto.getpixel((foto_x, foto_y))
            if racs_rgb[3]:
                alap = _kompozit(alap, racs_rgb[:3], racs_rgb[3] / 255)

            if not benne:
                vart = alap
            elif belso:
                vart = _kompozit(alap, KITOLTES, ALFA)
            else:
                vart = _kompozit(alap, KERET, ALFA)

            kapott = _rgb(kep, sx, sy)
            vizsgalt += 1
            if max(abs(a - b) for a, b in zip(kapott, vart, strict=True)) > 5:
                hibas += 1
                if len(hibak) < 5:
                    hibak.append(f"({x},{y}) pixel {kapott}, várt {vart}")

    return hibas, vizsgalt, hibak


@pytest.fixture
def qml_app_color_patches(qt_app, tmp_path):
    from tests.app.qml_functional.conftest import _build_qml_app

    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_color_patches)


def test_a_kiegyenesites_savja_a_referencia_alakjat_rajzolja_pixelekbol(
    qml_app_color_patches, qt_app, tmp_path
):
    """Offscreen főablak-kimenet; a sávot nem QML-méretekből ellenőrzi."""
    window, controller, _engine = qml_app_color_patches
    _ablak_meretezese(window, qt_app, ABLAK[1])
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    window.setProperty("viewerOpen", True)
    for _ in range(8):
        qt_app.processEvents()
    _kattint(window, _item(window, "editTabFixes"), qt_app)

    # Szomszéd-regresszió: a Derítőfény sávkitöltése és középső jelölője a
    # renderelt képen maradjon a PicasaSlider alapértelmezett színén.
    masik_csuszka = _item(window, "fixesFillSlider")
    kep_elotte = window.grabWindow()
    masik_pixelek = _masik_csuszka_pixelei(kep_elotte, masik_csuszka)
    assert masik_pixelek == (KITOLTES_RGB, JELOLO_RGB), (
        f"a Derítőfény renderelt pixelei megváltoztak: {masik_pixelek}"
    )

    _kattint(window, _item(window, "editToolTilt"), qt_app)
    racs_utvonal = (
        Path(__file__).resolve().parents[3]
        / "src/picasapy/app/assets/tools/straighten_grid.png"
    )
    racs = Image.open(racs_utvonal).convert("RGBA")
    foto = Image.open(controller.photos.filePathAt(0)).convert("RGB")
    foto_item = _item(window, "viewerImage")
    racs_item = _item(window, "straightenGridImage")
    kontener = _item(window, "toolSliderContainer")
    slider = _item(window, "tiltSlider")
    eszkozsav = _item(window, "editorToolBar")
    fogantyu = slider.property("handle")
    assert fogantyu is not None

    # A referencia-fit ablakmagasság körüli ±5 px induló eltérésen is
    # renderelünk; a helper a kép 1:1 méretét utána a nézetben visszaállítja.
    for indulasi_eltolas in (-5, 0, 5):
        _ablak_meretezese(window, qt_app, ABLAK[1] + indulasi_eltolas)
        _egyes_nezetre_hangol(window, qt_app)
        kep = window.grabWindow()
        assert not kep.isNull(), "a valódi főablak képe nem rajzolódott ki"
        assert kep.devicePixelRatio() == pytest.approx(1)
        if indulasi_eltolas == 0:
            assert kep.save(str(tmp_path / "picasapy-4073-now.png"), "PNG")

        # A vezérlősor pixelhatárait a látható és az áttetszőre rejtett
        # eszközsáv renderelt képének különbségéből mérjük. A QML-geometria
        # nem szolgál x-koordinátaként vagy szélességként.
        eszkozsav.setProperty("opacity", 0.0)
        for _ in range(5):
            qt_app.processEvents()
        alap_kep = window.grabWindow()
        eszkozsav.setProperty("opacity", 1.0)
        for _ in range(5):
            qt_app.processEvents()
        sor_meres = _eszkozsav_pixeles_meresei(kep, alap_kep)
        sarok_hiany, sarokprofilok = _sarok_kivagasok(
            kep, alap_kep, sor_meres["sav"]
        )
        foto_bal = _foto_bal_szele_pixelegbol(kep, foto_item)
        foto_kozep = foto_bal + FOTO_MERET / 2

        savon = sor_meres["sav"]
        alkalmaz = sor_meres["alkalmaz"]
        megse = sor_meres["megse"]
        print(
            f"#4073 pixelmérés ({indulasi_eltolas:+d}px): "
            f"fotóbal={foto_bal}, fotóközép={foto_kozep:.1f}; "
            f"sáv={savon}, Alkalmaz={alkalmaz}, Mégse={megse}; "
            f"fogantyúközép={sor_meres['fogantyu_kozepe']:.1f}; "
            f"rés={sor_meres['sav_alkalmaz_res']}, "
            f"Alkalmaz-sávtávolság={sor_meres['savtol_alkalmaz']}, "
            f"teljes sor={sor_meres['teljes_sor']}; "
            f"sarokhiány={sarok_hiany}, sarokprofil={sarokprofilok}"
        )
        assert savon[1] - savon[0] == SAV_SZELESSEG
        assert alkalmaz[1] - alkalmaz[0] == 82
        assert megse[1] - megse[0] == 82
        bal_sarkok_hianya = sarok_hiany[0] + sarok_hiany[2]
        jobb_sarkok_hianya = sarok_hiany[1] + sarok_hiany[3]
        assert 11 <= bal_sarkok_hianya <= 14 and 14 <= jobb_sarkok_hianya <= 18, (
            f"a renderelt sáv négy sarkának hiányzó területe {sarok_hiany}, "
            f"oldalanként {bal_sarkok_hianya}/{jobb_sarkok_hianya} px²; "
            "ez nem illik a referencia 7,0–7,5 px-es ívéhez"
        )
        assert abs(sor_meres["sav_alkalmaz_res"] - 11) <= 1, (
            f"a renderelt sáv és Alkalmaz közötti rés "
            f"{sor_meres['sav_alkalmaz_res']} px; a referencia 11±1 px"
        )
        assert abs(sor_meres["savtol_alkalmaz"] - 278) <= 1, (
            f"Alkalmaz bal széle {sor_meres['savtol_alkalmaz']} px-re van a "
            "sáv bal szélétől; a referencia 278±1 px"
        )
        assert sor_meres["megse"][0] - sor_meres["alkalmaz"][1] == 5
        assert sor_meres["teljes_sor"] == 447
        assert abs(
            sor_meres["fogantyu_kozepe"] - savon[0] - 133.5
        ) <= 1, "a fogantyú közepe elmozdult a sáv közepéhez képest"

        foto_szel = float(foto_item.property("paintedWidth"))
        foto_mag = float(foto_item.property("paintedHeight"))
        assert (foto_szel, foto_mag) == pytest.approx((FOTO_MERET, FOTO_MERET), abs=1)
        foto_kezdete = foto_item.mapToScene(
            QPointF(
                (foto_item.width() - foto_szel) / 2,
                (foto_item.height() - foto_mag) / 2,
            )
        )
        roi_kezdete = kontener.mapToScene(QPointF(0, 0))
        racs_kezdete = racs_item.mapToScene(QPointF(0, 0))
        hibas, vizsgalt, elso_hibak = _sav_pixel_eltetesek(
            kep,
            foto,
            racs,
            roi_kezdete,
            foto_kezdete,
            racs_kezdete,
            fogantyu,
        )
        assert vizsgalt >= 1000, f"kevés sávképpontot mértünk: {vizsgalt}"
        assert hibas == 0, (
            f"a {indulasi_eltolas:+d} px ablakeltolásnál a renderelt sáv "
            f"{hibas}/{vizsgalt} képpontja tér el a job-69 4. kép 267×28 px, "
            f"7 px sugarú lekerekített téglalapjától; példák: {elso_hibak}"
        )


def test_a_sav_es_az_alkalmaz_kozti_res_rogzitett_ablakmagassagokon_pixeles(
    qml_app_color_patches, qt_app
):
    """A sor réstávolsága a renderelt képen három rögzített magasságon."""
    window, _controller, _engine = qml_app_color_patches
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    window.setProperty("viewerOpen", True)
    for _ in range(8):
        qt_app.processEvents()
    _kattint(window, _item(window, "editTabFixes"), qt_app)
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    eszkozsav = _item(window, "editorToolBar")

    # Ezeket a magasságokat az eszközsávteszt is külön-külön méri; itt nincs
    # kép-fit visszaigazítás az ablakméret-váltások után.
    for magassag in (1019, 1029, 1039):
        _ablak_meretezese(window, qt_app, magassag)
        aktiv = window.grabWindow()
        eszkozsav.setProperty("opacity", 0.0)
        for _ in range(5):
            qt_app.processEvents()
        rejtett = window.grabWindow()
        eszkozsav.setProperty("opacity", 1.0)
        for _ in range(5):
            qt_app.processEvents()

        meres = _eszkozsav_pixeles_meresei(aktiv, rejtett)
        assert meres["sav"][1] - meres["sav"][0] == 267
        assert meres["alkalmaz"][1] - meres["alkalmaz"][0] == 82
        assert meres["megse"][1] - meres["megse"][0] == 82
        assert abs(meres["sav_alkalmaz_res"] - 11) <= 1, (
            f"{magassag}px-es ablakban a sáv és Alkalmaz közti rés "
            f"{meres['sav_alkalmaz_res']} px; a referencia 11±1 px"
        )
        assert abs(meres["savtol_alkalmaz"] - 278) <= 1
        assert meres["megse"][0] - meres["alkalmaz"][1] == 5
        assert meres["teljes_sor"] == 447


def test_ablakszelesseg_sweepben_egesz_pixeles_a_sor_es_nem_szivarog_at_a_racs(
    qml_app_color_patches, qt_app
):
    """Képpontból méri a 447 px-es sort, az éleket és a gombpár rácsmaszkját."""
    window, _controller, _engine = qml_app_color_patches
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    window.setProperty("viewerOpen", True)
    for _ in range(8):
        qt_app.processEvents()
    _kattint(window, _item(window, "editTabFixes"), qt_app)
    _kattint(window, _item(window, "editToolTilt"), qt_app)

    toolbar = _item(window, "editorToolBar")
    slider = _item(window, "tiltSlider")
    overlay = _item(window, "straightenGridOverlay")
    apply = _item(window, "tiltApplyButton")
    cancel = _item(window, "tiltCancelButton")
    eredmenyek = []

    for szelesseg in (1279, 1280, 1281, 1282, 1283):
        _ablak_meretezese(window, qt_app, ABLAK[1], szelesseg)
        aktiv = window.grabWindow()
        toolbar.setProperty("opacity", 0.0)
        for _ in range(5):
            qt_app.processEvents()
        rejtett = window.grabWindow()
        toolbar.setProperty("opacity", 1.0)
        for _ in range(5):
            qt_app.processEvents()

        meres = _eszkozsav_pixeles_meresei(aktiv, rejtett)
        savon, alkalmaz, megse = meres["sav"], meres["alkalmaz"], meres["megse"]
        szelhibak = []
        el_fedettsegek = []
        for nev, tartomany in (("sáv", savon), ("Alkalmaz", alkalmaz), ("Mégse", megse)):
            for x, teljes_x in (
                (tartomany[0], tartomany[0] + 1),
                (tartomany[1] - 1, tartomany[1] - 2),
            ):
                fedettseg = _fedettseg(
                    aktiv, rejtett, x, meres["sor"], teljes_x, KERET
                )
                el_fedettsegek.append(fedettseg)
                if not 0.92 <= fedettseg <= 1.08:
                    szelhibak.append(f"{nev} x={x}: fedettség={fedettseg:.2f}, várt 1,00")
            for x in (tartomany[0] - 1, tartomany[1]):
                if _rgb(aktiv, x, meres["sor"]) != _rgb(rejtett, x, meres["sor"]):
                    szelhibak.append(f"{nev} külső x={x} oszlopa részben fedett")

        QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                         _pont_scene(slider, slider.width() / 2, slider.height() / 2))
        QTest.mouseMove(
            window,
            _pont_scene(slider, slider.width() * 0.78, slider.height() / 2),
            10,
        )
        for _ in range(8):
            qt_app.processEvents()
        assert slider.property("pressed") is True, f"{szelesseg}px-nél nem indult el a húzás"

        overlay.setProperty("visible", False)
        for _ in range(5):
            qt_app.processEvents()
        racs_nelkul = window.grabWindow()
        overlay.setProperty("visible", True)
        for _ in range(8):
            qt_app.processEvents()
        racsos = window.grabWindow()
        gombpar = _vezerlo_rect(apply).united(_vezerlo_rect(cancel))
        szivargas = _kulonbozo_pixelek(racsos, racs_nelkul, gombpar)
        QTest.mouseRelease(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _pont_scene(slider, slider.width() * 0.78, slider.height() / 2),
        )
        for _ in range(5):
            qt_app.processEvents()

        eredmenyek.append(
            {
                "ablak": szelesseg,
                "res": meres["sav_alkalmaz_res"],
                "sor": meres["teljes_sor"],
                "el-fedettsegek": tuple(round(x, 2) for x in el_fedettsegek),
                "elek": tuple(szelhibak),
                "racs-szivargas": szivargas,
            }
        )

    print("#4073 ablakszélesség-sweep (ablak → rés, sor, élfedettségek, rácsszivárgás):")
    for adat in eredmenyek:
        print(
            f"  {adat['ablak']} → {adat['res']} px, {adat['sor']} px, "
            f"{adat['el-fedettsegek']}, {adat['racs-szivargas']} px; "
            f"élhibák={adat['elek']}"
        )
    hibak = [
        adat
        for adat in eredmenyek
        if adat["res"] != 11 or adat["sor"] != 447 or adat["elek"] or adat["racs-szivargas"]
    ]
    assert not hibak, f"a renderelt sáv/gombsor nem egész pixeles minden szélességen: {hibak}"


# rontás-kontroll: 253×28 px-es, 14 px sugarú, három jelölővonalas háttérrel a
# renderelt régióőrzőnek a javítás nélkül el kell buknia; ez tényleges
# képpont-összevetés, nem QML-tulajdonságot mérő vagy pusztán számozó őr.
