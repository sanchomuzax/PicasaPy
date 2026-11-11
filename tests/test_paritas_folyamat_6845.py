"""A folyamatszintű képernyőkép-felvevő tesztje (#6845).

Két réteg:

* a lépéssor-értelmező (`scripts/paritas_lepesek.py`) tiszta Python: az
  érvénytelen lépés érthető hibát ad, még mielőtt bármi elindulna;
* a futtató (`scripts/paritas_folyamat.py`) offscreen, egy tesztkönyvtárral:
  füstfutás (egy kijelölés + egy ablakkép) és az ismeretlen objectName
  érthető hibája.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import paritas_folyamat as folyamat
from scripts import paritas_lepesek as lepesek

GYOKER = Path(__file__).resolve().parents[1]
FUTTATO = GYOKER / "scripts" / "paritas_folyamat.py"

ELSO_HASZNALAT = (
    '[{"kijelol":3},{"kijelol_mod":[4,"ctrl"]},{"jobbklikk":4},'
    '{"menupont":"contextMenuMove"},{"var":2},{"billentyu":"ctrl+a"},'
    '{"gepel":"UjMappa"},{"billentyu":"Return"},{"var":5}]'
)


# --- a lépéssor-értelmező ---------------------------------------------------


def test_az_elso_hasznalat_lepessora_ertelmezheto():
    sor = lepesek.ertelmez(json.loads(ELSO_HASZNALAT))

    assert [lepes.fajta for lepes in sor] == [
        "kijelol",
        "kijelol_mod",
        "jobbklikk",
        "menupont",
        "var",
        "billentyu",
        "gepel",
        "billentyu",
        "var",
    ]
    assert sor[0].racsindex == 3
    assert (sor[1].racsindex, sor[1].modosito) == (4, "ctrl")
    assert sor[3].objektumnev == "contextMenuMove"
    assert sor[3].fomenu is None
    assert sor[4].masodperc == 2.0
    assert sor[5].billentyu == "ctrl+a"
    assert sor[6].szoveg == "UjMappa"


def test_a_fomenu_a_menupont_melle_all():
    sor = lepesek.ertelmez(
        [{"fomenu": "menuView", "menupont": "menuViewLibraryView"}]
    )

    assert sor[0].fajta == "menupont"
    assert sor[0].fomenu == "menuView"
    assert sor[0].objektumnev == "menuViewLibraryView"


def test_a_mappa_jobbklikk_es_a_mappanev():
    sor = lepesek.ertelmez([{"jobbklikk_mappa": "PicasaTeszt"}])

    assert sor[0].fajta == "jobbklikk_mappa"
    assert sor[0].mappanev == "PicasaTeszt"


@pytest.mark.parametrize(
    ("nyers", "varhato"),
    [
        ("Return", "return"),
        ("enter", "return"),
        ("ESC", "escape"),
        ("Ctrl+A", "ctrl+a"),
        ("control+shift+o", "ctrl+shift+o"),
        ("shift+ctrl+o", "ctrl+shift+o"),
        ("F2", "f2"),
        ("Del", "delete"),
        ("PageDown", "pagedown"),
    ],
)
def test_a_billentyu_egysegesitett_alakot_kap(nyers, varhato):
    sor = lepesek.ertelmez([{"billentyu": nyers}])

    assert sor[0].billentyu == varhato


def test_a_lepes_eredeti_alakja_megmarad_a_naplohoz():
    sor = lepesek.ertelmez([{"kijelol_mod": [4, "Ctrl"]}])

    assert json.loads(sor[0].eredeti) == {"kijelol_mod": [4, "Ctrl"]}


def _hiba(adat) -> str:
    with pytest.raises(lepesek.LepesHiba) as kivetel:
        lepesek.ertelmez(adat)
    return str(kivetel.value)


def test_nem_lista_bemenet_ertheto_hibat_ad():
    assert "lista" in _hiba({"kijelol": 1})


def test_ures_lista_hibat_ad():
    assert "legalább egy lépés" in _hiba([])


def test_a_nem_objektum_lepes_hibaja_megnevezi_a_lepes_sorszamat():
    uzenet = _hiba([{"kijelol": 0}, "kattints"])

    assert "2. lépés" in uzenet
    assert "objektum" in uzenet


def test_ismeretlen_lepesfajta_hibaja_felsorolja_az_ervenyeseket():
    uzenet = _hiba([{"kattints": 1}])

    assert "1. lépés" in uzenet
    assert "kattints" in uzenet
    assert "kijelol" in uzenet and "billentyu" in uzenet


def test_ures_objektum_lepes_hibat_ad():
    assert "1. lépés" in _hiba([{}])


def test_ket_lepesfajta_egy_lepesben_hibat_ad():
    uzenet = _hiba([{"kijelol": 1, "jobbklikk": 2}])

    assert "1. lépés" in uzenet
    assert "egyetlen" in uzenet


@pytest.mark.parametrize(
    "ertek", [True, -1, 1.5, "3", None, [1]], ids=repr
)
def test_a_racsindex_nemnegativ_egesz(ertek):
    uzenet = _hiba([{"kijelol": ertek}])

    assert "1. lépés" in uzenet
    assert "rácsindex" in uzenet


@pytest.mark.parametrize(
    "ertek",
    [[4], [4, "ctrl", "x"], "ctrl", [4, "alt"], ["4", "ctrl"], [4, 7]],
    ids=repr,
)
def test_a_kijelol_mod_ket_elemu_es_ctrl_vagy_shift(ertek):
    uzenet = _hiba([{"kijelol_mod": ertek}])

    assert "1. lépés" in uzenet
    assert "kijelol_mod" in uzenet


@pytest.mark.parametrize("kulcs", ["menupont", "jobbklikk_mappa"])
@pytest.mark.parametrize("ertek", ["", "   ", 5, None])
def test_a_nevlepes_nem_lehet_ures_vagy_nem_szoveg(kulcs, ertek):
    uzenet = _hiba([{kulcs: ertek}])

    assert "1. lépés" in uzenet
    assert kulcs in uzenet


@pytest.mark.parametrize("ertek", ["", 5, None, ["a"]])
def test_a_gepelt_szoveg_nem_lehet_ures_vagy_nem_szoveg(ertek):
    uzenet = _hiba([{"gepel": ertek}])

    assert "1. lépés" in uzenet
    assert "gepel" in uzenet


def test_a_gepelt_szoveg_szokozeit_megtartja():
    sor = lepesek.ertelmez([{"gepel": "  Uj Mappa "}, {"gepel": " "}])

    assert [lepes.szoveg for lepes in sor] == ["  Uj Mappa ", " "]


def test_a_fomenu_onmagaban_hibat_ad():
    uzenet = _hiba([{"fomenu": "menuView"}])

    assert "fomenu" in uzenet
    assert "menupont" in uzenet


def test_a_fomenu_mas_lepesfajta_mellett_hibat_ad():
    assert "fomenu" in _hiba([{"fomenu": "menuView", "kijelol": 1}])


def test_a_fomenu_nem_lehet_ures():
    assert "fomenu" in _hiba([{"fomenu": "", "menupont": "x"}])


@pytest.mark.parametrize(
    "ertek", ["", "ctrl", "ctrl+", "ctrl+bogus", "+a", "ctrl+a+b", 5, None]
)
def test_ervenytelen_billentyu_ertheto_hibat_ad(ertek):
    uzenet = _hiba([{"billentyu": ertek}])

    assert "1. lépés" in uzenet
    assert "billentyu" in uzenet


@pytest.mark.parametrize(
    "ertek", [-1, True, "2", None, float("nan"), float("inf"), 601]
)
def test_a_var_masodperce_vegesen_nemnegativ_szam(ertek):
    uzenet = _hiba([{"var": ertek}])

    assert "1. lépés" in uzenet
    assert "var" in uzenet


def test_a_tort_masodperc_megengedett():
    assert lepesek.ertelmez([{"var": 0.5}])[0].masodperc == 0.5


def test_ervenytelen_json_ertheto_hibat_ad():
    with pytest.raises(lepesek.LepesHiba) as kivetel:
        lepesek.betolt('[{"kijelol": 1},')

    assert "JSON" in str(kivetel.value)


def test_a_lepessor_fajlbol_is_betoltheto(tmp_path):
    fajl = tmp_path / "lepesek.json"
    fajl.write_text('[{"kijelol": 2}]', encoding="utf-8")

    sor = lepesek.betolt(str(fajl))

    assert sor[0].racsindex == 2


def test_a_hianyzo_lepessor_fajl_ertheto_hibat_ad(tmp_path):
    with pytest.raises(lepesek.LepesHiba) as kivetel:
        lepesek.betolt(str(tmp_path / "nincs.json"))

    assert "nincs.json" in str(kivetel.value)


def test_a_parancssor_ervenytelen_lepessorral_ketteshez_ter_vissza(tmp_path):
    eredmeny = subprocess.run(
        [
            sys.executable,
            str(FUTTATO),
            "futtat",
            "--lepesek",
            '[{"kattints": 1}]',
            "--kimenet",
            str(tmp_path / "ki"),
        ],
        cwd=GYOKER,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert eredmeny.returncode == 2
    assert "kattints" in eredmeny.stderr
    assert not (tmp_path / "ki").exists()


# --- a futtató: offscreen ------------------------------------------------------


@pytest.fixture(scope="module")
def qt_app():
    from PySide6.QtGui import QGuiApplication

    # A gép valódi (Wayland) képernyőjét a teszt nem érintheti: az offscreen
    # platformot kikényszerítjük, nem csak alapértelmezzük.
    with pytest.MonkeyPatch.context() as javitas:
        javitas.setenv("QT_QPA_PLATFORM", "offscreen")
        javitas.setenv("QT_QUICK_BACKEND", "software")
        app = QGuiApplication.instance() or QGuiApplication([])
        yield app
        app.processEvents()


def _modul(nev: str):
    """A Qt-t betöltő testvérmodul, késleltetve: az értelmező-tesztek Qt nélkül futnak."""
    return importlib.import_module(f"scripts.{nev}")


def test_a_futas_idejere_a_valodi_kepernyo_valtozoi_eltunnek_es_visszaterenek(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")

    with folyamat._kepernyo_nelkul():
        assert "DISPLAY" not in os.environ
        assert "WAYLAND_DISPLAY" not in os.environ

    assert os.environ["DISPLAY"] == ":0"
    assert os.environ["WAYLAND_DISPLAY"] == "wayland-0"


def test_a_futas_idejere_a_munkamappaba_lep_es_visszalep(tmp_path):
    korabbi = Path.cwd()

    with folyamat._munkamappaban(tmp_path):
        assert Path.cwd().resolve() == tmp_path.resolve()

    assert Path.cwd() == korabbi


def test_a_teszkonyvtar_24_kepet_ad_rogzitett_mtime_mal(tmp_path):
    lib = tmp_path / "kepek"
    lib.mkdir()

    folyamat.teszt_mappa_keszitese(lib)

    kepek = sorted((lib / folyamat.TESZT_MAPPA).glob("*.jpg"))
    assert len(kepek) == 24
    idok = [kep.stat().st_mtime_ns for kep in kepek]
    assert idok == sorted(set(idok)), "az mtime-ok egyediek és névsorrendben nőnek"
    assert idok == [
        (folyamat.MINTA_MTIME + index * folyamat.MINTA_MTIME_LEPES) * 10**9
        for index in range(24)
    ]


def test_a_nem_ures_munkakonyvtar_ertheto_hibat_ad(qt_app, tmp_path):
    munka = tmp_path / "munka"
    munka.mkdir()
    (munka / "regi.txt").write_text("x", encoding="utf-8")

    with pytest.raises(ValueError) as kivetel:
        folyamat.futtat(
            lepesek.ertelmez([{"kijelol": 0}]),
            tmp_path / "ki",
            qt_app=qt_app,
            munkakonyvtar=munka,
        )

    assert "nem üres" in str(kivetel.value)
    assert not (tmp_path / "ki").exists()


# --- teljes futások (egy-egy alkalmazásépítéssel) ------------------------------


def test_a_fusstfutas_kijelolest_es_helyi_menut_rogzit(qt_app, tmp_path):
    kimenet = tmp_path / "ki"

    manifest = folyamat.futtat(
        lepesek.ertelmez([{"kijelol": 0}, {"jobbklikk": 2}]),
        kimenet,
        qt_app=qt_app,
        munkakonyvtar=tmp_path / "munka",
    )

    assert manifest["siker"] is True
    assert [lepes["sorszam"] for lepes in manifest["lepesek"]] == [1, 2]
    for sorszam in range(3):
        assert (kimenet / f"kepernyo__{sorszam:02d}.png").is_file()
    from PySide6.QtGui import QImage

    kep = QImage(str(kimenet / "kepernyo__01.png"))
    assert not kep.isNull() and kep.width() >= 800 and kep.height() >= 600
    assert manifest["kezdo"]["allapot"]["kijeloles"] == []
    assert manifest["lepesek"][0]["allapot"]["kijeloles"] == [0]
    # a jobb klikk a 0. kijelölést a 2. képre cseréli, és megnyitja a helyi menüt
    masodik = manifest["lepesek"][1]["allapot"]
    assert masodik["kijeloles"] == [2]
    assert masodik["nyitott_parbeszedek"] == ["photoContextMenu"]
    elotte = (kimenet / "kepernyo__01.png").read_bytes()
    utana = (kimenet / "kepernyo__02.png").read_bytes()
    assert elotte != utana, "a megnyílt helyi menünek látszania kell az ablakképen"

    allapot = json.loads((kimenet / "allapot.json").read_text(encoding="utf-8"))
    assert allapot["racs"]["elemszam"] == 24
    assert allapot["racs"]["fajlnevek"][:2] == ["kep_01.jpg", "kep_02.jpg"]
    assert allapot["racs"]["aktualis_mappa"] == folyamat.TESZT_MAPPA
    assert allapot["lemez"]["mappak"] == [folyamat.TESZT_MAPPA]
    assert len(allapot["lemez"]["fajlok"]) == 24
    assert allapot["lemez"]["fajlok"][0]["ut"] == f"{folyamat.TESZT_MAPPA}/kep_01.jpg"
    assert allapot["lemez"]["kivul"] == []
    assert any(
        sor["nev"] == folyamat.TESZT_MAPPA and sor["darab"] == 24
        for sor in allapot["bal_hasab"]["modell"]
    )
    assert "photoContextMenu" in allapot["nyitott_parbeszedek"]
    assert allapot["kijeloles"]["indexek"] == [2]


def test_a_fomenus_folyamat_az_ekezetes_nevet_helyesen_gepeli_be(qt_app, tmp_path):
    """Valódi kattintás a menüsoron és a tételen, ctrl+a, gépelés, Return.

    A `QTest.sendKeyEvent` a PySide-ban a `char` túlterhelést választja, és a
    `É` `Ã` lenne: a nem ASCII karaktert a felvevő külön küldi."""
    kimenet = tmp_path / "ki"

    manifest = folyamat.futtat(
        lepesek.ertelmez(
            [
                {"kijelol": 0},
                {"kijelol_mod": [1, "shift"]},
                {"fomenu": "File", "menupont": "menuFileMoveToNewFolder"},
                {"var": 1},
                {"billentyu": "ctrl+a"},
                {"gepel": "Új Éé"},
                {"billentyu": "Return"},
                {"var": 2},
            ]
        ),
        kimenet,
        qt_app=qt_app,
        munkakonyvtar=tmp_path / "munka",
    )

    assert manifest["siker"] is True, manifest["lepesek"]
    harmadik = manifest["lepesek"][2]["allapot"]
    assert harmadik["nyitott_parbeszedek"] == ["moveToNewFolderDialog"]
    allapot = json.loads((kimenet / "allapot.json").read_text(encoding="utf-8"))
    assert f"{folyamat.TESZT_MAPPA}/Új Éé" in allapot["lemez"]["mappak"]
    athelyezett = [
        fajl["ut"]
        for fajl in allapot["lemez"]["fajlok"]
        if fajl["ut"].startswith(f"{folyamat.TESZT_MAPPA}/Új Éé/kep_")
    ]
    assert athelyezett == [
        f"{folyamat.TESZT_MAPPA}/Új Éé/kep_01.jpg",
        f"{folyamat.TESZT_MAPPA}/Új Éé/kep_02.jpg",
    ]
    nevek = [sor["nev"] for sor in allapot["bal_hasab"]["lathato_sorok"]]
    assert "Új Éé" in nevek and folyamat.TESZT_MAPPA in nevek


def test_a_hibas_lepes_utan_a_kep_a_manifest_es_az_allapot_megmarad(qt_app, tmp_path):
    kimenet = tmp_path / "ki"

    manifest = folyamat.futtat(
        lepesek.ertelmez([{"kijelol": 0}, {"menupont": "nincsIlyenObjektum"}, {"kijelol": 1}]),
        kimenet,
        qt_app=qt_app,
        munkakonyvtar=tmp_path / "munka",
    )

    assert manifest["siker"] is False
    assert len(manifest["lepesek"]) == 2, "a hiba után a futás megáll"
    hiba = manifest["lepesek"][1]["hiba"]
    assert "nincsIlyenObjektum" in hiba
    assert "2. lépés" in hiba
    assert (kimenet / "kepernyo__02.png").is_file(), "a hibás lépés képe is megvan"
    assert not (kimenet / "kepernyo__03.png").exists()
    assert (kimenet / "allapot.json").is_file()
    assert (kimenet / "manifest.json").is_file()


# --- lépések egy közös, élő alkalmazáson -----------------------------------------


@pytest.fixture(scope="module")
def elo(qt_app, tmp_path_factory):
    munka = tmp_path_factory.mktemp("paritas") / "munka"
    with folyamat.alkalmazas_inditasa(qt_app=qt_app, munkakonyvtar=munka) as kon:
        yield kon


@pytest.fixture
def tiszta(elo):
    """Minden teszt kijelölés és nyitott réteg nélküli állapotból indul és oda tér vissza."""
    qt = _modul("paritas_qt")

    allapot = _modul("paritas_allapot")

    def _alaphelyzet():
        for _ in range(3):
            qt.billentyu_kuldese(elo.alkalmazas, elo.ablak, "escape")
        elo.ablak.setProperty("selectedIndexes", [])
        elo.ablak.setProperty("selectedIndex", -1)
        assert qt.var_feltetelre(
            elo.alkalmazas, lambda: not allapot.nyitott_retegek(elo.ablak), 10.0
        ), "a nyitott rétegek nem zárultak be"

    _alaphelyzet()
    yield elo
    _alaphelyzet()


def _vegrehajt(kon, adat):
    lepes = lepesek.ertelmez([adat])[0]
    _modul("paritas_vegrehajt").vegrehajt(kon, lepes)


def _kijeloles(kon) -> list[int]:
    return _modul("paritas_allapot").kijeloles(kon.vezerlo, kon.ablak)["indexek"]


def _hibaszoveg(kon, adat) -> str:
    qt = _modul("paritas_qt")
    with pytest.raises(qt.FuttatasiHiba) as kivetel:
        _vegrehajt(kon, adat)
    return str(kivetel.value)


def test_a_ctrl_kattintas_hozzaad_a_shift_kattintas_tartomanyt_jelol(tiszta):
    _vegrehajt(tiszta, {"kijelol": 3})
    _vegrehajt(tiszta, {"kijelol_mod": [5, "ctrl"]})
    assert _kijeloles(tiszta) == [3, 5]

    _vegrehajt(tiszta, {"kijelol": 0})
    _vegrehajt(tiszta, {"kijelol_mod": [2, "shift"]})
    assert _kijeloles(tiszta) == [0, 1, 2]


def test_az_also_sor_kepe_a_racs_gorgetesevel_kijelolheto(tiszta):
    _vegrehajt(tiszta, {"kijelol": 23})

    assert _kijeloles(tiszta) == [23]


def test_a_mappasor_jobb_klikkje_megnyitja_a_mappa_menujet(tiszta):
    _vegrehajt(tiszta, {"jobbklikk_mappa": folyamat.TESZT_MAPPA})

    nevek = _modul("paritas_allapot").nyitott_retegek(tiszta.ablak)
    assert "folderContextMenu" in [reteg["objectName"] for reteg in nevek]


def test_az_almenu_neve_megnyitja_az_almenut(tiszta):
    from PySide6.QtCore import QObject

    _vegrehajt(tiszta, {"jobbklikk": 2})
    _vegrehajt(tiszta, {"menupont": "contextMenuOpenWithMenu"})

    almenu = tiszta.ablak.findChild(QObject, "contextMenuOpenWithMenu")
    assert almenu.property("visible") is True


@pytest.mark.parametrize("fomenu", ["menuView", "&View", "view"])
def test_a_fomenu_objectnevvel_es_cimmel_is_megnyithato(tiszta, fomenu):
    """A Library View tétel a könyvtárban tiltott: a valódi kattintás nem változtat semmit."""
    _vegrehajt(tiszta, {"fomenu": fomenu, "menupont": "menuViewLibraryView"})

    retegek = _modul("paritas_allapot").nyitott_retegek(tiszta.ablak)
    assert "menuView" in [reteg["objectName"] for reteg in retegek]


def test_az_ismeretlen_objectnev_hibaja_megnevezi_a_hianyzot_es_a_latszo_menuket(
    tiszta, monkeypatch
):
    monkeypatch.setattr(_modul("paritas_qt"), "KATTINTAS_HATARIDO_MP", 0.3)
    _vegrehajt(tiszta, {"jobbklikk": 2})

    uzenet = _hibaszoveg(tiszta, {"menupont": "nincsIlyenObjektum"})

    assert "nincsIlyenObjektum" in uzenet
    assert "nincs ilyen objectName" in uzenet
    assert "contextMenuMove" in uzenet, "a látható menü-objektumokat felsorolja"


def test_a_lathatatlan_de_letezo_objektum_hibaja_ezt_kulon_mondja(tiszta, monkeypatch):
    monkeypatch.setattr(_modul("paritas_qt"), "KATTINTAS_HATARIDO_MP", 0.3)

    uzenet = _hibaszoveg(tiszta, {"menupont": "contextMenuMove"})

    assert "contextMenuMove" in uzenet
    assert "nem látható" in uzenet


def test_az_ismeretlen_mappanev_felsorolja_a_latszo_mappakat(tiszta):
    uzenet = _hibaszoveg(tiszta, {"jobbklikk_mappa": "NincsIlyenMappa"})

    assert "NincsIlyenMappa" in uzenet
    assert folyamat.TESZT_MAPPA in uzenet


def test_a_tul_nagy_racsindex_hibaja_megnevezi_az_indexet(tiszta):
    uzenet = _hibaszoveg(tiszta, {"kijelol": 99})

    assert "99" in uzenet


def test_az_ismeretlen_fomenu_hibaja_felsorolja_a_menusort(tiszta):
    uzenet = _hibaszoveg(tiszta, {"fomenu": "NincsIlyen", "menupont": "x"})

    assert "NincsIlyen" in uzenet
    assert "file" in uzenet and "help" in uzenet


def test_a_gepeles_es_a_billentyu_szovegmezo_nelkul_nem_hasal_el(tiszta):
    _vegrehajt(tiszta, {"gepel": "abc Éé"})
    _vegrehajt(tiszta, {"billentyu": "ctrl+shift+f2"})
    _vegrehajt(tiszta, {"var": 0})
