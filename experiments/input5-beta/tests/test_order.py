from identifiers.order import parse_order


def test_order_identifier():
    assert parse_order("  ORD-AbC-9  ") == "ord-abc-9"
