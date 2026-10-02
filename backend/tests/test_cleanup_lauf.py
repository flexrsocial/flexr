"""Der stuendliche Timer (python -m app.cleanup) muss alle Loeschfristen
anstossen - nicht nur die, die zufaellig beim Login mitlaufen."""

from unittest.mock import patch

from app import cleanup


def test_run_all_stoesst_alle_fristen_an():
    with patch.object(cleanup, "purge_deleted_users", return_value=1) as konten, \
         patch.object(cleanup, "purge_stale_verification_uploads", return_value=2) as aufnahmen, \
         patch.object(cleanup, "purge_old_report_evidence", return_value=3) as beweise:
        assert cleanup.run_all("db") == {
            "deleted_users": 1,
            "verification_requests": 2,
            "report_evidence": 3,
        }
    for mock in (konten, aufnahmen, beweise):
        mock.assert_called_once_with("db")
