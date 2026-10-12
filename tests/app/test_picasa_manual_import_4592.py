"""#4592: a db3 kézzel megadott Picasa2 mappából és útvonal-leképezéssel is importálható."""

from pathlib import Path

from picasapy.app.picasa_import_controller import PicasaImportController
from picasapy.pmpimport.db3_atvetel import AtvetelJelentes


def test_kezzel_megadott_picasa2_mappat_es_meghajto_lekepezest_hasznal(qt_app, tmp_path):
    db3 = tmp_path / "Picasa2"
    db3.mkdir()
    cel = tmp_path / "kepek"
    cel.mkdir()
    felderitesek = []
    olvasasi_hivasok = []

    def felderito():
        felderitesek.append(True)
        return ()

    def olvaso(konyvtar, remapper):
        olvasasi_hivasok.append((Path(konyvtar), remapper.remap(r"D:\Fotok\kep.jpg")))
        return ("rekord",)

    controller = PicasaImportController(
        felderito=felderito,
        olvaso=olvaso,
        atvevo=lambda _rekordok: AtvetelJelentes(mappak=1, kulcsszo=1),
    )
    kesz = []
    controller.importFinished.connect(lambda *args: kesz.append(args))

    controller.startManualImport(str(db3), r"D:\Fotok", str(cel))
    assert controller.waitForBackgroundWorkers(5.0)
    qt_app.processEvents()

    assert not felderitesek, "a kézi mappa helyett automatikus telepítésfelderítés indult"
    assert olvasasi_hivasok == [(db3, str(cel / "kep.jpg"))]
    assert kesz == [(1, 1, 0, 0, 0)]
