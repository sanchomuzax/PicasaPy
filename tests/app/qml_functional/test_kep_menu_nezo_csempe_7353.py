"""A Kép menü effektparancsai a nézőben: a célfülre váltanak, és a NYITOTT képre
alkalmaznak, a könyvtári kijelölést nem érintik (#7353, #7371).

## Előzmény

A #7353 a menüparancsnál csak kék kiemeléssel jelölte ki a célcsempét,
alkalmazás nélkül. A #7346 kutatás megdöntötte ezt az olvasatot: az eredeti
a csempekattintással egyenértékű hatást ad, ezért a #7371 óta a parancs a
csempe útján azonnal hat. A kiemelés-gépezet (`menuEffectSelection`)
ezért megszűnt, és ez a fájl a vele járó viselkedést már nem várja.

## Mit mér ez a fájl, és miben egészíti ki a #7371 próbáit

A `test_csoportos_szerkesztes_nezoben_7371.py` azt az esetet méri, amikor a
megnyitott kép egyben a könyvtári kijelölés első eleme. Itt a néző MÁS képet
mutat, mint a kijelölés (egy- és kétképes kijelöléssel), és az ablak
magassága is változik, mert a menükattintás geometriája platformfüggő:

- a célfül kiválasztódik, és az effekt a nyitott kép láncára kerül;
- a kijelölt és a többi kép lánca nem változik, kötegművelet nem indul;
- a néző nyitva marad, a kijelölés (`selectedIndex(es)`) változatlan;
- a Sharpen a csempéjével azonos módon a paraméterpanelt nyitja meg, a
  lánc az Alkalmazás előtt nem változik;
- a menüparancs után egyetlen csempe sem marad kiemelve.

A vizuális egyezést (az eredeti Picasa képe vs. a miénk) ez a fájl NEM méri.
"""

from __future__ import annotations

import pytest

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    gyerek,
    kijelol,
    szures,
    tetel_kattintasa,
    varj,
)
from tests.app.qml_functional._szerkeszto_5150_helpers import item, kattint

_BATCH = ("menuPictureBatchEdit",)

#: A néző ezt a képet mutatja; a kijelölés első eleme MÁS kép (0).
_NYITOTT_SOR = 1

#: Menütétel, effektnév, fül, csempe, a lánc kulcsa (None: paraméterpanel).
_EFFEKTEK = (
    ("menuBatchAutoContrast", "autolight", 0, "editToolAutolight", "autolight=1;"),
    ("menuBatchAutoColor", "autocolor", 0, "editToolAutocolor", "autocolor=1;"),
    ("menuBatchEnhance", "enhance", 0, "editToolEnhance", "enhance=1;"),
    ("menuBatchSepia", "sepia", 2, "effectSepia", "sepia=1;"),
    ("menuBatchSharpen", "unsharp", 2, "effectUnsharp", None),
    ("menuBatchWarmify", "warm", 2, "effectWarm", "warm=1;"),
    ("menuBatchFilmGrain", "grain2", 2, "effectGrain2", "grain2=1;"),
    ("menuBatchBlackWhite", "bw", 2, "effectBw", "bw=1;"),
)
_ESETEK = [pytest.param(i, *e, id=e[1]) for i, e in enumerate(_EFFEKTEK)]


@pytest.fixture
def kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _nezo_a_masodik_kepen(window, qt_app, sorok, eltolas, kezdo_ful):
    """Néző a második képen, a megadott kijelöléssel és ablakmagassággal."""
    viewer = gyerek(window, "photoViewer")
    panel = gyerek(window, "viewerEditorPanel")
    window.setProperty("viewerOpen", True)
    viewer.setProperty("currentIndex", _NYITOTT_SOR)
    qt_app.processEvents()
    window.resize(window.width(), window.height() + eltolas)
    kijelol(window, qt_app, sorok)
    viewer.setProperty("currentIndex", _NYITOTT_SOR)
    panel.setProperty("activeTab", kezdo_ful)
    qt_app.processEvents()
    return viewer, panel


@pytest.mark.parametrize(
    ("index", "tetel", "nev", "ful", "csempe", "kulcs"), _ESETEK
)
def test_nezoben_a_menuparancs_a_nyitott_kepre_hat_a_kijelolest_nem_erinti(
    kep_app, qt_app, index, tetel, nev, ful, csempe, kulcs
):
    window, controller, _engine = kep_app
    elokeszit(window, qt_app, controller)
    sorok = [0] if index % 2 == 0 else [0, 1]
    # A kiinduló fül a célfüllel ellentétes, így a fülváltás is bizonyít.
    viewer, panel = _nezo_a_masodik_kepen(
        window, qt_app, sorok, (-5, 0, 5)[index % 3], 2 if ful == 0 else 0
    )
    assert panel.property("activeTab") != ful, (
        "a kiinduló fül már a célfül: a fülváltás nem bizonyít"
    )
    sorok_szama = len(controller.photos.photos)
    assert [szures(controller, sor) for sor in range(sorok_szama)] == [""] * sorok_szama, (
        "a kiinduló láncok nem üresek: a teszt nem bizonyít"
    )

    tetel_kattintasa(window, qt_app, "&Picture", tetel, almenu_utvonal=_BATCH)

    assert varj(qt_app, lambda: panel.property("activeTab") == ful), (
        f"a {tetel} nem a célfület választotta (fül={panel.property('activeTab')})"
    )
    if kulcs is None:
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is True), (
            f"a {tetel} nem nyitotta meg a paraméterpanelt"
        )
        assert szures(controller, _NYITOTT_SOR) == "", (
            f"a {tetel} az Alkalmazás előtt a nyitott kép láncára került"
        )
        kattint(window, item(window, "effectParamCancelButton"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is False)
    else:
        assert varj(
            qt_app, lambda: szures(controller, _NYITOTT_SOR).endswith(kulcs)
        ), (
            f"a {tetel} nem került a nyitott kép láncára: "
            f"{szures(controller, _NYITOTT_SOR)!r}"
        )
    for sor in range(sorok_szama):
        if sor != _NYITOTT_SOR:
            assert szures(controller, sor) == "", (
                f"a nézőben a {tetel} a nem nyitott {sor}. kép láncát is módosította"
            )

    assert window.property("viewerOpen") is True
    assert viewer.property("currentIndex") == _NYITOTT_SOR
    assert window.property("selectedIndex") == sorok[0]
    assert list(window.property("selectedIndexes")) == sorok
    assert controller.batchEditActive is False
    assert controller.canUndoBatchEdit is False
    for _t, _n, _f, masik_csempe, _k in _EFFEKTEK:
        assert gyerek(window, masik_csempe).property("active") is False, (
            f"a {tetel} után a {masik_csempe} csempe kiemelve maradt"
        )


def test_a_kep_menu_nem_hagy_menuhoz_kotott_kijelolest_a_panelen(kep_app, qt_app):
    """A menüparancsnak nincs külön kijelölés-állapota: a csempe útján hat."""
    window, controller, _engine = kep_app
    elokeszit(window, qt_app, controller)
    _viewer, panel = _nezo_a_masodik_kepen(window, qt_app, [0], 0, 0)

    tetel_kattintasa(
        window, qt_app, "&Picture", "menuBatchSepia", almenu_utvonal=_BATCH
    )

    assert varj(
        qt_app, lambda: szures(controller, _NYITOTT_SOR).endswith("sepia=1;")
    ), "a Sepia nem hatott: az állítás nem bizonyít"
    assert panel.metaObject().indexOfProperty("menuEffectSelection") < 0, (
        "a panelen megmaradt a Kép menü kiemelés-állapota"
    )
