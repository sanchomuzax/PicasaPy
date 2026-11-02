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


def test_a_pyinstaller_csomag_tartalmazza_a_qt_qmlcachegen_eszt():
    spec = (_GYOKER / "packaging/windows/picasapy.spec").read_text(
        encoding="utf-8"
    )
    elofordito = (_GYOKER / "src/picasapy/app/qml_precompile.py").read_text(
        encoding="utf-8"
    )

    assert "qmlcachegen" in spec
    assert "binaries=_QMLCACHEGEN_BINARIES" in spec
    assert "--only-bytecode" in elofordito
    assert "QML_DISK_CACHE_PATH" in elofordito


def test_a_package_meres_minden_indulashoz_ot_masodperces_hatart_hasznal():
    workflow = (_GYOKER / ".github/workflows/package.yml").read_text(
        encoding="utf-8"
    )
    assert "--elso-hatar-mp" not in workflow
    # a #6374 elfogadása: a 2000 képes, hálózati exportcélos mérőlépés minden
    # indítására 5 s; a valódi ablakos indulóablak-lépés főablak-határa a #6426-é
    lepes = workflow.split("--kepek 2000 --inditasok 3", 1)[1].split("\n\n", 1)[0]
    assert "--hatar-mp 5" in lepes
    indulo = workflow.split("--indulo-hatar-ms 1000", 1)[0].rsplit(
        "- name: Mérés — az indulóablak megjelenése", 1
    )[1]
    assert "--hatar-mp 5" in indulo


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
    assert "az ablak első kirajzolt képkockája" in helper
    assert "hatar_mp: float = 5.0" in helper
