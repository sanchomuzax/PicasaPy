"""Közös, külön fájlban tartott alkalmazásindító-állandók."""

# #240 óta a főablakon belüli nyitókép legalább 1500 ms-ig látszott, hogy
# gyors betöltésnél is észrevehető legyen. A #6367 óta a külön indulóablak a
# 0. pillanattól látszik (mint az eredeti Picasában, docs/specs/picasa-indulas.md
# 6. fejezet), így a mesterséges várakozás csak az indulást lassította
# (a windowsos CI-on mérve 0,5-1 s). Az eredeti Picasa nem ír elő ilyet.
_SPLASH_MIN_VISIBLE_MS = 0
