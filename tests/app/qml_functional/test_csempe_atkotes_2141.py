"""#2141 — az 1. effekt-fül három csempéje az EREDETI elsődlegest hívja.

Az eredeti csempe-táblája (`0x00c7e5a0`, 36 rekord × 12 bájt) szerint az
1. fül első hat csempéje: `unsharp2`, `sepia`, `bw`, `warm`, `PicnikGrain`,
`PicnikTint`. A hármas második eleme (`unsharp`, `grain`, `tint`) a
**Shift** lenyomásakor lép be — Shift nélkül az eredetiben sem fut.

Nálunk három csempe a másodlagost hívta, kettőnél az elsődleges
feliratával. A `grain2` ráadásul `oneclick`, ezért a Filmszemcse
**jelvényt** kapott, holott az eredetiben nincs rajta.

⚠️ A próba a **`buttonClicked` jelet** bocsátja ki — a valódi kattintás
útját —, nem a QML forrását olvassa: a szövegre nézve mindhárom csempe
zöld volt a hibás kötés mellett is.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, QUrl, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine

#: A betöltött objektumokat életben kell tartani (Qt-tulajdonjog).
_KEEPALIVE: list = []


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _make_panel(engine):
    """A szerkesztő-panel az EFFEKTEK fülön (`activeTab: 2`)."""
    component = QQmlComponent(engine)
    component.setData(
        b'import QtQuick\nimport PicasaPy 1.0\n'
        b'EditorPanel { objectName: "panel"; activeTab: 2 }\n',
        QUrl(),
    )
    obj = component.create()
    hibak = [e.toString() for e in component.errors()]
    assert hibak == [], hibak
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(component)
    _KEEPALIVE.append(obj)
    return obj


#: (elemnév, a hívandó kulcs) — az eredeti tábla szerint.
CSEMPEK = [
    ("effectUnsharp", "unsharp2"),
    ("effectGrain2", "picnikgrain"),
    ("effectTint", "picniktint"),
]


class TestAHaromCsempeAzEredetitHivja:
    @pytest.mark.parametrize("elemnev,kulcs", CSEMPEK)
    def test_a_csempe_az_elsodleges_szurot_hivja(
        self, qml_engine, qt_app, elemnev, kulcs
    ):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        kert: list[str] = []
        panel.effectRequested.connect(lambda nev: kert.append(nev))
        # A paraméter-panel útját is figyeljük: ha a csempének csúszkája
        # van, a `tryOpenParamPanel` nyeli el a kattintást, és a kulcs a
        # `paramEffectName`-be kerül az `effectRequested` helyett.
        gomb = panel.findChild(QObject, elemnev)
        assert gomb is not None, f"nincs ilyen csempe: {elemnev}"
        QMetaObject.invokeMethod(
            gomb, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert kert == [kulcs] or panel.property("paramEffectName") == kulcs, (
            f"a {elemnev} csempe nem a {kulcs!r} szűrőt hívta (kért: {kert}, "
            f"panel-kulcs: {panel.property('paramEffectName')!r})"
        )


class TestAFeliratokValtozatlanok:
    """A felirat és a hívás KÜLÖN mérendő — az átkötés a feliratot nem
    érintheti (a csempe felirata az elsődlegesé volt már eddig is)."""

    FELIRATOK = [
        ("effectUnsharp", "Sharpen"),
        ("effectGrain2", "Film Grain"),
        ("effectTint", "Tint"),
    ]

    @pytest.mark.parametrize("elemnev,felirat", FELIRATOK)
    def test_a_felirat_nem_valtozott(self, qml_engine, qt_app, elemnev, felirat):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        gomb = panel.findChild(QObject, elemnev)
        assert gomb.property("label") == felirat


class TestAJelvenyAFilmszemcserolEltunik:
    """A jegy harmadik pontja — mérve, nem feltételezve.

    A jelvényt a szűrő `mode`-ja dönti el (`oneclick` → jelvény). A
    `grain2` `oneclick`, a `PicnikGrain` `effect`: az átkötés ezért
    magától eltünteti a jelvényt a Filmszemcséről, és a másik kettőn
    (mindkét oldal `effect`) nem változtat semmit.
    """

    def test_a_filmszemcse_mar_nem_oneclick(self):
        from picasapy.render.registry import get_filter_spec

        assert get_filter_spec("grain2").mode == "oneclick"
        assert get_filter_spec("picnikgrain").mode == "effect"

    def test_a_masik_ketto_jelvenyallapota_valtozatlan(self):
        from picasapy.render.registry import get_filter_spec

        for regi, uj in [("unsharp", "unsharp2"), ("tint", "picniktint")]:
            assert (
                get_filter_spec(regi).mode == get_filter_spec(uj).mode
            ), f"{regi} és {uj} módja eltér — a jelvény-állapot változna"


class TestAHaromCelSzuroTENYLEG_RENDEREL:
    """⚠️ Működő vezérlőt hatástalanra cserélni rosszabb, mint a hibás kötés.

    A golden-összevetés (a jegy 2. pontja) itt a MÉRHETŐ része: mind a
    három cél-szűrő megváltoztatja a képet. A `PicnikGrain` `darken`
    módú szürke zaj, ezért VILÁGOS képen mérendő — sötét mintán a
    `min(kép, zaj)` a képet adja vissza, és tévesen »nem hat«-nak
    látszik (ebbe menet közben belefutottam).
    """

    def _elteres(self, kulcs, params, kep):
        import numpy as np

        from picasapy.ini.filters import FilterOp
        from picasapy.render.chain import apply_filters

        r = apply_filters(kep, (FilterOp(kulcs, params),))
        ki = np.asarray(r.image if hasattr(r, "image") else r)
        return int(np.abs(ki.astype(int) - kep.astype(int)).sum())

    def test_mindharom_celszuro_valtoztat_a_kepen(self):
        """⚠️ A láncba az INI-NÉV megy, nem a vezérlő-kulcs.

        A vezérlő kulcsa kisbetűs (`picnikgrain`), a `.picasa.ini`-be
        viszont a Picasa írásmódja kerül (`PicnikGrain`) — ezt az
        `_EFFECT_INI_NAMES` képezi le. Kisbetűs névvel a renderelő NÉMÁN
        kihagyja a szűrőt (`skipped`), ezért itt az ini-néven mérünk:
        ugyanazon a leképezésen át, amit a vezérlő is használ."""
        import numpy as np

        from picasapy.app.edit_controller import _EFFECT_INI_NAMES

        rng = np.random.default_rng(7)
        vilagos = rng.integers(200, 256, size=(40, 50, 3), dtype=np.uint8)

        def ininev(kulcs):
            return _EFFECT_INI_NAMES.get(kulcs, kulcs)

        assert self._elteres(ininev("unsharp2"), ("1", "60"), vilagos) > 0
        assert self._elteres(ininev("picnikgrain"), ("1", "50"), vilagos) > 0
        assert self._elteres(ininev("picniktint"), ("1", "0"), vilagos) > 0

    def test_a_harom_kulcs_INI_NEVE_a_renderelot_talalja(self):
        """Az őr, ami a fenti csapdát a jövőben elkapja.

        Ha egy csempe kulcsához hiányzik az ini-név-leképezés, a szűrő
        némán kimarad a láncból: a felhasználó rákattint, és nem történik
        semmi. Ez a próba a `skipped` listát nézi, nem a képet."""
        import numpy as np

        from picasapy.app.edit_controller import _EFFECT_INI_NAMES
        from picasapy.ini.filters import FilterOp
        from picasapy.render.chain import apply_filters

        rng = np.random.default_rng(5)
        kep = rng.integers(200, 256, size=(20, 25, 3), dtype=np.uint8)
        for kulcs in ["unsharp2", "picnikgrain", "picniktint"]:
            ini = _EFFECT_INI_NAMES.get(kulcs, kulcs)
            r = apply_filters(kep, (FilterOp(ini, ("1", "10")),))
            assert not list(r.skipped), (
                f"{kulcs} (ini: {ini}) kimaradt a láncból: {list(r.skipped)}"
            )

    def test_az_unsharp_es_unsharp2_az_ALAPERTEKEN_azonos(self):
        """Az átkötés a szokásos használatban nem változtat a képen.

        Mindkettő ugyanazt a feldolgozót hívja, és az alapértékük ugyanaz
        (0,6). A CSÚSZKA-TARTOMÁNYUK viszont eltér — ld. a következő
        próbát —, ezért a felső végén más eredményt adnak; a csempe
        alapból az alapértékkel nyílik."""
        import numpy as np

        rng = np.random.default_rng(11)
        kep = rng.integers(40, 215, size=(40, 50, 3), dtype=np.uint8)
        assert self._elteres("unsharp", ("1", "0.6"), kep) == self._elteres(
            "unsharp2", ("1", "0.6"), kep
        )

    def test_a_ket_unsharp_TARTOMANYA_elter(self):
        """⚠️ Nem kozmetika: a csúszka felső vége 1,0 → 3,0.

        Ezt az átkötés magával hozza, és a felhasználó meg is fogja látni,
        ha végigtolja a csúszkát. A #2141 az eredeti csempe-tábláját
        követi, tehát ez a helyes irány — de kimondva, nem véletlenül."""
        from picasapy.render.registry import get_filter_spec

        regi = get_filter_spec("unsharp").sliders[0]
        uj = get_filter_spec("unsharp2").sliders[0]
        assert regi.maximum == 1.0
        assert uj.maximum == 3.0
        assert regi.default == uj.default == 0.6


class TestAzAtkotesNEM_veszi_el_a_csuszkat:
    """⚠️ Az átkötés legveszélyesebb mellékhatása.

    A csempe akkor nyit csúszkás alpanelt, ha a szűrőnek van
    **katalógus-bejegyzése** (`effect_params`). Az `unsharp2` és a
    `picniktint` viszont hiányzott onnan — pedig a szűrő-regiszterben van
    csúszkájuk. Bejegyzés nélkül a csempe némán elveszi a csúszkát, és
    alapértékkel azonnal alkalmaz: a felhasználó szempontjából a vezérlő
    eltűnik. Ezért a katalógust is bővíteni kellett (#2141).
    """

    def test_mindharom_uj_kulcsnak_van_katalogus_bejegyzese(self):
        from picasapy.app.effect_params import has_params

        for kulcs in ["unsharp2", "picnikgrain", "picniktint"]:
            assert has_params(kulcs), (
                f"{kulcs}: nincs katalógus-bejegyzés, a csempe elvenné a csúszkát"
            )

    def test_a_csuszka_szama_nem_csokkent_egyik_csempen_sem(self):
        from picasapy.app.effect_params import resolve_effect_params

        def db(kulcs):
            return len(resolve_effect_params(kulcs, width=1000, height=1000))

        # az Élesítés és az Árnyalás eddig is csúszkás volt
        assert db("unsharp2") >= 1
        assert db("picniktint") >= 1
        # a Filmszemcse eddig egykattintásos volt — most csúszkás lett,
        # az eredetihez hűen (`PicnikGrain` mode="effect")
        assert db("picnikgrain") == 2

    def test_a_katalogus_ertekei_a_REGISZTERBOL_jonnek(self):
        """Nem becslés: a `filterdesc.xml`-ből származó regiszter adja."""
        from picasapy.app.effect_params import resolve_effect_params
        from picasapy.render.registry import get_filter_spec

        for kulcs in ["unsharp2", "picniktint"]:
            katalogus = resolve_effect_params(kulcs, width=1000, height=1000)[0]
            regiszter = get_filter_spec(kulcs).sliders[0]
            assert katalogus.minimum == regiszter.minimum, kulcs
            assert katalogus.maximum == regiszter.maximum, kulcs
            assert katalogus.default == regiszter.default, kulcs
