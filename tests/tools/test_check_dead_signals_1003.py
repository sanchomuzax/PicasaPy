"""#1003 — a néma jelzések őrének tesztjei.

Az őr értéke két dolgon áll vagy bukik, és mindkettőt a KIMENETRE kell
állítani, nem arra, hogy „lefut hiba nélkül":

1. **Van foga**: a mesterségesen beadott néma jelzést megtalálja.
2. **Nem kiabál hiába**: ahol VAN fogadó, ott hallgat. A hamis riasztás itt
   rosszabb, mint a kihagyás — attól a csapat kikapcsolja az őrt, és akkor
   a #985/#989/#1001 hibaosztálya visszatér.

Ezért a fogadó minden alakjára külön eset van: QML-kezelő, `Connections`
blokk, Pythonból és QML-ből indított `.connect()`, property-értesítő.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import check_dead_signals as guard  # noqa: E402

CONTROLLER = """\
from PySide6.QtCore import QObject, Signal


class Vezerlo(QObject):
    valamiTortent = Signal(str)

    def fut(self):
        self.valamiTortent.emit("kesz")
"""


def _fa(tmp_path: Path, *, python: str = CONTROLLER, qml: str = "") -> Path:
    """Minta-forrásfa: egy vezérlő és — ha kell — egy QML-fájl."""
    gyoker = tmp_path / "src"
    (gyoker / "qml").mkdir(parents=True)
    (gyoker / "vezerlo.py").write_text(python, encoding="utf-8")
    if qml:
        (gyoker / "qml" / "Main.qml").write_text(qml, encoding="utf-8")
    return gyoker


def _nema_kulcsok(gyoker: Path) -> set[str]:
    return {jelzes.key for jelzes in guard.scan(gyoker).silent}


# -- 1. van foga -----------------------------------------------------------


def test_a_nema_jelzest_megtalalja(tmp_path: Path) -> None:
    """Kibocsátjuk, senki nem fogadja — az őrnek jeleznie KELL."""
    gyoker = _fa(tmp_path, qml='Item { Text { text: "semmi" } }')
    assert _nema_kulcsok(gyoker) == {"vezerlo.py::valamiTortent"}


def test_a_kijavitott_hibajelzesek_nem_maradnak_a_valodi_alapallapotban() -> None:
    """#1003: a két régi hibaút a látható `syncFailed` csatornára kerül."""
    live = guard.scan(_REPO_ROOT / "src" / "picasapy")
    keys = {signal.key for signal in live.silent}

    assert "app/people_controller.py::personWriteFailed" not in keys
    assert "app/perf_controller.py::diagnosticsFolderOpenFailed" not in keys


