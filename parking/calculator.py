import math

from . import rules


def is_night_entry(entry):
    h = entry.hour
    return h >= rules.NIGHT_START_HOUR or h < rules.NIGHT_END_HOUR


def _base_charge(vehicle_type, minutes):
    """Charge for a stay of 0 < minutes <= 24h, capped at the daily cap."""
    hours = math.ceil(minutes / 60)
    charge = rules.FIRST_HOUR_RATE[vehicle_type]
    if hours > 1:
        charge += (hours - 1) * rules.EXTRA_HOUR_RATE[vehicle_type]
    return min(charge, rules.DAILY_CAP[vehicle_type])


def calculate_fee(vehicle_type, entry, exit_, is_ev=False, lost_ticket=False):
    """Return parking fee (float, 2 dp). Raises ValueError on bad input."""
    if vehicle_type not in rules.VEHICLE_TYPES:
        raise ValueError("Unknown vehicle type")
    if exit_ < entry:
        raise ValueError("Exit time is before entry time")

    minutes = int((exit_ - entry).total_seconds() // 60)
    if minutes > rules.MAX_STAY_MINUTES:
        raise ValueError("Stay exceeds maximum of 7 days")

    if minutes <= rules.GRACE_MINUTES:
        charge = 0.0
    else:
        full_days, rem = divmod(minutes, 24 * 60)
        charge = full_days * rules.DAILY_CAP[vehicle_type]
        if rem > 0:
            charge += _base_charge(vehicle_type, rem)
        if is_ev:
            charge *= (1 - rules.EV_DISCOUNT)
        if is_night_entry(entry):
            charge += rules.NIGHT_SURCHARGE

    if lost_ticket:
        charge += rules.LOST_TICKET_PENALTY
    return round(charge, 2)
