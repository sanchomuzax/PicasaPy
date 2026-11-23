"""#7389: Képi összevetés — nyitott effekt-paraméterpanel mellett a Kép menü
és a Csoportos szerkesztés almenü tételeinek renderelt letiltott (szürke) színe,
valamint a panel bezárása utáni aktív színe.

Specifikáció: docs/specs/paritas-folyamat-7346.md T7 (#7389).
Eredeti felvétel: job-878 #15 és #17 (Picasa 3.9, Soft Focus nyitva, Kép menü legördítve).
Kimenet: .tmp/osszevetes_7389.png összehasonlító kép.
"""

from __future__ import annotations

import pathlib
from PIL import Image, ImageDraw
import pytest
from PySide6.QtCore import QObject, QPointF

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    varj,
    zar,
)
from tests.app.qml_functional._szerkeszto_5150_helpers import item, kattint
from tests.app.qml_functional.test_kep_menu_parameterpanel_7389 import (
    _kezdo_allapot,
    _kep_menut_nyit,
)


@pytest.fixture
def kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _qimage_to_pil(qimg) -> Image.Image:
    """QImage átalakítása PIL Image-re."""
    buffer = qimg.bits().tobytes()
    return Image.frombuffer(
        "RGBA",
        (qimg.width(), qimg.height()),
        buffer,
        "raw",
        "BGRA",
        qimg.bytesPerLine(),
        1,
    ).convert("RGB")


