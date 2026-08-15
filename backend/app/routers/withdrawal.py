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

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from .. import legal
from ..database import get_db
from ..mailer import email_configured, send_withdrawal_confirmation
from ..models import User, WithdrawalDeclaration
from ..rate_limit import limiter
from ..schemas import WithdrawalAck, WithdrawalRequest
from ..security import optional_current_user

logger = logging.getLogger("flexr.withdrawal")

router = APIRouter(prefix="/api/withdrawal", tags=["withdrawal"])


def build_declaration_text(
    name: str, contract_reference: str | None, message: str | None, received_at: datetime
) -> str:
    """Der Wortlaut, der bestätigt und gespeichert wird.

    Angelehnt an das Muster-Widerrufsformular der Anlage zum FAGG - ergänzt um
    den Zeitpunkt, weil § 13a Abs. 4 FAGG Datum und Uhrzeit in der Bestätigung
    verlangt.
    """
    zeilen = [
        f"Hiermit widerrufe ich den von mir abgeschlossenen Vertrag über die "
        f"Nutzung von {legal.BRAND} ({legal.DOMAIN}).",
        "",
        f"Name: {name}",
    ]
    if contract_reference:
        zeilen.append(f"Vertrag/Konto: {contract_reference}")
    zeilen.append(
        f"Erklärt am: {received_at.strftime('%d.%m.%Y')} um "
        f"{received_at.strftime('%H:%M:%S')} Uhr (UTC)"
    )
    if message:
        zeilen += ["", "Anmerkung des Erklärenden:", message]
    return "\n".join(zeilen)


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
    received_at = datetime.utcnow()
    text = build_declaration_text(
        payload.name, payload.contract_reference, payload.message, received_at
    )

    declaration = WithdrawalDeclaration(
        user_id=current_user.id if current_user else None,
        name=payload.name,
        email=payload.email,
        contract_reference=payload.contract_reference,
        message=payload.message,
        declaration_text=text,
        received_at=received_at,
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
        declaration.confirmation_sent_at = datetime.utcnow()
        declaration.confirmation_channel = "email"
        db.commit()
        background_tasks.add_task(
            send_withdrawal_confirmation,
            payload.email,
            payload.name,
            declaration.reference,
            received_at.strftime("%d.%m.%Y %H:%M:%S UTC"),
            text,
            payload.contract_reference,
        )
    else:
        logger.error(
            "Ruecktritt %s ohne Bestaetigungsmail: SMTP ist nicht konfiguriert "
            "(siehe LEGAL_REVIEW.md, T-06)",
            declaration.reference,
        )

    logger.info(
        "Ruecktrittserklaerung %s eingegangen (Konto zugeordnet: %s)",
        declaration.reference,
        bool(current_user),
    )

    if kann_mailen:
        hinweis = (
            f"Die Bestätigung geht an {payload.email}. Bewahre sie auf — sie ist "
            "dein Nachweis nach § 13a Abs. 4 FAGG."
        )
    else:
        hinweis = (
            "Wir können dir gerade keine Bestätigungsmail schicken. Deine "
            "Erklärung ist trotzdem wirksam — sie gilt mit dem Eingang, nicht "
            "mit der Bestätigung. Bitte sichere dir den unten angezeigten "
            "Wortlaut samt Aktenzeichen (Bildschirmfoto genügt) und schreib uns "
            "zur Sicherheit an flexr.social@proton.me."
        )

    return WithdrawalAck(
        reference=declaration.reference,
        received_at=received_at,
        declaration_text=text,
        confirmation_sent=kann_mailen,
        message=(
            f"Dein Rücktritt ist erklärt (Aktenzeichen {declaration.reference}). "
            f"{hinweis}"
        ),
    )
