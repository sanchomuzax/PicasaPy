"""#4866: a nyelvi szótár-generátor idempotens, és nem párosít írásjel-eltérően."""

from __future__ import annotations

import importlib.util
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_GYOKER = Path(__file__).resolve().parents[1]
_I18N = _GYOKER / "src" / "picasapy" / "app" / "i18n"
_REFERENCIA = Path.home() / "picasapy-agent" / "referencia" / "i18n"

_spec = importlib.util.spec_from_file_location(
    "build_i18n_dictionaries_4866", _GYOKER / "scripts" / "build_i18n_dictionaries.py"
)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def _ts(language: str, messages: list[tuple[str, str | None, str | None]]) -> str:
    """Minimális Qt TS: (forrás, extracomment, fordítás); None fordítás = unfinished."""
    rows = []
    for source, extra, translation in messages:
        comment = f"<extracomment>{extra}</extracomment>" if extra else ""
        if translation is None:
            tr = '<translation type="unfinished" />'
        else:
            tr = f"<translation>{translation}</translation>"
        rows.append(f"<message><source>{source}</source>{comment}{tr}</message>")
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<TS version="2.1" language="{language}"><context><name>Ctx</name>'
        + "".join(rows)
        + "</context></TS>"
    )


def _referencia(root: Path, hu: dict[str, str], de: dict[str, str]) -> Path:
    for code in gen._REFERENCE_LANGUAGES:
        (root / code).mkdir(parents=True)
    for code, texts in (("hu", hu), ("de", de)):
        items = "".join(
            f'<stringres id="{k}"><xmbtext>{v}</xmbtext></stringres>' for k, v in texts.items()
        )
        (root / code / "p.xml").write_text(f"<resources>{items}</resources>", encoding="utf-8")
    return root


def _futtat(tmp_path: Path, hu_ts: str, de_ts: str | None, hu_ref, de_ref) -> Path:
    refs = _referencia(tmp_path / "ref", hu_ref, de_ref)
    out = tmp_path / "out"
    out.mkdir()
    (out / "picasapy_hu.ts").write_text(hu_ts, encoding="utf-8")
    if de_ts is not None:
        (out / "picasapy_de.ts").write_text(de_ts, encoding="utf-8")
    gen.build_dictionaries(refs, out, compile_qm=False)
    return out


def _messages(path: Path) -> dict[str, ET.Element]:
    root = ET.parse(path).getroot()
    return {m.findtext("source"): m for m in root.iter("message")}


def _tr(message: ET.Element) -> tuple[str | None, str | None]:
    t = message.find("translation")
    return t.get("type"), t.text


def test_kulonbozo_irasjelu_elem_nem_parosodik_automatikusan(tmp_path):
    hu = _ts("hu_HU", [("Files...", None, "Fájlok..."), ("Plain", None, "Kezdőlap")])
    out = _futtat(
        tmp_path, hu, None,
        {"p:menu": "Fájlok...", "p:label": "Fájlok:", "p:home": "Kezdőlap."},
        {"p:menu": "Dateien...", "p:label": "Dateien:", "p:home": "Startseite."},
    )
    de = _messages(out / "picasapy_de.ts")
    # „Fájlok..." két jelölt közül csak a „..." maradhat: pontosan az `p:menu`.
    assert _tr(de["Files..."]) == (None, "Dateien...")
    # a hiányzó vs. kiírt írásjel párosítása a #4313 szerint megmarad
    assert _tr(de["Plain"]) == (None, "Startseite.")


def test_csak_eltero_irasjelu_jelolt_eseten_unfinished(tmp_path):
    hu = _ts("hu_HU", [("Files...", None, "Fájlok...")])
    out = _futtat(tmp_path, hu, None, {"p:label": "Fájlok:"}, {"p:label": "Dateien:"})
    de = _messages(out / "picasapy_de.ts")
    assert _tr(de["Files..."])[0] == "unfinished"


