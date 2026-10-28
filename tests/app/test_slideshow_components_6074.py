"""A #6074-es diavetítés-QML részei maradjanak az áttekinthető méret alatt."""

from pathlib import Path


_QML = Path(__file__).parents[2] / "src/picasapy/app/qml/PicasaPy"
_RESZEK = (
    "SlideshowView.qml",
    "SlideshowImageLayer.qml",
    "SlideshowControls.qml",
    "SlideshowTiming.qml",
    "SlideshowCurrentImage.qml",
    "SlideshowPreviousImage.qml",
    "SlideshowVeil.qml",
    "SlideshowPreloadImage.qml",
)


def test_minden_diavetitesi_resz_800_sor_alatt_marad():
    hosszak = {
        nev: len((_QML / nev).read_text(encoding="utf-8").splitlines())
        for nev in _RESZEK
        if (_QML / nev).is_file()
    }
    hianyzo = sorted(set(_RESZEK) - set(hosszak))
    assert not hianyzo and all(sorok <= 800 for sorok in hosszak.values()), (
        f"hiányzó részek: {hianyzo}; sorok: {hosszak}"
    )


def test_a_belso_diavetitesi_reszek_a_qml_modulban_regisztralva_vannak():
    qmldir = (_QML / "qmldir").read_text(encoding="utf-8")
    for tipus, fajl in (
        ("SlideshowImageLayer", "SlideshowImageLayer.qml"),
        ("SlideshowControls", "SlideshowControls.qml"),
        ("SlideshowTiming", "SlideshowTiming.qml"),
        ("SlideshowCurrentImage", "SlideshowCurrentImage.qml"),
        ("SlideshowPreviousImage", "SlideshowPreviousImage.qml"),
        ("SlideshowVeil", "SlideshowVeil.qml"),
        ("SlideshowPreloadImage", "SlideshowPreloadImage.qml"),
    ):
        assert f"internal {tipus} {fajl}" in qmldir
