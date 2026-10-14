"""Neue Konten starten mit dem groessten Suchradius, den sie einstellen duerfen.

Bis zum 14.10.2026 stand jedes neue Konto auf 20 km (Spalten-Default) - in
einer duenn besetzten Gegend ein fast leeres erstes Deck, obwohl waehrend des
Startboosts 580 km erlaubt sind.
"""

from datetime import timedelta

from app.config import settings
from app.schemas import MAX_SEARCH_RADIUS_KM
from app.timeutil import utcnow
from tests.conftest import register_user


def _radius(client, headers):
    return client.get("/api/profiles/me", headers=headers).json()["search_radius_km"]


def test_im_startboost_voller_regler(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "radius_boost_last_day", utcnow().date() + timedelta(days=30))
    headers = register_user(client, "start.boost@example.com")
    assert _radius(client, headers) == MAX_SEARCH_RADIUS_KM


def test_nach_dem_startboost_die_gratis_grenze(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "radius_boost_last_day", utcnow().date() - timedelta(days=1))
    headers = register_user(client, "start.frei@example.com")
    assert _radius(client, headers) == settings.free_max_radius_km


def test_ohne_premium_schalter_voller_regler(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", False)
    monkeypatch.setattr(settings, "radius_boost_last_day", utcnow().date() - timedelta(days=1))
    headers = register_user(client, "start.aus@example.com")
    assert _radius(client, headers) == MAX_SEARCH_RADIUS_KM
