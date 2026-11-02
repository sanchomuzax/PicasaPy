"""A telepítő és a CI minden mérés előtt előállítja a QML-cache-t (#6374)."""

from pathlib import Path


_GYOKER = Path(__file__).resolve().parents[1]


def test_a_telepito_rejtve_varva_es_eredeti_felhasznalokent_fordit():
    tartalom = (_GYOKER / "packaging/windows/picasapy.iss").read_text(
        encoding="utf-8"
    )
    fordits_sor = next(
        sor
        for sor in tartalom.splitlines()
        if 'Parameters: "--qml-elofordit"' in sor
    )
    assert "runhidden waituntilterminated runasoriginaluser" in fordits_sor
    assert tartalom.index(fordits_sor) < tartalom.index("Flags: nowait postinstall skipifsilent")
    assert "Parameters: \"--qml-elofordit\"" in fordits_sor


def test_a_package_meres_minden_indulashoz_ot_masodperces_hatart_hasznal():
    workflow = (_GYOKER / ".github/workflows/package.yml").read_text(
        encoding="utf-8"
    )
    assert "--elso-hatar-mp" not in workflow
    assert workflow.count("--hatar-mp 5") >= 2


def test_a_meroszkript_elomelegiti_a_profilt_es_mer_frissites_utan():
    meres = (_GYOKER / "packaging/windows/csomag_meres.py").read_text(
        encoding="utf-8"
    )
    helper = (_GYOKER / "src/picasapy/app/qml_cache_warmup.py").read_text(
        encoding="utf-8"
    )
    assert "melegitsd_qml_cache" in meres
    assert "frissitesi_indulasi_kapu" in meres
    assert "--qml-elofordit" in helper
    assert "QML betöltése (Main.qml)" in helper
    assert "A főablak a splash után megjelent" in helper
    assert "hatar_mp: float = 5.0" in helper
