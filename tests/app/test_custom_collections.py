

class TestCollectionNameValidation:
    """#461: az eredeti Picasa KÉT hibát különböztet meg — érvénytelen név
    és már létező név —, ezért a réteg is kettőt ad vissza."""

    def test_empty_name_is_invalid(self):
        from picasapy.app.custom_collections import (
            NAME_INVALID,
            validate_collection_name,
        )

        assert validate_collection_name((), "") == NAME_INVALID
        assert validate_collection_name((), "   ") == NAME_INVALID

    def test_existing_name_is_a_duplicate_case_insensitively(self):
        from picasapy.app.custom_collections import (
            NAME_DUPLICATE,
            CustomCollection,
            validate_collection_name,
        )

        existing = (CustomCollection(name="Nyaralás"),)
        assert validate_collection_name(existing, "nyaralás") == NAME_DUPLICATE

    def test_renaming_to_the_same_name_is_allowed(self):
        """Átnevezéskor a SAJÁT (változatlan) név nem ütközés."""
        from picasapy.app.custom_collections import (
            NAME_OK,
            CustomCollection,
            validate_collection_name,
        )

        existing = (CustomCollection(name="Nyaralás"),)
        assert (
            validate_collection_name(
                existing, "Nyaralás", existing_name="Nyaralás"
            )
            == NAME_OK
        )

    def test_a_fresh_name_is_accepted(self):
        from picasapy.app.custom_collections import (
            NAME_OK,
            CustomCollection,
            validate_collection_name,
        )

        existing = (CustomCollection(name="Nyaralás"),)
        assert validate_collection_name(existing, "Tél") == NAME_OK
