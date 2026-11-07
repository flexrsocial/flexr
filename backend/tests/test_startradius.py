"""Neue Konten starten mit dem groessten Suchradius, den sie einstellen duerfen.

Bis zum 14.10.2026 stand jedes neue Konto auf 20 km (Spalten-Default) - in
einer duenn besetzten Gegend ein fast leeres erstes Deck, obwohl waehrend des
Startboosts der volle Regler erlaubt war.
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


def test_unbefristet_frei_voller_regler_ohne_datum(client, monkeypatch):
    """Seit 07.11.2026: voller Umkreis (1100 km) für alle, ohne Enddatum."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "radius_free_for_all", True)
    monkeypatch.setattr(settings, "radius_boost_last_day", utcnow().date() - timedelta(days=1))
    headers = register_user(client, "start.unbefristet@example.com")
    assert _radius(client, headers) == MAX_SEARCH_RADIUS_KM == 1100
    status = client.get("/api/billing/status", headers=headers).json()
    assert status["max_radius_km"] == 1100
    assert status["radius_free_for_all"] is True
    assert status["radius_boost_last_day"] is None
    resp = client.patch("/api/profiles/me", headers=headers, json={"search_radius_km": 1100})
    assert resp.json()["search_radius_km"] == 1100
    assert client.patch(
        "/api/profiles/me", headers=headers, json={"search_radius_km": 1101}
    ).status_code == 422


def test_ganz_oesterreich_und_deutschland_in_reichweite():
    from app.geo import haversine_km

    # Sylt (List) bis Bad Radkersburg: die weiteste Strecke in AT+DE.
    assert haversine_km(55.0587, 8.4144, 46.677, 16.107) < MAX_SEARCH_RADIUS_KM
