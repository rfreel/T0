from identifiers.user import parse_user


def test_user_identifier():
    assert parse_user("  Alice@EXAMPLE.COM  ") == "alice@example.com"
