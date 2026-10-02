from .normalize import normalize_identifier


def parse_invoice(raw: str) -> str:
    return normalize_identifier(raw)
