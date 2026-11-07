"""Frist für die Alters- und Identitätsprüfung.

Regel (seit 08.11.2026): Wer sich registriert, aber nicht innerhalb eines
Monats seinen Ausweis zur Prüfung einreicht, verliert das Konto - es wird
samt allen Daten endgültig gelöscht (cleanup.purge_unverified_accounts).
Bis dahin geht jede Woche eine Mail mit dem Löschdatum raus
(email_jobs.run_deletion_warnings).

Was "eingereicht" heißt: Der Vorgang wurde mit Ausweis abgeschickt
(VerificationRequest.submitted_at). Danach liegt es beim Prüfer, nicht mehr
beim Nutzer - ein Konto, das auf die Prüfung wartet, wird nie gelöscht. Auch
bindende Ablehnungen fallen nicht unter die Regel, sie haben eingereicht.

Nur für Konten, die seit der Registrierung geprüft werden müssen: Ein
Bestandskonto, für das ein Admin die Prüfung nachträglich verlangt
(admin.require_verification, auch nach einer Ablehnung), fällt nicht
darunter - es hat Matches und Chats, die Aufforderungs-Mail kündigt keine
Löschung an, und AGB 5 g spricht von 30 Tagen "nach der Registrierung".
Bei neuen Konten setzt auth.register ``verification_required_at`` auf den
Zeitpunkt der Registrierung.

Wann die Frist beginnt (der späteste dieser Zeitpunkte):

* Registrierung (``created_at``),
* Anforderung eines neuen Ausweises durch den Prüfer: Wer rechtzeitig
  eingereicht hat, soll nicht deshalb gelöscht werden, weil die Rückfrage am
  29. Tag kam - ab der Rückfrage läuft wieder ein voller Monat,
* Einführung der Regel (``RULE_START``): Bestandskonten, die schon länger
  hängen, werden nicht über Nacht gelöscht, sondern bekommen ebenfalls einen
  Monat samt Mails.

Das Löschdatum ist ein Kalendertag in Wien: Beginn plus
``UNVERIFIED_ACCOUNT_DAYS`` Tage. Gelöscht wird beim ersten stündlichen
Aufräumlauf an diesem Tag; die Mail nennt genau diesen Tag.
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import and_, exists, func
from sqlalchemy.orm import Query, Session

from .message_texts import VIENNA
from .models import User, VerificationRequest, VerificationStatus
from .retention import UNVERIFIED_ACCOUNT_DAYS

#: Einführung der Regel: 08.11.2026, 00:00 Uhr in Wien (naive UTC wie in der DB).
RULE_START = datetime(2026, 11, 7, 23, 0, 0)

#: Spielraum zwischen created_at und verification_required_at, in dem die
#: Prüfpflicht noch als "seit der Registrierung" gilt (beide werden in
#: auth.register gesetzt, nur nicht im selben Augenblick).
REGISTRATION_SLACK = timedelta(hours=1)

#: Abstand der Erinnerungsmails.
WARNING_INTERVAL_DAYS = 7


def _vienna_date(value: datetime) -> date:
    return value.replace(tzinfo=timezone.utc).astimezone(VIENNA).date()


def _requirement_start(user: User) -> datetime:
    """Ab wann die Prüfung verlangt ist - ohne Rücksicht auf RULE_START.

    Eine Einreichung zählt nur, wenn sie danach liegt: Eine Prüfung aus der
    Zeit vor einer erneuten Anforderung erfüllt die neue nicht.
    """
    return max(filter(None, (user.created_at, user.verification_required_at)))


def submitted_condition():
    """SQL: Das Konto hat für die aktuell verlangte Prüfung einen Ausweis
    eingereicht."""
    return exists().where(
        and_(
            VerificationRequest.user_id == User.id,
            VerificationRequest.submitted_at.isnot(None),
            VerificationRequest.submitted_at
            >= func.coalesce(User.verification_required_at, User.created_at),
        )
    )


def subject_accounts(db: Session) -> Query:
    """Konten, für die die Frist läuft.

    Gesperrte Konten bleiben außen vor: Über sie entscheidet die Moderation,
    und ihre Geräte-IDs sind der Schutz gegen ein neues Konto.
    """
    return db.query(User).filter(
        User.deleted_at.is_(None),
        User.is_banned.is_(False),
        User.verification_required.is_(True),
        User.activated_at.is_(None),
        ~submitted_condition(),
    )


def required_since_registration(user: User) -> bool:
    """Prüfpflicht seit der Registrierung - nicht nachträglich verlangt.

    In Python statt in der Abfrage: ``DateTime + timedelta`` rechnet SQLite
    (Testdatenbank) in SQL nicht verlässlich. Die Aufrufer filtern damit die
    Treffer von subject_accounts().
    """
    if user.verification_required_at is None or user.created_at is None:
        return True
    return user.verification_required_at <= user.created_at + REGISTRATION_SLACK


def deadline_start(db: Session, user: User) -> datetime:
    """Beginn der Frist (siehe Moduldoku)."""
    candidates = [_requirement_start(user), RULE_START]
    latest = (
        db.query(VerificationRequest)
        .filter(VerificationRequest.user_id == user.id)
        .order_by(VerificationRequest.created_at.desc())
        .first()
    )
    if (
        latest is not None
        and latest.status == VerificationStatus.reupload_required
        and latest.decided_at is not None
    ):
        candidates.append(latest.decided_at)
    return max(candidates)


def deletion_date(start: datetime) -> date:
    """Kalendertag (Wien), an dem das Konto gelöscht wird."""
    return _vienna_date(start) + timedelta(days=UNVERIFIED_ACCOUNT_DAYS)


def is_due(start: datetime, now: datetime) -> bool:
    return _vienna_date(now) >= deletion_date(start)


def warning_number(start: datetime, now: datetime) -> int | None:
    """Welche Wochenmail fällig ist - oder None.

    Mail 1 nach einer Woche, Mail 2 nach zwei Wochen usw., solange das
    Löschdatum noch nicht erreicht ist. Bestandskonten (Frist ab RULE_START)
    bekommen zusätzlich sofort Mail 0: Sie haben sich unter der alten Regel
    registriert und sollen nicht erst nach einer Woche davon erfahren.
    """
    if is_due(start, now):
        return None
    days = (_vienna_date(now) - _vienna_date(start)).days
    number = days // WARNING_INTERVAL_DAYS
    if number == 0 and start != RULE_START:
        return None
    return number
