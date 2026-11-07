"""Gym-Entscheidungs-Mail fuer Vorschlaege nachsenden, die vor dem 07.11.2026
(Einfuehrung von mailer.send_gym_decision) schon entschieden waren.

Ohne Schalter nur anzeigen; mit ``--senden`` verschicken. Jede Mail hoechstens
einmal (send_once). Bei Ablehnung faellt wie in admin.reject_gym die
Gym-Wechselsperre weg. Offene Vorschlaege bleiben unberuehrt: Deren Mail geht
automatisch raus, sobald im Admin-Dashboard entschieden wird.

    ssh flexr-vps "cd /flexr/backend && venv/bin/python scripts/gym_entscheid_nachsenden.py [--senden] [--tage N]"
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.getcwd())

from app import mailer  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.email_notifications import send_once  # noqa: E402
from app.models import Gym, GymStatus, gym_members  # noqa: E402


def maskiert(email: str) -> str:
    lokal, _, domain = email.partition("@")
    return f"{lokal[:2]}***@{domain}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--senden", action="store_true")
    parser.add_argument("--tage", type=int, default=3)
    args = parser.parse_args()

    seit = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=args.tage)
    db = SessionLocal()
    try:
        gyms = (
            db.query(Gym)
            .filter(Gym.created_at >= seit)
            .order_by(Gym.created_at)
            .all()
        )
        if not gyms:
            print(f"Keine Gym-Vorschlaege in den letzten {args.tage} Tagen.")
            return
        gesendet = 0
        for gym in gyms:
            mitglieder = gym_members(db, gym)
            print(f"{gym.created_at:%d.%m. %H:%M}  {gym.status.value:9} {gym.label}  "
                  f"({len(mitglieder)} Nutzer)")
            if gym.status == GymStatus.pending:
                print("    offen - Mail kommt automatisch bei der Entscheidung im Dashboard")
                continue
            approved = gym.status == GymStatus.approved
            for user in mitglieder:
                print(f"    -> {maskiert(user.email)} ({user.language})")
                if not args.senden:
                    continue
                if not approved:
                    user.gym_changed_at = None
                    db.commit()
                ok = send_once(
                    db,
                    f"gym_decision:{gym.id}:{gym.status.value}:{user.id}",
                    "gym_decision",
                    lambda u=user: mailer.send_gym_decision(
                        u.email, u.name, gym.name, approved, u.language
                    ),
                )
                print("       gesendet" if ok else "       FEHLER beim Versand")
                gesendet += ok
        if args.senden:
            print(f"\n{gesendet} Mail(s) verschickt.")
        else:
            print("\nNur angezeigt. Zum Verschicken mit --senden aufrufen.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
