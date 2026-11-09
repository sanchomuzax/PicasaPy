"""A NumPy tényleges importját az első attribútum-használatig halasztja (#6688)."""

from __future__ import annotations

from picasapy.lazy_import import lazy_module

np = lazy_module("numpy")

__all__ = ["np"]
