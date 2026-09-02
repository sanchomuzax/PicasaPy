"""A `tests/export/` CSOMAG — a modulnév-ütközés elkerülésére (#1968).

A `tests/app/qml_functional/` alatt is van `test_export_mukodes_1166.py`
(az exportálás FELÜLETI viselkedése; itt a mag ini-átvitele és a
célmappa-ütközés). `__init__.py` nélkül a pytest mindkettőre ugyanazt a
modulnevet képezné (`test_export_mukodes_1166`), és az EGYÜTTES gyűjtés
elszállna — a fájlonkénti futtatás viszont elfedi, ezért hónapokig
észrevétlen maradt.

Ez a projekt saját, már bevált mintája: a `tests/render/` ugyanígy csomag,
és ezért fér meg a `tests/ini/` azonos alapnevű `test_retouch.py`-jával.

Az őr: `tests/tools/test_teszt_modulnev_utkozes_1968.py`.
"""
