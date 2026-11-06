"""Zaehlt, wo noch nicht freigeschaltete Konten haengen. Nur lesen, nur Summen.

Keine Namen, Adressen oder IDs in der Ausgabe. Ausfuehren vom eigenen Rechner:

    ssh flexr-vps 'cd /flexr/backend && venv/bin/python -' < backend/scripts/pruefung_haenger.py
"""

import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.getcwd())

from app.database import SessionLocal  # noqa: E402
from app.email_jobs import VERIFICATION_REMINDER_AFTER, VERIFICATION_REMINDER_LAST_DAY  # noqa: E402
from app.models import MIN_PHOTOS, EmailNotification, User, VerificationStatus  # noqa: E402
from app.verification_service import latest_request, next_step_for  # noqa: E402


def schritt(db, user) -> str:
    req = latest_request(db, user.id)
    if req is not None and req.status in (VerificationStatus.approved, VerificationStatus.rejected):
        return req.status.value
    return next_step_for(req)


def fenster(user, now) -> str:
    reference = user.last_active_at or user.created_at
    if reference is None or reference <= now - timedelta(days=VERIFICATION_REMINDER_LAST_DAY):
        return "aelter als 14 Tage"
    if reference > now - VERIFICATION_REMINDER_AFTER:
        return "unter 20 Stunden"
    return "im Erinnerungsfenster"


def main() -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db = SessionLocal()
    try:
        users = (
            db.query(User)
            .filter(
                User.deleted_at.is_(None),
                User.is_banned.is_(False),
                User.verification_required.is_(True),
                User.activated_at.is_(None),
            )
            .all()
        )
        zeilen = Counter()
        for user in users:
            zeilen[(
                "bestaetigt" if user.email_verified_at else "UNBESTAETIGT",
                schritt(db, user),
                f"fotos>={MIN_PHOTOS}" if len(user.valid_photos) >= MIN_PHOTOS else f"fotos<{MIN_PHOTOS}",
                fenster(user, now),
            )] += 1
        mails = Counter(
            kind for (kind,) in db.query(EmailNotification.kind)
            .filter(
                EmailNotification.kind.in_(["verification_reminder", "verification_reminder_2"]),
                EmailNotification.sent_at.isnot(None),
            )
        )
    finally:
        db.rollback()
        db.close()

    print(f"Nicht freigeschaltete Konten: {len(users)}")
    for key, anzahl in sorted(zeilen.items()):
        print(f"{anzahl:5d}  " + " | ".join(key))
    print("Bisher verschickt:", dict(mails))


main()
