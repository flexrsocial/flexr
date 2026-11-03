"""Kündigungsbutton nach § 312k BGB.

Mit dem Start in Deutschland Pflicht: Wer Abos über eine Website anbietet,
muss dort eine gut lesbare, ständig verfügbare Schaltfläche "Verträge hier
kündigen" bereitstellen. Sie führt ohne Anmeldung auf eine Bestätigungsseite
(Art der Kündigung, bei außerordentlicher mit Grund; Name; Vertrag;
Zeitpunkt; E-Mail) mit dem Knopf "Jetzt kündigen". Die Kündigung gilt mit dem
Zugang; bestätigt wird unverzüglich mit Inhalt, Datum, Uhrzeit und dem
Zeitpunkt, zu dem der Vertrag endet.

Nicht zu verwechseln mit dem Rücktritt (routers/withdrawal.py): Der löst den
Vertrag binnen 14 Tagen rückwirkend auf, die Kündigung beendet ihn zum Ende
der bezahlten Periode.

Automatisch umgesetzt wird eine ordentliche Kündigung zum nächstmöglichen
Zeitpunkt, wenn sich ein Web-Abo (Stripe) zuordnen lässt: über das
angemeldete Konto oder - ohne Anmeldung - über die angegebene E-Mail-Adresse.
Missbrauch durch Dritte bleibt dabei harmlos und sichtbar: Das Abo endet nur
zum Periodenende, lässt sich neu abschließen, und die Bestätigung geht an die
Adresse des Kontos. Alles andere (außerordentlich, Wunschtermin, kein Treffer,
Store-Abo) wird protokolliert, bestätigt und dem Betreiber gemeldet.
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import legal, stripe_client, telegram
from ..database import get_db
from ..mailer import email_configured, send_cancellation_confirmation
from ..message_texts import normalise, t
from ..models import CancellationDeclaration, User
from ..rate_limit import limiter
from ..schemas import CancellationAck, CancellationRequest
from ..security import optional_current_user
from ..timeutil import utcnow

logger = logging.getLogger("flexr.cancellation")

_LOCAL = ZoneInfo("Europe/Vienna")

router = APIRouter(prefix="/api/cancellation", tags=["cancellation"])


_DECLARATION = {
    "de": {
        "intro": "Hiermit kündige ich meinen Vertrag über FLEXR Premium ({brand}, {domain}).",
        "kind": "Art der Kündigung: {kind}",
        "reason": "Grund: {reason}",
        "name": "Name: {name}",
        "email": "E-Mail: {email}",
        "contract": "Vertrag/Konto: {contract}",
        "end": "Zeitpunkt: {end}",
        "next": "zum nächstmöglichen Zeitpunkt",
        "declared": "Erklärt am: {date} um {time} Uhr (UTC)",
    },
    "en": {
        "intro": "I hereby cancel my contract for FLEXR Premium ({brand}, {domain}).",
        "kind": "Type of cancellation: {kind}",
        "reason": "Reason: {reason}",
        "name": "Name: {name}",
        "email": "Email: {email}",
        "contract": "Contract/account: {contract}",
        "end": "Effective: {end}",
        "next": "at the earliest possible date",
        "declared": "Declared on: {date} at {time} (UTC)",
    },
}


def build_declaration_text(payload: CancellationRequest, received_at: datetime, lang: str) -> str:
    """Der Wortlaut, der gespeichert, angezeigt und bestätigt wird."""
    texte = _DECLARATION[normalise(lang)]
    zeilen = [
        texte["intro"].format(brand=legal.BRAND, domain=legal.DOMAIN),
        "",
        texte["kind"].format(kind=t(f"cancellation.kind.{payload.kind}", lang)),
    ]
    if payload.reason:
        zeilen.append(texte["reason"].format(reason=payload.reason))
    zeilen += [
        texte["name"].format(name=payload.name),
        texte["email"].format(email=payload.email),
    ]
    if payload.contract_reference:
        zeilen.append(texte["contract"].format(contract=payload.contract_reference))
    ende = payload.requested_end.strftime("%d.%m.%Y") if payload.requested_end else texte["next"]
    zeilen.append(texte["end"].format(end=ende))
    zeilen.append(
        texte["declared"].format(
            date=received_at.strftime("%d.%m.%Y"), time=received_at.strftime("%H:%M:%S"),
        )
    )
    return "\n".join(zeilen)


def _konto_zuordnen(db: Session, payload: CancellationRequest, current_user: User | None) -> User | None:
    if current_user is not None:
        return current_user
    return (
        db.query(User)
        .filter(func.lower(User.email) == payload.email.lower())
        .first()
    )


def _local_text(value: datetime, lang: str) -> str:
    lokal = value.replace(tzinfo=ZoneInfo("UTC")).astimezone(_LOCAL)
    if normalise(lang) == "en":
        return f"{lokal.day} {lokal.strftime('%B %Y')}, {lokal.strftime('%H:%M:%S')} ({lokal.strftime('%Z')})"
    return lokal.strftime("%d.%m.%Y, %H:%M:%S Uhr (%Z)")


def _end_text(declaration: CancellationDeclaration, lang: str) -> str:
    if declaration.effective_at is not None:
        lokal = declaration.effective_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(_LOCAL)
        return t("cancellation.end.date", lang, date=lokal.strftime("%d.%m.%Y"))
    if declaration.requested_end is not None:
        return t("cancellation.end.requested", lang, date=declaration.requested_end.strftime("%d.%m.%Y"))
    return t("cancellation.end.next", lang)


@router.post("", response_model=CancellationAck, status_code=201)
@router.post("/", response_model=CancellationAck, status_code=201, include_in_schema=False)
@limiter.limit("10/hour")
def declare_cancellation(
    request: Request,
    payload: CancellationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_current_user),
):
    """Nimmt eine Kündigung entgegen und bestätigt sie unverzüglich.

    Erst speichern, dann versenden: Die Kündigung gilt mit dem Zugang, ein
    Fehlschlag beim Versand oder bei Stripe darf sie nicht kippen.
    """
    lang = normalise(current_user.language if current_user else payload.language)

    # Idempotenz wie beim Rücktritt: Doppelklick auf "Jetzt kündigen" schickt
    # dieselbe request_id. Ein Treffer zählt nur, wenn er demselben
    # Erklärenden gehört - sonst gäbe eine erratene id fremde Daten heraus.
    request_id = payload.request_id
    if request_id:
        eigene = db.query(CancellationDeclaration).filter(
            CancellationDeclaration.request_id == request_id
        )
        if current_user is not None:
            eigene = eigene.filter(CancellationDeclaration.user_id == current_user.id)
        else:
            eigene = eigene.filter(
                func.lower(CancellationDeclaration.email) == payload.email.lower()
            )
        bestehend = eigene.first()
        if bestehend:
            return _ack_from(bestehend, payload.email, lang=lang)
        if db.query(CancellationDeclaration.id).filter(
            CancellationDeclaration.request_id == request_id
        ).first():
            request_id = None

    received_at = utcnow()
    text = build_declaration_text(payload, received_at, lang)

    konto = _konto_zuordnen(db, payload, current_user)
    automatisch = (
        payload.kind == "ordentlich"
        and payload.requested_end is None
        and konto is not None
        and bool(konto.stripe_subscription_id)
    )
    effective_at = None
    cancelled_at = None
    if automatisch:
        try:
            effective_at = stripe_client.cancel_subscription_at_period_end(
                konto.stripe_subscription_id
            )
            cancelled_at = utcnow()
        except Exception:  # noqa: BLE001 - darf die Erklärung nie zum Scheitern bringen
            logger.exception(
                "Stripe-Abo %s konnte bei der Kuendigung nicht automatisch "
                "gekuendigt werden - manuell nachziehen.",
                konto.stripe_subscription_id,
            )

    declaration = CancellationDeclaration(
        user_id=konto.id if konto else None,
        request_id=request_id,
        name=payload.name,
        email=payload.email,
        contract_reference=payload.contract_reference,
        kind=payload.kind,
        reason=payload.reason,
        requested_end=payload.requested_end,
        declaration_text=text,
        received_at=received_at,
        received_at_local=_local_text(received_at, lang),
        effective_at=effective_at,
        subscription_cancelled_at=cancelled_at,
        status="eingegangen",
    )
    db.add(declaration)
    db.commit()
    db.refresh(declaration)

    kann_mailen = email_configured()
    if kann_mailen:
        declaration.confirmation_sent_at = utcnow()
        declaration.status = "bestaetigt"
        db.commit()
        background_tasks.add_task(
            send_cancellation_confirmation,
            payload.email,
            payload.name,
            declaration.reference,
            declaration.received_at_local,
            text,
            payload.contract_reference,
            payload.kind,
            _end_text(declaration, lang),
            cancelled_at is not None,
            lang,
        )
    else:
        logger.error(
            "Kuendigung %s ohne Bestaetigungsmail: SMTP ist nicht konfiguriert.",
            declaration.reference,
        )

    if cancelled_at is not None:
        hinweis = "Stripe-Abo automatisch zum Periodenende gekuendigt"
    elif konto is not None and konto.has_store_premium:
        hinweis = "Store-Abo: Kuendigung laeuft ueber Apple bzw. Google, Kunde ist informiert"
    elif payload.kind == "ausserordentlich":
        hinweis = "AUSSERORDENTLICH - Grund pruefen und von Hand umsetzen"
    elif payload.requested_end is not None:
        hinweis = f"Wunschtermin {payload.requested_end:%d.%m.%Y} - von Hand umsetzen"
    else:
        hinweis = "kein Web-Abo zugeordnet, bitte von Hand pruefen"
    background_tasks.add_task(
        telegram.notify_admin_task,
        f"✂️ Kündigung {declaration.reference} eingegangen - {hinweis}. "
        f"Vertrag/Konto: {payload.contract_reference or payload.email}",
    )
    logger.info(
        "Kuendigung %s eingegangen (Konto zugeordnet: %s, automatisch: %s)",
        declaration.reference, konto is not None, cancelled_at is not None,
    )
    return _ack_from(declaration, payload.email, kann_mailen, lang)


def _ack_from(
    declaration: CancellationDeclaration,
    email: str,
    kann_mailen: bool | None = None,
    lang: str = "de",
) -> CancellationAck:
    if kann_mailen is None:
        kann_mailen = declaration.confirmation_sent_at is not None
    hinweis = (
        t("api.cancellation.confirmed", lang, email=email) if kann_mailen
        else t("api.cancellation.noMail", lang)
    )
    return CancellationAck(
        reference=declaration.reference,
        received_at=declaration.received_at,
        declaration_text=declaration.declaration_text,
        confirmation_sent=kann_mailen,
        effective_at=declaration.effective_at,
        status=declaration.status,
        message=t("api.cancellation.received", lang, reference=declaration.reference, hint=hinweis),
    )
