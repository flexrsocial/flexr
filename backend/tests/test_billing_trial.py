"""Der Probemonat läuft ab der Registrierung, nicht ab der Zahlung.

Beim Stripe-Checkout darf deshalb kein neuer 30-Tage-Zeitraum angekündigt
werden - übergeben wird das bereits feststehende Ende des Probemonats.
"""

from datetime import datetime, timedelta, timezone

from app.stripe_client import trial_end_timestamp


NOW = datetime(2026, 7, 27, 12, 0, 0)


def test_verbleibende_gratiszeit_wird_als_trial_end_uebergeben():
    trial_ends_at = NOW + timedelta(days=12)
    result = trial_end_timestamp(trial_ends_at, now=NOW)
    assert result == int(trial_ends_at.replace(tzinfo=timezone.utc).timestamp())


def test_zeitstempel_wird_als_utc_gerechnet():
    """Naive Werte aus der DB sind UTC - unabhängig von der Serverzeitzone."""
    trial_ends_at = datetime(2026, 8, 8, 12, 0, 0)
    # 2026-08-08T12:00:00Z
    assert trial_end_timestamp(trial_ends_at, now=NOW) == 1786190400


def test_abgelaufener_probemonat_ergibt_keinen_trial():
    assert trial_end_timestamp(NOW - timedelta(days=1), now=NOW) is None


def test_weniger_als_48_stunden_ergibt_keinen_trial():
    # Stripe lehnt ein trial_end unter 48 Stunden ab - dann startet das Abo sofort.
    assert trial_end_timestamp(NOW + timedelta(hours=47), now=NOW) is None
    assert trial_end_timestamp(NOW + timedelta(hours=49), now=NOW) is not None


def test_ohne_trial_ends_at_kein_trial():
    assert trial_end_timestamp(None, now=NOW) is None
