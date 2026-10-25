import argparse
import sys
from datetime import datetime

from . import calculator, validator
from .storage import ParkingStore


def _t(value):
    return value if value else datetime.now().replace(second=0, microsecond=0)


def build_parser():
    p = argparse.ArgumentParser(prog="parking", description="Parking Fee Calculator")
    p.add_argument("--db", default="parking.db", help="SQLite file (default parking.db)")
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("quote", help="calculate a fee without saving")
    q.add_argument("vehicle_type")
    q.add_argument("entry")
    q.add_argument("exit")
    q.add_argument("--ev", action="store_true")
    q.add_argument("--lost", action="store_true")

    e = sub.add_parser("entry", help="record a vehicle entry")
    e.add_argument("plate")
    e.add_argument("vehicle_type")
    e.add_argument("--time")
    e.add_argument("--ev", action="store_true")

    x = sub.add_parser("exit", help="record exit and print fee")
    x.add_argument("plate")
    x.add_argument("--time")
    x.add_argument("--lost", action="store_true")

    sub.add_parser("active", help="list parked vehicles")
    h = sub.add_parser("history", help="list log")
    h.add_argument("--plate")
    return p


def run(argv=None, out=print):
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "quote":
            fee = calculator.calculate_fee(
                validator.validate_vehicle_type(args.vehicle_type),
                validator.parse_time(args.entry),
                validator.parse_time(args.exit),
                args.ev, args.lost)
            out("Fee: %.2f" % fee)
            return 0
        store = ParkingStore(args.db)
        try:
            if args.cmd == "entry":
                rid = store.record_entry(args.plate, args.vehicle_type, _t(args.time), args.ev)
                out("Entry recorded (id %d)" % rid)
            elif args.cmd == "exit":
                fee = store.record_exit(args.plate, _t(args.time), args.lost)
                out("Fee: %.2f" % fee)
            elif args.cmd == "active":
                for r in store.active():
                    out("%(plate)s %(vehicle_type)s in=%(entry_time)s" % r)
            elif args.cmd == "history":
                for r in store.history(args.plate):
                    out("%(plate)s %(vehicle_type)s in=%(entry_time)s out=%(exit_time)s fee=%(fee)s" % r)
        finally:
            store.close()
        return 0
    except ValueError as exc:
        out("Error: %s" % exc)
        return 1


def main():
    sys.exit(run())
