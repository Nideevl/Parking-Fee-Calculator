"""White-box tests: each test targets a specific branch / path in
parking/calculator.py. Run with --cov-branch to verify coverage."""
from datetime import timedelta

import pytest

from parking import calculator

from .helpers import dt, plus

pytestmark = [pytest.mark.unit, pytest.mark.whitebox]

DAY = dt("2026-10-26 10:00")


@pytest.mark.parametrize("hour,expected", [
    (0, True), (5, True), (6, False), (12, False), (21, False), (22, True), (23, True),
])
def test_is_night_entry_branches(hour, expected):
    """TC-WB-01: both sides of 'h >= 22 or h < 6'."""
    assert calculator.is_night_entry(DAY.replace(hour=hour)) is expected


def test_base_charge_single_hour_skips_extra_hours_branch():
    """TC-WB-02: hours == 1 -> 'if hours > 1' False."""
    assert calculator._base_charge("CAR", 45) == 30


def test_base_charge_multiple_hours_takes_extra_hours_branch():
    """TC-WB-03: hours > 1 -> 'if hours > 1' True."""
    assert calculator._base_charge("CAR", 150) == 70


def test_base_charge_cap_branch_returns_cap():
    """TC-WB-04: min() selects the cap."""
    assert calculator._base_charge("TRUCK", 1000) == 400


def test_base_charge_below_cap_returns_computed():
    """TC-WB-05: min() selects the computed charge."""
    assert calculator._base_charge("TRUCK", 120) == 100


def test_path_grace_period():
    """TC-WB-06: path = grace branch, no EV / night checks."""
    assert calculator.calculate_fee("CAR", DAY, plus(DAY, 15)) == 0


def test_path_remainder_zero():
    """TC-WB-07: rem == 0 -> 'if rem > 0' False (exact multiple of 24h)."""
    assert calculator.calculate_fee("BIKE", DAY, plus(DAY, 2 * 1440)) == 120


def test_path_remainder_positive():
    """TC-WB-08: rem > 0 -> 'if rem > 0' True."""
    assert calculator.calculate_fee("BIKE", DAY, plus(DAY, 1440 + 60)) == 70


def test_path_paid_stay_ev_true_night_true_lost_true():
    """TC-WB-09: every optional branch True."""
    entry = dt("2026-10-26 22:30")
    assert calculator.calculate_fee("CAR", entry, plus(entry, 60), True, True) == pytest.approx(
        30 * 0.8 + 15 + 100)


def test_path_paid_stay_ev_false_night_false_lost_false():
    """TC-WB-10: every optional branch False."""
    assert calculator.calculate_fee("CAR", DAY, plus(DAY, 60), False, False) == 30


def test_guard_unknown_vehicle_type():
    """TC-WB-11: first guard raises."""
    with pytest.raises(ValueError, match="Unknown vehicle type"):
        calculator.calculate_fee("PLANE", DAY, plus(DAY, 60))


def test_guard_exit_before_entry():
    """TC-WB-12: second guard raises."""
    with pytest.raises(ValueError, match="before entry"):
        calculator.calculate_fee("CAR", DAY, DAY - timedelta(minutes=5))


def test_guard_max_stay():
    """TC-WB-13: third guard raises."""
    with pytest.raises(ValueError, match="maximum"):
        calculator.calculate_fee("CAR", DAY, plus(DAY, 7 * 1440 + 1))


def test_seconds_are_truncated_to_whole_minutes():
    """TC-WB-14: 15m59s counts as 15 min (free); 16m00s is paid."""
    entry = DAY
    assert calculator.calculate_fee("CAR", entry, entry + timedelta(minutes=15, seconds=59)) == 0
    assert calculator.calculate_fee("CAR", entry, entry + timedelta(minutes=16)) == 30


def test_result_rounded_to_two_decimals():
    """TC-WB-15: round(charge, 2) applied."""
    result = calculator.calculate_fee("BIKE", DAY, plus(DAY, 120), is_ev=True)
    assert result == 12.0
    assert result == round(result, 2)
