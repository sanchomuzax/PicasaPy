"""#7355: a frissítő ablak csíkja az első pillanattól a teljes telepítést mutatja.

A tulajdonos jelzése: a kicsomagolás alatt nem volt százalék, a csík csak a
`qml_cache` szakaszban jelent meg. A teljes százalék a szakaszok sávjaiból és
a szakaszon belüli kész/összes arányból áll össze, és soha nem lép vissza.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from picasapy.app import update_ablak
from picasapy.app.update_swap_helper import extract_update_archive


def _allapot(stage: str, **tobbi: object) -> dict[str, object]:
    return {"stage": stage, "error": "", "done": False, **tobbi}


def test_a_sulyok_osszege_100_es_minden_szakasznak_van_sava():
    sulyok = update_ablak.SZAKASZ_SULYOK
    assert sum(sulyok.values()) == 100
    for kulcs in update_ablak._LEPESEK["en"]:
        assert kulcs in sulyok, f"a(z) {kulcs} szakasznak nincs sávja"


def test_az_elejen_nulla_es_a_kicsomagolas_alatt_no():
    assert update_ablak.teljes_szazalek(_allapot("varakozas")) == 0
    eleje = update_ablak.teljes_szazalek(
        _allapot("kicsomagolas", extract_done=0, extract_total=200)
    )
    fele = update_ablak.teljes_szazalek(
        _allapot("kicsomagolas", extract_done=100, extract_total=200)
    )
    vege = update_ablak.teljes_szazalek(
        _allapot("kicsomagolas", extract_done=200, extract_total=200)
    )
    assert eleje < fele < vege, (eleje, fele, vege)


def test_a_teljes_sorozat_monoton_es_100_on_vegzodik():
    sorozat = [
        _allapot("varakozas"),
        _allapot("kicsomagolas", extract_done=0, extract_total=10),
        _allapot("kicsomagolas", extract_done=5, extract_total=10),
        _allapot("kicsomagolas", extract_done=10, extract_total=10),
        _allapot("maradek_folyamatok"),
        _allapot("csere"),
        _allapot("onellenorzes"),
        _allapot("qml_cache", qml_done=0, qml_total=358),
        _allapot("qml_cache", qml_done=44, qml_total=358),
        _allapot("qml_cache", qml_done=358, qml_total=358),
        _allapot("qml_grafika"),
        _allapot("inditas"),
        _allapot("ablak_varakozas"),
        {"stage": "ablak_varakozas", "error": "", "done": True},
    ]
    ertekek = [update_ablak.teljes_szazalek(a) for a in sorozat]
    assert ertekek == sorted(ertekek), ertekek
    assert ertekek[0] == 0
    assert ertekek[-1] == 100


def test_a_qml_cache_a_sajat_savjan_belul_aranyosan_halad():
    sulyok = update_ablak.SZAKASZ_SULYOK
    kulcsok = list(sulyok)
    kezdet = sum(sulyok[k] for k in kulcsok[: kulcsok.index("qml_cache")])
    fele = update_ablak.teljes_szazalek(
        _allapot("qml_cache", qml_done=179, qml_total=358)
    )
    assert fele == kezdet + sulyok["qml_cache"] // 2


def test_ismeretlen_vagy_hibas_adatnal_sem_omlik_ossze():
    assert update_ablak.teljes_szazalek({}) == 0
    assert update_ablak.teljes_szazalek(_allapot("ismeretlen")) == 0
    assert 0 <= update_ablak.teljes_szazalek(
        _allapot("kicsomagolas", extract_done="x", extract_total=True)
    ) <= 100


def test_a_kicsomagolas_jelenti_az_elorehaladast(tmp_path: Path):
    archiv = tmp_path / "frissites.zip"
    with zipfile.ZipFile(archiv, "w") as zf:
        zf.writestr("PicasaPy/PicasaPy.exe", b"exe")
        for i in range(6):
            zf.writestr(f"PicasaPy/lib/f{i}.txt", b"x")
    jelentesek: list[tuple[int, int]] = []
    extract_update_archive(
        archiv, tmp_path / "stage", haladas=lambda k, o: jelentesek.append((k, o))
    )
    assert jelentesek, "a kicsomagolás nem jelentett előrehaladást"
    assert jelentesek[-1][0] == jelentesek[-1][1] == 7
    kesz = [k for k, _ in jelentesek]
    assert kesz == sorted(kesz)


def test_az_ablak_allapotfajlja_a_kicsomagolas_szamait_hordozza(
    tmp_path: Path, monkeypatch
):
    status = tmp_path / "statusz.json"
    monkeypatch.setattr(update_ablak, "_status_utvonal", lambda: status)
    monkeypatch.setattr(update_ablak, "nyelv", lambda nyelvkod=None: "hu")
    with update_ablak.FrissitesiAblak(
        megjelenit=lambda _kod, _cim: object(), bezar=lambda *_: None, windows=True
    ) as ablak:
        ablak.lepes("kicsomagolas")
        ablak.kicsomagolas_halad(3, 12, kenyszer=True)
        adat = json.loads(status.read_text(encoding="utf-8"))
        assert adat["stage"] == "kicsomagolas"
        assert (adat["extract_done"], adat["extract_total"]) == (3, 12)
        assert update_ablak.teljes_szazalek(adat) > 0
        ablak.lepes("csere")
        adat = json.loads(status.read_text(encoding="utf-8"))
        assert "extract_done" not in adat


def test_a_csik_felirata_szazalek_es_ahol_van_darabszam():
    assert update_ablak.csik_felirat(
        _allapot("qml_cache", qml_done=44, qml_total=358), 37
    ) == "37% · 44/358"
    assert update_ablak.csik_felirat(
        _allapot("kicsomagolas", extract_done=3, extract_total=12), 10
    ) == "10% · 3/12"
    assert update_ablak.csik_felirat(_allapot("csere"), 50) == "50%"
