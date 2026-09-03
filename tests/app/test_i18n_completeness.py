"""#319: a magyar fordítás legyen TELJES — minden `qsTr()`/`tr()` szöveghez
tartozzon BEFEJEZETT bejegyzés a `picasapy_hu.ts`-ben.

A teszt a valódi `pyside6-lupdate` kinyerő-logikát futtatja (QML és Python
forrásokon egyaránt — ld. `-extensions` alapértelmezés + explicit
fájllista), egy ideiglenes másolatba egyesítve a betelepített `.ts`-t. Ez
megbízhatóbb, mint egy kézzel írt `qsTr(...)` reguláris kifejezés: a valódi
Qt-eszköz kezeli a többsoros/összefűzött string-literálokat (pl.
`qsTr("a " + "b")`), a plural (`%n`) alakokat és a fájlonkénti kontextus-
hozzárendelést is — pontosan úgy, ahogy a futásidejű `.qm` betöltés is
értelmezi őket.

Ismert, indokolt kivétel (ld. CONTRIBUTING.md "i18n-regen buktató"): a
`CreateMixin` (create_controller.py) NEM önálló QObject, hanem az
`AppController`-be kevert mixin — a `self.tr()` FUTÁSIDŐBEN az
`AppController` kontextust használja (a konkrét példány osztálya, nem a
lexikai osztály), de a statikus `lupdate`-elemzés ezt nem látja, és a
lexikai `CreateMixin` nevet rendeli hozzá. Emiatt ezek a szövegek a
`lupdate` szemével örökre "unfinished"-nek látszanak — valójában az
`AppController` kontextusban MÁR le vannak fordítva (ezt a
`test_bound_tr_exceptions_resolve_at_runtime` teszt közvetlenül,
`QTranslator`-ral is ellenőrzi, nem csak a `.ts`-t nézi).
"""

from __future__ import annotations

import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_APP_DIR = _REPO_ROOT / "src" / "picasapy" / "app"
_I18N_DIR = _APP_DIR / "i18n"
_TS_PATH = _I18N_DIR / "picasapy_hu.ts"

# (lupdate által talált, TÉVES kontextus, forrásszöveg) -> a FUTÁSIDŐBEN
# ténylegesen használt, helyes kontextus. Csak ide vehető fel új tétel, ha
# indokoltan, kötött/mixin `tr()`-hívás miatt a lupdate statikus elemzése
# nem tudja levezetni a valódi kontextust — ld. a modul docstringjét.
_KNOWN_CONTEXT_FORWARDING_EXCEPTIONS: dict[tuple[str, str], str] = {
    ("CreateMixin", "No pictures are selected."): "AppController",
    ("CreateMixin", "No target file was chosen."): "AppController",
    ("CreateMixin", "Unknown collage type."): "AppController",
    # #431: a képkeret-választó hibaszövege ugyanebbe a családba tartozik
    ("CreateMixin", "Unknown picture frame."): "AppController",
    ("CreateMixin", "None of the selected pictures could be read."): "AppController",
    # #459: az `ExportMixin` (export_controller.py) ugyanígy a mixin-
    # kontextus fölé kevert `AppController` — a lemezhely-ellenőrzés
    # hibaszövege futásidőben ott van lefordítva.
    (
        "ExportMixin",
        "Sorry, there is not enough free disk space to safely download pictures.",
    ): "AppController",
    # #943: a `CollageMixin` (collage_controller.py) ugyanez az eset — a
    # kollázs-panel szelete is az `AppController`-be kevert mixin, tehát a
    # mentés folyamat- és hibaszövegei futásidőben ott vannak lefordítva.
    # #949: a mentés szövegei a `CollageSaveMixin`-be költöztek (a
    # `collage_controller.py` 1100 sor fölé nőtt), de a futásidejű kontextus
    # változatlanul az `AppController` — ugyanaz a mixin-eset.
    ("CollageSaveMixin", "Creating collage… initializing"): "AppController",
    # a Többszörös exponálás saját folyamatszövege (spec 9.1)
    ("CollageSaveMixin", "Stacking pictures"): "AppController",
    # a megszakítás visszajelzése (`collage::cancelling`)
    ("CollageSaveMixin", "Creating collage… shutting down"): "AppController",
    ("CollageSaveMixin", "The collage is ready"): "AppController",
    # #1072: a piszkozat helykitöltő képébe rajzolt felirat
    ("CollageSaveMixin", "DRAFT"): "AppController",
    # #1002: a kész kollázs újranyitásának hibája
    (
        "CollageSaveMixin",
        "The collage project file could not be opened.",
    ): "AppController",
    (
        "CollageSaveMixin",
        "None of the selected pictures could be read.",
    ): "AppController",
    # #1500: a `ColorIndexMixin` (color_index_controller.py) ugyanez az
    # eset — az `AppController`-be kevert szelet, tehát a színkeresés
    # „még készül" tájékoztatója futásidőben az `AppController`
    # kontextusban van lefordítva.
    (
        "ColorIndexMixin",
        "Color search is still being prepared: {0} of {1} photos have been "
        "analyzed so far. Photos that have not been analyzed yet cannot show "
        "up in the results, but the list fills in on its own as soon as the "
        "preparation finishes.",
    ): "AppController",
}


