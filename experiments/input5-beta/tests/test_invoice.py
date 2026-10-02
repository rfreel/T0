from identifiers.invoice import parse_invoice


def test_invoice_identifier():
    assert parse_invoice("  INV-XyZ-2  ") == "inv-xyz-2"
