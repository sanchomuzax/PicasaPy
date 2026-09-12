"""A valódi mappa-figyelő BIZTONSÁGOS leállítása tesztekből (#1457).

A `controller.start()`-ot hívó tesztek a valódi `LibraryWatcher`-t
indítják el, és a legtöbbjük így állította le:

```python
ctl._watcher.stop()
ctl._watcher = None          # ⛔ akkor is, ha a szál MÉG FUT
```

A `stop()` `join(timeout=5)`-öt hív. Ha az időtúllépéssel tér vissza, a
megfigyelő szála tovább fut — a referencia eldobásával viszont a figyelő
(és rajta át a vezérlő) felszabadulhat alóla. A CI jel nélküli
összeomlásainak (#1457) TÖBBSÉGE ilyen fájlokból jön: a 40 CI-futás
naplójából kigyűjtött **13** összeomlásból **10** a `start()`-ot hívó
tizenhárom fájl valamelyikéből (a `tests/app` több mint 200 fájlja
közül). A maradék három MÁS fájlból jött (`test_csillag_lanc_1438`,
`test_naplo_lefedettseg_750`), tehát a `start()` nem az egyetlen út.

⚠️ Ez a mechanizmus, nem bizonyított diagnózis — a bizonyítékot a
következő összeomlás veremképe adja (a futtató most kiírja). A néma
eldobás viszont attól függetlenül hiba.
"""

from __future__ import annotations

import time


#: #3059: mennyit várunk a megfigyelő szál kifutására a `stop()` UTÁN.
#: A `stop()` maga `join(timeout=5)`-öt hív; ez a ráhagyás arra kell,
#: amikor a szál épp egy hosszabb fájlrendszer-hívásban áll.
_VARAKOZAS_S = 5.0


def allitsd_le_a_figyelot(controller) -> None:
    """A vezérlő figyelőjének leállítása; a referenciát csak akkor engedi
    el, ha a megfigyelő szála tényleg megállt.

    #3059: a `stop()` után MEGVÁRJUK a szálat, nem csak megkérdezzük
    egyszer. A windowsos CI-n a `test_projekt_mappa_figyeles_1123.py`
    `0xC0000409` fast-faillel omlott össze (kétszer, egymás után): a
    megfigyelő szál a lebontás közben is futott. Ha a szál a várakozás
    után SEM állt meg, a referencia marad — a néma eldobás volna a
    rosszabb, mert akkor a figyelő a vezérlővel együtt szabadulna fel a
    szál alól."""
    figyelo = getattr(controller, "_watcher", None)
    if figyelo is None:
        return
    figyelo.stop()
    hatarido = time.monotonic() + _VARAKOZAS_S
    while not figyelo.leallt() and time.monotonic() < hatarido:
        time.sleep(0.02)
    if figyelo.leallt():
        controller._watcher = None
