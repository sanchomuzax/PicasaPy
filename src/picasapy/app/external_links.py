"""A program külső hivatkozásai: honlap, adatvédelem, feltételek (#6402).

Egy helyen élnek. A QML az `appLinks` kontextus-tulajdonságon át éri el
(ld. application_startup_qml.py), a kulcsok: `website`, `privacy`, `terms`.
"""

from __future__ import annotations

WEBSITE_URL = "https://sancho.hu/picasapy/"
PRIVACY_POLICY_URL = "https://sancho.hu/picasapy/policy.html"
TERMS_URL = "https://sancho.hu/picasapy/terms.html"

EXTERNAL_LINKS: dict[str, str] = {
    "website": WEBSITE_URL,
    "privacy": PRIVACY_POLICY_URL,
    "terms": TERMS_URL,
}
