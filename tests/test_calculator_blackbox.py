"""Black-box tests: expected values are hand-computed from the rules,
never taken from the code under test."""
import pytest

from parking.calculator import calculate_fee

from .helpers import dt, plus

pytestmark = [pytest.mark.unit, pytest.mark.blackbox]

DAY = dt("2026-10-26 10:00")   # daytime entry (no night surcharge)


def fee(vt, minutes, entry=DAY, **kw):
    return calculate_fee(vt, entry, plus(entry, minutes), **kw)


# ---- Boundary Value Analysis on stay duration (CAR) ----
@pytest.mark.parametrize("minutes,expected", [
    pytest.param(0, 0, id="TC-BVA-01-0min"),
    pytest.param(15, 0, id="TC-BVA-02-15min-grace-edge"),
    pytest.param(16, 30, id="TC-BVA-03-16min-first-paid"),
    pytest.param(60, 30, id="TC-BVA-04-60min-first-hour-edge"),
    pytest.param(61, 50, id="TC-BVA-05-61min-second-hour"),
    pytest.param(120, 50, id="TC-BVA-06-120min"),
    pytest.param(121, 70, id="TC-BVA-07-121min"),
    pytest.param(540, 190, id="TC-BVA-08-9h-just-below-cap"),
    pytest.param(541, 200, id="TC-BVA-09-cap-kicks-in"),
    pytest.param(1440, 200, id="TC-BVA-10-exactly-24h"),
    pytest.param(1441, 230, id="TC-BVA-11-24h-plus-1min"),
    pytest.param(2880, 400, id="TC-BVA-12-exactly-48h"),
    pytest.param(10080, 1400, id="TC-BVA-13-exactly-7days"),
])
def test_car_duration_boundaries(minutes, expected):
    assert fee("CAR", minutes) == pytest.approx(expected)


def test_stay_over_7_days_rejected():
    """TC-BVA-14: 7 days + 1 minute."""
    with pytest.raises(ValueError):
        fee("CAR", 10081)


def test_exit_one_minute_before_entry_rejected():
    """TC-BVA-15"""
    with pytest.raises(ValueError):
        calculate_fee("CAR", DAY, plus(DAY, -1))


# ---- Equivalence Partitioning on vehicle type ----
@pytest.mark.parametrize("vt,minutes,expected", [
    pytest.param("BIKE", 60, 10, id="TC-EP-01-bike-1h"),
    pytest.param("BIKE", 120, 15, id="TC-EP-02-bike-2h"),
    pytest.param("BIKE", 660, 60, id="TC-EP-03-bike-11h-equals-cap"),
    pytest.param("BIKE", 661, 60, id="TC-EP-04-bike-12h-capped"),
    pytest.param("CAR", 120, 50, id="TC-EP-05-car-2h"),
    pytest.param("TRUCK", 60, 60, id="TC-EP-06-truck-1h"),
    pytest.param("TRUCK", 120, 100, id="TC-EP-07-truck-2h"),
    pytest.param("TRUCK", 540, 380, id="TC-EP-08-truck-9h-below-cap"),
    pytest.param("TRUCK", 541, 400, id="TC-EP-09-truck-capped"),
])
def test_vehicle_type_partitions(vt, minutes, expected):
    assert fee(vt, minutes) == pytest.approx(expected)


def test_unknown_vehicle_type_rejected():
    """TC-EP-10"""
    with pytest.raises(ValueError):
        fee("PLANE", 60)


# ---- Night surcharge boundaries (entry time, 60 min CAR stay) ----
@pytest.mark.parametrize("entry,expected", [
    pytest.param("2026-10-26 21:59", 30, id="TC-NIGHT-01-21:59-day"),
    pytest.param("2026-10-26 22:00", 45, id="TC-NIGHT-02-22:00-night"),
    pytest.param("2026-10-26 00:00", 45, id="TC-NIGHT-03-midnight-night"),
    pytest.param("2026-10-26 05:59", 45, id="TC-NIGHT-04-05:59-night"),
    pytest.param("2026-10-26 06:00", 30, id="TC-NIGHT-05-06:00-day"),
    pytest.param("2026-10-26 12:00", 30, id="TC-NIGHT-06-noon-day"),
])
def test_night_surcharge_boundaries(entry, expected):
    e = dt(entry)
    assert fee("CAR", 60, entry=e) == pytest.approx(expected)


def test_night_surcharge_not_applied_to_free_stay():
    """TC-NIGHT-07"""
    assert fee("CAR", 10, entry=dt("2026-10-26 23:00")) == 0


def test_night_surcharge_added_once_for_multi_day_stay():
    """TC-NIGHT-08: 24h from 23:00 = 200 cap + 15."""
    assert fee("CAR", 1440, entry=dt("2026-10-26 23:00")) == pytest.approx(215)


# ---- Decision table: EV x night x lost (CAR, 120 min -> base 50) ----
@pytest.mark.parametrize("ev,night,lost,expected", [
    pytest.param(False, False, False, 50, id="TC-DT-01-none"),
    pytest.param(True, False, False, 40, id="TC-DT-02-ev"),
    pytest.param(False, True, False, 65, id="TC-DT-03-night"),
    pytest.param(False, False, True, 150, id="TC-DT-04-lost"),
    pytest.param(True, True, False, 55, id="TC-DT-05-ev-night"),
    pytest.param(True, False, True, 140, id="TC-DT-06-ev-lost"),
    pytest.param(False, True, True, 165, id="TC-DT-07-night-lost"),
    pytest.param(True, True, True, 155, id="TC-DT-08-all"),
])
def test_discount_surcharge_penalty_combinations(ev, night, lost, expected):
    entry = dt("2026-10-26 23:00") if night else DAY
    assert fee("CAR", 120, entry=entry, is_ev=ev, lost_ticket=lost) == pytest.approx(expected)


# ---- Other rules ----
def test_ev_discount_on_bike_and_truck():
    """TC-EV-01: BIKE 1h 10 -> 8 ; TRUCK 1h 60 -> 48."""
    assert fee("BIKE", 60, is_ev=True) == pytest.approx(8)
    assert fee("TRUCK", 60, is_ev=True) == pytest.approx(48)


def test_ev_discount_on_full_day():
    """TC-EV-02: CAR 24h cap 200 -> 160."""
    assert fee("CAR", 1440, is_ev=True) == pytest.approx(160)


def test_ev_free_stay_stays_free():
    """TC-EV-03"""
    assert fee("CAR", 10, is_ev=True) == 0


def test_lost_ticket_on_free_stay_still_charged():
    """TC-LOST-01"""
    assert fee("CAR", 10, lost_ticket=True) == pytest.approx(100)


def test_lost_ticket_on_zero_minute_stay():
    """TC-LOST-02"""
    assert fee("CAR", 0, lost_ticket=True) == pytest.approx(100)