def test_meglevo_hivatalos_fordítas_es_jelolo_valtozatlan(tmp_path):
    hu = _ts("hu_HU", [("Original Size", "picasapy-origin: picasa\npicasapy-origin-key: p:x", "Eredeti méret")])
    de = _ts(
        "de_DE",
        [("Original Size", "picasapy-origin: picasa\npicasapy-origin-key: p:x", "Originalgröße")],
    )
    # a magyar szöveg nem egyezik az XML-lel, a régi generátor ezt unfinished-re ejtette
    out = _futtat(tmp_path, hu, de, {"p:y": "Valami más"}, {"p:y": "Etwas"})
    message = _messages(out / "picasapy_de.ts")["Original Size"]
    assert _tr(message) == (None, "Originalgröße")
    assert message.findtext("extracomment") == (
        "picasapy-origin: picasa\npicasapy-origin-key: p:x"
    )


def test_magyar_jelolo_nem_ir_at_de_a_jelolo_nelkulit_kitolti(tmp_path):
    hu = _ts(
        "hu_HU",
        [
            ("Kept", "picasapy-origin: picasa\npicasapy-origin-key: p:regi", "Megtartott"),
            ("Fresh", None, "Friss"),
        ],
    )
    out = _futtat(tmp_path, hu, None, {"p:a": "Friss"}, {"p:a": "Frisch"})
    hu_out = _messages(out / "picasapy_hu.ts")
    assert hu_out["Kept"].findtext("extracomment") == (
        "picasapy-origin: picasa\npicasapy-origin-key: p:regi"
    )
    assert hu_out["Fresh"].findtext("extracomment") == (
        "picasapy-origin: picasa\npicasapy-origin-key: p:p:a"
    )


def test_hianyzo_uzenet_bekerul_a_megszunt_kiesik_az_unfinished_ujraszamolodik(tmp_path):
    hu = _ts("hu_HU", [("New", None, "Új"), ("Todo", None, "Teendő")])
    de = _ts(
        "de_DE",
        [
            ("Gone", "picasapy-origin: picasa", "Weg"),
            ("Todo", "picasapy-origin: picasapy", None),
        ],
    )
    out = _futtat(
        tmp_path, hu, de, {"p:n": "Új", "p:t": "Teendő"}, {"p:n": "Neu", "p:t": "Aufgabe"}
    )
    de_out = _messages(out / "picasapy_de.ts")
    assert "Gone" not in de_out
    assert _tr(de_out["New"]) == (None, "Neu")
    assert _tr(de_out["Todo"]) == (None, "Aufgabe")


def test_ket_futas_azonos_es_a_kitoltott_sor_nem_valtozik(tmp_path):
    jelolo = "picasapy-origin: picasa\npicasapy-origin-key: p:regi"
    hu = _ts(
        "hu_HU",
        [
            ("Kept", jelolo, "Megtartott"),
            ("Todo", None, "Teendő"),
            ("New", None, "Új"),
            ("Dup", None, "Ismétlődő"),
            ("Dup", None, "Ismétlődő"),
            ("Files...", None, "Fájlok…"),
            ("Dot", None, "Pont."),
        ],
    )
    de = _ts(
        "de_DE",
        [
            ("Kept", jelolo, "Behalten"),
            ("Todo", "picasapy-origin: picasapy", None),
            ("Dup", "picasapy-origin: picasapy", "Erste"),
            ("Dup", "picasapy-origin: picasapy", "Zweite"),
        ],
    )
    hu_ref = {"p:t": "Teendő", "p:n": "Új", "p:m": "Fájlok…", "p:l": "Fájlok:", "p:d": "Pont...", "p:i": "Ismétlődő"}
    de_ref = {"p:t": "Aufgabe", "p:n": "Neu", "p:m": "Dateien…", "p:l": "Dateien:", "p:d": "Punkt...", "p:i": "Wiederholt"}
    out = _futtat(tmp_path, hu, de, hu_ref, de_ref)
    first = {p.name: p.read_bytes() for p in out.glob("*.ts")}
    gen.build_dictionaries(tmp_path / "ref", out, compile_qm=False)
    assert {p.name: p.read_bytes() for p in out.glob("*.ts")} == first
    de_out = ET.parse(out / "picasapy_de.ts").getroot()
    rows = [m for m in de_out.iter("message") if m.findtext("source") == "Dup"]
    assert [_tr(m)[1] for m in rows] == ["Erste", "Zweite"]
    msgs = _messages(out / "picasapy_de.ts")
    assert _tr(msgs["Kept"]) == (None, "Behalten")
    assert _tr(msgs["Todo"]) == (None, "Aufgabe")
    assert _tr(msgs["New"]) == (None, "Neu")
    assert _tr(msgs["Files..."]) == (None, "Dateien…")
    # „.” és „...” külön osztály: a „Pont.” nem párosul a „Pont...”-tal
    assert _tr(msgs["Dot"])[0] == "unfinished"


