import re
from datetime import datetime

from .rules import VEHICLE_TYPES

_PLATE_RE = re.compile(r"^[A-Z0-9]{4,10}$")
TIME_FORMAT = "%Y-%m-%d %H:%M"


def normalize_plate(plate):
    if not isinstance(plate, str):
        raise ValueError("Plate must be a string")
    plate = plate.strip().upper().replace(" ", "").replace("-", "")
    if not _PLATE_RE.match(plate):
        raise ValueError("Plate must be 4-10 letters/digits")
    return plate


def validate_vehicle_type(vehicle_type):
    if not isinstance(vehicle_type, str):
        raise ValueError("Vehicle type must be a string")
    vt = vehicle_type.strip().upper()
    if vt not in VEHICLE_TYPES:
        raise ValueError("Vehicle type must be one of: " + ", ".join(VEHICLE_TYPES))
    return vt


def parse_time(value):
    if isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(value, TIME_FORMAT)
    except (TypeError, ValueError):
        raise ValueError("Time must be 'YYYY-MM-DD HH:MM'")
