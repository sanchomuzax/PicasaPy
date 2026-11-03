"""#6458: a frissítés foglalt fájlnál nem áll vissza azonnal, és a kudarcot kiírja.

A tulajdonos céges gépén (2026-11-03) az 1.0.26 -> 1.0.29 csere háromszor
`[WinError 32]`-vel állt vissza: a program egyik fájlját egy másik folyamat
fogta. A segéd azonnal visszaállt, és a program a következő induláskor nem
mondott semmit.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from picasapy.app import update_ablak, update_eredmeny, update_folyamatok, update_swap_helper
from picasapy.app.update_swap_helper import swap_update_directory


class _Ora:
    def __init__(self) -> None:
        self.most = 0.0

    def __call__(self) -> float:
        return self.most

    def alszik(self, mp: float) -> None:
        self.most += mp


def _foglalt() -> OSError:
    hiba = PermissionError(13, "A folyamat nem fér hozzá a fájlhoz")
    hiba.winerror = 32
    return hiba


def test_foglalt_atnevezes_ujraprobalkozik_es_vegul_sikerul(tmp_path):
    ora = _Ora()
    probak: list[tuple[Path, Path]] = []

    def rename(forras, cel):
        probak.append((forras, cel))
        if len(probak) < 3:
            raise _foglalt()

    update_folyamatok.atnevez_ujraprobalva(
        tmp_path / "a", tmp_path / "b", rename=rename, alszik=ora.alszik, ora=ora
    )

    assert len(probak) == 3
    assert ora.most > 0


def test_foglalt_atnevezes_a_hatarido_utan_feladja(tmp_path):
    ora = _Ora()

    def rename(_forras, _cel):
        raise _foglalt()

    with pytest.raises(OSError):
        update_folyamatok.atnevez_ujraprobalva(
            tmp_path / "a", tmp_path / "b", hatarido=10.0,
            rename=rename, alszik=ora.alszik, ora=ora,
        )
    assert 10.0 <= ora.most <= 15.0


def test_mas_hiba_nem_vart_ujraprobalast(tmp_path):
    ora = _Ora()
    probak = []

    def rename(_forras, _cel):
        probak.append(1)
        raise FileNotFoundError(2, "nincs")

    with pytest.raises(FileNotFoundError):
        update_folyamatok.atnevez_ujraprobalva(
            tmp_path / "a", tmp_path / "b", rename=rename, alszik=ora.alszik, ora=ora
        )
    assert probak == [1]


def test_a_telepitesi_mappa_maradek_folyamatait_megvarja_majd_leallitja(tmp_path):
    ora = _Ora()
    eletben = {101, 102}
    leallitott: list[int] = []

    def lista(_mappa, sajat_pid):
        assert sajat_pid == 7
        return sorted(eletben)

    def leallit(pid):
        leallitott.append(pid)
        eletben.discard(pid)

    db = update_folyamatok.varj_vagy_allitsd_le(
        tmp_path, sajat_pid=7, hatarido=5.0,
        lista=lista, leallit=leallit, alszik=ora.alszik, ora=ora,
    )

    assert db == 2
    assert leallitott == [101, 102]
    assert ora.most >= 5.0


def test_ha_a_maradek_folyamat_magatol_kilep_nem_allitja_le(tmp_path):
    ora = _Ora()
    eletben = {101}

    def lista(_mappa, sajat_pid):
        if ora.most >= 1.0:
            eletben.clear()
        return sorted(eletben)

    db = update_folyamatok.varj_vagy_allitsd_le(
        tmp_path, sajat_pid=7, hatarido=5.0,
        lista=lista, leallit=lambda pid: pytest.fail("nem kellett leállítani"),
        alszik=ora.alszik, ora=ora,
    )

    assert db == 0


def test_a_csere_a_foglalt_mappat_ujraprobalva_vegzi_el(tmp_path, monkeypatch):
    app = tmp_path / "PicasaPy"
    app.mkdir()
    (app / "PicasaPy.exe").write_text("regi")
    stage = tmp_path / "stage"
    stage.mkdir()
    (stage / "PicasaPy.exe").write_text("uj")
    ora = _Ora()
    eredeti = update_folyamatok._rename
    probak = []

    def rename(forras, cel):
        probak.append(Path(forras).name)
        if len(probak) == 1:
            raise _foglalt()
        eredeti(forras, cel)

    monkeypatch.setattr(update_folyamatok, "_rename", rename)
    monkeypatch.setattr(update_folyamatok, "_alszik", ora.alszik)
    monkeypatch.setattr(update_folyamatok, "_ora", ora)

    assert swap_update_directory(stage, app, launch=lambda: True)
    assert (app / "PicasaPy.exe").read_text(encoding="utf-8") == "uj"
    assert probak[:2] == ["PicasaPy", "PicasaPy"]


def test_az_eredmeny_jelzo_kudarcnal_megmarad_es_egyszer_olvashato(tmp_path):
    jelzo = tmp_path / "frissites-eredmeny.json"
    update_eredmeny.ird(jelzo, siker=False, ok=update_eredmeny.FAJL_FOGLALT)

    assert json.loads(jelzo.read_text(encoding="utf-8"))["ok"] == "fajl-foglalt"
    assert update_eredmeny.olvasd_es_torold(jelzo) == "fajl-foglalt"
    assert not jelzo.exists()
    assert update_eredmeny.olvasd_es_torold(jelzo) == ""


def test_sikeres_frissites_utan_nincs_mit_kiirni(tmp_path):
    jelzo = tmp_path / "frissites-eredmeny.json"
    update_eredmeny.ird(jelzo, siker=True, ok="")

    assert update_eredmeny.olvasd_es_torold(jelzo) == ""
    assert not jelzo.exists()


def test_serult_jelzo_nem_dont_el_semmit(tmp_path):
    jelzo = tmp_path / "frissites-eredmeny.json"
    jelzo.write_text("{nem json", encoding="utf-8")

    assert update_eredmeny.olvasd_es_torold(jelzo) == update_eredmeny.EGYEB
    assert not jelzo.exists()


@pytest.mark.parametrize(
    ("hiba", "vart"),
    [
        (_foglalt(), "fajl-foglalt"),
        (PermissionError(13, "hozzáférés megtagadva"), "fajl-foglalt"),
        (ValueError("rossz zip"), "egyeb"),
    ],
)
def test_a_kivetel_okkoddá_alakul(hiba, vart):
    assert update_eredmeny.ok_kod(hiba) == vart


def test_a_seged_kudarcnal_okkodot_ir_a_jelzobe(tmp_path, monkeypatch):
    jelzo = tmp_path / "adat" / "frissites-eredmeny.json"
    monkeypatch.setattr(update_eredmeny, "jelzo_utvonal", lambda: jelzo)
    monkeypatch.setattr(update_swap_helper, "wait_for_process", lambda pid: None)
    monkeypatch.setattr(update_swap_helper, "_log_update", lambda *a, **k: None)
    monkeypatch.setattr(update_swap_helper, "inditsd_a_felhasznalonak", lambda *a, **k: None)
    monkeypatch.setattr(update_folyamatok, "varj_vagy_allitsd_le", lambda *a, **k: 0)
    monkeypatch.setattr(update_swap_helper, "extract_update_archive", lambda a, s: s)

    def foglalt_csere(*_a, **_k):
        raise _foglalt()

    monkeypatch.setattr(update_swap_helper, "swap_update_directory", foglalt_csere)
    app = tmp_path / "PicasaPy"
    app.mkdir()

    with pytest.raises(OSError):
        update_swap_helper.install_after_exit(1, tmp_path / "x.zip", app, "PicasaPy.exe")

    assert json.loads(jelzo.read_text(encoding="utf-8")) == {"siker": False, "ok": "fajl-foglalt"}


def test_a_vezerlo_induláskor_kiolvassa_az_elozo_kudarcot(qt_app, tmp_path, monkeypatch):
    from picasapy.app.update_manager import UpdateController

    jelzo = tmp_path / "frissites-eredmeny.json"
    update_eredmeny.ird(jelzo, siker=False, ok=update_eredmeny.FAJL_FOGLALT)
    monkeypatch.setattr(update_eredmeny, "jelzo_utvonal", lambda: jelzo)

    class _Beallitas(dict):
        def value(self, kulcs, alap=None):
            return self.get(kulcs, alap)

        def setValue(self, kulcs, ertek):  # noqa: N802
            self[kulcs] = ertek

        def remove(self, kulcs):
            self.pop(kulcs, None)

        def sync(self):
            pass

    vezerlo = UpdateController("1.0.26", settings=_Beallitas(), schedule=False)

    assert vezerlo.previousUpdateFailure == "fajl-foglalt"
    assert not jelzo.exists()


def test_a_frissitesi_ablak_a_munka_idejere_latszik_es_a_vegen_bezarul():
    naplo = []
    ablak = update_ablak.FrissitesiAblak(
        megjelenit=lambda kod, cim: naplo.append(("nyit", cim)) or "fogantyu",
        bezar=lambda cim, fogantyu: naplo.append(("zar", cim, fogantyu)),
        windows=True,
    )
    with ablak:
        pass

    assert naplo[0][0] == "nyit" and naplo[-1][0] == "zar"
    assert naplo[0][1] == naplo[-1][1] != "PicasaPy"
    assert naplo[-1][2] == "fogantyu", "a bezárás a megnyitott folyamatot kapja"


def test_a_frissitesi_ablak_kulon_folyamatban_fut_nem_szalon():
    """#988: nyers szál helyett a segéd önmagát indítja ablak-üzemmódban."""
    parancs = update_ablak.ablak_parancs("hu")
    assert parancs[-2:] == [update_ablak.ABLAK_KAPCSOLO, "hu"]


