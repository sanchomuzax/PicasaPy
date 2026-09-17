"""A PR-kapu próbasora (agent-#92).

Két szabály, amelyiknek eddig nem volt kapuja, és 2026-09-17-én mindkettőt
megszegtem:

1. **a PR nevezzen meg jegyet** — két PR jegy nélkül nyílt, csak a tulajdonos
   kérdésére lett jegye;
2. **az aláírás tiltott** — a PR szerzője már a bot, a lábléc ugyanazt
   ismétli, és a globális szabály szerint az attribúció ki van kapcsolva.

⚠️ A pozitív kontroll a **VALÓDI parancs alakjával** fut, `--body-file`-lal:
a projekt szabálya szerint a törzs mindig fájlból jön, tehát a parancssorban
csak az útvonal áll. Egy kapu, ami csak az inline törzset nézi, épp a
szokásos alakot engedné át.
"""

from __future__ import annotations

import importlib.util
import io
import json
import pathlib

import pytest

_UT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "scripts" / "hooks" / "pr_jegy_kapu.py"
)
_spec = importlib.util.spec_from_file_location("pr_jegy_kapu", _UT)
kapu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapu)

T = "--title"
ALAIRAS = "🤖 Generated with [Claude Code](https://claude.com/claude-code)"


@pytest.fixture
def torzs(tmp_path):
    """A törzs-fájl útvonala **POSIX alakban** (előre dőlő jelekkel).

    ⚠️ Nem kényelmi választás: a kapu `shlex.split`-tel, POSIX szabály
    szerint bontja a parancsot — ez a helyes, mert a hookot a fejlesztői gép
    shellje adja be. Windowson a `str(p)` visszafelé dőlő jeleket ad
    (`C:\\Users\\...`), amiket a POSIX-bontás ESCAPE-nek olvas és lenyel: a
    fájl megnyithatatlan lesz, a kapu fail-openre esik, és a próba
    „átengedte" hibával bukik. A windows-CI pontosan ezen hasalt el
    (2026-09-18, piros main). A POSIX-alakú útvonalat MINDKÉT platform
    megnyitja, tehát az állítás ugyanaz marad."""

    def ir(tartalom: str) -> str:
        p = tmp_path / "torzs.md"
        p.write_text(tartalom, encoding="utf-8")
        return p.as_posix()
    return ir


class TestAJegyhivatkozas:
    def test_a_VALODI_eset_blokkolva(self, torzs) -> None:
        """A #3291 parancsa: jegy nélkül nyílt, `--body-file`-lal."""
        f = torzs("Egy sor a gitignore-ba.\n")
        assert kapu.blokkolando(
            f"gh-bot pr create --repo r --base main --head h {T} 'chore: x' "
            f"--body-file {f}")

    def test_a_torzsben_megnevezett_jegy_atmegy(self, torzs) -> None:
        f = torzs("Egy sor.\n\nJegy: sanchomuzax/picasapy-agent#92\n")
        assert not kapu.blokkolando(
            f"gh-bot pr create --repo r {T} 'chore: x' --body-file {f}")

    def test_a_CIMBEN_megnevezett_jegy_is_eleg(self, torzs) -> None:
        f = torzs("Egy sor, jegyszám nélkül.\n")
        assert not kapu.blokkolando(
            f"gh-bot pr create --repo r {T} 'fix: valami (#3288)' "
            f"--body-file {f}")

    def test_inline_torzs_jegy_nelkul(self) -> None:
        assert kapu.blokkolando(f"gh-bot pr create --repo r {T} 'x' --body 'semmi'")

    def test_inline_torzs_jeggyel(self) -> None:
        assert not kapu.blokkolando(
            f"gh-bot pr create --repo r {T} 'x' --body 'lásd #92'")


class TestAzAlairas:
    def test_a_lablec_blokkolva(self, torzs) -> None:
        f = torzs(f"Egy sor.\n\nJegy: #92\n\n{ALAIRAS}\n")
        indok = kapu.blokkolando(
            f"gh-bot pr create --repo r {T} 'x' --body-file {f}")
        assert indok and "lablec" in indok

    def test_a_lablec_akkor_is_blokkol_ha_VAN_jegy(self, torzs) -> None:
        """A két szabály független: a jegy megléte nem menti az aláírást."""
        f = torzs(f"Jegy: #92\n{ALAIRAS}\n")
        assert kapu.blokkolando(
            f"gh-bot pr create --repo r {T} 'x (#92)' --body-file {f}")


