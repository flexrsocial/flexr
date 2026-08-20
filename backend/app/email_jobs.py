"""Taegliche transaktionale E-Mails, fuer die Stripe kein Ereignis erzeugt."""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from . import mailer
from .database import SessionLocal
from .email_notifications import send_once
from .models import User


def _utc_naive(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _vienna_day_window(day: date) -> tuple[datetime, datetime]:
    start_local = datetime.combine(day, time.min, tzinfo=mailer.VIENNA)
    end_local = start_local + timedelta(days=1)
    return _utc_naive(start_local), _utc_naive(end_local)


def run_due_email_jobs(db: Session, now: datetime | None = None) -> dict[str, int]:
    """Versendet Faelliges und gibt nur aggregierte Zaehler zurueck."""
    current = now or datetime.utcnow()
    local_day = current.replace(tzinfo=timezone.utc).astimezone(mailer.VIENNA).date()
    ending_start, ending_end = _vienna_day_window(local_day + timedelta(days=3))

    base = db.query(User).filter(
        User.deleted_at.is_(None),
        User.is_banned.is_(False),
        User.email_verified_at.isnot(None),
        User.is_subscribed.is_(False),
        User.stripe_subscription_id.is_(None),
    )

    ending_users = base.filter(
        User.trial_ends_at >= ending_start,
        User.trial_ends_at < ending_end,
    ).all()
    ended_users = base.filter(
        User.trial_ends_at <= current,
        User.trial_ends_at > current - timedelta(days=2),
    ).all()

    result = {"trial_ending_sent": 0, "trial_ended_sent": 0, "failed": 0}

    for user in ending_users:
        key = f"trial:ending:{user.id}:{user.trial_ends_at.isoformat()}"
        sent = send_once(
            db,
            key,
            "free_trial_ending",
            lambda user=user: mailer.send_free_trial_ending(
                user.email, user.name, user.trial_ends_at
            ),
        )
        result["trial_ending_sent" if sent else "failed"] += 1

    for user in ended_users:
        key = f"trial:ended:{user.id}:{user.trial_ends_at.isoformat()}"
        sent = send_once(
            db,
            key,
            "free_trial_ended",
            lambda user=user: mailer.send_free_trial_ended(user.email, user.name),
        )
        result["trial_ended_sent" if sent else "failed"] += 1

    return result


def main() -> None:
    db = SessionLocal()
    try:
        result = run_due_email_jobs(db)
    finally:
        db.close()
    print(result)
    if result["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