def test_a_seged_ablak_uzemmodban_csak_az_ablakot_mutatja(monkeypatch):
    hivas = []
    monkeypatch.setattr(update_ablak, "ablak_foprogram", lambda kod: hivas.append(kod) or 0)
    monkeypatch.setattr(update_swap_helper, "install_after_exit",
                        lambda *a, **k: hivas.append("telepites"))

    assert update_swap_helper.main([update_ablak.ABLAK_KAPCSOLO, "hu"]) == 0
    assert hivas == ["hu"]


def test_a_frissitesi_ablak_nem_windowson_semmit_nem_nyit(monkeypatch):
    monkeypatch.setattr(update_ablak, "_platform", lambda: "linux")
    naplo = []
    with update_ablak.FrissitesiAblak(megjelenit=lambda *a: naplo.append(a),
                                      bezar=lambda *a: naplo.append(a)):
        pass
    assert naplo == []


def test_a_frissitesi_ablak_szovege_magyar_windowson_magyar():
    assert "frissül" in update_ablak.szoveg(0x040E)
    assert "being updated" in update_ablak.szoveg(0x0409)


def test_a_seged_a_teljes_munkat_az_ablakban_vegzi(tmp_path, monkeypatch):
    sorrend = []

    class _Ablak:
        def __enter__(self):
            sorrend.append("nyit")
            return self

        def __exit__(self, *_a):
            sorrend.append("zar")

    monkeypatch.setattr(update_ablak, "FrissitesiAblak", _Ablak)
    monkeypatch.setattr(update_swap_helper, "_telepites",
                        lambda *a, **k: sorrend.append("munka") or True)

    assert update_swap_helper.install_after_exit(1, tmp_path / "x.zip", tmp_path, "P.exe")
    assert sorrend == ["nyit", "munka", "zar"]


