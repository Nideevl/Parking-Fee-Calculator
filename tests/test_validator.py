from datetime import datetime

import pytest

from parking import validator

pytestmark = [pytest.mark.unit, pytest.mark.blackbox]


@pytest.mark.parametrize("raw,expected", [
    pytest.param("MH12AB1234", "MH12AB1234", id="TC-VAL-01-valid-plate"),
    pytest.param(" mh-12 ab1234 ", "MH12AB1234", id="TC-VAL-02-normalised"),
    pytest.param("AB12", "AB12", id="TC-VAL-03-min-length-4"),
    pytest.param("ABCDEFGHIJ", "ABCDEFGHIJ", id="TC-VAL-04-max-length-10"),
])
def test_plate_valid(raw, expected):
    assert validator.normalize_plate(raw) == expected


@pytest.mark.parametrize("raw", [
    pytest.param("AB1", id="TC-VAL-05-too-short-3"),
    pytest.param("ABCDEFGHIJK", id="TC-VAL-06-too-long-11"),
    pytest.param("MH12@B1234", id="TC-VAL-07-special-char"),
    pytest.param("", id="TC-VAL-08-empty"),
    pytest.param("   ", id="TC-VAL-09-blank"),
    pytest.param(None, id="TC-VAL-10-none"),
    pytest.param(1234, id="TC-VAL-11-not-string"),
])
def test_plate_invalid(raw):
    with pytest.raises(ValueError):
        validator.normalize_plate(raw)


@pytest.mark.parametrize("raw,expected", [
    pytest.param("car", "CAR", id="TC-VAL-12-lowercase"),
    pytest.param(" Truck ", "TRUCK", id="TC-VAL-13-spaces-mixed-case"),
    pytest.param("BIKE", "BIKE", id="TC-VAL-14-bike"),
])
def test_vehicle_type_valid(raw, expected):
    assert validator.validate_vehicle_type(raw) == expected


@pytest.mark.parametrize("raw", [
    pytest.param("BUS", id="TC-VAL-15-unknown-type"),
    pytest.param("", id="TC-VAL-16-empty-type"),
    pytest.param(None, id="TC-VAL-17-none-type"),
    pytest.param(5, id="TC-VAL-18-non-string-type"),
])
def test_vehicle_type_invalid(raw):
    with pytest.raises(ValueError):
        validator.validate_vehicle_type(raw)


def test_parse_time_valid_string():
    """TC-VAL-19"""
    assert validator.parse_time("2026-10-26 10:00") == datetime(2026, 10, 26, 10, 0)


def test_parse_time_datetime_passthrough():
    """TC-VAL-20"""
    now = datetime(2026, 1, 1, 8, 30)
    assert validator.parse_time(now) is now


@pytest.mark.parametrize("raw", [
    pytest.param("2026-10-26", id="TC-VAL-21-date-only"),
    pytest.param("26-10-2026 10:00", id="TC-VAL-22-wrong-order"),
    pytest.param("2026-13-01 10:00", id="TC-VAL-23-month-13"),
    pytest.param("2026-02-30 10:00", id="TC-VAL-24-impossible-date"),
    pytest.param("", id="TC-VAL-25-empty-time"),
    pytest.param(None, id="TC-VAL-26-none-time"),
])
def test_parse_time_invalid(raw):
    with pytest.raises(ValueError):
        validator.parse_time(raw)
