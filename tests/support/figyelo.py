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


def allitsd_le_a_figyelot(controller) -> None:
    """A vezérlő figyelőjének leállítása; a referenciát csak akkor engedi
    el, ha a megfigyelő szála tényleg megállt."""
    figyelo = getattr(controller, "_watcher", None)
    if figyelo is None:
        return
    figyelo.stop()
    if figyelo.leallt():
        controller._watcher = None
