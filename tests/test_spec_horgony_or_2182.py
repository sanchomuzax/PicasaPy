"""A spec-lapok horgony-előírása (22.4) — betartatva (#2182).

A `docs/specs/binaris-regeszet-modszertan.md` **22.4** pontja előírja, hogy
az elemet dokumentáló szakaszban legyen **horgony**: `0x00…` kódcím vagy
`fájl.kiterjesztés:sor`. Eddig ezt **semmi nem tartatta be**, és ennek mért
ára volt: a `picasa-nyomtatas.md` nyomtatási táblája 26 sorban, teljes néven
írt le `printoptions/*` elemeket — horgony nélkül —, ezért a lefedettségi
mérő mind a **12** elemet `feltáratlan`-nak sorolta, vagyis a kutatói körök
munkalistájára tette azt, ami már le volt írva. A teljes mérés:
`docs/specs/binaris-regeszet-modszertan.md` 22.5.

A mechanizmus a privát mérő `lekutatott_elemek()` függvényében van: szakaszonként
dolgozik, és horgony nélkül a **teljes szakaszt** átugorja — némán.

Ez az őr ugyanazzal a szakaszolással és ugyanazokkal a mintákkal dolgozik,
tehát azt állítja, amit a mérő tenni fog: *ezt a szakaszt át fogja ugrani.*
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.support import spec_horgony as sh

GYOKER = Path(__file__).resolve().parents[1]
SPEC_DIR = GYOKER / "docs" / "specs"


def _lap(tmp_path: Path, nev: str, szoveg: str) -> Path:
    (tmp_path / nev).write_text(szoveg, encoding="utf-8")
    return tmp_path


# --- A FOG: ezek mérik, hogy az őr tényleg elbukik a rossz szakaszon --------

TABLA = (
    "| elem | felirat |\n"
    "|---|---|\n"
    "| `printoptions/usenotext` | Nincs szöveg |\n"
)


def test_horgony_nelkuli_elemtablara_BUKIK(tmp_path):
    """A fog. Enélkül az őr zöld lenne úgy is, hogy semmit nem mér."""
    hely = _lap(tmp_path, "proba.md", f"## A nyomtatás beállításai\n\n{TABLA}")

    sertesek = sh.sertesek(hely, {"printoptions"})

    assert [(s.lap, s.cim) for s in sertesek] == [
        ("proba.md", "## A nyomtatás beállításai")
    ]
    assert sertesek[0].elemek == ("printoptions/usenotext",)


@pytest.mark.parametrize(
    "horgony",
    [
        "A vezérlő a `0x004b1e20` címen áll.",
        "Forrás: `printoptions.tre:43`.",
        "Geometria: `respack.yt:118`.",
    ],
)
def test_horgonnyal_MAR_NEM_bukik(tmp_path, horgony):
    """Mindhárom engedett horgony-alak feloldja a sértést."""
    hely = _lap(tmp_path, "proba.md", f"## Beállítások\n\n{horgony}\n\n{TABLA}")

    assert sh.sertesek(hely, {"printoptions"}) == []


def test_a_SZAKASZ_a_bizonyitas_egysege(tmp_path):
    """Másik szakaszban álló horgony NEM igazol — ezt teszi a mérő is."""
    hely = _lap(
        tmp_path,
        "proba.md",
        f"## Cím `printoptions.tre:43`\n\nszöveg\n\n## Elemek\n\n{TABLA}",
    )

    assert [s.cim for s in sh.sertesek(hely, {"printoptions"})] == ["## Elemek"]


def test_a_szinkonstans_NEM_horgony(tmp_path):
    """`0xFF…` egy ARGB szín, nem kódcím — a mérő is csak `0x00…`-t fogad el."""
    hely = _lap(tmp_path, "proba.md", f"## Elemek\n\nSzín: `0xFF7D8397`.\n\n{TABLA}")

    assert len(sh.sertesek(hely, {"printoptions"})) == 1


def test_a_puszta_PROZAI_emlites_nem_sertes(tmp_path):
    """Az őr a dokumentáló TÁBLÁT nézi, nem a folyó szöveget.

    Szándékos hatókör-szűkítés: az elemnevet említő próza (pl. egy nyitott
    kérdés megfogalmazása) nem dokumentáció, tehát nem is veszít el semmit
    a mérésben. Ha ez is sértés lenne, az őr minden őszinte írásbeli
    felvetést büntetne — mérve 150 szakasz 40 lapon, szemben a
    táblasoros 58-cal.
    """
    hely = _lap(
        tmp_path,
        "proba.md",
        "## Nyitott kérdés\n\nA `printoptions/usenotext` hatása ismeretlen.\n",
    )

    assert sh.sertesek(hely, {"printoptions"}) == []


def test_a_generalt_lapokat_kihagyja(tmp_path):
    """A generált lapokat nem a spec-író írja — rajtuk a 22.4 értelmetlen."""
    hely = _lap(tmp_path, "ui-lefedettseg.md", f"## Elemek\n\n{TABLA}")

    assert sh.sertesek(hely, {"printoptions"}) == []


# --- Az ÉLES fa ------------------------------------------------------------


def test_nincs_UJ_horgony_nelkuli_elemtabla():
    """A mai fán csak az ismert, jegyre kötött sértések állhatnak.

    A 22.4-et évekig semmi nem tartatta be, ezért a bevezetéskor 58 valódi
    sértés állt 30 lapon (mérve, #2182). Ezeket egyenként fel kell horgonyozni
    — az a #2193 dolga —, de amíg az meg nem történt, az őr ÚJAKRA már bukik.
    """
    ismert = sh.ismert_sertesek()
    ujak = [s for s in sh.sertesek(SPEC_DIR, sh.panelnevek()) if s.kulcs() not in ismert]

    assert not ujak, "horgony nélküli elemtábla — a 22.4 megsértve:\n" + sh.jelentes(ujak)


def test_az_ismert_lista_nem_avulhat_el():
    """Elavult bejegyzés = elnyelt regresszió (#659 tanulsága).

    Ha egy szakasz megkapta a horgonyt (vagy átnevezték a címét), a
    bejegyzésének is el kell tűnnie innen, különben a lista némán újra
    kimentene egy visszaesést ugyanazon a címen.
    """
    elo = {s.kulcs() for s in sh.sertesek(SPEC_DIR, sh.panelnevek())}
    elavult = sorted(k for k in sh.ismert_sertesek() if k not in elo)

    assert not elavult, "javított/átnevezett szakasz maradt az ismert-listán — töröld:\n" + "\n".join(
        f"  {lap} :: {cim}" for lap, cim in elavult
    )


def test_az_ismert_lista_minden_bejegyzese_jegyre_hivatkozik():
    """A lista nem tárolóhely: minden tétel mögött legyen nyitott jegy."""
    adat = json.loads(sh.ISMERT_UT.read_text(encoding="utf-8"))

    assert adat["_jegy"], "az ismert-listának meg kell neveznie a levezető jegyet"
