import pytest

from parking.storage import ParkingStore

pytestmark = [pytest.mark.unit, pytest.mark.whitebox]


@pytest.fixture
def store():
    s = ParkingStore(":memory:")
    yield s
    s.close()


def test_entry_returns_incrementing_ids(store):
    """TC-ST-01"""
    assert store.record_entry("AB1234", "CAR", "2026-10-26 10:00") == 1
    assert store.record_entry("CD5678", "BIKE", "2026-10-26 10:05") == 2


def test_entry_stores_normalised_values(store):
    """TC-ST-02"""
    store.record_entry(" mh-12 ab1234", "car", "2026-10-26 10:00", is_ev=True)
    row = store.active()[0]
    assert row["plate"] == "MH12AB1234"
    assert row["vehicle_type"] == "CAR"
    assert row["is_ev"] == 1


def test_duplicate_active_entry_rejected_case_insensitive(store):
    """TC-ST-03"""
    store.record_entry("AB1234", "CAR", "2026-10-26 10:00")
    with pytest.raises(ValueError, match="already parked"):
        store.record_entry("ab1234", "CAR", "2026-10-26 11:00")


def test_invalid_entry_inserts_nothing(store):
    """TC-ST-04"""
    for args in [("A", "CAR", "2026-10-26 10:00"),
                 ("AB1234", "BUS", "2026-10-26 10:00"),
                 ("AB1234", "CAR", "bad-time")]:
        with pytest.raises(ValueError):
            store.record_entry(*args)
    assert store.history() == []


def test_exit_computes_and_persists_fee(store):
    """TC-ST-05: CAR 10:00-12:30 -> 70."""
    store.record_entry("AB1234", "CAR", "2026-10-26 10:00")
    assert store.record_exit("AB1234", "2026-10-26 12:30") == pytest.approx(70)
    row = store.history()[0]
    assert row["fee"] == pytest.approx(70)
    assert row["exit_time"] == "2026-10-26 12:30"
    assert store.active() == []


def test_exit_uses_stored_ev_flag(store):
    """TC-ST-06"""
    store.record_entry("AB1234", "CAR", "2026-10-26 10:00", is_ev=True)
    assert store.record_exit("AB1234", "2026-10-26 12:00") == pytest.approx(40)


def test_exit_lost_ticket_flag_saved(store):
    """TC-ST-07"""
    store.record_entry("AB1234", "CAR", "2026-10-26 10:00")
    assert store.record_exit("AB1234", "2026-10-26 11:00", lost_ticket=True) == pytest.approx(130)
    assert store.history()[0]["lost_ticket"] == 1


def test_exit_without_entry_rejected(store):
    """TC-ST-08"""
    with pytest.raises(ValueError, match="No active entry"):
        store.record_exit("AB1234", "2026-10-26 12:00")


def test_exit_before_entry_rejected_and_vehicle_stays_active(store):
    """TC-ST-09"""
    store.record_entry("AB1234", "CAR", "2026-10-26 10:00")
    with pytest.raises(ValueError):
        store.record_exit("AB1234", "2026-10-26 09:00")
    assert len(store.active()) == 1
    assert store.history()[0]["exit_time"] is None


def test_reentry_allowed_after_exit(store):
    """TC-ST-10"""
    store.record_entry("AB1234", "CAR", "2026-10-26 10:00")
    store.record_exit("AB1234", "2026-10-26 11:00")
    store.record_entry("AB1234", "CAR", "2026-10-26 12:00")
    assert len(store.history()) == 2
    assert len(store.active()) == 1


def test_history_filter_by_plate(store):
    """TC-ST-11"""
    store.record_entry("AB1234", "CAR", "2026-10-26 10:00")
    store.record_entry("CD5678", "BIKE", "2026-10-26 10:00")
    assert [r["plate"] for r in store.history("cd5678")] == ["CD5678"]
    assert len(store.history()) == 2


def test_history_invalid_plate_filter_rejected(store):
    """TC-ST-12"""
    with pytest.raises(ValueError):
        store.history("A")


def test_data_persists_across_connections(tmp_path):
    """TC-ST-13"""
    db = str(tmp_path / "p.db")
    s1 = ParkingStore(db)
    s1.record_entry("AB1234", "CAR", "2026-10-26 10:00")
    s1.close()
    s2 = ParkingStore(db)
    assert len(s2.active()) == 1
    s2.close()
