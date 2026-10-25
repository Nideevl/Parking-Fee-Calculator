import sqlite3

from . import calculator, validator

_SCHEMA = """
CREATE TABLE IF NOT EXISTS parking_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate TEXT NOT NULL,
    vehicle_type TEXT NOT NULL,
    is_ev INTEGER NOT NULL DEFAULT 0,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    lost_ticket INTEGER NOT NULL DEFAULT 0,
    fee REAL
)
"""


class ParkingStore:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(_SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def _active_row(self, plate):
        return self.conn.execute(
            "SELECT * FROM parking_log WHERE plate=? AND exit_time IS NULL", (plate,)
        ).fetchone()

    def record_entry(self, plate, vehicle_type, entry_time, is_ev=False):
        plate = validator.normalize_plate(plate)
        vehicle_type = validator.validate_vehicle_type(vehicle_type)
        entry = validator.parse_time(entry_time)
        if self._active_row(plate):
            raise ValueError("Vehicle already parked")
        cur = self.conn.execute(
            "INSERT INTO parking_log (plate, vehicle_type, is_ev, entry_time) VALUES (?,?,?,?)",
            (plate, vehicle_type, int(bool(is_ev)), entry.strftime(validator.TIME_FORMAT)),
        )
        self.conn.commit()
        return cur.lastrowid

    def record_exit(self, plate, exit_time, lost_ticket=False):
        plate = validator.normalize_plate(plate)
        exit_ = validator.parse_time(exit_time)
        row = self._active_row(plate)
        if not row:
            raise ValueError("No active entry for this vehicle")
        entry = validator.parse_time(row["entry_time"])
        fee = calculator.calculate_fee(
            row["vehicle_type"], entry, exit_, bool(row["is_ev"]), lost_ticket
        )
        self.conn.execute(
            "UPDATE parking_log SET exit_time=?, lost_ticket=?, fee=? WHERE id=?",
            (exit_.strftime(validator.TIME_FORMAT), int(bool(lost_ticket)), fee, row["id"]),
        )
        self.conn.commit()
        return fee

    def active(self):
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM parking_log WHERE exit_time IS NULL ORDER BY id")]

    def history(self, plate=None):
        if plate:
            plate = validator.normalize_plate(plate)
            rows = self.conn.execute(
                "SELECT * FROM parking_log WHERE plate=? ORDER BY id", (plate,))
        else:
            rows = self.conn.execute("SELECT * FROM parking_log ORDER BY id")
        return [dict(r) for r in rows]
