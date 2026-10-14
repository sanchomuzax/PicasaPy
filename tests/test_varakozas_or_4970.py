"""Őr a tests/app várakozó-segédeinek korlátjára (#4970).

A feltételre váró helyi segédek (`_var*`, `_wait*` előtaggal) korlátja legalább
10 másodperc legyen, és a hívások se adjanak 10 másodperc alatti literált. Így a
windowsos CI lassú futásai nem adnak hamis bukást, és a szorzó
(`PICASAPY_TESZT_IDOSZORZO`) a helyi korlátokon is hat.

A még át nem írt fájlok a `KIVETEL` listán vannak. A lista csak csökkenhet:
ha egy fájl átíródott, a kivételt törölni kell (a stale bejegyzés bukik), és
új fájl nem kerülhet fel rá (`KIVETEL_PLAFON`).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

TESZT_GYOKER = Path(__file__).resolve().parent
TESZT_APP = TESZT_GYOKER / "app"

KORLAT_MP = 10.0
KORLAT_MS = 10_000.0

HELYI_PREFIX = re.compile(r"^_(var|wait)")
IDOS_NEV = re.compile(r"(masodperc|timeout|seconds|hatarido|lejarat|ezred|^ido$|^ms$|_ms$|_mp$|_s$|^s$)")
MS_NEV = re.compile(r"(^ms$|_ms$|ezred)")
# A pillanatnyi lista hossza (110 fájl); csak csökkenhet.
KIVETEL_PLAFON = 110
KIVETEL: frozenset[str] = frozenset(
    {
        "tests/app/qml_album_zene_probe_4601.py",
        "tests/app/qml_diavetites_beallitasok_probe_4320.py",
        "tests/app/qml_functional/_fomenu_4420_akciok.py",
        "tests/app/qml_functional/test_ajandek_cd_bekotes_3503.py",
        "tests/app/qml_functional/test_button_bar_context_menu_4637.py",
        "tests/app/qml_functional/test_button_label_fit_992.py",
        "tests/app/qml_functional/test_cimke_panel_4271.py",
        "tests/app/qml_functional/test_collage_background_1009.py",
        "tests/app/qml_functional/test_collage_clips_tab_949.py",
        "tests/app/qml_functional/test_collage_panel_layout_945.py",
        "tests/app/qml_functional/test_collage_panel_wiring_985.py",
        "tests/app/qml_functional/test_collage_ring_fade_1000.py",
        "tests/app/qml_functional/test_color_spectrum_4548.py",
        "tests/app/qml_functional/test_create_result_dialog_binding_loop_918.py",
        "tests/app/qml_functional/test_crop_meret_4549.py",
        "tests/app/qml_functional/test_document_tab_strip_944.py",
        "tests/app/qml_functional/test_editor_maradek_4183.py",
        "tests/app/qml_functional/test_f5_konyvtar_frissites_4697.py",
        "tests/app/qml_functional/test_fanezet_belyegkep_2989.py",
        "tests/app/qml_functional/test_fejlec_film_gomb_4539.py",
        "tests/app/qml_functional/test_fejlec_geometria_1993.py",
        "tests/app/qml_functional/test_fejlec_kollazs_gomb_1006.py",
        "tests/app/qml_functional/test_felirat_kapcsolo_2587.py",
        "tests/app/qml_functional/test_felirat_sav_renderelt_2608.py",
        "tests/app/qml_functional/test_film_panel_4182.py",
        "tests/app/qml_functional/test_film_text_slide_infotext_4402.py",
        "tests/app/qml_functional/test_film_ujraexport_4612.py",
        "tests/app/qml_functional/test_filmszalag_kozepre_4562.py",
        "tests/app/qml_functional/test_filmszalag_mappa_1905.py",
        "tests/app/qml_functional/test_folder_pane_custom_collections_476.py",
        "tests/app/qml_functional/test_folder_pane_scroll_730_731_732.py",
        "tests/app/qml_functional/test_folder_rename_qml_4482.py",
        "tests/app/qml_functional/test_general_ui_settings_4449.py",
        "tests/app/qml_functional/test_gyorsbillentyuk_2163.py",
        "tests/app/qml_functional/test_hasab_gyoker_menu_1407.py",
        "tests/app/qml_functional/test_hely_jelolo_buborek_4582.py",
        "tests/app/qml_functional/test_helyek_terkep_drop_4583.py",
        "tests/app/qml_functional/test_hold_jelveny_1918.py",
        "tests/app/qml_functional/test_jegy_4150_ui.py",
        "tests/app/qml_functional/test_kepalairas_sav_2565.py",
        "tests/app/qml_functional/test_keptalca_455.py",
        "tests/app/qml_functional/test_kimeneti_tulcsordulas_2191.py",
        "tests/app/qml_functional/test_klipek_ful_bekotes_1153.py",
        "tests/app/qml_functional/test_klipgyujto_csoport_kozepen_3605.py",
        "tests/app/qml_functional/test_klipgyujto_savja_1939.py",
        "tests/app/qml_functional/test_left_pane_757.py",
        "tests/app/qml_functional/test_library_frame_hidden_1026.py",
        "tests/app/qml_functional/test_mappa_borito_2049.py",
        "tests/app/qml_functional/test_mappa_borito_ikon_2215.py",
        "tests/app/qml_functional/test_mappa_borito_lathato_ikon_4876.py",
        "tests/app/qml_functional/test_mappa_datum_naptar_4494.py",
        "tests/app/qml_functional/test_maradek_arc_video_4229.py",
        "tests/app/qml_functional/test_nagyitas_alsosav_2564.py",
        "tests/app/qml_functional/test_nagyitas_sav_2311.py",
        "tests/app/qml_functional/test_nyomtatas_ablakmeret_4795.py",
        "tests/app/qml_functional/test_nyomtato_nincs_nyomtato_4608.py",
        "tests/app/qml_functional/test_nyomtato_telepites_2103.py",
        "tests/app/qml_functional/test_panelkapcsolo_sorrend_2305.py",
        "tests/app/qml_functional/test_panelkapcsolok_1927.py",
        "tests/app/qml_functional/test_papiradat_mezo_2368.py",
        "tests/app/qml_functional/test_param_panel_modal_4068.py",
        "tests/app/qml_functional/test_people_album_context_menu_4587.py",
        "tests/app/qml_functional/test_people_album_menu_4645.py",
        "tests/app/qml_functional/test_people_manager_kattintas_4334.py",
        "tests/app/qml_functional/test_photo_menu_commands.py",
        "tests/app/qml_functional/test_places_loading_offline_4584.py",
        "tests/app/qml_functional/test_places_marker_showphotos_4575.py",
        "tests/app/qml_functional/test_poszter_4268.py",
        "tests/app/qml_functional/test_properties_panel_context_menu_4581.py",
        "tests/app/qml_functional/test_racs_belyegkep_elotoltes_4289.py",
        "tests/app/qml_functional/test_racs_nagyito_kapcsolo_1911.py",
        "tests/app/qml_functional/test_rejtett_jelszo_menu_3461.py",
        "tests/app/qml_functional/test_search_suggestion_keyboard_4530.py",
        "tests/app/qml_functional/test_shift_csempe_belyegkep_4558.py",
        "tests/app/qml_functional/test_shortcut_focus_4398.py",
        "tests/app/qml_functional/test_single_click_exit_4449.py",
        "tests/app/qml_functional/test_sugo_bekotes_2054.py",
        "tests/app/qml_functional/test_sugo_hivatkozasok_2212.py",
        "tests/app/qml_functional/test_sugo_kereso_lista_2214.py",
        "tests/app/qml_functional/test_sugo_navigacio_2213.py",
        "tests/app/qml_functional/test_szoveg_igazito_ikonok_4547.py",
        "tests/app/qml_functional/test_talca_ikonok_1224.py",
        "tests/app/qml_functional/test_talca_kijeloles_ui_2039.py",
        "tests/app/qml_functional/test_talca_mappa_token_bekotes_1919.py",
        "tests/app/qml_functional/test_talca_vizjel_2179.py",
        "tests/app/qml_functional/test_titledialog_4198.py",
        "tests/app/qml_functional/test_tobb_szovegdoboz_qml_4545.py",
        "tests/app/qml_functional/test_tulcsordulas_fuggoleges_4537.py",
        "tests/app/qml_functional/test_ui_maradek_4214.py",
        "tests/app/qml_functional/test_ures_racs_uzenet_1945.py",
        "tests/app/qml_functional/test_visszavonas_alkalmazas_4063.py",
        "tests/app/qml_functional/test_voros_auto_undo_4541.py",
        "tests/app/qml_video_controls_probe_4229.py",
        "tests/app/test_busy_integration.py",
        "tests/app/test_busy_registry.py",
        "tests/app/test_controller.py",
        "tests/app/test_ertesito_csuszas_2157.py",
        "tests/app/test_exportcel_indexelese_1565.py",
        "tests/app/test_folder_rename_4482.py",
        "tests/app/test_kimenet_resync_1539.py",
        "tests/app/test_kollazs_szal_hid_988.py",
        "tests/app/test_mappa_athelyezes_resync_1538.py",
        "tests/app/test_projekt_mappa_figyeles_1123.py",
        "tests/app/test_qml_busy.py",
        "tests/app/test_qml_editor_panel.py",
        "tests/app/test_qml_hatterjelzo_2966.py",
        "tests/app/test_qml_helyek_kereses_4147.py",
        "tests/app/test_qml_options_dialog.py",
        "tests/app/test_qml_splash.py",
        "tests/app/test_qml_timeline.py",
    }
)


@dataclass(frozen=True)
class Helper:
    nev: str
    fajl: str
    sor: int
    idoparamok: tuple[tuple[int, str, bool, float | None], ...]  # (index, név, ms?, alap)


@dataclass(frozen=True)
class Eltres:
    fajl: str
    sor: int
    tipus: str  # "helyi" (a segéd alapértéke) vagy "hivas" (a hívás literálja)
    leiras: str


def _feltetel_tipusu(fn: ast.FunctionDef) -> bool:
    """Feltételre vár: a törzsében a paraméterét, egy belső függvényét, vagy a
    közös `var_feltetelre`-t hívja (a vékony burkoló is ilyen)."""
    hivhatok = {a.arg for a in fn.args.args}
    hivhatok |= {n.name for n in ast.walk(fn) if isinstance(n, ast.FunctionDef) and n is not fn}
    hivhatok.add("var_feltetelre")
    return any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in hivhatok
        for n in ast.walk(fn)
    )


def _szam(node: ast.AST | None) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    return None


def _helperek(fa: ast.Module, rel: str) -> list[Helper]:
    eredmeny = []
    for node in ast.walk(fa):
        if not (isinstance(node, ast.FunctionDef) and HELYI_PREFIX.match(node.name)):
            continue
        if not _feltetel_tipusu(node):
            continue
        args = node.args.args
        off = len(args) - len(node.args.defaults)
        idoparamok = []
        for i, a in enumerate(args):
            if not IDOS_NEV.search(a.arg):
                continue
            alap = _szam(node.args.defaults[i - off]) if i >= off else None
            idoparamok.append((i, a.arg, bool(MS_NEV.search(a.arg)), alap))
        if idoparamok:
            eredmeny.append(Helper(node.name, rel, node.lineno, tuple(idoparamok)))
    return eredmeny


def _korlat_alatt(ertek: float, ms: bool) -> bool:
    return ertek < (KORLAT_MS if ms else KORLAT_MP)


def _eltresek(forrasok: dict[str, str]) -> list[Eltres]:
    """Minden forrásfájl (relatív út -> szöveg) sértését megadja, egyszer."""
    fak = {rel: ast.parse(szoveg) for rel, szoveg in forrasok.items()}
    helperek = [h for rel, fa in fak.items() for h in _helperek(fa, rel)]
    eredmeny: list[Eltres] = []
    for h in helperek:
        for _index, nev, ms, alap in h.idoparamok:
            if alap is not None and _korlat_alatt(alap, ms):
                eredmeny.append(Eltres(h.fajl, h.sor, "helyi", f"{h.nev}: {nev}={alap:g} (korlát {'ms' if ms else 's'})"))
    nevek = {}
    for h in helperek:
        nevek.setdefault(h.nev, []).append(h)
    for rel, fa in fak.items():
        helyi_nevek = {n.name for n in ast.walk(fa) if isinstance(n, ast.FunctionDef)}
        for node in ast.walk(fa):
            if not isinstance(node, ast.Call):
                continue
            cel = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", None)
            if cel in helyi_nevek:
                # a fájl saját definíciója árnyékolja a másik modulbelit
                jeloltek = [h for h in nevek.get(cel, []) if h.fajl == rel]
            else:
                jeloltek = nevek.get(cel, [])
            for h in jeloltek:
                eredmeny.extend(_hivas_eltresei(rel, node, h))
    egyedi: dict[tuple[str, int, str], Eltres] = {}
    for e in eredmeny:
        egyedi.setdefault((e.fajl, e.sor, e.tipus), e)
    return sorted(egyedi.values(), key=lambda e: (e.fajl, e.sor))


def _hivas_eltresei(rel: str, hivas: ast.Call, h: Helper) -> list[Eltres]:
    talalt = []
    for index, nev, ms, _alap in h.idoparamok:
        ertek = _szam(hivas.args[index]) if index < len(hivas.args) else None
        kulcsszo = next((kw for kw in hivas.keywords if kw.arg == nev), None)
        if kulcsszo is not None:
            ertek = _szam(kulcsszo.value)
        if ertek is not None and _korlat_alatt(ertek, ms):
            talalt.append(Eltres(rel, hivas.lineno, "hivas", f"{h.nev}({nev}={ertek:g}) (korlát {'ms' if ms else 's'})"))
    return talalt


def _beolvas() -> dict[str, str]:
    return {
        p.relative_to(TESZT_GYOKER.parent).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(TESZT_APP.rglob("*.py"))
    }


def test_a_helyi_segedek_korlata_legalabb_tiz_masodperc():
    eltresek = [e for e in _eltresek(_beolvas()) if e.tipus == "helyi" and e.fajl not in KIVETEL]
    assert not eltresek, "10 s alatti helyi várakozás:\n" + "\n".join(
        f"  {e.fajl}:{e.sor} {e.leiras}" for e in eltresek
    )


def test_a_hivasok_nem_adnak_tiz_masodperc_alatti_literalt():
    hivas_sertesek = [
        e for e in _eltresek(_beolvas()) if e.tipus == "hivas" and e.fajl not in KIVETEL
    ]
    assert not hivas_sertesek, "10 s alatti literál a várakozó hívásban:\n" + "\n".join(
        f"  {e.fajl}:{e.sor} {e.leiras}" for e in hivas_sertesek
    )


def test_kivetellista_csak_csokkenhet():
    alap = {e.fajl for e in _eltresek(_beolvas())}
    elavult = sorted(KIVETEL - alap)
    assert not elavult, "ezek már át vannak írva, töröld a KIVETEL-ből: " + ", ".join(elavult)
    print(f"\nKIVETEL hossza: {len(KIVETEL)} (plafon: {KIVETEL_PLAFON})")
    assert len(KIVETEL) <= KIVETEL_PLAFON, (
        f"a KIVETEL nőtt: {len(KIVETEL)} > {KIVETEL_PLAFON}; új fájl nem kerülhet fel"
    )


_ROSSZ = '''
def _var(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    return feltetel()


def teszt(qt_app):
    _var(qt_app, lambda: True, 2.0)
'''

_JO = '''
def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return feltetel()


def _wait_ms(qt_app, ms):
    return ms


def teszt(qt_app):
    _var(qt_app, lambda: True, 10.0)
    _wait_ms(qt_app, 300)
'''


def test_az_or_maga_eszleli_a_rovid_korlatot():
    eltresek = _eltresek({"tests/app/minta.py": _ROSSZ})
    assert {(e.tipus, e.sor) for e in eltresek} == {("helyi", 2), ("hivas", 7)}


def test_az_or_nem_jelez_a_tiz_masodperces_korlatra_es_a_fix_varakozasra():
    assert _eltresek({"tests/app/minta.py": _JO}) == []


_BURKOLO = '''
from tests.support.varakozas import var_feltetelre


def _var(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def teszt(qt_app):
    _var(qt_app, lambda: True, 2.0)
'''


def test_az_or_eszleli_a_kozos_segedet_hivo_burkolot():
    eltresek = _eltresek({"tests/app/minta.py": _BURKOLO})
    assert {(e.tipus, e.sor) for e in eltresek} == {("helyi", 5), ("hivas", 10)}
