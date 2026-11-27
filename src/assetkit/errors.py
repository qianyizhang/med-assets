"""Shared exception and domain constants for AssetKit."""

from __future__ import annotations


class AssetKitError(ValueError):
    """Raised when catalog data violates domain or storage invariants."""
