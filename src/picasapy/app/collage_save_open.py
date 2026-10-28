"""A mentett kollázs MEGNYITÁSA szerkesztésre (#1002, #1072, #1272) - a `collage_save.py` szelete.

Belépési pontok: a kész kollázs és a piszkozat megnyitása
(`openCollageProject`), a piszkozat visszatöltése (`restoreCollageDraft`) és a
befejezés (`finishCollageDraft`). Mind a három EGY visszatöltési kódútra megy
(`_apply_cxf_project`). A `.cxf` mezőit a panelre teszi; a háttérkép
(`_apply_cxf_background`) a csomópontok UTÁN kerül vissza (#1103).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtGui import QColor

from picasapy.collage.cxf import read_cxf
from picasapy.collage.draft import nodes_from_project
from picasapy.collage.draft_state import draft_project_path, is_draft_image
from picasapy.collage.page_formats import ORIENTATIONS, format_key_of
from picasapy.collage.themes import BORDER_THEMES, COLLAGE_THEMES
from picasapy.collage.win_paths import decode_cxf_path

from .collage_model import CollageNode

logger = logging.getLogger(__name__)

class CollageSaveOpenMixin:
    """A mentett kollázs megnyitása és ráterítése a panelra - a `CollageSaveMixin` részeként."""

    @Slot(str, result=bool)
    def hasCollageProject(self, image_path: str) -> bool:  # noqa: N802
        """Van-e a képnek `.cxf` párja - vagyis kollázs-e (#1002).

        A szerkesztő „Kollázs szerkesztése" gombja ezen látszik
        (`editpanel/editcollage`, `m_hidden`: alapból rejtett, csak
        kollázsnál jön elő). A tulajdonos szava: *„Ez a gomb mindig
        megjelenik, ha megnyitom a kollázst."* - tehát nem a létrehozás
        emléke kapcsolja be, hanem a fájl mellett álló projektfájl."""
        return self._collage_project_path(image_path) is not None

    @Slot(str, result=bool)
    def isCollageDraft(self, image_path: str) -> bool:  # noqa: N802
        """Befejezetlen PISZKOZAT-e a megadott kép (#1072).

        A `hasCollageProject` párja, de a MÁSIK állapotra: az KÉSZ
        kollázsra igaz (van `<név>.cxf` párja), ez a piszkozatra (nincs
        párja, de a mappában ott az `autosave.cxf`). A kettő soha nem igaz
        egyszerre - a szabály a spec 1. szakaszának táblája.

        Erre kötődik a felület három következménye: a „Létrehozás" gomb
        megjelenése, a „Kollázs szerkesztése" gomb piszkozaton is, és a
        megosztás/nyomtatás tilalma."""
        return is_draft_image(image_path)

    @Slot(str)
    def openCollageProject(self, image_path: str) -> None:  # noqa: N802
        """A kollázs újranyitása SZERKESZTÉSRE - készen és piszkozaton is.

        A tulajdonos jelentése a v0.8.17-ről: *„Jelenleg ennek hiányában
        nem szerkeszthető a kollázs."* (#1002) - a kész képhez nem vezetett
        vissza út a panelra.

        ⚠️ #1072: a PISZKOZAT projektje nem a kép melletti `<név>.cxf` (az
        épp nincs is), hanem a mappa `autosave.cxf`-je. Enélkül a „Kollázs
        szerkesztése" gomb a piszkozaton némán hatástalan lett volna,
        pedig a spec 6. szakasza szerint ott is működik. A visszatöltés
        maga UGYANAZ a kódút - a `restoreCollageDraft`-tal együtt három
        belépési pont, egy `_apply_cxf_project`.

        A `saved_path` a MEGNYITOTT képre áll, tehát a „Létrehozás" a
        meglévő fájlt írja felül, nem újat számoz mellé: a felhasználó
        ugyanazt a kollázst szerkeszti tovább, nem másolatot készít.

        ⚠️ #1387: ha PISZKOZAT nyílik meg, a mappáját (ahol az `autosave.cxf`
        ténylegesen fekszik) megjegyezzük - a `finishCollageDraft` (a
        `createCollage` befejező hívása) ebből a TÉNYLEGES mappából takarít,
        nem a jelenleg beállítottból. Kész kollázs megnyitásakor nincs
        aktív piszkozat, ezért töröljük a korábbi jegyzetet."""
        utvonal = self._collage_project_path(image_path)
        piszkozat_mappa: Path | None = None
        if utvonal is None:
            utvonal = draft_project_path(image_path)
            if utvonal is not None:
                piszkozat_mappa = utvonal.parent
        if utvonal is None:
            return
        try:
            projekt = read_cxf(utvonal)
        except ValueError:
            logger.warning("A kollázs projektfájlja nem olvasható: %s", utvonal)
            self._collage_megnyitas_hiba()
            return
        self._ensure_collage_panel()
        self._collage_panel_draft_source_dir = piszkozat_mappa
        self._apply_cxf_project(projekt, saved_path=str(image_path))

    def _collage_project_path(self, image_path: str) -> Path | None:
        """A képhez tartozó `.cxf`, ha van és olvasható fájl."""
        if not image_path:
            return None
        try:
            utvonal = Path(str(image_path)).with_suffix(".cxf")
        except (OSError, ValueError):  # pragma: no cover - platformfüggő
            return None
        try:
            return utvonal if utvonal.is_file() else None
        except OSError:  # pragma: no cover - elérhetetlen hálózati út
            return None

    @Slot(str)
    def finishCollageDraft(self, image_path: str) -> None:  # noqa: N802
        """A piszkozat BEFEJEZÉSE - az `editpanel/render_now` gomb (#1072).

        A jegy harmadik hiánya: nálunk *„a mentés egyben véglegesít"* volt,
        vagyis egy MÁR mentett piszkozathoz nem vezetett külön befejező
        lépés. Az eredetiben ez a kép fölött ülő **„Létrehozás"** gomb
        (spec 4.1/4.3), és a `projectutils::draft_collage` szövege is erre
        hivatkozik.

        **Nem új mentő kódút** (spec 8.2 szabálya): betölti a piszkozat
        projektjét, majd a meglévő `createCollage`-ot hívja
        `replaceExisting=True`-val. Az eredeti is UGYANAZT a fájlnevet írja
        felül - a spec 5.1 mért igazolása szerint az `AI10.jpg` a piszkozat
        46 KB-járól ugyanazon a néven nőtt 2440 KB-ra, nem sorszámozott
        mellé. A takarítás (az `autosave.cxf` és a helykitöltő-jelölő
        megszűnése) a közös `_discard_draft_after_render` dolga.

        Nem piszkozatra NEM csinál semmit: a felület null-őrei és a
        gyorsan változó néző-sorok miatt ez a slot idegen útvonalat is
        kaphat, és egy véletlen renderelés a felhasználó képét írná felül."""
        if not is_draft_image(image_path):
            return
        self.openCollageProject(image_path)
        if not self._collage_panel_open:
            return
        self.createCollage(False, False, True)

    def _apply_cxf_background(self, hatter) -> None:
        """A `.cxf` háttere vissza a panelra (#1085).

        A tulajdonos jelentése: *„helyreállítja az előbbi fél mentést, de a
        háttérképet elfelejti, sima színre kapcsolja vissza."* A
        visszatöltés mindent visszahozott a témától a címig - a hátteret
        nem, pedig a `.cxf` tárolja.

        ⚠️ **A képháttér INDEXKÉNT él a panelen** (#1009: a háttérkép a
        kollázs SAJÁT képeinek egyike), a `.cxf` viszont ÚTVONALAT tárol -
        itt kell a kettő közé fordítani. Ha a hivatkozott kép már nincs a
        kollázsban, **színre esünk vissza**: üres képhátteret mutatni
        rosszabb volna, mint a színt, és törött hivatkozást a #1009
        szabálya szerint sosem hagyunk.

        A mezőket KÖZVETLENÜL állítjuk, a `set*` slotok helyett: azok
        `_set_dirty(True)`-t hívnának, a visszatöltés viszont nem
        módosítás."""
        if hatter is None:
            return
        if hatter.type == "image" and hatter.src:
            # #1096: a `.cxf` a hátteret is KÓDOLT alakban tárolja
            # (`$My Pictures\…`), a csomópontok útvonala viszont a
            # `nodes_from_project`-ben már feloldva érkezik. Kódolt
            # szöveggel keresve az egyezés SOSEM jönne össze, és a háttér
            # némán színre esne vissza - pont az a hiba, amit a #1085/#1103
            # javított, csak az eredeti Picasa fájljain.
            index = self._node_index_of_path(decode_cxf_path(hatter.src))
            if index >= 0:
                self._collage_panel_bg_index = index
                self._collage_panel_bg_mode = "image"
                self.collageBackgroundModeChanged.emit()
                self.collageBackgroundImageChanged.emit()
                return
            logger.info(
                "a piszkozat háttérképe már nincs a kollázsban (%s) - szín marad",
                hatter.src,
            )
        self._collage_panel_bg_mode = "solid"
        self.collageBackgroundModeChanged.emit()
        szin = _qcolor_from_argb(hatter.color)
        if szin is not None:
            self._collage_panel_bg_color = szin
            self.collageBackgroundColorChanged.emit()

    def _node_index_of_path(self, utvonal: str) -> int:
        """Melyik csomópont ez az útvonal; -1, ha nincs a kollázsban.

        Az összehasonlítás NORMALIZÁLT: a `.cxf` a mentés platformjának
        elválasztóit hordozza, a mai csomópont az aktuálisét (#1019)."""
        cel = os.path.normcase(os.path.normpath(str(utvonal)))
        for index, csomopont in enumerate(self._nodes()):
            if csomopont.path is None:
                continue
            if os.path.normcase(os.path.normpath(str(csomopont.path))) == cel:
                return index
        return -1

    def _apply_cxf_project(self, projekt, *, saved_path: str) -> None:
        """Egy `.cxf` projekt ráterítése a panelra - EGY kódút.

        A piszkozat-visszatöltés (#1051) és a kész kollázs újranyitása
        (#1002) ugyanaz a művelet, csak a forrás más. Két külön
        megvalósítás előbb-utóbb elválna, és a felhasználó azt látná, hogy
        a kollázs máshogy jön vissza attól függően, honnan nyitotta."""
        if projekt.theme in COLLAGE_THEMES:
            self._collage_panel_theme = projekt.theme
            self.collageThemeChanged.emit()
            self.collageCapabilitiesChanged.emit()
        if projekt.orientation in ORIENTATIONS:
            self._collage_panel_orientation = projekt.orientation
            self.collageOrientationChanged.emit()
            self.collagePageRatioChanged.emit()
        # ⚠️ #1272: a LAPFORMÁTUM is a fájlból jön, nem a legutóbb
        # használtból. Eddig hiányzott, ezért az újranyitott kollázsra a
        # mentett beállítás ült rá - a tulajdonos szava: „mindig az utolsó
        # használt képarányt erőlteti rá a korábbi szerkesztésére."
        #
        # A `.cxf` a formátum NEVÉT tárolja (#1089: az A4 neve `297:210`),
        # ezért kulccsá kell visszafordítani. Ismeretlen vagy dinamikus
        # névnél a panel pillanatnyi formátuma marad: egy idegen fájl nem
        # teheti használhatatlanná a panelt.
        formatum_kulcs = format_key_of(projekt.aspect_ratio)
        if formatum_kulcs is not None:
            self._collage_panel_format = formatum_kulcs
            self.collageFormatKeyChanged.emit()
            self.collagePageRatioChanged.emit()
        # #1274: a térköz ugyanígy a projekté, nem a legutóbbié.
        terkoz = float(projekt.spacing or 0.0)
        if self._collage_panel_spacing != terkoz:
            self._collage_panel_spacing = terkoz
            self.collageSpacingChanged.emit()
        self._collage_panel_shadows = bool(projekt.shadows)
        self._collage_panel_shadows_explicit = True
        self.collageShadowsChanged.emit()
        self._collage_panel_captions = bool(projekt.captions)
        self.collageCaptionsChanged.emit()
        if projekt.album_title:
            self.setCollageTitle(projekt.album_title)
        # ⚠️ #1274: az album-azonosítók és a dátum a panelen nem
        # SZERKESZTHETŐK, de a projekté maradnak - újramentéskor
        # változatlanul mennek vissza. Enélkül egy Picasával készült
        # kollázs újramentése ELDOBTA volna őket (a 12 golden minta
        # mindegyikében van albumUID és albumDate).
        self._collage_panel_album_uid = projekt.album_uid
        self._collage_panel_album_id = projekt.album_id
        self._collage_panel_album_date = projekt.album_date
        # #1092: a csomópont-azonosítókat a vászon-csomópont nem hordozza,
        # ezért `src → uid` leképezésben tesszük el. A KÓDOLT és a
        # FELOLDOTT alak is kulcs: a `.cxf` a Picasa változós útvonalát
        # tárolja (`$My Pictures\…`, #1096), a visszaíráskor viszont az
        # újrakódolt alakot keressük - a két kulcs együtt akkor is talál,
        # ha a feloldás ezen a gépen máshova mutat.
        self._collage_panel_node_uids = {
            kulcs: node.uid
            for node in projekt.nodes
            if node.uid and node.src
            for kulcs in {node.src, str(decode_cxf_path(node.src))}
        }
        # #2923: a `scale` UGYANÍGY a projektből él tovább. A #1412 277. köre
        # kimérte, hogy az eredeti nem számolja: a fájlból örökli, és a
        # másolók/`reset` változatlanul viszik. A mi számolt értékünk egy
        # Picasával készült kollázs újramentésekor elrontotta a fájlt.
        self._collage_panel_node_scales = {
            kulcs: node.scale
            for node in projekt.nodes
            if node.scale and node.src
            for kulcs in {node.src, str(decode_cxf_path(node.src))}
        }
        panel_csomopontok = _panel_nodes_of(nodes_from_project(projekt))
        self._set_nodes(panel_csomopontok, dirty=False)
        # ⚠️ #1274: a panel KERET-választója is a projekté. A `.cxf` a
        # keretet csomópontonként tárolja, a panelen viszont EGY választó
        # van - ezért csak akkor állítjuk, ha MINDEN csomópont ugyanazt
        # viseli. Vegyes keretnél a választó a helyén marad: egy értéket
        # mutatni ott hazugság volna, a felhasználó pedig azt hinné, hogy
        # a kollázs egységes.
        #
        # Enélkül az újranyitott polaroidos kollázs „nincs keret"-et
        # mutatott, és a KÖVETKEZŐ felvett kép keret nélkül került be - a
        # mentés ugyanis a panel értékéből dolgozik.
        keretek = {node.border for node in panel_csomopontok}
        if len(keretek) == 1:
            keret = keretek.pop()
            if keret in BORDER_THEMES and keret != self._collage_panel_border:
                self._collage_panel_border = keret
                self.collageBorderChanged.emit()
        # ⚠️ #1103: a háttér CSAK a csomópontok után. A képháttér a panelen
        # INDEXKÉNT él (#1009), a `.cxf` viszont ÚTVONALAT tárol, tehát a
        # visszaállítás megkeresi a képet a csomópontok között. Ha előbb
        # fut, a lista még a RÉGI (újraindítás után: ÜRES), az index -1
        # lesz, és a #1085 védőága - helyesen, de rossz pillanatban
        # kérdezve - színre ejti a hátteret. A tulajdonos ezt a v0.8.20 óta
        # látta: „a háttérképet elfelejti, sima színre kapcsolja vissza."
        self._apply_cxf_background(projekt.background)
        self._set_dirty(False)
        self._set_saved_path(saved_path)
        if not self._collage_panel_open:
            self._collage_panel_open = True
            self.collageOpenChanged.emit()

def _panel_nodes_of(nodes) -> tuple[CollageNode, ...]:
    """Rajzoló-csomópontok → a panel modell-csomópontjai.

    Az `output.render_nodes_of` megfordítása: a kijelölés (a modell mezője) a
    visszatöltésnél mindig üres, a kitöltés-mód (a rajzoló mezője) pedig a
    témából él tovább - egyik sem utazik a `.cxf`-ben.

    ⚠️ #989: a KÉP oldalarányát (`aspect`) a `.cxf` sem tárolja, ezért a
    csomópont dobozából vesszük. A Képkupacnál, az Indexképnél és a
    Többszörös exponálásnál ez PONTOS (ott a doboz a képé), a rácsos
    témáknál viszont a CELLA aránya - a visszatöltött kollázs egy későbbi
    téma-váltásnál ilyenkor közelítő arányokkal rendez újra. A képfájlok
    fejlécének beolvasása pontos volna, de 350 képnél a visszatöltést
    érezhetően lassítaná; ezt a cserét tudatosan vállaljuk."""
    return tuple(
        CollageNode(
            path="" if node.path is None else str(node.path),
            center_x=node.center_x,
            center_y=node.center_y,
            width=node.width,
            height=node.height,
            theta=node.theta,
            border=node.border,
            caption=node.caption,
            missing=node.missing,
            aspect=node.width / node.height,
        )
        for node in nodes
    )

def _qcolor_from_argb(ertek: str | None) -> QColor | None:
    """`FFRRGGBB` (ARGB hexa) → `QColor`; érvénytelenre `None`.

    A `.cxf` nagybetűs, nyolc karakteres ARGB-t tárol (`draft.py::_argb`); a
    `QColor` `#AARRGGBB` alakot vár. Hibás értékre nem dobunk: egy idegen
    `.cxf` sem tehet visszaállíthatatlanná egy kollázst."""
    if not ertek:
        return None
    szoveg = str(ertek).strip().lstrip("#")
    if len(szoveg) != 8:
        return None
    szin = QColor(f"#{szoveg}")
    return szin if szin.isValid() else None
