"""#2077: az őrök a SAJÁT kiírásukon ne bukjanak el Windowson.

## A mérés

`ci.yml` **33693910159**, windows 1/4:

```
File "scripts\\cv2_utvonal_or.py", line 77, in main
    print("\\u2705 nincs fájlútvonalas cv2.imread/imwrite a forrásban")
UnicodeEncodeError: 'charmap' codec can't encode character '\\u2705'
```

A Windows-konzol alapértelmezett kódolása `cp1252`; a `✅` abban nem
ábrázolható. Az őr tehát **nem a leletre**, hanem a saját sikerüzenetére
hasalt el — és a hívó tesztje ezt valódi leletnek látta.

⚠️ Ez a hibaosztály **minden** olyan szkriptet érint, ami emojit ír ki.
Ez a fájl a CI-be bekötött őröket méri.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

GYOKER = Path(__file__).resolve().parents[1]

#: A CI-be bekötött, emojit író őrök.
OROK = ("cv2_utvonal_or.py", "posix_or.py")


@pytest.mark.parametrize("nev", OROK)
def test_az_or_CP1252_kimeneten_sem_bukik_el(nev):
    """Kikényszerített `cp1252` kimenettel is le kell futnia.

    A `PYTHONIOENCODING` ugyanazt a szűk kódolást állítja be, ami a
    windowsos runneren alapértelmezés — így a hiba Linuxon is előjön.

    Fog: `reconfigure` nélkül az őr `UnicodeEncodeError`-ral áll meg, és
    a kilépőkódja 1 lesz, holott a forrás tiszta.
    """
    kornyezet = dict(os.environ, PYTHONIOENCODING="cp1252")
    eredmeny = subprocess.run(
        [sys.executable, str(GYOKER / "scripts" / nev)],
        cwd=GYOKER,
        capture_output=True,
        text=True,
        errors="replace",
        env=kornyezet,
    )
    assert "UnicodeEncodeError" not in (eredmeny.stderr or ""), (
        f"{nev}: a SAJÁT kiírásán hasalt el cp1252 kimeneten:\n{eredmeny.stderr}"
    )
    assert eredmeny.returncode == 0, (
        f"{nev}: nem nulla kilépőkód cp1252 kimeneten\n{eredmeny.stderr}"
    )
