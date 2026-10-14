"""Der stuendliche Timer (python -m app.cleanup) muss alle Loeschfristen
anstossen - nicht nur die, die zufaellig beim Login mitlaufen."""

from datetime import timedelta
from unittest.mock import patch

from app import cleanup
from app.models import PushNotification
from app.timeutil import utcnow
from tests.conftest import TestingSessionLocal, register_user


def test_run_all_stoesst_alle_fristen_an():
    with patch.object(cleanup, "purge_deleted_users", return_value=1) as konten, \
         patch.object(cleanup, "purge_stale_verification_uploads", return_value=2) as aufnahmen, \
         patch.object(cleanup, "purge_old_report_evidence", return_value=3) as beweise, \
         patch.object(cleanup, "purge_old_push_notifications", return_value=4) as mitteilungen, \
         patch.object(cleanup, "purge_orphan_photo_objects", return_value=5) as fotos, \
         patch.object(cleanup, "purge_unmatched_flagged_messages", return_value=6) as markiert, \
         patch.object(cleanup, "purge_stale_push_tokens", return_value=7) as tokens:
        assert cleanup.run_all("db") == {
            "deleted_users": 1,
            "verification_requests": 2,
            "report_evidence": 3,
            "push_notifications": 4,
            "orphan_photos": 5,
            "unmatched_flagged_messages": 6,
            "push_tokens": 7,
        }
    for mock in (konten, aufnahmen, beweise, mitteilungen, fotos, markiert, tokens):
        mock.assert_called_once_with("db")


def test_alte_app_benachrichtigungen_werden_geloescht(client):
    register_user(client, "mitteilung@example.com")
    db = TestingSessionLocal()
    try:
        from app.models import User

        user_id = db.query(User.id).filter(User.email == "mitteilung@example.com").scalar()
        jetzt = utcnow()
        for key, alter in (("alt", timedelta(days=31)), ("jung", timedelta(days=29))):
            db.add(PushNotification(user_id=user_id, topic="inactivity", title=key,
                                    body="x", dedupe_key=key, created_at=jetzt - alter))
        db.commit()
        assert cleanup.purge_old_push_notifications(db) == 1
        assert [p.title for p in db.query(PushNotification).filter_by(user_id=user_id)] == ["jung"]
    finally:
        db.close()


def test_alte_push_adressen_werden_geloescht(client):
    """Wer FLEXR 60 Tage nicht geöffnet hat, dessen Geräteadresse geht -
    eine frisch gemeldete bleibt."""
    from app import push
    from app.models import PushToken, User
    from app.retention import PUSH_TOKEN_STALE_DAYS

    register_user(client, "pushalt@example.com")
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "pushalt@example.com").one()
        push.register(db, user, "android", "token-alt")
        push.register(db, user, "android", "token-frisch")
        alt = db.query(PushToken).filter(PushToken.token == "token-alt").one()
        alt.last_seen = utcnow() - timedelta(days=PUSH_TOKEN_STALE_DAYS, hours=1)
        db.commit()

        assert cleanup.purge_stale_push_tokens(db) == 1
        assert [t.token for t in db.query(PushToken)] == ["token-frisch"]

        # Meldet sich das Gerät nach der Pause wieder, ist es sofort zurück.
        push.register(db, user, "android", "token-alt")
        assert db.query(PushToken).count() == 2
    finally:
        db.close()
