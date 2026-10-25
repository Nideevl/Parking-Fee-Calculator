from datetime import datetime, timedelta

FMT = "%Y-%m-%d %H:%M"


def dt(text):
    return datetime.strptime(text, FMT)


def plus(entry, minutes):
    return entry + timedelta(minutes=minutes)
