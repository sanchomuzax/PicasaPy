"""A #4462 paritástáblák teljességét és kódbeli horgonyait őrző CI-teszt."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[2]
_GYORS_SPEC = _GYOKER / "docs/specs/picasa-gyorsbillentyuk.md"
_MENU_SPEC = _GYOKER / "docs/specs/ui-audit-context-menus.md"
_QML_GYOKER = _GYOKER / "src/picasapy/app/qml"

_ALLAPOTOK = (
    "megvan és működik",
    "hiányzik",
    "nem cél",
    "tisztázandó",
)


def _tabla_sorok(szoveg: str) -> list[list[str]]:
    sorok = []
    for sor in szoveg.splitlines():
        if not sor.lstrip().startswith("|"):
            continue
        cellak = [c.strip() for c in sor.strip().strip("|").split("|")]
        if not cellak or set(cellak[0]) <= {"-", ":"}:
            continue
        sorok.append(cellak)
    return sorok


def _fejezet_tabla(utvonal: Path, kezdo: str) -> list[list[str]]:
    szoveg = utvonal.read_text(encoding="utf-8")
    assert kezdo in szoveg, f"hiányzik a #4462 táblázat: {kezdo}"
    resz = szoveg.split(kezdo, 1)[1]
    return _tabla_sorok(resz)


def _allapot(cell: str) -> str:
    tiszta = cell.replace(chr(96), "").replace("*", "").replace("_", "").casefold()
    talalatok = [a for a in _ALLAPOTOK if a in tiszta]
    assert len(talalatok) == 1, f"hiányzik vagy kétértelmű az állapot: {cell}"
    return talalatok[0]


def _qml_forrasok() -> str:
    return "\n".join(
        utvonal.read_text(encoding="utf-8")
        for utvonal in _QML_GYOKER.rglob("*.qml")
    )


def test_mind_a_48_eredeti_keymaprekeszhez_van_osszevetesi_sor():
    spec = _GYORS_SPEC.read_text(encoding="utf-8")
    eredeti_resz = spec.split("### 2.5", 1)[1].split("## 3.", 1)[0]
    eredeti = _tabla_sorok(eredeti_resz)
    assert [int(sor[0]) for sor in eredeti[1:]] == list(range(1, 49))

    aktualis = _fejezet_tabla(_GYORS_SPEC, "## 11. #4462")
    sorok = aktualis[1:]
    assert [int(sor[0]) for sor in sorok] == list(range(1, 49))
    assert len(eredeti[1:]) == len(sorok)
    qml = _qml_forrasok()
    for eredeti_sor, sor in zip(eredeti[1:], sorok, strict=True):
        assert eredeti_sor[0] == sor[0]
        eredeti_bill = eredeti_sor[2].replace(chr(96), "")
        nalunk_bill = sor[1].replace(chr(96), "")
        assert eredeti_bill in nalunk_bill, (
            f"a {sor[0]}. eredeti billentyű megváltozott: "
            f"{eredeti_sor[2]} → {sor[1]}"
        )
        assert _allapot(sor[4]) in _ALLAPOTOK
        assert sor[3].strip() not in {"", "—", "-"}
        assert sor[5].strip() not in {"", "—", "-"}
        assert "tests/" in sor[6], f"a {sor[0]}. sorhoz nincs teszthivatkozás"
        tesztek = re.findall(r"tests/[A-Za-z0-9_./-]+", sor[6])
        assert tesztek and all((_GYOKER / t).is_file() for t in tesztek), (
            f"a {sor[0]}. hivatkozott tesztfájl hiányzik: {sor[6]}"
        )
        if _allapot(sor[4]) == "megvan és működik":
            horgonyok = re.findall(
                r"(?:objectName|sequence|Keys)=([^\s,;]+)", sor[3]
            )
            assert horgonyok, f"a {sor[0]}. sorhoz nincs QML-horgony"
            assert any(horgony in qml for horgony in horgonyok), (
                f"a {sor[0]}. QML-horgony eltűnt: {sor[3]}"
            )

    idorend = sorok[23]
    assert _allapot(idorend[4]) == "nem cél" and "#4443" in idorend[4]
    tisztazando = [s for s in sorok if _allapot(s[4]) == "tisztázandó"]
    assert all(len(s[4]) > len("tisztázandó") for s in tisztazando), (
        "a tisztázandó billentyűk indoka hiányzik"
    )


def test_a_helyi_menu_tabla_minden_eredeti_kontextust_es_tetelt_orzi():
    tabla = _fejezet_tabla(_MENU_SPEC, "## E. #4462")
    sorok = tabla[1:]
    vart_darabszamok = {
        "AlbumList": 15,
        "Indexkép": 23,
        "Album": 12,
        "OneUp": 19,
        "PplAlbum": 4,
        "PplAlbumPhoto": 4,
    }
    assert Counter(s[0] for s in sorok) == Counter(vart_darabszamok)
    assert all(len(s) == 6 for s in sorok), "a menüsor oszlopa hiányos"
    assert len({(s[0], s[1]) for s in sorok}) == len(sorok), (
        "ugyanaz az eredeti parancs kétszer került a táblába"
    )

    qml = _qml_forrasok()
    for sor in sorok:
        assert _allapot(sor[4])
        assert sor[2].strip() not in {"", "—", "-"}
        assert sor[5].strip() not in {"", "—", "-"}
        tesztek = re.findall(r"tests/[A-Za-z0-9_./-]+", sor[5])
        assert all((_GYOKER / t).is_file() for t in tesztek), (
            f"a {sor[0]} / {sor[1]} hivatkozott tesztfájlja hiányzik: {sor[5]}"
        )
        if _allapot(sor[4]) == "megvan és működik":
            assert tesztek, f"a {sor[0]} / {sor[1]} működéséhez nincs teszt"
        if _allapot(sor[4]) == "megvan és működik":
            objektumnevek = re.findall(
                r"objectName[=:]([A-Za-z][A-Za-z0-9_]*)", sor[3]
            )
            assert objektumnevek, f"nincs QML-horgony: {sor}"
            assert any(nev in qml for nev in objektumnevek), (
                f"a QML-horgony eltűnt: {sor[3]}"
            )


def test_a_tisztazando_es_nem_cel_menuallapotok_indokoltak():
    tabla = _fejezet_tabla(_MENU_SPEC, "## E. #4462")
    for sor in tabla[1:]:
        allapot = _allapot(sor[4])
        if allapot in {"nem cél", "tisztázandó", "hiányzik"}:
            assert len(sor[4]) > len(allapot), (
                f"a {sor[0]} / {sor[1]} sor állapotának nincs indoka/javaslata"
            )
