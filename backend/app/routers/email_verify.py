"""Bestätigung der E-Mail-Adresse per Aktivierungslink.

Der Bestätigungs-Endpunkt braucht bewusst **keine** Anmeldung: Der Link wird
oft in einem anderen Browser oder auf einem anderen Gerät geöffnet als dem, auf
dem registriert wurde. Der Token selbst ist der Nachweis.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..email_verification import (
    ConfirmationError,
    TOKEN_TTL_HOURS,
    build_link,
    confirm,
    issue,
)
from ..mailer import send_verification_email
from ..models import User
from ..rate_limit import limiter
from ..schemas import EmailConfirmRequest, EmailConfirmResponse, EmailResendResponse
from ..security import get_current_user

router = APIRouter(prefix="/api/auth/email", tags=["auth"])

logger = logging.getLogger("flexr.mail")


@router.post("/confirm", response_model=EmailConfirmResponse)
@limiter.limit("20/hour")
def confirm_email(
    request: Request,
    payload: EmailConfirmRequest,
    db: Session = Depends(get_db),
):
    try:
        user = confirm(db, payload.token)
    except ConfirmationError as err:
        raise HTTPException(400, str(err))
    return EmailConfirmResponse(email=user.email, name=user.name)


@router.post("/resend", response_model=EmailResendResponse)
@limiter.limit("3/hour")
def resend_email(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Neuen Link anfordern. Ein älterer offener Link verfällt dabei."""
    if current_user.email_verified:
        raise HTTPException(400, "Deine E-Mail-Adresse ist bereits bestätigt.")

    # Token synchron erzeugen (das ist eine Datenbankänderung, die feststehen
    # muss), Versand danach - ein hängender Mailserver darf die Antwort nicht
    # aufhalten. Gleiches Muster wie bei der Registrierung.
    token = issue(db, current_user)
    background_tasks.add_task(
        send_verification_email,
        current_user.email,
        current_user.name,
        build_link(token),
        TOKEN_TTL_HOURS,
    )
    return EmailResendResponse(email=current_user.email, valid_hours=TOKEN_TTL_HOURS)