def test_a_futtatas_hibaval_ter_vissza_uj_nema_jelzesre(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A parancssori futás kilépési kódja és kimenete is jelezze az újat."""
    gyoker = _fa(tmp_path)
    alapallapot = tmp_path / "alap.txt"
    alapallapot.write_text("# üres alapállapot\n", encoding="utf-8")

    kod = guard.main(["--root", str(gyoker), "--baseline", str(alapallapot)])

    kimenet = capsys.readouterr().out
    assert kod == 1
    assert "ÚJ néma jelzés" in kimenet
    assert "vezerlo.py::valamiTortent" in kimenet


# -- 2. nem kiabál hiába: a fogadó minden ismert alakja --------------------


def test_a_cel_nelkuli_qml_kezelo_nem_fogad_python_jelzest(tmp_path: Path) -> None:
    """A QML saját `signal done`-jához tartozó `onDone` nem a Pythoné."""
    gyoker = _fa(
        tmp_path,
        python="""\
from PySide6.QtCore import QObject, Signal


class Worker(QObject):
    done = Signal()
""",
        qml="Item { signal done(); onDone: console.log(1) }",
    )
    assert _nema_kulcsok(gyoker) == {"vezerlo.py::done"}


def test_a_connections_blokkot_fogadonak_veszi(tmp_path: Path) -> None:
    """`Connections { target: ...; function onXxx() }` — a #305 óta ez a bevett alak."""
    qml = """\
Item {
    Connections {
        target: vezerlo
        function onValamiTortent(uzenet) { console.log(uzenet) }
    }
}
"""
    gyoker = _fa(tmp_path, qml=qml)
    assert _nema_kulcsok(gyoker) == set()


def test_a_python_connectet_fogadonak_veszi(tmp_path: Path) -> None:
    python = CONTROLLER + """

def koss(vezerlo, ablak):
    vezerlo.valamiTortent.connect(ablak.mutat)
"""
    gyoker = _fa(tmp_path, python=python)
    assert _nema_kulcsok(gyoker) == set()


def test_a_qml_bol_inditott_connectet_fogadonak_veszi(tmp_path: Path) -> None:
    """`Component.onCompleted`-ben kötött jelzés — ez sem néma."""
    qml = """\
Item {
    Component.onCompleted: vezerlo.valamiTortent.connect(root.mutat)
}
"""
    gyoker = _fa(tmp_path, qml=qml)
    assert _nema_kulcsok(gyoker) == set()


def test_a_property_ertesitot_kihagyja(tmp_path: Path) -> None:
    """A `notify=` jelzéseket a QML-kötések némán fogyasztják — nem hiba."""
    python = """\
from PySide6.QtCore import Property, QObject, Signal


class Vezerlo(QObject):
    cimValtozott = Signal()

    @Property(str, notify=cimValtozott)
    def cim(self):
        return "x"
"""
    gyoker = _fa(tmp_path, python=python)
    jelentes = guard.scan(gyoker)
    assert jelentes.silent == ()
    assert jelentes.notify == 1
    assert jelentes.action == 0


def test_a_notify_csak_a_sajat_osztaly_azonos_nevu_jelzeset_hagyja_ki(
    tmp_path: Path,
) -> None:
    """`A.done` property-értesítője nem nyelheti el `B.done` akciójelét."""
    gyoker = tmp_path / "src"
    gyoker.mkdir()
    (gyoker / "a.py").write_text(
        """\
from PySide6.QtCore import Property, QObject, Signal


class A(QObject):
    done = Signal()

    @Property(bool, notify=done)
    def ready(self):
        return True
""",
        encoding="utf-8",
    )
    (gyoker / "b.py").write_text(
        """\
from PySide6.QtCore import QObject, Signal


class B(QObject):
    done = Signal()
""",
        encoding="utf-8",
    )

    assert _nema_kulcsok(gyoker) == {"b.py::done"}


def test_a_deklaralo_modul_factoryjen_at_kotott_jelzes_nem_nema(
    tmp_path: Path,
) -> None:
    """A `get_a().done.connect(...)` a saját `a.py::done` jelzését fogadja."""
    gyoker = tmp_path / "src"
    gyoker.mkdir()
    (gyoker / "a.py").write_text(
        """\
from PySide6.QtCore import QObject, Signal


class A(QObject):
    done = Signal()


def get_a():
    return A()
""",
        encoding="utf-8",
    )
    (gyoker / "consumer.py").write_text(
        """\
from a import get_a


get_a().done.connect(lambda: None)
""",
        encoding="utf-8",
    )

    assert _nema_kulcsok(gyoker) == set()


# -- 3. pontosság: szóhatár és az azonos nevű jelzések ---------------------


def test_a_hasonlo_nevu_kezelo_nem_szamit_fogadonak(tmp_path: Path) -> None:
    """`onValamiTortentMasként` NEM a `valamiTortent` kezelője."""
    gyoker = _fa(tmp_path, qml="Item { onValamiTortentUtan: console.log(1) }")
    assert _nema_kulcsok(gyoker) == {"vezerlo.py::valamiTortent"}


def test_az_azonos_nevu_jelzesek_kulon_kulcsot_kapnak(tmp_path: Path) -> None:
    """Nyolc jelzésnév kétszer szerepel az éles fában — a kulcs a fájlt is viszi."""
    gyoker = _fa(tmp_path)
    (gyoker / "masik.py").write_text(CONTROLLER, encoding="utf-8")
    assert _nema_kulcsok(gyoker) == {
        "vezerlo.py::valamiTortent",
        "masik.py::valamiTortent",
    }


def test_a_connections_csak_a_sajat_qml_celjanak_jelzeset_fogadja(
    tmp_path: Path,
) -> None:
    """Azonos jelzésnévnél a másik vezérlő kezelője nem lehet ál-fogadó."""
    gyoker = tmp_path / "src"
    qml_dir = gyoker / "qml"
    qml_dir.mkdir(parents=True)
    for nev in ("a", "b"):
        (gyoker / f"{nev}.py").write_text(
            "from PySide6.QtCore import QObject, Signal\n\n"
            f"class {nev.upper()}(QObject):\n"
            "    done = Signal()\n",
            encoding="utf-8",
        )
    (qml_dir / "Main.qml").write_text(
        "Item {\n"
        "    Connections {\n"
        "        target: a\n"
        "        function onDone() {}\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )

    assert _nema_kulcsok(gyoker) == {"b.py::done"}


def test_a_property_alias_csak_a_sajat_pontos_rhs_at_oldja_fel(tmp_path: Path) -> None:
    """A szomszédos, nem kapcsolódó property nem lehet a `target` alias része."""
    gyoker = tmp_path / "src"
    qml_dir = gyoker / "qml"
    qml_dir.mkdir(parents=True)
    for nev in ("worker", "other"):
        (gyoker / f"{nev}.py").write_text(
            "from PySide6.QtCore import QObject, Signal\n\n"
            f"class {nev.title()}(QObject):\n"
            "    done = Signal()\n",
            encoding="utf-8",
        )
    (qml_dir / "Main.qml").write_text(
        """\
Item {
    property var endpoint: worker
    property var unrelated: other
    Connections {
        target: root.endpoint
        function onDone() {}
    }
}
""",
        encoding="utf-8",
    )

    assert _nema_kulcsok(gyoker) == {"other.py::done"}


def test_az_azonos_nevu_aliasok_qml_fajlonkent_kulon_oldodnek_fel(
    tmp_path: Path,
) -> None:
    """Egy QML-fájl `endpoint` propertyje nem szivároghat át a másikba."""
    gyoker = tmp_path / "src"
    qml_dir = gyoker / "qml"
    qml_dir.mkdir(parents=True)
    for nev in ("worker", "other"):
        (gyoker / f"{nev}.py").write_text(
            "from PySide6.QtCore import QObject, Signal\n\n"
            f"class {nev.title()}(QObject):\n"
            "    done = Signal()\n",
            encoding="utf-8",
        )
    for qml_name, target in (("One.qml", "worker"), ("Two.qml", "other")):
        (qml_dir / qml_name).write_text(
            "Item {\n"
            f"    property var endpoint: {target}\n"
            "    Connections {\n"
            "        target: root.endpoint\n"
            "        function onDone() {}\n"
            "    }\n"
            "}\n",
            encoding="utf-8",
        )

    assert _nema_kulcsok(gyoker) == set()


# -- 4. az alapállapot: rövidülhet, de nem hízhat --------------------------


def test_az_alapallapotban_szereplo_tetel_nem_bukik(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    gyoker = _fa(tmp_path)
    alapallapot = tmp_path / "alap.txt"
    alapallapot.write_text(
        "vezerlo.py::valamiTortent #1003 — tudatos tartalék\n", encoding="utf-8"
    )

    kod = guard.main(["--root", str(gyoker), "--baseline", str(alapallapot)])

    assert kod == 0
    assert "Rendben" in capsys.readouterr().out


def test_az_elavult_bejegyzes_bukik(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ha a tétel már NEM néma, a sorát törölni kell — a lista ne konzerváljon."""
    gyoker = _fa(
        tmp_path,
        qml="""\
Item {
    Connections {
        target: vezerlo
        function onValamiTortent() {}
    }
}
""",
    )
    alapallapot = tmp_path / "alap.txt"
    alapallapot.write_text(
        "vezerlo.py::valamiTortent #1003 — tudatos tartalék\n", encoding="utf-8"
    )

    kod = guard.main(["--root", str(gyoker), "--baseline", str(alapallapot)])

    kimenet = capsys.readouterr().out
    assert kod == 1
    assert "ELAVULT" in kimenet
    assert "vezerlo.py::valamiTortent" in kimenet


def test_az_indoklas_nelkuli_tetel_hiba(tmp_path: Path) -> None:
    """„Néma engedély" nincs: minden sor mellé jegyszám vagy indoklás kell."""
    alapallapot = tmp_path / "alap.txt"
    alapallapot.write_text("vezerlo.py::valamiTortent\n", encoding="utf-8")
    with pytest.raises(ValueError, match="INDOKLÁS"):
        guard.load_baseline(alapallapot)


def test_a_ketszer_szereplo_tetel_hiba(tmp_path: Path) -> None:
    alapallapot = tmp_path / "alap.txt"
    alapallapot.write_text(
        "a.py::x #1 — egy\na.py::x #2 — ketto\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="kétszer"):
        guard.load_baseline(alapallapot)


def test_a_lista_nem_nohet_a_felso_korlat_fole(tmp_path: Path) -> None:
    """Az „új néma jelzés = piros CI" szabály egy sor beírásával kerülhető ki.

    A plafon ezt teszi tudatos lépéssé: a korláton túli tételhez a szkriptben
    álló számot is emelni kell, azt pedig a felülvizsgálat látja.
    """
    alapallapot = tmp_path / "alap.txt"
    sorok = [
        f"a.py::jelzes{index} #1003 — tartalék" for index in range(guard.MAX_BASELINE_ENTRIES + 1)
    ]
    alapallapot.write_text("\n".join(sorok) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="felső korlát"):
        guard.load_baseline(alapallapot)


def test_a_hibas_alapallapot_kettes_kilepesi_kodot_ad(tmp_path: Path) -> None:
    """A CI-nek látszania kell, hogy nem a kód rossz, hanem a lista."""
    gyoker = _fa(tmp_path)
    assert guard.main(["--root", str(gyoker), "--baseline", str(tmp_path / "nincs")]) == 2


def test_a_hianyzo_gyoker_kettes_kilepesi_kodot_ad(tmp_path: Path) -> None:
    assert guard.main(["--root", str(tmp_path / "nincs")]) == 2


# -- 5. az ÉLES fa: az alapállapot ne rohadjon el --------------------------


def test_az_eles_forrasfa_egyezik_az_alapallapottal() -> None:
    """Ugyanaz, amit a CI futtat — itt a helyi futás is megfogja."""
    assert guard.main([]) == 0


def test_az_alapallapot_minden_tetelehez_van_indoklas() -> None:
    tetelek = guard.load_baseline(guard._DEFAULT_BASELINE)
    assert tetelek, "az alapállapot nem lehet üres, amíg van néma jelzés"
    assert all(indoklas.strip() for indoklas in tetelek.values())
