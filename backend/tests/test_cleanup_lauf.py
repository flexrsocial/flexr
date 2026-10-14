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
         patch.object(cleanup, "purge_orphan_photo_objects", return_value=5) as fotos:
        assert cleanup.run_all("db") == {
            "deleted_users": 1,
            "verification_requests": 2,
            "report_evidence": 3,
            "push_notifications": 4,
            "orphan_photos": 5,
        }
    for mock in (konten, aufnahmen, beweise, mitteilungen, fotos):
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
