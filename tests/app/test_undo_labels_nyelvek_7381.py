"""#7381: a Visszavonás/Újra gomb "lépés-alakja" nyelvenként az ERESETI szerint.

Az eredeti Picasa `CFilterStackUI::undoname` / `redoname` szövege a
visszavonandó lépés neve ELÉ kerül, egyszerű összefűzéssel. Az angol alak
„Undo " (záró szóközzel, kettőspont nélkül): az eredeti Picasa 3.9 felvételei
(`job-836 __20` / `__22`, `job-838 __34`) „Undo Straighten", „Redo
Straighten", „Undo Retouches". A magyar „Visszavonás: " és a török „Geri al: "
kettőspontos, a többi nyelv szóközös, a japán és a két kínai alak szóköz
nélküli (CJK).

Az alábbi tábla az eredeti nyelvi erőforrás (`stringres.xml`,
`CFilterStackUI::undoname` / `redoname`) kiolvasott értéke, MIND a 41
nyelvre, a `%1` a lépés neve helyén. A forrás privát (a termék-repóba nem
kerülhet), ezért a tábla másolat: a teszt azt őrzi, hogy a `.ts` fordítása
egyezik vele.

NYITOTT KÉRDÉS (három alak): a perzsa `undoname` („لغو") és `redoname`
(„انجام مجدد"), valamint a litván `redoname` („Grąžinti") az erőforrásban
szóköz és kettőspont nélküli, szóközös írású nyelvekben. Az nem dönthető el
az erőforrásból, hogy az eredeti ilyenkor a nevet közvetlenül hozzáragasztja
(hibás felirat), vagy a kód tesz közé elválasztót. Ehhez perzsa és litván
nyelvű eredeti Picasa felvétel kell ("Undo <lépés>" gomb). Addig ezen a
három helyen a MAI alak marad: a lefordított felirat + ": " + a név.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.app.language_controller import SUPPORTED_LANGUAGES

_I18N_DIR = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"

_PANEL_CONTEXT = "EditorPanel"

#: nyelv -> (undoname + "%1", redoname + "%1"), az eredeti erőforrásból
_ERESETI_ALAKOK: dict[str, tuple[str, str]] = {
    "ar": ("تراجع %1", "إعادة %1"),
    "iw": ("בטל %1", "בצע שוב %1"),
    "id": ("Batal %1", "Ulang %1"),
    "ca": ("Desfés %1", "Refés %1"),
    "da": ("Fortryd %1", "Annuller fortryd %1"),
    "de": ("Rückgängig machen %1", "Wiederholen %1"),
    "enUK": ("Undo %1", "Redo %1"),
    "en": ("Undo %1", "Redo %1"),
    "es": ("Deshacer %1", "Rehacer %1"),
    "fr": ("Annuler %1", "Rétablir %1"),
    "hr": ("Poništi %1", "Ponovi %1"),
    "it": ("Annulla %1", "Ripeti %1"),
    "lv": ("Atsaukt %1", "Atcelt atsaukšanu %1"),
    "lt": ("Anuliuoti %1", ""),  # a redo: nyitott kérdés, ld. lent
    "hu": ("Visszavonás: %1", "Újra: %1"),
    "nl": ("Ongedaan maken %1", "Opnieuw %1"),
    "no": ("Angre %1", "Gjør om %1"),
    "pl": ("Cofnij %1", "Powtórz %1"),
    "pt": ("Anular %1", "Refazer %1"),
    "pt-BR": ("Desfazer %1", "Refazer %1"),
    "ro": ("Anulați acţiunea %1", "Repetaţi %1"),
    "sk": ("Späť %1", "Znova %1"),
    "sl": ("Razveljavi %1", "Uveljavi %1"),
    "fi": ("Kumoa %1", "Toista %1"),
    "sv": ("Ångra %1", "Gör om %1"),
    "fil": ("Undo %1", "Gawing Muli %1"),
    "vi": ("Hoàn tác %1", "Làm lại %1"),
    "tr": ("Geri al: %1", "Yeniden yap: %1"),
    "cs": ("Vrátit zpět %1", "Znovu %1"),
    "el": ("Αναίρεση %1", "Επανάληψη %1"),
    "ru": ("Отменить %1", "Повторить %1"),
    "sr": ("Опозови %1", "Понови %1"),
    "uk": ("Скасувати %1", "Повернути дію %1"),
    "bg": ("Отмяна %1", "Възстановяване %1"),
    "hi": ("वापस लाएं %1", "फिर से करें %1"),
    "th": ("เลิกทำ %1", "ทำใหม่ %1"),
    "zh-CN": ("撤消%1", "重做%1"),
    "zh-TW": ("復原%1", "取消復原%1"),
    "ja": ("取消し%1", "やり直し%1"),
    "ko": ("실행취소 %1", "다시실행 %1"),
}

#: A NYITOTT KÉRDÉS három alakja: a MAI alak marad (a lefordított puszta
#: felirat + ": " + név), amíg a perzsa/litván eredeti felvétel meg nem
#: mondja, mit tesz a program.
_NYITOTT_ALAKOK: dict[str, tuple[str | None, str | None]] = {
    "fa": ("واگرد: %1", "ازنو: %1"),
    "lt": (None, "Grąžinti: %1"),
}


def _elvart(code: str) -> tuple[str, str]:
    undo, redo = _ERESETI_ALAKOK.get(code, (None, None))
    nyitott_undo, nyitott_redo = _NYITOTT_ALAKOK.get(code, (None, None))
    return (nyitott_undo or undo, nyitott_redo or redo)


def test_a_tabla_mind_a_41_nyelvet_lefedi():
    lefedett = set(_ERESETI_ALAKOK) | set(_NYITOTT_ALAKOK)
    assert lefedett == set(SUPPORTED_LANGUAGES)
    assert len(lefedett) == 41


def test_az_eredeti_alakok_a_lepes_nevenek_helyen_tartalmazzak_a_helykitoltot():
    for code in SUPPORTED_LANGUAGES:
        for alak in _elvart(code):
            assert alak.count("%1") == 1, (code, alak)
            assert alak.endswith("%1"), (code, alak)


@pytest.fixture(scope="module")
def _qt_app():
    pytest.importorskip("PySide6.QtCore")
    from PySide6.QtCore import QCoreApplication

    return QCoreApplication.instance() or QCoreApplication([])


def _betolt(code: str, app):
    from PySide6.QtCore import QTranslator

    translator = QTranslator()
    assert translator.load(str(_I18N_DIR / f"picasapy_{code}.qm")), (
        f"{code}: a .qm nem tölthető be"
    )
    app.installTranslator(translator)
    return translator


@pytest.mark.parametrize("code", SUPPORTED_LANGUAGES)
def test_a_lepes_alak_nyelvenkent_az_eredeti_undoname_redoname(code, _qt_app):
    """A `.qm`-ből betöltött fordítás pontosan az eredeti erőforrás alakja."""
    from PySide6.QtCore import QCoreApplication

    translator = _betolt(code, _qt_app)
    try:
        undo = QCoreApplication.translate(_PANEL_CONTEXT, "Undo %1")
        redo = QCoreApplication.translate(_PANEL_CONTEXT, "Redo %1")
    finally:
        _qt_app.removeTranslator(translator)
    assert (undo, redo) == _elvart(code)


@pytest.mark.parametrize("code", ["hu", "de", "tr", "ja", "en", "fa", "lt"])
def test_a_kesz_felirat_a_nyelv_alakjat_hasznalja(code, _qt_app):
    """A kész gombfelirat = a nyelv alakja a lépés LEFORDÍTOTT nevével."""
    from PySide6.QtCore import QCoreApplication

    from picasapy.app.edit_action_names import redo_label, undo_label

    translator = _betolt(code, _qt_app)
    try:
        nev = QCoreApplication.translate(_PANEL_CONTEXT, "Straighten")
        undo = undo_label("tilt")
        redo = redo_label("tilt")
    finally:
        _qt_app.removeTranslator(translator)
    elvart_undo, elvart_redo = _elvart(code)
    assert undo == elvart_undo.replace("%1", nev)
    assert redo == elvart_redo.replace("%1", nev)


@pytest.mark.parametrize("code", SUPPORTED_LANGUAGES)
def test_a_ket_alaknak_befejezett_forditasa_van(code):
    """A `.ts`-ben mindkét sablon BEFEJEZETT (nem unfinished/vanished), a
    `%1` helykitöltővel."""
    import xml.etree.ElementTree as ET

    root = ET.parse(_I18N_DIR / f"picasapy_{code}.ts").getroot()
    talalt: dict[str, ET.Element] = {}
    for ctx in root.findall("context"):
        if (ctx.findtext("name") or "") != _PANEL_CONTEXT:
            continue
        for msg in ctx.findall("message"):
            forras = msg.findtext("source") or ""
            if forras in ("Undo %1", "Redo %1"):
                talalt[forras] = msg
    assert set(talalt) == {"Undo %1", "Redo %1"}, f"{code}: hiányzó sablon"
    for forras, msg in talalt.items():
        translation = msg.find("translation")
        assert translation is not None
        assert translation.get("type") not in ("unfinished", "vanished"), (
            f"{code}: {forras!r} nincs befejezve"
        )
        assert "%1" in (translation.text or ""), (code, forras)
