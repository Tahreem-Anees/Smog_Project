import sys
from pathlib import Path

# Let the tests find src/validate.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validate import validate_rows


def make_row(**overrides):
    """One good hourly row. Tests change only the field they want to break."""
    row = {
        "city": "Lahore",
        "time": "2024-01-15T10:00",
        "pm2_5": 120.5,
        "temperature": 18.0,
        "humidity": 65.0,
        "wind_speed": 12.0,
        "pressure": 1015.0,
    }
    row.update(overrides)
    return row


def test_valid_row_passes():
    valid, invalid = validate_rows([make_row()])
    assert len(valid) == 1
    assert len(invalid) == 0
    assert valid[0]["city"] == "Lahore"


def test_missing_optional_values_are_allowed():
    row = make_row(pm2_5=None, temperature=None, humidity=None)
    valid, invalid = validate_rows([row])
    assert len(valid) == 1
    assert len(invalid) == 0


def test_negative_pm25_is_rejected():
    valid, invalid = validate_rows([make_row(pm2_5=-5)])
    assert len(valid) == 0
    assert len(invalid) == 1
    assert "pm2_5" in invalid[0]["error"]


def test_humidity_above_100_is_rejected():
    valid, invalid = validate_rows([make_row(humidity=150)])
    assert len(valid) == 0
    assert len(invalid) == 1


def test_missing_city_is_rejected():
    row = make_row()
    del row["city"]
    valid, invalid = validate_rows([row])
    assert len(valid) == 0
    assert len(invalid) == 1


def test_mixed_rows_are_split_correctly():
    rows = [make_row(), make_row(pressure=500), make_row(temperature=99)]
    valid, invalid = validate_rows(rows)
    assert len(valid) == 1
    assert len(invalid) == 2