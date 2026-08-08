"""Altersberechnung - eine einzige, serverseitig verbindliche Stelle.

Das Alter wird immer aus dem Geburtsdatum gegen das tatsächliche Tagesdatum
gerechnet, nie als ``aktuelles Jahr - Geburtsjahr``. Am 18. Geburtstag ist die
Person 18 - die Registrierung ist an diesem Tag zulässig.

Am 29. Februar Geborene erreichen in Nicht-Schaltjahren am 1. März das nächste
Lebensjahr: der Vergleich (Monat, Tag) < (Geburtsmonat, Geburtstag) ist am
28. Februar noch wahr und zieht ein Jahr ab.
"""

from datetime import date

MIN_AGE = 18
MAX_AGE = 99

# Text, den ein Nutzer unter 18 zu sehen bekommt - an genau einer Stelle
# definiert, damit Web, Apps und API dieselbe Formulierung verwenden.
UNDERAGE_MESSAGE = "Du musst mindestens 18 Jahre alt sein, um FLEXR nutzen zu können."


def age_on(birthdate: date, today: date | None = None) -> int:
    """Alter in vollendeten Lebensjahren am Stichtag (Standard: heute)."""
    reference = today or date.today()
    return (
        reference.year
        - birthdate.year
        - ((reference.month, reference.day) < (birthdate.month, birthdate.day))
    )


def is_adult(birthdate: date, today: date | None = None) -> bool:
    return age_on(birthdate, today) >= MIN_AGE


def is_plausible_birthdate(birthdate: date, today: date | None = None) -> bool:
    """Formale Plausibilität: nicht in der Zukunft, nicht unrealistisch alt.
    Die Altersgrenze selbst prüft ``is_adult``."""
    reference = today or date.today()
    if birthdate > reference:
        return False
    return age_on(birthdate, reference) <= MAX_AGE
