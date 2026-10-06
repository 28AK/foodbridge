from app.services.notify import normalize_phone


def test_normalize_indian_numbers():
    assert normalize_phone("9876543210") == "+919876543210"
    assert normalize_phone("09876543210") == "+919876543210"
    assert normalize_phone("+91 98765 43210") == "+919876543210"
    assert normalize_phone("919876543210") == "+919876543210"


def test_keeps_international_numbers():
    assert normalize_phone("+1 (415) 555-0100") == "+14155550100"


def test_rejects_invalid():
    assert normalize_phone("") is None
    assert normalize_phone(None) is None
    assert normalize_phone("12345") is None