class TestAmitNemErint:
    @pytest.mark.parametrize("cmd", [
        "gh-bot pr view 3291 --repo r",
        "gh-bot pr list --repo r",
        "gh-bot pr checks 3291 --repo r",
        "gh-bot pr diff 3291 --repo r",
        "gh-bot pr edit 3291 --repo r --add-label bug",
        "gh-bot issue create --repo r --body 'x'",
    ])
    def test_atengedi(self, cmd: str) -> None:
        assert not kapu.blokkolando(cmd)

    def test_a_torzs_atirasat_viszont_fogja(self, torzs) -> None:
        f = torzs("semmi jegy\n")
        assert kapu.blokkolando(f"gh-bot pr edit 3291 --repo r --body-file {f}")


class TestMindenBurkolo:
    @pytest.mark.parametrize("eszkoz", [
        "gh", "gh-bot", "codex-bot", "opencode-bot", "hermes-bot",
        "~/picasapy-agent/eszkozok/gh-bot",
    ])
    def test_eszkozonkenti_burkolo_is_fogva(self, eszkoz: str) -> None:
        """⛔ Ez a hibaosztály háromszor harapott: az őr csak egy nevet
        ismert, és a másik eszköz parancsát átengedte."""
        assert kapu.blokkolando(f"{eszkoz} pr create --repo r {T} 'x' --body 'semmi'")


class TestFailOpen:
    def test_olvashatatlan_torzs_fajl_ATENGED(self) -> None:
        """A kapu nem tudja, mi van benne — blokkolni nem szabad.

        ⚠️ Ezt a próba fogta meg: a docstring fail-open-t ígért, a kód
        viszont blokkolt volna.
        """
        assert not kapu.blokkolando(
            f"gh-bot pr create --repo r {T} 'x' --body-file /nincs/ilyen.md")

    def test_rossz_bemenetre_nulla(self, monkeypatch) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO("nem json"))
        assert kapu.main() == 0

    def test_blokkolas_kilepokodja_2(self, monkeypatch) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
            {"tool_input": {"command":
                f"gh-bot pr create --repo r {T} 'x' --body 'semmi'"}})))
        assert kapu.main() == 2

class TestBackslashesUtvonal:
    """#3302: a backslash-es útvonal ne nyelje el a kaput.

    A `shlex` POSIX-módban a `\\`-t escape-nek veszi, tehát egy windowsos
    útvonalból (`C:\\Users\\...`) eltűnnek a választójelek: a kapu nem létező
    fájlt nyitna, az „olvashatatlan → átenged" ágra futna, és a VALÓDI
    elkövetőt is átengedné. A main windows-lába ettől ment pirosra.

    ⚠️ A próba Linuxon is MÉR, nem skipel: ott a `\\` rendes fájlnév-karakter,
    tehát az elnyelődés ugyanúgy kimutatható. (A környezetfüggő skip nem őr.)"""

    def test_a_backslashes_utvonalu_torzs_is_elolvasva(self, tmp_path):
        mappa = tmp_path / "wt"
        mappa.mkdir()
        fajl = mappa / "Temp\\picasapy\\torzs.md"
        fajl.parent.mkdir(parents=True, exist_ok=True)
        fajl.write_text("Torzs jegyszam nelkul.\n", encoding="utf-8")
        indok = kapu.blokkolando(
            f"gh-bot pr create --repo r {T} 'chore: x' --body-file {fajl}")
        assert indok and "jegyet" in indok

    def test_a_nem_utf8_torzs_sem_engedi_at(self, tmp_path):
        """Rossz bájt a törzsben: a kapu akkor sem lesz néma.

        Korábban a rendszer kódlapja `UnicodeDecodeError`-t adott, és a
        kapu fail-open lett — pedig a jegyszámot és az aláírást a hibás
        bájt mellett is meg tudjuk keresni."""
        fajl = tmp_path / "torzs.md"
        fajl.write_bytes(b"Torzs jegyszam nelkul \x8f vege.\n")
        indok = kapu.blokkolando(
            f"gh-bot pr create --repo r {T} 'chore: x' --body-file {fajl}")
        assert indok and "jegyet" in indok
