"""A szabályváltozás-jelző próbasora — #48 (agent-repó).

## A hibaosztály

A szabálykönyvek **csak induláskor** töltődnek be, a felhasználó viszont
napokig élő munkameneteket futtat. 2026-09-04-én egy 07:22-kor bevezetett
szabály után három élő session **hét órán át** dolgozott a régi módon — a
#2336 foglalása azonosító nélkül ment. Nem szegte meg senki: nem volt honnan
tudniuk.

Az értesítés nem ért el hozzájuk: ütemezett körből a `send_message` tiltott, a
`session_emlekezteto.md` pedig csak az ütemezett köröket éri el.

Ez a jelző az a csatorna, ami **minden** munkamenethez elér, mert minden
munkamenet futtat parancsot. Nem kapu: **soha nem blokkol**, csak szól.
"""

import importlib.util
import io
import json
import pathlib

import pytest

_UT = (pathlib.Path(__file__).resolve().parents[2]
       / "scripts" / "hooks" / "szabalyvaltozas_jelzo.py")
_spec = importlib.util.spec_from_file_location("szabalyvaltozas_jelzo", _UT)
jelzo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(jelzo)


@pytest.fixture()
def kornyezet(tmp_path, monkeypatch):
    """Két szabálykönyv és egy üres állapot-mappa."""
    szabalyok = tmp_path / "szabalyok"
    szabalyok.mkdir()
    (szabalyok / "CLAUDE.md").write_text("első\n", encoding="utf-8")
    (szabalyok / "PROTOKOLL.md").write_text("második\n", encoding="utf-8")
    monkeypatch.setattr(jelzo, "SZABALYKONYVEK", [
        szabalyok / "CLAUDE.md", szabalyok / "PROTOKOLL.md"])
    monkeypatch.setattr(jelzo, "ALLAPOT_MAPPA", tmp_path / "allapot")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "proba-session")
    return szabalyok


def _fut(monkeypatch, cmd="ls"):
    monkeypatch.setattr("sys.stdin", io.StringIO(
        json.dumps({"tool_input": {"command": cmd}, "cwd": "."})))
    hiba = io.StringIO()
    monkeypatch.setattr("sys.stderr", hiba)
    kod = jelzo.main()
    return kod, hiba.getvalue()


def test_az_elso_futas_CSAK_rogzit(kornyezet, monkeypatch):
    """Induláskor nincs mihez képest változás — hallgatnia kell."""
    kod, uzenet = _fut(monkeypatch)

    assert kod == 0
    assert uzenet == "", "az első futás zajt csinált"


def test_a_valtozast_JELZI(kornyezet, monkeypatch):
    """A FOG. Enélkül a session órákig a régi szabállyal dolgozik."""
    _fut(monkeypatch)
    (kornyezet / "PROTOKOLL.md").write_text("második, MÁSKÉPP\n", encoding="utf-8")

    kod, uzenet = _fut(monkeypatch)

    assert kod == 0, "a jelző soha nem blokkolhat"
    assert "PROTOKOLL.md" in uzenet, "nem nevezte meg, MI változott"
    assert "CLAUDE.md" not in uzenet, "a változatlan fájlt is bejelentette"


def test_CSAK_EGYSZER_szol_ugyanarra(kornyezet, monkeypatch):
    """Minden parancs előtt fut — ismételve elviselhetetlen zaj lenne."""
    _fut(monkeypatch)
    (kornyezet / "CLAUDE.md").write_text("első, MÁSKÉPP\n", encoding="utf-8")
    _, elso = _fut(monkeypatch)

    _, masodik = _fut(monkeypatch)

    assert elso, "az első jelzés elmaradt"
    assert masodik == "", "másodszor is szólt ugyanarra a változásra"


def test_UJABB_valtozasra_ismet_szol(kornyezet, monkeypatch):
    """A némítás a LÁTOTT állapotra szól, nem örökre."""
    _fut(monkeypatch)
    (kornyezet / "CLAUDE.md").write_text("A\n", encoding="utf-8")
    _fut(monkeypatch)
    _fut(monkeypatch)
    (kornyezet / "CLAUDE.md").write_text("B\n", encoding="utf-8")

    _, uzenet = _fut(monkeypatch)

    assert "CLAUDE.md" in uzenet


def test_HIANYZO_szabalykonyv_nem_okoz_bajt(kornyezet, monkeypatch):
    """A privát repó klónja hiányozhat — attól még dolgozni kell."""
    monkeypatch.setattr(jelzo, "SZABALYKONYVEK",
                        [kornyezet / "nincs-ilyen.md"])

    kod, uzenet = _fut(monkeypatch)

    assert kod == 0
    assert uzenet == ""


def test_ELROMLOTT_jelzo_sem_blokkol(kornyezet, monkeypatch):
    """Fail-open: egy hibás jelző nem akaszthatja meg a munkát."""
    monkeypatch.setattr("sys.stdin", io.StringIO("ez nem json"))
    monkeypatch.setattr("sys.stderr", io.StringIO())

    assert jelzo.main() == 0


def test_SESSION_azonosito_nelkul_is_mukodik(kornyezet, monkeypatch):
    """Ha nincs azonosító, inkább hallgat, mint hogy hibázzon."""
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)

    kod, _ = _fut(monkeypatch)

    assert kod == 0
