from .normalize import normalize_identifier


def parse_order(raw: str) -> str:
    return normalize_identifier(raw)
