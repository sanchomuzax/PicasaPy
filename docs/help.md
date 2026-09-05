# A felhasználói súgó — a `src/picasapy/help/` alatt

A PicasaPy felhasználói kézikönyve **nem itt**, hanem a
[`src/picasapy/help/`](../src/picasapy/help/index.md) mappában él.

## Miért a csomagfa alatt

A súgónak **net nélkül**, a telepített programból is elérhetőnek kell
lennie (#2054). A telepíthető csomagba viszont kizárólag a
`src/picasapy` fa alól kerül be bármi:

- `MANIFEST.in` — `graft src/picasapy`
- `pyproject.toml` — `[tool.setuptools.packages.find] where = ["src"]`

A `docs/` alatt hagyva a súgó **git-másolatból működne, telepített
csomagból nem** — és ez némán, csak a felhasználónál derülne ki. Ez a
hibaosztály a projektben már egyszer 40 fájlt vitt el észrevétlenül
(#646): forrásból minden működött, ezért hónapokig nem tűnt fel.

A `graft` miatt a `src/picasapy/help/` **magától** bekerül a csomagba, és
a `tests/test_package_contents.py` őre azonnal jelez, ha kiesne.

## Ki írja

A napi automatikus frissítő (#2051, `eszkozok/sugo/update_help.sh` a
privát `picasapy-agent` repóban) ide ír.
