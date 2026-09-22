"""Online-Rücktrittsfunktion nach § 13a FAGG.

Ab 1. Oktober 2026 muss ein Unternehmer, der Verträge über eine
Online-Benutzeroberfläche schließt, dort auch eine Rücktrittsfunktion
bereitstellen: eine leicht auffindbare Möglichkeit, den Rücktritt zu erklären,
mit einem getrennten Bestätigungsschritt und einer unverzüglichen Bestätigung
auf einem dauerhaften Datenträger.

Warum das nicht "Abo kündigen" ist: Die Kündigung beendet einen laufenden
Vertrag zum Ende der Abrechnungsperiode; der Rücktritt löst ihn binnen der
14-Tage-Frist rückwirkend auf. Wer nur kündigen kann, hat sein Rücktrittsrecht
nicht ausgeübt. Beide Wege stehen deshalb nebeneinander.

Kein Login nötig: Wer sein Konto schon gelöscht hat oder sich nicht mehr
einloggen kann, muss trotzdem zurücktreten können. Ist ein gültiger Token
dabei, wird die Erklärung dem Konto zugeordnet - Pflicht ist das nicht.
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import legal
from ..database import get_db
from ..mailer import email_configured, send_withdrawal_confirmation
from ..models import User, WithdrawalDeclaration
from ..rate_limit import limiter
from ..message_texts import normalise, t
from ..schemas import WithdrawalAck, WithdrawalRequest, WithdrawalStatus
from ..security import optional_current_user
from ..stripe_client import cancel_subscription_immediately
from ..timeutil import utcnow

logger = logging.getLogger("flexr.withdrawal")

_VIENNA = ZoneInfo("Europe/Vienna")

router = APIRouter(prefix="/api/withdrawal", tags=["withdrawal"])


#: Bausteine des Wortlauts. Die Erklärung wird in der Sprache aufgezeichnet,
#: in der sie abgegeben wurde - wer das englische Formular ausfüllt, erklärt
#: auf Englisch, und genau das wird gespeichert und bestätigt. Eine deutsche
#: Aufzeichnung einer englisch abgegebenen Erklärung wäre nicht ihr Inhalt,
#: sondern eine Übersetzung davon.
_DECLARATION = {
    "de": {
        "intro": "Hiermit widerrufe ich den von mir abgeschlossenen Vertrag über die "
                 "Nutzung von {brand} ({domain}).",
        "name": "Name: {name}",
        "contract": "Vertrag/Konto: {contract}",
        "declared": "Erklärt am: {date} um {time} Uhr (UTC)",
        "note": "Anmerkung des Erklärenden:",
    },
    "en": {
        "intro": "I hereby give notice that I withdraw from my contract for the use "
                 "of {brand} ({domain}).",
        "name": "Name: {name}",
        "contract": "Contract/account: {contract}",
        "declared": "Declared on: {date} at {time} (UTC)",
        "note": "Note from the person declaring:",
    },
}


def build_declaration_text(
    name: str,
    contract_reference: str | None,
    message: str | None,
    received_at: datetime,
    lang: str = "de",
) -> str:
    """Der Wortlaut, der bestätigt und gespeichert wird.

    Angelehnt an das Muster-Widerrufsformular der Anlage zum FAGG - ergänzt um
    den Zeitpunkt, weil § 13a Abs. 4 FAGG Datum und Uhrzeit in der Bestätigung
    verlangt.
    """
    texte = _DECLARATION[normalise(lang)]
    zeilen = [
        texte["intro"].format(brand=legal.BRAND, domain=legal.DOMAIN),
        "",
        texte["name"].format(name=name),
    ]
    if contract_reference:
        zeilen.append(texte["contract"].format(contract=contract_reference))
    zeilen.append(
        texte["declared"].format(
            date=received_at.strftime("%d.%m.%Y"),
            time=received_at.strftime("%H:%M:%S"),
        )
    )
    if message:
        zeilen += ["", texte["note"], message]
    return "\n".join(zeilen)


@router.get("/status", response_model=WithdrawalStatus)
def withdrawal_status():
    """Ob die hervorgehobene Online-Rücktrittsfunktion schon Pflicht ist.

    Öffentlich, ungedrosselt, ohne Anmeldung - jede Seite mit dem
    Legal-Footer ruft das bei jedem Laden ab (siehe frontend/legal-status.js).
    """
    return WithdrawalStatus(
        legally_required=legal.withdrawal_function_legally_required(),
        effective_date=legal.WITHDRAWAL_FUNCTION_EFFECTIVE_DATE.isoformat(),
    )


@router.post("", response_model=WithdrawalAck, status_code=201)
@router.post("/", response_model=WithdrawalAck, status_code=201, include_in_schema=False)
@limiter.limit("10/hour")
def declare_withdrawal(
    request: Request,
    payload: WithdrawalRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_current_user),
):
    """Nimmt eine Rücktrittserklärung entgegen und bestätigt sie unverzüglich.

    Die Erklärung gilt mit dem Eingang - unabhängig davon, ob die
    Bestätigungsmail ankommt. Deshalb wird zuerst gespeichert und erst danach
    versendet, und ein Fehlschlag beim Versand kippt den Vorgang nicht.
    """
    # Idempotenz: Ein Doppelklick auf "Widerruf bestätigen" (Netzwerk-Retry,
    # zwei schnelle Klicks) schickt dieselbe request_id erneut. Statt einer
    # zweiten Erklärung samt zweiter Mail geben wir dann einfach die schon
    # gespeicherte zurück - der deaktivierte Button im Browser ist nur die
    # erste, nicht die einzige Absicherung.
    #
    # Die request_id kommt vom Client und ist damit frei waehlbar. Ungebunden
    # nachgeschlagen gaebe ein Treffer die *fremde* Erklaerung im Klartext
    # zurueck - declaration_text enthaelt Name, Vertragsbezug und die eigenen
    # Worte des Erklaerenden. Deshalb zaehlt ein Treffer nur, wenn er
    # demselben Erklaerenden gehoert: dem angemeldeten Konto, sonst derselben
    # E-Mail-Adresse einer kontolosen Erklaerung.
    request_id = payload.request_id
    if request_id:
        eigene = db.query(WithdrawalDeclaration).filter(
            WithdrawalDeclaration.request_id == request_id
        )
        if current_user is not None:
            eigene = eigene.filter(WithdrawalDeclaration.user_id == current_user.id)
        else:
            eigene = eigene.filter(
                WithdrawalDeclaration.user_id.is_(None),
                func.lower(WithdrawalDeclaration.email) == payload.email.lower(),
            )
        bestehend = eigene.first()
        if bestehend:
            return _ack_from(
                bestehend,
                payload.email,
                lang=normalise(
                    current_user.language if current_user else payload.language
                ),
            )

        # Kein eigener Treffer, die id ist aber schon vergeben: request_id ist
        # unique, ein zweiter Datensatz damit scheiterte am Constraint. Die
        # Erklaerung selbst darf daran nie scheitern (§ 13a FAGG - sie gilt mit
        # dem Eingang), also wird sie ohne die fremde id gespeichert.
        fremd = (
            db.query(WithdrawalDeclaration.id)
            .filter(WithdrawalDeclaration.request_id == request_id)
            .first()
        )
        if fremd:
            logger.warning(
                "Ruecktritt: request_id %r ist bereits fremd vergeben - "
                "Erklaerung wird ohne Idempotenzschluessel gespeichert.",
                request_id,
            )
            request_id = None

    # Die Profilsprache geht vor: Wer angemeldet ist, bekommt FLEXR ohnehin in
    # dieser Sprache. Ohne Konto zaehlt die Formularseite (/widerruf.html oder
    # /en/widerruf.html) - ein Ruecktritt steht ausdruecklich auch Leuten ohne
    # Konto offen (§ 13a FAGG), es gibt dort also kein Profil zum Nachschlagen.
    lang = normalise(current_user.language if current_user else payload.language)

    received_at = utcnow()
    received_at_vienna = received_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(_VIENNA)
    text = build_declaration_text(
        payload.name, payload.contract_reference, payload.message, received_at, lang
    )

    # Ein zugeordnetes, noch laufendes Abo wird sofort an der weiteren
    # Verlängerung gehindert - nicht erst, wenn jemand die Erklärung manuell
    # bearbeitet. Betrifft nur angemeldete Erklärungen: Ohne Konto lässt sich
    # kein Abo zuverlässig zuordnen, das bleibt manuelle Bearbeitung anhand
    # von contract_reference.
    subscription_stopped_at = None
    if current_user and current_user.stripe_subscription_id:
        try:
            cancel_subscription_immediately(current_user.stripe_subscription_id)
            subscription_stopped_at = utcnow()
            current_user.is_subscribed = False
        except Exception:  # noqa: BLE001 - darf die Erklärung nie zum Scheitern bringen
            logger.exception(
                "Stripe-Abo %s konnte beim Ruecktritt nicht automatisch gestoppt "
                "werden - manuell nachziehen.",
                current_user.stripe_subscription_id,
            )

    # Ein im App Store oder Play Store gekauftes Abo lässt sich hier **nicht**
    # stoppen, und das ist keine Lücke, sondern die Rechtslage: Bei einem Kauf
    # über einen Store ist Apple bzw. Google der Vertragspartner des Kunden.
    # Wir haben dort keinen Vertrag zu beenden und auch keine Handhabe dazu -
    # die Kündigung läuft über die Abo-Verwaltung des jeweiligen Stores, die
    # Rückerstattung über dessen Verfahren.
    #
    # Die Erklärung wird trotzdem entgegengenommen und protokolliert: Sie ist
    # eine Willenserklärung des Kunden, und es ist nicht seine Aufgabe, vorher
    # zu wissen, wer sie umzusetzen hat. Der Hinweis auf den richtigen Weg
    # steht in der Bestätigungsmail (siehe mailer.build_withdrawal_ack) und im
    # Admin-Dashboard, wo die Erklärung ohnehin gesichtet wird.
    if current_user and current_user.has_store_premium:
        logger.info(
            "Rücktritt bei laufendem Store-Abo (user=%s): Kündigung muss im "
            "Store erfolgen, hier nicht möglich.",
            current_user.id,
        )

    declaration = WithdrawalDeclaration(
        user_id=current_user.id if current_user else None,
        request_id=request_id,
        name=payload.name,
        email=payload.email,
        contract_reference=payload.contract_reference,
        message=payload.message,
        declaration_text=text,
        received_at=received_at,
        received_at_vienna=_received_at_text(received_at_vienna, lang),
        status="eingegangen",
        subscription_stopped_at=subscription_stopped_at,
    )
    db.add(declaration)
    db.commit()
    db.refresh(declaration)

    # Ob überhaupt eine Mail rausgehen kann, entscheidet die SMTP-Konfiguration.
    # Ohne sie schreibt der Mailer nur ins Log - dann darf hier weder ein
    # Versandzeitstempel stehen noch dem Erklärenden eine Bestätigung
    # versprochen werden, die nie ankommt. § 13a Abs. 4 FAGG verlangt eine
    # Bestätigung auf dauerhaftem Datenträger; wer keine bekommt, muss das
    # sofort erfahren und sich den angezeigten Wortlaut selbst sichern können.
    kann_mailen = email_configured()
    if kann_mailen:
        declaration.confirmation_sent_at = utcnow()
        declaration.confirmation_channel = "email"
        declaration.status = "bestaetigt"
        db.commit()
        background_tasks.add_task(
            send_withdrawal_confirmation,
            payload.email,
            payload.name,
            declaration.reference,
            declaration.received_at_vienna,
            text,
            payload.contract_reference,
            subscription_stopped_at is not None,
            lang,
        )
    else:
        logger.error(
            "Ruecktritt %s ohne Bestaetigungsmail: SMTP ist nicht konfiguriert.",
            declaration.reference,
        )

    logger.info(
        "Ruecktrittserklaerung %s eingegangen (Konto zugeordnet: %s, Abo gestoppt: %s)",
        declaration.reference,
        bool(current_user),
        subscription_stopped_at is not None,
    )

    return _ack_from(declaration, payload.email, kann_mailen, lang)


def _received_at_text(value: datetime, lang: str) -> str:
    """Eingangszeitpunkt für die Bestätigung nach § 13a Abs. 4 FAGG.

    Wird so gespeichert, wie er dem Erklärenden gezeigt und bestätigt wird -
    deshalb in seiner Sprache formatiert und nicht erst beim Anzeigen
    umgerechnet."""
    if normalise(lang) == "en":
        return f"{value.day} {value.strftime('%B %Y')}, {value.strftime('%H:%M:%S')} ({value.strftime('%Z')})"
    return value.strftime("%d.%m.%Y, %H:%M:%S Uhr (%Z)")


def _ack_from(
    declaration: WithdrawalDeclaration,
    email: str,
    kann_mailen: bool | None = None,
    lang: str = "de",
) -> WithdrawalAck:
    if kann_mailen is None:
        kann_mailen = declaration.confirmation_sent_at is not None

    hinweis = (
        t("api.withdrawal.confirmed", lang, email=email) if kann_mailen
        else t("api.withdrawal.noMail", lang)
    )

    return WithdrawalAck(
        reference=declaration.reference,
        received_at=declaration.received_at,
        declaration_text=declaration.declaration_text,
        confirmation_sent=kann_mailen,
        status=declaration.status,
        message=t(
            "api.withdrawal.received", lang,
            reference=declaration.reference, hint=hinweis,
        ),
    )