def test_comment_kulonbozteti_meg_az_azonos_forrasu_sorokat(tmp_path):
    def rows(items):
        return "".join(
            f"<message><source>Same</source><comment>{c}</comment>"
            f"<translation>{t}</translation></message>"
            for c, t in items
        )

    def doc(lang, items):
        return (
            f'<?xml version="1.0" encoding="utf-8"?><TS version="2.1" language="{lang}">'
            f"<context><name>Ctx</name>{rows(items)}</context></TS>"
        )

    hu = doc("hu_HU", [("a", "Egy"), ("mid", "Közbe"), ("b", "Kettő")])
    de = doc("de_DE", [("a", "Eins"), ("b", "Zwei")])
    out = _futtat(tmp_path, hu, de, {"p:x": "Egy"}, {"p:x": "Eins"})
    got = {
        m.findtext("comment"): _tr(m)
        for m in ET.parse(out / "picasapy_de.ts").getroot().iter("message")
    }
    assert got["a"] == (None, "Eins")
    assert got["b"] == (None, "Zwei")


def _kitoltott(root: ET.Element) -> dict[tuple, tuple[bytes, bytes]]:
    """(környezet, forrás, sorszám) -> (extracomment, translation) a kitöltött soroknál."""
    result = {}
    for message, key in gen._message_keys(root):
        if gen._is_settled(message):
            result[key] = (
                ET.tostring(message.find("extracomment")) if message.find("extracomment") is not None else b"",
                ET.tostring(message.find("translation")),
            )
    return result


@pytest.mark.skipif(not _REFERENCIA.is_dir(), reason="nincs helyi referencia (~/picasapy-agent)")
def test_valodi_ts_eken_nem_modosit_hivatalosat_es_masodszorra_ures_diff(tmp_path):
    work = tmp_path / "i18n"
    work.mkdir()
    for path in _I18N.glob("picasapy_*.ts"):
        shutil.copy(path, work / path.name)
    before = {p.name: ET.parse(p).getroot() for p in work.glob("picasapy_*.ts")}
    assert len(before) == 41

    gen.build_dictionaries(_REFERENCIA, work, compile_qm=False)
    after_first = {p.name: p.read_bytes() for p in work.glob("picasapy_*.ts")}

    for name, root in before.items():
        settled_before = _kitoltott(root)
        after_root = ET.fromstring(after_first[name])
        settled_after = _kitoltott(after_root)
        all_after = {k for _m, k in gen._message_keys(after_root)}
        for key, value in settled_before.items():
            if key in all_after:  # a magyarból megszűnt üzenet kieshet
                assert key in settled_after and settled_after[key] == value, (name, key)
    hu_after = {
        key: message
        for message, key in gen._message_keys(ET.fromstring(after_first["picasapy_hu.ts"]))
    }
    for message, key in gen._message_keys(before["picasapy_hu.ts"]):
        origin = message.findtext("extracomment")
        if origin:
            assert hu_after[key].findtext("extracomment") == origin, key

    gen.build_dictionaries(_REFERENCIA, work, compile_qm=False)
    after_second = {p.name: p.read_bytes() for p in work.glob("picasapy_*.ts")}
    assert after_second == after_first
