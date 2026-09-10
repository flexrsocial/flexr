"""FLEXR Premium - Grenzen fuer Standardnutzer und ihre Durchsetzung.

Das Geschaeftsmodell seit dem 10.09.2026: **Die Plattform ist dauerhaft
kostenlos.** Registrieren, Profile sehen, liken, matchen, schreiben - all das
kostet nie etwas. Es gibt keine Bezahlwand und keinen Probemonat mehr; ein
Konto wird nie mangels Zahlung ausgesperrt.

Wer mehr will, schliesst FLEXR Premium ab (10 EUR/Monat, jederzeit kuendbar).
Standardnutzer stossen dafuer an drei Grenzen (Zahlen in ``config.py``):

* ``free_daily_likes``  - Likes je rollierendem 24-Stunden-Fenster
* ``free_open_chats``   - gleichzeitig laufende Unterhaltungen
* ``free_max_radius_km``- Suchumkreis

Dazu drei Funktionen, die es nur mit Premium gibt: eingehende Likes sehen, den
letzten Swipe zuruecknehmen und das Premium-Abzeichen im Profil.

**Alle Grenzen haengen an ``settings.premium_enabled``.** Solange der Schalter
aus ist (Beta), ist fuer jeden alles unbegrenzt - die Funktionen hier geben
dann durchweg "erlaubt" zurueck. Das ist der einzige Hebel; es gibt bewusst
keinen zweiten Ort, an dem sich das Verhalten in der Beta unterscheidet.

Warum die Zaehlungen hier stehen und nicht im jeweiligen Router: Die
Oberflaeche muss dieselben Zahlen anzeigen, die der Server durchsetzt
(GET /api/billing/status liefert sie mit). Zwei Zaehlungen an zwei Orten
laufen genau so lange synchron, bis jemand eine davon anfasst.
"""

from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import settings
from .models import Match, Message, Swipe, User

# Das Like-Fenster laeuft rollierend ab dem ersten Like, nicht ab Mitternacht.
# Ein Kalendertag waere fuer eine App, die abends nach dem Training benutzt
# wird, die schlechtere Wahl: Der Zaehler springt dann mitten in der Nutzung
# auf null zurueck oder eben gerade nicht, je nach Zeitzone des Servers.
LIKE_WINDOW = timedelta(hours=24)


# ---------------------------------------------------------------------------
# Likes
# ---------------------------------------------------------------------------

def likes_used(db: Session, user: User, now: datetime | None = None) -> int:
    """Wie viele Likes dieser Nutzer im laufenden 24-Stunden-Fenster gesetzt hat."""
    current = now or datetime.utcnow()
    return (
        db.query(func.count(Swipe.id))
        .filter(
            Swipe.from_user_id == user.id,
            Swipe.action == "like",
            Swipe.created_at >= current - LIKE_WINDOW,
        )
        .scalar()
        or 0
    )


def likes_remaining(db: Session, user: User, now: datetime | None = None) -> int | None:
    """Verbleibende Likes, oder ``None`` fuer "unbegrenzt".

    ``None`` statt einer sehr grossen Zahl, damit die Oberflaeche den
    Unterschied zwischen "noch 999" und "ohne Grenze" nicht raten muss.
    """
    if not settings.premium_enabled or user.is_premium:
        return None
    return max(0, settings.free_daily_likes - likes_used(db, user, now))


def next_like_at(db: Session, user: User, now: datetime | None = None) -> datetime | None:
    """Wann der naechste Like wieder frei wird (aeltester Like im Fenster + 24 h).

    Nur gefuellt, wenn das Kontingent gerade aufgebraucht ist - sonst gibt es
    nichts abzuwarten.
    """
    current = now or datetime.utcnow()
    if likes_remaining(db, user, current) != 0:
        return None
    oldest = (
        db.query(func.min(Swipe.created_at))
        .filter(
            Swipe.from_user_id == user.id,
            Swipe.action == "like",
            Swipe.created_at >= current - LIKE_WINDOW,
        )
        .scalar()
    )
    return oldest + LIKE_WINDOW if oldest else None


