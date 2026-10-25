"""Business rules / tariff constants. Change values here only."""

VEHICLE_TYPES = ("BIKE", "CAR", "TRUCK")

FIRST_HOUR_RATE = {"BIKE": 10, "CAR": 30, "TRUCK": 60}
EXTRA_HOUR_RATE = {"BIKE": 5, "CAR": 20, "TRUCK": 40}
DAILY_CAP = {"BIKE": 60, "CAR": 200, "TRUCK": 400}

GRACE_MINUTES = 15          # stay <= 15 min is free
EV_DISCOUNT = 0.20          # 20% off parking charge for EVs
NIGHT_SURCHARGE = 15        # flat, if entry between 22:00 and 05:59
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 6
LOST_TICKET_PENALTY = 100   # flat
MAX_STAY_MINUTES = 7 * 24 * 60   # stays longer than 7 days are rejected