def _source_files() -> list[Path]:
    """Minden QML és Python forrás az app alatt, az i18n mappa kivételével
    (a `.ts`/`.qm` maga nem forrás, ne nézze át saját magát)."""
    files = [
        p
        for p in (*_APP_DIR.rglob("*.qml"), *_APP_DIR.rglob("*.py"))
        if _I18N_DIR not in p.parents
    ]
    assert files, "nem található QML/Python forrás — hibás útvonal?"
    return files


def _extract_with_lupdate(tmp_path: Path) -> ET.Element:
    """A jelenlegi `.ts` + a mai forrásállapot egyesítése egy ideiglenes
    másolatban — a valódi `.ts` érintetlen marad."""
    lupdate = shutil.which("pyside6-lupdate")
    if lupdate is None:
        pytest.skip("pyside6-lupdate nincs telepítve — a PySide6-tal jön")

    scratch_ts = tmp_path / "picasapy_hu.scratch.ts"
    scratch_ts.write_text(_TS_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    files = [str(p) for p in _source_files()]
    result = subprocess.run(
        [lupdate, *files, "-ts", str(scratch_ts), "-silent"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        timeout=60,
    )
    assert result.returncode == 0, (
        f"pyside6-lupdate hibával tért vissza:\n{result.stdout}\n{result.stderr}"
    )
    return ET.parse(scratch_ts).getroot()


def _shipped_translation(root: ET.Element, context: str, source: str) -> str | None:
    """A betelepített `.ts`-ből a (context, source) BEFEJEZETT fordítása,
    vagy None, ha nincs ilyen / nincs befejezve."""
    for ctx in root.findall("context"):
        if (ctx.find("name").text or "") != context:
            continue
        for msg in ctx.findall("message"):
            if msg.find("source").text != source:
                continue
            translation = msg.find("translation")
            if translation is None or translation.get("type") in (
                "unfinished",
                "vanished",
            ):
                return None
            # numerus (plural) alak: legalább egy numerusform legyen kitöltve
            if msg.get("numerus") == "yes":
                forms = translation.findall("numerusform")
                return forms[0].text if forms and forms[0].text else None
            return translation.text
    return None


def _location_text(message: ET.Element) -> str:
    locations = message.findall("location")
    if not locations:
        return "(nincs location)"
    return ", ".join(
        f"{loc.get('filename')}:{loc.get('line')}" for loc in locations
    )


class TestI18nCompleteness:
    def test_every_qstr_has_a_finished_hungarian_translation(self, tmp_path):
        shipped_root = ET.parse(_TS_PATH).getroot()
        extracted_root = _extract_with_lupdate(tmp_path)

        missing: list[str] = []
        exceptions_seen: set[tuple[str, str]] = set()

        for ctx in extracted_root.findall("context"):
            context = ctx.find("name").text or ""
            for msg in ctx.findall("message"):
                translation = msg.find("translation")
                ttype = translation.get("type") if translation is not None else None
                if ttype != "unfinished":
                    # None (befejezett) vagy "vanished" (nem élő szöveg,
                    # nem ez a teszt tárgya — ld. CONTRIBUTING.md)
                    continue

                source = msg.find("source").text
                key = (context, source)

                real_context = _KNOWN_CONTEXT_FORWARDING_EXCEPTIONS.get(key)
                if real_context is not None:
                    exceptions_seen.add(key)
                    if _shipped_translation(shipped_root, real_context, source):
                        continue
                    missing.append(
                        f"[{context}→{real_context}] {source!r} "
                        f"({_location_text(msg)}) — a dokumentált kivétel "
                        "célkontextusában SEM található befejezett fordítás"
                    )
                    continue

                missing.append(f"[{context}] {source!r} ({_location_text(msg)})")

        assert not missing, (
            f"{len(missing)} qsTr()/tr() szöveghez nincs befejezett magyar "
            "fordítás a picasapy_hu.ts-ben (vagy a hozzá tartozó .qm nincs "
            "frissítve):\n" + "\n".join(sorted(missing))
        )

        # ha egy kivétel többé nem jelentkezik lupdate-nél (pl. a mixin
        # QObject-té vált, vagy a szöveg megszűnt), az a lista karbantartását
        # jelzi — nem hiba, csak figyelmeztetés, hogy a kivétel törölhető
        stale = set(_KNOWN_CONTEXT_FORWARDING_EXCEPTIONS) - exceptions_seen
        if stale:
            import warnings

            warnings.warn(
                "A _KNOWN_CONTEXT_FORWARDING_EXCEPTIONS listában elavult "
                f"bejegyzések (törölhetők): {sorted(stale)}",
                stacklevel=1,
            )

    def test_bound_tr_exceptions_resolve_at_runtime(self):
        """A dokumentált kivételek NEM csak a `.ts`-ben léteznek egy másik
        kontextus alatt — ténylegesen betöltve a `.qm`-et, a mixin
        `self.tr()`-je is a helyes (lefordított) szöveget adja vissza."""
        pytest.importorskip("PySide6.QtCore")
        from PySide6.QtCore import QCoreApplication, QObject, QTranslator

        app = QCoreApplication.instance() or QCoreApplication([])
        translator = QTranslator()
        loaded = translator.load("picasapy_hu", str(_I18N_DIR))
        assert loaded, "a picasapy_hu.qm nem tölthető be"
        app.installTranslator(translator)
        try:
            from picasapy.app.collage_controller import CollageMixin
            from picasapy.app.create_controller import CreateMixin
            from picasapy.app.export_controller import ExportMixin

            # A self.tr() futásidejű kontextusa a KONKRÉT (Python) osztály
            # neve — nem a lexikai (mixin) osztályé, FÜGGETLENÜL attól,
            # melyik mixin metódusa hívja. Ezért a próba-osztályt
            # szándékosan "AppController" néven hozzuk létre (type(), a
            # valódi controller.py importja nélkül — az sok más függőséget
            # vonna be), MINDEN dokumentált kivétel mixinjével összefűzve,
            # hogy pontosan azt a felbontást reprodukáljuk, amit a valódi
            # AppController(QObject, ..., CreateMixin, ExportMixin, ...) csinál.
            # (#943: a CollageMixin is itt van — a `collageFailed` jelzés két
            # mixinben is szerepel, ez PySide6-ban rendben van.)
            probe_cls = type(
                "AppController", (QObject, CreateMixin, ExportMixin, CollageMixin), {}
            )
            probe = probe_cls()
            for (_wrong_context, source), real_context in (
                _KNOWN_CONTEXT_FORWARDING_EXCEPTIONS.items()
            ):
                assert real_context == "AppController"  # a jelenlegi egyetlen cél
                translated = probe.tr(source)
                assert translated != source, (
                    f"{source!r} angolul jelenik meg — a mixin self.tr() "
                    "nem találta a fordítást"
                )
        finally:
            app.removeTranslator(translator)