def _menu_doboz_kivagasa(window, menu, grab_img: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """A Kép menü és fejléce geometriájának platformfüggetlen kivágása."""
    menu_bar = window.property("menuBar")
    fejlec = next(
        elem
        for elem in menu_bar.findChildren(QObject)
        if "MenuBarItem" in elem.metaObject().className()
        and elem.property("text") in {"&Picture", "&Kép"}
    )
    fejlec_pos = fejlec.mapToScene(QPointF(0, 0))
    x0 = max(0, int(round(fejlec_pos.x())) - 2)
    y0 = max(0, int(round(fejlec_pos.y())))
    menu_w = int(round(menu.property("width")))
    menu_h = int(round(menu.property("height")))
    x1 = min(grab_img.width, x0 + menu_w + 10)
    y1 = min(grab_img.height, y0 + int(round(fejlec.height())) + menu_h + 10)
    crop = grab_img.crop((x0, y0, x1, y1))
    return crop, (x0, y0, x1, y1)


def _sorok_minimalis_luminanciaja(crop_img: Image.Image, y_start: int, y_end: int, x_start: int, x_end: int) -> list[int]:
    """Soronkénti legsötétebb pixelek luminanciája a menü szövegterületén."""
    mins = []
    for y in range(y_start, min(crop_img.height, y_end), 5):
        row = [crop_img.getpixel((x, y)) for x in range(x_start, min(crop_img.width, x_end))]
        if row:
            mins.append(min(sum(p[:3]) // 3 for p in row))
    return mins


class TestKepMenuRender7389:
    @pytest.mark.parametrize("magassag_offset", [-5, 0, 5])
    def test_kep_menu_render_szurke_es_aktiv_szin_osszevetes(
        self, kep_app, qt_app, magassag_offset: int
    ):
        """Renderelt próba ±5 px ablakmagasság-eltolással:
        1. Nyitott Soft Focus panel mellett a Kép menü legördítve, grabWindow mentés.
        2. A menü hét tételének felirata szürke (letiltott) színnel rajzolódik.
        3. A panel bezárása után újra legördítve aktív (sötét) színnel rajzolódik.
        4. Az összevető kép mentése a .tmp/osszevetes_7389.png fájlba (offset=0 esetén).
        """
        window, _controller, panel, _szerk = _kezdo_allapot(kep_app, qt_app)

        if magassag_offset != 0:
            window.setHeight(window.height() + magassag_offset)
            qt_app.processEvents()

        # 1. Soft Focus paraméterpanel megnyitása
        kattint(window, item(window, "effectRadblur"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is True)

        # Kép menü legördítése nyitott panel mellett
        menu_szurke = _kep_menut_nyit(window, qt_app)
        grab_szurke_q = window.grabWindow()
        assert not grab_szurke_q.isNull(), "a letiltott menü grabWindow-ja érvénytelen"
        pil_szurke = _qimage_to_pil(grab_szurke_q)
        crop_szurke, _bbox_szurke = _menu_doboz_kivagasa(window, menu_szurke, pil_szurke)
        zar(qt_app, menu_szurke)

        # 2. Panel bezárása Mégse gombbal
        kattint(window, item(window, "effectParamCancelButton"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is False)

        # Kép menü legördítése bezárt panel mellett (aktív állapot)
        menu_aktiv = _kep_menut_nyit(window, qt_app)
        grab_aktiv_q = window.grabWindow()
        assert not grab_aktiv_q.isNull(), "az aktív menü grabWindow-ja érvénytelen"
        pil_aktiv = _qimage_to_pil(grab_aktiv_q)
        crop_aktiv, _bbox_aktiv = _menu_doboz_kivagasa(window, menu_aktiv, pil_aktiv)
        zar(qt_app, menu_aktiv)

        # 3. Színmérés:
        # A fejléc alatt a menütételek magja x: 30..150, y: 35..crop.height - 10
        min_szurke = _sorok_minimalis_luminanciaja(crop_szurke, 35, crop_szurke.height - 10, 30, 160)
        min_aktiv = _sorok_minimalis_luminanciaja(crop_aktiv, 35, crop_aktiv.height - 10, 30, 160)

        # Szürke (letiltott) állapotban a szövegek sosem érnek el fekete/sötét színt:
        # a legsötétebb pixel luminanciája > 90 (mért érték: ~120-135).
        # Tűréssel: legalább 80.
        abszolút_min_szurke = min(min_szurke)
        assert abszolút_min_szurke >= 80, (
            f"a letiltott menüben túl sötét pixel található (lum={abszolút_min_szurke}), nem szürke"
        )

        # Aktív állapotban a legördülő menü aktív sorainak szövege fekete/nagyon sötét:
        # a legsötétebb pixel luminanciája < 65 (mért érték: ~30-35).
        abszolút_min_aktiv = min(min_aktiv)
        assert abszolút_min_aktiv <= 65, (
            f"az aktív menüben a szöveg nem rajzolódott ki sötét színnel (lum={abszolút_min_aktiv})"
        )

        # Jelentős különbség a két állapot között
        assert abszolút_min_szurke - abszolút_min_aktiv >= 40, (
            "a szürke és aktív menüszöveg között nincs mérhető színkülönbség"
        )

        # 4. Összevető kép mentése a .tmp/osszevetes_7389.png-be (alap magasságnál)
        if magassag_offset == 0:
            tmp_dir = pathlib.Path(__file__).resolve().parents[3] / ".tmp"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            osszevetes_fajl = tmp_dir / "osszevetes_7389.png"

            p15 = tmp_dir / "job-878/kepernyo__15.png"
            p17 = tmp_dir / "job-878/kepernyo__17.png"

            if p15.exists() and p17.exists():
                im15 = Image.open(p15)
                im17 = Image.open(p17)
                # Eredeti menü kivágása (job-878 menü bbox: 137, 20, 290, 192)
                orig_crop15 = im15.crop((130, 0, 300, 200))
                orig_crop17 = im17.crop((130, 0, 300, 200))

                w_orig = orig_crop15.width
                h_orig = orig_crop15.height
                w_py = crop_szurke.width
                h_py = crop_szurke.height

                max_h = max(h_orig * 2 + 80, h_py * 2 + 80)
                total_w = w_orig + w_py + 60

                canvas = Image.new("RGB", (total_w, max_h), (245, 245, 245))
                draw = ImageDraw.Draw(canvas)

                draw.text((10, 10), "Eredeti Picasa 3.9 (job-878 #15)", fill=(0, 0, 0))
                canvas.paste(orig_crop15, (10, 30))

                draw.text((10, 50 + h_orig), "Eredeti Picasa 3.9 (job-878 #17 hovered)", fill=(0, 0, 0))
                canvas.paste(orig_crop17, (10, 70 + h_orig))

                x_py = w_orig + 30
                draw.text((x_py, 10), "PicasaPy (nyitott Soft Focus: letiltva)", fill=(0, 0, 0))
                canvas.paste(crop_szurke, (x_py, 30))

                draw.text((x_py, 50 + h_py), "PicasaPy (panel bezárva: aktív menü)", fill=(0, 0, 0))
                canvas.paste(crop_aktiv, (x_py, 70 + h_py))

                canvas.save(osszevetes_fajl)
            else:
                w = max(crop_szurke.width, crop_aktiv.width)
                h = crop_szurke.height + crop_aktiv.height + 60
                canvas = Image.new("RGB", (w + 20, h), (245, 245, 245))
                draw = ImageDraw.Draw(canvas)
                draw.text((10, 10), "PicasaPy letiltott Kép menü", fill=(0, 0, 0))
                canvas.paste(crop_szurke, (10, 30))
                draw.text((10, 40 + crop_szurke.height), "PicasaPy aktív Kép menü", fill=(0, 0, 0))
                canvas.paste(crop_aktiv, (10, 60 + crop_szurke.height))
                canvas.save(osszevetes_fajl)

            assert osszevetes_fajl.exists(), "az összevető kép nem készült el"
