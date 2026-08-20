"""#943: a kollázs-panel vezérlője (`app/collage_controller.py`).

A `CollageMixin` a `kollazs-panel-ui-spec.md` **8.** szakaszának
szerződése: property-k, slotok és jelzések, PONTOSAN a spec neveivel.

A mixin ÖNÁLLÓAN, minimális host-osztályon tesztelt (a
`test_people_controller.py` mintája) — az `AppController`-be kötés
(`controller.py`, forró fájl) az integrátor dolga. QML és vászon nélkül
fut: a modell adat, nem rajz.
"""

from __future__ import annotations

import gc

from pathlib import PurePath

import math
from dataclasses import dataclass

import pytest
from PySide6.QtCore import QEventLoop, QObject, QSettings, QTimer
from PySide6.QtGui import QColor

from picasapy.collage.themes import (
    CONTACTSHEET,
    MULTIEXP,
    NOBORDER,
    PICTUREPILE,
    POLAROID,
    REGULARGRID,
    WHITEBORDER,
    capabilities_for,
)
from support.jpeg_factory import make_jpeg


@dataclass
class _Photo:
    """A `PhotoRecord` azon mezői, amiket a panel használ."""

    folder_path: str
    name: str
    caption: str | None = None
    width: int | None = 400
    height: int | None = 300


class _Photos:
    def __init__(self, photos):
        self.photos = list(photos)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / name, size=(80, 60))
    return root


