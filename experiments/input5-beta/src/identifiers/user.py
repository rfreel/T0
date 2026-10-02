from .normalize import normalize_identifier


def parse_user(raw: str) -> str:
    return normalize_identifier(raw)
