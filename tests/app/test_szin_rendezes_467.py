"""#467: „Rendezés szín alapján" — amit a Picasa megírt, de nem kötött be.

Az eredeti rendezés-motorja (`CSelectionNode`) **hat** módot ismert, a menü
viszont csak négyet kínált; a `SortColor` („Rendezés szín alapján") a
kimaradók közt volt. A felhasználó tehát soha nem érhette el.

Nálunk a #383 színkeresése miatt az átlagszín (`photo_colors.avgcolor`)
minden képre megvan, ezért ez a rendezés **egyetlen kulcs**.

A sorrend három osztálya (a jegy javaslata szerint):

1. **színes** kép — a MÉRT színezet (`color.pixel_hue`) szerint;
2. **telítetlen** kép — a színesek után (a színezetük nem értelmes);
3. **még nem indexelt** kép — utolsóként, fájlnév szerint, mert a színindex
   háttérben töltődik fel.

⚠️ Ez az őr a SORRENDET méri, nem azt, hogy „szivárványnak látszik".
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from picasapy.app.photo_sort import (
    NINCS_ADAT,
    SORT_MODES,
    SZINES,
    TELITETLEN,
    coerce_sort_mode,
    sort_folder_blocks,
    szin_kulcs,
)
from picasapy.color import pixel_hue, rgb_to_avgcolor
from picasapy.index import open_index
from picasapy.index.colors import load_avgcolors, save_colors

_MENU = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "FolderContextMenu.qml"
).read_text(encoding="utf-8")


def _foto(nev: str, mappa: str = "/k", **extra):
    from picasapy.index import PhotoRecord

    alap = dict(
        id=abs(hash((mappa, nev))) % 100000,
        folder_path=mappa,
        name=nev,
        kind="photo",
        size=100,
        mtime_ns=5,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=None,
        height=None,
    )
    alap.update(extra)
    return PhotoRecord(**alap)


def _hue_tabla(parok):
    """`{(útvonal, mtime, méret): színezet}` — a vezérlő ezt adja a modellnek."""
    return {
        (str(Path(r.folder_path) / r.name), r.mtime_ns, r.size): hue
        for r, hue in parok
    }


class TestASzempont:
    def test_a_szin_a_negyedik_szempont(self):
        assert SORT_MODES == ("date", "name", "size", "color")

    def test_ervenyes_szempontkent_atmegy(self):
        assert coerce_sort_mode("color") == "color"

    def test_a_menu_tetel_ott_van_es_ki_van_kotve(self):
        kezd = _MENU.index('objectName: "folderMenuSortByColor"')
        blokk = _MENU[kezd : kezd + 400]
        assert 'text: qsTr("&Color")' in blokk
        assert 'menu.sortModeRequested("color")' in blokk
        #: a #1468-as minta: a jelzés után visszakötjük a pipát
        assert "Qt.binding" in blokk


class TestAKulcs:
    def test_a_szines_kep_a_SZINEZETE_szerint_all(self):
        kep = _foto("a.jpg")
        tabla = _hue_tabla([(kep, 42)])
        assert szin_kulcs(kep, tabla)[:2] == (SZINES, 42)

    def test_a_telitetlen_kep_a_szinesek_UTAN(self):
        kep = _foto("a.jpg")
        assert szin_kulcs(kep, _hue_tabla([(kep, None)]))[0] == TELITETLEN
        assert TELITETLEN > SZINES

    def test_az_indexeletlen_kep_a_LEGVEGRE(self):
        kep = _foto("a.jpg")
        assert szin_kulcs(kep, {})[0] == NINCS_ADAT
        assert NINCS_ADAT > TELITETLEN

    def test_azonos_szinezetnel_a_FAJLNEV_dont(self):
        """Futásfüggő sorrend a rácson „ugrálásnak" látszana."""
        a, b = _foto("b.jpg"), _foto("a.jpg")
        tabla = _hue_tabla([(a, 10), (b, 10)])
        assert szin_kulcs(b, tabla) < szin_kulcs(a, tabla)


class TestARendezes:
    def test_a_szivarvany_sorrend(self):
        piros, zold, kek = _foto("z.jpg"), _foto("y.jpg"), _foto("x.jpg")
        tabla = _hue_tabla(
            [
                (piros, pixel_hue(255, 0, 0)),
                (zold, pixel_hue(0, 255, 0)),
                (kek, pixel_hue(0, 0, 255)),
            ]
        )
        sorrend = sort_folder_blocks((kek, zold, piros), "color", False, tabla)
        assert [r.name for r in sorrend] == ["z.jpg", "y.jpg", "x.jpg"]

    def test_a_szurke_a_szinesek_utan_marad(self):
        szines, szurke = _foto("a.jpg"), _foto("b.jpg")
        tabla = _hue_tabla([(szines, 200), (szurke, None)])
        sorrend = sort_folder_blocks((szurke, szines), "color", False, tabla)
        assert [r.name for r in sorrend] == ["a.jpg", "b.jpg"]

    def test_a_MAPPA_hatarok_nem_mozdulnak(self):
        """A rendezés blokkon belüli — ez a #1436 szerződése."""
        elso = _foto("z.jpg", "/egy")
        masodik = _foto("a.jpg", "/ketto")
        harmadik = _foto("b.jpg", "/ketto")
        tabla = _hue_tabla([(elso, 5), (masodik, 200), (harmadik, 10)])
        sorrend = sort_folder_blocks(
            (elso, masodik, harmadik), "color", False, tabla
        )
        assert [r.folder_path for r in sorrend] == ["/egy", "/ketto", "/ketto"]
        assert [r.name for r in sorrend] == ["z.jpg", "b.jpg", "a.jpg"]

    def test_szinadat_NELKUL_fajlnev_sorrend_a_visszaeses(self):
        """A rács sosem ürül ki és nem lesz futásfüggő, ha az index üres."""
        a, b = _foto("b.jpg"), _foto("a.jpg")
        assert [r.name for r in sort_folder_blocks((a, b), "color", False, None)] == [
            "a.jpg",
            "b.jpg",
        ]

    def test_a_forditott_sorrend_megforditja(self):
        piros, kek = _foto("a.jpg"), _foto("b.jpg")
        tabla = _hue_tabla([(piros, 0), (kek, 170)])
        sorrend = sort_folder_blocks((piros, kek), "color", True, tabla)
        assert [r.name for r in sorrend] == ["b.jpg", "a.jpg"]