def ensure_like_allowed(db: Session, user: User) -> None:
    """Wirft 403, wenn das Like-Kontingent aufgebraucht ist.

    Bewusst **403 und nicht 402**: 402 hiess frueher "Probemonat abgelaufen,
    Konto gesperrt" und schickte die Clients auf die Bezahlwand, die es nicht
    mehr gibt. Ein erschoepftes Like-Kontingent ist kein gesperrtes Konto -
    alles andere funktioniert weiter.
    """
    remaining = likes_remaining(db, user)
    if remaining is None or remaining > 0:
        return
    frei_ab = next_like_at(db, user)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "like_limit_reached",
            "limit": settings.free_daily_likes,
            "next_like_at": frei_ab.isoformat() if frei_ab else None,
            "message": (
                f"Du hast deine {settings.free_daily_likes} Likes für heute "
                "aufgebraucht. Mit FLEXR Premium likest du ohne Grenze - "
                "sonst geht es in ein paar Stunden weiter."
            ),
        },
    )


# ---------------------------------------------------------------------------
# Offene Unterhaltungen
# ---------------------------------------------------------------------------

def _match_ids_with_own_messages(db: Session, user: User) -> set[str]:
    """Matches, in denen dieser Nutzer schon mindestens einmal geschrieben hat.

    Das ist die Definition von "offene Unterhaltung": Ein Match, das nur
    entstanden ist, zaehlt nicht - erst wer schreibt, belegt einen Platz. Ein
    Standardnutzer sammelt also beliebig viele Matches an und entscheidet
    selbst, mit wem er die drei Plaetze belegt.
    """
    return {
        row.match_id
        for row in db.query(Message.match_id)
        .filter(Message.sender_id == user.id)
        .distinct()
    }


def open_chats_used(db: Session, user: User) -> int:
    """Wie viele der eigenen Unterhaltungen noch bestehen.

    Aufgeloeste Matches zaehlen nicht mehr mit: Beim Aufloesen verschwindet der
    Match-Datensatz (die Nachrichten haengen per ON DELETE CASCADE daran), der
    Platz wird also von selbst frei. Der Join hier faengt den Rest ab - etwa
    Matches, die durch eine Kontoloeschung der Gegenseite weggefallen sind.
    """
    eigene = _match_ids_with_own_messages(db, user)
    if not eigene:
        return 0
    return (
        db.query(func.count(Match.id)).filter(Match.id.in_(eigene)).scalar() or 0
    )


def open_chats_remaining(db: Session, user: User) -> int | None:
    """Freie Chat-Plaetze, oder ``None`` fuer "unbegrenzt"."""
    if not settings.premium_enabled or user.is_premium:
        return None
    return max(0, settings.free_open_chats - open_chats_used(db, user))


def ensure_chat_allowed(db: Session, user: User, match_id: str) -> None:
    """Wirft 403, wenn eine **neue** Unterhaltung keinen Platz mehr haette.

    In einer bereits begonnenen Unterhaltung ist die Nachrichtenzahl nicht
    begrenzt - die Grenze steht am Anfang eines Gespraechs, nicht mittendrin.
    Jemandem beim dreissigsten Satz das Wort abzuschneiden waere die
    unfreundlichere Variante derselben Grenze.
    """
    if not settings.premium_enabled or user.is_premium:
        return
    eigene = _match_ids_with_own_messages(db, user)
    if match_id in eigene:
        return  # laeuft schon, belegt seinen Platz bereits
    if len(eigene) < settings.free_open_chats:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "chat_limit_reached",
            "limit": settings.free_open_chats,
            "message": (
                f"Du hast {settings.free_open_chats} Unterhaltungen offen - mehr "
                "gehen ohne FLEXR Premium nicht gleichzeitig. Löse ein Match auf "
                "oder hol dir Premium für unbegrenzt viele Chats."
            ),
        },
    )


# ---------------------------------------------------------------------------
# Suchumkreis
# ---------------------------------------------------------------------------

def max_radius_km(user: User) -> int:
    """Groesster Umkreis, den dieses Konto einstellen darf."""
    from .schemas import MAX_SEARCH_RADIUS_KM

    if not settings.premium_enabled or user.is_premium:
        return MAX_SEARCH_RADIUS_KM
    return settings.free_max_radius_km


def clamp_radius(user: User, radius_km: int) -> int:
    """Kappt einen Umkreiswunsch auf das Erlaubte.

    Bewusst kappen statt ablehnen: Wer Premium kuendigt, hat unter Umstaenden
    250 km eingestellt. Ein Fehler bei jedem spaeteren Speichern des Profils
    waere eine Sackgasse - stillschweigend auf 50 km zurueckzugehen ist das,
    was der Nutzer ohnehin tun muesste. Beim aktiven Verstellen faengt die
    Oberflaeche den Fall vorher ab und erklaert ihn.
    """
    return min(radius_km, max_radius_km(user))
