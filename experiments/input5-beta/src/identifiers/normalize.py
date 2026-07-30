from __future__ import annotations

import unicodedata


class UnsafeIdentifier(ValueError):
    pass


def normalize_identifier(raw: str) -> str:
    normalized = unicodedata.normalize("NFKC", raw).strip().casefold()
    unsafe = [
        ch for ch in normalized
        if unicodedata.category(ch).startswith("C")
    ]
    if unsafe:
        codepoints = ", ".join(f"U+{ord(ch):04X}" for ch in unsafe)
        raise UnsafeIdentifier(
            "identifier contains control or format characters: " + codepoints
        )
    return normalized
