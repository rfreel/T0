import pytest

from identifiers.normalize import normalize_identifier


def test_nfkc_compatibility_normalization():
    assert normalize_identifier("  ＡＢＣ-１２  ") == "abc-12"


def test_rejects_zero_width_format_character():
    with pytest.raises(ValueError):
        normalize_identifier("admin\u200b")


def test_rejects_ascii_control_character():
    with pytest.raises(ValueError):
        normalize_identifier("abc\x00def")
