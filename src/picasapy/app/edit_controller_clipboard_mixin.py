"""Az EditController vágólap-mixinje: a megjelenített kép a vágólapra (#7030).

## A lelet a binárisból

Az eredeti Picasa 3.9 a szerkesztőben (egyképes nézetben) a Másolás
paranccsal a szerkesztésekkel együtt kiszámolt képet teszi a vágólapra,
valódi képadatként: a `0x00a706f0` a `0x00a70776`-nál `push 2`
(`CF_BITMAP`) után hívja a `SetClipboardData`-t (hívó: `0x0069b000`, ld.
`docs/specs/paritas-ellenorzes.md`, #7028). A kép így más programba
közvetlenül képként illeszthető be.

A rácsbeli Másolás ettől független: az továbbra is fájlokat tesz fel
(`FileOpsController.copyFilesToClipboard`, #1526).
"""

from __future__ import annotations

from PySide6.QtCore import Slot
from PySide6.QtGui import QGuiApplication, QImage

#: Fej nélküli Qt-platformok: nincs mögöttük vágólap-tulajdonos, és a
#: rendszervágólapra írás CI-n szegmenshibát okozott (ld. a
#: `fileops_controller_clipboard_mixin` magyarázatát).
_FEJ_NELKULI_PLATFORMOK = ("offscreen", "minimal")


class EditControllerClipboardMixin:
    #: A legutóbb a vágólapra szánt kép. Fej nélküli környezetben ez az
    #: egyetlen hely, ahonnan a próba visszaolvassa, mit tennénk fel.
    _vagolap_kep: QImage | None = None

    @Slot(str, result=bool)
    def copyRenderedImageToClipboard(self, photo_id: str) -> bool:  # noqa: N802
        """A néző MEGJELENÍTETT képe a vágólapra, képadatként (#7030).

        A kép a szolgáltató tárolt, szerkesztésekkel renderelt előnézete
        (`EditPreviewProvider.rendered_image`), tehát ugyanaz, amit a néző
        mutat; külön számítás nincs.

        `photo_id`: annak a fotónak az azonosítója, amelyiket a hívó másolni
        akar. Ha a munkamenet közben másik fotóra állt (vagy nincs
        munkamenet), a kérés elavult, és a rossz fotó képét nem visszük át.

        Visszatérés: felkerült-e a kép. `False` esetén a vágólap és a
        korábban feltett kép érintetlen: a hívó ilyenkor a fájl-vágólapra
        eshet vissza, nem marad néma hatástalanság."""
        if not photo_id or photo_id != self._photo_id:
            return False
        kep = self._provider.rendered_image(self._kulcs)
        if kep is None:
            return False
        self._vagolap_kep = kep
        if QGuiApplication.platformName() in _FEJ_NELKULI_PLATFORMOK:
            return True
        vagolap = QGuiApplication.clipboard()
        if vagolap is not None:
            vagolap.setImage(kep)
        return True

    def _vagolap_kepe(self) -> QImage | None:
        """A vágólap képe - a próbák EZT a metódust olvassák.

        Fej nélküli környezetben a legutóbb feltett saját képet adjuk
        vissza (a Qt-rendszervágólaphoz ott nem nyúlunk), egyébként a
        rendszervágólap képét."""
        if QGuiApplication.platformName() in _FEJ_NELKULI_PLATFORMOK:
            return self._vagolap_kep
        vagolap = QGuiApplication.clipboard()
        return None if vagolap is None else vagolap.image()
