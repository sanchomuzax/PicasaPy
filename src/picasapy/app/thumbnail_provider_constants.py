"""A bélyegkép-szolgáltató megosztott korlátai és prioritásai."""

# #151/7: az edit-előnézet provider is ezt importálja, így a placeholder
# színe egyetlen helyen van definiálva.
PLACEHOLDER_COLOR = 0xFFE8E8E8

# A 4 mag a mért optimum (~3× gyorsulás RPi5-ön); több szál nem segít.
_MAX_RENDER_THREADS = 4

# Az értelmezett filters-láncok cache-korlátja; túlcsordulásnál ürítünk.
_OPS_CACHE_CAPACITY = 4096

# Bájtkeret: a tényleges QImage-méreteket számolja, így a DPR és a
# változó bélyegképméret nem növelheti korlátlanul a memóriatárat.
_FILTERED_MEMO_CAPACITY = 16 * 1024 * 1024

# A látható Image-kérések előzik meg a háttér-előtöltéseket.
_VISIBLE_THUMB_PRIORITY = 1
_PREFETCH_THUMB_PRIORITY = -1
_PREFETCH_QUEUE_CAPACITY = 256
