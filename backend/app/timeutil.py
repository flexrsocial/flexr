"""Aktuelle Zeit als naives UTC-datetime.

``datetime.utcnow()`` ist seit Python 3.12 veraltet. Die Datenbank speichert
aber durchgehend naive UTC-Zeitstempel (DateTime ohne Zeitzone), und daran
haengen rechtlich relevante Fristen (Aufbewahrung, DSA-Meldefristen,
Karenzzeiten). Ein Umstieg auf zeitzonenbewusste Werte liesse Vergleiche
zwischen alten und neuen Werten mit TypeError scheitern oder - schlimmer - an
Stellen, die das abfangen, still falsch ausgehen.

Diese Helfer liefern deshalb exakt denselben Wert wie bisher (naiv, UTC), nur
ohne die veraltete API. Ein echter Umstieg auf zeitzonenbewusste Spalten waere
ein eigenes, sorgfaeltig geplantes Vorhaben samt Migration.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Wie das alte ``datetime.utcnow()``: jetzt, in UTC, ohne tzinfo."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utcfromtimestamp(timestamp: float) -> datetime:
    """Wie das alte ``datetime.utcfromtimestamp()``: naives UTC."""
    return datetime.fromtimestamp(timestamp, timezone.utc).replace(tzinfo=None)
