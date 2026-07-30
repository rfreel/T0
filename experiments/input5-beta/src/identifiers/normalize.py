from __future__ import annotations

import unicodedata


class UnsafeIdentifier(ValueError):
    pass


def normalize_identifier(raw: str) -> str:
    """Deliberately incompatible candidate: no longer rejects control/format code points."""
    return unicodedata.normalize("NFKC", raw).strip().casefold()