class TestAzIndexOlvasasa:
    def test_az_avgcolor_visszaolvasható(self, tmp_path):
        with open_index(tmp_path / "i.db") as conn:
            save_colors(
                conn,
                [("/k/a.jpg", 5, 100, rgb_to_avgcolor(255, 0, 0), ("red",))],
            )
            tabla = load_avgcolors(conn, [("/k/a.jpg", 5, 100)])
        assert tabla[("/k/a.jpg", 5, 100)] == rgb_to_avgcolor(255, 0, 0)

    def test_az_ELAVULT_sor_nem_szamit(self, tmp_path):
        """Más mtime = más kép; a régi átlagszín nem rendezhet."""
        with open_index(tmp_path / "i.db") as conn:
            save_colors(
                conn, [("/k/a.jpg", 5, 100, rgb_to_avgcolor(0, 255, 0), ("green",))]
            )
            assert load_avgcolors(conn, [("/k/a.jpg", 9, 100)]) == {}

    def test_ures_kereses_ures_valasz(self, tmp_path):
        with open_index(tmp_path / "i.db") as conn:
            assert load_avgcolors(conn, []) == {}


class TestAMertSzinezet:
    @pytest.mark.parametrize(
        "rgb,vart", [((255, 0, 0), 0), ((0, 255, 0), 85), ((0, 0, 255), 170)]
    )
    def test_az_alapszinek_a_hue_koron(self, rgb, vart):
        assert pixel_hue(*rgb) == vart

    @pytest.mark.parametrize("rgb", [(128, 128, 128), (0, 0, 0), (255, 255, 255)])
    def test_a_telitetlen_kep_None(self, rgb):
        assert pixel_hue(*rgb) is None

    def test_a_RES_beli_keppontnak_is_van_szinezete(self):
        """A `pixel_bucket` mért rése (b == 25) a KERESÉS szemantikája — a
        rendezésnek attól is kell színezetet adni, különben egy keskeny
        vörös sáv képei a lista végére esnének."""
        from picasapy.color import pixel_bucket

        # H 250…254: a kör legvége, közvetlenül a piros előtt
        piros_hatar = (255, 0, 8)
        assert pixel_bucket(*piros_hatar) is None
        assert pixel_hue(*piros_hatar) is not None


class TestAVezerloIntegracio:
    """A lánc VÉGE: a vezérlő tényleg ad színadatot a modellnek, és csak
    `color` szempontnál nyit indexet."""

    @pytest.fixture
    def vezerlo(self, qt_app, tmp_path):
        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache
        from PySide6.QtCore import QSettings

        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        with open_index(tmp_path / "index.db"):
            pass
        return AppController(
            tmp_path / "index.db",
            (str(gyoker),),
            ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
            settings=QSettings(
                str(tmp_path / "s.ini"), QSettings.Format.IniFormat
            ),
            watched_file=tmp_path / "WatchedFolders.txt",
        )

    def test_a_szin_szempont_tarolhato(self, vezerlo):
        vezerlo.setFolderPhotoSort("color")
        assert vezerlo.folderPhotoSort == "color"

    def test_a_vezerlo_az_INDEXBOL_adja_a_szinezetet(self, vezerlo, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(
                conn,
                [("/k/a.jpg", 5, 100, rgb_to_avgcolor(0, 0, 255), ("blue",))],
            )
            conn.commit()  # a `save_colors` a HÍVÓRA hagyja a commitot
        tabla = vezerlo._folder_photo_hues([_foto("a.jpg")])
        assert tabla[("/k/a.jpg", 5, 100)] == pixel_hue(0, 0, 255)

    def test_ures_rekordlistara_nem_nyit_indexet(self, vezerlo):
        assert vezerlo._folder_photo_hues([]) == {}

    def test_a_modell_CSAK_szin_szempontnal_kerdez(self, qt_app):
        """Minden más rendezésnél az index olvasása fölösleges munka."""
        from picasapy.app.models import PhotoGridModel

        hivasok = []
        modell = PhotoGridModel()
        modell.set_folder_photo_sort(
            "name", False, is_active=lambda: True,
            hues=lambda rekordok: hivasok.append(len(rekordok)) or {},
        )
        modell.set_photos((_foto("b.jpg"), _foto("a.jpg")))
        assert hivasok == []
        modell.set_folder_photo_sort("color", False, is_active=lambda: True)
        assert hivasok == [2]
