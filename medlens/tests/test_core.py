from backend.app.main import classify


def test_reference_ranges():
    assert classify(10, 12, 16) == "LOW"
    assert classify(14, 12, 16) == "NORMAL"
    assert classify(20, 12, 16) == "HIGH"


def test_missing_range_is_not_assessed():
    assert classify(20, None, None) == "NOT_ASSESSED"
    assert classify(None, 12, 16) == "NOT_ASSESSED"


def test_one_sided_ranges_are_supported():
    assert classify(8, float("-inf"), 10) == "NORMAL"
    assert classify(12, float("-inf"), 10) == "HIGH"
    assert classify(50, 40, float("inf")) == "NORMAL"
    assert classify(30, 40, float("inf")) == "LOW"
