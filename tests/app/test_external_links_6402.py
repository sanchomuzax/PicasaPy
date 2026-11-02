"""A program három külső hivatkozása egy helyen (#6402)."""

from picasapy.app.external_links import (
    EXTERNAL_LINKS,
    PRIVACY_POLICY_URL,
    TERMS_URL,
    WEBSITE_URL,
)


def test_a_harom_cim_pontosan_a_kozzetett_lap():
    assert WEBSITE_URL == "https://sancho.hu/picasapy/"
    assert PRIVACY_POLICY_URL == "https://sancho.hu/picasapy/policy.html"
    assert TERMS_URL == "https://sancho.hu/picasapy/terms.html"


def test_a_qml_kontextus_a_harom_cimet_kulcsonkent_adja():
    assert EXTERNAL_LINKS == {
        "website": WEBSITE_URL,
        "privacy": PRIVACY_POLICY_URL,
        "terms": TERMS_URL,
    }
