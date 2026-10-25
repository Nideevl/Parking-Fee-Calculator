"""Integration tests: CLI -> validator -> calculator -> storage -> SQLite file."""
import os
import runpy
import subprocess
import sys

import pytest

from parking import cli
from parking.storage import ParkingStore

pytestmark = [pytest.mark.integration, pytest.mark.blackbox]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def db(tmp_path):
    return str(tmp_path / "it.db")


def run(db, *argv):
    lines = []
    code = cli.run(["--db", db, *argv], out=lines.append)
    return code, lines


def test_full_flow_entry_active_exit_history(db):
    """TC-IT-01"""
    assert run(db, "entry", "mh12ab1234", "car", "--time", "2026-10-26 09:00", "--ev") == (
        0, ["Entry recorded (id 1)"])
    code, lines = run(db, "active")
    assert code == 0 and lines == ["MH12AB1234 CAR in=2026-10-26 09:00"]
    assert run(db, "exit", "MH12AB1234", "--time", "2026-10-26 14:10") == (0, ["Fee: 104.00"])
    code, lines = run(db, "history")
    assert code == 0
    assert lines == ["MH12AB1234 CAR in=2026-10-26 09:00 out=2026-10-26 14:10 fee=104.0"]
    assert run(db, "active") == (0, [])


def test_quote_does_not_touch_database(db):
    """TC-IT-02"""
    assert run(db, "quote", "CAR", "2026-10-26 23:00", "2026-10-27 01:00", "--ev", "--lost") == (
        0, ["Fee: 155.00"])
    assert not os.path.exists(db)


def test_cli_rejects_unknown_vehicle_type(db):
    """TC-IT-03"""
    code, lines = run(db, "quote", "PLANE", "2026-10-26 10:00", "2026-10-26 12:00")
    assert code == 1 and lines[0].startswith("Error:")


def test_cli_rejects_bad_time_format(db):
    """TC-IT-04"""
    code, lines = run(db, "quote", "CAR", "26/10/2026 10:00", "2026-10-26 12:00")
    assert code == 1 and "YYYY-MM-DD HH:MM" in lines[0]


def test_cli_exit_without_entry(db):
    """TC-IT-05"""
    code, lines = run(db, "exit", "AB1234", "--time", "2026-10-26 12:00")
    assert code == 1 and "No active entry" in lines[0]


def test_cli_duplicate_entry_rejected(db):
    """TC-IT-06"""
    run(db, "entry", "AB1234", "car", "--time", "2026-10-26 10:00")
    code, lines = run(db, "entry", "ab1234", "car", "--time", "2026-10-26 10:30")
    assert code == 1 and "already parked" in lines[0]


def test_cli_exit_before_entry(db):
    """TC-IT-07"""
    run(db, "entry", "AB1234", "car", "--time", "2026-10-26 10:00")
    code, lines = run(db, "exit", "AB1234", "--time", "2026-10-26 09:00")
    assert code == 1 and "before entry" in lines[0]


def test_cli_lost_ticket_on_exit(db):
    """TC-IT-08"""
    run(db, "entry", "AB1234", "truck", "--time", "2026-10-26 10:00")
    assert run(db, "exit", "AB1234", "--time", "2026-10-26 11:00", "--lost") == (0, ["Fee: 160.00"])


def test_cli_history_filtered_by_plate(db):
    """TC-IT-09"""
    run(db, "entry", "AB1234", "car", "--time", "2026-10-26 10:00")
    run(db, "entry", "CD5678", "bike", "--time", "2026-10-26 10:00")
    code, lines = run(db, "history", "--plate", "cd5678")
    assert code == 0 and len(lines) == 1 and lines[0].startswith("CD5678")


def test_cli_default_time_is_now(db):
    """TC-IT-10: entry and exit without --time (fee must be 0, within grace)."""
    assert run(db, "entry", "AB1234", "car")[0] == 0
    assert run(db, "exit", "AB1234") == (0, ["Fee: 0.00"])


def test_state_shared_between_cli_and_store(db):
    """TC-IT-11: CLI writes, ParkingStore reads the same file."""
    run(db, "entry", "AB1234", "car", "--time", "2026-10-26 10:00")
    run(db, "exit", "AB1234", "--time", "2026-10-26 12:30")
    store = ParkingStore(db)
    try:
        assert store.history()[0]["fee"] == pytest.approx(70)
    finally:
        store.close()


def test_python_dash_m_entrypoint_subprocess(tmp_path):
    """TC-IT-12: real process, real stdout, real exit code."""
    ok = subprocess.run(
        [sys.executable, "-m", "parking", "quote", "CAR", "2026-10-26 10:00", "2026-10-26 12:30"],
        cwd=ROOT, capture_output=True, text=True)
    assert ok.returncode == 0 and ok.stdout.strip() == "Fee: 70.00"
    bad = subprocess.run(
        [sys.executable, "-m", "parking", "quote", "PLANE", "2026-10-26 10:00", "2026-10-26 12:30"],
        cwd=ROOT, capture_output=True, text=True)
    assert bad.returncode == 1


def test_main_and_dunder_main_exit_codes(monkeypatch, capsys):
    """TC-IT-13: in-process run of main() / __main__ so coverage sees them."""
    monkeypatch.setattr(sys, "argv", ["parking", "quote", "CAR", "2026-10-26 10:00", "2026-10-26 11:00"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("parking", run_name="__main__")
    assert exc.value.code == 0
    assert "Fee: 30.00" in capsys.readouterr().out