_CSAK_WINDOWS = pytest.mark.skipif(
    __import__("sys").platform != "win32", reason="valódi Windows-fájlzár és folyamatkezelés"
)


@_CSAK_WINDOWS
def test_windowson_a_valoban_foglalt_mappa_atnevezese_kivarja_a_zar_veget(tmp_path):
    import subprocess
    import sys
    import time

    mappa = tmp_path / "PicasaPy"
    mappa.mkdir()
    fajl = mappa / "zarolt.dll"
    fajl.write_bytes(b"x")
    # a gyermekfolyamat 3 s-ig nyitva tartja a fájlt (mint egy víruskereső)
    tarto = subprocess.Popen(
        [sys.executable, "-c",
         f"import time; f=open(r'{fajl}','rb'); print('nyitva', flush=True); time.sleep(3)"],
        stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
    )
    assert tarto.stdout.readline().strip() == "nyitva"
    kezdet = time.monotonic()

    update_folyamatok.atnevez_ujraprobalva(mappa, tmp_path / "PicasaPy.previous", hatarido=30.0)

    assert (tmp_path / "PicasaPy.previous" / "zarolt.dll").exists()
    assert time.monotonic() - kezdet >= 1.0
    tarto.wait(timeout=10)


@_CSAK_WINDOWS
def test_windowson_a_telepitesi_mappabol_futo_folyamatot_megtalalja_es_leallitja(tmp_path):
    import shutil
    import subprocess
    import sys

    mappa = tmp_path / "PicasaPy"
    mappa.mkdir()
    masolat = mappa / "PicasaPy.exe"
    shutil.copy2(sys.executable, masolat)
    for dll in Path(sys.executable).parent.glob("*.dll"):
        shutil.copy2(dll, mappa / dll.name)
    import os

    # a másolt értelmező a saját könyvtárát az eredeti helyről kapja
    regi = subprocess.Popen(
        [str(masolat), "-c", "import time; time.sleep(120)"],
        env={**os.environ, "PYTHONHOME": sys.base_prefix},
    )
    try:
        assert regi.pid in update_folyamatok.telepitesi_folyamatok(mappa, sajat_pid=0)

        db = update_folyamatok.varj_vagy_allitsd_le(mappa, hatarido=1.0)

        assert db == 1
        assert regi.wait(timeout=10) is not None
    finally:
        if regi.poll() is None:
            regi.kill()