@pytest.fixture
def host(qt_app, tmp_path, library):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin

    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "kimenet"))

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos(
                [
                    _Photo(str(library), "a.jpg", "Alma", 400, 300),
                    _Photo(str(library), "b.jpg", None, 300, 400),
                    _Photo(str(library), "c.jpg", "Cica", 200, 200),
                ]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            # a headless (offscreen) képernyő 800×800-as, azaz NÉGYZETES —
            # így a formátum-eltérés vizsgálata a véletlenen múlna
            return 9 / 16

    instance = _Host()
    yield instance
    assert instance.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


@pytest.fixture
def nyitott(host):
    host.openCollage([0, 1, 2])
    return host


def _wait(signal, action, timeout_ms=15000):
    """A műveletet a jelzésre FELIRATKOZVA indítja, majd bevárja azt.

    ⚠️ **A várakozás idejére kikapcsoljuk a szemétgyűjtőt (#988) — és ez
    NEM a hiba javítása.**

    A CI-n visszatérő `exit -11` (SIGSEGV) veremkiíratása ezt mutatta:

    ```
    Thread (háttér):  picasa_render._canvas ← collage_save._render_worker
    Current thread:   Garbage-collecting ← _wait ← a teszt
    ```

    Vagyis a főszál épp GC-t futtat ebben a beágyazott eseményhurokban,
    miközben a háttérszál — egy sima `threading.Thread` — Qt-jelzést
    marsall a PySide-burkolókon. A GC időzítése dönti el, hogy elszáll-e;
    ezért nem volt reprodukálható terhelés nélkül, és ezért látszott
    párhuzamosság-függőnek.

    **A valódi javítás** a worker Qt-natívvá tétele (`QThread`/
    `QueuedConnection`), az állapotírással együtt — az a #988/#999 köre,
    másik munkamenetnél. Ez itt csak annyit tesz, hogy a **teszt** ne
    hordozza a versenyhelyzetet, amíg az meg nem történik: a főág piros
    CI-je e-mailt küld a tulajdonosnak, és minden kiadást blokkol.

    A `gc.enable()` a `finally`-ben — egy elszálló teszt sem hagyhatja
    kikapcsolva a gyűjtőt a többinek.
    """
    loop = QEventLoop()
    received = {}

    def _on(*args):
        received.setdefault("args", args)
        loop.quit()

    signal.connect(_on)
    gc.disable()
    try:
        action()
        if "args" not in received:
            QTimer.singleShot(timeout_ms, loop.quit)
            loop.exec()
    finally:
        gc.enable()
    return ("args" in received, received.get("args", ()))


class TestAlapallapot:
    def test_a_panel_zarva_indul(self, host):
        assert host.collageOpen is False
        assert host.collageClipCount == 0
        assert host.collageDirty is False
        assert host.collageFrameCenter == -1

    def test_az_alapertelmezett_beallitasok(self, host):
        assert host.collageTheme == PICTUREPILE
        assert host.collageBorder == NOBORDER
        assert host.collageSpacing == 0.0
        assert host.collageCaptions is True
        assert host.collageOrientation == "landscape"
        assert host.collageFormatKey == "Desktop4x3"
        assert host.collagePageRatio == pytest.approx(3 / 4)
        assert host.collageBackgroundMode == "solid"

    def test_a_kepkupacnal_az_arnyek_alapbol_be(self, host):
        """A maszk 14. bitje — a Képkupacnál BE, a Rácsnál KI."""
        assert host.collageShadows is True
        host.setCollageTheme(REGULARGRID)
        assert host.collageShadows is False

    def test_a_modell_ures_de_letezik(self, host):
        assert host.collageNodes is not None
        assert host.collageNodes.rowCount() == 0


class TestKepessegek:
    @pytest.mark.parametrize(
        "tema", [PICTUREPILE, REGULARGRID, CONTACTSHEET, MULTIEXP]
    )
    def test_a_terkep_a_themes_modulbol_jon(self, host, tema):
        host.setCollageTheme(tema)
        vart = capabilities_for(tema)
        assert host.collageCapabilities == {
            "borders": vart.borders,
            "spacing": vart.spacing,
            "shadow": vart.shadow,
            "selection": vart.selection,
            "background": vart.background,
            "shuffle": vart.shuffle,
            "scramble": vart.scramble,
            "ring": vart.ring,
            "rotate": vart.rotate,
        }

    def test_ismeretlen_tema_nem_valtoztat(self, host):
        host.setCollageTheme("kollazs2000")
        assert host.collageTheme == PICTUREPILE

    def test_a_temavaltas_ELDOBJA_a_kezi_elrendezest(self, nyitott):
        """Spec 5./2.: téma-váltáskor a csomópontok helye a téma pakolójából
        jön újra, tehát a kézi mozgatás elveszik — az eredeti sem kérdez rá.
        A váltás mentetlen MÓDOSÍTÁS, nem semleges nézetváltás.

        (A témánkénti pakoló bekötése a vászon-jegyé; ma minden téma a
        Képkupac szórását kapja, ezért a KÉZI hely elvesztése az, ami itt
        ellenőrizhető.)"""
        nyitott.moveNode(0, 7.0, 9.0)
        nyitott.setCollageTheme(REGULARGRID)
        assert nyitott.collageDirty is True
        assert nyitott.collageNodes.nodes[0].center_x != 7.0
        assert nyitott.collageClipCount == 3

    def test_a_temavaltas_utan_is_ugyanazok_a_kepek(self, nyitott):
        elotte = [n.path for n in nyitott.collageNodes.nodes]
        nyitott.setCollageTheme(CONTACTSHEET)
        assert [n.path for n in nyitott.collageNodes.nodes] == elotte


class TestMegnyitas:
    def test_a_kepekbol_csomopontok_lesznek(self, nyitott):
        assert nyitott.collageOpen is True
        assert nyitott.collageClipCount == 3
        utak = [n.path for n in nyitott.collageNodes.nodes]
        assert [PurePath(u).name for u in utak] == ["a.jpg", "b.jpg", "c.jpg"]

    # ⚠️ #989: ez a két eset ÁTÍRÓDOTT. A #943 azt rögzítette, hogy MINDEN
    # csomópont szélessége `initial_node_width(n)` — ez akkor volt igaz,
    # amikor a panel a téma pakolója helyett egy saját, egyszerűsített
    # szórást futtatott. A Képkupac valódi pakolója (`collage/pile.py`,
    # 1.9.2) minden képet UGYANABBA A NÉGYZETBE illeszt (`pile_size`), tehát
    # az álló kép szélessége kisebb, mint a fekvőé — a régi szabály egy álló
    # képet 1,33-szor akkorára nagyított, mint egy fekvőt. A darabszámból
    # jövő méret ettől nem tűnt el: az a NÉGYZET oldala (és egyben a
    # `collageBaseNodeWidth` viszonyítási pontja, spec 6.2).

    def test_a_kezdo_meret_a_darabszambol(self, nyitott):
        from picasapy.collage.pile import pile_size

        oldal = pile_size(1, 1024)
        for n in nyitott.collageNodes.nodes:
            assert max(n.width, n.height) == pytest.approx(oldal, abs=1.0)

    def test_a_meretarany_viszonyitasi_pontja_a_darabszamon_all(self, nyitott):
        """A fogantyú 1,0-s viszonyítási pontja (spec 6.2, #947) továbbra is
        a darabszámból jön — ezt a téma-váltás nem bántja."""
        from picasapy.app.collage_model import initial_node_width

        assert nyitott.collageBaseNodeWidth == pytest.approx(initial_node_width(3))

    def test_a_magassag_a_kep_aranyabol(self, nyitott):
        """A kép aránya megmarad — EGY lapegység tűréssel: az illesztő egész
        képpontra kerekít (`fitting.picasa_round`)."""
        also, allo, negyzet = nyitott.collageNodes.nodes
        assert also.height == pytest.approx(also.width * 300 / 400, abs=1.0)
        assert allo.height == pytest.approx(allo.width * 400 / 300, abs=1.0)
        assert negyzet.height == pytest.approx(negyzet.width, abs=1.0)

    def test_a_felirat_a_kephez_tartozik(self, nyitott):
        assert [n.caption for n in nyitott.collageNodes.nodes] == [
            "Alma",
            "",
            "Cica",
        ]

    def test_a_hianyzo_fajl_helykitolto_csempe(self, host, tmp_path):
        host._photos.photos.append(_Photo(str(tmp_path), "nincs.jpg"))
        host.openCollage([0, 3])
        assert [n.missing for n in host.collageNodes.nodes] == [False, True]

    def test_a_megnyitas_nem_piszkos(self, nyitott):
        assert nyitott.collageDirty is False

    def test_bezaraskor_kiurul(self, nyitott):
        nyitott.closeCollage()
        assert nyitott.collageOpen is False
        assert nyitott.collageClipCount == 0


class TestKijeloles:
    def test_kijeloles_indexekkel(self, nyitott):
        nyitott.setCollageSelection([0, 2])
        assert nyitott.collageSelection == [0, 2]

    def test_mind_es_semmi(self, nyitott):
        nyitott.selectAllNodes()
        assert nyitott.collageSelection == [0, 1, 2]
        nyitott.selectNoNodes()
        assert nyitott.collageSelection == []

    def test_a_tobbszoros_exponalasban_nincs_kijeloles(self, nyitott):
        nyitott.setCollageTheme(MULTIEXP)
        nyitott.selectAllNodes()
        assert nyitott.collageSelection == []

    def test_a_kijeloltek_eltavolitasa(self, nyitott):
        nyitott.setCollageSelection([1])
        nyitott.removeSelectedNodes()
        utak = [PurePath(n.path).name for n in nyitott.collageNodes.nodes]
        assert utak == ["a.jpg", "c.jpg"]
        assert nyitott.collageDirty is True


class TestRetegsorrend:
    def test_a_legfelsot_felemelni_NEM_valtoztat_semmit(self, nyitott):
        """A jegy sarokesete: `raiseNodeToTop` a legfelső elemen tétlen."""
        elotte = nyitott.collageNodes.nodes
        jelzesek: list[str] = []
        nyitott.collageNodes.modelReset.connect(lambda: jelzesek.append("reset"))
        nyitott.collageNodes.dataChanged.connect(
            lambda *_: jelzesek.append("data")
        )
        nyitott.raiseNodeToTop(2)
        assert nyitott.collageNodes.nodes == elotte
        assert jelzesek == []
        assert nyitott.collageDirty is False

    def test_alt_huzas_a_legfelso_retegbe_visz(self, nyitott):
        nyitott.raiseNodeToTop(0)
        utak = [PurePath(n.path).name for n in nyitott.collageNodes.nodes]
        assert utak == ["b.jpg", "c.jpg", "a.jpg"]
        assert nyitott.collageDirty is True

    def test_savon_kivuli_index_nem_omlik_ossze(self, nyitott):
        elotte = nyitott.collageNodes.nodes
        nyitott.raiseNodeToTop(9)
        assert nyitott.collageNodes.nodes == elotte

    def test_a_negy_retegparancs(self, nyitott):
        nyitott.setCollageSelection([0])
        nyitott.moveSelectionUp()
        assert _nevek(nyitott) == ["b.jpg", "a.jpg", "c.jpg"]
        nyitott.moveSelectionTop()
        assert _nevek(nyitott) == ["b.jpg", "c.jpg", "a.jpg"]
        nyitott.moveSelectionDown()
        assert _nevek(nyitott) == ["b.jpg", "a.jpg", "c.jpg"]
        nyitott.moveSelectionBottom()
        assert _nevek(nyitott) == ["a.jpg", "b.jpg", "c.jpg"]

    def test_a_kijeloles_koveti_a_csomopontot(self, nyitott):
        nyitott.setCollageSelection([0])
        nyitott.moveSelectionTop()
        assert nyitott.collageSelection == [2]


def _nevek(host) -> list[str]:
    return [PurePath(n.path).name for n in host.collageNodes.nodes]


class TestCsereEsMozgatas:
    def test_a_csere_csak_a_kepet_mozgatja(self, nyitott):
        """A jegy sarokesete: `swapNodes(a, b)` a két `path`-t cseréli, a
        méret, a keret és a szög marad."""
        nyitott.transformNode(0, 2.0, 0.4)
        nyitott.setCollageSelection([0])
        nyitott.setCollageBorder(POLAROID)
        elso, masodik = nyitott.collageNodes.nodes[:2]
        nyitott.swapNodes(0, 1)
        uj_elso, uj_masodik = nyitott.collageNodes.nodes[:2]
        assert uj_elso.path == masodik.path
        assert uj_masodik.path == elso.path
        assert (uj_elso.width, uj_elso.height) == (elso.width, elso.height)
        assert uj_elso.theta == elso.theta
        assert uj_elso.border == elso.border
        assert uj_masodik.border == masodik.border

    def test_mozgatas_lapegysegben(self, nyitott):
        nyitott.moveNode(1, 100.5, 900.25)
        node = nyitott.collageNodes.nodes[1]
        assert (node.center_x, node.center_y) == (100.5, 900.25)
        assert nyitott.collageDirty is True

    def test_a_meretezes_az_alapmerethez_kepest_szol(self, nyitott):
        from picasapy.app.collage_model import initial_node_width

        elotte = nyitott.collageNodes.nodes[0]
        nyitott.transformNode(0, 0.5, math.radians(30.0))
        node = nyitott.collageNodes.nodes[0]
        assert node.width == pytest.approx(initial_node_width(3) * 0.5)
        assert node.height / node.width == pytest.approx(
            elotte.height / elotte.width
        )
        assert node.theta == pytest.approx(math.radians(30.0))

    def test_nem_pozitiv_meretezes_kimarad(self, nyitott):
        elotte = nyitott.collageNodes.nodes
        nyitott.transformNode(0, 0.0, 0.0)
        assert nyitott.collageNodes.nodes == elotte


class TestForgatas:
    def test_a_snap_9_MINUSZ_90_fokot_tarol(self, nyitott):
        """A jegy sarokesete: a `.cxf`-be −1,570796 kerül, nem 4,712389 —
        különben a windowsos Picasával az oda-vissza olvasás elcsúszna."""
        nyitott.setCollageSelection([0])
        nyitott.snapRotation("snap_9")
        theta = nyitott.collageNodes.nodes[0].theta
        assert theta == pytest.approx(math.radians(-90.0))
        assert theta < 0.0
        assert theta != pytest.approx(math.radians(270.0))

    @pytest.mark.parametrize(
        "parancs,fok", [("snap_12", 0.0), ("snap_3", 90.0), ("snap_6", 180.0)]
    )
    def test_a_masik_harom_irany(self, nyitott, parancs, fok):
        nyitott.setCollageSelection([1])
        nyitott.snapRotation(parancs)
        assert nyitott.collageNodes.nodes[1].theta == pytest.approx(
            math.radians(fok)
        )

    def test_kijeloles_nelkul_kijelolest_ker(self, nyitott):
        kert: list[int] = []
        nyitott.collageNeedsSelection.connect(lambda: kert.append(1))
        nyitott.snapRotation("snap_3")
        assert kert == [1]

    def test_ismeretlen_parancs_nem_omlik_ossze(self, nyitott):
        """#989: a Képkupac a képeket LEGYEZŐSEN dönti meg (`pile_rotation`),
        tehát a kiinduló szög nem nulla — az állítás azért arról szól, hogy
        az ismeretlen parancs semmit NEM változtat."""
        nyitott.setCollageSelection([0])
        elotte = nyitott.collageNodes.nodes[0].theta
        nyitott.snapRotation("snap_7")
        assert nyitott.collageNodes.nodes[0].theta == elotte


class TestVeletlenszerusites:
    def test_az_osszekeveres_a_kepeket_mozgatja_a_reseket_nem(self, nyitott):
        elotte = nyitott.collageNodes.nodes
        for _ in range(8):
            nyitott.shufflePictures()
            if _nevek(nyitott) != ["a.jpg", "b.jpg", "c.jpg"]:
                break
        assert sorted(_nevek(nyitott)) == ["a.jpg", "b.jpg", "c.jpg"]
        assert _nevek(nyitott) != ["a.jpg", "b.jpg", "c.jpg"]
        assert [n.center_x for n in nyitott.collageNodes.nodes] == [
            n.center_x for n in elotte
        ]

    def test_a_szetszoras_uj_helyeket_ad(self, nyitott):
        elotte = [n.center_x for n in nyitott.collageNodes.nodes]
        nyitott.scrambleCollage()
        assert [n.center_x for n in nyitott.collageNodes.nodes] != elotte

    def test_a_racsban_nincs_szetszoras(self, nyitott):
        nyitott.setCollageTheme(REGULARGRID)
        elotte = nyitott.collageNodes.nodes
        nyitott.scrambleCollage()
        assert nyitott.collageNodes.nodes == elotte


class TestBeallitasok:
    def test_a_keret_a_kijeloltekre_megy_ha_van(self, nyitott):
        nyitott.setCollageSelection([1])
        nyitott.setCollageBorder(POLAROID)
        assert [n.border for n in nyitott.collageNodes.nodes] == [
            NOBORDER,
            POLAROID,
            NOBORDER,
        ]

    def test_kijeloles_nelkul_mindenkire(self, nyitott):
        nyitott.setCollageBorder(WHITEBORDER)
        assert {n.border for n in nyitott.collageNodes.nodes} == {WHITEBORDER}
        assert nyitott.collageBorder == WHITEBORDER

    def test_a_terkoz_savba_kerul(self, nyitott):
        nyitott.setCollageSpacing(2.5)
        assert nyitott.collageSpacing == 1.0
        nyitott.setCollageSpacing(-1.0)
        assert nyitott.collageSpacing == 0.0

    def test_nulla_terkoznel_bekapcsol_az_arnyek(self, nyitott):
        """Spec 5.: nulla térköznél az árnyék az egyetlen, ami elválasztja a
        képeket — ezért BEkapcsol (nem tiltódik)."""
        nyitott.setCollageTheme(REGULARGRID)
        nyitott.setCollageShadows(False)
        nyitott.setCollageSpacing(0.0)
        assert nyitott.collageShadows is True

    def test_a_tobbszoros_exponalasban_nincs_arnyek(self, nyitott):
        nyitott.setCollageTheme(MULTIEXP)
        nyitott.setCollageShadows(True)
        assert nyitott.collageShadows is False

    def test_tajolas_es_formatum(self, nyitott):
        nyitott.setCollageFormat("10x15m")
        assert nyitott.collagePageRatio == pytest.approx(10 / 15)
        nyitott.setCollageOrientation("portrait")
        assert nyitott.collagePageRatio == pytest.approx(15 / 10)
        nyitott.setCollageOrientation("átlós")
        assert nyitott.collageOrientation == "portrait"

    def test_ismeretlen_formatum_nem_valtoztat(self, nyitott):
        nyitott.setCollageFormat("A3plusz")
        assert nyitott.collageFormatKey == "Desktop4x3"

    def test_hatterszin_es_mod(self, nyitott):
        nyitott.setCollageBackgroundColor(QColor("#204080"))
        assert nyitott.collageBackgroundColor.name() == "#204080"
        assert nyitott.collageBackgroundMode == "solid"
        nyitott.setCollageBackgroundMode("avg")
        assert nyitott.collageBackgroundMode == "avg"
        nyitott.setCollageBackgroundMode("csillamos")
        assert nyitott.collageBackgroundMode == "avg"

    def test_hatter_a_kijelolesbol(self, nyitott):
        nyitott.setCollageSelection([2])
        nyitott.setBackgroundFromSelection()
        assert nyitott.collageBackgroundMode == "image"
        assert nyitott.collageBackgroundImage.endswith("c.jpg")

    def test_hatter_kijeloles_nelkul_kijelolest_ker(self, nyitott):
        kert: list[int] = []
        nyitott.collageNeedsSelection.connect(lambda: kert.append(1))
        nyitott.setCollageSelection([0, 1])
        nyitott.setBackgroundFromSelection()
        assert kert == [1]
        assert nyitott.collageBackgroundMode == "solid"

    def test_kepkockakozeppont_a_kijelolesbol(self, nyitott):
        nyitott.setCollageSelection([1])
        nyitott.setFrameCenterFromSelection()
        assert nyitott.collageFrameCenter == 1

    def test_megjelenites_es_szerkesztes(self, nyitott):
        kert: list[str] = []
        nyitott.collageEditRequested.connect(kert.append)
        nyitott.setCollageSelection([0])
        nyitott.viewAndEditSelection()
        assert len(kert) == 1 and kert[0].endswith("a.jpg")


class TestKlipek:
    def test_hozzaadas_es_torles(self, nyitott):
        nyitott.deleteClips([0])
        assert nyitott.collageClipCount == 2
        nyitott.addClips([0])
        assert nyitott.collageClipCount == 3
        assert _nevek(nyitott)[-1] == "a.jpg"

    def test_az_uj_klip_a_legfelso_reteg(self, nyitott):
        nyitott.addClips([1])
        assert _nevek(nyitott) == ["a.jpg", "b.jpg", "c.jpg", "b.jpg"]


class TestVisszaallitas:
    def test_a_reset_ujraszamolja_az_elrendezest(self, nyitott):
        nyitott.moveNode(0, 1.0, 1.0)
        nyitott.resetCollage()
        assert nyitott.collageNodes.nodes[0].center_x != 1.0
        assert nyitott.collageDirty is False
        assert nyitott.collageClipCount == 3

    def test_a_reset_a_KEVERT_kepekbol_dolgozik(self, nyitott):
        """A reset a vászon jelenlegi képeit rendezi újra — nem egy
        párhuzamosan vezetett, közben elcsúszott forrás-listát."""
        nyitott.deleteClips([1])
        nyitott.shufflePictures()
        elotte = sorted(_nevek(nyitott))
        nyitott.resetCollage()
        assert sorted(_nevek(nyitott)) == elotte
        assert nyitott.collageClipCount == 2

    def test_a_torolt_kep_nem_ter_vissza(self, nyitott):
        nyitott.deleteClips([0])
        nyitott.resetCollage()
        assert _nevek(nyitott) == ["b.jpg", "c.jpg"]


class TestLetrehozas:
    def test_csupa_hianyzo_kepnel_is_mentes_mellozve(self, host, tmp_path):
        """9.4: ha a kollázs minden képe eltűnt a lemezről, ugyanaz a
        zsákutca — nem nyers kivétel-szöveg megy ki a felhasználóhoz."""
        host._photos.photos = [_Photo(str(tmp_path), "nincs.jpg")]
        host.openCollage([0])
        jelzett: list[int] = []
        hibak: list[str] = []
        host.collageNoImages.connect(lambda: jelzett.append(1))
        host.collageFailed.connect(hibak.append)
        host.createCollage(False)
        assert jelzett == [1] and hibak == []

    def test_kep_nelkul_mentes_mellozve(self, host):
        jelzett: list[int] = []
        host.collageNoImages.connect(lambda: jelzett.append(1))
        host.createCollage(False)
        assert jelzett == [1]

    def test_a_kesz_fajl_a_kimeneti_mappaba_kerul(self, nyitott, tmp_path, library):
        megjott, args = _wait(nyitott.collageDone, lambda: nyitott.createCollage(False))
        assert megjott, "nem érkezett collageDone"
        from pathlib import Path

        cel = Path(args[0])
        assert cel.exists() and cel.parent == tmp_path / "kimenet"
        # ⚠️ #949: a fájlnév a FORRÁSMAPPA címe (spec 9.1), nem beégetett
        # „kollázs" — az utóbbi csak a tartalék, ha nincs egy közös forrás.
        # A #943 köre a tartalékot vette törvénynek; a részletes állítások a
        # `test_collage_output_949.py`-ban élnek.
        assert cel.name == f"{library.name}.jpg"

    def test_a_mentes_utan_nem_piszkos(self, nyitott):
        nyitott.moveNode(0, 5.0, 5.0)
        assert nyitott.collageDirty is True
        megjott, _ = _wait(nyitott.collageDone, lambda: nyitott.createCollage(False))
        assert megjott
        assert nyitott.collageDirty is False

    def test_asztali_hatterkep_eltero_formatumnal_figyelmeztet(self, nyitott):
        jelzett: list[int] = []
        nyitott.collageFormatMismatch.connect(lambda: jelzett.append(1))
        nyitott.setCollageFormat("Square")
        nyitott.createCollage(True)
        assert jelzett == [1]
        assert nyitott.backgroundWorkersRunning() is False

    def test_a_figyelmeztetes_atlepheto(self, nyitott):
        nyitott.setCollageFormat("Square")
        megjott, _ = _wait(
            nyitott.collageDesktopBackgroundReady,
            lambda: nyitott.createCollage(True, True),
        )
        assert megjott

    def test_a_folyamatjelzo_szazalekot_es_szoveget_ad(self, nyitott):
        lepesek: list[tuple[int, str]] = []
        nyitott.collageProgress.connect(lambda p, s: lepesek.append((p, s)))
        megjott, _ = _wait(nyitott.collageDone, lambda: nyitott.createCollage(False))
        assert megjott
        assert lepesek[0][0] == 0 and lepesek[0][1]
        assert lepesek[-1][0] == 100


class TestMegorzottBeallitasok:
    def test_a_beallitasok_visszatoltodnek(self, host, qt_app):
        from picasapy.app.collage_controller import CollageMixin

        host.setCollageTheme(CONTACTSHEET)
        host.setCollageFormat("A4")
        host.setCollageOrientation("portrait")
        host.setCollageCaptions(False)
        host.setCollageShadows(False)
        host.setCollageBackgroundColor(QColor("#123456"))
        host._get_settings().sync()

        class _Masik(CollageMixin, QObject):
            def __init__(self, settings):
                super().__init__()
                self._settings = settings

            def _get_settings(self):
                return self._settings

        masik = _Masik(host._get_settings())
        assert masik.collageTheme == CONTACTSHEET
        assert masik.collageFormatKey == "A4"
        assert masik.collageOrientation == "portrait"
        assert masik.collageCaptions is False
        assert masik.collageShadows is False
        assert masik.collageBackgroundColor.name() == "#123456"

    def test_serult_beallitas_az_alapertelmezesre_esik(self, tmp_path, qt_app):
        from picasapy.app.collage_controller import CollageMixin

        settings = QSettings(
            str(tmp_path / "rossz.ini"), QSettings.Format.IniFormat
        )
        settings.setValue("collage/theme", "kollazs2000")
        settings.setValue("collage/format", "A3plusz")
        settings.setValue("collage/orientation", "átlós")

        class _Host(CollageMixin, QObject):
            def _get_settings(self):
                return settings

        host = _Host()
        assert host.collageTheme == PICTUREPILE
        assert host.collageFormatKey == "Desktop4x3"
        assert host.collageOrientation == "landscape"


class TestApiFelulet:
    """A spec 8. szakasza NÉV SZERINTI szerződés: a QML-jegyek (3–8.) erre
    az API-ra épülnek, ezért egyetlen elgépelés is későbbi, néma
    kötés-hibaként jelentkezne."""

    PROPERTYK = (
        "collageOpen",
        "collageTheme",
        "collageBorder",
        "collageSpacing",
        "collageShadows",
        "collageCaptions",
        "collageOrientation",
        "collageFormatKey",
        "collagePageRatio",
        "collageBackgroundMode",
        "collageBackgroundColor",
        "collageBackgroundImage",
        "collageNodes",
        "collageSelection",
        "collageFrameCenter",
        "collageClipCount",
        "collageDirty",
        "collageCapabilities",
    )

    SLOTOK = (
        "openCollage",
        "closeCollage",
        "setCollageTheme",
        "setCollageBorder",
        "setCollageSpacing",
        "setCollageShadows",
        "setCollageCaptions",
        "setCollageOrientation",
        "setCollageFormat",
        "setCollageBackgroundMode",
        "setCollageBackgroundColor",
        "setBackgroundFromSelection",
        "setCollageSelection",
        "selectAllNodes",
        "selectNoNodes",
        "removeSelectedNodes",
        "moveNode",
        "transformNode",
        "swapNodes",
        "raiseNodeToTop",
        "moveSelectionTop",
        "moveSelectionUp",
        "moveSelectionDown",
        "moveSelectionBottom",
        "snapRotation",
        "shufflePictures",
        "scrambleCollage",
        "setFrameCenterFromSelection",
        "viewAndEditSelection",
        "createCollage",
        "resetCollage",
        "addClips",
        "deleteClips",
    )

    JELZESEK = (
        "collageProgress",
        "collageDone",
        "collageFailed",
        "collageNoImages",
        "collageFormatMismatch",
        "collageNeedsSelection",
        "collageDraftSaved",
    )

    #: A `collageNodes` a modell-PÉLDÁNY, ami sosem cserélődik — Qt-ben az
    #: ilyen property `constant`, és a `constant` kizárja a `notify`-t. Egy
    #: sosem tüzelő „Changed" jelzés csak félrevezetné az olvasót.
    JELZES_NELKUL = ("collageNodes",)

    @pytest.mark.parametrize("nev", PROPERTYK)
    def test_minden_property_letezik(self, host, nev):
        assert hasattr(type(host), nev), f"hiányzik a property: {nev}"
        getattr(host, nev)  # olvasható, és nem dob

    @pytest.mark.parametrize("nev", PROPERTYK)
    def test_minden_property_jelzest_kap(self, host, nev):
        if nev in TestApiFelulet.JELZES_NELKUL:
            pytest.skip("constant property — nincs (és nem is lehet) jelzése")
        assert hasattr(host, f"{nev}Changed"), f"hiányzik: {nev}Changed"

    @pytest.mark.parametrize("nev", SLOTOK)
    def test_minden_slot_letezik(self, host, nev):
        assert callable(getattr(host, nev))

    @pytest.mark.parametrize("nev", JELZESEK)
    def test_minden_jelzes_letezik(self, host, nev):
        jelzes = getattr(host, nev)
        assert hasattr(jelzes, "connect"), f"nem jelzés: {nev}"
