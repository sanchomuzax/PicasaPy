"""#465: a Visszavonás/Újra felirat MINDEN lépést néven nevez.

Az eredeti Picasa `CFilterStackUI` osztályának hat szövege (a jegy 5.
kommentje) rögzíti, hogy a gombpárnak KÉT állapota volt:

- `undolabel` / `redolabel` — „Visszavonás" / „Újra" (üres veremnél),
- `undoname` / `redoname` — „Visszavonás: " / „Újra: " (**záró szóközzel**),
  ami után a visszavonandó művelet NEVE következett.

A felhasználó tehát látta, mit fog visszavonni. Ez akkor ér valamit, ha a
lánc MINDEN eleméhez tartozik olvasható név — nem csak egy kézzel gondozott
tucathoz. Ez a teszt azt őrzi, hogy

1. a szerkesztő által feltehető minden művelet-kulcsnak van neve,
2. a `.picasa.ini`-ből visszaolvasott (valódi Picasa írta) szűrőnevek is
   feloldódnak — beleértve a verziós alakokat (`crop64`, `finetune2`,
   `unsharp2`, `glow`, `grain`),
3. a nevek MAGYARUL jelennek meg (a betelepített `.qm`-ből),
4. az ismeretlen kulcs a nyers nevét adja vissza (informatívabb az üresnél).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.app.edit_action_names import (
    ACTION_LABELS,
    UNNAMED_CHAIN_KEYS,
    action_label,
    redo_label,
    undo_label,
)

_I18N_DIR = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"


def _editor_action_keys() -> set[str]:
    """Minden művelet-kulcs, amit a szerkesztő MAGA tehet az undo-veremre:
    az eszközök és az alkalmazható effektek (a „Régi effektek" fülével
    együtt) — az `edit_controller` saját igazságforrásaiból, nem kézzel
    másolt listából."""
    from picasapy.app import edit_controller as ec

    tools = {
        "crop",
        "tilt",
        "retouch",
        "redeye",
        "text",
        "enhance",
        "autolight",
        "autocolor",
        "finetune",
    }
    return tools | set(ec._APPLICABLE_EFFECTS)


class TestNevKatalogus:
    def test_minden_szerkesztoi_muvelethez_van_nev(self):
        missing = sorted(k for k in _editor_action_keys() if k not in ACTION_LABELS)
        assert not missing, (
            "a szerkesztő fel tudja tenni ezeket az undo-veremre, de a "
            f"Visszavonás-felirat nem tudja megnevezni őket: {missing}"
        )

    def test_az_ini_betuzese_is_felold(self):
        """A `.picasa.ini`-be írt betűzés (Vignette, CrossProcess, IR…) a
        kisbetűs kulccsal azonos nevet ad — a lánc visszaolvasásakor a
        felirat nem eshet vissza a nyers névre."""
        from picasapy.app import edit_controller as ec

        for key, ini_name in ec._EFFECT_INI_NAMES.items():
            assert action_label(ini_name) == action_label(key), (
                f"{ini_name!r} (ini-betűzés) más nevet ad, mint {key!r}"
            )

    @pytest.mark.parametrize(
        ("key", "alias_of"),
        [
            ("crop64", "crop"),
            ("finetune2", "finetune"),
        ],
    )
    def test_verzios_alakok_ugyanazt_a_nevet_adjak(self, key, alias_of):
        """Két alak, amely az EREDETI szövegtárban is azonos feliratot kap.

        A `crop64` a `.picasa.ini` vágás-kulcsa, nem külön eszköz; a
        `finetune`/`finetune2` pedig az egyetlen verziós pár, amelynek az
        eredeti `filter_*_label0` bejegyzése is ugyanaz („Tuning").
        """
        assert action_label(key) == action_label(alias_of)

    @pytest.mark.parametrize(
        ("regi_kulcs", "uj_kulcs", "regi_felirat", "uj_felirat"),
        [
            ("unsharp", "unsharp2", "Sharpen (Old)", "Sharpen"),
            ("glow", "glow2", "Glow (Old)", "Glow"),
            ("grain", "grain2", "Film Grain (Old)", "Film Grain"),
            ("tint", "picniktint", "Tint (Old)", "Tint"),
        ],
    )
    def test_a_regi_valtozat_kulon_Old_feliratot_kap(
        self, regi_kulcs, uj_kulcs, regi_felirat, uj_felirat
    ):
        """#2240: a négy verziós párnál az eredeti MEGKÜLÖNBÖZTET.

        Korábban mindkét alak ugyanazt a nevet kapta, és a felhasználó a
        Visszavonás gombon nem látta, hogy régi effektet von vissza. Az
        eredeti szövegtár (`filter_*_label0`) a régi változatra „(Old)"
        toldatot tesz — magyarul „(régi)", a `grain`-nél „Régi
        filmszemcse".

        Ez a próba SZÁNDÉKOSAN az angol feliratot nézi (`ACTION_LABELS`),
        nem a lefordítottat: a fordítás meglétét külön őr méri.
        """
        assert ACTION_LABELS[regi_kulcs][0] == regi_felirat
        assert ACTION_LABELS[uj_kulcs][0] == uj_felirat
        assert action_label(regi_kulcs) != action_label(uj_kulcs)

    def test_a_renderelo_minden_kulcsat_vagy_megnevezzuk_vagy_kimondjuk(self):
        """A renderelő által ismert szűrők (tehát ami egy valódi Picasa-
        láncból elénk kerülhet) vagy kapnak nevet, vagy NÉVSZERINT szerepelnek
        a „nincs hozzá eredeti felirat" listán. Új renderelő bekötése így
        döntést kényszerít, nem csendben esik vissza a nyers kulcsra."""
        from picasapy.render import chain

        handled = set(chain._HANDLERS) | set(chain._FRAME_EFFECTS) | {"crop64"}
        unnamed = sorted(k for k in handled if k not in ACTION_LABELS)
        assert unnamed == sorted(UNNAMED_CHAIN_KEYS), (
            "a névtelen szűrők köre megváltozott — vagy adj nevet neki, vagy "
            f"vedd fel az UNNAMED_CHAIN_KEYS közé: {unnamed}"
        )

    def test_a_nev_a_GOMB_felirata(self):
        """A visszavonás neve pontosan az a szöveg, amit a felhasználó a
        gombon látott, amikor az effektet alkalmazta. Ha egy gomb feliratát
        átírják, ez a teszt bukik — enélkül a két szöveg némán elcsúszna, és
        a felhasználó két különböző nevet látna ugyanarra az effektre."""
        import re
        from pathlib import Path

        qml_dir = (
            Path(__file__).resolve().parents[2]
            / "src"
            / "picasapy"
            / "app"
            / "qml"
            / "PicasaPy"
        )
        pattern = re.compile(
            r'label:\s*qsTr\("([^"]+)"\)[\s\S]{0,200}?effectRequested\("([a-z_0-9]+)"\)'
        )
        buttons: dict[str, str] = {}
        for path in sorted(qml_dir.glob("EditorEffectsTab*.qml")):
            for label, key in pattern.findall(path.read_text(encoding="utf-8")):
                buttons[key] = label
        assert buttons, "nem sikerült effekt-gombot kiolvasni a QML-fülekből"

        mismatched = sorted(
            f"{key}: gomb={label!r} vs. névtár={ACTION_LABELS.get(key, ('—',))[0]!r}"
            for key, label in buttons.items()
            if ACTION_LABELS.get(key, (None,))[0] != label
        )
        assert not mismatched, (
            "az effekt-gomb felirata és a Visszavonás-név elcsúszott: "
            f"{mismatched}"
        )

    def test_ismeretlen_kulcs_a_nyers_nevet_adja(self):
        assert action_label("valami_ismeretlen") == "valami_ismeretlen"

    def test_ures_kulcs_ures_nevet_ad(self):
        assert action_label("") == ""


class TestMagyarFelirat:
    """A nevek nem maradhatnak angolul a magyar felületen: a katalógus
    minden felirata a betelepített `.qm`-ből fordítva jön."""

    @pytest.fixture(scope="class")
    def translated(self):
        pytest.importorskip("PySide6.QtCore")
        from PySide6.QtCore import QCoreApplication, QTranslator

        app = QCoreApplication.instance() or QCoreApplication([])
        translator = QTranslator()
        assert translator.load("picasapy_hu", str(_I18N_DIR)), (
            "a picasapy_hu.qm nem tölthető be"
        )
        app.installTranslator(translator)
        yield
        app.removeTranslator(translator)

    def test_minden_nevnek_van_befejezett_forditasa(self):
        """A `.ts`-ben minden (kontextus, felirat) párhoz BEFEJEZETT magyar
        bejegyzés tartozik. Nem a lefordított szöveg ELTÉRÉSÉT nézzük: van
        néhány felirat, ami magyarul is ugyanaz (Neon, Polaroid) — a
        kérdés az, hogy a fordító végigment-e rajta."""
        import xml.etree.ElementTree as ET

        root = ET.parse(_I18N_DIR / "picasapy_hu.ts").getroot()
        finished: set[tuple[str, str]] = set()
        for ctx in root.findall("context"):
            name = ctx.find("name").text or ""
            for msg in ctx.findall("message"):
                translation = msg.find("translation")
                if translation is None or translation.get("type") in (
                    "unfinished",
                    "vanished",
                ):
                    continue
                finished.add((name, msg.find("source").text))

        missing = sorted(
            f"[{context}] {label!r} ({key})"
            for key, (label, context) in ACTION_LABELS.items()
            if (context, label) not in finished
        )
        assert not missing, (
            "ezekhez a művelet-nevekhez nincs befejezett magyar fordítás a "
            f"megadott kontextusban: {missing}"
        )

    def test_a_felirat_ket_allapota(self, translated):
        """Üres veremnél a puszta „Visszavonás"/„Újra", egyébként a
        „Visszavonás: <lépés>" alak (`undoname` záró szóköze)."""
        assert undo_label("") == "Visszavonás"
        assert redo_label("") == "Újra"
        assert undo_label("crop") == "Visszavonás: Vágás"
        assert redo_label("sepia") == "Újra: Szépia"

    def test_a_teljes_effekt_kinalat_magyarul_nevezodik(self, translated):
        """Konkrét minta a korábban NÉVTELEN effektekből — ezek eddig a
        nyers ini-kulcsot mutatták a gombon („Visszavonás: crossprocess")."""
        assert undo_label("crossprocess") == "Visszavonás: Áttűnés"
        assert undo_label("museummatte") == "Visszavonás: Múzeumi matt"
        assert undo_label("nightvision") == "Visszavonás: Éjjellátó"
        # #2240: a „(finom)" toldat a MI találmányunk volt — az eredeti
        # szövegtárban a `picnikgrain` felirata sima „Film Grain".
        assert undo_label("picnikgrain") == "Visszavonás: Filmszemcse"
